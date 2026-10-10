"""Persist real OpenAQ hourly PM2.5 history for operational forecasts.

PostgreSQL (including Supabase) is selected by DATABASE_URL. The private
airtwin schema is not exposed through Supabase's default public Data API.
Without PostgreSQL, an ignored SQLite file supports local development.
"""
from __future__ import annotations

import logging
import os
import sqlite3
from concurrent.futures import ThreadPoolExecutor, as_completed
from contextlib import closing
from datetime import datetime, timedelta, timezone

import pandas as pd

from app.config import RAW
from app.services import database

LOG = logging.getLogger("airtwin.live.observations")
SQLITE_PATH = RAW / "live_station_history.sqlite3"
RETENTION_DAYS = 90
SCHEMA_SQLITE = """
CREATE TABLE IF NOT EXISTS station_observations (
    station_id TEXT NOT NULL,
    observed_at TEXT NOT NULL,
    pm25 REAL NOT NULL CHECK(pm25 >= 0 AND pm25 <= 1000),
    latitude REAL NOT NULL,
    longitude REAL NOT NULL,
    station_name TEXT NOT NULL,
    received_at TEXT NOT NULL,
    PRIMARY KEY(station_id, observed_at)
)"""
SCHEMA_POSTGRES = """
CREATE TABLE IF NOT EXISTS airtwin.station_observations (
    station_id TEXT NOT NULL,
    observed_at TIMESTAMPTZ NOT NULL,
    pm25 DOUBLE PRECISION NOT NULL CHECK(pm25 >= 0 AND pm25 <= 1000),
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    station_name TEXT NOT NULL,
    received_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY(station_id, observed_at)
)"""


def _utc_hour(value):
    stamp = pd.Timestamp(value)
    if pd.isna(stamp) or stamp.tzinfo is None:
        raise ValueError("Observed timestamp requires timezone")
    return stamp.tz_convert("UTC").floor("h").isoformat()


def _normalize(record):
    if record.get("source_type", "observed") != "observed":
        return None
    sensor = str(record.get("station_id", ""))
    if not sensor.startswith("openaq-") or not sensor[7:].isdigit():
        return None
    try:
        value = float(record["pm25"])
        lat, lon = float(record["latitude"]), float(record["longitude"])
        if not (0 <= value <= 1000 and -90 <= lat <= 90 and -180 <= lon <= 180):
            return None
        if not all(pd.notna(x) for x in (value, lat, lon)):
            return None
        if pd.Timestamp(record['timestamp'])>pd.Timestamp.now(tz='UTC'):
            return None
        return (sensor, _utc_hour(record["timestamp"]), value, lat, lon,
                str(record.get("name", sensor))[:250],
                datetime.now(timezone.utc).isoformat())
    except (KeyError, TypeError, ValueError, OverflowError):
        return None


def _sqlite():
    SQLITE_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(SQLITE_PATH, timeout=15)
    conn.execute(SCHEMA_SQLITE)
    return conn


def _ensure_postgres(conn):
    conn.execute("CREATE SCHEMA IF NOT EXISTS airtwin")
    conn.execute(SCHEMA_POSTGRES)
    # No grants to anon/authenticated; backend connects using DATABASE_URL.


def persist_observations(records):
    """Upsert observed station-hours; never persist CAMS or demo targets."""
    rows = [row for item in records if (row := _normalize(item)) is not None]
    if not rows:
        return 0
    if database.configured():
        with database._connect() as conn:
            _ensure_postgres(conn)
            with conn.cursor() as cursor:
                cursor.executemany("""
                    INSERT INTO airtwin.station_observations
                      (station_id, observed_at, pm25, latitude, longitude, station_name, received_at)
                    VALUES (%s, %s::timestamptz, %s, %s, %s, %s, %s::timestamptz)
                    ON CONFLICT (station_id, observed_at) DO UPDATE SET
                      pm25=EXCLUDED.pm25, received_at=EXCLUDED.received_at
                    """, rows)
            conn.execute("DELETE FROM airtwin.station_observations WHERE observed_at < now() - interval '90 days'")
    else:
        with closing(_sqlite()) as conn, conn:
            conn.executemany("""
                INSERT INTO station_observations
                  (station_id, observed_at, pm25, latitude, longitude, station_name, received_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT (station_id, observed_at) DO UPDATE SET
                  pm25=excluded.pm25, received_at=excluded.received_at
                """, rows)
            cutoff = (datetime.now(timezone.utc) - timedelta(days=RETENTION_DAYS)).isoformat()
            conn.execute("DELETE FROM station_observations WHERE observed_at < ?", (cutoff,))
    return len(rows)


def read_observations(station_id, hours=96):
    if not str(station_id).startswith("openaq-"):
        return []
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()
    columns = "station_id, observed_at, pm25, latitude, longitude, station_name"
    if database.configured():
        with database._connect() as conn:
            # First read also initializes a newly provisioned Supabase database.
            _ensure_postgres(conn)
            records = conn.execute(f"""
                SELECT {columns} FROM airtwin.station_observations
                WHERE station_id=%s AND observed_at >= %s::timestamptz
                ORDER BY observed_at DESC LIMIT 2200
                """, (station_id, cutoff)).fetchall()
    else:
        with closing(_sqlite()) as conn:
            records = conn.execute(f"""
                SELECT {columns} FROM station_observations
                WHERE station_id=? AND observed_at >= ?
                ORDER BY observed_at DESC LIMIT 2200
                """, (station_id, cutoff)).fetchall()
    return [
        {"station_id": r[0], "timestamp": pd.Timestamp(r[1]).isoformat(),
         "pm25": r[2], "latitude": r[3], "longitude": r[4],
         "name": r[5], "source_type": "observed"}
        for r in reversed(records)
    ]


def ingest_pune_history(stations, fetch_payload, *, max_sensors=None):
    """Fetch OpenAQ /hours for visible real sensors, independently of UI requests.

    Full 30-day backfill on first discovery; later fetch recent hours.
    A bounded thread pool prevents one broken sensor blocking all others.
    """
    key = os.getenv("OPENAQ_API_KEY")
    if not key:
        return {"sensors": 0, "rows": 0, "failures": 0}
    limit = max_sensors if max_sensors is not None else int(os.getenv("LIVE_HISTORY_MAX_SENSORS", "12"))
    sensors = sorted(
        [s for s in stations if str(s.get("id", "")).startswith("openaq-")],
        key=lambda s: s.get("timestamp", ""), reverse=True
    )[:max(0, limit)]
    now = datetime.now(timezone.utc)

    def fetch_sensor(station):
        sid = station["id"].split("-", 1)[1]
        if not sid.isdigit():
            return 0
        previous = read_observations(station["id"], hours=96)
        from_time = now - timedelta(hours=720 if not previous else 8)
        payload = fetch_payload(
            f"https://api.openaq.org/v3/sensors/{sid}/hours",
            {"datetime_from": from_time.isoformat(), "datetime_to": now.isoformat(),
             "limit": 1000, "page": 1},
            {"X-API-Key": key},
        )
        rows = []
        for item in payload.get("results", []):
            # OpenAQ /hours puts the measured hour under period.datetimeFrom.
            period = item.get("period") or {}
            instant = (period.get("datetimeFrom") or item.get("datetimeFrom") or {}).get("utc")
            if instant is None or item.get("value") is None:
                continue
            rows.append({
                "station_id": station["id"], "timestamp": instant,
                "pm25": item["value"], "latitude": station["latitude"],
                "longitude": station["longitude"], "name": station["name"],
                "source_type": "observed",
            })
        return persist_observations(rows)

    collected, failures = 0, 0
    with ThreadPoolExecutor(max_workers=min(3, max(1, len(sensors)))) as workers:
        futures = [workers.submit(fetch_sensor, s) for s in sensors]
        for job in as_completed(futures):
            try:
                collected += job.result()
            except Exception:
                failures += 1
                LOG.warning("Hourly OpenAQ history request or persistence failed", exc_info=True)
    return {"sensors": len(sensors), "rows": collected, "failures": failures}


def latest_cached_monitors(candidates, *, now=None):
    clock=pd.Timestamp.now(tz='UTC') if now is None else pd.Timestamp(now)
    latest=[]
    for station in candidates:
        records=read_observations(station['id'],hours=24)
        valid=[r for r in records if 0<=(clock-pd.Timestamp(r['timestamp'])).total_seconds()<=24*3600]
        if not valid:
            continue
        row=max(valid,key=lambda r:pd.Timestamp(r['timestamp']))
        latest.append({'id':row['station_id'],'name':row['name'],'short_name':row['name'].split(',')[0],
                       'latitude':row['latitude'],'longitude':row['longitude'],'pm25':row['pm25'],
                       'timestamp':row['timestamp'],'source_type':'observed',
                       'assumptions':['OpenAQ cached hourly PM2.5 observation; original measurement time is retained.']})
    return latest
