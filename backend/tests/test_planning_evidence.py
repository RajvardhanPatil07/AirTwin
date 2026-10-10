import numpy as np
import pandas as pd
import pytest
from app.services.planning import optimize, CATALOG
from app.services.monitor_coverage import monitor_coverage
from app.services.station_selection import station_bundle, station_forecast, choose_candidate


def cells(background=20):
    return [dict(id='cell',latitude=18.62,longitude=73.85,pm25=100,background=background,
                 population=1000,local_weights=dict(traffic=.4,industry=.4,dust=.2))]


def observations():
    start=pd.Timestamp('2026-05-01T00:00:00Z')
    return [dict(station_id='openaq-123',timestamp=(start+pd.Timedelta(hours=i)).isoformat(),
                 pm25=50.,source_type='observed') for i in range(600)]


def test_package_preferences_and_explanation_reconcile():
    for preference in ('robust','max_benefit','min_cost'):
        p=optimize(cells(),budget=300000,target_percent=5,preference=preference)
        chosen=next(r['package'] for r in p['recommendations'] if r['kind']==preference)
        assert p['selected']==chosen
        assert p['selected']['cost']<=p['budget']
        assert p['selected']['reduction_percent']==pytest.approx(sum(r['reduction_percent'] for r in p['explanation']['category_reductions']))
        if preference=='min_cost':
            assert chosen['cost']==p['explanation']['minimum_budget_for_target']
    max_plan=optimize(cells(),preference='max_benefit')
    assert max_plan['selected']['reduction_percent']==max_plan['maximum_feasible_reduction_percent']


def test_background_and_unavailability_explain_infeasible_target():
    p=optimize(cells(background=99),target_percent=12)
    assert p['explanation']['background_share_percent']==99
    assert p['explanation']['local_excess_share_percent']==1
    assert p['explanation']['limiting_reason']=='action_scope_and_background'
    assert p['explanation']['minimum_budget_for_target'] is None
    assert p['recommendations'][2]['package'] is None
    all_blocked=optimize(cells(),unavailable=[a['id'] for a in CATALOG['actions']])
    assert all_blocked['explanation']['available_actions_maximum_percent']==0


def test_budget_infeasibility_has_an_actual_required_budget():
    p=optimize(cells(),budget=0,target_percent=1)
    assert p['explanation']['limiting_reason']=='budget'
    required=p['explanation']['minimum_budget_for_target']
    assert required>0
    q=optimize(cells(),budget=required,target_percent=1,preference='min_cost')
    assert q['target_feasible'] and q['selected']['cost']==required


def test_action_evidence_ranges_include_no_effect_and_have_matching_citations():
    known={s['id'] for s in CATALOG['evidence_sources']}
    for a in CATALOG['actions']:
        assert set(a['source_ids'])<=known
        assert a['response_range_percent']['low']==0
        assert a['response_range_percent']['central']==a['cut_percent']
        assert a['cost_evidence']['documented_unit_cost_inr'] is None
    p=optimize(cells())
    assert p['selected']['response_envelope_low_percent']==0
    assert p['selected']['response_envelope_high_percent']>=p['selected']['reduction_percent']


def test_monitor_coverage_keeps_future_stale_and_replay_distinct():
    now=pd.Timestamp('2026-10-10T12:00:00Z')
    stations=[dict(id=str(i),name=str(i),source_type='observed',pm25=50,
                   timestamp=(now-pd.Timedelta(hours=age)).isoformat()) for i,age in enumerate((1,25,-1))]
    c=monitor_coverage(stations,now,provider_payload={},now=now)
    assert c['fresh_monitor_count']==1
    assert [m['status'] for m in c['monitors']]==['fresh','stale','future']
    replay=monitor_coverage(stations,now,replay=True,now=now+pd.Timedelta(days=10))
    assert replay['mode']=='historical_replay' and replay['fresh_monitor_count']==1


def test_persistence_wins_ties_and_when_model_loses():
    assert choose_candidate([50,60],np.array([90,90]),np.array([50,60]))[0]=='Persistence'
    assert choose_candidate([50,60],np.array([50,60]),np.array([50,60]))[0]=='Persistence'


def test_later_test_targets_cannot_change_selection_and_splits_are_purged():
    records=observations()
    a=station_bundle(records)['report']
    changed=[{**r,'pm25':999} if pd.Timestamp(r['timestamp'])>=pd.Timestamp(a['test_issue_start'])+pd.Timedelta(hours=24) else r for r in records]
    b=station_bundle(changed)['report']
    assert a['selected_method']==b['selected_method']=='Persistence'
    assert a['selection_model_mae']==b['selection_model_mae']
    assert a['selection_persistence_mae']==b['selection_persistence_mae']
    assert pd.Timestamp(a['fit_target_end'])<pd.Timestamp(a['selection_issue_start'])
    assert pd.Timestamp(a['selection_target_end'])<pd.Timestamp(a['test_issue_start'])
    assert a['test_persistence_mae']!=b['test_persistence_mae']


def test_selected_station_forecast_uses_actual_issue_time_and_rejects_stale_history():
    records=observations();issue=pd.Timestamp(records[-1]['timestamp'])
    p=station_forecast({'id':'openaq-123'},records,now=issue)
    assert p['model_id']=='observed-station-persistence'
    assert p['input_cutoff']==issue.isoformat()
    assert p['series'][-1]['predicted']==50
    assert pd.Timestamp(p['series'][-1]['timestamp'])==issue+pd.Timedelta(hours=24)
    assert station_forecast({'id':'openaq-123'},records,now=issue+pd.Timedelta(hours=4)) is None
    with pytest.raises(ValueError,match='observed'):
        station_bundle([{**r,'source_type':'modeled'} for r in records])
