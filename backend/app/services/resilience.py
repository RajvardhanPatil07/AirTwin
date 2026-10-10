"""Spatial forecasts with masked observations and a monitor excluded from development."""
from functools import lru_cache
import hashlib
import json
import joblib
import numpy as np
import pandas as pd
from lightgbm import LGBMRegressor
from app.config import ROOT, WEATHER_COLUMNS
from app.services.spatial import distance_km, idw, CONFIG

ARTIFACT = ROOT / 'backend/models/resilience.joblib'
REPORT = ROOT / 'docs/evidence/sensor_resilience.json'
VERSION = 1
HORIZONS = (6, 24, 72)
LOSSES = (0, 25, 50, 75)
FEATURES = ['spatial_pm25', 'spatial_lag24', 'own_pm25', 'own_lag24',
            'available_count', 'nearest_km', 'spatial_std', 'latitude', 'longitude',
            'hour_sin', 'hour_cos', 'dow_sin', 'dow_cos', *WEATHER_COLUMNS]


def excluded_ids(ids, loss, seed, withheld=None):
    pool = sorted(str(i) for i in ids if str(i) != withheld)
    ranked = sorted(pool, key=lambda i: hashlib.sha256(f'{seed}:{i}'.encode()).hexdigest())
    return set(ranked[:int(np.ceil(len(pool) * loss / 100))]) | ({withheld} if withheld else set())


def spatial_features(target, neighbors, issue, horizon, own=None, own_lag24=None, weather=None):
    if not neighbors:
        raise ValueError('No available PM2.5 neighbors')
    distances = np.array([distance_km(target['latitude'], target['longitude'], p['latitude'], p['longitude']) for p in neighbors])
    weights = 1 / np.maximum(distances, .15) ** 2
    values = np.array([p['pm25'] for p in neighbors], float)
    lags = np.array([p.get('lag24', p['pm25']) for p in neighbors], float)
    future = pd.Timestamp(issue) + pd.Timedelta(hours=horizon)
    row = {'spatial_pm25': float(np.average(values, weights=weights)),
           'spatial_lag24': float(np.average(lags, weights=weights)),
           'own_pm25': np.nan if own is None else own,
           'own_lag24': np.nan if own_lag24 is None else own_lag24,
           'available_count': len(neighbors), 'nearest_km': float(distances.min()),
           'spatial_std': float(values.std()), 'latitude': target['latitude'], 'longitude': target['longitude'],
           'hour_sin': np.sin(2*np.pi*future.hour/24), 'hour_cos': np.cos(2*np.pi*future.hour/24),
           'dow_sin': np.sin(2*np.pi*future.dayofweek/7), 'dow_cos': np.cos(2*np.pi*future.dayofweek/7)}
    row.update({key: (weather or {}).get(key, np.nan) for key in WEATHER_COLUMNS})
    return row


def training_rows(frame, horizon, withheld, stride=6, seed=731):
    frame = frame.copy()
    frame['station_id'] = frame.station_id.astype(str)
    pivot = frame.pivot_table(index='timestamp', columns='station_id', values='pm25').sort_index()
    metadata = frame.groupby('station_id').first()
    ids = list(pivot.columns)
    times = pivot.index[::stride]
    current = pivot.reindex(times).to_numpy(float)
    lag = pivot.reindex(times-pd.Timedelta(hours=24)).to_numpy(float)
    future = pivot.reindex(times+pd.Timedelta(hours=horizon)).to_numpy(float)
    rows = []
    for j, sid in enumerate(ids):
        target = metadata.loc[sid]
        weather = frame[frame.station_id == sid].set_index('timestamp').reindex(times)
        for loss in LOSSES:
            omitted = excluded_ids(ids, loss, seed, withheld)
            eligible = np.array([i for i, key in enumerate(ids) if key != sid and key not in omitted], int)
            if not len(eligible):
                continue
            distances = np.array([distance_km(target.latitude, target.longitude, metadata.loc[ids[i], 'latitude'], metadata.loc[ids[i], 'longitude']) for i in eligible])
            raw = current[:, eligible]
            valid = np.isfinite(raw)
            weights = valid / np.maximum(distances, .15)**2
            den = weights.sum(axis=1)
            good = (den > 0) & np.isfinite(future[:, j])
            baseline = np.divide(np.nansum(raw*weights, axis=1), den, out=np.full(len(times),np.nan), where=den>0)
            lag_raw = np.where(np.isfinite(lag[:, eligible]), lag[:, eligible], raw)
            lagged = np.divide(np.nansum(lag_raw*weights,axis=1),den,out=np.full(len(times),np.nan),where=den>0)
            own = current[:, j] if sid not in omitted else np.full(len(times), np.nan)
            own_lag = lag[:, j] if sid not in omitted else np.full(len(times), np.nan)
            std = np.sqrt(np.divide(np.nansum((raw-baseline[:,None])**2*valid,axis=1),valid.sum(axis=1),out=np.zeros(len(times)),where=valid.sum(axis=1)>0))
            target_times = times + pd.Timedelta(hours=horizon)
            data = {'station_id': sid, 'issue_time': times, 'timestamp': target_times,
                    'loss_percent': loss, 'target': future[:,j], 'spatial_pm25': baseline,
                    'spatial_lag24': lagged, 'own_pm25': own, 'own_lag24': own_lag,
                    'persistence': np.where(np.isfinite(own), own, baseline),
                    'persistence_kind': np.where(np.isfinite(own),'station','spatial_persistence'),
                    'available_count': valid.sum(axis=1),
                    'nearest_km': np.min(np.where(valid,distances,np.inf),axis=1),
                    'spatial_std': std, 'latitude': target.latitude, 'longitude': target.longitude,
                    'hour_sin': np.sin(2*np.pi*target_times.hour/24), 'hour_cos': np.cos(2*np.pi*target_times.hour/24),
                    'dow_sin': np.sin(2*np.pi*target_times.dayofweek/7), 'dow_cos': np.cos(2*np.pi*target_times.dayofweek/7)}
            data.update({k: weather[k].to_numpy(float) if k in weather else np.full(len(times),np.nan) for k in WEATHER_COLUMNS})
            rows.append(pd.DataFrame(data)[good])
    if not rows:
        raise ValueError('At least two monitoring locations and valid future targets are required')
    return pd.concat(rows,ignore_index=True)


def score(rows, predicted, low, high):
    error = predicted - rows.target.to_numpy(float)
    return {'samples': len(rows), 'mae': float(np.mean(abs(error))), 'rmse': float(np.sqrt(np.mean(error**2))),
            'idw_mae': float(np.mean(abs(rows.target-rows.spatial_pm25))),
            'persistence_mae': float(np.mean(abs(rows.target-rows.persistence))),
            'station_persistence_samples': int((rows.persistence_kind=='station').sum()),
            'spatial_persistence_samples': int((rows.persistence_kind=='spatial_persistence').sum()),
            'coverage_percent': float(np.mean((rows.target>=low)&(rows.target<=high))*100),
            'mean_interval_width': float(np.mean(high-low))}


def train_resilience(frame, fingerprint, withheld=None, stride=6):
    sources = sorted(frame.source_type.unique().tolist())
    ids = sorted(frame.station_id.astype(str).unique())
    if len(ids) < 3:
        raise ValueError('Need at least three actual monitoring locations for the spatial holdout')
    withheld = withheld or ('12237987' if '12237987' in ids else ids[-1])
    if withheld not in ids:
        raise ValueError('Withheld monitor is absent from dataset')
    times = frame.timestamp.drop_duplicates().sort_values()
    calibration_start = times.iloc[int(len(times)*.65)]
    test_start = times.iloc[int(len(times)*.8)]
    report = {'version': VERSION, 'dataset_fingerprint': fingerprint, 'target_source_types': sources,
              'withheld_station_id': withheld, 'training_station_ids': [i for i in ids if i!=withheld],
              'calibration_start': calibration_start.isoformat(), 'test_issue_start': test_start.isoformat(),
              'sensor_loss_levels': list(LOSSES), 'mask_seed': 731, 'stride_hours': stride,
              'features': FEATURES, 'results': [], 'splits': [],
              'limitations': ['Masks remove sensors for the whole declared experiment; they are simulated outages.',
                              'The held-out monitor is excluded from all fitting, calibration and neighbor predictors.',
                              'Weather is issue-time context, not future realized weather. Retrospective source availability is not an operational guarantee.',
                              'When station persistence is unavailable, spatial persistence uses the same issue-time neighbor estimate as IDW.',
                              'Bands use separate chronological calibration residuals. Temporal dependence and distribution shift prevent guaranteed coverage.',
                              'Results are development evidence on a previously inspected historical dataset; no causal intervention effects are established.']}
    models, predictions = {}, []
    for horizon in HORIZONS:
        rows = training_rows(frame,horizon,withheld,stride)
        fit = rows[(rows.station_id!=withheld)&(rows.timestamp<calibration_start)]
        cal = rows[(rows.station_id!=withheld)&(rows.issue_time>=calibration_start)&(rows.timestamp<test_start)]
        test = rows[rows.issue_time>=test_start]
        if len(fit)<100 or len(cal)<24 or len(test)<24:
            raise ValueError('Insufficient separated fit/calibration/test pairs')
        model = LGBMRegressor(n_estimators=180,num_leaves=15,max_depth=5,min_child_samples=40,
                              learning_rate=.04,reg_lambda=5,verbosity=-1,n_jobs=2,random_state=731)
        model.fit(fit[FEATURES],np.log(np.maximum(fit.target,1)/np.maximum(fit.spatial_pm25,1)))
        residuals = cal.target.to_numpy(float)-np.maximum(0,cal.spatial_pm25.to_numpy(float)*np.exp(model.predict(cal[FEATURES])))
        bands = {}
        for loss in LOSSES:
            r=residuals[cal.loss_percent.to_numpy()==loss]
            bands[loss] = (float(min(0,np.quantile(r,.1))),float(max(0,np.quantile(r,.9))))
        predicted=np.maximum(0,test.spatial_pm25.to_numpy(float)*np.exp(model.predict(test[FEATURES])))
        lows=np.maximum(0,predicted+np.array([bands[l][0] for l in test.loss_percent]))
        highs=predicted+np.array([bands[l][1] for l in test.loss_percent])
        for group,label in [(test.station_id==withheld,'withheld_location'),(test.station_id!=withheld,'known_locations')]:
            for loss in LOSSES:
                mask=(group&(test.loss_percent==loss)).to_numpy()
                if mask.any():
                    report['results'].append({'scope':label,'horizon':horizon,'loss_percent':loss,**score(test[mask],predicted[mask],lows[mask],highs[mask])})
        saved=test[['station_id','issue_time','timestamp','loss_percent','target','spatial_pm25','persistence','persistence_kind']].copy()
        saved['predicted'],saved['p10'],saved['p90'],saved['horizon']=predicted,lows,highs,horizon
        predictions.append(saved)
        models[horizon]={'model':model,'bands':bands}
        report['splits'].append({'horizon':horizon,'fit_rows':len(fit),'calibration_rows':len(cal),'test_rows':len(test),
                                'fit_target_end':fit.timestamp.max().isoformat(),'calibration_issue_start':cal.issue_time.min().isoformat(),
                                'calibration_target_end':cal.timestamp.max().isoformat(),'test_issue_start':test.issue_time.min().isoformat()})
    report['model_id']='airtwin-spatial-lightgbm-v1'
    artifact={'version':VERSION,'models':models,'report':report}
    ARTIFACT.parent.mkdir(parents=True,exist_ok=True)
    joblib.dump(artifact,ARTIFACT)
    REPORT.write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    for saved in predictions:
        horizon=int(saved.horizon.iloc[0])
        saved.to_csv(REPORT.with_name(f'sensor_resilience_predictions_{horizon}h.csv.gz'),
                     index=False,compression={'method':'gzip','mtime':0})
    return report


@lru_cache(maxsize=2)
def _load(path, modified):
    return joblib.load(path)


def load_resilience():
    if not ARTIFACT.exists():
        return None
    artifact=_load(str(ARTIFACT),ARTIFACT.stat().st_mtime_ns)
    if artifact.get('version')!=VERSION:
        return None
    return artifact


def estimate_snapshot(stations, cells, weather, issue, horizon=24, loss=0, withheld=None, seed=731, lag_lookup=None):
    artifact=load_resilience()
    observed=[s for s in stations if s['source_type']=='observed' and 0<=(pd.Timestamp(issue)-pd.Timestamp(s['timestamp'])).total_seconds()<=3*3600]
    omitted=excluded_ids([s['id'] for s in observed],loss,seed,withheld)
    available=[s for s in observed if s['id'] not in omitted]
    supported=artifact is not None and artifact['report']['target_source_types']==['observed']
    if artifact and pd.Timestamp(issue)<pd.Timestamp(artifact['report']['test_issue_start']):
        supported=False
    if observed and not available:
        raise ValueError('All measured PM2.5 inputs are masked; a modeled provider fallback or at least one available monitor is required')
    background = float(np.percentile([p['pm25'] for p in available], CONFIG['background_percentile'])) if available else None
    outputs=[]
    for cell in cells:
        if supported and len(available)>=2:
            neighbors=[{**p,'lag24':(lag_lookup or {}).get(p['id'],p['pm25'])} for p in available]
            features=spatial_features(cell,neighbors,issue,horizon,weather=weather)
            bundle=artifact['models'][min(HORIZONS,key=lambda h:abs(h-horizon))]
            value=max(0,features['spatial_pm25']*float(np.exp(bundle['model'].predict(pd.DataFrame([features],columns=FEATURES))[0])))
            level=min(LOSSES,key=lambda l:abs(l-loss))
            low,high=bundle['bands'][level]
            outputs.append({**cell,'background':min(background,value),'pm25':value,'p10':max(0,value+low),'p90':max(value,value+high),'source_type':'modeled'})
        else:
            value=idw(cell['latitude'],cell['longitude'],available) if available else cell['pm25']
            outputs.append({**cell,'pm25':value,'background':min(background,value) if background is not None else cell['background'],'source_type':'modeled','p10':None,'p90':None})
    return {'cells':outputs,'source_type':'modeled','available_sensors':len(available),'total_sensors':len(observed),
            'masked_sensor_ids':sorted(omitted),'withheld_location_id':withheld,
            'method':'Spatial LightGBM' if supported and len(available)>=2 else 'provider_or_historical_snapshot',
            'uncertainty_kind':'historically_calibrated' if supported and len(available)>=2 else 'unavailable',
            'fallback_reason':None if supported and len(available)>=2 else 'At least two recent observed PM2.5 monitors and an eligible observed-target spatial artifact are required.',
            'model_id':artifact['report']['model_id'] if artifact and supported and len(available)>=2 else None,
            'issued_at':pd.Timestamp.now(tz='UTC').isoformat(),'input_cutoff':pd.Timestamp(issue).isoformat(),
            'assumptions':['Sensor masking removes observed PM2.5 inputs; CAMS points are not counted as physical monitors.',
                           'Grid forecasts are modeled. Withheld-monitor evaluation is reported separately; every grid cell is not independently validated.',
                           'Spatial prediction bands use historical monitor calibration, not a guarantee at arbitrary grid locations.']}
