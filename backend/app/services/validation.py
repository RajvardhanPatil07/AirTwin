"""Seasonal evaluation without modifying serving models or their model card."""
import pandas as pd
from app.services.features import supervised, build_features, hourly, LAGS
from app.services.model import feature_columns, evaluate


def validation_rows(frame, horizon, policy, exog=None, latency_hours=1):
    if policy == 'retrospective':
        rows = supervised(frame, horizon, exog)
        return rows, feature_columns(rows)
    if policy != 'pollution_only':
        raise ValueError('Unknown input policy')
    if latency_hours < 0:
        raise ValueError('Latency must be nonnegative')
    # Move observation availability forward, retaining original valid-time targets.
    available = frame.copy()
    available['timestamp'] = available.timestamp + pd.Timedelta(hours=latency_hours)
    station_rows = []
    for station_id, station in available.groupby('station_id'):
        x = build_features(station, horizon, None)
        targets = hourly(frame[frame.station_id == station_id])
        target_times = x.index + pd.Timedelta(hours=horizon)
        x['target'] = targets.pm25.reindex(target_times).to_numpy()
        x['source_type'] = targets.source_type.reindex(target_times).to_numpy()
        x['persistence'] = x.current_pm25
        x['issue_time'], x['timestamp'], x['station_id'] = x.index, target_times, station_id
        required = ['target', 'current_pm25', *[f'lag_{lag}' for lag in LAGS], 'rolling_mean_24']
        station_rows.append(x.dropna(subset=required).reset_index(drop=True))
    rows = pd.concat(station_rows, ignore_index=True).sort_values(['issue_time', 'station_id']).reset_index(drop=True)
    features = [name for name in feature_columns(rows)
                if name.startswith(('current_', 'lag_', 'rolling_', 'hour', 'dow'))]
    return rows, features


def seasonal_windows(frame):
    first, last = frame.timestamp.min(), frame.timestamp.max()
    seasons = [('summer', 3, 6), ('monsoon', 6, 10), ('post_monsoon', 10, 11), ('winter', 11, 2)]
    for year in range(first.year, last.year + 1):
        for name, start_month, end_month in seasons:
            start = pd.Timestamp(year=year, month=start_month, day=1, tz=first.tz)
            end = pd.Timestamp(year=year + int(end_month < start_month), month=end_month, day=1, tz=first.tz)
            if start >= first.normalize() and end <= last + pd.Timedelta(hours=1):
                yield f'{name}_{year}', start, end


def validate(frame, exog, horizons, policies, latency_hours=1):
    windows = list(seasonal_windows(frame))
    results, skipped = [], []
    for policy in policies:
        for horizon in horizons:
            rows, features = validation_rows(frame, horizon, policy, exog, latency_hours)
            for season, start, end in windows:
                outcome = evaluate(rows, features, start, end)
                if outcome is None:
                    skipped.append({'policy': policy, 'horizon': horizon, 'season': season,
                                    'reason': 'Insufficient chronological train/test rows'})
                    continue
                train, test = outcome['train'], outcome['test']
                results.append({'policy': policy, 'horizon': horizon, 'season': season,
                                'start': start.isoformat(), 'end_exclusive': end.isoformat(),
                                'train_target_end': train.timestamp.max().isoformat(),
                                'first_test_issue': test.issue_time.min().isoformat(),
                                'first_test_target': test.timestamp.min().isoformat(),
                                'last_test_target': test.timestamp.max().isoformat(),
                                'target_sources': sorted(test.source_type.unique()),
                                'features': features, **outcome['summary']})
                print(f'{policy} {season} {horizon}h: MAE {outcome["summary"]["mae"]:.2f}', flush=True)
    return results, skipped
