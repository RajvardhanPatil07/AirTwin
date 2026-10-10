import json
import pandas as pd
import pytest
from app.services.live_feed import parse_indices
from app.services.planning import optimize, CATALOG
from app.services.resilience import training_rows, FEATURES, excluded_ids


def grid():
    return [dict(id=f'c-{i}',latitude=18.6+i*.02,longitude=73.8,pm25=80+i*10,
                 background=20,population=1000,local_weights=dict(traffic=.4,industry=.4,dust=.2),
                 source_type='modeled',population_source_type='synthetic',assumptions=[],
                 bounds=((18.59,73.79),(18.61,73.81))) for i in range(3)]


def test_public_indices_keep_measurement_time_and_reject_zero_and_future():
    html=''.join(f'<p id="{key}_aqi_heading">{date} - {value}</p>' for key,date,value in [
        ('Bhosari','2026-10-10 12:00:00',134),('karve','2026-10-10 12:00:00',0),
        ('Nigadi','2026-10-11 12:00:00',144)])
    records=parse_indices(html,'2026-10-10T07:00:00Z')
    assert len(records)==1
    assert records[0]['timestamp']=='2026-10-10T12:00:00+05:30'
    assert records[0]['indicator']=='AQI' and records[0]['unit']=='index'


def test_budget_unavailability_and_physical_bounds():
    cells=grid()
    unavailable=[a['id'] for a in CATALOG['actions'] if a['category']=='industry']
    result=optimize(cells,budget=150000,unavailable=unavailable)
    assert result['selected']['cost']<=150000
    assert not set(a['id'] for a in result['selected']['actions'])&set(unavailable)
    assert result['rejected_package']['violations']
    assert all(after['pm25']>=before['background'] and after['pm25']<=before['pm25'] for before,after in zip(cells,result['cells_after']))
    assert all(sum(a['category']==cat for a in result['selected']['actions'])<=limit for cat,limit in CATALOG['limits'].items())
    zero=optimize(cells,budget=0)
    assert zero['selected']['actions']==[] and zero['selected']['cost']==0
    assert zero['target_feasible'] is False


def test_forecast_uncertainty_enters_package_objective_and_cost_sensitivity():
    cells=grid()
    base=optimize(cells)
    uncertain=optimize([{**c,'p10':c['background'],'p90':c['pm25']*2} for c in cells])
    assert not base['stability']['forecast_uncertainty_used']
    assert uncertain['stability']['forecast_uncertainty_used']
    assert base['selected']['worst_case_benefit']!=uncertain['selected']['worst_case_benefit']
    assert uncertain['cost_sensitivity']['expenditure']<=uncertain['budget']
    assert uncertain==optimize([{**c,'p10':c['background'],'p90':c['pm25']*2} for c in cells])


def sample_frame():
    rows=[]
    for sid in ['a','b','heldout']:
        for i,time in enumerate(pd.date_range('2026-01-01',periods=120,freq='h',tz='Asia/Kolkata')):
            rows.append(dict(timestamp=time,station_id=sid,latitude=18.6,longitude=73.8+['a','b','heldout'].index(sid)*.02,
                             pm25=30+i%10,source_type='observed'))
    return pd.DataFrame(rows)


def test_withheld_sensor_is_excluded_from_every_development_predictor():
    frame=sample_frame()
    before=training_rows(frame,6,'heldout',stride=6)
    frame.loc[frame.station_id=='heldout','pm25']=999
    after=training_rows(frame,6,'heldout',stride=6)
    pd.testing.assert_frame_equal(before[before.station_id!='heldout'][FEATURES],after[after.station_id!='heldout'][FEATURES])
    heldout=before[before.station_id=='heldout']
    assert heldout.own_pm25.isna().all() and heldout.own_lag24.isna().all()
    assert 'heldout' in excluded_ids(['a','b','heldout'],0,731,'heldout')


def test_future_values_cannot_change_issue_time_features():
    frame=sample_frame()
    issue=frame.timestamp.min()+pd.Timedelta(hours=48)
    before=training_rows(frame,6,'heldout',stride=6)
    frame.loc[frame.timestamp>issue,'pm25']=999
    after=training_rows(frame,6,'heldout',stride=6)
    pd.testing.assert_frame_equal(before[before.issue_time==issue][FEATURES],after[after.issue_time==issue][FEATURES])


def test_snapshot_rejects_observations_after_the_input_cutoff(monkeypatch):
    from app.services import resilience
    monkeypatch.setattr(resilience,'load_resilience',lambda:None)
    issue=pd.Timestamp('2026-01-01T12:00:00Z')
    stations=[dict(id='known',latitude=18.6,longitude=73.8,pm25=30,source_type='observed',timestamp=issue.isoformat()),
              dict(id='future',latitude=18.6,longitude=73.8,pm25=999,source_type='observed',timestamp=(issue+pd.Timedelta(hours=1)).isoformat())]
    result=resilience.estimate_snapshot(stations,grid(),{},issue)
    assert result['total_sensors']==1
    assert all(c['pm25']==30 for c in result['cells'])


def test_api_region_schema_rejects_other_regions():
    from app.routers.operations import PlanRequest
    from pydantic import ValidationError
    assert PlanRequest(region='pcmc').region=='pcmc'
    with pytest.raises(ValidationError):
        PlanRequest(region='maharashtra')


def test_feasible_target_changes_package_even_when_stress_ranking_differs(monkeypatch):
    import numpy as np
    from app.services import planning
    actions=[dict(id=category,name=category,category=category,cost=100,
                  latitude=18.6,longitude=73.8,radius_km=5,cut_percent=cut)
             for category,cut in [('traffic',10),('dust',20)]]
    monkeypatch.setattr(planning,'CATALOG',{'actions':actions,'limits':{}})
    class FixedStress:
        def uniform(self, low, high, size):
            return np.tile([1.4,1.,.6],(size[0],1))
    monkeypatch.setattr(planning.np.random,'default_rng',lambda seed:FixedStress())
    cells=[{**grid()[0],'pm25':100,'background':0,
            'local_weights':dict(traffic=.5,industry=0,dust=.5)}]
    unconstrained=planning.optimize(cells,budget=100,target_percent=0)
    target=planning.optimize(cells,budget=100,target_percent=unconstrained['selected']['reduction_percent']*1.5)
    assert unconstrained['selected']['actions'][0]['id']=='traffic'
    assert target['target_feasible']
    assert target['selected']['actions'][0]['id']=='dust'
    assert target['selected']['reduction_percent']>=target['target_percent']
    assert all(p['id']!=target['selected']['id'] for p in target['alternatives'])


@pytest.mark.parametrize('source,expected_kind,expected_method',[
    ('observed','snapshot','Snapshot interpolation'),
    ('modeled','forecast','CAMS provider forecast'),
    ('synthetic','snapshot','Snapshot interpolation'),
])
def test_plan_fallback_time_matches_its_actual_baseline(monkeypatch,source,expected_kind,expected_method):
    from app.routers import operations
    from app.services import resilience
    monkeypatch.setattr(resilience,'load_resilience',lambda:None)
    issue=pd.Timestamp('2026-10-10T12:30:00Z')
    station=dict(id='point',name='Test monitor',latitude=18.6,longitude=73.8,pm25=100,
                 source_type=source,timestamp=issue.isoformat())
    class Runtime:
        frame=pd.DataFrame(columns=['timestamp','station_id','pm25'])
        def snapshot(self,replay_at):
            return [station],grid(),None,{},issue
        def forecast(self,location_id,hours,replay_at):
            return {'series':[{'predicted':130}]}
    monkeypatch.setattr(operations,'get_region_runtime',lambda *args:Runtime())
    result=operations.plan(operations.PlanRequest())
    assert result['baseline_kind']==expected_kind
    assert result['forecast']['method']==expected_method
    expected=issue+pd.Timedelta(hours=24) if expected_kind=='forecast' else issue
    assert pd.Timestamp(result['forecast_valid_at'])==expected
    assert all(c['pm25']==(130 if source=='modeled' else 100 if source=='observed' else grid()[i]['pm25'])
               for i,c in enumerate(result['cells_before']))


def test_no_available_actions_never_spends_budget_or_claims_a_benefit():
    result=optimize(grid(),budget=700000,unavailable=[a['id'] for a in CATALOG['actions']])
    assert result['feasible_count']==1
    assert result['selected']['actions']==[]
    assert result['selected']['cost']==result['selected']['reduction_percent']==0
    assert not result['target_feasible']
