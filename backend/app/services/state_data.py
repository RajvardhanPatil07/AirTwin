"""Hourly state coverage from CAMS; measured stations retain independent timestamps."""
import json
import logging
import os
import threading
import pandas as pd
import requests
from fastapi import HTTPException
from app.config import RAW, ROOT, TIMEZONE, BBOX
from app.services.regions import CITY_POINTS, PUNE_POINTS, STATE_BBOX, inside_state, region_metadata
from app.services.runtime import Runtime, get_runtime
from app.services import database
from app.services.spatial import make_grid, distance_km, CONFIG, ZONES, ASSUMPTIONS, spatial_assumptions
from app.services.spatial_inputs import load_spatial_inputs
from app.services.scenarios import simulate

LOG = logging.getLogger('airtwin.live')
CACHE = RAW / 'maharashtra_context.json'
SAMPLE = ROOT / 'data/sample/maharashtra_context.json'
PUNE_CACHE = RAW / 'pune_context.json'
AIR_FIELDS = ['pm2_5', 'pm10', 'nitrogen_dioxide', 'sulphur_dioxide', 'ozone', 'carbon_monoxide', 'dust', 'aerosol_optical_depth']
WEATHER_FIELDS = ['temperature_2m', 'relative_humidity_2m', 'wind_speed_10m', 'wind_direction_10m', 'precipitation', 'surface_pressure', 'cloud_cover']
STATE_ASSUMPTIONS = [*ASSUMPTIONS,
    'Statewide coverage uses CAMS global atmospheric forecasts (~45 km), not new sensors or statewide LightGBM validation.',
    'City sampling coordinates are approximate. Grid cells are retained when their centre lies inside the state boundary.',
    'Source/activity zones are only mapped around Pune. Outside that area, shares use generic assumed weights, not local inventories.',
    'Statewide population weights remain an illustrative synthetic grid, not Maharashtra census or WorldPop data.',
]
PUNE_ASSUMPTIONS = [
    'Named Pune and PCMC points are CAMS model samples, not monitors at those locations; CAMS global resolution is approximately 45 km.',
    'Fresh OpenAQ PM2.5 station measurements, when available, have their own locations and timestamps.',
    'Map cells interpolate nearby values; they are not additional observations.',
    'Forecasts are CAMS provider forecasts, not a newly validated local LightGBM forecast.',
    'Traffic, industry and dust scenario responses are assumed, not measured activity or causal effects.',
]


def get_payload(url, params=None, headers=None):
    response = requests.get(url, params=params, headers=headers, timeout=30)
    response.raise_for_status()
    return response.json()


def fetch_context(reference_points=CITY_POINTS, bbox=STATE_BBOX, inside=inside_state,
                  region_name='Maharashtra', prefix='cams'):
    coordinates = {'latitude': ','.join(str(p[1]) for p in reference_points),
                   'longitude': ','.join(str(p[2]) for p in reference_points),
                   'timezone': TIMEZONE, 'past_days': 2, 'forecast_days': 4}
    air = get_payload('https://air-quality-api.open-meteo.com/v1/air-quality',
                      {**coordinates, 'hourly': ','.join(AIR_FIELDS), 'domains': 'cams_global'})
    weather = get_payload('https://api.open-meteo.com/v1/forecast',
                          {**coordinates, 'hourly': ','.join(WEATHER_FIELDS), 'wind_speed_unit': 'ms'})
    if not isinstance(air, list) or len(air) != len(reference_points) or len(weather) != len(reference_points):
        raise ValueError('Incomplete multi-location provider response')
    points = []
    for index, (name, lat, lon) in enumerate(reference_points):
        points.append({'id': f'{prefix}-{index}', 'name': name, 'latitude': lat, 'longitude': lon,
                       'air': air[index]['hourly'], 'air_units': air[index]['hourly_units'],
                       'weather': weather[index]['hourly'], 'weather_units': weather[index]['hourly_units']})
    observed, warnings, discovered = [], [], 0
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
            for location in valid:
                last = (location.get('datetimeLast') or {}).get('utc')
                if not last or now - pd.Timestamp(last) > pd.Timedelta(hours=24):
                    continue
                sensors = {s['id']: s for s in location.get('sensors', [])}
                latest = get_payload(f"https://api.openaq.org/v3/locations/{location['id']}/latest", {'limit': 1000}, {'X-API-Key': key})['results']
                for row in latest:
                    sensor = sensors.get(row.get('sensorsId'))
                    if not sensor or sensor['parameter']['name'] != 'pm25':
                        continue
                    unit = sensor['parameter'].get('units')
                    time = row['datetime']['utc']
                    value = row.get('value')
                    if unit not in ['µg/m³', 'μg/m³', 'ug/m3'] or value is None or not 0 <= value <= 1000:
                        continue
                    if now - pd.Timestamp(time) > pd.Timedelta(hours=24):
                        continue
                    coords = location['coordinates']
                    observed.append({'id': f"openaq-{sensor['id']}", 'name': location['name'],
                        'short_name': location['name'].split(',')[0], 'latitude': coords['latitude'],
                        'longitude': coords['longitude'], 'pm25': value, 'timestamp': pd.Timestamp(time).tz_convert(TIMEZONE).isoformat(),
                        'source_type': 'observed', 'assumptions': ['OpenAQ latest station concentration; timestamp is independent of CAMS.', f"Provider: {(location.get('provider') or {}).get('name', 'OpenAQ upstream provider')}."]})
            if not observed:
                age = round((now - max(latest_dates)).total_seconds() / 3600) if latest_dates else None
                warnings.append(f'No {region_name} OpenAQ PM2.5 readings passed the 24-hour freshness filter; latest location update age: {age} hours. CAMS coverage remains MODELED.')
        except (requests.RequestException, ValueError, KeyError, TypeError):
            warnings.append('OpenAQ current-station refresh failed; CAMS is retained with its MODELED label.')
    else:
        warnings.append('OpenAQ key absent: current coverage is entirely CAMS MODELED data.')
    return {'updated_at': pd.Timestamp.now(tz='UTC').isoformat(), 'points': points,
            'observed': observed, 'discovered_pm25_sensors': discovered, 'warnings': warnings,
            'source_type': 'modeled', 'provider': 'CAMS / Open-Meteo', 'assumptions': STATE_ASSUMPTIONS}


def save_context(payload, path=CACHE, region='maharashtra'):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix('.tmp')
    temp.write_text(json.dumps(payload, allow_nan=False))
    temp.replace(path)
    try:
        database.save_snapshot(region, payload)
    except Exception:
        LOG.warning('Could not persist %s provider snapshot to PostgreSQL.', region, exc_info=True)


class StateRuntime(Runtime):
    region_name = 'Maharashtra'
    region_id = 'maharashtra'
    bbox = STATE_BBOX
    grid_size = 24
    mask = staticmethod(inside_state)
    assumptions = STATE_ASSUMPTIONS
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

    def snapshot(self, replay_at=None):
        if replay_at:
            raise HTTPException(422, 'Historical held-out replay is available in the Pune + PCMC region only.')
        rows = self.frame[self.frame.timestamp == self.origin].dropna(subset=['pm25'])
        stations = []
        for row in rows.itertuples():
            point = self.points[row.station_id]
            pollutants = {key: {'value': float(getattr(row, 'pm25' if key == 'pm2_5' else key)),
                                  'unit': point['air_units'].get(key, ''), 'source_type': 'modeled',
                                  'timestamp': self.origin.isoformat()}
                          for key in AIR_FIELDS if pd.notna(getattr(row, 'pm25' if key == 'pm2_5' else key, None))}
            weather = {key: float(getattr(row, key)) for key in WEATHER_FIELDS if pd.notna(getattr(row, key, None))}
            stations.append({'id': row.station_id, 'name': f'{row.station_name} · CAMS reference',
                'short_name': row.station_name, 'latitude': row.latitude, 'longitude': row.longitude,
                'pm25': float(row.pm25), 'timestamp': self.origin.isoformat(), 'source_type': 'modeled',
                'assumptions': self.assumptions, 'pollutants': pollutants,
                'weather': {**weather, 'source_type': 'modeled', 'timestamp': self.origin.isoformat()}})
        if not stations:
            raise HTTPException(503, 'No valid CAMS points in provider cache')
        def weather_at(lat, lon):
            nearest = min(stations, key=lambda p: distance_km(lat, lon, p['latitude'], p['longitude']))
            return nearest['weather']
        weather = weather_at(18.52, 73.86)
        observed = [point for point in self.payload.get('observed', []) if (pd.Timestamp.now(tz=TIMEZONE) - pd.Timestamp(point['timestamp'])).total_seconds() <= 86400]
        interpolation_points = stations + [point for point in observed
            if pd.Timestamp(point['timestamp']).tz_convert(TIMEZONE).floor('h') == self.origin]
        cells, background = make_grid(interpolation_points, weather, self.origin, self.bbox, self.grid_size,
                                      self.mask, weather_at, spatial_inputs=self.spatial_inputs)
        for cell in cells:
            cell['assumptions'] = self.spatial_assumptions
        return stations + observed, cells, background, weather, self.origin

    def stations(self, replay_at=None):
        stations, _, _, weather, _ = self.snapshot(replay_at)
        age = max(0, (pd.Timestamp.now(tz=TIMEZONE) - self.origin).total_seconds() / 3600)
        warnings = [*self.warnings]
        if age > 6:
            warnings.append(f'CAMS context is {age:.0f} hours old. Provider updates do not guarantee real-time measurements.')
        return {'stations': stations, 'source_type': 'modeled', 'assumptions': self.assumptions,
            'warnings': warnings, 'data_mode': 'dated_cams_sample' if self.sample else 'refreshed_provider_cache',
            'weather': weather, 'zones': self.zones, 'zones_source_type': 'mapped' if self.spatial_inputs else 'illustrative',
            'region': {**region_metadata(self.region_id), 'forecast_provider': 'CAMS via Open-Meteo'},
            'coverage': {'modeled_points': len(self.points), 'observed_points': sum(p['source_type'] == 'observed' for p in stations),
                         'discovered_pm25_sensors': self.payload.get('discovered_pm25_sensors', 0),
                         'updated_at': self.payload['updated_at'], 'variables': AIR_FIELDS + WEATHER_FIELDS}}

    def location(self, location_id, replay_at=None):
        stations, cells, background, _, timestamp = self.snapshot(replay_at)
        found = next((p for p in stations if p['id'] == location_id), None)
        if found is None:
            cell = next((c for c in cells if c['id'] == location_id), None)
            if cell:
                found = {**cell, 'name': f'{self.region_name} grid {location_id}', 'short_name': 'Selected grid cell', 'timestamp': timestamp.isoformat()}
        if found is None:
            raise HTTPException(404, 'Unknown Maharashtra location')
        references = [p for p in stations if p['id'] in self.points]
        nearest = min(references, key=lambda p: distance_km(found['latitude'], found['longitude'], p['latitude'], p['longitude']))
        series = self.frame[self.frame.station_id == nearest['id']]
        return found, series, cells, background, nearest['weather'], timestamp, nearest['id']

    def forecast(self, location_id, hours=24, replay_at=None):
        _, history, _, _, _, timestamp, nearest = self.location(location_id, replay_at)
        future = self.all_frame[(self.all_frame.station_id == nearest) & (self.all_frame.timestamp > timestamp)].head(hours)
        future = future.dropna(subset=['pm25'])
        if len(future) < hours:
            raise HTTPException(503, 'CAMS cache lacks the requested horizon; refresh provider data.')
        points = [{'timestamp': row.timestamp.isoformat(), 'actual': float(row.pm25), 'predicted': None,
                   'p10': None, 'p90': None, 'persistence': None}
                  for row in history.tail(49).itertuples()]
        points += [{'timestamp': row.timestamp.isoformat(), 'actual': None, 'predicted': float(row.pm25),
                    'p10': None, 'p90': None, 'persistence': None} for row in future.itertuples()]
        return {'location_id': location_id, 'source_type': 'modeled', 'history_source_type': 'modeled',
            'history_reference': nearest, 'series': points, 'shap': None, 'weather_forecast': [
                {'timestamp': row.timestamp.isoformat(), 'source_type': 'modeled',
                 **{key: float(getattr(row, key)) for key in WEATHER_FIELDS if pd.notna(getattr(row, key, None))}}
                for row in future.itertuples()],
            'assumptions': [*self.assumptions, f'Forecast reference: {nearest}; origin: {timestamp.isoformat()}.',
                            'This is a CAMS provider forecast, not the locally validated LightGBM model. No calibrated p10/p90 bands or TreeSHAP are claimed.']}

    def backtest(self, location_id, replay_at=None):
        self.location(location_id, replay_at)
        return {'location_id': location_id, 'source_type': 'modeled', 'target_source_type': 'modeled',
                'series': [], 'metrics': None, 'available': False, 'method': 'Live CAMS provider forecast has no held-out local validation',
                'assumptions': ['Historical AirTwin backtests do not validate current CAMS provider forecasts.']}

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


class PuneRuntime(StateRuntime):
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

    def backtest(self, location_id, replay_at=None):
        result = super().backtest(location_id, replay_at)
        result['assumptions'].append('Use historical replay for the separate AirTwin model validation.')
        return result


_runtime = None
_lock = threading.Lock()
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
    if region == 'maharashtra':
        return get_state_runtime()
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
    save_context(payload, PUNE_CACHE, 'pcmc')
    with _pune_lock:
        _pune_runtime = runtime
    LOG.info('Pune refresh: %s modeled reference points; %s observed points',
             len(payload['points']), len(payload['observed']))

def get_state_runtime():
    global _runtime
    with _lock:
        if _runtime is None:
            database_payload = None
            try:
                database_payload = database.load_latest_snapshot('maharashtra')
            except Exception:
                LOG.warning('Could not load the Maharashtra snapshot from PostgreSQL; trying local caches.', exc_info=True)
            for path, payload in [(CACHE, database_payload), (CACHE, None), (SAMPLE, None)]:
                try:
                    if payload is None:
                        payload = json.loads(path.read_text())
                    _runtime = StateRuntime(payload, path == SAMPLE)
                    break
                except (OSError, ValueError, KeyError, TypeError):
                    continue
            if _runtime is None:
                raise HTTPException(503, 'Maharashtra cache and sample are unavailable. Run backend/scripts/fetch_state.py.')
        return _runtime


def refresh_state():
    global _runtime
    payload = fetch_context()
    runtime = StateRuntime(payload)
    runtime.snapshot()
    save_context(payload, region='maharashtra')
    with _lock:
        _runtime = runtime
    LOG.info('State refresh: %s modeled points; %s observed points', len(payload['points']), len(payload['observed']))


def live_loop(stop):
    interval = max(900, int(os.getenv('LIVE_REFRESH_SECONDS', '3600')))
    while not stop.is_set():
        try:
            refresh_pune()
        except (requests.RequestException, ValueError, KeyError, TypeError, HTTPException):
            LOG.warning('Pune provider refresh failed; retaining the last labeled cache.', exc_info=True)
            runtime = get_pune_runtime()
            if runtime:
                warning = 'Latest Pune provider refresh failed; showing the last cache with its original timestamp.'
                if warning not in runtime.warnings:
                    runtime.warnings.append(warning)
        try:
            refresh_state()
        except (requests.RequestException, ValueError, KeyError, TypeError, HTTPException):
            LOG.warning('State provider refresh failed; retaining the last labeled cache.')
            try:
                runtime = get_state_runtime()
                warning = 'Latest provider refresh failed; showing the last available cache with its original timestamp.'
                if warning not in runtime.warnings:
                    runtime.warnings.append(warning)
            except HTTPException:
                pass
        stop.wait(interval)
