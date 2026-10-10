"""Select a station's 24-hour forecaster before its untouched test period."""
from functools import lru_cache
import numpy as np
import pandas as pd
from lightgbm import LGBMRegressor
from app.services.model import metrics

LAGS=(1,3,6,12,24,48)


def season(stamp):
    month=pd.Timestamp(stamp).month
    return 'winter' if month in (11,12,1,2) else 'summer' if month in (3,4,5) else 'monsoon' if month in (6,7,8,9) else 'post_monsoon'


def features(values,issue):
    times=[issue,*[issue-pd.Timedelta(hours=lag) for lag in LAGS]]
    if any(t not in values for t in times):
        return None
    return [values[t] for t in times]+[np.sin(2*np.pi*issue.hour/24),np.cos(2*np.pi*issue.hour/24),float(issue.dayofweek)]


def choose_candidate(actual,model,persistence):
    model_mae=float(np.mean(np.abs(np.asarray(actual)-model)))
    persistence_mae=float(np.mean(np.abs(np.asarray(actual)-persistence)))
    return ('LightGBM' if model_mae<persistence_mae else 'Persistence'),model_mae,persistence_mae


@lru_cache(maxsize=32)
def fit_station(records):
    values={pd.Timestamp(time):value for time,value in records}
    samples=[]
    for target in sorted(values):
        issue=target-pd.Timedelta(hours=24)
        x=features(values,issue)
        if x is not None:
            samples.append((issue,target,x,values[target],values[issue]))
    if len(samples)<240:
        raise ValueError('At least 240 complete observed 24-hour pairs are needed for separate fit, selection and test periods.')
    selection_start=samples[int(len(samples)*.6)][0]
    test_start=samples[int(len(samples)*.8)][0]
    fit=[s for s in samples if s[1]<selection_start]
    selection=[s for s in samples if s[0]>=selection_start and s[1]<test_start]
    test=[s for s in samples if s[0]>=test_start]
    if len(fit)<48 or len(selection)<24 or len(test)<24:
        raise ValueError('Insufficient purged fit/selection/test pairs; no baseline selection claimed.')
    model=LGBMRegressor(objective='regression_l1',n_estimators=120,learning_rate=.04,
                       num_leaves=7,max_depth=3,min_child_samples=12,reg_lambda=5,
                       verbosity=-1,n_jobs=1,random_state=42)
    model.fit([s[2] for s in fit],[s[3] for s in fit])
    candidate=np.maximum(0,model.predict([s[2] for s in selection]))
    baseline=np.array([s[4] for s in selection])
    chosen,model_mae,persistence_mae=choose_candidate([s[3] for s in selection],candidate,baseline)
    selected=candidate if chosen=='LightGBM' else baseline
    residual=np.array([s[3] for s in selection])-selected
    low=min(0.,float(np.quantile(residual,.1)))
    high=max(0.,float(np.quantile(residual,.9)))
    raw=np.maximum(0,model.predict([s[2] for s in test]))
    persistence=np.array([s[4] for s in test])
    prediction=raw if chosen=='LightGBM' else persistence
    actual=np.array([s[3] for s in test])
    lows=np.maximum(0,prediction+low);highs=prediction+high
    rows=[{'timestamp':s[1].isoformat(),'actual':s[3],'predicted':float(pred),
           'persistence':s[4],'p10':float(lo),'p90':float(hi)}
          for s,pred,lo,hi in zip(test,prediction,lows,highs)]
    comparisons=[]
    for label in sorted({season(s[1]) for s in test}):
        mask=np.array([season(s[1])==label for s in test])
        comparisons.append({'season':label,'samples':int(mask.sum()),
                            'lightgbm_mae':float(np.mean(abs(actual[mask]-raw[mask]))),
                            'persistence_mae':float(np.mean(abs(actual[mask]-persistence[mask]))),
                            'selected_mae':float(np.mean(abs(actual[mask]-prediction[mask])))})
    report={'selected_method':chosen,'selection_model_mae':model_mae,
            'selection_persistence_mae':persistence_mae,'fit_rows':len(fit),
            'selection_rows':len(selection),'test_rows':len(test),
            'fit_target_end':fit[-1][1].isoformat(),'selection_issue_start':selection[0][0].isoformat(),
            'selection_target_end':selection[-1][1].isoformat(),'test_issue_start':test[0][0].isoformat(),
            'test_target_end':test[-1][1].isoformat(),
            'test_model_mae':float(np.mean(abs(actual-raw))),
            'test_persistence_mae':float(np.mean(abs(actual-persistence))),
            'seasonal_comparisons':comparisons,
            'reason':f'{chosen} had the lower selection-period MAE. Ties select persistence. The later test period does not choose the method.'}
    return {'model':model,'report':report,'series':rows,'bands':(low,high),
            'metrics':metrics(actual,prediction,persistence,lows,highs)}


def station_bundle(observations):
    if any(row.get('source_type','observed')!='observed' for row in observations):
        raise ValueError('Station selection requires observed PM2.5 targets.')
    if len({row.get('station_id') for row in observations})>1:
        raise ValueError('Station selection cannot mix sensor histories.')
    records={}
    for row in observations:
        stamp=pd.Timestamp(row['timestamp'])
        value=float(row['pm25'])
        if stamp.tzinfo is None or not np.isfinite(value) or not 0<=value<=1000:
            raise ValueError('Invalid observed station hour.')
        records[stamp.tz_convert('UTC').floor('h').isoformat()]=value
    return fit_station(tuple(sorted(records.items())))


def station_forecast(station,observations,hours=24,now=None):
    if hours!=24:
        return None
    clock=pd.Timestamp.now(tz='UTC') if now is None else pd.Timestamp(now)
    eligible=[r for r in observations if pd.Timestamp(r['timestamp'])<=clock]
    if not eligible:
        return None
    bundle=station_bundle(eligible)
    values={pd.Timestamp(r['timestamp']).tz_convert('UTC').floor('h'):float(r['pm25']) for r in eligible}
    issue=max(values)
    if not 0<=(clock-issue).total_seconds()<=3*3600:
        return None
    x=features(values,issue)
    if x is None:
        return None
    chosen=bundle['report']['selected_method']
    endpoint=max(0,float(bundle['model'].predict([x])[0])) if chosen=='LightGBM' else values[issue]
    low,high=bundle['bands']
    history=[{'timestamp':t.isoformat(),'actual':v,'predicted':None,'persistence':None,'p10':None,'p90':None}
             for t,v in sorted(values.items()) if t>=issue-pd.Timedelta(hours=48)]
    future=[{'timestamp':(issue+pd.Timedelta(hours=h)).isoformat(),'actual':None,
             'predicted':values[issue]+(endpoint-values[issue])*h/24,'persistence':values[issue],
             'p10':max(0,endpoint+low) if h==24 else None,'p90':endpoint+high if h==24 else None}
            for h in range(1,25)]
    return {'location_id':station['id'],'source_type':'modeled','history_source_type':'observed',
            'history_reference':station['id'],'series':history+future,'shap':None,'weather_forecast':[],
            'forecast_provider':f'AirTwin selected {chosen}','model_id':f'observed-station-{chosen.lower()}',
            'model_version':'station-selector-v1','issued_at':clock.isoformat(),'input_cutoff':issue.isoformat(),
            'fallback_reason':'Persistence selected on earlier validation data.' if chosen=='Persistence' else None,
            'selection':bundle['report'],
            'assumptions':[bundle['report']['reason'],
                           'Exact observed lags are required; fit targets end before selection origins and selection targets before test origins.',
                           'Only the 24-hour endpoint is tested. Shorter displayed points interpolate from the issue observation.',
                           '24-hour bands use selection-period residuals; coverage is measured on the separate test period and is not guaranteed live.',
                           'A station forecast does not establish street-level accuracy or causal intervention benefits.']}
