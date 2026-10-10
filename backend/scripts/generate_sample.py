"""Generate an explicitly synthetic, reproducible offline development fixture."""
import csv
import math
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from common import LOG
from app.config import SAMPLE, TIMEZONE, CENTROID, WEATHER_COLUMNS

def main():
    fields = ["timestamp", "station_id", "station_name", "latitude", "longitude", "pm25",
              "source_type", "target_provider", *WEATHER_COLUMNS,
              "weather_source_type", "weather_provider"]
    start = datetime(2025, 10, 1, tzinfo=ZoneInfo(TIMEZONE))
    end = datetime(2026, 2, 1, tzinfo=ZoneInfo(TIMEZONE))
    rows = []
    current = start
    while current < end:
        day = (current - start).days
        wave = math.sin(2 * math.pi * current.hour / 24)
        pm25 = 45 + 12 * wave + 0.12 * day + 7 * math.sin(day / 6)
        rows.append([current.isoformat(), "demo-centroid", "Synthetic centroid demo", *CENTROID,
                     round(pm25, 2), "synthetic", "deterministic demo generator",
                     round(24 + 5 * wave, 2), round(60 - 15 * wave, 2),
                     round(2 + math.cos(day / 4), 2), (day * 13) % 360,
                     1.2 if day % 17 == 0 and current.hour == 15 else 0,
                     "synthetic", "deterministic demo generator"])
        current += timedelta(hours=1)
    SAMPLE.parent.mkdir(parents=True, exist_ok=True)
    with SAMPLE.open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(fields)
        writer.writerows(rows)
    LOG.info("Generated %s synthetic hours (%s bytes)", len(rows), SAMPLE.stat().st_size)

if __name__ == "__main__":
    main()
