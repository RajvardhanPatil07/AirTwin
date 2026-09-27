# Validation and test coverage

## Automated commands

Create a Python 3.11 environment and install the executable backend stack:

```sh
python -m pip install -r backend/requirements-ml.txt
python -m pytest backend/tests -q
bash scripts/pipeline.sh --offline
python scripts/check_repository.py
```

Run from `frontend/`:

```sh
npm run lint
npm test
npm run build
npm run test:sites
```

`make check PYTHON=.venv/bin/python` combines backend tests, frontend tests/lint/build
and hosting-worker checks. CI splits ingestion, backend and frontend into separate jobs.
No provider keys are needed for CI because the committed fallback is synthetic.

## What the suites prove

**Python pipeline:** outlier rejection/duplicate averaging, provenance preservation,
missing-weather handling, sample continuity and provider-failure fallback behavior.

**Forecasting backend:** chronological holdout construction, persistence baseline,
requested recursive horizon length and preservation of target/history provenance.

**Spatial/scenario engine:** 12×12 modeled grid, observed station provenance,
three local source categories plus background, normalized attribution shares,
zero-cut invariance and consistent combined-action behavior.

**FastAPI contract:** health, stations, hotspots, attribution, backtest, forecast
and scenarios work end to end on the committed sample; analytical responses include
`source_type` and `assumptions`.

**TypeScript browser demo:** zero cuts, source/local share invariants, IDW behavior,
synthetic persistence demonstration and sensitivity bounds.

**Frontend API adapter:** no request when backend is unconfigured; complete initial
fallback to the browser demo; rejection of invalid response provenance.

**Hosting worker:** static assets, SPA routing and worker behavior. This is separate
from FastAPI behavior, which is covered by `backend/tests/test_api.py`.

## Browser checks

Test both modes:

1. Browser-only deterministic demo with `VITE_API_BASE_URL` unset.
2. Backend mode with FastAPI on port 8000 and
   `VITE_API_BASE_URL=http://localhost:8000`.

Check tabs, location/cell selection, map layers, before/after views, scenario
outdated state, zero cuts, ranked actions, assumptions, error/retry behavior,
responsive layout and console errors. Keep provenance/date visible in screenshots.

## What a green CI badge does not prove

CI does not contact live environmental providers. A green badge therefore proves
code paths, invariants and reproducibility—not observed Pune/PCMC forecast accuracy,
chemical source apportionment, causal intervention effects or public-health impact.
Those claims require live provider coverage and separately recorded evidence.
