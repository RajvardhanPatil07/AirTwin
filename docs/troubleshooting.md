# Troubleshooting

## Frontend

**npm ci fails:** use Node 22 and the committed package-lock.json. Avoid mixing
package managers. If dependencies are intentionally changed, regenerate/review
the lockfile rather than deleting it to make an error disappear.

**Port 5173 is occupied:** Vite normally prints another available port. Use that
URL, or start `npm run dev -- --port 5174`. A running older server can show older
files; identify its working directory before stopping a process.

**Backend warning:** no backend exists in this release. Unset VITE_API_BASE_URL
and restart Vite for the pure demo. If using a future backend, verify its URL,
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
becomes missing. The model must later define how to handle this; the current
pipeline does not invent weather observations.

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
