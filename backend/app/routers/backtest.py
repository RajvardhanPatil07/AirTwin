from fastapi import APIRouter
from app.schemas import BacktestResponse
from app.services.runtime import get_runtime
router = APIRouter()

@router.get('/backtest', response_model=BacktestResponse)
def backtest(location_id: str, replay_at: str | None = None):
    return get_runtime().backtest(location_id, replay_at)

@router.get('/replay')
def replay():
    return get_runtime().replay()
