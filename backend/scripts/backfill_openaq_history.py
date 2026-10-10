"""One-time bounded OpenAQ history backfill, separate from hourly live refresh.

Run from the repository root with DATABASE_URL and OPENAQ_API_KEY in .env:
    python backend/scripts/backfill_openaq_history.py --days 45 --max-sensors 23

Uses existing discovered PCMC sensors; does not fabricate fresh observations.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services import database
from app.services.live_observations import ingest_pune_history
from app.services.state_data import PUNE_CACHE
from common import get_json


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--days", type=int, default=45, help="Historical lookback, 1-90 days")
    parser.add_argument("--max-sensors", type=int, default=23, help="Maximum discovered PCMC sensors")
    args = parser.parse_args()

    if not os.getenv("OPENAQ_API_KEY"):
        raise SystemExit("OPENAQ_API_KEY missing from .env")
    if not database.configured():
        raise SystemExit("DATABASE_URL missing: refusing to backfill ephemeral SQLite")
    status = database.status()
    if not status.get("connected"):
        raise SystemExit("Supabase PostgreSQL unreachable. Connect via working network and retry.")
    payload = database.load_latest_snapshot("pcmc")
    if payload is None and PUNE_CACHE.exists():
        payload = json.loads(PUNE_CACHE.read_text(encoding="utf-8"))
    candidates = (payload or {}).get("history_sensor_candidates", [])
    if not candidates:
        raise SystemExit("No PCMC sensors discovered yet. Start the backend, wait for its refresh and retry.")

    print(f"Starting observed PM2.5 backfill for up to {min(args.max_sensors, len(candidates))} "
          f"OpenAQ sensors over {args.days} days.")
    print("These records are historical OBSERVED targets, not current live readings.")
    summary = ingest_pune_history(candidates, get_json,
                                  max_sensors=args.max_sensors, backfill_days=args.days)
    print("Backfill:", json.dumps(summary))
    with database._connect() as conn:
        count, stations, first, last = conn.execute("""
            SELECT count(*), count(DISTINCT station_id),
                   min(observed_at), max(observed_at)
            FROM airtwin.station_observations
        """).fetchone()
    print(f"Stored total: {count} station-hours across {stations} sensors")
    print(f"Measurement window: {first} to {last}")
    if summary["failures"]:
        raise SystemExit("Some sensors failed; already saved rows are retained. Check errors above.")
    if not summary["rows"]:
        print("No new hours returned in this window. OpenAQ source may not have newer data.")


if __name__ == "__main__":
    main()
