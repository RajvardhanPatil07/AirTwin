from fastapi import APIRouter
from app.schemas import ScenarioRequest, ScenarioResponse
from app.services.state_data import get_region_runtime
router = APIRouter()

@router.post('/scenarios', response_model=ScenarioResponse)
def scenarios(body: ScenarioRequest):
    runtime = get_region_runtime(body.region, body.replay_at)
    return runtime.scenario(body.location_id, body.cuts.model_dump(), body.replay_at)
