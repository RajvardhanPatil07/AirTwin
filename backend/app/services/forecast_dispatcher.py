"""Live observed-target LightGBM when defensible; explicit CAMS fallback otherwise."""
from __future__ import annotations

from functools import lru_cache
import logging
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from app.services.live_features import LiveFeatureError, build_live_input
from app.services.live_observations import read_observations
from app.services.model import ARTIFACT, VERSION, predict, explain_features
from app.services.retraining import LIVE_ARTIFACT
from app.services.spatial import distance_km

LOG = logging.getLogger("airtwin.live.dispatch")


@lru_cache(maxsize=3)
def _load_artifact(path, last_modified_ns):
    try:
        return joblib.load(path)  # Load only the locally trusted trainer output.
    except Exception as exc:
        raise LiveFeatureError("model_artifact_unreadable") from exc


def _verified_file(file):
    if not file.is_file():
        raise LiveFeatureError("observed_model_artifact_missing")
    artifact = _load_artifact(str(file), file.stat().st_mtime_ns)
    if not isinstance(artifact, dict) or artifact.get("version") != VERSION:
        raise LiveFeatureError("model_artifact_version_mismatch")
    if set(artifact.get("report", {}).get("target_source_types", [])) != {"observed"}:
        raise LiveFeatureError("model_artifact_not_observed_target")
    if not artifact.get("models") or 24 not in artifact["models"]:
        raise LiveFeatureError("missing_model_horizons")
    return artifact


def verified_artifact(path=ARTIFACT):
    # Retained historical model is still used for replay/backtests. The
    # independently validated live candidate takes precedence *only* for
    # observed-station inference. A failed live read falls back safely.
    if Path(path) == ARTIFACT and LIVE_ARTIFACT.is_file():
        try:
            return _verified_file(LIVE_ARTIFACT)
        except (LiveFeatureError, OSError, ValueError, EOFError):
            LOG.warning("Invalid live retrained artifact; using historical fallback")
    return _verified_file(Path(path))


def nearest_provider_frame(station, provider_points, all_frame):
    """Find modeled covariates near an observed station, not a fake monitor."""
    if not provider_points:
        raise LiveFeatureError("missing_cams_references")
    ref = min(provider_points.values(), key=lambda p: distance_km(
        station["latitude"], station["longitude"], p["latitude"], p["longitude"]))
    return all_frame[all_frame.station_id == ref["id"]].copy()


def run_observed_station_forecast(station, provider_frame, hours, *,
                                  model_path=ARTIFACT, observation_reader=None, now=None):
    """Return (forecast, None), or (None, clear reason).

    Only observed OpenAQ sensor IDs qualify. Grids and CAMS-only locations
    retain the existing explicitly labeled provider forecast.
    """
    if (not station or station.get("source_type") != "observed"
            or not str(station.get("id", "")).startswith("openaq-")):
        return None, "location_has_no_observed_sensor"
    reader = observation_reader or read_observations
    try:
        artifact = verified_artifact(model_path)
        observations = reader(station["id"], hours=96)
        frame, exog, origin, reference = build_live_input(
            observations, provider_frame, artifact, hours=hours, now=now)
        comparisons=artifact['report'].get('skill',[])
        comparison=next((r for r in comparisons if r.get('horizon')==hours),None)
        use_model=bool(comparison and comparison.get('mae',float('inf'))<comparison.get('persistence_mae',0))
        outputs = predict(artifact, frame, hours, exog) if use_model else [(float(frame.pm25.iloc[-1]),None,None)]*hours
        if len(outputs) != hours or any(
            not np.isfinite(point[0]) or (use_model and (not all(np.isfinite(v) for v in point) or point[1] > point[2]))
            for point in outputs
        ):
            raise LiveFeatureError("invalid_ml_predictions")
        past = [
            {"timestamp": row.timestamp.isoformat(), "actual": float(row.pm25),
             "predicted": None, "p10": None, "p90": None, "persistence": None}
            for row in frame.tail(49).itertuples()
        ]
        future = [
            {"timestamp": (origin + pd.Timedelta(hours=i + 1)).isoformat(),
             "actual": None, "predicted": float(point[0]),
             "p10": float(point[1]) if point[1] is not None else None, "p90": float(point[2]) if point[2] is not None else None,
             "persistence": float(frame.pm25.iloc[-1])}
            for i, point in enumerate(outputs)
        ]
        try:
            shap = explain_features(artifact, frame, exog) if use_model else None
        except Exception:
            shap = None
            LOG.warning("Optional live SHAP explanation unavailable", exc_info=True)
        created = pd.Timestamp.now(tz="UTC").isoformat()
        return {
            "location_id": station["id"], "source_type": "modeled",
            "history_source_type": "observed", "history_reference": station["id"],
            "series": past + future, "shap": shap, "weather_forecast": [],
            "forecast_provider": "AirTwin LightGBM" if use_model else "Observed persistence",
            "model_id": "airtwin-lightgbm-live" if use_model else "observed-persistence",
            "model_version": str(artifact["version"]),
            "issued_at": created,
            "input_cutoff": origin.isoformat(),
            "fallback_reason": None if use_model else "LightGBM has no better eligible horizon benchmark; retaining the latest observed PM2.5 as persistence.",
            "assumptions": [
                "Recent OpenAQ hourly observations are the PM2.5 target history.",
                f"Weather and CAMS model covariates come from nearby reference {reference}.",
                "Direct LightGBM horizons 1–24, 48, 72; intervening hours interpolated." if use_model else "Persistence holds the latest observed concentration constant across the requested horizon.",
                "Prediction bands have historical calibration, not demonstrated live coverage." if use_model else "No prediction band is supplied for this persistence fallback.",
                "This is a station forecast, not an independently validated street-level estimate.",
                "The historical pooled benchmark gates future serving; selected-method accuracy on that same benchmark is not an independent test of the gate.",
            ],
        }, None
    except LiveFeatureError as exc:
        return None, str(exc)
    except Exception:
        LOG.exception("Unable to generate live LightGBM forecast for %s", station["id"])
        return None, "live_ml_inference_error"
