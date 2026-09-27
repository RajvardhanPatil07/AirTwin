import sys
from pathlib import Path
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.services import data_loader


def test_invalid_processed_data_falls_back_with_provenance(tmp_path, monkeypatch):
    pd.DataFrame({'unrelated': [1]}).to_parquet(tmp_path / 'dataset.parquet')
    monkeypatch.setattr(data_loader, 'PROCESSED', tmp_path)
    frame, warnings, fingerprint = data_loader.load_dataset()
    assert set(frame.source_type) == {'synthetic'}
    assert any('validated' in warning for warning in warnings)
    assert len(fingerprint) == 64
