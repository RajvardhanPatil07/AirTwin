import sys
from pathlib import Path
import numpy as np
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.services.validation import validation_rows


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
