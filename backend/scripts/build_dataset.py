"""Clean hourly targets, merge weather, and export an offline-sized sample."""
import argparse
import pandas as pd
from common import LOG, get_json, sample_frame
from fetch_weather import fetch as fetch_weather
from app.config import RAW, PROCESSED, SAMPLE, TIMEZONE, CENTROID, WEATHER_COLUMNS, MIN_OBSERVED_HOURS

IDENTITY = ["station_id", "station_name", "latitude", "longitude", "source_type", "target_provider"]

def clean_air(frame):
    frame = frame.copy()
    frame["timestamp"] = pd.to_datetime(frame["timestamp"], utc=True, errors="coerce").dt.tz_convert(TIMEZONE)
    frame["pm25"] = pd.to_numeric(frame["pm25"], errors="coerce")
    frame = frame.dropna(subset=["timestamp", "station_id", "latitude", "longitude", "pm25"])
    frame = frame[frame["pm25"].between(0, 1000)]
    if not frame["source_type"].isin(["observed", "modeled", "synthetic"]).all():
        raise ValueError("Unknown target source_type")
    frame["timestamp"] = frame["timestamp"].dt.floor("h")
    # Missing hours stay missing: interpolation must never create 'observations'.
    return frame.groupby(["timestamp", *IDENTITY], as_index=False, dropna=False)["pm25"].mean()

def cams():
    LOG.warning("Sparse station data: trying MODELED CAMS target (last 92 days, not 18 months).")
    payload = get_json("https://air-quality-api.open-meteo.com/v1/air-quality", {
        "latitude": CENTROID[0], "longitude": CENTROID[1], "hourly": "pm2_5",
        "past_days": 92, "forecast_days": 1, "timezone": TIMEZONE})
    frame = pd.DataFrame(payload["hourly"]).rename(columns={"time": "timestamp", "pm2_5": "pm25"})
    frame["timestamp"] = pd.to_datetime(frame["timestamp"]).dt.tz_localize(TIMEZONE)
    # Exclude current/future model output from the historical training target.
    cutoff = pd.Timestamp.now(tz=TIMEZONE).normalize() - pd.Timedelta(days=5)
    frame = frame[frame["timestamp"] < cutoff]
    for column, value in {"station_id": "cams-centroid", "station_name": "City centroid (CAMS model)",
                          "latitude": CENTROID[0], "longitude": CENTROID[1],
                          "source_type": "modeled", "target_provider": "Open-Meteo CAMS"}.items():
        frame[column] = value
    weather = fetch_weather(frame.timestamp.min().date(), frame.timestamp.max().date())
    return clean_air(frame), weather

def merge(air, weather):
    weather = weather.copy()
    weather["timestamp"] = pd.to_datetime(weather["timestamp"], utc=True).dt.tz_convert(TIMEZONE).dt.floor("h")
    weather = weather.drop_duplicates("timestamp")
    result = air.merge(weather[["timestamp", *WEATHER_COLUMNS, "weather_source_type", "weather_provider"]],
                       on="timestamp", how="left", validate="many_to_one")
    result["weather_source_type"] = result.weather_source_type.fillna("missing")
    result["weather_provider"] = result.weather_provider.fillna("unavailable")
    return result.sort_values(["station_id", "timestamp"]).reset_index(drop=True)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--offline", action="store_true")
    parser.add_argument("--update-sample", action="store_true", help="Replace committed demo sample deliberately")
    args = parser.parse_args()
    try:
        if args.offline:
            raise RuntimeError("offline requested")
        air = clean_air(pd.read_csv(RAW / "air_quality.csv", dtype={"station_id": str}))
        observed = air[air.source_type == "observed"]
        if observed.empty or observed.groupby("station_id").size().max() < MIN_OBSERVED_HOURS:
            air, weather = cams()
        else:
            air = observed
            weather = pd.read_csv(RAW / "weather.csv")
        result = merge(air, weather)
        if result.empty:
            raise RuntimeError("No valid target rows")
    except Exception as error:
        LOG.warning("Dataset pipeline unavailable (%s); using offline sample", type(error).__name__)
        result = sample_frame()
    PROCESSED.mkdir(parents=True, exist_ok=True)
    result.to_parquet(PROCESSED / "dataset.parquet", index=False)
    if args.update_sample:
        subset = result.groupby("station_id", group_keys=False).tail(720)
        content = subset.to_csv(index=False)
        if len(content.encode()) >= 1_000_000:
            raise ValueError("Sample exceeds 1 MB; reduce rows or stations")
        SAMPLE.write_text(content)
    LOG.info("Exported %s rows; target provenance: %s; missing weather hours: %s", len(result),
             result.source_type.value_counts().to_dict(), result[WEATHER_COLUMNS].isna().any(axis=1).sum())

if __name__ == "__main__":
    main()
