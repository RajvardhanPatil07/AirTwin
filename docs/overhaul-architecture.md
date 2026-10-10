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


## Performance architecture (dev/parth-overhaul only)

The previous dashboard fan-out fetched stations, hotspots, forecast, backtest,
attribution, scenarios, and timeline during initial navigation; this could
trigger repeated spatial interpolation and multiple slow model evaluations.
The optimized path is:

```text
React shell → GET /api/v2/bootstrap → shared Runtime.cached_snapshot()
      │               │
      │               └── station metadata + cells + source evidence
      ├── active panel only → forecast OR source analysis OR validation
      ├── overview → forecast and policy overview (independent requests)
      └── click "Load modeled forecast playback" → timeline interpolation
```

- **Single initial spatial request:** `GET /api/v2/bootstrap` combines
  station/context and modeled hotspot cells. Older backends remain supported
  through the two existing `/api/stations` and `/api/hotspots` routes.
- **Per-runtime grid snapshot reuse:** a bounded eight-key, 30-second cache
  serves concurrent read endpoints. Provider refresh creates a new runtime
  instance and therefore a fresh cache. Scenario outputs allocate new cells,
  so baseline map cells are never rewritten by an intervention.
- **Browser query deduplication:** reads use a bounded 64-entry in-memory
  cache with expiry; in-flight identical queries share one Promise. Failed
  responses are not cached. Explicit refresh bypasses the dashboard cache.
  Decision writes and AI explanations are never cached.
- **Demand-based analysis:** the map and shell can display while unrelated
  model calculations are deferred until the user opens their specific panel.
  Timeline replay is opt-in because it can interpolate thousands of values.
- **Independent visual chunks:** Leaflet map and Recharts chart modules
  load separately via React.lazy/Suspense. The core UI can render before
  the map or plotting libraries load. The map maintains its own stable
  placeholder height.
- **Smooth map gestures:** a resized map no longer forces zoom to level 11
  or repeatedly refits the viewport. Resize invalidation is coalesced per
  animation frame. Each grid cell uses one vector layer rather than two.

### Performance acceptance checks

1. On a cold page visit with an available upgraded API, the frontend should
   request one bootstrap payload instead of two station/grid payloads.
2. Before choosing playback, `/api/timeline` must not be requested.
3. Attribution and validation requests should occur only when the relevant
   inspector tab is opened.
4. Zoom and pan should persist when the viewport layout resizes.
5. Fast repeated reads should reuse cached data; a manual refresh should fetch
   a fresh city bootstrap; failed requests must not become cached success.
6. Run `pytest backend/tests` and `npm run lint && npm test && npm run build`
   in CI. Validate actual startup TTFB, transfer bytes, p95 API latency,
   and interaction frame timings before claiming measured speedups.

**Limitations:** No quantified latency reduction or guaranteed frame rate has
been measured by this change alone. Model loading on cold API instances and
provider/network delays remain deployment-level risks. Source labeling,
historical validation, and all existing `/api/*` response contracts remain
part of the acceptance gate.
