from fastapi import APIRouter
from app.schemas import ScenarioRequest, ScenarioResponse
from app.services.runtime import get_runtime
router = APIRouter()

@router.post('/scenarios', response_model=ScenarioResponse)
def scenarios(body: ScenarioRequest):
    return get_runtime().scenario(body.location_id, body.cuts.model_dump(), body.replay_at)
