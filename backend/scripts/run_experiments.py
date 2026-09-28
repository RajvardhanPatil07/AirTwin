"""Run paired forecast/ablation/interval benchmarks without overwriting serving artifacts."""
import argparse
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.config import ROOT
from app.services.data_loader import load_all
from app.services.experiments import ARMS, environment, run_experiments, verify_reference, write_report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--offline', action='store_true')
    parser.add_argument('--horizons', nargs='+', type=int, default=[6, 24, 72])
    parser.add_argument('--policies', nargs='+', choices=['retrospective', 'pollution_only'], default=['retrospective', 'pollution_only'])
    parser.add_argument('--arms', nargs='+', choices=ARMS, default=list(ARMS))
    parser.add_argument('--alpha', type=float, default=.2)
    parser.add_argument('--n-estimators', type=int, default=300)
    parser.add_argument('--latency-hours', type=int, default=1)
    parser.add_argument('--max-windows', type=int)
    parser.add_argument('--no-challenger', action='store_true')
    parser.add_argument('--output', type=Path, default=ROOT / 'docs/evidence/paired_experiments.json')
    parser.add_argument('--verify', type=Path, help='Compare to an existing reference; never update it')
    parser.add_argument('--tolerance', type=float, default=1e-8)
    args = parser.parse_args()
    if (any(h <= 0 for h in args.horizons) or not 0 < args.alpha < 1 or args.n_estimators < 1 or
            args.latency_hours < 0 or args.tolerance < 0 or (args.max_windows is not None and args.max_windows < 1)):
        parser.error('Invalid horizon, alpha, estimator count, latency, tolerance or window count')
    if args.verify and args.verify.resolve() == args.output.resolve():
        parser.error('Verification output must differ from the reference')
    frame, warnings, fingerprint, exog = load_all(args.offline)
    protocol = {k: getattr(args, k) for k in ('offline', 'horizons', 'policies', 'arms', 'alpha',
        'n_estimators', 'latency_hours', 'max_windows', 'no_challenger')}
    protocol['lookback_embargo_hours'] = 48
    sources = [ROOT / 'backend/app/services' / name for name in ('experiments.py', 'features.py', 'model.py', 'validation.py')]
    report = {'schema_version': 1, 'dataset_fingerprint': fingerprint, 'protocol': protocol,
        'code_fingerprints': {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
        'environment': environment(), 'dataset_start': frame.timestamp.min().isoformat(),
        'dataset_end': frame.timestamp.max().isoformat(), 'warnings': warnings,
        'limitations': [
            'No serving model or uncertainty band is automatically promoted from these experiments.',
            'Windows were previously inspected: results are development evidence, not a new blind test.',
            'Retrospective weather/CAMS do not establish operational issue-time availability.',
            'Pollution-only assumes sensor latency; it does not verify provider publication times.',
            'Temporal dependence and seasonal shifts invalidate unconditional conformal coverage claims.',
            'No headline winner is selected from test results. Fix a future promotion protocol before a new evaluation period.',
            'Missing targets are excluded; aggregate metrics can hide episode/station failures.',
            'Environment and code/data hashes are checked; independent-machine reproducibility remains unverified.']}
    report['results'], report['skipped'] = run_experiments(frame, exog, args.horizons, args.policies,
        args.arms, args.alpha, args.n_estimators, args.latency_hours, args.max_windows, not args.no_challenger)
    write_report(report, args.output)
    if not report['results']:
        print('No evaluable folds; no evidence established.', file=sys.stderr)
        return 2
    if args.verify:
        differences = verify_reference(json.loads(args.verify.read_text()), report, args.tolerance)
        if differences:
            print('\n'.join(differences[:30]), file=sys.stderr)
            return 1
        print(f'Reproduction verified with absolute tolerance {args.tolerance:g}.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
