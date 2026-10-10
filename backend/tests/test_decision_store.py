from datetime import timedelta
from app.services.decision_store import snapshot_rows, summarize_scenario


def test_snapshot_rows_preserve_observed_vs_modeled():
    payload = {
        "provider": "CAMS / Open-Meteo",
        "points": [{
            "id": "cams-0", "name": "Bhosari", "latitude": 18.62,
            "longitude": 73.85, "air": {
                "time": ["2026-10-08T09:00", "2026-10-08T10:00"],
                "pm2_5": [42, None],
            },
        }],
        "observed": [{
            "id": "openaq-1", "name": "Ground sensor",
            "latitude": 18.63, "longitude": 73.84,
            "pm25": 54, "timestamp": "2026-10-08T04:00:00Z",
            "source_type": "observed",
        }, {
            "id": "bad", "name": "Unproven", "latitude": 18.63,
            "longitude": 73.84, "pm25": 65,
            "timestamp": "2026-10-08T04:00:00Z",
            "source_type": "modeled",
        }],
    }
    rows = snapshot_rows("pcmc", payload)
    assert len(rows) == 2
    assert {row[3] for row in rows} == {"observed", "modeled"}
    assert rows[0][2].utcoffset() == timedelta(hours=5, minutes=30)
    assert rows[1][2].utcoffset() == timedelta(0)
    assert rows[0][-1] == 42.0


def test_scenario_summary_does_not_store_grid_copies():
    source = {
        "scenario_id": "abc", "location_id": "bhosari",
        "results": [{
            "id": "traffic", "name": "Traffic",
            "rank": 1, "before": 90, "after": 84, "reduction": 6,
            "cells": [{"id": "cell-1", "pm25": 84}],
        }],
    }
    summary = summarize_scenario(source)
    assert summary["source_type"] == "modeled"
    assert summary["results"][0]["after"] == 84
    assert "cells" not in summary["results"][0]


def test_future_cams_forecast_not_misfiled_as_historical_sample():
    payload = {
        "updated_at": "2026-10-08T10:00:00+05:30",
        "points": [{
            "id": "pune-cams-0", "name": "Pune", "latitude": 18.52,
            "longitude": 73.86,
            "air": {
                "time": ["2026-10-08T09:00", "2026-10-08T11:00"],
                "pm2_5": [40, 45],
            },
        }],
    }
    samples = snapshot_rows("pcmc", payload)
    assert len(samples) == 1
    assert samples[0][-1] == 40
