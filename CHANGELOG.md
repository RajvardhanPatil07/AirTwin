# Changelog

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

### End-to-end implementation

- Added FastAPI/Pydantic endpoints and connected the existing dashboard.
- Added LightGBM direct forecasts, quantiles, winter holdout, purged CV and baselines.
- Added generated observed-target metrics/model card; underperformance is disclosed.
- Added archived issue-aligned forecast weather and exact TreeSHAP feature groups.
- Added configured spatial/source/scenario engine with synthetic population labels.
- Added grounded explanation drawer and historical replay with pre-holdout model.
- Added backend leakage, split, spatial, scenario and endpoint tests.
- Added fetch → build → train → serve runner and CI training checks.

Data availability/freshness and calibrated policy or health effects remain limited.
