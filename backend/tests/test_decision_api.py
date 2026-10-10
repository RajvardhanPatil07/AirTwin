import sys
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.routers import decision
from app.services import decision_store


class FakeRuntime:
    def location(self, location_id, replay_at=None):
        return ({"id": location_id, "source_type": "observed"}, None)

    def scenario(self, location_id, cuts, replay_at=None):
        return {
            "scenario_id": "test123", "location_id": location_id,
            "source_type": "modeled", "assumptions": ["Assumed pass-through"],
            "results": [{
                "id": "combined", "name": "Combined", "rank": 1, "before": 30,
                "after": 28, "reduction": 2, "reduction_low": 1,
                "reduction_high": 3, "reduction_percent": 6.66,
                "exposure_benefit": 10, "population_source_type": "synthetic",
                "cells": [],
            }],
        }

    def cached_snapshot(self, replay_at=None):
        return self.snapshot()

    def stations(self, replay_at=None):
        return {
            "stations": [
                {"id": "sensor", "name": "Test station", "source_type": "observed",
                 "timestamp": "2026-10-09T00:00:00+00:00", "assumptions": ["Measured"]},
            ],
            "source_type": "modeled",
            "assumptions": ["Station and map provenance are preserved."],
            "warnings": [],
        }

    def snapshot(self):
        timestamp = datetime(2026, 10, 9, tzinfo=timezone.utc)
        stations = [{"id": "sensor"}]
        cells = [
            {"id": "cell-a", "pm25": 33, "latitude": 18.6, "longitude": 73.8},
            {"id": "cell-b", "pm25": 42, "latitude": 18.7, "longitude": 73.9},
        ]
        return stations, cells, None, None, timestamp


def test_decision_router_provenance_and_no_database(monkeypatch):
    monkeypatch.setattr(decision, "get_region_runtime", lambda *_: FakeRuntime())
    monkeypatch.setattr(decision_store, "enabled", lambda: False)
    api = FastAPI()
    api.include_router(decision.router, prefix="/api")
    client = TestClient(api)
    response = client.post("/api/v2/decision-runs", json={
        "region": "pcmc", "location_id": "sensor",
        "cuts": {"traffic": 20, "industry": 30, "dust": 40}
    })
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["source_type"] == "modeled"
    assert data["scenario"]["source_type"] == "modeled"
    assert data["persisted"] is False
    assert data["run_id"] is None
    assert "DATABASE_URL" in data["storage_warning"]
    assert data["scenario"]["results"][0]["population_source_type"] == "synthetic"


def test_invalid_policy_cuts_are_rejected(monkeypatch):
    monkeypatch.setattr(decision, "get_region_runtime", lambda *_: FakeRuntime())
    api = FastAPI()
    api.include_router(decision.router, prefix="/api")
    result = TestClient(api).post("/api/v2/decision-runs", json={
        "location_id": "sensor",
        "cuts": {"traffic": 51, "industry": 0, "dust": 0},
    })
    assert result.status_code == 422


def test_hotspot_summary_explicitly_modeled(monkeypatch):
    monkeypatch.setattr(decision, "get_region_runtime", lambda *_: FakeRuntime())
    api = FastAPI()
    api.include_router(decision.router, prefix="/api")
    data = TestClient(api).get("/api/v2/hotspot-summary").json()
    assert data["source_type"] == "modeled"
    assert data["hotspots"][0]["cell_id"] == "cell-b"
    assert "IDW" in data["assumptions"][0]


def test_bootstrap_reuses_workspace_and_preserves_provenance(monkeypatch):
    monkeypatch.setattr(decision, "get_region_runtime", lambda *_: FakeRuntime())
    api = FastAPI()
    api.include_router(decision.router, prefix="/api")
    result = TestClient(api).get("/api/v2/bootstrap?region=pcmc")
    assert result.status_code == 200, result.text
    body = result.json()
    assert body["source_type"] == "modeled"
    assert len(body["stations"]) == 1
    assert body["stations"][0]["source_type"] == "observed"
    assert len(body["cells"]) == 2
    assert "interpolation" in body["assumptions"][0]


def test_runtime_snapshot_cache_deduplicates_repeated_queries():
    from app.services.runtime import Runtime

    class Counter:
        def __init__(self):
            self.calls = 0

        def snapshot(self, replay_at=None):
            self.calls += 1
            return {"replay": replay_at}

    runtime = Counter()
    first = Runtime.cached_snapshot(runtime)
    second = Runtime.cached_snapshot(runtime)
    historical = Runtime.cached_snapshot(runtime, "2026-10-09")
    assert first is second
    assert first is not historical
    assert runtime.calls == 2
