import sys
from pathlib import Path
import numpy as np
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.services.validation import validation_rows, guarded_weight, residual_band, evaluate_challenger


def test_delayed_inputs_keep_original_targets_and_exclude_retrospective_covariates():
    times = pd.date_range('2025-03-01', periods=160, freq='h', tz='Asia/Kolkata')
    frame = pd.DataFrame({'station_id': 'a', 'timestamp': times, 'pm25': np.arange(160) + 10.,
                          'source_type': 'observed', 'latitude': 18.6, 'longitude': 73.8,
                          'temperature_2m': np.arange(160) + 1000.})
    rows, features = validation_rows(frame, 24, 'pollution_only', latency_hours=2)
    original = frame.set_index('timestamp').pm25
    for row in rows.itertuples():
        assert row.current_pm25 == original.loc[row.issue_time - pd.Timedelta(hours=2)]
        assert row.target == original.loc[row.timestamp]
        assert row.persistence == row.current_pm25
    assert not any('temperature' in name or 'cams' in name or 'boundary' in name for name in features)
    changed = frame.copy()
    changed['temperature_2m'] = -9999.
    other, other_features = validation_rows(changed, 24, 'pollution_only', latency_hours=2)
    pd.testing.assert_frame_equal(rows[features], other[other_features])


def test_delay_does_not_require_an_observation_at_target_minus_latency():
    times = pd.date_range('2025-03-01', periods=160, freq='h', tz='Asia/Kolkata')
    frame = pd.DataFrame({'station_id': 'a', 'timestamp': times, 'pm25': 30.,
                          'source_type': 'observed', 'latitude': 18.6, 'longitude': 73.8})
    issue = times[80]
    frame = frame[frame.timestamp != issue + pd.Timedelta(hours=22)]
    rows, _ = validation_rows(frame, 24, 'pollution_only', latency_hours=2)
    assert issue in set(rows.issue_time)


def test_guard_rejects_model_that_only_wins_when_folds_are_pooled():
    folds = [(np.array([10., 10.]), np.array([10., 10.]), np.array([20., 20.])),
             (np.array([10., 10.]), np.array([13., 13.]), np.array([11., 11.]))]
    assert guarded_weight(folds) == 0
    assert guarded_weight([(np.array([10., 10.]), np.array([10., 10.]), np.array([20., 20.]))]) == 1
    assert guarded_weight([]) == 0


def test_challenger_selection_and_calibration_do_not_use_test_targets():
    from app.services.data_loader import load_dataset
    from app.services.model import choose_holdout
    frame, _, _ = load_dataset(True)
    rows, features = validation_rows(frame, 24, 'pollution_only')
    start, end, _ = choose_holdout(rows)
    before = evaluate_challenger(rows, features, start, end)
    changed = rows.copy()
    changed.loc[changed.timestamp.between(start, end, inclusive='left'), 'target'] = 999.
    after = evaluate_challenger(changed, features, start, end)
    assert before is not None
    assert pd.Timestamp(before['fit_target_end']) < pd.Timestamp(before['selection_issue_start'])
    assert pd.Timestamp(before['selection_target_end']) < pd.Timestamp(before['calibration_issue_start'])
    assert pd.Timestamp(before['calibration_target_end']) < pd.Timestamp(before['test_issue_start'])
    for key in ['blend_weight', 'calibration_coverage', 'interval_mean_width']:
        assert before[key] == after[key]
    assert before['mae'] != after['mae']


def test_calibration_bands_contain_point_estimate_even_with_biased_residuals():
    low, high = residual_band(np.full(30, 50.), np.full(30, 10.))
    assert low <= 0 <= high
