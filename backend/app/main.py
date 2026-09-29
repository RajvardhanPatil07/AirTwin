from contextlib import asynccontextmanager
import os
import threading
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import forecast, backtest, map, attribution, scenarios, explain
from app.services.runtime import get_runtime
from app.services.state_data import get_pune_runtime
from app.services import database

@asynccontextmanager
async def lifespan(app):
    get_runtime()
    if os.getenv('DATABASE_URL'):
        try:
            database.initialize()
        except Exception:
            import logging
            logging.getLogger('airtwin.live').warning('PostgreSQL is configured but unavailable during startup.', exc_info=True)
    stop = threading.Event()
    if os.getenv('LIVE_REFRESH_ENABLED', '1') == '1' and not os.getenv('PYTEST_CURRENT_TEST'):
        from app.services.state_data import live_loop
        threading.Thread(target=live_loop, args=(stop,), daemon=True, name='airtwin-provider-refresh').start()
    yield
    stop.set()

app = FastAPI(title='AirTwin Maharashtra + PCMC', version='0.1.0', lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=[origin.strip() for origin in os.getenv('CORS_ORIGINS', '').split(',') if origin.strip()],
                   allow_origin_regex=r'https?://(localhost|127\.0\.0\.1)(:[0-9]+)?',
                   allow_methods=['GET', 'POST'], allow_headers=['Content-Type'])
for routes in [forecast, backtest, map, attribution, scenarios, explain]:
    app.include_router(routes.router, prefix='/api')

@app.get('/api/health')
def health():
    runtime = get_runtime()
    pune = get_pune_runtime()
    return {'regions': ['pcmc', 'maharashtra'], 'chat_provider': 'gemini', 'chat_configured': bool(os.getenv('GEMINI_API_KEY')), 'status': 'ok', 'source_type': 'modeled', 'database': database.status(), 'assumptions': runtime.warnings,
            'pune_live': {'ready': pune is not None,
                          'updated_at': pune.payload['updated_at'] if pune else None,
                          'modeled_points': len(pune.points) if pune else 0,
                          'observed_points': len(pune.payload.get('observed', [])) if pune else 0},
            'model': runtime.artifact['report'].get('model', 'LightGBM direct horizons'), 'dataset_rows': len(runtime.frame),
            'target_source_types': sorted(runtime.frame.source_type.unique()),
            'last_dataset_time': runtime.frame.timestamp.max().isoformat(),
            'warnings': runtime.warnings, 'fingerprint': runtime.fingerprint}
