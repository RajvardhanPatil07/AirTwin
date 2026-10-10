"""Small CI smoke test against an actual PostgreSQL service.

The script uses deliberately modeled/observed fixtures and never calls a provider.
Run with DATABASE_URL and PYTHONPATH=backend.
"""
import os
import uuid
from app.services import decision_store


def main():
    if not os.getenv("DATABASE_URL"):
        raise SystemExit("DATABASE_URL is required for the PostgreSQL integration test")
    decision_store.initialize()
    unique = "ci-" + uuid.uuid4().hex[:12]
    payload = {
        "updated_at": "2026-10-10T09:00:00+05:30",
        "provider": "CAMS / Open-Meteo",
        "points": [{
            "id": unique + "-model", "name": "Test modeled point",
            "latitude": 18.60, "longitude": 73.85,
            "air": {
                "time": ["2026-10-10T08:00", "2026-10-10T10:00"],
                "pm2_5": [47.5, 49.2],
            },
        }],
        "observed": [{
            "id": unique + "-station", "name": "Test observed point",
            "source_type": "observed", "timestamp": "2026-10-10T03:30:00Z",
            "latitude": 18.61, "longitude": 73.86, "pm25": 53,
        }],
    }
    inserted = decision_store.capture_snapshot("pcmc", payload)
    assert inserted == 2, f"Expected one historical model record and one observed record; got {inserted}"
    latest = decision_store.recent_samples("pcmc", limit=100)
    selected = [r for r in latest if r["location_id"].startswith(unique)]
    assert len(selected) == 2, selected
    assert {r["source_type"] for r in selected} == {"observed", "modeled"}

    scenario = {
        "scenario_id": unique, "location_id": unique + "-station",
        "source_type": "modeled",
        "assumptions": ["Assumed, not causal"],
        "results": [{
            "id": "combined", "name": "Test policy", "rank": 1,
            "before": 53, "after": 49, "reduction": 4, "reduction_low": 2,
            "reduction_high": 6, "reduction_percent": 7.55,
            "exposure_benefit": 400, "population_source_type": "synthetic",
            "cells": [{"id": "cell", "pm25": 49}],
        }],
    }
    run_id = decision_store.save_scenario(
        region="pcmc", location_id=unique + "-station",
        input_source_type="observed",
        cuts={"traffic": 15, "industry": 20, "dust": 30},
        scenario=scenario,
    )
    assert run_id is not None
    runs = decision_store.recent_runs("pcmc", 50)
    saved = next(r for r in runs if r["run_id"] == run_id)
    assert saved["source_type"] == "modeled"
    assert saved["input_source_type"] == "observed"
    assert saved["summary"]["results"][0]["after"] == 49
    assert "cells" not in saved["summary"]["results"][0]
    overview = decision_store.overview("pcmc")
    assert overview["connected"] is True
    assert overview["samples"] >= 2
    assert overview["runs"] >= 1
    print("PostgreSQL decision-store integration succeeded:", run_id)


if __name__ == "__main__":
    main()
