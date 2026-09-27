"""Direct LightGBM forecasts, chronological holdout, quantiles and SHAP."""
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
HORIZONS = [*range(1, 25), 48, 72]
EXCLUDE = {'target', 'persistence', 'issue_time', 'timestamp', 'station_id', 'source_type'}
PARAMS = dict(n_estimators=100, learning_rate=0.05, num_leaves=15,
              max_depth=5, min_child_samples=20, verbosity=-1, n_jobs=2, random_state=42)


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
        model = LGBMRegressor(**PARAMS).fit(train[features], train.target)
        scores.append({'train_target_end': train.timestamp.max().isoformat(),
                       'validation_issue_start': valid.issue_time.min().isoformat(),
                       'mae': float(mean_absolute_error(valid.target, model.predict(valid[features]))),
                       'train_rows': len(train), 'validation_rows': len(valid)})
    return scores


def fit_models(rows, features):
    models = {}
    for name, alpha in [('mean', None), ('p10', 0.1), ('p90', 0.9)]:
        options = PARAMS if alpha is None else {**PARAMS, 'objective': 'quantile', 'alpha': alpha}
        models[name] = LGBMRegressor(**options).fit(rows[features], rows.target)
    return models


def train(frame, fingerprint, warnings, report_path=None):
    base = supervised(frame, 24)
    if len(base) < 300:
        raise ValueError('Need at least 300 usable hourly examples for training and evaluation')
    features = [column for column in base if column not in EXCLUDE]
    start, end, method = choose_holdout(base)
    # The first evaluated origin cannot see a target used during training.
    test = base[base.timestamp.between(start, end, inclusive='left')]
    train_rows = base[base.timestamp < test.issue_time.min()]
    if len(train_rows) < 100 or len(test) < 48:
        raise ValueError('Insufficient chronological train/test coverage')
    validation = fit_models(train_rows, features)
    prediction = np.maximum(validation['mean'].predict(test[features]), 0)
    lower = np.maximum(validation['p10'].predict(test[features]), 0)
    upper = np.maximum(validation['p90'].predict(test[features]), 0)
    lower, upper = np.minimum(lower, upper), np.maximum(lower, upper)
    hourly_means = train_rows.groupby('hour').target.mean()
    seasonal = test.hour.map(hourly_means).fillna(train_rows.target.mean()).to_numpy()
    results = test[['station_id', 'timestamp', 'issue_time', 'target', 'persistence', 'source_type']].copy()
    results['predicted'], results['p10'], results['p90'] = prediction, lower, upper
    report = {'method': method, 'horizon_hours': 24, 'fingerprint': fingerprint,
              'train_rows': len(train_rows), 'test_rows': len(test),
              'train_target_end': train_rows.timestamp.max().isoformat(),
              'test_issue_start': test.issue_time.min().isoformat(),
              'test_start': start.isoformat(), 'test_end_exclusive': end.isoformat(),
              'target_source_types': sorted(frame.source_type.unique()), 'warnings': warnings,
              'weather_evaluation': ('Archived 24h previous-run forecast weather aligned to its issue time; missing values use issue-weather persistence.' if 'forecast_24_temperature_2m' in frame else 'Issue-time weather persistence; no future realized weather is used.'),
              'metrics': metrics(test.target.to_numpy(), prediction, test.persistence.to_numpy(), lower, upper),
              'seasonal_hourly_mean': {'mae': float(mean_absolute_error(test.target, seasonal)),
                                       'rmse': float(np.sqrt(mean_squared_error(test.target, seasonal))),
                                       'r2': float(r2_score(test.target, seasonal))},
              'cv': temporal_cv(train_rows, features), 'stations': {}}
    for station_id, data in results.groupby('station_id'):
        report['stations'][station_id] = metrics(data.target.to_numpy(), data.predicted.to_numpy(),
                                                data.persistence.to_numpy(), data.p10.to_numpy(), data.p90.to_numpy())
    production = {}
    for horizon in HORIZONS:
        rows = supervised(frame, horizon)
        if len(rows) >= 100:
            production[horizon] = fit_models(rows, features)
    artifact = {'models': production, 'features': features, 'report': report,
                'backtest': results, 'fingerprint': fingerprint, 'validation_models': validation, 'version': 2}
    MODELS.mkdir(parents=True, exist_ok=True)
    joblib.dump(artifact, ARTIFACT)
    (MODELS / 'metrics.json').write_text(json.dumps(report, indent=2))
    if report_path:
        write_card(report, report_path)
    return artifact


def write_card(report, path):
    lines = ['# Generated model card', '', 'Generated by `backend/scripts/train_model.py`; metrics below are computed.',
             '', f"Target provenance: **{', '.join(report['target_source_types']).upper()}**.",
             f"Validation: {report['method']}; direct 24-hour LightGBM.",
             f"Holdout: {report['test_start']} to {report['test_end_exclusive']} (exclusive).",
             f"Training rows: {report['train_rows']}; test rows: {report['test_rows']}.",
             f"Dataset fingerprint: `{report['fingerprint']}`.", '',
             '| Scope | MAE | RMSE | R² | Persistence MAE | Improvement % | Band coverage % |',
             '| --- | --- | --- | --- | --- | --- | --- |']
    for name, values in [('pooled', report['metrics']), *report['stations'].items()]:
        lines.append('| ' + name + ' | ' + ' | '.join(f'{values[key]:.4f}' for key in
                     ['mae', 'rmse', 'r2', 'persistence_mae', 'improvement_percent', 'interval_coverage']) + ' |')
    lines.extend(['', 'Negative improvement means the model loses to persistence.',
                  'Concentration errors are µg/m³. Quantile coverage is measured, not guaranteed.',
                  '', '## Training and evaluation', '', report['weather_evaluation'],
                  'Training-only target-hour means form the seasonal baseline. CV purges targets crossing validation origins.',
                  'Serving models refit on all available data; held-out metrics use a separate pre-holdout model.',
                  'Direct models cover hours 1–24, 48 and 72; intervening 25–71-hour points are linearly interpolated.',
                  '', '## Warnings', '', *[f'- {warning}' for warning in report['warnings']],
                  '', '## Limitations', '',
                  'Proxy source attribution is separate from SHAP feature explanation. No causal or health benefit is validated.',
                  'Reanalysis covariates at historical issue time are retrospective; this is not archived operational weather validation.',
                  'Horizon weather uses archived previous-run forecasts for 24/48/72h where available; other horizons use issue-weather persistence.',
                  'Sparse stations, gaps, synthetic population and model-target fallback constrain real-world interpretation.',
                  '', '## Cross-validation', '', '```json', json.dumps(report['cv'], indent=2), '```',
                  '', '## Seasonal hourly mean baseline', '', '```json', json.dumps(report['seasonal_hourly_mean'], indent=2), '```'])
    Path(path).write_text('\n'.join(lines) + '\n')


def load_or_train(frame, fingerprint, warnings):
    if ARTIFACT.exists():
        artifact = joblib.load(ARTIFACT)
        if artifact.get('fingerprint') == fingerprint and artifact.get('version') == 2:
            return artifact
    return train(frame, fingerprint, warnings)


def predict(artifact, station, hours, coordinates=None):
    features = artifact['features']
    anchors = {}
    for horizon, models in artifact['models'].items():
        x = build_features(station, horizon).iloc[[-1]][features]
        if coordinates:
            x.loc[:, ['latitude', 'longitude']] = coordinates
        values = {name: max(float(model.predict(x)[0]), 0) for name, model in models.items()}
        low, high = sorted([values['p10'], values['p90']])
        anchors[horizon] = (values['mean'], low, high)
    xp = sorted(anchors)
    return [tuple(float(np.interp(h, xp, [anchors[k][j] for k in xp])) for j in range(3))
            for h in range(1, hours + 1)]


def explain_features(artifact, station):
    model = artifact['models'][24]['mean']
    x = build_features(station, 24).iloc[[-1]][artifact['features']]
    # LightGBM's TreeSHAP contribution output avoids numba startup on every request.
    contributions = model.booster_.predict(x, pred_contrib=True)[0]
    groups = {'weather': 0.0, 'temporal': 0.0, 'persistence': 0.0, 'spatial': 0.0}
    for name, value in zip(artifact['features'], contributions[:-1]):
        groups[group_for(name)] += float(value)
    return {'groups': groups, 'base_value': float(contributions[-1]),
            'prediction': float(model.predict(x)[0]), 'method': 'LightGBM exact TreeSHAP'}
