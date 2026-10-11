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
        "version": 3,
        "models": {24: {
            "features": ["current_pm25", "lag_48", "rolling_mean_24",
                         "cams_target", "boundary_layer_height"]
        }},
        "report": {"covariates": {"cams_pm25": True, "boundary_layer_height": True},
                   "skill":[{"horizon":24,"mae":5,"persistence_mae":8}]},
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


def test_hourly_history_recovers_outage_gap(monkeypatch, tmp_path):
    """Restarting after a three-day outage must fetch missed hourly observations."""
    monkeypatch.setenv("OPENAQ_API_KEY", "test-only")
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setattr(observations, "SQLITE_PATH", tmp_path / "catchup.sqlite")
    now = pd.Timestamp.now(tz="UTC").floor("h")
    previous_time = now - pd.Timedelta(hours=72)
    previous = {**station(previous_time), "station_id": "openaq-123", "pm25": 40}
    assert observations.persist_observations([previous]) == 1
    requested = []

    def provider_response(url, params, headers):
        requested.append(pd.Timestamp(params["datetime_from"]))
        return {"results": [
            {"period": {"datetimeFrom": {
                "utc": (previous_time + pd.Timedelta(hours=24)).isoformat()}},
             "value": 42.0},
        ]}

    result = observations.ingest_pune_history([station(now)], provider_response)
    assert result == {"sensors": 1, "rows": 1, "failures": 0}
    assert requested[0] <= previous_time
    assert len(observations.read_observations("openaq-123", hours=96)) == 2


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


@pytest.mark.parametrize("skill", [[], [{"horizon": 24, "mae": 9, "persistence_mae": 8}]])
def test_observed_dispatch_retains_persistence_without_better_benchmark(monkeypatch, skill):
    t = pd.Timestamp.now(tz=TIMEZONE).floor("h")
    candidate = artifact()
    candidate["report"]["skill"] = skill
    monkeypatch.setattr(dispatcher, "verified_artifact", lambda path: candidate)

    def forbidden_prediction(*args):
        pytest.fail("A losing or unbenchmarked model must not serve predictions")

    monkeypatch.setattr(dispatcher, "predict", forbidden_prediction)
    result, reason = dispatcher.run_observed_station_forecast(
        station(t), provider(t), 24, observation_reader=lambda *_a, **_kw: history(t), now=t)
    assert reason is None
    assert result["model_id"] == "observed-persistence"
    future = [p for p in result["series"] if p["predicted"] is not None]
    assert all(p["predicted"] == history(t)[-1]["pm25"] for p in future)
    assert all(p["p10"] is None and p["p90"] is None for p in future)


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


def test_stale_openaq_sensor_is_discovered_for_history_not_live(monkeypatch):
    """A 64-hour-old monitor must still qualify for an hourly backfill."""
    from app.services import state_data
    now = pd.Timestamp.now(tz="UTC")
    last = (now - pd.Timedelta(hours=64)).isoformat()
    urls = []

    def fake_payload(url, params=None, headers=None):
        urls.append(url)
        if "air-quality-api.open-meteo.com" in url:
            return [{"hourly": {}, "hourly_units": {}}]
        if "api.open-meteo.com" in url:
            return [{"hourly": {}, "hourly_units": {}}]
        if url.endswith("/v3/locations"):
            return {"results": [{
                "id": 42, "name": "Stale PCMC monitor",
                "coordinates": {"latitude": 18.62, "longitude": 73.85},
                "datetimeLast": {"utc": last},
                "sensors": [
                    {"id": 123, "parameter": {"name": "pm25", "units": "µg/m³"}},
                    {"id": 124, "parameter": {"name": "pm25", "units": "ppm"}},
                    {"id": 125, "parameter": {"name": "pm10", "units": "µg/m³"}},
                ],
            }]}
        if url.endswith("/42/latest"):
            return {"results": [{"sensorsId": 123, "value": 35, "datetime": {"utc": last}}]}
        raise AssertionError("Unexpected provider request")

    monkeypatch.setenv("OPENAQ_API_KEY", "test-only")
    monkeypatch.setattr(state_data, "get_payload", fake_payload)
    result = state_data.fetch_context(
        [("PCMC", 18.62, 73.85)], (73.7, 18.45, 73.98, 18.8),
        lambda lat, lon: 18.45 <= lat <= 18.8 and 73.7 <= lon <= 73.98,
        "Pune + PCMC", "pune-cams",
    )
    assert result["observed"] == []
    assert result["discovered_pm25_sensors"] == 2
    assert [s["id"] for s in result["history_sensor_candidates"]] == ["openaq-123"]
    assert any(url.endswith("/42/latest") for url in urls)
    assert "64 hours" in result["warnings"][0]


def test_stale_sensor_history_is_persisted_without_becoming_live(monkeypatch, tmp_path):
    monkeypatch.setenv("OPENAQ_API_KEY", "test-only")
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setattr(observations, "SQLITE_PATH", tmp_path / "stale.sqlite")
    now = pd.Timestamp.now(tz="UTC").floor("h")
    candidate = {"id": "openaq-123", "name": "Old PCMC monitor",
                 "latitude": 18.62, "longitude": 73.85,
                 "timestamp": (now - pd.Timedelta(hours=64)).isoformat()}

    def hourly(url, params, headers):
        assert url.endswith("/v3/sensors/123/hours")
        return {"results": [
            {"period": {"datetimeFrom": {"utc": (now - pd.Timedelta(hours=i)).isoformat()}},
             "value": 36.0}
            for i in (64, 65, 66)
        ]}

    outcome = observations.ingest_pune_history([candidate], hourly)
    assert outcome == {"sensors": 1, "rows": 3, "failures": 0}
    saved = observations.read_observations("openaq-123", hours=96)
    assert len(saved) == 3
    assert set(row["source_type"] for row in saved) == {"observed"}
    assert max(pd.Timestamp(row["timestamp"]) for row in saved) <= now - pd.Timedelta(hours=64)


def test_refresh_pune_backfills_candidates_not_just_live_stations(monkeypatch):
    from app.services import state_data
    candidate = {"id": "openaq-123", "name": "Stale monitor",
                 "latitude": 18.62, "longitude": 73.85,
                 "timestamp": "2026-10-07T00:00:00+00:00"}
    payload = {"points": [{"id": "pune-cams-0"}], "observed": [],
               "history_sensor_candidates": [candidate], "warnings": []}
    calls = {}

    class StubRuntime:
        def __init__(self, data):
            self.warnings = []

        def snapshot(self):
            return None

    def fake_ingest(sensors, get_payload):
        calls["sensors"] = sensors
        return {"sensors": 1, "rows": 3, "failures": 0}

    def fake_save(data, path, region):
        calls["saved"] = data
        assert region == "pcmc"

    monkeypatch.setattr(state_data, "fetch_context", lambda *args: payload)
    monkeypatch.setattr(state_data, "PuneRuntime", StubRuntime)
    monkeypatch.setattr(state_data, "_pune_runtime", None)
    monkeypatch.setattr(observations, "read_training_observations", lambda **kwargs: [])
    monkeypatch.setattr(state_data, "save_context", fake_save)
    monkeypatch.setattr(observations, "ingest_pune_history", fake_ingest)
    monkeypatch.setattr(observations, "latest_cached_monitors", lambda *a: [])
    state_data.refresh_pune()
    assert calls["sensors"] == [candidate]
    assert calls["saved"]["observed"] == []
    assert calls["saved"]["history_ingestion"]["rows"] == 3
