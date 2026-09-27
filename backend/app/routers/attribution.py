from fastapi import APIRouter
from app.schemas import AttributionResponse
from app.services.runtime import get_runtime
router = APIRouter()

@router.get('/attribution', response_model=AttributionResponse)
def attribution(location_id: str, replay_at: str | None = None):
    return get_runtime().attribution(location_id, replay_at)
