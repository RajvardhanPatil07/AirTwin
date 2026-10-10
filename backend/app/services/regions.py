"""State boundary and approximate city sampling coordinates, not sensor locations."""
import json
from app.config import ROOT, BBOX

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

# Named sampling coordinates across the Pune–PCMC map. They are model reference
# locations, never a claim that a monitor exists at each place.
PUNE_POINTS = [
    ('Shivajinagar', 18.5308, 73.8475), ('Deccan', 18.5167, 73.8414),
    ('Kothrud', 18.5074, 73.8077), ('Aundh', 18.5580, 73.8075),
    ('Baner', 18.5590, 73.7868), ('Balewadi', 18.5791, 73.7686),
    ('Pashan', 18.5417, 73.7928), ('Wakad', 18.5978, 73.7607),
    ('Hinjawadi', 18.5913, 73.7389), ('Ravet', 18.6517, 73.7482),
    ('Nigdi', 18.6607, 73.7715), ('Akurdi', 18.6519, 73.7827),
    ('Chinchwad', 18.6298, 73.7997), ('Pimpri', 18.6186, 73.8020),
    ('Pimple Saudagar', 18.5984, 73.7998), ('Bhosari', 18.6212, 73.8487),
    ('Moshi', 18.6754, 73.8506), ('Chakan', 18.7606, 73.8636),
    ('Yerawada', 18.5521, 73.8870), ('Kalyani Nagar', 18.5481, 73.9030),
    ('Viman Nagar', 18.5679, 73.9143), ('Hadapsar', 18.5089, 73.9259),
    ('Magarpatta', 18.5157, 73.9308), ('Kondhwa', 18.4777, 73.8907),
    ('Katraj', 18.4575, 73.8373),
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
            'bounds': [[south, west], [north, east]], 'grid_size': 24 if region == 'maharashtra' else 12,
            'boundary': STATE_BOUNDARY if region == 'maharashtra' else None,
            'forecast_provider': 'CAMS via Open-Meteo' if region == 'maharashtra' else 'AirTwin LightGBM'}
