from fastapi import APIRouter, Query
from app.schemas import ForecastResponse
from app.services.runtime import get_runtime
router = APIRouter()

@router.get('/forecast', response_model=ForecastResponse)
def forecast(location_id: str, hours: int = Query(24, ge=1, le=72), replay_at: str | None = None):
    return get_runtime().forecast(location_id, hours, replay_at)
