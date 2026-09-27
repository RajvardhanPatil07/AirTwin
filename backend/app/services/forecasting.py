"""Leakage-aware PM2.5 forecasting and chronological validation for AirTwin.

The model is deliberately small and reproducible. It predicts one hour ahead from
information available at the issue time, then recursively rolls forward for the
24/48/72-hour dashboard horizons. Historical validation uses a chronological
holdout rather than a shuffled split.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor

from ..config import TIMEZONE, WEATHER_COLUMNS

FEATURE_COLUMNS = [
    "pm25_now",
    "pm25_lag_1",
    "pm25_lag_3",
    "pm25_lag_24",
    "pm25_roll_6",
    "pm25_roll_24",
    *[f"{column}_now" for column in WEATHER_COLUMNS],
    "hour_sin",
    "hour_cos",
    "dow_sin",
    "dow_cos",
]
MIN_SUPERVISED_ROWS = 120


@dataclass(frozen=True)
class FittedForecast:
    model: HistGradientBoostingRegressor
    residual_q10: float
    residual_q90: float
    assumptions: list[str]


def _source_type(values: Iterable[str]) -> str:
    kinds = {str(value) for value in values if pd.notna(value)}
    if kinds == {"observed"}:
        return "observed"
    if kinds == {"synthetic"}:
        return "synthetic"
    return "modeled"


def _station_frame(frame: pd.DataFrame, station_id: str) -> pd.DataFrame:
    station = frame[frame["station_id"].astype(str) == str(station_id)].copy()
    if station.empty:
        raise KeyError(f"Unknown station_id: {station_id}")
    station["timestamp"] = pd.to_datetime(
        station["timestamp"], utc=True, errors="coerce"
    ).dt.tz_convert(TIMEZONE)
    station["pm25"] = pd.to_numeric(station["pm25"], errors="coerce")
    station = station.dropna(subset=["timestamp", "pm25"]).sort_values("timestamp")
    station = station.drop_duplicates("timestamp", keep="last").set_index("timestamp")

    # Reindexing preserves real gaps as NaN instead of turning the previous row into
    # a fake one-hour lag when hours are missing.
    full_index = pd.date_range(station.index.min(), station.index.max(), freq="h")
    station = station.reindex(full_index)
    station.index.name = "timestamp"
    for column in WEATHER_COLUMNS:
        if column not in station:
            station[column] = np.nan
        station[column] = pd.to_numeric(station[column], errors="coerce")
    return station


def _feature_table(station: pd.DataFrame) -> pd.DataFrame:
    table = pd.DataFrame(index=station.index)
    table["pm25_now"] = station["pm25"]
    table["pm25_lag_1"] = station["pm25"].shift(1)
    table["pm25_lag_3"] = station["pm25"].shift(3)
    table["pm25_lag_24"] = station["pm25"].shift(24)
    table["pm25_roll_6"] = station["pm25"].rolling(6, min_periods=3).mean()
    table["pm25_roll_24"] = station["pm25"].rolling(24, min_periods=12).mean()
    for column in WEATHER_COLUMNS:
        table[f"{column}_now"] = station[column]

    hours = table.index.hour.to_numpy()
    days = table.index.dayofweek.to_numpy()
    table["hour_sin"] = np.sin(2 * np.pi * hours / 24)
    table["hour_cos"] = np.cos(2 * np.pi * hours / 24)
    table["dow_sin"] = np.sin(2 * np.pi * days / 7)
    table["dow_cos"] = np.cos(2 * np.pi * days / 7)
    return table


def _supervised(station: pd.DataFrame) -> pd.DataFrame:
    table = _feature_table(station)
    table["target"] = station["pm25"].shift(-1)
    return table.dropna(
        subset=["pm25_now", "pm25_lag_1", "pm25_lag_3", "pm25_lag_24", "target"]
    )


def _new_model() -> HistGradientBoostingRegressor:
    return HistGradientBoostingRegressor(
        learning_rate=0.055,
        max_iter=220,
        max_leaf_nodes=18,
        l2_regularization=0.7,
        min_samples_leaf=12,
        random_state=42,
    )


def _fit(table: pd.DataFrame) -> FittedForecast:
    if len(table) < MIN_SUPERVISED_ROWS:
        raise ValueError(
            f"Need at least {MIN_SUPERVISED_ROWS} usable hourly rows; got {len(table)}"
        )
    model = _new_model()
    x = table[FEATURE_COLUMNS]
    y = table["target"]
    model.fit(x, y)
    train_pred = model.predict(x)
    residuals = y.to_numpy() - train_pred
    q10, q90 = np.quantile(residuals, [0.10, 0.90])
    return FittedForecast(
        model=model,
        residual_q10=float(q10),
        residual_q90=float(q90),
        assumptions=[
            "One-hour model uses PM2.5 lags, rolling history, calendar cycles and weather available at issue time.",
            "Longer dashboard horizons are recursive one-hour forecasts; future weather is held at the latest available value.",
            "Prediction bands use empirical training residual quantiles and are diagnostic, not calibrated regulatory confidence intervals.",
        ],
    )


def _metrics(actual: np.ndarray, predicted: np.ndarray, persistence: np.ndarray, low: np.ndarray, high: np.ndarray) -> dict:
    error = predicted - actual
    mae = float(np.mean(np.abs(error)))
    rmse = float(np.sqrt(np.mean(error**2)))
    variance = float(np.sum((actual - np.mean(actual)) ** 2))
    r2 = float(1 - np.sum(error**2) / variance) if variance else 0.0
    persistence_mae = float(np.mean(np.abs(persistence - actual)))
    improvement = (
        float((1 - mae / persistence_mae) * 100) if persistence_mae else 0.0
    )
    coverage = float(np.mean((actual >= low) & (actual <= high)) * 100)
    return {
        "mae": mae,
        "rmse": rmse,
        "r2": r2,
        "persistence_mae": persistence_mae,
        "improvement_percent": improvement,
        "interval_coverage": coverage,
    }


def backtest_response(frame: pd.DataFrame, station_id: str) -> dict:
    station = _station_frame(frame, station_id)
    table = _supervised(station)
    if len(table) < MIN_SUPERVISED_ROWS:
        raise ValueError("Not enough historical coverage for chronological validation")

    # Last 20%, bounded to at least 48 hours and at most 14 days, is held out.
    holdout = min(max(48, int(round(len(table) * 0.20))), 24 * 14)
    if len(table) - holdout < 72:
        holdout = max(24, len(table) - 72)
    train = table.iloc[:-holdout]
    test = table.iloc[-holdout:]
    fitted = _fit(train)

    predicted = fitted.model.predict(test[FEATURE_COLUMNS])
    actual = test["target"].to_numpy(dtype=float)
    persistence = test["pm25_now"].to_numpy(dtype=float)
    low = predicted + fitted.residual_q10
    high = predicted + fitted.residual_q90

    series = []
    for issue_time, y, yhat, base, p10, p90 in zip(
        test.index, actual, predicted, persistence, low, high, strict=True
    ):
        series.append(
            {
                "timestamp": (issue_time + pd.Timedelta(hours=1)).isoformat(),
                "actual": float(y),
                "predicted": float(max(0, yhat)),
                "persistence": float(base),
                "p10": float(max(0, p10)),
                "p90": float(max(0, p90)),
            }
        )

    target_rows = frame[frame["station_id"].astype(str) == str(station_id)]
    return {
        "location_id": str(station_id),
        "target_source_type": _source_type(target_rows["source_type"]),
        "method": "HistGradientBoosting one-hour forecast; chronological final-20% holdout",
        "series": series,
        "metrics": _metrics(actual, predicted, persistence, low, high),
        "source_type": "modeled",
        "assumptions": [
            *fitted.assumptions,
            "The holdout is chronological and is never shuffled into training.",
            "Persistence baseline predicts the next hour as the latest PM2.5 reading.",
        ],
    }


def forecast_response(frame: pd.DataFrame, station_id: str, hours: int) -> dict:
    if hours not in {24, 48, 72}:
        raise ValueError("hours must be one of 24, 48 or 72")
    station = _station_frame(frame, station_id)
    table = _supervised(station)
    fitted = _fit(table)

    history_source = _source_type(
        frame[frame["station_id"].astype(str) == str(station_id)]["source_type"]
    )
    series = [
        {
            "timestamp": timestamp.isoformat(),
            "actual": float(value),
            "predicted": None,
            "persistence": None,
            "p10": None,
            "p90": None,
        }
        for timestamp, value in station["pm25"].dropna().tail(48).items()
    ]

    state = station.copy()
    for _ in range(hours):
        features = _feature_table(state).iloc[[-1]][FEATURE_COLUMNS]
        if features[["pm25_now", "pm25_lag_1", "pm25_lag_3", "pm25_lag_24"]].isna().any(axis=None):
            raise ValueError("Recent history has gaps that prevent recursive forecasting")
        prediction = float(max(0, fitted.model.predict(features)[0]))
        next_time = state.index[-1] + pd.Timedelta(hours=1)
        next_row = {column: np.nan for column in state.columns}
        next_row["pm25"] = prediction
        for column in WEATHER_COLUMNS:
            latest = state[column].dropna()
            next_row[column] = float(latest.iloc[-1]) if not latest.empty else np.nan
        state.loc[next_time] = next_row
        series.append(
            {
                "timestamp": next_time.isoformat(),
                "actual": None,
                "predicted": prediction,
                "persistence": None,
                "p10": float(max(0, prediction + fitted.residual_q10)),
                "p90": float(max(0, prediction + fitted.residual_q90)),
            }
        )

    return {
        "location_id": str(station_id),
        "history_source_type": history_source,
        "series": series,
        "source_type": "modeled",
        "assumptions": fitted.assumptions,
    }
