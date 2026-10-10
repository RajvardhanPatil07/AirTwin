"""Typed, optional PostgreSQL decision store. Never converts CAMS or synthetic data to observations."""
from __future__ import annotations

import logging
import math
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

LOG = logging.getLogger("airtwin.decisions")
SQL = Path(__file__).resolve().parents[2] / "migrations" / "001_decision_store.sql"
IST = ZoneInfo("Asia/Kolkata")
ALLOWED_REGIONS = {"pcmc", "maharashtra"}


def enabled() -> bool:
    return bool(os.getenv("DATABASE_URL"))


def _connect():
    from app.services.database import _connect as database_connect
    return database_connect()


def initialize() -> bool:
    if not enabled():
        return False
    with _connect() as connection:
        connection.execute(SQL.read_text(encoding="utf-8"))
    return True


def _aware(value: str) -> datetime:
    """The Open-Meteo hourly cache uses local IST timestamps without a UTC offset."""
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return dt if dt.tzinfo else dt.replace(tzinfo=IST)


def _valid_pm25(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) and 0 <= number <= 1000 else None


def snapshot_rows(region: str, payload: dict[str, Any]) -> list[tuple]:
    """Flatten a provider snapshot, retaining source labels and independent timestamps.

    Historical CAMS values are MODEL OUTPUTS. OpenAQ measurements are OBSERVED.
    Neither IDW cells nor scenarios are inserted as measurements.
    """
    if region not in ALLOWED_REGIONS:
        raise ValueError("Unsupported region")
    rows: list[tuple] = []
    for point in payload.get("points", []):
        hourly = point.get("air", {})
        times = hourly.get("time", [])
        values = hourly.get("pm2_5", [])
        # Bound refresh writes; older history remains in the database.
        cutoff = _aware(payload.get("updated_at", datetime.now(IST).isoformat()))
        # Forecast hours after the refresh are not historical concentration samples.
        historical = [(stamp, value) for stamp, value in zip(times, values) if _aware(stamp) <= cutoff]
        for stamp, value in historical[-48:]:
            pm25 = _valid_pm25(value)
            if pm25 is None:
                continue
            rows.append((region, str(point["id"]), _aware(stamp), "modeled",
                         str(payload.get("provider", "CAMS / Open-Meteo")),
                         str(point["name"]), float(point["latitude"]),
                         float(point["longitude"]), pm25))
    for point in payload.get("observed", []):
        pm25 = _valid_pm25(point.get("pm25"))
        if pm25 is None or point.get("source_type") != "observed":
            continue
        # The original station reading timestamp is never replaced with cache refresh time.
        rows.append((region, str(point["id"]), _aware(point["timestamp"]), "observed",
                     "OpenAQ / upstream station", str(point["name"]),
                     float(point["latitude"]), float(point["longitude"]), pm25))
    return rows


def capture_snapshot(region: str, payload: dict[str, Any]) -> int:
    if not enabled():
        return 0
    rows = snapshot_rows(region, payload)
    if not rows:
        return 0
    with _connect() as connection:
        with connection.cursor() as cursor:
            cursor.executemany("""
                INSERT INTO air_quality_samples
                (region, location_id, sample_time, source_type, provider,
                 location_name, latitude, longitude, pm25_ugm3)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (region, location_id, sample_time, source_type, provider)
                DO UPDATE SET pm25_ugm3=EXCLUDED.pm25_ugm3,
                              imported_at=now()
            """, rows)
        connection.execute(
            "DELETE FROM air_quality_samples WHERE sample_time < now() - interval '180 days'"
        )
    return len(rows)


def summarize_scenario(scenario: dict[str, Any]) -> dict[str, Any]:
    """Store comparable numeric outcomes, not hundreds of duplicated grid cells."""
    return {
        "scenario_id": scenario["scenario_id"],
        "location_id": scenario["location_id"],
        "source_type": "modeled",
        "results": [
            {key: item[key] for key in (
                "id", "name", "rank", "before", "after", "reduction",
                "reduction_low", "reduction_high", "reduction_percent",
                "exposure_benefit", "exposure_benefit_low", "exposure_benefit_high",
                "population_source_type"
            ) if key in item}
            for item in scenario["results"]
        ],
    }


def save_scenario(*, region: str, location_id: str, input_source_type: str,
                  cuts: dict[str, float], scenario: dict[str, Any],
                  replay_at: str | None = None) -> str | None:
    if not enabled():
        return None
    if region not in ALLOWED_REGIONS:
        raise ValueError("Unsupported region")
    if input_source_type not in {"observed", "modeled", "synthetic"}:
        raise ValueError("Unknown input provenance")
    from psycopg.types.json import Jsonb
    run_id = str(uuid.uuid4())
    with _connect() as connection:
        connection.execute("""
            INSERT INTO decision_runs
              (run_id, scenario_id, region, location_id, replay_at,
               input_source_type, cuts, summary, assumptions)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (run_id, scenario["scenario_id"], region, location_id,
              _aware(replay_at) if replay_at else None,
              input_source_type, Jsonb(cuts),
              Jsonb(summarize_scenario(scenario)),
              Jsonb(scenario.get("assumptions", []))))
    return run_id


def recent_runs(region: str = "pcmc", limit: int = 15) -> list[dict[str, Any]]:
    if region not in ALLOWED_REGIONS:
        raise ValueError("Unsupported region")
    if not enabled():
        return []
    with _connect() as connection:
        rows = connection.execute("""
            SELECT run_id::text, scenario_id, location_id,
                   created_at, input_source_type, cuts, summary
            FROM decision_runs WHERE region=%s
            ORDER BY created_at DESC LIMIT %s
        """, (region, max(1, min(limit, 50)))).fetchall()
    return [
        {"run_id": r[0], "scenario_id": r[1], "location_id": r[2],
         "created_at": r[3].isoformat(), "input_source_type": r[4],
         "cuts": r[5], "summary": r[6], "source_type": "modeled"}
        for r in rows
    ]


def overview(region: str = "pcmc") -> dict[str, Any]:
    if not enabled():
        return {"configured": False, "connected": False, "samples": 0, "runs": 0}
    with _connect() as connection:
        sample = connection.execute("""
            SELECT source_type, count(*), max(sample_time) FROM air_quality_samples
            WHERE region=%s GROUP BY source_type
        """, (region,)).fetchall()
        runs = connection.execute(
            "SELECT count(*) FROM decision_runs WHERE region=%s", (region,)
        ).fetchone()[0]
    return {
        "configured": True, "connected": True, "runs": runs,
        "samples": sum(int(r[1]) for r in sample),
        "samples_by_source": {r[0]: int(r[1]) for r in sample},
        "latest_sample_by_source": {r[0]: r[2].isoformat() for r in sample},
    }


def safe_overview(region: str = "pcmc") -> dict[str, Any]:
    try:
        return overview(region)
    except Exception:
        LOG.warning("Decision store unavailable", exc_info=True)
        return {"configured": enabled(), "connected": False, "samples": 0, "runs": 0}


def recent_samples(region: str = "pcmc", source_type: str | None = None,
                   limit: int = 50) -> list[dict[str, Any]]:
    """Return actual normalized point samples (never gridded IDW cells)."""
    if region not in ALLOWED_REGIONS:
        raise ValueError("Unsupported region")
    if source_type not in (None, "observed", "modeled", "synthetic"):
        raise ValueError("Invalid provenance filter")
    if not enabled():
        return []
    sql = """
        SELECT location_id, location_name, sample_time, source_type, provider,
               latitude, longitude, pm25_ugm3
        FROM air_quality_samples WHERE region=%s
    """
    params: list[Any] = [region]
    if source_type:
        sql += " AND source_type=%s"
        params.append(source_type)
    sql += " ORDER BY sample_time DESC LIMIT %s"
    params.append(max(1, min(limit, 100)))
    with _connect() as connection:
        rows = connection.execute(sql, params).fetchall()
    return [{
        "location_id": row[0], "name": row[1],
        "timestamp": row[2].isoformat(), "source_type": row[3],
        "provider": row[4], "latitude": row[5], "longitude": row[6],
        "pm25": row[7], "unit": "µg/m³",
    } for row in rows]
