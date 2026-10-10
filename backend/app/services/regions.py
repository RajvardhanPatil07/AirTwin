"""Bounded Pune–PCMC urban model reference locations, not sensors."""
from app.config import BBOX

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


def inside_pune(lat, lon):
    return BBOX[1] <= lat <= BBOX[3] and BBOX[0] <= lon <= BBOX[2]


def region_metadata(region='pcmc'):
    if region != 'pcmc':
        raise ValueError('Only Pune + PCMC is supported')
    west,south,east,north=BBOX
    return {'id':'pcmc','name':'Pune + PCMC','bounds':[[south,west],[north,east]],
            'grid_size':12,'boundary':None,'forecast_provider':'CAMS via Open-Meteo'}
