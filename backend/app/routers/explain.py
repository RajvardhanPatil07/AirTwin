from fastapi import APIRouter
from app.schemas import ExplainRequest, ExplainResponse
from app.services.runtime import get_runtime
from app.services.explainer import explain
from app.services.state_data import get_state_runtime
router = APIRouter()

@router.post('/explain', response_model=ExplainResponse)
def explain_route(body: ExplainRequest):
    runtime = get_runtime() if body.region == 'pcmc' else get_state_runtime()
    return explain(runtime, body.location_id, body.question, body.replay_at, body.cuts.model_dump(), body.hours, [message.model_dump() for message in body.history])
