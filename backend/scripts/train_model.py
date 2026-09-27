"""Regenerate ignored models and an honest model card from available data."""
import argparse
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.config import ROOT
from app.services.data_loader import load_all
from app.services.model import train

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--offline', action='store_true')
    args = parser.parse_args()
    frame, warnings, fingerprint, exog = load_all(args.offline)
    artifact = train(frame, fingerprint, warnings, ROOT / 'docs/model_card.md', exog=exog)
    report = artifact['report']
    print(report['method'], '·', report['model'])
    for row in report['skill']:
        print(f"h={row['horizon']:>2}  MAE {row['mae']:.2f}  persistence {row['persistence_mae']:.2f}  "
              f"improvement {row['improvement_percent']:+.1f}%  coverage {row['interval_coverage']:.1f}%  weight {row['blend_weight']}")
    for warning in warnings:
        print('WARNING:', warning)
