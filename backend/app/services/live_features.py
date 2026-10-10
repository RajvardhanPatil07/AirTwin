"""Build training-compatible features from actual station observations.

Observed PM2.5 history is NEVER replaced with modeled CAMS values. Current
CAMS and weather provider forecasts are explanatory inputs only.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from app.config import TIMEZONE, WEATHER_COLUMNS
from app.services.features import build_features


class LiveFeatureError(ValueError):
    """An operational LightGBM prediction cannot be supported by these inputs."""


def build_live_input(observations, provider_frame, artifact, *, hours=24, now=None):
    """Return (station_frame, modeled_exogenous, last_observed_hour, provider_id)."""
    if not observations:
        raise LiveFeatureError("missing_observed_history")
    frame = pd.DataFrame(observations).copy()
    required = {"timestamp", "station_id", "pm25", "source_type", "latitude", "longitude"}
    if not required.issubset(frame):
        raise LiveFeatureError("missing_observation_columns")
    if set(frame.source_type) != {"observed"} or frame.station_id.nunique() != 1:
        raise LiveFeatureError("non_observed_or_mixed_station_history")
    if not str(frame.station_id.iloc[0]).startswith("openaq-"):
        raise LiveFeatureError("unsupported_sensor_id")
    frame["timestamp"] = pd.to_datetime(frame.timestamp, utc=True).dt.tz_convert(TIMEZONE).dt.floor("h")
    frame["pm25"] = pd.to_numeric(frame.pm25, errors="coerce")
    if frame.pm25.isna().any() or not frame.pm25.between(0, 1000).all():
        raise LiveFeatureError("invalid_observed_value")
    frame = frame.sort_values("timestamp").drop_duplicates("timestamp", keep="last")
    issue = frame.timestamp.max()
    clock = pd.Timestamp.now(tz=TIMEZONE) if now is None else pd.Timestamp(now)
    if clock.tzinfo is None:
        raise LiveFeatureError("now_requires_timezone")
    age_hours = (clock.tz_convert(TIMEZONE) - issue).total_seconds() / 3600
    if age_hours < -0.25 or age_hours > 3.0:
        raise LiveFeatureError("stale_or_future_observation")

    # Lag 48 and rolling 24 require a contiguous 49-hour observed window.
    index = pd.date_range(end=issue, periods=49, freq="h")
    recent = frame.set_index("timestamp").reindex(index)
    if recent.pm25.isna().any():
        raise LiveFeatureError("incomplete_49_hour_observed_history")
    recent.index.name = "timestamp"
    recent = recent.reset_index()

    if provider_frame is None or provider_frame.empty:
        raise LiveFeatureError("missing_cams_weather")
    provider = provider_frame.copy()
    provider["timestamp"] = pd.to_datetime(provider.timestamp, utc=True).dt.tz_convert(TIMEZONE).dt.floor("h")
    provider = provider.sort_values("timestamp").drop_duplicates("timestamp", keep="last")
    current = provider[provider.timestamp <= issue]
    if current.empty or issue - current.timestamp.iloc[-1] > pd.Timedelta(hours=3):
        raise LiveFeatureError("stale_cams_weather")
    for col in WEATHER_COLUMNS:
        if col not in provider or not pd.notna(current.iloc[-1][col]):
            raise LiveFeatureError(f"missing_issue_weather_{col}")

    weather = provider[["timestamp", *WEATHER_COLUMNS]]
    recent = pd.merge_asof(
        recent.sort_values("timestamp"), weather,
        on="timestamp", direction="backward", tolerance=pd.Timedelta(hours=3),
    )
    if recent.iloc[-1][WEATHER_COLUMNS].isna().any():
        raise LiveFeatureError("missing_current_weather")

    # Snapshot future weather (if available) at issue time. Otherwise the
    # existing build_features() explicitly uses issue-weather persistence.
    target_rows = provider.set_index("timestamp")
    for horizon in artifact["models"]:
        valid_at = issue + pd.Timedelta(hours=int(horizon))
        if valid_at in target_rows.index:
            for col in WEATHER_COLUMNS:
                recent.loc[recent.index[-1], f"forecast_{horizon}_{col}"] = target_rows.loc[valid_at, col]

    exog = target_rows[["pm25"]].rename(columns={"pm25": "cams_pm25"})
    if "boundary_layer_height" in target_rows:
        exog["boundary_layer_height"] = pd.to_numeric(
            target_rows["boundary_layer_height"], errors="coerce")
    else:
        exog["boundary_layer_height"] = np.nan
    covariates = artifact["report"].get("covariates", {})
    if covariates.get("boundary_layer_height") and not np.isfinite(
        exog["boundary_layer_height"].get(issue, np.nan)
    ):
        raise LiveFeatureError("missing_boundary_layer_height")
    if covariates.get("cams_pm25"):
        for horizon in artifact["models"]:
            future = issue + pd.Timedelta(hours=int(horizon))
            if not np.isfinite(exog["cams_pm25"].get(future, np.nan)):
                raise LiveFeatureError(f"missing_cams_target_{horizon}h")
        if not np.isfinite(exog["cams_pm25"].get(issue, np.nan)):
            raise LiveFeatureError("missing_cams_issue")

    for horizon, bundle in artifact["models"].items():
        features = build_features(recent, int(horizon), exog).iloc[-1]
        if not set(bundle["features"]).issubset(features.index):
            raise LiveFeatureError("model_feature_schema_mismatch")
        # The model may have tolerated missing nonessential historical weather
        # in training, but pollution lags and rolling mean must be real.
        if not all(np.isfinite(features.get(col, np.nan)) for col in
                   ("current_pm25", "lag_48", "rolling_mean_24")):
            raise LiveFeatureError("invalid_lag_features")
    return recent, exog, issue, str(provider.station_id.iloc[0])
