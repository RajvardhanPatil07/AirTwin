"""State boundary and approximate city sampling coordinates, not sensor locations."""
import json
from app.config import ROOT, BBOX, CITY_GRID_SIZE

STATE_BOUNDARY = json.loads((ROOT / 'data/maharashtra.geojson').read_text())
STATE_BBOX = (72.6, 15.6, 80.95, 22.1)
CITY_POINTS = [
    ('Mumbai', 19.07, 72.88), ('Pune', 18.52, 73.86), ('Pimpri-Chinchwad', 18.63, 73.80),
    ('Nagpur', 21.14, 79.08), ('Nashik', 19.99, 73.79), ('Thane', 19.20, 72.97),
    ('Palghar', 19.70, 72.77), ('Raigad / Alibag', 18.64, 72.87), ('Ratnagiri', 16.99, 73.31),
    ('Sindhudurg / Oros', 16.10, 73.70), ('Kolhapur', 16.70, 74.24), ('Sangli', 16.85, 74.58),
    ('Satara', 17.68, 74.00), ('Solapur', 17.65, 75.91), ('Ahilyanagar', 19.09, 74.74),
    ('Chhatrapati Sambhajinagar', 19.88, 75.34), ('Jalna', 19.83, 75.88), ('Beed', 18.99, 75.76),
    ('Dharashiv', 18.18, 76.04), ('Latur', 18.40, 76.57), ('Nanded', 19.14, 77.32),
    ('Parbhani', 19.27, 76.77), ('Hingoli', 19.71, 77.15), ('Jalgaon', 21.01, 75.57),
    ('Dhule', 20.90, 74.77), ('Nandurbar', 21.37, 74.24), ('Buldhana', 20.53, 76.18),
    ('Akola', 20.70, 77.00), ('Washim', 20.11, 77.13), ('Amravati', 20.94, 77.75),
    ('Yavatmal', 20.39, 78.13), ('Wardha', 20.75, 78.60), ('Bhandara', 21.17, 79.65),
    ('Gondia', 21.46, 80.20), ('Chandrapur', 19.96, 79.30), ('Gadchiroli', 20.18, 80.00),
]


def in_ring(lon, lat, ring):
    inside = False
    previous = ring[-1]
    for point in ring:
        x, y = point[:2]
        px, py = previous[:2]
        if (y > lat) != (py > lat) and lon < (px - x) * (lat - y) / (py - y) + x:
            inside = not inside
        previous = point
    return inside


def inside_state(lat, lon):
    geometry = STATE_BOUNDARY['features'][0]['geometry']
    polygons = geometry['coordinates'] if geometry['type'] == 'MultiPolygon' else [geometry['coordinates']]
    return any(in_ring(lon, lat, polygon[0]) and not any(in_ring(lon, lat, hole) for hole in polygon[1:])
               for polygon in polygons)


def region_metadata(region):
    bbox = STATE_BBOX if region == 'maharashtra' else BBOX
    west, south, east, north = bbox
    return {'id': region, 'name': 'Maharashtra' if region == 'maharashtra' else 'Pune + PCMC',
            'bounds': [[south, west], [north, east]], 'grid_size': 24 if region == 'maharashtra' else CITY_GRID_SIZE,
            'boundary': STATE_BOUNDARY if region == 'maharashtra' else None,
            'forecast_provider': 'CAMS via Open-Meteo' if region == 'maharashtra' else 'AirTwin LightGBM'}
