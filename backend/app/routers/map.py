from typing import Literal
from fastapi import APIRouter, HTTPException
from app.schemas import StationsResponse, HotspotsResponse, Region
from app.services.state_data import get_state_runtime, STATE_ASSUMPTIONS
from app.services.regions import region_metadata
from app.services.runtime import get_runtime
from app.services.spatial import ASSUMPTIONS
router = APIRouter()

@router.get('/stations', response_model=StationsResponse)
def stations(replay_at: str | None = None, region: Region = 'pcmc'):
    runtime = get_runtime() if region == 'pcmc' else get_state_runtime()
    return {**runtime.stations(replay_at), 'region': region_metadata(region)}

@router.get('/hotspots', response_model=HotspotsResponse)
def hotspots(mode: Literal['before', 'after'] = 'before', scenario_id: str | None = None, replay_at: str | None = None, region: Region = 'pcmc'):
    runtime = get_runtime() if region == 'pcmc' else get_state_runtime()
    if mode == 'after':
        result = runtime.scenarios.get(scenario_id)
        if result is None:
            raise HTTPException(404, 'Scenario not found; run a scenario first')
        cells = next(r['cells'] for r in result['results'] if r['id'] == 'combined')
    else:
        _, cells, _, _, _ = runtime.snapshot(replay_at)
    return {'cells': cells, 'source_type': 'modeled', 'assumptions': STATE_ASSUMPTIONS if region == 'maharashtra' else ASSUMPTIONS}


@router.get('/timeline')
def timeline(replay_at: str | None = None, region: Region = 'pcmc'):
    if region == 'maharashtra':
        return get_state_runtime().timeline(None, (0, 3, 6, 9, 12, 18, 24))
    return get_runtime().timeline(replay_at)
