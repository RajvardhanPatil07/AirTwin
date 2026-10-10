"""Train only a real OpenAQ observed-target AirTwin model; fail closed.

Must follow historical backfill + export + reanalysis weather + build_dataset.
Synthetic or CAMS target fallbacks are not eligible for operational deployment.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.config import ROOT
from app.services.data_loader import load_all
from app.services.model import train


def verify_observed_dataset(frame, min_station_hours=720):
    if frame.empty or set(frame.source_type) != {"observed"}:
        raise ValueError("Training refused: targets must be exclusively OBSERVED, not CAMS or synthetic")
    if "target_provider" not in frame or set(frame.target_provider.dropna()) != {"OpenAQ"}:
        raise ValueError("Training refused: missing or non-OpenAQ target provenance")
    if not frame.station_id.astype(str).str.fullmatch(r"openaq-[0-9]+").all():
        raise ValueError("Training refused: target station IDs must be numeric OpenAQ sensors")
    coverage = frame.groupby("station_id").timestamp.nunique()
    if coverage.empty or int(coverage.max()) < min_station_hours:
        raise ValueError(
            f"Training refused: need {min_station_hours} real distinct hours on one station; "
            f"best available is {int(coverage.max()) if not coverage.empty else 0}"
        )
    if "weather_source_type" not in frame or (frame.weather_source_type == "synthetic").any():
        raise ValueError("Training refused: synthetic or unprovenanced weather is not allowed")
    if (frame.weather_source_type == "modeled").sum() < 300:
        raise ValueError("Training refused: insufficient modeled reanalysis weather covariates")
    return int(coverage.max())


def main():
    frame, warnings, fingerprint, exog = load_all(force_sample=False)
    longest = verify_observed_dataset(frame)
    print(f"Training on {len(frame)} genuine observed station-hours; "
          f"most complete monitor has {longest} recorded hours.")
    artifact = train(frame, fingerprint, warnings, ROOT / "docs/model_card.md", exog=exog)
    report = artifact["report"]
    if set(report["target_source_types"]) != {"observed"}:
        raise RuntimeError("Unsafe artifact provenance after training")
    skill = report["metrics"]
    print(f"24h held-out LightGBM blend MAE: {skill['mae']:.2f} µg/m³; "
          f"persistence: {skill['persistence_mae']:.2f} µg/m³; "
          f"change: {skill['improvement_percent']:+.1f}%.")
    print("Model is only eligible for live serving when a fresh observed station "
          "also has 49 consecutive observed hours.")
    print("Report: backend/models/metrics.json and docs/model_card.md")


if __name__ == "__main__":
    main()
