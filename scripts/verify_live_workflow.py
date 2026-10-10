"""Exercise the running API and export final-round scenario evidence."""
import argparse
import gzip
import json
from pathlib import Path
import requests

ROOT=Path(__file__).resolve().parents[1]


def verify(base):
    session=requests.Session()
    def get(path):
        response=session.get(base+'/api/'+path,timeout=60)
        response.raise_for_status()
        return response.json()
    def plan(body):
        response=session.post(base+'/api/plans',json=body,timeout=60)
        response.raise_for_status()
        result=response.json()
        assert result['selected']['cost']<=body.get('budget',300000)
        assert result['rejected_package']['violations']
        assert all(after['pm25']<=before['pm25']+1e-8 for before,after in zip(result['cells_before'],result['cells_after']))
        return result
    feed=get('feed')
    stations=get('stations?region=pcmc')
    evidence=get('resilience/evidence')
    assert evidence['available'] and evidence['replay_at']
    replay=evidence['replay_at']
    withheld=evidence['report']['withheld_station_id']
    scenarios=[('complete_observations',dict(replay_at=replay)),
               ('sensor_loss',dict(replay_at=replay,sensor_loss_percent=50)),
               ('withheld_location',dict(replay_at=replay,withheld_location_id=withheld)),
               ('reduced_budget_and_unavailable_action',dict(replay_at=replay,budget=100000,unavailable_actions=['bhosari-industry']))]
    outputs=[]
    for name,body in scenarios:
        result=plan(body)
        if body.get('withheld_location_id'):
            assert withheld in result['forecast']['masked_sensor_ids']
        if body.get('sensor_loss_percent'):
            assert result['forecast']['available_sensors']<result['forecast']['total_sensors']
        if name=='reduced_budget_and_unavailable_action':
            assert all(a['id']!='bhosari-industry' for a in result['selected']['actions'])
        assert result['forecast']['method']=='Spatial LightGBM'
        outputs.append({'scenario':name,'request':body,'output':result})
        print(name,result['forecast']['available_sensors'],'sensors',result['selected']['cost'],'INR',flush=True)
    live=plan({})
    live_station=stations['stations'][0]['id']
    forecast=get('forecast?region=pcmc&location_id='+live_station+'&hours=24')
    assert any(p['predicted'] is not None for p in forecast['series'])
    report={'feed':feed,'live_coverage':stations.get('coverage'),'live_forecast_provider':forecast.get('forecast_provider'),
            'live_input_cutoff':forecast.get('input_cutoff'),'live_plan':live,'scenarios':outputs,
            'fresh_observed_aqi_verified':feed['fresh_count']>0,
            'fresh_observed_pm25_verified':stations.get('coverage',{}).get('observed_points',0)>0,
            'limitations':['AQI indices are separate from PM2.5 concentration targets.',
                           'Live station availability depends on source publication. Historical scenarios are labeled replayed.',
                           'Synthetic intervention effects do not establish causal pollution reduction.']}
    path=ROOT/'docs/evidence/live_workflow.json.gz'
    path.write_bytes(gzip.compress((json.dumps(report,separators=(',',':'),allow_nan=False)+'\n').encode(),mtime=0))
    print('Fresh observed AQI stations:',feed['fresh_count'])
    print('Fresh observed PM2.5 stations:',stations.get('coverage',{}).get('observed_points',0))
    print('Evidence:',path)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-url',default='http://127.0.0.1:8000')
    verify(parser.parse_args().base_url.rstrip('/'))
