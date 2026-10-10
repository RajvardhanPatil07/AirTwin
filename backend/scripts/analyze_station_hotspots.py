"""Write an exploratory Local Moran report for a simultaneous PCMC station snapshot."""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.config import ROOT
from app.services.data_loader import load_all
from app.services.local_moran import local_moran


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--offline', action='store_true')
    parser.add_argument('--permutations', type=int, default=999)
    parser.add_argument('--output', type=Path, default=ROOT / 'docs/evidence/station_local_moran.json')
    args = parser.parse_args()
    frame, warnings, fingerprint, _ = load_all(args.offline)
    counts = frame.groupby('timestamp').station_id.nunique()
    eligible = counts[counts >= 8]
    if eligible.empty:
        print('No simultaneous snapshot with eight stations; no Local Moran claim.', file=sys.stderr)
        return 2
    timestamp = eligible.index.max()
    rows = frame[frame.timestamp == timestamp].sort_values('station_id')
    stations = [{'id': str(row.station_id), 'name': row.station_name,
        'latitude': row.latitude, 'longitude': row.longitude, 'pm25': row.pm25}
        for row in rows.itertuples()]
    output = {'schema_version': 1, 'timestamp': timestamp.isoformat(),
        'dataset_fingerprint': fingerprint, 'target_sources': sorted(rows.source_type.unique().tolist()),
        'station_count': len(stations), 'method': {'neighbors': 3,
            'spatial_weights': 'three nearest stations, equal row-standardized weights',
            'permutations': args.permutations, 'seed': 42,
            'p_value': 'two-sided absolute deviation from conditional permutation mean, with +1 correction',
            'multiple_testing': 'Benjamini-Hochberg at q <= 0.05'},
        'limitations': ['Exploratory association among station points, not a citywide hotspot surface or source attribution.',
            'Sparse and uneven station locations limit geographic interpretation.',
            'Conditional permutations are descriptive; temporal dependence and sensor selection are not modeled.'],
        'warnings': warnings, 'stations': stations,
        'results': local_moran(stations, args.permutations)}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2, allow_nan=False) + '\n')
    flagged = [x for x in output['results'] if x['flagged_q_0_05']]
    lines = ['# Station Local Moran analysis', '',
        f"Shared hour: {output['timestamp']}; {len(stations)} stations; {len(flagged)} flagged after BH correction.",
        'This is exploratory station association, not a validated hotspot map or causal source estimate.', '',
        '| Station | PM2.5 | Quadrant | Local I | Raw p | BH q | Flagged |',
        '| --- | ---: | --- | ---: | ---: | ---: | --- |']
    for r in output['results']:
        lines.append(f"| {r['station_name']} ({r['station_id']}) | {r['pm25']:.1f} | {r['quadrant']} | {r['local_moran_i']:.3f} | {r['p_raw']:.3f} | {r['q_bh']:.3f} | {'yes' if r['flagged_q_0_05'] else 'no'} |")
    lines += ['', *['- ' + s for s in output['limitations']]]
    args.output.with_suffix('.md').write_text('\n'.join(lines) + '\n')
    print(f'Analyzed {len(stations)} stations; {len(flagged)} BH-flagged.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
