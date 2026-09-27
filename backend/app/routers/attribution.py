from fastapi import APIRouter
from app.schemas import AttributionResponse, Region
from app.services.state_data import get_state_runtime
from app.services.runtime import get_runtime
router = APIRouter()

@router.get('/attribution', response_model=AttributionResponse)
def attribution(location_id: str, replay_at: str | None = None, region: Region = 'pcmc'):
    runtime = get_runtime() if region == 'pcmc' else get_state_runtime()
    return runtime.attribution(location_id, replay_at)
