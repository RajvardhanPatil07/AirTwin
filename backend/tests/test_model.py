import sys
from pathlib import Path
import numpy as np
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.services.features import build_features, supervised
from app.services.data_loader import load_dataset
from app.services.model import choose_holdout, metrics, temporal_cv


def test_features_do_not_change_when_future_targets_or_weather_change():
    frame, _, _ = load_dataset(True)
    before = build_features(frame, 24)
    issue = frame.timestamp.iloc[200]
    changed = frame.copy()
    changed.loc[changed.timestamp > issue, 'pm25'] = 999
    changed.loc[changed.timestamp > issue, 'temperature_2m'] = -99
    pd.testing.assert_series_equal(before.loc[issue], build_features(changed, 24).loc[issue])
    assert before.loc[issue, 'lag_24'] == frame.pm25.iloc[176]
    assert before.loc[issue, 'rolling_mean_6'] == frame.pm25.iloc[194:200].mean()


def test_gaps_are_not_treated_as_one_hour_lags():
    frame, _, _ = load_dataset(True)
    frame = frame.drop(index=199)
    x = build_features(frame)
    assert np.isnan(x.loc[frame.timestamp.iloc[199], 'lag_1'])


def test_holdout_and_cv_have_strict_time_boundaries():
    frame, _, _ = load_dataset(True)
    rows = supervised(frame, 24)
    start, end, method = choose_holdout(rows)
    test = rows[rows.timestamp.between(start, end, inclusive='left')]
    train = rows[rows.timestamp < test.issue_time.min()]
    assert 'winter' in method
    assert train.timestamp.max() < test.issue_time.min()
    columns = [name for name in rows if name not in {'target', 'persistence', 'timestamp', 'issue_time', 'station_id', 'source_type'}]
    for fold in temporal_cv(train, columns):
        assert pd.Timestamp(fold['train_target_end']) < pd.Timestamp(fold['validation_issue_start'])


def test_metrics_are_computed_and_underperformance_is_negative():
    actual = np.array([10., 20., 30.])
    result = metrics(actual, actual + 5, actual + 1, actual - 2, actual + 2)
    assert result['mae'] == 5
    assert result['rmse'] == 5
    assert result['improvement_percent'] == -400
    assert result['interval_coverage'] == 100


def test_horizon_weather_uses_issue_aligned_forecast_not_future_realization():
    frame, _, _ = load_dataset(True)
    frame['forecast_24_temperature_2m'] = 17.0
    issue = frame.timestamp.iloc[200]
    frame.loc[frame.timestamp > issue, 'temperature_2m'] = 999.0
    x = build_features(frame, 24)
    assert x.loc[issue, 'horizon_temperature_2m'] == 17.0
    assert x.loc[issue, 'temperature_2m'] != 999.0
