"""Pune–PCMC coverage from CAMS; measured stations retain independent timestamps."""
import json
import hashlib
import logging
import math
import os
import threading
from concurrent.futures import ThreadPoolExecutor
import pandas as pd
import requests
from fastapi import HTTPException
from app.config import RAW, ROOT, TIMEZONE, BBOX
from app.services.regions import PUNE_POINTS, inside_pune, region_metadata
from app.services.runtime import Runtime, get_runtime
from app.services import database
from app.services.spatial import make_grid, distance_km, idw, CONFIG, ZONES, ASSUMPTIONS, spatial_assumptions
from app.services.spatial_inputs import load_spatial_inputs
from app.services.scenarios import simulate

LOG = logging.getLogger('airtwin.live')
SAMPLE = ROOT / 'data/sample/pune_provider_context.json'
PUNE_CACHE = RAW / 'pune_context.json'
AIR_FIELDS = ['pm2_5', 'pm10', 'nitrogen_dioxide', 'sulphur_dioxide', 'ozone', 'carbon_monoxide', 'dust', 'aerosol_optical_depth']
WEATHER_FIELDS = ['temperature_2m', 'relative_humidity_2m', 'wind_speed_10m', 'wind_direction_10m', 'precipitation', 'surface_pressure', 'cloud_cover']
PUNE_ASSUMPTIONS = [
    'Named Pune and PCMC points are CAMS model samples, not monitors at those locations; CAMS global resolution is approximately 45 km.',
    'Fresh OpenAQ PM2.5 station measurements, when available, have their own locations and timestamps.',
    'Map cells interpolate nearby values; they are not additional observations.',
    'Forecasts are CAMS provider forecasts, not a newly validated local LightGBM forecast.',
    'Traffic, industry and dust scenario responses are assumed, not measured activity or causal effects.',
]


def get_payload(url, params=None, headers=None, timeout=30):
    response = requests.get(url, params=params, headers=headers, timeout=timeout)
    response.raise_for_status()
    return response.json()


def fetch_observed_locations(locations, key, now):
    def fetch(location):
        sensors = {s['id']: s for s in location.get('sensors', [])
                   if (s.get('parameter') or {}).get('name') == 'pm25'
                   and (s.get('parameter') or {}).get('units') in ('µg/m³', 'μg/m³', 'ug/m3')}
        if not sensors:
            return [], 0
        try:
            rows = get_payload(f"https://api.openaq.org/v3/locations/{location['id']}/latest",
                               {'limit': 1000}, {'X-API-Key': key})['results']
        except (requests.RequestException, ValueError, KeyError, TypeError):
            return [], 1
        accepted = []
        for row in rows:
            try:
                sensor = sensors.get(row.get('sensorsId'))
                stamp = pd.Timestamp(row['datetime']['utc'])
                value = float(row['value'])
                coords = row.get('coordinates') or location['coordinates']
                if (not sensor or stamp.tzinfo is None or not math.isfinite(value)
                        or not 0 <= value <= 1000
                        or not pd.Timedelta(0) <= now - stamp <= pd.Timedelta(hours=24)):
                    continue
                if not all(math.isfinite(float(coords[k])) for k in ('latitude', 'longitude')):
                    continue
                name = location.get('name') or f"OpenAQ sensor {sensor['id']}"
                accepted.append({'id': f"openaq-{sensor['id']}", 'name': name,
                    'short_name': name.split(',')[0], 'latitude': coords['latitude'],
                    'longitude': coords['longitude'], 'pm25': value,
                    'timestamp': stamp.tz_convert(TIMEZONE).isoformat(), 'source_type': 'observed',
                    'assumptions': ['OpenAQ station concentration; freshness uses its measurement timestamp.',
                        f"Provider: {(location.get('provider') or {}).get('name', 'OpenAQ upstream provider')}."]})
            except (ValueError, KeyError, TypeError):
                continue
        return accepted, 0
    with ThreadPoolExecutor(max_workers=3) as pool:
        results = list(pool.map(fetch, locations))
    return [row for rows, _ in results for row in rows], sum(errors for _, errors in results)


def fetch_context(reference_points=PUNE_POINTS, bbox=BBOX, inside=inside_pune,
                  region_name='Pune + PCMC', prefix='pune-cams'):
    coordinates = {'latitude': ','.join(str(p[1]) for p in reference_points),
                   'longitude': ','.join(str(p[2]) for p in reference_points),
                   'timezone': TIMEZONE, 'past_days': 2, 'forecast_days': 4}
    air = get_payload('https://air-quality-api.open-meteo.com/v1/air-quality',
                      {**coordinates, 'hourly': ','.join(AIR_FIELDS), 'domains': 'cams_global'})
    weather = get_payload('https://api.open-meteo.com/v1/forecast',
                          {**coordinates, 'hourly': ','.join(WEATHER_FIELDS + ['boundary_layer_height']), 'wind_speed_unit': 'ms'})
    if not isinstance(air, list) or len(air) != len(reference_points) or len(weather) != len(reference_points):
        raise ValueError('Incomplete multi-location provider response')
    points = []
    for index, (name, lat, lon) in enumerate(reference_points):
        points.append({'id': f'{prefix}-{index}', 'name': name, 'latitude': lat, 'longitude': lon,
                       'air': air[index]['hourly'], 'air_units': air[index]['hourly_units'],
                       'air_grid': {'latitude': air[index].get('latitude'), 'longitude': air[index].get('longitude')},
                       'weather': weather[index]['hourly'], 'weather_units': weather[index]['hourly_units']})
    observed, warnings, discovered, observed_sensors, history_sensor_candidates = [], [], 0, [], []
    failures = 0
    key = os.getenv('OPENAQ_API_KEY')
    if key:
        try:
            locations = []
            page = 1
            while True:
                result = get_payload('https://api.openaq.org/v3/locations',
                    {'bbox': ','.join(map(str, bbox)), 'limit': 1000, 'page': page}, {'X-API-Key': key})['results']
                locations.extend(result)
                if len(result) < 1000:
                    break
                page += 1
            now = pd.Timestamp.now(tz='UTC')
            valid = [p for p in locations if inside((p.get('coordinates') or {}).get('latitude', 0),
                                                   (p.get('coordinates') or {}).get('longitude', 0))]
            discovered = sum(s.get('parameter', {}).get('name') == 'pm25' for p in valid for s in p.get('sensors', []))
            latest_dates = [pd.Timestamp(p['datetimeLast']['utc']) for p in valid if (p.get('datetimeLast') or {}).get('utc')]
            # Discover historical sensors independently of the 24-hour live-reading
            # gate. Stale sensor metadata is not itself an observed measurement.
            if prefix == 'pune-cams':
                seen = set()
                for location in valid:
                    coords = location['coordinates']
                    last = (location.get('datetimeLast') or {}).get('utc')
                    for sensor in location.get('sensors', []):
                        parameter = sensor.get('parameter') or {}
                        sid = str(sensor.get('id', ''))
                        if (parameter.get('name') != 'pm25'
                                or parameter.get('units') not in ('µg/m³', 'μg/m³', 'ug/m3')
                                or not sid.isdigit() or sid in seen):
                            continue
                        seen.add(sid)
                        history_sensor_candidates.append({
                            'id': f'openaq-{sid}', 'name': location.get('name') or f'OpenAQ sensor {sid}',
                            'latitude': coords['latitude'], 'longitude': coords['longitude'],
                            'timestamp': last or '',
                        })
            for location in valid:
                coords = location.get('coordinates') or {}
                for sensor in location.get('sensors', []):
                    parameter = sensor.get('parameter', {})
                    if parameter.get('name') == 'pm25' and parameter.get('units') in ['µg/m³', 'μg/m³', 'ug/m3']:
                        observed_sensors.append({'id': sensor['id'], 'location_id': location['id'],
                            'name': location.get('name', f"OpenAQ sensor {sensor['id']}"),
                            'latitude': coords.get('latitude'), 'longitude': coords.get('longitude'),
                            'source_type': 'observed'})
            observed, failures = fetch_observed_locations(valid, key, now)
            observed = [p for p in observed if inside(p['latitude'], p['longitude'])]
            if failures:
                warnings.append(f'{failures} OpenAQ location checks failed; other monitors were checked independently.')
            if not observed:
                age = round((now - max(latest_dates)).total_seconds() / 3600) if latest_dates else None
                warnings.append(f'No {region_name} OpenAQ PM2.5 readings passed the 24-hour freshness filter; latest location update age: {age} hours. CAMS coverage remains MODELED.')
        except (requests.RequestException, ValueError, KeyError, TypeError):
            warnings.append('OpenAQ current-station refresh failed; CAMS is retained with its MODELED label.')
    else:
        warnings.append('OpenAQ key absent: current coverage is entirely CAMS MODELED data.')
    return {'updated_at': pd.Timestamp.now(tz='UTC').isoformat(), 'points': points,
            'observed': observed, 'discovered_pm25_sensors': discovered, 'warnings': warnings,
            'observed_sensors': observed_sensors, 'history_sensor_candidates': history_sensor_candidates,
            'monitor_check_failures': failures,
            'source_type': 'modeled', 'provider': 'CAMS / Open-Meteo', 'assumptions': PUNE_ASSUMPTIONS}


def save_context(payload, path=PUNE_CACHE, region='pcmc'):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix('.tmp')
    temp.write_text(json.dumps(payload, allow_nan=False))
    temp.replace(path)
    if not database.configured():
        return
    try:
        database.save_snapshot(region, payload)
    except Exception:
        LOG.warning('Could not persist %s provider snapshot to PostgreSQL.', region, exc_info=True)


class ProviderRuntime(Runtime):
    region_name = 'Pune + PCMC'
    region_id = 'pcmc'
    bbox = BBOX
    grid_size = 12
    mask = None
    assumptions = PUNE_ASSUMPTIONS
    def __init__(self, payload, sample=False):
        self.payload = payload
        self.sample = sample
        self.warnings = [*payload.get('warnings', [])]
        if sample:
            self.warnings.append('Provider cache unavailable: using a dated committed CAMS sample, not current live readings.')
        self.scenarios = {}
        self.timelines = {}
        self.exog = None
        self.spatial_inputs = None
        self.zones = ZONES
        self.spatial_assumptions = self.assumptions
        rows = []
        self.points = {p['id']: p for p in payload['points']}
        self.model_references = {
            point['id']: {field: 'cams-series-' + hashlib.sha256(json.dumps(
                [point['air']['time'], point['air'].get(field), point['air_units'].get(field)],
                separators=(',', ':'), allow_nan=False).encode()).hexdigest()
                for field in AIR_FIELDS if field in point['air']}
            for point in payload['points']
        }
        for point in payload['points']:
            weather = pd.DataFrame(point['weather']).rename(columns={'time': 'timestamp'})
            air = pd.DataFrame(point['air']).rename(columns={'time': 'timestamp', 'pm2_5': 'pm25'})
            data = air.merge(weather, on='timestamp', how='left')
            data['timestamp'] = pd.to_datetime(data.timestamp).dt.tz_localize(TIMEZONE)
            data['station_id'], data['station_name'] = point['id'], point['name']
            data['latitude'], data['longitude'] = point['latitude'], point['longitude']
            data['source_type'], data['target_provider'] = 'modeled', 'CAMS via Open-Meteo'
            rows.append(data)
        self.all_frame = pd.concat(rows, ignore_index=True)
        now = pd.Timestamp.now(tz=TIMEZONE).floor('h')
        self.origin = min(now, self.all_frame.timestamp.max() - pd.Timedelta(hours=24))
        if sample:
            self.origin = pd.Timestamp(payload['sample_origin'])
        self.frame = self.all_frame[self.all_frame.timestamp <= self.origin]
        self.future_weather = []

    def map_anchors(self, stations):
        anchors = {}
        for station in stations:
            if station['id'] not in self.points:
                continue
            grid = self.points[station['id']].get('air_grid') or {}
            lat, lon = grid.get('latitude'), grid.get('longitude')
            if lat is not None and lon is not None:
                key = (lat, lon, station['model_reference_id'])
                anchors.setdefault(key, {**station, 'latitude': lat, 'longitude': lon})
            else:
                anchors[station['id']] = station
        return list(anchors.values())

    def snapshot(self, replay_at=None):
        if replay_at:
            raise HTTPException(422, 'Historical held-out replay is available in the Pune + PCMC region only.')
        rows = self.frame[self.frame.timestamp == self.origin].dropna(subset=['pm25'])
        stations = []
        for row in rows.itertuples():
            point = self.points[row.station_id]
            pollutants = {key: {'value': float(getattr(row, 'pm25' if key == 'pm2_5' else key)),
                                  'unit': point['air_units'].get(key, ''), 'source_type': 'modeled',
                                  'timestamp': self.origin.isoformat(),
                                  'model_reference_id': self.model_references[row.station_id][key]}
                          for key in AIR_FIELDS if pd.notna(getattr(row, 'pm25' if key == 'pm2_5' else key, None))}
            weather = {key: float(getattr(row, key)) for key in WEATHER_FIELDS if pd.notna(getattr(row, key, None))}
            stations.append({'id': row.station_id, 'name': f'{row.station_name} · CAMS reference',
                'short_name': row.station_name, 'latitude': row.latitude, 'longitude': row.longitude,
                'pm25': float(row.pm25), 'timestamp': self.origin.isoformat(), 'source_type': 'modeled',
                'assumptions': self.assumptions, 'pollutants': pollutants,
                'model_reference_id': self.model_references[row.station_id]['pm2_5'],
                'weather': {**weather, 'source_type': 'modeled', 'timestamp': self.origin.isoformat()}})
        if not stations:
            raise HTTPException(503, 'No valid CAMS points in provider cache')
        def weather_at(lat, lon):
            nearest = min(stations, key=lambda p: distance_km(lat, lon, p['latitude'], p['longitude']))
            return nearest['weather']
        weather = weather_at(18.52, 73.86)
        observed = [point for point in self.payload.get('observed', []) if 0<=(pd.Timestamp.now(tz=TIMEZONE) - pd.Timestamp(point['timestamp'])).total_seconds()<=86400]
        synchronized = [point for point in observed
            if pd.Timestamp(point['timestamp']).tz_convert(TIMEZONE).floor('h') == self.origin]
        interpolation_points = [*self.map_anchors(stations), *synchronized]
        cells, background = make_grid(interpolation_points, weather, self.origin, self.bbox, self.grid_size,
                                      self.mask, weather_at, spatial_inputs=self.spatial_inputs)
        for cell in cells:
            nearest = min(observed, key=lambda p: distance_km(cell['latitude'], cell['longitude'],
                          p['latitude'], p['longitude'])) if observed else None
            cell['measurement_support'] = {
                'nearest_monitor_km': round(distance_km(cell['latitude'], cell['longitude'],
                    nearest['latitude'], nearest['longitude']), 1) if nearest else None,
                'nearest_monitor_timestamp': nearest['timestamp'] if nearest else None,
                'synchronized_monitor_count': len(synchronized),
                'uncertainty': 'Local spatial error has not been validated; no calibrated interval is available.',
            }
            cell['assumptions'] = self.spatial_assumptions
        return stations + observed, cells, background, weather, self.origin

    def stations(self, replay_at=None):
        stations, _, _, weather, _ = self.snapshot(replay_at)
        age = max(0, (pd.Timestamp.now(tz=TIMEZONE) - self.origin).total_seconds() / 3600)
        warnings = [*self.warnings]
        if age > 6:
            warnings.append(f'CAMS context is {age:.0f} hours old. Provider updates do not guarantee real-time measurements.')
        modeled_values = {round(point['pm25'], 2) for point in stations if point['source_type'] == 'modeled'}
        return {'stations': stations, 'source_type': 'modeled', 'assumptions': self.assumptions,
            'warnings': warnings, 'data_mode': 'dated_cams_sample' if self.sample else 'refreshed_provider_cache',
            'weather': weather, 'zones': self.zones, 'zones_source_type': 'mapped' if self.spatial_inputs else 'illustrative',
            'region': {**region_metadata(self.region_id), 'forecast_provider': 'CAMS via Open-Meteo'},
            'coverage': {'modeled_points': len(self.points), 'observed_points': sum(p['source_type'] == 'observed' for p in stations),
                         'distinct_modeled_pm25_levels': len(modeled_values),
                         'discovered_pm25_sensors': self.payload.get('discovered_pm25_sensors', 0),
                         'monitor_check_failures': self.payload.get('monitor_check_failures', 0),
                         'synchronized_monitor_count': sum(p['source_type'] == 'observed' and
                             pd.Timestamp(p['timestamp']).tz_convert(TIMEZONE).floor('h') == self.origin for p in stations),
                         'native_model_resolution_km': 45,
                         'spatial_validation': 'Local spatial error is unvalidated. Finer map cells do not add measured detail.',
                         **self.payload.get('history_readiness', {}),
                         'updated_at': self.payload['updated_at'], 'refresh_interval_seconds': max(900, int(os.getenv('LIVE_REFRESH_SECONDS', '900'))), 'variables': AIR_FIELDS + WEATHER_FIELDS}}

    def location(self, location_id, replay_at=None):
        stations, cells, background, _, timestamp = self.snapshot(replay_at)
        found = next((p for p in stations if p['id'] == location_id), None)
        if found is None:
            cell = next((c for c in cells if c['id'] == location_id), None)
            if cell:
                found = {**cell, 'name': f'{self.region_name} grid {location_id}', 'short_name': 'Selected grid cell', 'timestamp': timestamp.isoformat()}
        if found is None:
            raise HTTPException(404, 'Unknown Pune–PCMC location')
        references = [p for p in stations if p['id'] in self.points]
        nearest = min(references, key=lambda p: distance_km(found['latitude'], found['longitude'], p['latitude'], p['longitude']))
        series = self.frame[self.frame.station_id == nearest['id']]
        return found, series, cells, background, nearest['weather'], timestamp, nearest['id']

    def forecast(self, location_id, hours=24, replay_at=None):
        location, history, _, _, _, timestamp, nearest = self.location(location_id, replay_at)
        targets = pd.date_range(timestamp + pd.Timedelta(hours=1), periods=hours, freq='h')
        future = self.all_frame[(self.all_frame.station_id == nearest) & self.all_frame.timestamp.isin(targets)].sort_values('timestamp')
        if (len(future) != hours or list(future.timestamp) != list(targets)
                or not all(pd.notna(value) and math.isfinite(value) and value >= 0 for value in future.pm25)):
            raise HTTPException(503, 'CAMS cache lacks complete hourly values for the requested horizon; refresh provider data.')
        points = [{'timestamp': row.timestamp.isoformat(), 'actual': float(row.pm25), 'predicted': None,
                   'p10': None, 'p90': None, 'persistence': None}
                  for row in history.tail(49).itertuples()]
        points += [{'timestamp': row.timestamp.isoformat(), 'actual': None, 'predicted': float(row.pm25),
                    'p10': None, 'p90': None, 'persistence': None} for row in future.itertuples()]
        reference = nearest
        spatial_notes = []
        if location_id.startswith('cell-'):
            stations = {s['id']: s for s in self.snapshot(replay_at)[0] if s['id'] in self.points}
            selected_times = {pd.Timestamp(p['timestamp']) for p in points}
            rows = self.all_frame[self.all_frame.timestamp.isin(selected_times)]
            values = {}
            for time, group in rows.groupby('timestamp'):
                samples = [{**stations[row.station_id], 'pm25': float(row.pm25)}
                    for row in group.itertuples() if row.station_id in stations
                    and pd.notna(row.pm25) and math.isfinite(row.pm25) and row.pm25 >= 0]
                anchors = self.map_anchors(samples)
                if time in targets and len({s['id'] for s in samples}) != len(stations):
                    raise HTTPException(503, 'CAMS cache lacks complete spatial forecast values; refresh provider data.')
                if anchors:
                    values[time] = idw(location['latitude'], location['longitude'], anchors)
            for point in points:
                value = values.get(pd.Timestamp(point['timestamp']))
                if value is None:
                    raise HTTPException(503, 'CAMS cache lacks values for the selected grid cell; refresh provider data.')
                point['predicted' if point['predicted'] is not None else 'actual'] = value
            reference = location_id
            spatial_notes = ['Grid-cell history and forecasts interpolate native CAMS model anchors by IDW, using the same spatial method as the forecast map.',
                             f'Weather uses the nearest named CAMS reference: {nearest}.']
        return {'location_id': location_id, 'source_type': 'modeled', 'history_source_type': 'modeled',
            'history_reference': reference, 'series': points, 'shap': None, 'weather_forecast': [
                {'timestamp': row.timestamp.isoformat(), 'source_type': 'modeled',
                 **{key: float(getattr(row, key)) for key in WEATHER_FIELDS if pd.notna(getattr(row, key, None))}}
                for row in future.itertuples()],
            'assumptions': [*self.assumptions, *spatial_notes, f'Forecast reference: {reference}; origin: {timestamp.isoformat()}.',
                            'This is a CAMS provider forecast, not the locally validated LightGBM model. No calibrated p10/p90 bands or TreeSHAP are claimed.']}

    def backtest(self, location_id, replay_at=None):
        if self.sample or (self.payload.get('sample_origin') and 'observed_sensors' not in self.payload):
            return self._backtest_unavailable(location_id, 'Dated sample context has no associated measured station benchmark. Use historical replay.')
        location = self.location(location_id, replay_at)[0]
        key = os.getenv('OPENAQ_API_KEY')
        catalog = self.payload.get('observed_sensors', [])
        if not catalog and key:
            try:
                locations = []
                page = 1
                while page <= 5:
                    result = get_payload('https://api.openaq.org/v3/locations',
                        {'bbox': ','.join(map(str, self.bbox)), 'limit': 1000, 'page': page},
                        {'X-API-Key': key}, timeout=10)['results']
                    locations.extend(result)
                    if len(result) < 1000:
                        break
                    page += 1
                catalog = []
                for item in locations:
                    coords = item.get('coordinates') or {}
                    lat, lon = coords.get('latitude'), coords.get('longitude')
                    if lat is None or lon is None or (self.mask is not None and not self.mask(lat, lon)):
                        continue
                    for sensor in item.get('sensors', []):
                        parameter = sensor.get('parameter', {})
                        if parameter.get('name') == 'pm25' and parameter.get('units') in ['µg/m³', 'μg/m³', 'ug/m3']:
                            catalog.append({'id': sensor['id'], 'name': item.get('name', 'OpenAQ monitor'),
                                'latitude': lat, 'longitude': lon, 'source_type': 'observed'})
            except (requests.RequestException, ValueError, KeyError, TypeError):
                catalog = []
        if not key:
            return self._backtest_unavailable(location_id, 'OPENAQ_API_KEY is not configured, so hourly measured history cannot be retrieved.')
        candidates = sorted((sensor for sensor in catalog if sensor.get('latitude') is not None and sensor.get('longitude') is not None),
            key=lambda sensor: distance_km(location['latitude'], location['longitude'], sensor['latitude'], sensor['longitude']))[:3]
        if not candidates:
            return self._backtest_unavailable(location_id, 'No PM2.5 monitor locations with coordinates are available in this region.')
        now = pd.Timestamp.now(tz='UTC')
        start = now - pd.Timedelta(days=30)
        chosen, observations = None, None
        for sensor in candidates:
            try:
                payload = get_payload(f"https://api.openaq.org/v3/sensors/{sensor['id']}/hours",
                    {'datetime_from': start.isoformat(), 'datetime_to': now.isoformat(), 'limit': 1000, 'page': 1},
                    {'X-API-Key': key}, timeout=12)
                series = {}
                for row in payload.get('results', []):
                    timestamp = (row.get('period') or {}).get('datetimeFrom', {}).get('utc')
                    value = row.get('value')
                    if timestamp and isinstance(value, (int, float)) and 0 <= value <= 1000:
                        series[pd.Timestamp(timestamp).floor('h')] = float(value)
                if len(series) >= 240:
                    chosen, observations = sensor, series
                    break
            except (requests.RequestException, ValueError, KeyError, TypeError):
                continue
        if observations is None:
            return self._backtest_unavailable(location_id, 'No nearby OpenAQ PM2.5 monitor has at least 240 valid hourly values in the last 30 days; a chronological holdout would be too small.')

        from app.services.station_selection import station_bundle
        records=[{'station_id':f"openaq-{chosen['id']}",'timestamp':time.isoformat(),
                  'pm25':value,'source_type':'observed'} for time,value in observations.items()]
        try:
            bundle=station_bundle(records)
        except ValueError as error:
            return self._backtest_unavailable(location_id,str(error))
        return {'location_id':location_id,'source_type':'modeled','target_source_type':'observed',
                'series':bundle['series'],'metrics':bundle['metrics'],'available':True,
                'method':'24-hour selected station baseline · purged fit/selection/test',
                'model':bundle['report']['selected_method'],'selection':bundle['report'],
                'assumptions':[f"Observed monitor: {chosen['name']} (sensor {chosen['id']}); the chosen station may differ from the map point.",
                               bundle['report']['reason'],
                               'Exact current and 1, 3, 6, 12, 24 and 48-hour observed lags; no gap imputation.',
                               'Fit and selection targets are purged before the following period begins. The final test is not used to choose the model.',
                               'This station benchmark does not validate CAMS or causal intervention effects.',
                               'Only seasons present in the test data are reported; absent seasons remain unvalidated.']}

    @staticmethod
    def _backtest_unavailable(location_id, reason):
        return {'location_id': location_id, 'source_type': 'modeled', 'target_source_type': 'observed',
            'series': [], 'metrics': None, 'available': False,
            'method': 'Observed hourly monitor history is required for a chronological 24-hour backtest',
            'assumptions': [reason, 'No modeled CAMS history is presented as an observed validation target.']}

    def scenario(self, location_id, cuts, replay_at=None):
        location, _, cells, background, weather, timestamp, _ = self.location(location_id, replay_at)
        result = simulate(location, cells, background, cuts, weather, timestamp,
                          self.zones, self.spatial_assumptions)
        result['scenario_id'] = self.region_id + '-' + result['scenario_id']
        result['assumptions'] = self.assumptions
        for item in result['results']:
            item['assumptions'] = self.assumptions
        if len(self.scenarios) >= 100:
            self.scenarios.pop(next(iter(self.scenarios)))
        self.scenarios[result['scenario_id']] = result
        return result

    def attribution(self, location_id, replay_at=None):
        result = super().attribution(location_id, replay_at)
        result['assumptions'] = self.assumptions
        return result


class PuneRuntime(ProviderRuntime):
    region_name = 'Pune + PCMC'
    region_id = 'pcmc'
    bbox = BBOX
    grid_size = 12
    mask = None
    assumptions = PUNE_ASSUMPTIONS

    def __init__(self, payload):
        super().__init__(payload)
        self.spatial_inputs = load_spatial_inputs()
        self.zones = self.spatial_inputs.get('zones', ZONES) if self.spatial_inputs else ZONES
        self.spatial_assumptions = [*spatial_assumptions(self.spatial_inputs), *PUNE_ASSUMPTIONS]

    def forecast(self, location_id, hours=24, replay_at=None):
        # Historical backtests are routed to the original Runtime, not live ML.
        if replay_at:
            return super().forecast(location_id, hours, replay_at)
        from app.services.forecast_dispatcher import (
            nearest_provider_frame, run_observed_station_forecast,
        )
        sensor = next((item for item in self.payload.get('observed', [])
                       if item.get('id') == location_id and item.get('source_type') == 'observed'), None)
        reason = 'location_has_no_observed_sensor'
        if sensor is not None:
            try:
                if hours==24:
                    from app.services.live_observations import read_observations
                    from app.services.station_selection import station_forecast
                    try:
                        selected=station_forecast(sensor,read_observations(sensor['id'],hours=720),hours)
                        if selected is not None:
                            return selected
                    except ValueError:
                        pass
                context = nearest_provider_frame(sensor, self.points, self.all_frame)
                result, reason = run_observed_station_forecast(sensor, context, hours)
                if result is not None:
                    return result
            except Exception:
                LOG.warning('Live ML dispatch failed; preserving CAMS fallback.', exc_info=True)
                reason = 'live_ml_dispatch_error'
        fallback = super().forecast(location_id, hours, replay_at)
        fallback.update(
            forecast_provider='CAMS via Open-Meteo',
            model_id='cams-global-provider',
            model_version=None,
            issued_at=self.payload.get('updated_at', self.origin.isoformat()),
            input_cutoff=self.origin.isoformat(),
            fallback_reason=reason,
        )
        fallback['assumptions'].append(
            f'Live LightGBM unavailable ({reason}); CAMS provider forecast shown instead.')
        return fallback

    def backtest(self, location_id, replay_at=None):
        result = super().backtest(location_id, replay_at)
        result['assumptions'].append('The Pune + PCMC historical replay validates the production AirTwin model separately from this observed-station benchmark.')
        return result


_pune_runtime = None
_pune_lock = threading.Lock()


def get_pune_runtime():
    global _pune_runtime
    with _pune_lock:
        if _pune_runtime is None:
            payload = None
            try:
                payload = database.load_latest_snapshot('pcmc')
            except Exception:
                LOG.warning('Could not load the PCMC snapshot from PostgreSQL; trying the local cache.', exc_info=True)
            if payload is not None:
                try:
                    _pune_runtime = PuneRuntime(payload)
                except (ValueError, KeyError, TypeError):
                    LOG.warning('Stored PCMC snapshot is invalid; trying the local cache.', exc_info=True)
            if _pune_runtime is None:
                try:
                    _pune_runtime = PuneRuntime(json.loads(PUNE_CACHE.read_text()))
                except (OSError, ValueError, KeyError, TypeError):
                    return None
        return _pune_runtime


def get_region_runtime(region, replay_at=None):
    if region != 'pcmc':
        raise HTTPException(422, 'Only Pune + PCMC is supported')
    if replay_at or os.getenv('LIVE_REFRESH_ENABLED', '1') != '1':
        return get_runtime()
    return get_pune_runtime() or get_runtime()


def refresh_pune():
    global _pune_runtime
    def inside_pune(lat, lon):
        return BBOX[1] <= lat <= BBOX[3] and BBOX[0] <= lon <= BBOX[2]
    payload = fetch_context(PUNE_POINTS, BBOX, inside_pune, 'Pune + PCMC', 'pune-cams')
    runtime = PuneRuntime(payload)
    runtime.snapshot()
    # Only actual OpenAQ hourly readings are stored as station observations.
    # Failure must not block CAMS provider coverage.
    try:
        from app.services.live_observations import ingest_pune_history, latest_cached_monitors
        history_status = ingest_pune_history(payload.get('history_sensor_candidates', []), get_payload)
        payload['history_ingestion'] = history_status
        from app.services.live_observations import read_training_observations
        records = read_training_observations(hours=720)
        counts = {}
        for record in records:
            counts[record['station_id']] = counts.get(record['station_id'], 0) + 1
        payload['history_readiness'] = {
            'training_observed_hours': len(records), 'training_monitor_count': len(counts),
            'largest_monitor_history_hours': max(counts.values(), default=0),
            'local_model_status': 'Spatial validation against withheld monitors is required before a finer local model can be used.',
        }
        merged={s['id']:s for s in payload.get('observed',[])}
        for point in latest_cached_monitors(payload.get('history_sensor_candidates',[])):
            if point['id'] not in merged or pd.Timestamp(point['timestamp'])>pd.Timestamp(merged[point['id']]['timestamp']):
                merged[point['id']]=point
        payload['observed']=list(merged.values())
        if payload['observed']:
            payload['warnings'] = [w for w in payload['warnings'] if 'passed the 24-hour freshness filter' not in w]
            runtime.warnings = [w for w in runtime.warnings if 'passed the 24-hour freshness filter' not in w]
        if history_status['failures']:
            message = (f"{history_status['failures']} OpenAQ hourly-history lookups failed; "
                       "live LightGBM may use CAMS fallback.")
            payload['warnings'].append(message)
            runtime.warnings.append(message)
        LOG.info('OpenAQ hourly history: %s sensors, %s accepted hours, %s errors',
                 history_status['sensors'], history_status['rows'], history_status['failures'])
    except Exception:
        message = 'OpenAQ history persistence unavailable; keeping CAMS fallback.'
        payload['warnings'].append(message)
        runtime.warnings.append(message)
        LOG.warning('OpenAQ hourly history refresh failed.', exc_info=True)
    save_context(payload, PUNE_CACHE, 'pcmc')
    with _pune_lock:
        _pune_runtime = runtime
    LOG.info('Pune refresh: %s modeled reference points; %s observed points',
             len(payload['points']), len(payload['observed']))

def live_loop(stop):
    interval = max(900, int(os.getenv('LIVE_REFRESH_SECONDS', '900')))
    while not stop.is_set():
        try:
            from app.services.live_feed import refresh_indices
            refresh_indices()
        except (requests.RequestException, ValueError, OSError):
            LOG.warning('IITM AQI refresh failed; original measurement timestamps retained.', exc_info=True)
        try:
            refresh_pune()
        except (requests.RequestException, ValueError, KeyError, TypeError, HTTPException):
            LOG.warning('Pune provider refresh failed; retaining the last labeled cache.', exc_info=True)
            runtime = get_pune_runtime()
            if runtime:
                warning = 'Latest Pune provider refresh failed; showing the last cache with its original timestamp.'
                if warning not in runtime.warnings:
                    runtime.warnings.append(warning)
        stop.wait(interval)
