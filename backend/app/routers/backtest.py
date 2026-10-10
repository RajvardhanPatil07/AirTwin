from fastapi import APIRouter
from app.schemas import BacktestResponse, Region
from app.services.state_data import get_region_runtime
from app.services.runtime import get_runtime
router = APIRouter()

@router.get('/backtest', response_model=BacktestResponse)
def backtest(location_id: str, replay_at: str | None = None, region: Region = 'pcmc'):
    runtime = get_region_runtime(region, replay_at)
    return runtime.backtest(location_id, replay_at)

@router.get('/replay')
def replay():
    return get_runtime().replay()
