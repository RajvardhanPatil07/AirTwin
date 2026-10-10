"""Small CI smoke test against an actual PostgreSQL service.

The script uses deliberately modeled/observed fixtures and never calls a provider.
Run with DATABASE_URL and PYTHONPATH=backend.
"""
import os
import uuid
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from app.services import decision_store


def main():
    if not os.getenv("DATABASE_URL"):
        raise SystemExit("DATABASE_URL is required for the PostgreSQL integration test")
    decision_store.initialize()
    unique = "ci-" + uuid.uuid4().hex[:12]
    clock = datetime.now(ZoneInfo("Asia/Kolkata")).replace(minute=0, second=0, microsecond=0)
    payload = {
        "updated_at": clock.isoformat(),
        "provider": "CAMS / Open-Meteo",
        "points": [{
            "id": unique + "-model", "name": "Test modeled point",
            "latitude": 18.60, "longitude": 73.85,
            "air": {
                "time": [(clock - timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M"),
                         (clock + timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M")],
                "pm2_5": [47.5, 49.2],
            },
        }],
        "observed": [{
            "id": unique + "-station", "name": "Test observed point",
            "source_type": "observed", "timestamp": clock.astimezone(timezone.utc).isoformat(),
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
