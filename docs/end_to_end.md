# Connected setup and verification

Use Python 3.11 and Node.js 22 or newer supported by Vite. On macOS, LightGBM
requires the OpenMP library (`libomp`). Follow the README installation steps.

## Credentials and provider behaviour

| Variable | Location | Behaviour |
| --- | --- | --- |
| `OPENAQ_API_KEY` | root `.env` | Live observed ingestion. Missing/unusable data falls back to modeled CAMS or labeled synthetic targets. |
| `GEMINI_API_KEY` | root `.env` | Generated explanation. Missing key, provider outage or rejected claims returns a labeled deterministic evidence summary. |
| `GEMINI_MODEL` | root `.env` | Provider model identifier; the example value must be available to your account. |
| `LIVE_REFRESH_ENABLED` | root `.env` | `1` enables hourly Maharashtra provider-cache refresh; `0` disables it for offline verification. Does not retrain PCMC. |
| `LIVE_REFRESH_SECONDS` | root `.env` | Cache refresh interval, default 3600 seconds. |
| `CORS_ORIGINS` | root `.env` | Comma-separated deployed frontend origins; loopback origins are allowed automatically. |
| `VITE_API_BASE_URL` | `frontend/.env` | Defaults to `/backend` through the Vite proxy. Use a public API URL for separate hosting; an empty value explicitly enables frontend-only synthetic mode. |
| `AIRTWIN_BACKEND_URL` | frontend server environment | Vite proxy target; defaults to `http://127.0.0.1:8000`. Useful for isolated verification on another API port. |

Only the public backend URL belongs in frontend variables. Never copy provider
keys there. Offline model results do not establish observed-city forecast skill.

## Clean offline check

Run in a separate clone so the sample pipeline does not replace your local
processed data or generated model card:

```sh
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -r backend/requirements.txt
AIRTWIN_PYTHON=.venv/bin/python bash scripts/pipeline.sh --offline
python backend/scripts/train_model.py --offline
LIVE_REFRESH_ENABLED=0 python -m uvicorn app.main:app --app-dir backend --port 8000
```

In another terminal, install frontend dependencies with `npm ci` in `frontend`,
then run `npm run dev`. Leave `frontend/.env` absent to use the proxy.

From the repository root, check the running API:

```sh
python scripts/verify_runtime.py
# Also require an actual generated, evidence-checked answer when credentials exist:
python scripts/verify_runtime.py --require-gemini
```

The checker discovers a real location ID and verifies forecast, held-out metrics,
source shares, three interventions, population-weighted sensitivity bounds,
combined additivity, matching after-grid, zero cuts and explanation evidence.
It exits unsuccessfully if any check fails. `--url` can select an isolated port
or the frontend proxy (`http://127.0.0.1:5188/backend`).

## Browser acceptance

- At desktop and 390px mobile width, select a location and inspect its snapshot.
  Data older than 24 hours is labeled stale; forecasts start at that snapshot.
- Compare all three actions and the combined package. Confirm the leading
  individual action, exposure range and overlap warning. Keep synthetic population visible.
- Change cuts, confirm previous results are marked outdated, then run again.
  Set every cut to zero and confirm no modeled reduction.
- Open Forecast, Backtest and Sources. Their explanation/provenance must remain separate.
- Ask a question. Confirm generated answers or explicitly labeled fallback.
  A failed request offers Retry explanation; frontend-only mode disables generation.
- If initial connection fails, confirm the synthetic banner and Retry backend.
  If later analysis fails, use Retry analysis; no real/mock mixture is introduced.
- Check keyboard navigation, theme switching, drawer scrolling and horizontal overflow.

Run `make check PYTHON=.venv/bin/python` and `python scripts/check_repository.py`
before reviewing the diff. Passing checks do not guarantee provider availability
or forecast accuracy. Current verification evidence is in `docs/verification.md`.
