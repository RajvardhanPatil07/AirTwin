"""Validated optional spatial inputs and count-conserving raster aggregation."""
import json
import math
from functools import lru_cache

from app.config import BBOX, ROOT

SPATIAL_PATH = ROOT / 'data/processed/spatial_inputs.json'
SAMPLE_SPATIAL_PATH = ROOT / 'data/sample/spatial_inputs.json'


def latitude_measure(south, north):
    return math.sin(math.radians(north)) - math.sin(math.radians(south))


def rectangle_overlap_fraction(pixel, cell):
    west, south, east, north = pixel
    cwest, csouth, ceast, cnorth = cell
    lo_lon, hi_lon = max(west, cwest), min(east, ceast)
    lo_lat, hi_lat = max(south, csouth), min(north, cnorth)
    if lo_lon >= hi_lon or lo_lat >= hi_lat:
        return 0.
    return ((hi_lon - lo_lon) * latitude_measure(lo_lat, hi_lat) /
            ((east - west) * latitude_measure(south, north)))


def aggregate_pixels(pixels, bbox=BBOX, grid_size=12):
    """Split each WGS84 source pixel among intersecting cells by spherical area."""
    west, south, east, north = bbox
    counts = [0.] * (grid_size * grid_size)
    for pixel, value in pixels:
        if not math.isfinite(value) or value < 0:
            continue
        for row in range(grid_size):
            a = south + (north - south) * row / grid_size
            c = south + (north - south) * (row + 1) / grid_size
            for col in range(grid_size):
                b = west + (east - west) * col / grid_size
                d = west + (east - west) * (col + 1) / grid_size
                fraction = rectangle_overlap_fraction(pixel, (b, a, d, c))
                if fraction:
                    counts[row * grid_size + col] += value * fraction
    floors = [math.floor(value) for value in counts]
    remaining = round(sum(counts)) - sum(floors)
    order = sorted(range(len(counts)), key=lambda i: (-(counts[i] - floors[i]), i))
    for i in order[:remaining]:
        floors[i] += 1
    return floors, sum(counts)


@lru_cache(maxsize=1)
def load_spatial_inputs():
    path = SPATIAL_PATH if SPATIAL_PATH.exists() else SAMPLE_SPATIAL_PATH
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text())
        if data['schema_version'] != 1 or data['bbox'] != list(BBOX) or data['grid_size'] != 12:
            raise ValueError('Spatial grid specification differs')
        counts = data['population_counts']
        if len(counts) != 144 or any(type(v) is not int or v < 0 for v in counts):
            raise ValueError('Invalid population counts')
        if data['population_source']['year'] != 2020 or not data['population_source']['sha256']:
            raise ValueError('Missing population provenance')
        zones = data.get('zones')
        if zones is not None and (zones.get('type') != 'FeatureCollection' or
                                  not isinstance(zones.get('features'), list)):
            raise ValueError('Invalid zone collection')
        return data
    except (ValueError, KeyError, TypeError, OSError):
        return None
