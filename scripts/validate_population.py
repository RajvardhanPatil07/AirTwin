"""Compare intervention rankings under alternative synthetic population profiles."""
import argparse
import json
from pathlib import Path
import urllib.request


def population_sensitivity(cells, results):
    total = sum(cell['population'] for cell in cells)
    profiles = {'configured_synthetic': [cell['population'] for cell in cells],
                'uniform_synthetic': [1.0 for _ in cells],
                'edge_weighted_synthetic': [1 / max(cell['population'], 1) for cell in cells]}
    rows = []
    for name, weights in profiles.items():
        weights = [value * total / sum(weights) for value in weights]
        scores = []
        for result in results:
            after = {cell['id']: cell['pm25'] for cell in result['cells']}
            score = sum((cell['pm25'] - after[cell['id']]) * weight
                        for cell, weight in zip(cells, weights))
            scores.append({'action': result['id'], 'exposure_index': score})
        scores.sort(key=lambda item: -item['exposure_index'])
        individuals = [row for row in scores if row['action'] != 'combined']
        rows.append({'profile': name, 'total_synthetic_weight': total, 'scores': scores,
                     'leading_individual': individuals[0]['action'] if individuals[0]['exposure_index'] > 0 else None})
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--url', default='http://127.0.0.1:8000')
    parser.add_argument('--output', type=Path, default=Path('docs/evidence/population_sensitivity.json'))
    args = parser.parse_args()
    def request(path, body=None):
        req = urllib.request.Request(args.url.rstrip('/') + '/api/' + path,
                                     data=json.dumps(body).encode() if body else None,
                                     headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(req, timeout=180) as response:
            return json.load(response)
    health = request('health')
    stations = request('stations')['stations']
    cells = request('hotspots?mode=before')['cells']
    cuts = {'traffic': 20, 'industry': 30, 'dust': 30}
    scenario = request('scenarios', {'location_id': stations[0]['id'], 'cuts': cuts})
    rows = population_sensitivity(cells, scenario['results'])
    report = {'dataset_fingerprint': health['fingerprint'], 'snapshot': health['last_dataset_time'],
              'target_sources': health['target_source_types'], 'cuts_percent': cuts,
              'population_provenance': 'synthetic', 'profiles': rows,
              'ranking_changed': len({row['leading_individual'] for row in rows}) > 1,
              'limitations': 'Fixed meteorology, geometry, source proxies and cuts. All three population profiles are hypothetical, normalized to the same synthetic total. No demographic, causal or health validation.'}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, allow_nan=False) + '\n')
    lines = ['# Synthetic population sensitivity', '', f'Snapshot: {report["snapshot"]}.',
             f'Dataset fingerprint: `{report["dataset_fingerprint"]}`.',
             'Cuts: traffic 20%, industry 30%, dust 30%.', '',
             '| Population assumption | Leading individual action | Traffic index | Industry index | Dust index |',
             '| --- | --- | --- | --- | --- |']
    for row in rows:
        scores = {score['action']: score['exposure_index'] for score in row['scores']}
        lines.append(f'| {row["profile"]} | {row["leading_individual"]} | {scores["traffic"]:.0f} | {scores["industry"]:.0f} | {scores["dust"]:.0f} |')
    lines += ['', 'Index units: synthetic person·µg/m³. These are comparative weights, not people protected.',
              'Uniform assigns equal weight to each cell. Edge-weighted uses inverse configured population, then rescales to the same total.',
              f'Leading action changed across these profiles: {report["ranking_changed"]}.',
              'Agreement across three profiles does not establish robustness to every population distribution.',
              '', report['limitations']]
    args.output.with_suffix('.md').write_text('\n'.join(lines) + '\n')
    print(json.dumps({'ranking_changed': report['ranking_changed'], 'output': str(args.output)}))


if __name__ == '__main__':
    main()
