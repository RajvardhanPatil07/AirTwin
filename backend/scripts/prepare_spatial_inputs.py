"""Aggregate the verified WorldPop raster and optional OSM extract for PCMC."""
import argparse
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.config import BBOX, ROOT
from app.services.spatial_inputs import aggregate_pixels

WORLDPOP_URL = ('https://data.worldpop.org/GIS/Population/Global_2000_2020_1km_UNadj/'
                '2020/IND/ind_ppp_2020_1km_Aggregated_UNadj.tif')


def read_pixels(path):
    import rasterio
    from rasterio.windows import from_bounds, transform
    with rasterio.open(path) as raster:
        if str(raster.crs) != 'EPSG:4326' or raster.count != 1:
            raise ValueError('Expected single-band EPSG:4326 WorldPop raster')
        window = from_bounds(*BBOX, transform=raster.transform).round_offsets().round_lengths()
        values = raster.read(1, window=window, masked=True)
        affine = transform(window, raster.transform)
        for row in range(values.shape[0]):
            for col in range(values.shape[1]):
                if values.mask[row, col]:
                    continue
                west, north = affine * (col, row)
                east, south = affine * (col + 1, row + 1)
                yield (west, south, east, north), float(values[row, col])


def osm_zones(path):
    source = json.loads(path.read_text())
    buckets = {}
    for element in source.get('elements', []):
        if element.get('type') != 'way' or len(element.get('geometry', [])) < 2:
            continue
        tags = element.get('tags', {})
        if tags.get('landuse') == 'industrial':
            category = 'industry'
        elif tags.get('landuse') == 'construction':
            category = 'dust'
        elif tags.get('highway') in ('primary', 'trunk', 'secondary'):
            category = 'traffic'
        else:
            continue
        coordinates = [[point['lon'], point['lat']] for point in element['geometry']]
        if any(not (BBOX[0] - .1 <= lon <= BBOX[2] + .1 and BBOX[1] - .1 <= lat <= BBOX[3] + .1)
               for lon, lat in coordinates):
            continue
        center_lon = sum(p[0] for p in coordinates) / len(coordinates)
        center_lat = sum(p[1] for p in coordinates) / len(coordinates)
        col = min(3, max(0, int(4 * (center_lon - BBOX[0]) / (BBOX[2] - BBOX[0]))))
        row = min(3, max(0, int(4 * (center_lat - BBOX[1]) / (BBOX[3] - BBOX[1]))))
        length = sum(((coordinates[i][0] - coordinates[i - 1][0]) ** 2 +
                       (coordinates[i][1] - coordinates[i - 1][1]) ** 2) ** .5
                     for i in range(1, len(coordinates)))
        feature = {'type': 'Feature', 'properties': {'category': category, 'osm_id': element['id']},
            'geometry': {'type': 'LineString', 'coordinates': coordinates}}
        buckets.setdefault((category, row, col), []).append((length, feature))
    features = [item[1] for key in sorted(buckets) for item in
                sorted(buckets[key], key=lambda pair: (-pair[0], pair[1]['properties']['osm_id']))[:2]]
    return {'type': 'FeatureCollection', 'features': features}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--raster', type=Path, default=ROOT / 'data/raw/worldpop_ind_ppp_2020_1km_unadj.tif')
    parser.add_argument('--osm', type=Path)
    parser.add_argument('--output', type=Path, default=ROOT / 'data/processed/spatial_inputs.json')
    args = parser.parse_args()
    counts, total = aggregate_pixels(read_pixels(args.raster))
    data = {'schema_version': 1, 'bbox': list(BBOX), 'grid_size': 12, 'population_counts': counts,
        'population_fractional_total': total,
        'population_source': {'name': 'WorldPop India 2020 1km UN-adjusted', 'year': 2020,
            'source_type': 'modeled', 'url': WORLDPOP_URL,
            'sha256': hashlib.sha256(args.raster.read_bytes()).hexdigest(),
            'license': 'CC BY 4.0', 'method': 'Spherical-area overlap; largest-remainder integer counts'}}
    if args.osm:
        raw_osm = json.loads(args.osm.read_text())
        data['zones'] = osm_zones(args.osm)
        data['zone_source'] = {'name': 'OpenStreetMap via Overpass', 'url': 'https://www.openstreetmap.org/copyright',
            'source_type': 'mapped', 'sha256': hashlib.sha256(args.osm.read_bytes()).hexdigest(),
            'osm_data_timestamp': raw_osm.get('osm3s', {}).get('timestamp_osm_base'),
            'license': 'ODbL 1.0',
            'method': 'Mapped industrial/construction landuse and major roads; two longest ways per category and 4x4 tile. Proxy weights remain assumed'}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(data, indent=2) + '\n')
    print(f'Wrote {args.output}; rounded population {sum(counts)}; fractional {total:.2f}; '
          f'OSM features {len(data.get("zones", {}).get("features", []))}')


if __name__ == '__main__':
    main()
