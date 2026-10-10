import json
import numpy as np
import pandas as pd
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Literal
from app.schemas import Region, Provenance
from app.services.state_data import get_region_runtime
from app.services.runtime import get_runtime
from app.services.live_feed import feed_status
from app.services.resilience import REPORT, estimate_snapshot
from app.services.planning import CATALOG, optimize
from app.services.spatial import idw, CONFIG
from app.services.monitor_coverage import monitor_coverage

router=APIRouter()


class PlanRequest(BaseModel):
    budget: float = Field(default=300000,ge=0,le=10000000)
    unavailable_actions: list[str] = Field(default_factory=list,max_length=8)
    cost_multiplier: float = Field(default=1,ge=.5,le=2)
    response_multiplier: float = Field(default=1,ge=.2,le=2)
    target_percent: float = Field(default=12,ge=0,le=100)
    sensor_loss_percent: int = Field(default=0,ge=0,le=100)
    withheld_location_id: str | None = None
    replay_at: str | None = None
    region: Region = 'pcmc'
    preference: Literal['robust','max_benefit','min_cost'] = 'robust'


@router.get('/feed')
def feed():
    return feed_status()


@router.get('/resilience/evidence')
def evidence():
    if not REPORT.exists():
        return {'source_type':'modeled','available':False,'assumptions':['Run backend/scripts/train_resilience.py to generate spatial forecast evidence.']}
    report=json.loads(REPORT.read_text())
    runtime=get_runtime()
    start=pd.Timestamp(report['test_issue_start'])+pd.Timedelta(days=7)
    rows=runtime.frame[runtime.frame.timestamp>=start]
    counts=rows.groupby('timestamp').station_id.nunique()
    heldout_times=rows[rows.station_id.astype(str)==report['withheld_station_id']].timestamp
    candidates=counts[(counts>=min(5,rows.station_id.nunique())) & counts.index.isin(heldout_times)]
    replay=candidates.index[0].isoformat() if not candidates.empty else None
    heldout=runtime.frame[runtime.frame.station_id.astype(str)==report['withheld_station_id']]
    return {'source_type':'modeled','available':True,'report':report,'replay_at':replay,
            'withheld_name':str(heldout.station_name.iloc[0]) if not heldout.empty else report['withheld_station_id'],
            'assumptions':report['limitations']}


@router.post('/plans')
def plan(body: PlanRequest):
    known={a['id'] for a in CATALOG['actions']}
    if set(body.unavailable_actions)-known:
        raise HTTPException(422,'Unknown intervention action')
    if body.region!='pcmc':
        raise HTTPException(422,'Intervention planning is bounded to Pune–PCMC')
    runtime=get_region_runtime(body.region,body.replay_at)
    stations,cells,_,weather,issue=runtime.snapshot(body.replay_at)
    if body.withheld_location_id and body.withheld_location_id not in {s['id'] for s in stations if s['source_type']=='observed'}:
        raise HTTPException(422,'Withheld location must be a monitor in this snapshot')
    # Provider-only fallback uses the 24-hour forecast grid rather than the current snapshot.
    modeled=[s for s in stations if s['source_type']=='modeled']
    baseline=cells
    provider_forecast=False
    if modeled and not any(s['source_type']=='observed' and 0<=(issue-pd.Timestamp(s['timestamp'])).total_seconds()<=3*3600 for s in stations):
        future=[]
        for station in modeled:
            if hasattr(runtime,'all_frame'):
                endpoint=runtime.all_frame[(runtime.all_frame.station_id==station['id']) & (runtime.all_frame.timestamp==issue+pd.Timedelta(hours=24))]
                if endpoint.empty or pd.isna(endpoint.pm25.iloc[0]):
                    raise HTTPException(503,'Provider cache lacks the exact 24-hour planning endpoint.')
                value=float(endpoint.pm25.iloc[0])
            else:
                forecast=runtime.forecast(station['id'],24,body.replay_at)
                value=forecast['series'][-1]['predicted']
            future.append({**station,'pm25':value})
        background=float(np.percentile([s['pm25'] for s in future],CONFIG['background_percentile']))
        baseline=[{**c,'pm25':idw(c['latitude'],c['longitude'],future),
                   'background':min(background,idw(c['latitude'],c['longitude'],future))} for c in cells]
        provider_forecast=True
    history=runtime.frame[runtime.frame.timestamp==issue-pd.Timedelta(hours=24)]
    lag={str(r.station_id):float(r.pm25) for r in history.itertuples() if pd.notna(r.pm25)}
    target=next((s for s in stations if s['id']==body.withheld_location_id),None)
    prediction_cells=baseline
    if target:
        prediction_cells=[*baseline,{**baseline[0],'id':'withheld-preview',
                                     'latitude':target['latitude'],'longitude':target['longitude']}]
    try:
        spatial=estimate_snapshot(stations,prediction_cells,weather,issue,24,body.sensor_loss_percent,
                                  body.withheld_location_id,lag_lookup=lag)
    except ValueError as error:
        raise HTTPException(503,str(error)) from error
    is_forecast=spatial['method'] in ('Spatial LightGBM','Spatial persistence')
    if not is_forecast:
        is_forecast=provider_forecast and spatial['available_sensors']==0
        spatial['method']='CAMS provider forecast' if is_forecast else 'Snapshot interpolation'
        spatial['assumptions'].append(
            'Planning uses the provider 24-hour forecast without calibrated forecast uncertainty.' if is_forecast else
            'Planning uses a snapshot interpolated from available inputs, not a 24-hour forecast. Future intervention benefits are not established.')
    heldout_result=None
    if target:
        point=spatial['cells'].pop()
        if spatial['method'] in ('Spatial LightGBM','Spatial persistence'):
            actual=runtime.frame[(runtime.frame.station_id.astype(str)==target['id']) &
                                 (runtime.frame.timestamp==issue+pd.Timedelta(hours=24))]
            heldout_result={'location_id':target['id'],'name':target['name'],'predicted':point['pm25'],
                            'p10':point['p10'],'p90':point['p90'],
                            'actual':float(actual.pm25.iloc[0]) if not actual.empty else None,
                            'forecast_source_type':'modeled','target_source_type':'observed',
                            'valid_at':(issue+pd.Timedelta(hours=24)).isoformat()}
    result=optimize(spatial['cells'],body.budget,body.unavailable_actions,body.cost_multiplier,
                    body.response_multiplier,body.target_percent,preference=body.preference)
    spatial.pop('cells')
    result['forecast']=spatial
    result['baseline_kind']='forecast' if is_forecast else 'snapshot'
    result['forecast_valid_at']=(issue+pd.Timedelta(hours=24) if is_forecast else issue).isoformat()
    result['snapshot_at']=issue.isoformat()
    result['input_source_types']=sorted({s['source_type'] for s in stations})
    result['replay_at']=body.replay_at
    result['heldout_result']=heldout_result
    result['coverage']=monitor_coverage(stations,issue,replay=bool(body.replay_at),provider_payload=getattr(runtime,'payload',None))
    result['assumptions']+=spatial['assumptions']
    return result
