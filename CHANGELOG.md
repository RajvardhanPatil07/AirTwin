# Changelog

## 0.2.0 — executable ENR-01 backend

- Added FastAPI endpoints for stations, hotspots, forecast, backtest, attribution and scenarios.
- Added scikit-learn gradient-boosting PM2.5 forecasting with regular-hour lag features and a chronological holdout.
- Added persistence-baseline metrics and recursive 24/48/72-hour serving.
- Added backend IDW hotspots, weather-aware traffic/industry/dust proxy attribution and three intervention actions.
- Added provenance-preserving API/model/spatial tests and a dedicated CI job.
- Updated documentation to distinguish executable capability from observed-data evidence.


User-visible changes are recorded here; planned work belongs in docs/roadmap.md.

## Unreleased

### Added

- Screenshot-matched React dashboard with map, five tabs and light/dark themes.
- Explicit synthetic demo locations, population and persistence backtest.
- Additive traffic/industry/dust scenario comparison and exposure ranking.
- Typed API adapter with initial demo fallback and provenance checks.
- OpenAQ hourly ingestion, centroid weather and CAMS/sample fallback pipeline.
- Deterministic small sample, pipeline tests and frontend engine/adapter tests.
- Detailed setup, methodology, source attribution and judge-facing status docs.
- GitHub Actions, issue forms, PR checklist and repository hygiene check.

### Known incomplete work

- FastAPI endpoints, LightGBM training, SHAP and real winter validation.
- Backend-configured spatial inputs, real population and scenario serving.
- Grounded explanation assistant and historical replay.

No release tag or production readiness is implied by this entry.
