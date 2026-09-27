from fastapi import APIRouter, Query
from app.schemas import ForecastResponse, Region
from app.services.state_data import get_state_runtime
from app.services.runtime import get_runtime
router = APIRouter()

@router.get('/forecast', response_model=ForecastResponse)
def forecast(location_id: str, hours: int = Query(24, ge=1, le=72), replay_at: str | None = None, region: Region = 'pcmc'):
    runtime = get_runtime() if region == 'pcmc' else get_state_runtime()
    return runtime.forecast(location_id, hours, replay_at)
