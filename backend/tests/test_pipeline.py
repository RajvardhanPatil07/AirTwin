import sys
from pathlib import Path
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from build_dataset import clean_air, merge
from common import sample_frame
from app.config import SAMPLE, WEATHER_COLUMNS

def test_cleaning_rejects_outliers_and_keeps_provenance():
    base = sample_frame().iloc[:1].copy()
    rows = pd.concat([base.assign(pm25=value) for value in [-1, 1001, 20, 40]])
    result = clean_air(rows)
    assert len(result) == 1
    assert result.pm25.iloc[0] == 30
    assert result.source_type.iloc[0] == "synthetic"

def test_hourly_merge_preserves_missing_weather():
    sample = sample_frame().iloc[:3]
    air = clean_air(sample)
    weather = sample.iloc[:1][["timestamp", *WEATHER_COLUMNS, "weather_source_type", "weather_provider"]]
    result = merge(air, weather)
    assert len(result) == 3
    assert result.weather_source_type.tolist() == ["synthetic", "missing", "missing"]
    assert result.temperature_2m.isna().sum() == 2
    assert result.timestamp.dt.tz is not None

def test_sample_size_and_honest_labels():
    frame = sample_frame()
    assert SAMPLE.stat().st_size < 1_000_000
    assert set(frame.source_type) == {"synthetic"}
    assert set(frame.weather_source_type) == {"synthetic"}
    assert frame.timestamp.diff().dropna().eq(pd.Timedelta(hours=1)).all()

def test_openaq_missing_key_falls_back(monkeypatch, tmp_path):
    import fetch_openaq
    monkeypatch.delenv("OPENAQ_API_KEY", raising=False)
    monkeypatch.setattr(fetch_openaq, "RAW", tmp_path)
    monkeypatch.setattr(sys, "argv", ["fetch_openaq.py"])
    fetch_openaq.main()
    assert set(pd.read_csv(tmp_path / "air_quality.csv").source_type) == {"synthetic"}


def test_weather_api_failure_falls_back(monkeypatch, tmp_path):
    import fetch_weather
    sample_frame().to_csv(tmp_path / "air_quality.csv", index=False)
    monkeypatch.setattr(fetch_weather, "RAW", tmp_path)
    monkeypatch.setattr(sys, "argv", ["fetch_weather.py"])
    def unavailable(*args, **kwargs):
        raise RuntimeError("simulated API outage")
    monkeypatch.setattr(fetch_weather, "fetch", unavailable)
    fetch_weather.main()
    assert set(pd.read_csv(tmp_path / "weather.csv").weather_source_type) == {"synthetic"}


def test_sparse_targets_and_cams_failure_use_sample(monkeypatch, tmp_path):
    import build_dataset
    sample_frame().to_csv(tmp_path / "air_quality.csv", index=False)
    monkeypatch.setattr(build_dataset, "RAW", tmp_path)
    monkeypatch.setattr(build_dataset, "PROCESSED", tmp_path)
    monkeypatch.setattr(sys, "argv", ["build_dataset.py"])
    def unavailable():
        raise RuntimeError("simulated CAMS outage")
    monkeypatch.setattr(build_dataset, "cams", unavailable)
    before = SAMPLE.read_bytes()
    build_dataset.main()
    assert set(pd.read_parquet(tmp_path / "dataset.parquet").source_type) == {"synthetic"}
    assert SAMPLE.read_bytes() == before
