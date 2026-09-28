"""Seasonal evaluation without modifying serving models or their model card."""
import numpy as np
import pandas as pd
from lightgbm import LGBMRegressor
from sklearn.metrics import mean_absolute_error
from app.services.features import supervised, build_features, hourly, LAGS
from app.services.model import feature_columns, evaluate
from app.services.model import (PARAMS, WEIGHTS, origin_folds, design, log_ratio,
                                raw_model_prediction, bundle_predict, metrics)


def guarded_weight(folds):
    """Reject blends that lose to persistence in any supplied selection fold."""
    if not folds:
        return 0.0
    losses = np.array([[mean_absolute_error(actual, w * model + (1 - w) * baseline)
                        for w in WEIGHTS] for actual, model, baseline in folds])
    eligible = np.all(losses <= losses[:, [0]] + 1e-12, axis=0)
    scores = np.where(eligible, losses.mean(axis=0), np.inf)
    return float(WEIGHTS[np.argmin(scores)])


def residual_band(actual, prediction):
    """Finite-sample order statistics, with the point estimate inside the band."""
    residuals = np.sort(np.log(np.clip(actual, 1, None) / np.clip(prediction, 1, None)))
    if len(residuals) < 24:
        raise ValueError('Need at least 24 calibration pairs')
    n = len(residuals)
    lower = max(0, int(np.floor((n + 1) * 0.1)) - 1)
    upper = min(n - 1, int(np.ceil((n + 1) * 0.9)) - 1)
    return min(0.0, float(residuals[lower])), max(0.0, float(residuals[upper]))


def evaluate_challenger(rows, features, start, end):
    """A frozen model and separate recent calibration window; never alters serving."""
    test = rows[rows.timestamp.between(start, end, inclusive='left')]
    if len(test) < 24:
        return None
    prior = rows[rows.timestamp < test.issue_time.min()]
    times = prior.issue_time.drop_duplicates().sort_values()
    if len(times) < 120:
        return None
    selection_start = times.iloc[int(len(times) * 0.8)]
    calibration_start = times.iloc[int(len(times) * 0.9)]
    fit = prior[prior.timestamp < selection_start]
    selection = prior[(prior.issue_time >= selection_start) & (prior.timestamp < calibration_start)]
    calibration = prior[prior.issue_time >= calibration_start]
    if len(fit) < 100 or len(selection) < 24 or len(calibration) < 24:
        return None
    folds = []
    for train, valid in origin_folds(fit):
        x, level = design(train, features)
        probe = LGBMRegressor(**PARAMS).fit(x, log_ratio(train, level))
        folds.append((valid.target.to_numpy(float), raw_model_prediction(probe, valid, features),
                      valid.persistence.to_numpy(float)))
    x, level = design(fit, features)
    model = LGBMRegressor(**PARAMS).fit(x, log_ratio(fit, level))
    folds.append((selection.target.to_numpy(float), raw_model_prediction(model, selection, features),
                  selection.persistence.to_numpy(float)))
    weight = guarded_weight(folds)
    bundle = {'model': model, 'features': features, 'weight': weight, 'q_low': 0., 'q_high': 0.}
    calibration_prediction = bundle_predict(bundle, calibration)[0]
    bundle['q_low'], bundle['q_high'] = residual_band(calibration.target.to_numpy(float), calibration_prediction)
    prediction, low, high, model_only = bundle_predict(bundle, test)
    summary = metrics(test.target.to_numpy(float), prediction, test.persistence.to_numpy(float), low, high)
    summary.update({'blend_weight': weight, 'lightgbm_only_mae': float(mean_absolute_error(test.target, model_only)),
                    'fit_rows': len(fit), 'calibration_rows': len(calibration), 'test_rows': len(test),
                    'fit_target_end': fit.timestamp.max().isoformat(),
                    'selection_rows': len(selection),
                    'selection_issue_start': selection.issue_time.min().isoformat(),
                    'selection_target_end': selection.timestamp.max().isoformat(),
                    'calibration_issue_start': calibration.issue_time.min().isoformat(),
                    'calibration_target_end': calibration.timestamp.max().isoformat(),
                    'test_issue_start': test.issue_time.min().isoformat(),
                    'interval_mean_width': float(np.mean(high - low)),
                    'calibration_coverage': float(np.mean((calibration.target >= bundle_predict(bundle, calibration)[1]) &
                                                         (calibration.target <= bundle_predict(bundle, calibration)[2])) * 100)})
    return summary


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


def validate(frame, exog, horizons, policies, latency_hours=1, challenger=False):
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
                row = {'policy': policy, 'horizon': horizon, 'season': season,
                                'start': start.isoformat(), 'end_exclusive': end.isoformat(),
                                'train_target_end': train.timestamp.max().isoformat(),
                                'first_test_issue': test.issue_time.min().isoformat(),
                                'first_test_target': test.timestamp.min().isoformat(),
                                'last_test_target': test.timestamp.max().isoformat(),
                                'target_sources': sorted(test.source_type.unique()),
                                'features': features, **outcome['summary']}
                if challenger:
                    row['challenger'] = evaluate_challenger(rows, features, start, end)
                    row['interval_mean_width'] = float(np.mean(outcome['prediction'][2] - outcome['prediction'][1]))
                results.append(row)
                print(f'{policy} {season} {horizon}h: MAE {outcome["summary"]["mae"]:.2f}', flush=True)
    return results, skipped
