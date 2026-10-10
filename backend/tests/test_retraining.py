"""Regression coverage for unattended observed-only model retraining."""
from contextlib import contextmanager
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import joblib
import numpy as np
import pandas as pd

from app.services import retraining as rt
from app.services import forecast_dispatcher as fd


def _rows(starts="2026-08-01", count=400, source="observed"):
    stamps = pd.date_range(starts, periods=count, freq="h", tz="UTC")
    return pd.DataFrame({
        "station_id": ["openaq-123"] * count,
        "timestamp": stamps,
        "pm25": np.linspace(20, 40, count),
        "latitude": [18.6] * count, "longitude": [73.8] * count,
        "source_type": [source] * count,
    })


def test_training_data_discards_modeled_and_synthetic_targets():
    base = pd.concat([_rows(source="observed"), _rows(source="synthetic"),
                      _rows(source="modeled")], ignore_index=True)
    live = [
        {"station_id": "openaq-123", "timestamp": "2026-08-01T00:00:00+00:00",
         "pm25": 123.0, "latitude": 18.6, "longitude": 73.8,
         "source_type": "observed"},
        {"station_id": "openaq-456", "timestamp": "2026-08-20T00:00:00+00:00",
         "pm25": 55.0, "latitude": 18.6, "longitude": 73.8,
         "source_type": "modeled"},
    ]
    frame, filtered = rt.prepare_training_data(base, live)
    assert set(frame.source_type) == {"observed"}
    assert len(filtered) == 1
    assert frame.loc[frame.timestamp.eq(pd.Timestamp("2026-08-01", tz="UTC")), "pm25"].iloc[0] == 123.0


def _stub_check(monkeypatch, candidate_mae=8.0, baseline_mae=10.0):
    original = _rows(count=400)
    new = _rows("2026-08-20", 60).to_dict("records")
    monkeypatch.setattr(rt, "load_all", lambda: (original, [], "orig-fingerprint", None))
    monkeypatch.setattr(rt, "read_training_observations", lambda: new)
    monkeypatch.setattr(rt, "_existing_live_artifact", lambda: None)
    monkeypatch.setattr(rt, "MIN_OBSERVED_ROWS", 300)
    monkeypatch.setattr(rt, "MIN_NEW_ROWS", 48)

    @contextmanager
    def lock():
        yield True

    monkeypatch.setattr(rt, "_exclusive_training", lock)
    calls = []

    def train_candidate(frame, fingerprint, warnings, *, exog, persist, prefer_recent_holdout):
        assert persist is False and prefer_recent_holdout is True
        assert set(frame.source_type) == {"observed"}
        assert len(frame) == 460
        return {
            "models": {24: {"weight": 0.3}}, "version": rt.VERSION,
            "fingerprint": fingerprint,
            "report": {"target_source_types": ["observed"],
                       "test_rows": 50,
                       "metrics": {"mae": candidate_mae,
                                   "persistence_mae": baseline_mae}},
        }

    monkeypatch.setattr(rt, "train", train_candidate)
    monkeypatch.setattr(rt, "_promote", lambda artifact: calls.append(artifact))
    return calls


def test_retraining_promotes_only_validated_candidate(monkeypatch):
    calls = _stub_check(monkeypatch)
    result = rt.run_retraining_check()
    assert result["status"] == "promoted"
    assert len(calls) == 1
    assert calls[0]["retraining"]["new_rows"] == 60


def test_retraining_rejects_candidate_worse_than_persistence(monkeypatch):
    calls = _stub_check(monkeypatch, candidate_mae=12.0)
    result = rt.run_retraining_check()
    assert result["status"] == "rejected"
    assert result["reason"] == "24h_model_does_not_beat_persistence"
    assert calls == []


def test_retraining_rejects_persistence_tie(monkeypatch):
    calls = _stub_check(monkeypatch, candidate_mae=10.0, baseline_mae=10.0)
    result = rt.run_retraining_check()
    assert result["status"] == "rejected"
    assert result["reason"] == "24h_model_does_not_beat_persistence"
    assert calls == []


def test_retraining_rejects_zero_weight_production_bundle(monkeypatch):
    calls = _stub_check(monkeypatch)
    def production_is_persistence_only(frame, fingerprint, warnings, **kwargs):
        return {
            "models": {24: {"weight": 0.0}},
            "version": rt.VERSION,
            "fingerprint": fingerprint,
            "report": {"target_source_types": ["observed"], "test_rows": 50,
                       "metrics": {"mae": 8.0, "persistence_mae": 10.0}},
        }
    monkeypatch.setattr(rt, "train", production_is_persistence_only)
    result = rt.run_retraining_check()
    assert result["status"] == "rejected"
    assert result["reason"] == "24h_production_model_has_no_lightgbm_contribution"
    assert calls == []


def test_invalid_legacy_promotion_does_not_block_replacement(monkeypatch):
    calls = _stub_check(monkeypatch)
    previous = {
        "models": {24: {"weight": 0.0}}, "version": rt.VERSION,
        "report": {"target_source_types": ["observed"], "test_rows": 50,
                   "metrics": {"mae": 10.0, "persistence_mae": 10.0}},
        "retraining": {
            "trained_at": pd.Timestamp.now(tz="UTC").isoformat(),
            "latest_observed_at": "2026-08-18T00:00:00+00:00",
        },
    }
    monkeypatch.setattr(rt, "_existing_live_artifact", lambda: previous)
    result = rt.run_retraining_check()
    assert result["status"] == "promoted"
    assert len(calls) == 1
    assert calls[0]["retraining"]["new_rows"] == 60


def test_retraining_waits_for_new_readings(monkeypatch):
    calls = _stub_check(monkeypatch)
    monkeypatch.setattr(rt, "MIN_NEW_ROWS", 61)
    result = rt.run_retraining_check()
    assert result["status"] == "skipped"
    assert calls == []


def test_retrained_artifact_is_preferred_but_bad_file_falls_back(monkeypatch, tmp_path):
    base = tmp_path / "forecast.joblib"
    live = tmp_path / "forecast_live.joblib"
    base.write_bytes(b"model")
    live.write_bytes(b"candidate")
    monkeypatch.setattr(fd, "ARTIFACT", base)
    monkeypatch.setattr(fd, "LIVE_ARTIFACT", live)
    attempts = []

    def valid_model(file):
        attempts.append(file)
        if file == live:
            raise fd.LiveFeatureError("model_artifact_unreadable")
        return {"version": 3, "models": {24: "existing"}}

    monkeypatch.setattr(fd, "_verified_file", valid_model)
    assert fd.verified_artifact(base) == {"version": 3, "models": {24: "existing"}}
    assert attempts == [live, base]


def test_legacy_persistence_tie_artifact_falls_back(monkeypatch, tmp_path):
    base = tmp_path / "forecast.joblib"
    live = tmp_path / "forecast_live.joblib"
    incumbent = {"version": rt.VERSION, "models": {24: {"weight": 0.4}},
                 "report": {"target_source_types": ["observed"]}}
    tied = {"version": rt.VERSION, "models": {24: {"weight": 0.0}},
            "report": {"target_source_types": ["observed"], "test_rows": 50,
                       "metrics": {"mae": 10.0, "persistence_mae": 10.0}}}
    joblib.dump(incumbent, base)
    joblib.dump(tied, live)
    monkeypatch.setattr(fd, "ARTIFACT", base)
    monkeypatch.setattr(fd, "LIVE_ARTIFACT", live)
    fd._load_artifact.cache_clear()
    assert fd.verified_artifact(base) == incumbent
    fd._load_artifact.cache_clear()


def test_validation_requires_observed_targets_and_honest_benchmark():
    sample = {"models": {24: {"weight": 0.3}},
              "report": {"target_source_types": ["modeled"], "test_rows": 100,
                         "metrics": {"mae": 3.0, "persistence_mae": 10.0}}}
    assert rt._validate(sample) == "candidate_includes_nonobserved_targets"
    sample["report"]["target_source_types"] = ["observed"]
    sample["report"]["test_rows"] = 1
    assert rt._validate(sample) == "insufficient_or_invalid_holdout"


def test_recent_holdout_ends_at_latest_hour():
    from app.services.model import choose_holdout
    data = pd.DataFrame({"timestamp": pd.date_range("2025-01-01",
                        periods=1500, freq="h", tz="Asia/Kolkata")})
    start, end, method = choose_holdout(data, prefer_recent=True)
    assert "recent" in method
    assert start == data.timestamp.iloc[1200]
    assert end > data.timestamp.iloc[-1]


def test_local_file_lock_prevents_concurrent_training(monkeypatch, tmp_path):
    monkeypatch.setattr(rt.database, "configured", lambda: False)
    monkeypatch.setattr(rt, "MODELS", tmp_path)
    with rt._exclusive_training() as acquired:
        assert acquired is True
        with rt._exclusive_training() as second:
            assert second is False
    with rt._exclusive_training() as acquired:
        assert acquired is True
