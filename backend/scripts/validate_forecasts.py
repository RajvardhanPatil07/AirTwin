"""Write reproducible seasonal holdouts and a delayed pollution-only input ablation."""
import argparse
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.config import ROOT
from app.services.data_loader import load_all
from app.services.validation import validate


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--offline', action='store_true')
    parser.add_argument('--horizons', type=int, nargs='+', default=[6, 24, 72])
    parser.add_argument('--policies', nargs='+', choices=['retrospective', 'pollution_only'],
                        default=['retrospective', 'pollution_only'])
    parser.add_argument('--latency-hours', type=int, default=1)
    parser.add_argument('--output', type=Path, default=ROOT / 'docs/evidence/seasonal_validation.json')
    args = parser.parse_args()
    if args.latency_hours < 0 or any(h <= 0 for h in args.horizons):
        parser.error('Horizons must be positive; latency must be nonnegative')
    frame, warnings, fingerprint, exog = load_all(args.offline)
    results, skipped = validate(frame, exog, args.horizons, args.policies, args.latency_hours)
    report = {'dataset_fingerprint': fingerprint, 'dataset_start': frame.timestamp.min().isoformat(),
              'dataset_end': frame.timestamp.max().isoformat(), 'warnings': warnings,
              'latency_hours': args.latency_hours, 'results': results, 'skipped': skipped,
              'limitations': [
                  'Retrospective inputs retain archived CAMS and reanalysis availability limitations.',
                  'Pollution-only excludes all weather, CAMS and boundary-layer inputs; sensor publication delay is assumed, not verified.',
                  'These are separately refitted evaluation models, not the serving-model metrics.',
                  'Seasonal mean means a training-only target-hour average, not a climatology fitted to multiple years.',
                  'Missing targets are not imputed; sparse valid pairs may underrepresent difficult hours.',
                  'No causal intervention, health benefit or statewide accuracy is established.']}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, allow_nan=False) + '\n')
    lines = ['# Seasonal forecast validation', '',
             f'Dataset: {report["dataset_start"]} to {report["dataset_end"]}.',
             f'Fingerprint: `{fingerprint}`.', '',
             f'Pollution-only assumes {args.latency_hours} hour(s) of sensor publication delay.',
             'Errors are µg/m³; positive skill means lower MAE than persistence.', '',
             '| Inputs | Season | Horizon | Train / test pairs | MAE | RMSE | Persistence MAE | Hourly mean MAE | Skill | Band coverage |',
             '| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |']
    for row in results:
        lines.append(f'| {row["policy"]} | {row["season"]} | {row["horizon"]}h | {row["train_rows"]} / {row["test_rows"]} | '
                     f'{row["mae"]:.2f} | {row["rmse"]:.2f} | {row["persistence_mae"]:.2f} | {row["seasonal_mae"]:.2f} | '
                     f'{row["improvement_percent"]:+.1f}% | {row["interval_coverage"]:.1f}% |')
    lines += ['', '## Interpretation and limits', '', *[f'- {item}' for item in report['limitations']],
              *[f'- {item}' for item in warnings], '', '## Skipped evaluations', '',
              *[f'- {r["policy"]}, {r["season"]}, {r["horizon"]}h: {r["reason"]}.' for r in skipped],
              '', 'Exact boundaries, input features, provenance and results are in the adjacent JSON file.',
              'A failed baseline comparison remains a reported result; it is not removed from this table.']
    args.output.with_suffix('.md').write_text('\n'.join(lines) + '\n')
    if not results:
        print('No complete seasonal evaluation available; no forecast skill established.', file=sys.stderr)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
