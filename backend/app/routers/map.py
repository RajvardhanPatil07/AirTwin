from typing import Literal
from fastapi import APIRouter, HTTPException
from app.schemas import StationsResponse, HotspotsResponse
from app.services.runtime import get_runtime
from app.services.spatial import ASSUMPTIONS
router = APIRouter()

@router.get('/stations', response_model=StationsResponse)
def stations(replay_at: str | None = None):
    return get_runtime().stations(replay_at)

@router.get('/hotspots', response_model=HotspotsResponse)
def hotspots(mode: Literal['before', 'after'] = 'before', scenario_id: str | None = None, replay_at: str | None = None):
    runtime = get_runtime()
    if mode == 'after':
        result = runtime.scenarios.get(scenario_id)
        if result is None:
            raise HTTPException(404, 'Scenario not found; run a scenario first')
        cells = next(r['cells'] for r in result['results'] if r['id'] == 'combined')
    else:
        _, cells, _, _, _ = runtime.snapshot(replay_at)
    return {'cells': cells, 'source_type': 'modeled', 'assumptions': ASSUMPTIONS}
