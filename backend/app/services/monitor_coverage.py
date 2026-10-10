"""Describe measured inputs without turning sensor metadata into measurements."""
import pandas as pd


def monitor_coverage(stations, issue, *, replay=False, provider_payload=None, now=None):
    clock=pd.Timestamp.now(tz='UTC') if now is None else pd.Timestamp(now)
    cutoff=pd.Timestamp(issue)
    payload=provider_payload or {}
    mode=('historical_replay' if replay else 'live_provider' if provider_payload is not None else
          'synthetic_demo' if all(s['source_type']=='synthetic' for s in stations) else 'cached_historical')
    measured_stations={s['id']:s for s in stations if s['source_type']=='observed'}
    input_ids=set(measured_stations)
    warnings=list(payload.get('warnings',[]))
    if provider_payload is not None:
        from app.services.live_observations import read_observations
        try:
            for candidate in payload.get('history_sensor_candidates',[])[:12]:
                records=read_observations(candidate['id'],hours=2160)
                valid=[r for r in records if pd.Timestamp(r['timestamp'])<=clock]
                if valid and candidate['id'] not in measured_stations:
                    row=max(valid,key=lambda r:pd.Timestamp(r['timestamp']))
                    measured_stations[candidate['id']]={**candidate,**row,'id':candidate['id'],'source_type':'observed'}
        except Exception:
            warnings.append('Stored monitor history could not be read; provider context remains available.')
    monitors=[]
    for station in measured_stations.values():
        if station['source_type']!='observed':
            continue
        measured=pd.Timestamp(station['timestamp'])
        age=(clock-measured).total_seconds()/3600
        issue_age=(cutoff-measured).total_seconds()/3600
        eligible=station['id'] in input_ids and 0<=issue_age<=3 and (replay or mode=='cached_historical' or 0<=age<=3)
        monitors.append({'id':station['id'],'name':station['name'],
                         'pm25':station['pm25'],'timestamp':measured.isoformat(),
                         'age_hours':round(age,2),'age_at_issue_hours':round(issue_age,2),
                         'eligible':eligible,'status':'historical' if mode in ('historical_replay','cached_historical') else
                         'fresh' if eligible else 'future' if age<0 or issue_age<0 else 'cached_not_in_snapshot' if age<=3 and station['id'] not in input_ids else 'delayed' if age<=24 else 'stale'})
    return {'mode':mode,'checked_at':clock.isoformat(),'snapshot_at':cutoff.isoformat(),
            'fresh_monitor_count':sum(m['eligible'] for m in monitors),
            'observed_monitor_count':len(monitors),
            'discovered_monitor_count':len(payload.get('history_sensor_candidates',[])) if provider_payload is not None else len(monitors),
            'modeled_point_count':sum(s['source_type']=='modeled' for s in stations),
            'monitors':monitors,'warnings':warnings,
            'freshness_rule':'Observed PM2.5 must be at or before the input cutoff and no more than 3 hours old. Replay freshness is relative to its historical issue time.',
            'coverage_note':'Monitor counts describe inputs, not complete spatial coverage. CAMS samples and public AQI indices are not PM2.5 monitors.'}
