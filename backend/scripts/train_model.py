"""Regenerate ignored models and an honest model card from available data."""
import argparse
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.config import ROOT
from app.services.data_loader import load_dataset
from app.services.model import train

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--offline', action='store_true')
    args = parser.parse_args()
    frame, warnings, fingerprint = load_dataset(args.offline)
    artifact = train(frame, fingerprint, warnings, ROOT / 'docs/model_card.md')
    print(artifact['report']['method'])
    print(artifact['report']['metrics'])
    for warning in warnings:
        print('WARNING:', warning)
