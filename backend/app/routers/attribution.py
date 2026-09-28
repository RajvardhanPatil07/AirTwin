from fastapi import APIRouter
from app.schemas import AttributionResponse, Region
from app.services.state_data import get_region_runtime
router = APIRouter()

@router.get('/attribution', response_model=AttributionResponse)
def attribution(location_id: str, replay_at: str | None = None, region: Region = 'pcmc'):
    runtime = get_region_runtime(region, replay_at)
    return runtime.attribution(location_id, replay_at)
