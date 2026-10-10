"""Stress-test action rankings with independent source and response assumptions."""
import argparse
from collections import Counter
from itertools import product
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'backend'))
from app.services.scenarios import delta, NAMES


def stress_rankings(cells, cuts, source_factors, responses):
    total = sum(c['population'] for c in cells)
    if not cells or total <= 0:
        raise ValueError('Need cells with positive population weight')
    actions = list(NAMES)
    profiles = {'configured': [c['population'] for c in cells],
                'uniform': [1. for c in cells],
                'inverse_density': [1 / max(c['population'], 1) for c in cells]}
    profiles = {name: [v * total / sum(values) for v in values] for name, values in profiles.items()}
    counts, examples, margins = Counter(), {}, []
    central = {a: sum(delta(c['pm25'], c['background'], c['local_weights'],
                           {k: cuts[k] if k == a else 0 for k in actions}) * c['population'] for c in cells)
               for a in actions}
    for factors in product(source_factors, repeat=3):
        weights = []
        for c in cells:
            raw = {a: c['local_weights'][a] * f for a, f in zip(actions, factors)}
            denominator = sum(raw.values())
            if denominator <= 0:
                raise ValueError('Source multipliers must preserve positive total weight')
            weights.append({a: raw[a] / denominator for a in actions})
        for response in product(responses, repeat=3):
            reductions = {a: [delta(c['pm25'], c['background'], w,
                                    {k: cuts[k] if k == a else 0 for k in actions}, p)
                              for c, w in zip(cells, weights)] for a, p in zip(actions, response)}
            for profile, population in profiles.items():
                scores = {a: sum(d * n for d, n in zip(reductions[a], population)) for a in actions}
                ordered = sorted(scores, key=lambda a: -scores[a])
                margin = scores[ordered[0]] - scores[ordered[1]]
                winner = ordered[0] if scores[ordered[0]] > 1e-9 and margin > 1e-9 else 'tie_or_zero'
                counts[winner] += 1
                margins.append(margin)
                examples.setdefault(winner, {'source_multipliers': dict(zip(actions, factors)),
                                             'pass_through': dict(zip(actions, response)),
                                             'population_profile': profile, 'scores': scores})
    central_order = sorted(central, key=lambda a: -central[a])
    central_leader = central_order[0] if central[central_order[0]] > 1e-9 and central[central_order[0]] - central[central_order[1]] > 1e-9 else None
    return {'cuts_percent': cuts, 'central_scores': central, 'central_leader': central_leader,
            'source_factors': source_factors, 'independent_response_factors': responses,
            'scenario_count': sum(counts.values()), 'winner_counts': dict(counts),
            'ranking_changed': bool(central_leader and any(k != central_leader for k in counts)),
            'minimum_top_two_margin': min(margins), 'examples': examples}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--offline', action='store_true')
    parser.add_argument('--output', type=Path, default=ROOT / 'docs/evidence/intervention_sensitivity.json')
    args = parser.parse_args()
    from app.services.data_loader import load_all
    from app.services.runtime import Runtime
    from app.services.spatial_inputs import load_spatial_inputs
    frame, warnings, fingerprint, _ = load_all(args.offline)
    # Snapshot construction needs only the frame, not model training or API credentials.
    snapshot = Runtime.__new__(Runtime)
    snapshot.frame = frame
    snapshot.warnings = warnings
    snapshot.spatial_inputs = None if args.offline else load_spatial_inputs()
    stations, cells, _, _, timestamp = snapshot.snapshot()
    selected = next((s for s in stations if 'bhosari' in s['name'].lower()), None)
    cases = []
    for label, cuts in [('demo', {'traffic': 20, 'industry': 30, 'dust': 30}),
                        ('equal_cuts', {'traffic': 30, 'industry': 30, 'dust': 30})]:
        for scope, factors, responses in [('configured_range', [0.8, 1., 1.2], [0.6, 0.7, 0.8]),
                                           ('wide_stress', [0.5, 1., 1.5], [0., 0.7, 1.])]:
            cases.append({'case': label, 'scope': scope, **stress_rankings(cells, cuts, factors, responses)})
    report = {'dataset_fingerprint': fingerprint, 'snapshot': timestamp.isoformat(),
              'demo_location': selected, 'target_sources': sorted(frame.source_type.unique()),
              'warnings': warnings,
              'population_provenance': cells[0]['population_source_type'],
              'population_source': snapshot.spatial_inputs.get('population_source') if snapshot.spatial_inputs else None,
              'zone_source': snapshot.spatial_inputs.get('zone_source') if snapshot.spatial_inputs else None,
              'cases': cases,
              'limitations': [
                  'Ranges are assumed stress tests, not empirically sourced response coefficients or confidence intervals.',
                  'Configured-range testing varies each source and response independently; existing UI bounds use aggregate scaling.',
                  'Winner counts describe an arbitrary finite grid, not probabilities of policy success.',
                  'Scores cover the Pune-PCMC grid; selecting Bhosari does not make them Bhosari-only benefits.',
                  'Geometry, meteorology and background are fixed. Equal cuts do not imply equal cost or feasibility.',
                  'No causal concentration reduction, demographic count or health benefit is validated.']}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, allow_nan=False) + '\n')
    lines = ['# Intervention ranking stress test', '', f'Snapshot: {report["snapshot"]}.',
             f'Dataset fingerprint: `{fingerprint}`.', '',
             '| Cuts | Assumption range | Central leader | Cases | Winners (counts, not probabilities) | Changed |',
             '| --- | --- | --- | --- | --- | --- |']
    for c in cases:
        lines.append(f'| {c["case"]} | {c["scope"]} | {c["central_leader"]} | {c["scenario_count"]} | {c["winner_counts"]} | {c["ranking_changed"]} |')
    lines += ['', '## Interpretation', '',
              'A ranking change provides a concrete counterexample to a universal winner claim.',
              'No change establishes agreement only on this finite grid of assumptions.',
              'The JSON records an example parameter combination for every winner or tie.', '',
              *[f'- {v}' for v in report['limitations']], '',
              'Category evidence and parameter status: [intervention evidence](../intervention_evidence.md).']
    args.output.with_suffix('.md').write_text('\n'.join(lines) + '\n')
    print(json.dumps({'output': str(args.output), 'cases': len(cases), 'bhosari_available': selected is not None}))


if __name__ == '__main__':
    main()
