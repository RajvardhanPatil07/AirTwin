# AirTwin decision-workspace overhaul

Branch: dev/parth-overhaul. City-scale domain: Pune–PCMC (the experimental Maharashtra API remains available).

## Evidence contract

- **OBSERVED** = independently timestamped OpenAQ ground-station readings.
- **MODELED** = CAMS provider fields, LightGBM forecasts, interpolated grid cells, source-proxy shares and intervention results.
- **SYNTHETIC** = offline fallback and illustrative population weights.
- Interventions are conditional mathematical scenarios, not measured reductions or policy effectiveness.
- A grid cell is never presented as an additional ground station. Baseline vs intervention is never presented as observed before/after evidence.
- The original 24-hour chronological model validation and persistence-baseline comparison are retained.

## Frontend

One city-oriented decision workspace: map explorer, source hypotheses, 24/48/72-hour PM2.5 forecasts, intervention comparisons, and held-out validation with uncertainty disclosure. Stale provider snapshots and synthetic fallback remain visible.

## Backend

FastAPI v1 endpoints stay compatible. New versioned endpoints:

| Endpoint | Purpose |
|---|---|
| POST /api/v2/decision-runs | Compute traffic, industry, dust, combined scenarios; persist only when PostgreSQL is configured |
| GET /api/v2/decision-runs?region=pcmc | Recent modeled decision outcomes, not observations |
| GET /api/v2/data-health?region=pcmc | Persistence state and lineage limitations |
| GET /api/v2/hotspot-summary?region=pcmc | IDW-derived hotspot ranking with explicit interpolation caveat |
| GET /api/v2/samples?region=pcmc&source_type=observed | Actual timestamped records only, each labeled with its own provenance |

The existing LightGBM + persistence blend, pre-holdout evaluation, SHAP explanation and CAMS/OpenAQ ingestion pipelines remain in place rather than substituting an untrained neural network.

## PostgreSQL

The old \`provider_snapshots\` table remains for reliable restore. The idempotent migration \`backend/migrations/001_decision_store.sql\` introduces:

1. \`air_quality_samples\`: point/time/provider/provenance grain with independent original sample timestamps; indexes for temporal queries.
2. \`decision_runs\`: execution ID, original input source type, region, assumptions, controls and outcome summary, with modeled-only result label.
3. \`forecast_evaluations\`: explicit schema for imported validation evidence (not automatically fabricated or populated).

On a provider refresh, only past/present CAMS hourly fields (not forecast future hours) retain modeled provenance while OpenAQ stations retain observed provenance. Data expires after 180 days in \`air_quality_samples\`; scenario runs are not automatically deleted. The decision store is **optional** so offline demos still work. Never claim a decision is saved without a returned run ID.

## Validation gates

- Backend: \`PYTHONPATH=backend pytest backend/tests\`
- Frontend: \`cd frontend && npm ci && npm run build && npm test && npm run lint\`
- With PostgreSQL: configure \`DATABASE_URL\`, start API, inspect \`/api/v2/data-health\`, save a decision, then retrieve \`/api/v2/decision-runs\`.
- Run and review historical MAE/RMSE vs persistence; flag negative skill rather than hiding it.

## Deployment constraints

Existing hosting is Vercel frontend + Railway API. PostgreSQL is opt-in through \`DATABASE_URL\`; the repo contains no credentials. Live OpenAQ requires a provider key. Synthetic offline mode must never be labeled as live observations.
