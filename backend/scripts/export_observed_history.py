"""Safely export actual Supabase OpenAQ hours into the observed-target training CSV.

Run after a one-time backfill. Does not train or overwrite demo datasets if
fewer than --min-station-hours real hourly observations exist for every station.
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.config import RAW
from app.services import database

COLUMNS = ["timestamp", "station_id", "station_name", "latitude", "longitude",
           "pm25", "source_type", "target_provider"]


def export_dataset(days=90, min_station_hours=720, destination=None):
    if not database.configured() or not database.status().get("connected"):
        raise RuntimeError("DATABASE_URL must connect to Supabase PostgreSQL")
    if not 1 <= days <= 90:
        raise ValueError("days must be 1-90")
    if min_station_hours < 1:
        raise ValueError("min_station_hours must be positive")
    with database._connect() as conn:
        records = conn.execute("""
            SELECT observed_at, station_id, station_name, latitude, longitude, pm25
            FROM airtwin.station_observations
            WHERE observed_at >= now() - (%s * interval '1 day')
            ORDER BY station_id, observed_at
        """, (days,)).fetchall()
    frame = pd.DataFrame(records, columns=COLUMNS[:6])
    if frame.empty:
        raise RuntimeError("No real OpenAQ station-hour observations in Supabase")
    frame["timestamp"] = pd.to_datetime(frame.timestamp, utc=True)
    frame["pm25"] = pd.to_numeric(frame.pm25, errors="coerce")
    frame = frame.dropna(subset=["timestamp", "latitude", "longitude", "pm25"])
    frame = frame[frame.pm25.between(0, 1000)]
    frame = frame[frame.station_id.astype(str).str.fullmatch(r"openaq-[0-9]+")]
    frame = frame.drop_duplicates(["station_id", "timestamp"])
    counts = frame.groupby("station_id").size()
    best = int(counts.max()) if not counts.empty else 0
    if best < min_station_hours:
        raise RuntimeError(
            f"Only {best} distinct observed hours for the best-covered station; "
            f"need {min_station_hours}. Export aborted; existing training data untouched."
        )
    frame["source_type"] = "observed"
    frame["target_provider"] = "OpenAQ"
    output = Path(destination) if destination else RAW / "air_quality.csv"
    output.parent.mkdir(parents=True, exist_ok=True)
    temp = output.with_name(output.name + ".tmp")
    frame[COLUMNS].to_csv(temp, index=False)
    os.replace(temp, output)
    return output, len(frame), len(counts), best


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--days", type=int, default=90)
    parser.add_argument("--min-station-hours", type=int, default=720)
    args = parser.parse_args()
    try:
        path, rows, sensors, best = export_dataset(args.days, args.min_station_hours)
    except (RuntimeError, ValueError) as exc:
        raise SystemExit(str(exc)) from exc
    print(f"Exported {rows} genuine observed station-hours across {sensors} sensors")
    print(f"Best-covered sensor: {best} distinct hours")
    print(f"Saved {path}; all source_type=observed (no CAMS or synthetic targets)")
    print("Next: fetch_weather.py, build_dataset.py, then train_model.py.")


if __name__ == "__main__":
    main()
