"""IDW and explicitly assumed source/population proxies."""
import json
import math
import numpy as np
import yaml
from app.config import ROOT, BBOX

CONFIG = yaml.safe_load((ROOT / 'config/assumptions.yaml').read_text())
ZONES = json.loads((ROOT / 'data/zones.geojson').read_text())
ASSUMPTIONS = [
    'Grid PM2.5 is IDW interpolation (power 2), not additional station observations.',
    'Regional background is the 15th percentile of a simultaneous station snapshot, capped at cell concentration.',
    'Source shares use hand-drawn zone proximity, assumed traffic profiles and weather proxies; they are not chemical source apportionment.',
    'Industrial upwind weighting uses meteorological wind-from direction; zone coordinates and activity are approximate.',
    'Emission-to-concentration pass-through is 0.7 (sensitivity 0.6–0.8 with ±20% source scaling). Weather is held fixed.',
    'Population weights are SYNTHETIC, not WorldPop; exposure benefit is person·µg/m³, not people protected.',
]


def distance_km(lat, lon, other_lat, other_lon):
    return 111.32 * math.hypot(lat - other_lat, (lon - other_lon) * math.cos(math.radians(lat)))


def idw(lat, lon, stations):
    distances = np.array([distance_km(lat, lon, s['latitude'], s['longitude']) for s in stations])
    if distances.min() < 1e-6:
        return float(stations[int(distances.argmin())]['pm25'])
    weights = 1 / distances ** CONFIG['idw_power']
    return float(np.dot(weights, [s['pm25'] for s in stations]) / weights.sum())


def bearing(lat, lon, other_lat, other_lon):
    return math.degrees(math.atan2((other_lon - lon) * math.cos(math.radians(lat)), other_lat - lat)) % 360


def zone_center(feature):
    geometry = feature['geometry']
    coords = geometry['coordinates'][0][:-1] if geometry['type'] == 'Polygon' else geometry['coordinates']
    return float(np.mean([c[1] for c in coords])), float(np.mean([c[0] for c in coords]))


def local_weights(lat, lon, hour, weather):
    traffic = CONFIG['traffic']['base']
    industry = CONFIG['industry']['base']
    dust = CONFIG['dust']['base']
    humidity = weather.get('relative_humidity_2m', 60) or 60
    rain = weather.get('precipitation', 0) or 0
    wind_from = weather.get('wind_direction_10m')
    dryness = max(0.1, 1 - humidity / 100) * (0.2 if rain > 0 else 1)
    for feature in ZONES['features']:
        zlat, zlon = zone_center(feature)
        distance = distance_km(lat, lon, zlat, zlon)
        category = feature['properties']['category']
        if category == 'industry':
            angle = bearing(lat, lon, zlat, zlon)
            upwind = 1 if wind_from is None else max(0, math.cos(math.radians(angle - wind_from)))
            upwind = max(CONFIG['industry']['minimum_wind_weight'], upwind)
            industry += CONFIG['industry']['strength'] * math.exp(-distance / CONFIG['industry']['scale_km']) * upwind
        elif category == 'traffic':
            coords = feature['geometry']['coordinates']
            closest = min(distance_km(lat, lon, p[1], p[0]) for p in coords)
            traffic += CONFIG['traffic']['corridor_strength'] * math.exp(-closest / 3)
        elif category == 'dust':
            dust += CONFIG['dust']['strength'] * math.exp(-distance / CONFIG['dust']['scale_km']) * dryness
    if hour in CONFIG['traffic']['peak_hours']:
        traffic *= CONFIG['traffic']['peak_multiplier']
    total = traffic + industry + dust
    return {'traffic': traffic / total, 'industry': industry / total, 'dust': dust / total}


def make_grid(stations, weather, timestamp, bbox=BBOX, grid_size=12, mask=None, weather_at=None):
    west, south, east, north = bbox
    background = float(np.percentile([s['pm25'] for s in stations], CONFIG['background_percentile']))
    population = CONFIG['population']
    cells = []
    for row in range(grid_size):
        for col in range(grid_size):
            a, b = south + row * (north - south) / grid_size, west + col * (east - west) / grid_size
            c, d = a + (north - south) / grid_size, b + (east - west) / grid_size
            lat, lon = (a + c) / 2, (b + d) / 2
            if mask and not mask(lat, lon):
                continue
            value = idw(lat, lon, stations)
            density = math.exp(-((lat - population['latitude']) ** 2 + (lon - population['longitude']) ** 2) / population['scale_degrees_squared'])
            cells.append({'id': f'cell-{row}-{col}', 'latitude': lat, 'longitude': lon,
                          'bounds': [[a, b], [c, d]], 'pm25': value, 'background': min(background, value),
                          'population': round(population['base'] + population['core_extra'] * density),
                          'population_source_type': 'synthetic', 'local_weights': local_weights(lat, lon, timestamp.hour, weather_at(lat, lon) if weather_at else weather),
                          'source_type': 'modeled', 'assumptions': ASSUMPTIONS})
    return cells, background
