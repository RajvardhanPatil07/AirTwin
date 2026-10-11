# AirTwin

AirTwin is an environmental digital twin for Pune and Pimpri-Chinchwad. It brings together pollution readings, weather, forecasts and hypothetical intervention comparisons in a map-based web application.

The interface has three main pages: **Overview**, **Map** and **Forecast**. Analytics is a subview of Map, with Ask AirTwin and a Research workbench for source estimates, scenario comparisons, historical validation and budget planning.

## What you can do

- Search supported areas and inspect timestamped pollution and weather data.
- Compare available pollutant readings and shared provider reference groups.
- Explore 24-, 48- and 72-hour PM2.5 forecasts and available spatial forecast frames.
- Ask questions about the selected area using backend evidence.
- Compare hypothetical traffic, industry and dust controls.
- Inspect historical model performance and explore budget-constrained intervention packages.

## Run locally

Requirements: Python 3.11, Node.js 22 and npm. LightGBM may also require `libomp` on macOS.

From the repository root:

```sh
python3.11 -m venv .venv311
source .venv311/bin/activate
python -m pip install -r backend/requirements.txt
npm --prefix frontend ci
cp .env.example .env
python scripts/dev.py
```

Copy `.env.example` only when you do not already have a `.env` file. Add optional provider credentials before starting.

On Windows, create and activate the environment with:

```powershell
py -3.11 -m venv .venv311
.\.venv311\Scripts\Activate.ps1
```

Then use the installation commands above and run `python scripts/dev.py` from the activated environment.

- Application: [http://127.0.0.1:5188/](http://127.0.0.1:5188/)
- API documentation: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- API health: [http://127.0.0.1:8000/api/health](http://127.0.0.1:8000/api/health)

The launcher starts FastAPI and Vite. Set `AIRTWIN_FRONTEND_PORT` to change the frontend port. First startup can take longer if a model needs to be trained. Without a downloaded historical dataset, the backend uses the committed synthetic sample; that does not reproduce observed-data accuracy results.

## Configuration

Keep secrets in the ignored root `.env` file or backend environment.

| Variable | Purpose |
| --- | --- |
| `OPENAQ_API_KEY` | Access measured PM2.5 station readings and history |
| `GEMINI_API_KEY` | Enable Ask AirTwin's Gemini responses |
| `GEMINI_MODEL` | Select the Gemini model |
| `DATABASE_URL` | Enable PostgreSQL storage for live observations and provider snapshots |
| `LIVE_REFRESH_ENABLED` | Enable background provider refresh |
| `LIVE_REFRESH_SECONDS` | Provider refresh interval, default 900 seconds |
| `RETRAIN_ENABLED` | Enable scheduled live-model retraining checks |
| `CORS_ORIGINS` | Allowed frontend origins for separate hosting |
| `VITE_API_BASE_URL` | Public backend URL for a separately hosted frontend |

Locally, Vite forwards `/backend` requests to port 8000. Leave `VITE_API_BASE_URL` unset for this arrangement. An explicitly empty value selects the synthetic frontend demo. Never put provider keys or database credentials in `VITE_` variables.

## Data and model workflow

OpenAQ supplies observed PM2.5. CAMS via Open-Meteo supplies modeled pollution forecasts, and Open-Meteo supplies weather context. Mapped OpenStreetMap inputs and dated WorldPop estimates support spatial scenarios.

The backend validates observations, preserves missing hours and stores live measured history for a rolling 90 days. Historical data are stored separately. Eligible stations can use observed-target models; unsupported locations or insufficient inputs use explicitly labeled provider forecasts.

The historical LightGBM model uses chronological validation and persistence comparisons. Separate live retraining checks run daily by default, after an initial 15-minute delay. Candidate training requires enough new measured data and a minimum interval between successful promotions. A candidate must pass validation and beat persistence before replacing the live artifact. Historical replay remains separate.

Model binaries and fetched datasets are ignored by Git and must be prepared or provisioned on each backend environment. For the historical pipeline:

```sh
bash scripts/run_all.sh --offline
# With provider access configured, rebuild historical data and models:
bash scripts/run_all.sh --live
```

These commands rebuild local pipeline outputs. See the [data pipeline](docs/data_pipeline.md) before running them against an existing archive.

## How to read the results

- **Observed** means a physical monitor reading. **Modeled** means a provider forecast or calculated estimate. **Synthetic** means demonstration data.
- Check source timestamps. Refreshing the interface does not make stale observations current.
- The 12 × 12 pollution grid and smooth overlay are estimates, not additional monitoring stations or street-level measurements.
- PM2.5 concentration is not official AQI. Other pollutants are available only when supplied by the provider; CO₂ and O₂ are unavailable.
- Historical model performance does not validate today's CAMS forecasts or every map cell. Read the [model card](docs/model_card.md) and [data report](docs/data_report.md).
- Source contributions and intervention responses are assumptions. Scenario reductions are not demonstrated policy effects.
- Population-weighted benefit is not a count of people protected or avoided deaths.
- Verified municipal authentication and action execution are not connected. Planning outputs are hypothetical.

Ask AirTwin explains backend evidence. If Gemini is unavailable, the backend returns a labeled evidence summary. The language model does not calculate the numerical pollution forecast.

## Verification

```sh
python -m pytest backend/tests -q
npm --prefix frontend run lint
npm --prefix frontend test
npm --prefix frontend run build
npm --prefix frontend run test:sites
python scripts/check_repository.py
python scripts/check_documentation.py
```

Local journey checks and their limitations are recorded in [user journey verification](docs/user-journey-verification.md). Build and test results do not establish forecast accuracy or production readiness.

## Repository guide

| Directory | Contents |
| --- | --- |
| `backend/app` | FastAPI routes, ingestion, forecasting, scenarios and explanations |
| `backend/scripts` | Data preparation, training and evaluation commands |
| `frontend` | React application, maps, charts and hosting adapter |
| `config` | Scenario assumptions and intervention configuration |
| `data/sample` | Committed offline demonstration inputs |
| `docs` | Methodology, data provenance, validation and operating instructions |
| `scripts` | Local startup, pipeline and verification helpers |

Read the [frontend README](frontend/README.md), [architecture](docs/architecture.md), [API reference](docs/api.md), [data sources](docs/data_sources.md) and [troubleshooting guide](docs/troubleshooting.md) for details.

Contributions follow [CONTRIBUTING.md](CONTRIBUTING.md). Report security issues through [SECURITY.md](SECURITY.md). Map and dataset attribution is documented in the data sources. No project-wide software license has been selected.
