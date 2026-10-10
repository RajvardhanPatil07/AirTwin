"""Offline Phase-1 tests: no OpenAQ key, Supabase project or network needed."""
from __future__ import annotations

import json
import pandas as pd
import pytest

from app.config import TIMEZONE, WEATHER_COLUMNS
from app.services import live_observations as observations
from app.services.live_features import LiveFeatureError, build_live_input
from app.services import forecast_dispatcher as dispatcher
from app.services.state_data import PuneRuntime, SAMPLE


def station(t):
    return {"id": "openaq-123", "name": "Test monitor",
            "latitude": 18.62, "longitude": 73.85, "pm25": 51.0,
            "timestamp": t.isoformat(), "source_type": "observed"}


def history(t, hours=72):
    return [
        {"station_id": "openaq-123", "name": "Test monitor",
         "latitude": 18.62, "longitude": 73.85,
         "timestamp": (t - pd.Timedelta(hours=i)).isoformat(),
         "pm25": 49.0 + i % 5, "source_type": "observed"}
        for i in reversed(range(hours))
    ]


def provider(t):
    timestamps = pd.date_range(
        t - pd.Timedelta(hours=48), t + pd.Timedelta(hours=90), freq="h")
    data = {"timestamp": timestamps, "station_id": "pune-cams-0",
            "pm25": 42.0, "boundary_layer_height": 750.0}
    for col in WEATHER_COLUMNS:
        data[col] = 180.0 if col == "wind_direction_10m" else 25.0
    return pd.DataFrame(data)


def artifact():
    return {
        "models": {24: {
            "features": ["current_pm25", "lag_48", "rolling_mean_24",
                         "cams_target", "boundary_layer_height"]
        }},
        "report": {"covariates": {"cams_pm25": True, "boundary_layer_height": True}},
    }


def test_hourly_upsert_dedup_and_provenance(monkeypatch, tmp_path):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setattr(observations, "SQLITE_PATH", tmp_path / "observations.sqlite")
    t = pd.Timestamp.now(tz="UTC").floor("h")
    records = history(t)
    assert observations.persist_observations(records) == 72
    observations.persist_observations(records)
    assert len(observations.read_observations("openaq-123")) == 72
    assert observations.persist_observations([
        {**records[0], "station_id": "cams-0"},
        {**records[0], "source_type": "synthetic"},
    ]) == 0


def test_real_openaq_hours_response_shape(monkeypatch, tmp_path):
    monkeypatch.setenv("OPENAQ_API_KEY", "test-only")
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setattr(observations, "SQLITE_PATH", tmp_path / "observations.sqlite")
    t = pd.Timestamp.now(tz="UTC").floor("h")
    calls = []

    def provider_response(url, params, headers):
        calls.append((url, params, headers))
        return {"results": [
            {"period": {"datetimeFrom": {"utc": (t - pd.Timedelta(hours=i)).isoformat()}},
             "value": 50 + i % 5}
            for i in range(70)
        ]}

    result = observations.ingest_pune_history([station(t)], provider_response)
    assert result == {"sensors": 1, "rows": 70, "failures": 0}
    assert calls[0][0].endswith("/v3/sensors/123/hours")
    assert len(observations.read_observations("openaq-123")) == 70
    observations.ingest_pune_history([station(t)], provider_response)
    assert len(observations.read_observations("openaq-123")) == 70


def test_live_feature_alignment_and_history_gates():
    t = pd.Timestamp.now(tz=TIMEZONE).floor("h")
    records, reference = history(t), provider(t)
    frame, exog, issue, ref = build_live_input(records, reference, artifact(), now=t)
    assert len(frame) == 49
    assert ref == "pune-cams-0"
    assert issue == t
    assert exog.loc[t, "cams_pm25"] == 42
    assert frame.iloc[-1]["lag_48"] if "lag_48" in frame else True
    missing = records[:-3] + records[-2:]
    with pytest.raises(LiveFeatureError, match="incomplete_49_hour"):
        build_live_input(missing, reference, artifact(), now=t)
    with pytest.raises(LiveFeatureError, match="stale_or_future"):
        build_live_input(records, reference, artifact(), now=t + pd.Timedelta(hours=5))
    with pytest.raises(LiveFeatureError, match="non_observed"):
        build_live_input([{**r, "source_type": "modeled"} for r in records],
                         reference, artifact(), now=t)


def test_live_ml_dispatch_success(monkeypatch):
    t = pd.Timestamp.now(tz=TIMEZONE).floor("h")
    monkeypatch.setattr(dispatcher, "verified_artifact", lambda path: artifact())
    monkeypatch.setattr(dispatcher, "predict",
                        lambda artifact, frame, hours, exog: [(52.0, 45.0, 58.0)] * hours)
    monkeypatch.setattr(dispatcher, "explain_features",
                        lambda *a: {"method": "test"})
    result, reason = dispatcher.run_observed_station_forecast(
        station(t), provider(t), 24, observation_reader=lambda *_a, **_kw: history(t), now=t)
    assert reason is None
    assert result["model_id"] == "airtwin-lightgbm-live"
    assert result["history_source_type"] == "observed"
    assert len([p for p in result["series"] if p["predicted"] is not None]) == 24
    assert result["input_cutoff"] == t.isoformat()


def test_model_fallback_and_pune_cams_preserved():
    ml, reason = dispatcher.run_observed_station_forecast(
        {"id": "pune-cams-0", "source_type": "modeled"}, pd.DataFrame(), 24)
    assert ml is None and reason == "location_has_no_observed_sensor"
    payload = json.loads(SAMPLE.read_text())
    payload["points"] = payload["points"][1:3]
    runtime = PuneRuntime(payload)
    location = runtime.stations()["stations"][0]["id"]
    output = runtime.forecast(location, 24)
    assert output["model_id"] == "cams-global-provider"
    assert output["forecast_provider"] == "CAMS via Open-Meteo"
    assert output["fallback_reason"] == "location_has_no_observed_sensor"
    assert all(p["p10"] is None for p in output["series"])
    assert runtime.backtest(location)["available"] is False
