# Troubleshooting

## Frontend

**npm ci fails:** use Node 22 and the committed package-lock.json. Avoid mixing
package managers. If dependencies are intentionally changed, regenerate/review
the lockfile rather than deleting it to make an error disappear.

**Port 5173 is occupied:** Vite normally prints another available port. Use that
URL, or start `npm run dev -- --port 5174`. A running older server can show older
files; identify its working directory before stopping a process.

**Backend warning:** start FastAPI on port 8000. Set VITE_API_BASE_URL to an empty value
and restart Vite for the frontend-only demo. For API mode, verify its URL,
CORS, response source_type and modeled assumptions. Initial incompatibility
switches the entire dashboard to synthetic demo inputs; later request failures
show a retry state instead of mixing synthetic and real analysis.

**Map tiles absent:** check network access and the visible tile-failure notice.
Synthetic grid/locations/scenarios still work; do not treat empty tiles as evidence
of offline map caching. Avoid bulk fetching tiles from the public OSM service.

**Slider change does not immediately change results:** intentional. Results are
marked outdated until Run scenario. The banner/cards/table/map must reflect the
last computed result together.

## Python pipeline

**python3.11 missing:** install Python 3.11 through a trusted local development
setup. Activate the virtual environment and use `python -m pip`, not a different
interpreter's pip.

**Parquet engine unavailable:** install backend/requirements.txt in the interpreter
running the script. PyArrow is required even in offline mode.

**No observed rows:** check the fetch log, key configuration, PM2.5 units, AOI and
provider coverage. A successful fallback is not a successful observed download.
Inspect source_type and target_provider in the resulting dataset.

**Weather is missing:** missing join hours remain null and weather_source_type
becomes missing. LightGBM accepts missing weather features; horizon features use issue-weather
persistence where possible. The pipeline does not invent weather observations.

**CAMS date range is short:** the implemented fallback uses recent output, not an
18-month archive. If there is no winter holdout, report that limitation.

## GitHub and hygiene

**CI fails after local success:** compare Python/Node versions, dependency lockfiles
and the failing command. Read job logs; do not bypass checks to get a green badge.

**A generated file appears staged:** unstage the path, preserve the local artifact,
and correct ignore rules if necessary. Never commit .env, raw/processed dumps,
models, node_modules or dist. Run scripts/check_repository.py after staging.

**A secret was already published:** rotate/revoke it first. Do not post it in an
issue; follow SECURITY.md. History cleanup needs a coordinated plan.

## Backend and ML

**LightGBM cannot load on macOS:** its native wheel needs OpenMP; install libomp
through your trusted package manager (for example Homebrew). Linux CI uses the
normal wheel/runtime. The application does not silently replace LightGBM with a
different model.

**First startup takes longer:** absent/mismatched models are regenerated from the
selected dataset before the server accepts traffic. Explicitly run train_model.py
first when preparing a recording. Artifacts remain ignored.

**Model loses to persistence:** this is a computed result, not an application
error. Show the warning and use training/CV decisions plus a new evaluation period
for improvements. Never tune repeatedly against the final holdout and still call
it untouched.

**Backtest references another sensor:** a current sensor may lack winter history.
The response discloses its nearest held-out reference; do not claim selected-sensor
accuracy from that series.

**Replay horizon is limited:** replay uses the pre-holdout 24-hour model. It is
limited to 24 hours and interpolates shorter points. Normal serving supports 72.

**Ask AirTwin shows "AirTwin evidence summary":** Gemini was unavailable or its answer failed verification twice. The reason is shown under the answer. Add or fix GEMINI_API_KEY / GEMINI_MODEL in the root .env and restart.
