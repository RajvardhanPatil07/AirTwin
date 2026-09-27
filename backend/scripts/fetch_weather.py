"""Fetch centroid reanalysis weather, labeled separately from target provenance."""
import argparse
import pandas as pd
from common import LOG, get_json, sample_frame
from app.config import RAW, TIMEZONE, CENTROID, WEATHER_COLUMNS

def fetch(start, end):
    payload = get_json("https://archive-api.open-meteo.com/v1/archive", {
        "latitude": CENTROID[0], "longitude": CENTROID[1],
        "start_date": str(start), "end_date": str(end),
        "hourly": ",".join(WEATHER_COLUMNS), "timezone": TIMEZONE,
        "wind_speed_unit": "ms"})
    frame = pd.DataFrame(payload["hourly"]).rename(columns={"time": "timestamp"})
    frame["timestamp"] = pd.to_datetime(frame["timestamp"]).dt.tz_localize(TIMEZONE)
    frame["weather_source_type"] = "modeled"
    frame["weather_provider"] = "Open-Meteo reanalysis"
    return frame

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--offline", action="store_true")
    args = parser.parse_args()
    try:
        if args.offline:
            raise RuntimeError("offline requested")
        air = pd.read_csv(RAW / "air_quality.csv")
        dates = pd.to_datetime(air["timestamp"], utc=True).dt.tz_convert(TIMEZONE)
        frame = fetch(dates.min().date(), dates.max().date())
    except Exception as error:
        LOG.warning("Weather unavailable (%s); falling back to sample", type(error).__name__)
        frame = sample_frame()[["timestamp", *WEATHER_COLUMNS, "weather_source_type", "weather_provider"]]
        frame = frame.drop_duplicates("timestamp")
    RAW.mkdir(parents=True, exist_ok=True)
    frame.to_csv(RAW / "weather.csv", index=False)
    LOG.info("Saved %s centroid weather hours (wind in m/s)", len(frame))

if __name__ == "__main__":
    main()
