"""Download hourly PM2.5 station data; preserve usable partial downloads."""
import argparse
import os
import pandas as pd
from common import LOG, pages, sample_frame
from app.config import RAW, BBOX

API = "https://api.openaq.org/v3"
COLUMNS = ["timestamp", "station_id", "station_name", "latitude", "longitude",
           "pm25", "source_type", "target_provider"]

def fetch(start, end):
    key = os.getenv("OPENAQ_API_KEY")
    if not key:
        raise RuntimeError("OPENAQ_API_KEY is missing")
    headers = {"X-API-Key": key}
    rows = []
    stations = 0
    for location in pages(f"{API}/locations", {"bbox": ",".join(map(str, BBOX))}, headers):
        coordinates = location.get("coordinates") or {}
        for sensor in location.get("sensors", []):
            parameter = sensor.get("parameter", {})
            if parameter.get("name") != "pm25":
                continue
            if parameter.get("units") not in ("µg/m³", "μg/m³", "ug/m3"):
                LOG.warning("Skipping sensor %s: unsupported PM2.5 units", sensor["id"])
                continue
            stations += 1
            try:
                for item in pages(f"{API}/sensors/{sensor['id']}/hours",
                                  {"datetime_from": start.isoformat(), "datetime_to": end.isoformat()}, headers):
                    timestamp = (item.get("period", {}).get("datetimeFrom") or {}).get("utc")
                    if timestamp is None:
                        continue
                    rows.append([timestamp, str(sensor["id"]), location.get("name"),
                                 coordinates.get("latitude"), coordinates.get("longitude"),
                                 item.get("value"), "observed", "OpenAQ"])
            except Exception as error:
                LOG.warning("Sensor %s failed (%s); keeping downloaded rows", sensor["id"], type(error).__name__)
    LOG.info("Found %s PM2.5 sensors; downloaded %s hourly records", stations, len(rows))
    return pd.DataFrame(rows, columns=COLUMNS)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--months", type=int, default=18)
    parser.add_argument("--offline", action="store_true")
    args = parser.parse_args()
    end = pd.Timestamp.now(tz="UTC").floor("h")
    start = end - pd.DateOffset(months=args.months)
    try:
        if args.offline:
            raise RuntimeError("offline requested")
        frame = fetch(start, end)
        if frame.empty:
            raise RuntimeError("No PM2.5 hours found")
    except Exception as error:
        LOG.warning("OpenAQ unavailable (%s); falling back to sample", type(error).__name__)
        frame = sample_frame()[COLUMNS]
    RAW.mkdir(parents=True, exist_ok=True)
    frame.to_csv(RAW / "air_quality.csv", index=False)
    LOG.info("Saved %s records to data/raw/air_quality.csv", len(frame))

if __name__ == "__main__":
    main()
