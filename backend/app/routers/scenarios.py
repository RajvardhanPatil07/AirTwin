from fastapi import APIRouter
from app.schemas import ScenarioRequest, ScenarioResponse
from app.services.runtime import get_runtime
from app.services.state_data import get_state_runtime
router = APIRouter()

@router.post('/scenarios', response_model=ScenarioResponse)
def scenarios(body: ScenarioRequest):
    runtime = get_runtime() if body.region == 'pcmc' else get_state_runtime()
    return runtime.scenario(body.location_id, body.cuts.model_dump(), body.replay_at)
