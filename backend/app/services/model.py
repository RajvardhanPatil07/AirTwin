"""Direct multi-horizon LightGBM on a level-normalized target, blended with persistence.

Why this design: the observed record starts in March 2025, so the first complete
winter is only ever seen in evaluation. Predicting raw µg/m³ forces trees to
extrapolate beyond levels they were trained on. Instead the model predicts the log
ratio of the target to the trailing 24-hour mean, from level-normalized pollution
features. Station coordinates and month/winter flags are excluded because they let
the model memorise training-period levels. Each horizon learns a blend weight with
persistence and multiplicative split-conformal intervals from purged rolling-origin
folds that all precede the holdout.
"""
import json
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from lightgbm import LGBMRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import TimeSeriesSplit
from app.config import ROOT
from app.services.features import supervised, build_features, group_for

MODELS = ROOT / 'backend/models'
ARTIFACT = MODELS / 'forecast.joblib'
VERSION = 3
HORIZONS = [*range(1, 25), 48, 72]
EVAL_HORIZONS = [1, 3, 6, 12, 24, 48, 72]
EXCLUDE = {'target', 'persistence', 'issue_time', 'timestamp', 'station_id', 'source_type',
           'latitude', 'longitude', 'month', 'month_sin', 'month_cos', 'winter'}
LEVEL_PREFIXES = ('current_', 'lag_', 'rolling_', 'cams_')
PARAMS = dict(objective='l1', n_estimators=300, learning_rate=0.03, num_leaves=15, max_depth=5,
              min_child_samples=50, subsample=0.8, subsample_freq=1, colsample_bytree=0.7,
              reg_lambda=5.0, verbosity=-1, n_jobs=4, random_state=42)
WEIGHTS = np.round(np.linspace(0, 1, 11), 2)
INTERVAL = (0.1, 0.9)


def metrics(actual, predicted, persistence, low, high):
    baseline = float(mean_absolute_error(actual, persistence))
    mae = float(mean_absolute_error(actual, predicted))
    return {'mae': mae, 'rmse': float(np.sqrt(mean_squared_error(actual, predicted))),
            'r2': float(r2_score(actual, predicted)) if len(actual) > 1 else 0.0,
            'persistence_mae': baseline,
            'improvement_percent': 100 * (1 - mae / baseline) if baseline else 0.0,
            'interval_coverage': float(np.mean((actual >= low) & (actual <= high)) * 100)}


def choose_holdout(rows):
    first, last = rows.timestamp.min(), rows.timestamp.max()
    for year in range(last.year, first.year - 2, -1):
        start = pd.Timestamp(year=year, month=11, day=1, tz=first.tz)
        end = pd.Timestamp(year=year + 1, month=2, day=1, tz=first.tz)
        if end <= last + pd.Timedelta(hours=1) and (rows.timestamp < start).sum() >= 200:
            if rows.timestamp.between(start, end, inclusive='left').sum() >= 168:
                return start, end, 'winter Nov–Jan holdout'
    times = rows.timestamp.drop_duplicates().sort_values()
    start = times.iloc[int(len(times) * 0.8)]
    return start, last + pd.Timedelta(hours=1), 'chronological last 20%; no complete winter holdout available'


def feature_columns(rows):
    return [column for column in rows if column not in EXCLUDE]


def design(rows, features):
    """Level-normalized features; returns (X, level)."""
    x = rows[features].astype(float).copy()
    level = rows['rolling_mean_24'].astype(float).clip(lower=1.0).to_numpy()
    for column in features:
        if column.startswith(LEVEL_PREFIXES):
            x[column] = x[column].to_numpy() / level
    return x, level


def log_ratio(rows, level):
    return np.log(rows.target.astype(float).clip(lower=1.0).to_numpy() / level)


def raw_model_prediction(model, rows, features):
    x, level = design(rows, features)
    return np.maximum(level * np.exp(model.predict(x)), 0.0)


def bundle_predict(bundle, rows):
    """Blend + intervals for a feature frame; returns (blend, low, high, model_only)."""
    model_only = raw_model_prediction(bundle['model'], rows, bundle['features'])
    persistence = rows['current_pm25'].astype(float).to_numpy()
    # A gap in the trailing 24 h window leaves no level to rescale by; fall back to persistence.
    model_only = np.where(np.isfinite(model_only), model_only, persistence)
    weight = bundle['weight']
    blend = np.maximum(weight * model_only + (1 - weight) * persistence, 0.0)
    low = blend * np.exp(bundle['q_low'])
    high = blend * np.exp(bundle['q_high'])
    return blend, low, high, model_only


def origin_folds(rows, splits=3):
    """Rolling-origin folds; each fit set's targets end before its validation issue times."""
    times = rows.issue_time.drop_duplicates().sort_values().to_numpy()
    for train_index, validation_index in TimeSeriesSplit(n_splits=splits).split(times):
        start, end = times[validation_index[0]], times[validation_index[-1]]
        fit = rows[rows.issue_time.isin(times[train_index]) & (rows.timestamp < start)]
        valid = rows[rows.issue_time.between(start, end)]
        if len(fit) >= 50 and len(valid) >= 24:
            yield fit, valid


def fit_bundle(rows, features):
    """Blend weight and conformal residuals come from out-of-sample rolling-origin folds."""
    predictions, persistence, actual = [], [], []
    for fit, valid in origin_folds(rows):
        fit_x, fit_level = design(fit, features)
        probe = LGBMRegressor(**PARAMS).fit(fit_x, log_ratio(fit, fit_level))
        predictions.append(raw_model_prediction(probe, valid, features))
        persistence.append(valid.current_pm25.astype(float).to_numpy())
        actual.append(valid.target.astype(float).to_numpy())
    if predictions:
        model_only, persistence, actual = (np.concatenate(v) for v in (predictions, persistence, actual))
        scores = [mean_absolute_error(actual, w * model_only + (1 - w) * persistence) for w in WEIGHTS]
        weight = float(WEIGHTS[int(np.argmin(scores))])
        blend = np.maximum(weight * model_only + (1 - weight) * persistence, 1.0)
        residual = np.log(np.clip(actual, 1.0, None) / blend)
        q_low, q_high = (float(np.quantile(residual, q)) for q in INTERVAL)
        calibration_rows, calibration_mae = len(actual), float(min(scores))
    else:
        weight, q_low, q_high, calibration_rows, calibration_mae = 0.5, -0.5, 0.5, 0, float('nan')
    x, level = design(rows, features)
    model = LGBMRegressor(**PARAMS).fit(x, log_ratio(rows, level))
    return {'model': model, 'features': features, 'weight': weight, 'q_low': q_low, 'q_high': q_high,
            'calibration_rows': calibration_rows, 'calibration_mae': calibration_mae}


def temporal_cv(rows, features):
    times = rows.issue_time.drop_duplicates().sort_values().to_numpy()
    scores = []
    for train_index, validation_index in TimeSeriesSplit(n_splits=3).split(times):
        start, end = times[validation_index[0]], times[validation_index[-1]]
        # Purge targets reaching the first validation issue time across every station.
        train = rows[rows.issue_time.isin(times[train_index]) & (rows.timestamp < start)]
        valid = rows[rows.issue_time.between(start, end)]
        if len(train) < 50 or valid.empty:
            continue
        x, level = design(train, features)
        model = LGBMRegressor(**PARAMS).fit(x, log_ratio(train, level))
        scores.append({'train_target_end': train.timestamp.max().isoformat(),
                       'validation_issue_start': valid.issue_time.min().isoformat(),
                       'mae': float(mean_absolute_error(valid.target, raw_model_prediction(model, valid, features))),
                       'persistence_mae': float(mean_absolute_error(valid.target, valid.persistence)),
                       'train_rows': len(train), 'validation_rows': len(valid)})
    return scores


def evaluate(base, features, start, end):
    test = base[base.timestamp.between(start, end, inclusive='left')]
    # The first evaluated origin cannot see a target used during training.
    train_rows = base[base.timestamp < test.issue_time.min()] if len(test) else base.iloc[:0]
    if len(train_rows) < 100 or len(test) < 24:
        return None
    bundle = fit_bundle(train_rows, features)
    blend, low, high, model_only = bundle_predict(bundle, test)
    actual, persistence = test.target.to_numpy(float), test.persistence.to_numpy(float)
    hourly_means = train_rows.groupby('hour').target.mean()
    seasonal = test.hour.map(hourly_means).fillna(train_rows.target.mean()).to_numpy(float)
    summary = metrics(actual, blend, persistence, low, high)
    summary.update({'lightgbm_only_mae': float(mean_absolute_error(actual, model_only)),
                    'seasonal_mae': float(mean_absolute_error(actual, seasonal)),
                    'blend_weight': bundle['weight'], 'test_rows': len(test), 'train_rows': len(train_rows)})
    cams = test.cams_target.to_numpy(float) if 'cams_target' in test else np.full(len(test), np.nan)
    if np.isfinite(cams).mean() > 0.8:
        mask = np.isfinite(cams)
        summary['cams_mae'] = float(mean_absolute_error(actual[mask], cams[mask]))
    return {'bundle': bundle, 'test': test, 'train': train_rows, 'summary': summary,
            'prediction': (blend, low, high), 'seasonal': seasonal}


def train(frame, fingerprint, warnings, report_path=None, exog=None):
    cache = {}
    def rows_for(horizon):
        if horizon not in cache:
            cache[horizon] = supervised(frame, horizon, exog)
        return cache[horizon]
    base = rows_for(24)
    if len(base) < 300:
        raise ValueError('Need at least 300 usable hourly examples for training and evaluation')
    features = feature_columns(base)
    start, end, method = choose_holdout(base)
    main = evaluate(base, features, start, end)
    if main is None:
        raise ValueError('Insufficient chronological train/test coverage')
    test, train_rows = main['test'], main['train']
    blend, low, high = main['prediction']
    results = test[['station_id', 'timestamp', 'issue_time', 'target', 'persistence', 'source_type']].copy()
    results['predicted'], results['p10'], results['p90'] = blend, low, high
    skill = []
    for horizon in EVAL_HORIZONS:
        outcome = main if horizon == 24 else evaluate(rows_for(horizon), features, start, end)
        if outcome is not None:
            skill.append({'horizon': horizon, **outcome['summary']})
    has_cams = bool(exog is not None and 'cams_pm25' in exog and base.cams_target.notna().mean() > 0.5)
    has_blh = bool(exog is not None and 'boundary_layer_height' in exog and base.boundary_layer_height.notna().mean() > 0.5)
    report = {'method': method, 'horizon_hours': 24, 'fingerprint': fingerprint,
              'model': 'LightGBM direct horizons · log-ratio target · persistence blend · split-conformal bands',
              'train_rows': len(train_rows), 'test_rows': len(test),
              'train_target_end': train_rows.timestamp.max().isoformat(),
              'test_issue_start': test.issue_time.min().isoformat(),
              'test_start': start.isoformat(), 'test_end_exclusive': end.isoformat(),
              'target_source_types': sorted(frame.source_type.unique()), 'warnings': warnings,
              'covariates': {'cams_pm25': has_cams, 'boundary_layer_height': has_blh},
              'weather_evaluation': ('Archived 24h previous-run forecast weather aligned to its issue time; missing values use issue-weather persistence.' if 'forecast_24_temperature_2m' in frame else 'Issue-time weather persistence; no future realized weather is used.'),
              'metrics': main['summary'],
              'seasonal_hourly_mean': {'mae': float(mean_absolute_error(test.target, main['seasonal'])),
                                       'rmse': float(np.sqrt(mean_squared_error(test.target, main['seasonal']))),
                                       'r2': float(r2_score(test.target, main['seasonal']))},
              'skill': skill, 'cv': temporal_cv(train_rows, features), 'stations': {}}
    for station_id, data in results.groupby('station_id'):
        report['stations'][station_id] = metrics(data.target.to_numpy(), data.predicted.to_numpy(),
                                                data.persistence.to_numpy(), data.p10.to_numpy(), data.p90.to_numpy())
    production = {}
    for horizon in HORIZONS:
        rows = rows_for(horizon)
        if len(rows) >= 100:
            production[horizon] = fit_bundle(rows, features)
        if horizon not in EVAL_HORIZONS:
            cache.pop(horizon, None)
    artifact = {'models': production, 'features': features, 'report': report,
                'backtest': results, 'fingerprint': fingerprint, 'validation_models': main['bundle'], 'version': VERSION}
    MODELS.mkdir(parents=True, exist_ok=True)
    joblib.dump(artifact, ARTIFACT)
    (MODELS / 'metrics.json').write_text(json.dumps(report, indent=2))
    if report_path:
        write_card(report, report_path)
    return artifact


def write_card(report, path):
    lines = ['# Generated model card', '', 'Generated by `backend/scripts/train_model.py`; metrics below are computed.',
             '', f"Model: {report['model']}.",
             f"Target provenance: **{', '.join(report['target_source_types']).upper()}**.",
             f"Validation: {report['method']}.",
             f"Holdout: {report['test_start']} to {report['test_end_exclusive']} (exclusive).",
             f"Training rows (24 h): {report['train_rows']}; test rows: {report['test_rows']}.",
             f"Covariates: CAMS PM2.5 {'used' if report['covariates']['cams_pm25'] else 'unavailable'}; "
             f"boundary-layer height {'used' if report['covariates']['boundary_layer_height'] else 'unavailable'}.",
             f"Dataset fingerprint: `{report['fingerprint']}`.", '',
             '## Skill by horizon (pooled holdout)', '',
             '| Horizon | AirTwin MAE | LightGBM only | Persistence | Seasonal mean | CAMS raw | Improvement vs persistence | Blend weight | p10–p90 coverage |',
             '| --- | --- | --- | --- | --- | --- | --- | --- | --- |']
    for row in report['skill']:
        cams = f"{row['cams_mae']:.2f}" if 'cams_mae' in row else '—'
        lines.append(f"| {row['horizon']} h | {row['mae']:.2f} | {row['lightgbm_only_mae']:.2f} | {row['persistence_mae']:.2f} | "
                     f"{row['seasonal_mae']:.2f} | {cams} | {row['improvement_percent']:+.1f}% | {row['blend_weight']:.1f} | {row['interval_coverage']:.1f}% |")
    lines += ['', '## 24-hour detail by station', '',
              '| Scope | MAE | RMSE | R² | Persistence MAE | Improvement % | Band coverage % |',
              '| --- | --- | --- | --- | --- | --- | --- |']
    for name, values in [('pooled', report['metrics']), *report['stations'].items()]:
        lines.append('| ' + name + ' | ' + ' | '.join(f'{values[key]:.2f}' for key in
                     ['mae', 'rmse', 'r2', 'persistence_mae', 'improvement_percent', 'interval_coverage']) + ' |')
    lines.extend(['', 'Negative improvement means the model loses to persistence.',
                  'Concentration errors are µg/m³. Band coverage is measured on the holdout; the target is 80%.',
                  '', '## Method', '',
                  '- Target: log(PM2.5 at target hour / trailing 24 h mean), L1 objective.',
                  '- Pollution features are divided by the same trailing mean, so winter levels are not extrapolation.',
                  '- Station coordinates and month/winter flags are excluded to avoid memorising training-period levels.',
                  '- Per horizon, a persistence blend weight and multiplicative split-conformal bands are chosen from out-of-sample predictions on three purged rolling-origin folds inside the training period.',
                  '- CAMS PM2.5 (Open-Meteo) at issue and target hour plus ERA5 boundary-layer height are MODELED covariates.',
                  f"- {report['weather_evaluation']}",
                  '- Training-only target-hour means form the seasonal baseline. CV purges targets crossing validation origins.',
                  '- Serving models refit on all available data; held-out metrics use separate pre-holdout models.',
                  '- Direct models cover hours 1–24, 48 and 72; intervening 25–71-hour points are linearly interpolated.',
                  '', '## Warnings', '', *[f'- {warning}' for warning in report['warnings']],
                  '', '## Limitations', '',
                  'Proxy source attribution is separate from SHAP feature explanation. No causal or health benefit is validated.',
                  'Archived CAMS values are short-lead provider forecasts; operational CAMS at 48–72 h lead is less accurate, so long-horizon skill here is optimistic.',
                  'Reanalysis covariates at historical issue time are retrospective; provider publication delay is not simulated.',
                  'Sparse stations, gaps, synthetic population and model-target fallback constrain real-world interpretation.',
                  '', '## Cross-validation', '', '```json', json.dumps(report['cv'], indent=2), '```',
                  '', '## Seasonal hourly mean baseline', '', '```json', json.dumps(report['seasonal_hourly_mean'], indent=2), '```'])
    Path(path).write_text('\n'.join(lines) + '\n')


def load_or_train(frame, fingerprint, warnings, exog=None):
    if ARTIFACT.exists():
        try:
            artifact = joblib.load(ARTIFACT)
        except Exception:
            artifact = {}
        if artifact.get('fingerprint') == fingerprint and artifact.get('version') == VERSION:
            return artifact
    return train(frame, fingerprint, warnings, exog=exog)


def predict(artifact, station, hours, exog=None):
    anchors = {}
    for horizon, bundle in artifact['models'].items():
        x = build_features(station, horizon, exog).iloc[[-1]]
        blend, low, high, _ = bundle_predict(bundle, x)
        anchors[horizon] = (float(blend[0]), float(low[0]), float(high[0]))
    xp = sorted(anchors)
    return [tuple(float(np.interp(h, xp, [anchors[k][j] for k in xp])) for j in range(3))
            for h in range(1, hours + 1)]


def explain_features(artifact, station, exog=None):
    bundle = artifact['models'][24]
    features = bundle['features']
    x_raw = build_features(station, 24, exog).iloc[[-1]]
    x, level = design(x_raw, features)
    # Exact TreeSHAP in the model's log-ratio space, mapped proportionally to µg/m³.
    contributions = bundle['model'].booster_.predict(x, pred_contrib=True)[0]
    base_log, parts = float(contributions[-1]), contributions[:-1]
    base_ug = float(level[0] * np.exp(base_log))
    model_ug = float(level[0] * np.exp(base_log + parts.sum()))
    scale = (model_ug - base_ug) / parts.sum() if abs(parts.sum()) > 1e-9 else 0.0
    groups = {'persistence': 0.0, 'weather': 0.0, 'temporal': 0.0, 'cams': 0.0}
    for name, value in zip(features, parts):
        key = group_for(name)
        groups[key] = groups.get(key, 0.0) + float(value) * scale
    return {'groups': groups, 'base_value': base_ug, 'prediction': base_ug + sum(groups.values()),
            'blend_weight': bundle['weight'],
            'method': 'LightGBM exact TreeSHAP (log-ratio space, mapped to µg/m³; model component before persistence blend)'}
