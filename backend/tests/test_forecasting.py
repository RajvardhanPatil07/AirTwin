import numpy as np
import pandas as pd

from backend.app.services.forecasting import backtest_response, forecast_response


def sample_frame(hours=420):
    timestamps = pd.date_range("2026-01-01", periods=hours, freq="h", tz="Asia/Kolkata")
    x = np.arange(hours)
    pm25 = 72 + 18 * np.sin(2 * np.pi * x / 24) + 0.025 * x + 4 * np.sin(2 * np.pi * x / (24 * 7))
    return pd.DataFrame(
        {
            "timestamp": timestamps,
            "station_id": "station-a",
            "station_name": "Observed test station",
            "latitude": 18.62,
            "longitude": 73.84,
            "pm25": pm25,
            "source_type": "observed",
            "target_provider": "test fixture",
            "temperature_2m": 25 + 4 * np.sin(2 * np.pi * x / 24),
            "relative_humidity_2m": 60 - 8 * np.sin(2 * np.pi * x / 24),
            "wind_speed_10m": 2.5 + 0.3 * np.cos(x / 8),
            "wind_direction_10m": (x * 11) % 360,
            "precipitation": np.where((x % 120) == 0, 1.2, 0.0),
            "weather_source_type": "modeled",
            "weather_provider": "test fixture",
        }
    )


def test_chronological_backtest_has_real_baseline_and_provenance():
    result = backtest_response(sample_frame(), "station-a")
    assert result["target_source_type"] == "observed"
    assert result["source_type"] == "modeled"
    assert len(result["series"]) >= 48
    assert result["metrics"]["mae"] >= 0
    assert result["metrics"]["persistence_mae"] >= 0
    timestamps = [pd.Timestamp(point["timestamp"]) for point in result["series"]]
    assert timestamps == sorted(timestamps)


def test_recursive_forecast_returns_requested_horizon_and_modeled_labels():
    result = forecast_response(sample_frame(), "station-a", 24)
    predicted = [point for point in result["series"] if point["predicted"] is not None]
    assert len(predicted) == 24
    assert result["history_source_type"] == "observed"
    assert result["source_type"] == "modeled"
    assert all(point["actual"] is None for point in predicted)
