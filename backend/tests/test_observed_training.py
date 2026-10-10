"""Fail-closed guard for training a genuine observed-target model."""
from __future__ import annotations

import sys
from pathlib import Path
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from train_observed_model import verify_observed_dataset


def rows(source="observed", provider="OpenAQ", weather="modeled", n=730):
    times = pd.date_range("2026-08-01", periods=n, freq="h", tz="UTC")
    return pd.DataFrame({
        "station_id": ["openaq-123"] * n, "timestamp": times,
        "source_type": [source] * n, "target_provider": [provider] * n,
        "weather_source_type": [weather] * n,
    })


def test_observed_training_requires_actual_openaq_targets_and_weather():
    assert verify_observed_dataset(rows()) == 730
    with pytest.raises(ValueError, match="exclusively OBSERVED"):
        verify_observed_dataset(rows(source="synthetic"))
    with pytest.raises(ValueError, match="target provenance"):
        verify_observed_dataset(rows(provider="CAMS"))
    with pytest.raises(ValueError, match="synthetic or unprovenanced weather"):
        verify_observed_dataset(rows(weather="synthetic"))
    with pytest.raises(ValueError, match="need 720"):
        verify_observed_dataset(rows(n=240))
