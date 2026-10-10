from typing import Literal
from fastapi import APIRouter, HTTPException
from app.schemas import StationsResponse, HotspotsResponse, Region
from app.services.state_data import get_region_runtime
from app.services.live_observations import historical_observed_stations
from app.services.regions import region_metadata
from app.services.spatial import ASSUMPTIONS
router = APIRouter()

@router.get('/stations', response_model=StationsResponse)
def stations(replay_at: str | None = None, region: Region = 'pcmc'):
    runtime = get_region_runtime(region, replay_at)
    response = runtime.stations(replay_at)
    return {**response, 'region': response.get('region', region_metadata(region))}

@router.get('/observed-history')
def observed_history(region: Region = 'pcmc'):
    if region != 'pcmc':
        raise HTTPException(422, 'Historical OpenAQ monitor layer is limited to Pune + PCMC.')
    stations = historical_observed_stations()
    return {
        'source_type': 'observed',
        'assumptions': [
            'These are real OpenAQ PM2.5 station measurements, but each is older than 24 hours.',
            'Historical station markers do not represent current pollution, live forecasts or grid cells.',
        ],
        'stations': stations,
        'latest_measurement_at': stations[0]['timestamp'] if stations else None,
    }


@router.get('/hotspots', response_model=HotspotsResponse)
def hotspots(mode: Literal['before', 'after'] = 'before', scenario_id: str | None = None, replay_at: str | None = None, region: Region = 'pcmc'):
    runtime = get_region_runtime(region, replay_at)
    if mode == 'after':
        result = runtime.scenarios.get(scenario_id)
        if result is None:
            raise HTTPException(404, 'Scenario not found; run a scenario first')
        cells = next(r['cells'] for r in result['results'] if r['id'] == 'combined')
    else:
        _, cells, _, _, _ = runtime.snapshot(replay_at)
    return {'cells': cells, 'source_type': 'modeled', 'assumptions': cells[0]['assumptions'] if cells else ASSUMPTIONS}


@router.get('/timeline')
def timeline(replay_at: str | None = None, region: Region = 'pcmc'):
    runtime = get_region_runtime(region, replay_at)
    if region == 'maharashtra' or getattr(runtime, 'region_name', None) == 'Pune + PCMC':
        return runtime.timeline(None, (0, 3, 6, 9, 12, 18, 24))
    return runtime.timeline(replay_at)
