from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import forecast, backtest, map, attribution, scenarios, explain
from app.services.runtime import get_runtime

@asynccontextmanager
async def lifespan(app):
    get_runtime()
    yield

app = FastAPI(title='AirTwin PCMC', version='0.1.0', lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=['http://localhost:5173', 'http://127.0.0.1:5173'],
                   allow_methods=['GET', 'POST'], allow_headers=['Content-Type'])
for routes in [forecast, backtest, map, attribution, scenarios, explain]:
    app.include_router(routes.router, prefix='/api')

@app.get('/api/health')
def health():
    runtime = get_runtime()
    return {'status': 'ok', 'source_type': 'modeled', 'assumptions': runtime.warnings,
            'model': 'LightGBM direct horizons with quantile models', 'dataset_rows': len(runtime.frame),
            'target_source_types': sorted(runtime.frame.source_type.unique()),
            'last_dataset_time': runtime.frame.timestamp.max().isoformat(),
            'warnings': runtime.warnings, 'fingerprint': runtime.fingerprint}
