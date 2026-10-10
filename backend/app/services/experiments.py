"""Development benchmarks with fixed folds, paired rows and disjoint calibration."""
import hashlib
import json
import platform
from importlib.metadata import version

import numpy as np
import pandas as pd
from lightgbm import LGBMRegressor
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import mean_absolute_error

from app.services.model import PARAMS, design, log_ratio, raw_model_prediction, metrics
from app.services.validation import validation_rows, seasonal_windows, residual_band

ARMS = ('history', 'weather', 'weather_cams')
LOOKBACK_HOURS = 48


def arm_features(features, arm):
    if arm not in ARMS:
        raise ValueError('Unknown feature arm')
    history = [c for c in features if c.startswith(('current_', 'lag_', 'rolling_', 'hour', 'dow'))]
    weather = [c for c in features if c not in history and not c.startswith('cams_')]
    return history + (weather if arm != 'history' else []) + (
        [c for c in features if c.startswith('cams_')] if arm == 'weather_cams' else [])


def chronological_blocks(rows, start, end, lookback_hours=LOOKBACK_HOURS):
    test = rows[rows.timestamp.between(start, end, inclusive='left')]
    if len(test) < 24:
        return None
    gap = pd.Timedelta(hours=lookback_hours)
    prior = rows[rows.timestamp < test.issue_time.min() - gap]
    origins = prior.issue_time.drop_duplicates().sort_values()
    if len(origins) < 240:
        return None
    selection_start = origins.iloc[int(len(origins) * .70)]
    calibration_start = origins.iloc[int(len(origins) * .85)]
    fit = prior[prior.timestamp < selection_start - gap]
    selection = prior[(prior.issue_time >= selection_start) &
                      (prior.timestamp < calibration_start - gap)]
    calibration = prior[prior.issue_time >= calibration_start]
    if len(fit) < 100 or min(len(selection), len(calibration)) < 24:
        return None
    return fit, selection, calibration, test


def conformal_radius(actual, predicted, alpha=.2):
    """Finite-sample absolute log-residual quantile, no test-time tuning."""
    if not 0 < alpha < 1:
        raise ValueError('alpha must be between zero and one')
    residuals = np.sort(np.abs(np.log(np.maximum(actual, 1.) / np.maximum(predicted, 1.))))
    if not len(residuals) or not np.isfinite(residuals).all():
        raise ValueError('Calibration pairs must be finite and nonempty')
    rank = int(np.ceil((len(residuals) + 1) * (1 - alpha)))
    if rank > len(residuals):
        raise ValueError('Insufficient calibration pairs for the requested coverage')
    return float(residuals[rank - 1])


def summarize(actual, prediction, persistence, low, high):
    return {**metrics(actual, prediction, persistence, low, high),
            'interval_mean_width': float(np.mean(high - low)), 'n': len(actual)}


def row_digest(test):
    keys = test[['station_id', 'issue_time', 'timestamp']].astype(str)
    return hashlib.sha256(keys.to_csv(index=False).encode()).hexdigest()


def evaluate_arm(blocks, features, alpha=.2, n_estimators=300, include_challenger=True):
    fit, selection, calibration, test = blocks
    x, level = design(fit, features)
    model = LGBMRegressor(**{**PARAMS, 'n_estimators': n_estimators}).fit(x, log_ratio(fit, level))
    raw = [raw_model_prediction(model, b, features) for b in (selection, calibration, test)]
    weights = np.round(np.linspace(0, 1, 11), 2)
    scores = [mean_absolute_error(selection.target, w * raw[0] + (1 - w) * selection.persistence)
              for w in weights]
    weight = float(weights[int(np.argmin(scores))])
    hourly_mean = fit.groupby('hour').target.mean()
    cal_mean = calibration.hour.map(hourly_mean).fillna(fit.target.mean()).to_numpy(float)
    test_mean = test.hour.map(hourly_mean).fillna(fit.target.mean()).to_numpy(float)
    predictions = {
        'persistence': (calibration.persistence.to_numpy(float), test.persistence.to_numpy(float)),
        'hourly_mean': (cal_mean, test_mean),
        'lightgbm': (raw[1], raw[2]),
        'lightgbm_blend': (weight * raw[1] + (1 - weight) * calibration.persistence.to_numpy(float),
                           weight * raw[2] + (1 - weight) * test.persistence.to_numpy(float)),
    }
    if include_challenger:
        challenger = HistGradientBoostingRegressor(loss='absolute_error', max_iter=n_estimators,
            learning_rate=.03, max_leaf_nodes=15, l2_regularization=5., early_stopping=False, random_state=42)
        challenger.fit(x, log_ratio(fit, level))
        predictions['hist_gradient_boosting'] = tuple(raw_model_prediction(challenger, b, features)
                                                     for b in (calibration, test))
    actual, persistence = test.target.to_numpy(float), test.persistence.to_numpy(float)
    results = []
    for name, (cal_prediction, prediction) in predictions.items():
        cal_prediction = np.maximum(cal_prediction, 1.)
        interval_center = np.maximum(prediction, 1.)
        q_low, q_high = residual_band(calibration.target.to_numpy(float), cal_prediction)
        radius = conformal_radius(calibration.target.to_numpy(float), cal_prediction, alpha)
        empirical = (interval_center * np.exp(q_low), interval_center * np.exp(q_high))
        conformal = (interval_center * np.exp(-radius), interval_center * np.exp(radius))
        for interval, (low, high) in [('empirical_log_80', empirical), ('split_conformal_log', conformal)]:
            record = {'model': name, 'interval': interval,
                'nominal_coverage_percent': 80. if interval == 'empirical_log_80' else 100 * (1 - alpha),
                **summarize(actual, prediction, persistence, low, high),
                'blend_weight': weight if name == 'lightgbm_blend' else None,
                'calibration_parameters': [q_low, q_high] if interval == 'empirical_log_80' else [radius]}
            if interval == 'split_conformal_log':
                per_station = []
                for station_id, station in test.groupby('station_id'):
                    mask = test.station_id.to_numpy() == station_id
                    per_station.append({'station_id': str(station_id),
                        **summarize(actual[mask], prediction[mask], persistence[mask], low[mask], high[mask])})
                record['per_station'] = per_station
            results.append(record)
    return results


def run_experiments(frame, exog, horizons, policies, arms, alpha=.2, n_estimators=300,
                    latency_hours=1, max_windows=None, include_challenger=True):
    windows = list(seasonal_windows(frame))
    if not windows or set(frame.source_type.unique()) == {'synthetic'}:
        times = frame.timestamp.drop_duplicates().sort_values()
        windows = [('sample_last_20_percent', times.iloc[int(len(times) * .8)],
                    times.iloc[-1] + pd.Timedelta(hours=1))]
    if max_windows:
        windows = windows[-max_windows:]
    results, skipped = [], []
    for policy in policies:
        for horizon in horizons:
            rows, available = validation_rows(frame, horizon, policy, exog, latency_hours)
            for season, start, end in windows:
                blocks = chronological_blocks(rows, start, end)
                if blocks is None:
                    skipped.append({'policy': policy, 'horizon': horizon, 'season': season,
                                    'reason': 'Insufficient purged fit/selection/calibration/test data'})
                    continue
                fit, selection, calibration, test = blocks
                bounds = {name: {'n': len(b), 'issue_start': b.issue_time.min().isoformat(),
                                  'target_end': b.timestamp.max().isoformat()}
                          for name, b in zip(('fit', 'selection', 'calibration', 'test'), blocks)}
                for arm in arms:
                    if policy == 'pollution_only' and arm != 'history':
                        continue
                    features = arm_features(available, arm)
                    added = set(features) - set(arm_features(available, 'history'))
                    if arm != 'history' and (not added or not fit[list(added)].notna().any().any()):
                        skipped.append({'policy': policy, 'horizon': horizon, 'season': season,
                            'arm': arm, 'reason': 'Requested covariates unavailable; not relabelled as an ablation'})
                        continue
                    if arm == 'weather_cams' and not fit[[c for c in features if c.startswith('cams_')]].notna().any().any():
                        continue
                    evaluated = evaluate_arm(blocks, features, alpha, n_estimators, include_challenger)
                    for result in evaluated:
                        results.append({'policy': policy, 'season': season, 'horizon': horizon, 'arm': arm,
                            'features': features, 'feature_nonnull_fraction_fit': fit[features].notna().mean().to_dict(),
                            'test_row_fingerprint': row_digest(test),
                            'target_sources': sorted(test.source_type.unique().tolist()),
                            'blocks': bounds, **result})
                    print(f'{policy} {season} +{horizon}h {arm}: {len(test)} paired test rows', flush=True)
    return results, skipped


def environment():
    return {'python': platform.python_version(), **{p: version(p) for p in
        ('numpy', 'pandas', 'scikit-learn', 'lightgbm')}}


def verify_reference(reference, current, tolerance=1e-8):
    """Compare deterministic report fields; no timestamps or fit durations are recorded."""
    mismatches = []
    def compare(a, b, path):
        if isinstance(a, dict) and isinstance(b, dict):
            if set(a) != set(b):
                mismatches.append(f'{path}: different keys')
                return
            for key in a:
                compare(a[key], b[key], f'{path}.{key}')
        elif isinstance(a, list) and isinstance(b, list):
            if len(a) != len(b):
                mismatches.append(f'{path}: different lengths')
                return
            for i, (x, y) in enumerate(zip(a, b)):
                compare(x, y, f'{path}[{i}]')
        elif isinstance(a, (int, float)) and not isinstance(a, bool) and isinstance(b, (int, float)):
            if not np.isclose(a, b, rtol=0, atol=tolerance):
                mismatches.append(f'{path}: {a} != {b}')
        elif a != b:
            mismatches.append(f'{path}: values differ')
    compare(reference, current, 'report')
    return mismatches


def write_report(report, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, separators=(',', ':'), allow_nan=False) + '\n')
    lines = ['# Paired forecast experiments', '',
        'Development evidence on previously inspected data; serving models are unchanged.',
        'Fit, blend selection, calibration and test are chronological and disjoint, with a 48-hour lookback embargo.',
        'Each feature arm and model uses the same test rows within a policy/season/horizon.',
        'History/weather/CAMS comparisons are predictive ablations, not source apportionment.', '',
        '| Policy | Season | h | Arm | Model | MAE | Persistence MAE | Skill % | Interval | Coverage % | Width |',
        '| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |']
    for r in report['results']:
        lines.append(f'| {r["policy"]} | {r["season"]} | {r["horizon"]} | {r["arm"]} | {r["model"]} | '
                     f'{r["mae"]:.2f} | {r["persistence_mae"]:.2f} | {r["improvement_percent"]:+.1f} | '
                     f'{r["interval"]} | {r["interval_coverage"]:.1f} | {r["interval_mean_width"]:.2f} |')
    lines += ['', '## Interpretation', '', *['- ' + s for s in report['limitations']], '',
              'Station metrics for the split-conformal interval, feature completeness, exact fold boundaries and paired-row hashes are in the JSON.',
              f'Skipped evaluations: {len(report["skipped"])} (reasons in JSON).']
    path.with_suffix('.md').write_text('\n'.join(lines) + '\n')
