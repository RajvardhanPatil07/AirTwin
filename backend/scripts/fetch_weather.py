"""Fetch centroid reanalysis weather, labeled separately from target provenance."""
import argparse
import json
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

def fetch_forecast_history(start, end):
    variables = [f'{column}_previous_day{day}' for day in (1, 2, 3) for column in WEATHER_COLUMNS]
    payload = get_json('https://previous-runs-api.open-meteo.com/v1/forecast', {
        'latitude': CENTROID[0], 'longitude': CENTROID[1], 'hourly': ','.join(variables),
        'start_date': str(start), 'end_date': str(pd.Timestamp(end).date() + pd.Timedelta(days=3)),
        'timezone': TIMEZONE, 'wind_speed_unit': 'ms'})
    valid_times = pd.to_datetime(payload['hourly']['time']).tz_localize(TIMEZONE)
    frames = []
    for day in (1, 2, 3):
        frame = pd.DataFrame({'timestamp': valid_times - pd.Timedelta(hours=24 * day)})
        for column in WEATHER_COLUMNS:
            frame[f'forecast_{24 * day}_{column}'] = payload['hourly'][f'{column}_previous_day{day}']
        frames.append(frame.set_index('timestamp'))
    return pd.concat(frames, axis=1).reset_index()


def fetch_forecast():
    payload = get_json("https://api.open-meteo.com/v1/forecast", {
        "latitude": CENTROID[0], "longitude": CENTROID[1],
        "hourly": ",".join(WEATHER_COLUMNS), "forecast_days": 4,
        "timezone": TIMEZONE, "wind_speed_unit": "ms"})
    frame = pd.DataFrame(payload["hourly"]).rename(columns={"time": "timestamp"})
    frame['timestamp'] = pd.to_datetime(frame.timestamp).dt.tz_localize(TIMEZONE).astype(str)
    frame['source_type'] = 'modeled'
    frame['provider'] = 'Open-Meteo forecast'
    return frame.to_dict(orient='records')


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
        try:
            archived = fetch_forecast_history(dates.min().date(), dates.max().date())
            frame = frame.merge(archived, on='timestamp', how='left', validate='one_to_one')
            LOG.info('Added issue-aligned archived forecast weather at 24/48/72h; non-null 24h temperature rows: %s', frame.forecast_24_temperature_2m.notna().sum())
        except Exception as error:
            LOG.warning('Archived forecast weather unavailable (%s); use issue-weather persistence', type(error).__name__)
    except Exception as error:
        LOG.warning("Weather unavailable (%s); falling back to sample", type(error).__name__)
        frame = sample_frame()[["timestamp", *WEATHER_COLUMNS, "weather_source_type", "weather_provider"]]
        frame = frame.drop_duplicates("timestamp")
    RAW.mkdir(parents=True, exist_ok=True)
    frame.to_csv(RAW / "weather.csv", index=False)
    LOG.info("Saved %s centroid weather hours (wind in m/s)", len(frame))
    if not args.offline:
        try:
            forecast = fetch_forecast()
            (RAW / 'weather_forecast.json').write_text(json.dumps(forecast))
            LOG.info('Saved %s forecast weather hours', len(forecast))
        except Exception as error:
            LOG.warning('Forecast weather unavailable (%s); historical model uses issue-weather persistence', type(error).__name__)

if __name__ == "__main__":
    main()
