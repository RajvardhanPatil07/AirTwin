from fastapi import APIRouter
from app.schemas import ExplainRequest, ExplainResponse
from app.services.runtime import get_runtime
from app.services.explainer import explain
router = APIRouter()

@router.post('/explain', response_model=ExplainResponse)
def explain_route(body: ExplainRequest):
    return explain(get_runtime(), body.location_id, body.question, body.replay_at)
