"""Fetch centroid boundary-layer height and the CAMS PM2.5 series used as model covariates.

Both are MODELED inputs. CAMS values past the latest archive hour are the current
provider forecast and are used only as future covariates, never as targets.
"""
import argparse
import pandas as pd
from common import LOG, get_json
from app.config import RAW, TIMEZONE, CENTROID

EXOGENOUS = RAW / "exogenous.csv"


def fetch(start, end):
    blh = get_json("https://archive-api.open-meteo.com/v1/archive", {
        "latitude": CENTROID[0], "longitude": CENTROID[1], "start_date": str(start), "end_date": str(end),
        "hourly": "boundary_layer_height", "timezone": TIMEZONE})
    cams = get_json("https://air-quality-api.open-meteo.com/v1/air-quality", {
        "latitude": CENTROID[0], "longitude": CENTROID[1], "start_date": str(start),
        "end_date": str(pd.Timestamp.now(tz=TIMEZONE).date() + pd.Timedelta(days=4)),
        "hourly": "pm2_5", "timezone": TIMEZONE})
    first = pd.DataFrame({"timestamp": blh["hourly"]["time"], "boundary_layer_height": blh["hourly"]["boundary_layer_height"]})
    second = pd.DataFrame({"timestamp": cams["hourly"]["time"], "cams_pm25": cams["hourly"]["pm2_5"]})
    frame = first.merge(second, on="timestamp", how="outer").sort_values("timestamp")
    frame["timestamp"] = pd.to_datetime(frame.timestamp).dt.tz_localize(TIMEZONE)
    return frame


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--offline", action="store_true")
    args = parser.parse_args()
    if args.offline:
        LOG.info("Offline: exogenous covariates skipped; models treat them as missing.")
        return
    try:
        air = pd.read_csv(RAW / "air_quality.csv", usecols=["timestamp"])
        dates = pd.to_datetime(air.timestamp, utc=True).dt.tz_convert(TIMEZONE)
        frame = fetch(dates.min().date(), dates.max().date())
    except Exception as error:
        LOG.warning("Exogenous covariates unavailable (%s); models treat them as missing", type(error).__name__)
        return
    RAW.mkdir(parents=True, exist_ok=True)
    frame.to_csv(EXOGENOUS, index=False)
    LOG.info("Saved %s hours of boundary-layer height and CAMS PM2.5 covariates", len(frame))


if __name__ == "__main__":
    main()
