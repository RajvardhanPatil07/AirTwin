"""A cached dataset/model bundle shared by all endpoint responses."""
from functools import lru_cache
import pandas as pd
import json
from app.config import RAW
from fastapi import HTTPException
from app.services.data_loader import load_dataset
from app.services.model import load_or_train, predict, explain_features, metrics
from app.services.spatial import make_grid, ASSUMPTIONS, CONFIG, ZONES, distance_km
from app.services.attribution import attribute
from app.services.scenarios import simulate


class Runtime:
    def __init__(self, force_sample=False):
        self.frame, self.warnings, self.fingerprint = load_dataset(force_sample)
        self.artifact = load_or_train(self.frame, self.fingerprint, self.warnings)
        self.scenarios = {}
        self.future_weather = []
        forecast_path = RAW / 'weather_forecast.json'
        if not force_sample and forecast_path.exists():
            try:
                self.future_weather = json.loads(forecast_path.read_text())
            except (ValueError, OSError):
                self.warnings.append('Forecast weather cache unavailable; issue-weather persistence remains in use.')

    def snapshot(self, replay_at=None):
        frame = self.frame
        if replay_at:
            try:
                timestamp = pd.Timestamp(replay_at)
                if timestamp.tzinfo is None:
                    raise ValueError('Replay requires a timezone offset')
                frame = frame[frame.timestamp <= timestamp]
            except (ValueError, TypeError):
                raise HTTPException(422, 'Invalid replay timestamp')
        if frame.empty:
            raise HTTPException(404, 'No data at requested replay time')

        timestamp = frame.timestamp.max()
        recent = frame[frame.timestamp >= timestamp - pd.Timedelta(hours=CONFIG['station_max_age_hours'])].copy()
        rows = (
            recent.sort_values(['station_id', 'timestamp'])
            .groupby('station_id', as_index=False, group_keys=False)
            .tail(1)
        )
        if rows.empty:
            raise HTTPException(404, 'No recent station anchors available')

        stations = []
        for row in rows.itertuples():
            age_hours = max(0.0, (timestamp - row.timestamp).total_seconds() / 3600)
            stations.append({
                'id': str(row.station_id),
                'name': row.station_name,
                'short_name': row.station_name.split(',')[0],
                'latitude': row.latitude,
                'longitude': row.longitude,
                'pm25': row.pm25,
                'timestamp': row.timestamp.isoformat(),
                'age_hours': age_hours,
                'source_type': row.source_type,
                'assumptions': [
                    f'Target provider: {row.target_provider}.',
                    f'Latest reading is {age_hours:.1f} hours behind the map reference time.',
                    'Interpolation down-weights older station anchors; missing measurements are not imputed.',
                    *self.warnings,
                ],
            })

        weather_columns = [
            'temperature_2m',
            'relative_humidity_2m',
            'wind_speed_10m',
            'wind_direction_10m',
            'precipitation',
        ]
        weather_rows = frame[frame.timestamp == timestamp]
        if weather_rows.empty:
            weather_rows = rows
        weather = {
            key: float(weather_rows[key].mean())
            for key in weather_columns
            if key in weather_rows and weather_rows[key].notna().any()
        }

        background_override = None
        if len(stations) < 3:
            history_start = timestamp - pd.Timedelta(days=30)
            history = frame[
                (frame.timestamp >= history_start) & (frame.timestamp <= timestamp)
            ].pm25.dropna()
            if not history.empty:
                temporal_background = float(
                    history.quantile(CONFIG['background_percentile'] / 100)
                )
                current_floor = min(float(station['pm25']) for station in stations)
                background_override = min(temporal_background, current_floor)
                note = (
                    'Sparse spatial anchors: regional background uses the recent '
                    f'30-day {CONFIG["background_percentile"]}th-percentile target '
                    'as a MODELED fallback.'
                )
                for station in stations:
                    station['assumptions'] = [note, *station['assumptions']]

        cells, background = make_grid(
            stations,
            weather,
            timestamp,
            background_override=background_override,
        )
        return stations, cells, background, weather, timestamp

    def stations(self, replay_at=None):
        stations, cells, _, weather, timestamp = self.snapshot(replay_at)
        source = stations[0]['source_type']
        warnings = [*self.warnings]
        age = (pd.Timestamp.now(tz=timestamp.tz) - timestamp).total_seconds() / 3600
        if not replay_at and age > 24:
            warnings.append(
                f'Latest available map reference is {age:.0f} hours old. '
                'This is cached historical data, not current live readings.'
            )
        return {
            'stations': stations,
            'source_type': source,
            'assumptions': ASSUMPTIONS,
            'warnings': warnings,
            'data_mode': 'historical_replay' if replay_at else 'cached_dataset',
            'weather': {
                **weather,
                'source_type': str(self.frame.weather_source_type.iloc[-1]),
                'timestamp': timestamp.isoformat(),
            },
            'zones': ZONES,
            'coverage': {
                'station_anchors': len(stations),
                'freshest_anchor_hours': min(s.get('age_hours', 0) for s in stations),
                'oldest_anchor_hours': max(s.get('age_hours', 0) for s in stations),
                'grid_cells': len(cells),
                'grid_size': int(round(len(cells) ** 0.5)),
            },
        }

    def location(self, location_id, replay_at=None):
        stations, cells, background, weather, timestamp = self.snapshot(replay_at)
        found = next((s for s in stations if s['id'] == location_id), None)
        if found is None:
            cell = next((c for c in cells if c['id'] == location_id), None)
            if cell:
                found = {**cell, 'name': f"Grid {location_id}", 'short_name': 'Selected grid cell',
                         'timestamp': timestamp.isoformat()}
        if found is None:
            raise HTTPException(404, 'Unknown location or station absent from snapshot')
        nearest = min(stations, key=lambda s: distance_km(found['latitude'], found['longitude'], s['latitude'], s['longitude']))
        series = self.frame[(self.frame.station_id == nearest['id']) & (self.frame.timestamp <= timestamp)]
        return found, series, cells, background, weather, timestamp, nearest['id']

    def forecast(self, location_id, hours=24, replay_at=None):
        location, series, _, _, _, timestamp, nearest_id = self.location(location_id, replay_at)
        history = [{'timestamp': row.timestamp.isoformat(), 'actual': row.pm25, 'predicted': None,
                    'persistence': None, 'p10': None, 'p90': None} for row in series[series.timestamp >= timestamp - pd.Timedelta(hours=48)].itertuples()]
        assumptions = [*self.warnings,
                       ('Replay uses the pre-holdout direct 24h model, with interpolation for shorter points.' if replay_at else 'Direct LightGBM horizons 1–24, 48 and 72; other hourly values are linearly interpolated.'),
                       'Quantile p10/p90 bounds have measured holdout coverage, not guaranteed calibration.',
                       self.artifact['report']['weather_evaluation'],
                       '24/48/72h use stored issue-aligned forecast weather where available; shorter horizons use issue-weather persistence.']
        assumptions.append(f'Forecast origin is {timestamp.isoformat()}; stale observations do not become current measurements.')
        if location_id != nearest_id:
            assumptions.append(f'Grid forecast uses temporal history of nearest station {nearest_id}; it is not an independently validated grid model.')
        if replay_at:
            assumptions.append('Replay uses the pre-holdout 24-hour model. Shorter horizons interpolate from the issue reading; these are not independently calibrated forecasts.')
        if replay_at:
            if hours > 24:
                raise HTTPException(422, 'Historical replay supports the held-out 24-hour model only')
            replay_artifact = {**self.artifact, 'models': {24: self.artifact['validation_models']}}
            endpoint = predict(replay_artifact, series, 24)[-1]
            initial = float(series.pm25.iloc[-1])
            values = [tuple(initial + (value - initial) * h / 24 for value in endpoint) for h in range(1, hours + 1)]
        else:
            values = predict(self.artifact, series, hours)
        forecast = [{'timestamp': (timestamp + pd.Timedelta(hours=i + 1)).isoformat(), 'actual': None,
                     'predicted': value[0], 'p10': value[1], 'p90': value[2], 'persistence': None}
                    for i, value in enumerate(values)]
        return {'location_id': location_id, 'series': history + forecast, 'source_type': 'modeled',
                'history_source_type': str(series.source_type.iloc[-1]), 'assumptions': assumptions,
                'history_reference': nearest_id,
                'shap': explain_features(replay_artifact if replay_at else self.artifact, series), 'weather_forecast': self.future_weather}

    def backtest(self, location_id, replay_at=None):
        _, _, _, _, _, _, nearest = self.location(location_id, replay_at)
        rows = self.artifact['backtest']
        rows = rows[rows.station_id == nearest]
        reference_note = f'Validation station: {nearest}.'
        if rows.empty:
            available = self.artifact['backtest'].station_id.unique()
            location = self.location(location_id, replay_at)[0]
            candidates = self.frame[self.frame.station_id.isin(available)].groupby('station_id').first()
            if candidates.empty:
                raise HTTPException(404, 'No held-out predictions available')
            nearest = min(candidates.index, key=lambda key: distance_km(location['latitude'], location['longitude'], candidates.loc[key, 'latitude'], candidates.loc[key, 'longitude']))
            rows = self.artifact['backtest'][self.artifact['backtest'].station_id == nearest]
            reference_note = f'No holdout for selected sensor; displaying reference sensor {nearest} at {candidates.loc[nearest, "station_name"]}. This is not selected-sensor accuracy.'
        report = self.artifact['report']
        values = metrics(rows.target.to_numpy(), rows.predicted.to_numpy(), rows.persistence.to_numpy(), rows.p10.to_numpy(), rows.p90.to_numpy())
        points = [{'timestamp': r.timestamp.isoformat(), 'actual': r.target, 'predicted': r.predicted,
                   'persistence': r.persistence, 'p10': r.p10, 'p90': r.p90} for r in rows.itertuples()]
        return {'location_id': location_id, 'series': points, 'metrics': values, 'method': report['method'] + ' · LightGBM direct 24h',
                'source_type': 'modeled', 'target_source_type': str(rows.source_type.iloc[0]),
                'assumptions': [*self.warnings, 'Historical predictions use a separate pre-holdout model; serving uses refit models.',
                                report['weather_evaluation'], reference_note,
                                'Metrics use all displayed hourly targets; overlapping horizons are not independent experiments.'],
                'seasonal_baseline': report['seasonal_hourly_mean'], 'cv': report['cv']}

    def attribution(self, location_id, replay_at=None):
        location, _, _, background, weather, timestamp, _ = self.location(location_id, replay_at)
        return {**attribute(location, background, weather, timestamp), 'config': CONFIG}

    def scenario(self, location_id, cuts, replay_at=None):
        location, _, cells, background, weather, timestamp, _ = self.location(location_id, replay_at)
        result = simulate(location, cells, background, cuts, weather, timestamp)
        # Bounded in-memory results; no user sessions or persistent scenario storage.
        if len(self.scenarios) >= 100:
            self.scenarios.pop(next(iter(self.scenarios)))
        self.scenarios[result['scenario_id']] = result
        return result

    def replay(self):
        rows = self.artifact['backtest']
        grouped = rows.groupby('timestamp').target.mean()
        selected = grouped.idxmax()
        stations, _, _, _, timestamp = self.snapshot(selected.isoformat())
        return {'source_type': 'modeled', 'assumptions': ['Replay selects the highest mean held-out target hour.', 'Forecast replay is retrospective; held-out predictions are available in Backtest.'],
                'timestamp': timestamp.isoformat(), 'location_id': stations[0]['id'],
                'target_source_type': stations[0]['source_type']}


@lru_cache(maxsize=1)
def get_runtime():
    return Runtime()
