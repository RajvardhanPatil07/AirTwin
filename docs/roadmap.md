# Prioritized roadmap

The deadline favors a complete, honest path over extra screens. This plan records
future work; checkboxes require implementation and evidence before completion.

## P0: establish real data and forecast evidence

- [ ] Fetch observed station coverage and report sensors, dates, gaps and units.
- [ ] Determine if a real winter holdout exists; expose modeled target fallback.
- [ ] Build station-separated hourly lags without treating gaps as prior hours.
- [ ] Add lag/rolling, cyclical, wind, humidity, rain and stagnation features.
- [ ] Choose one clearly defined forecast issue time and 24-hour direct target.
- [ ] Separate train, CV and winter holdout with horizon-aware temporal gaps.
- [ ] Fit LightGBM; compare persistence and training-only seasonal hourly mean.
- [ ] Compute MAE/RMSE/R²/improvement/coverage and write a generated model card.
- [ ] Document whether future weather uses archived forecasts or retrospective reanalysis.
- [ ] Save ignored artifacts and make training reproducible from scripts.

Evidence: generated metrics + exact dates/provenance + tests detecting leakage.
48/72-hour ML is optional after the 24-hour model works.

## P0: serve a coherent contract

- [ ] Implement FastAPI with Pydantic models matching frontend/src/types.ts.
- [ ] Implement health, stations, hotspots, forecast, backtest and attribution.
- [ ] Implement scenarios returning consistent selected-location and grid results.
- [ ] Return provenance and assumptions, including sample-fallback warnings.
- [ ] Configure development CORS and test invalid IDs, horizons and cut values.
- [ ] Load/regenerate models without pretending unavailable models exist.

Evidence: endpoint integration tests and frontend running against the API.

## P0: source and scenario consistency

- [ ] Centralize weights and assumptions in config/assumptions.yaml.
- [ ] Verify approximate locations and ship clearly sourced zone GeoJSON.
- [ ] Add road/industrial/construction proxies and explicit wind convention.
- [ ] Keep SHAP weather/temporal/persistence groups separate from source shares.
- [ ] Test background bounds, IDW identity, shares, zero cuts and additivity.
- [ ] Use a sourced population product or retain SYNTHETIC labels and limitations.

## P1: frontend integration and submission

- [ ] Replace demo responses with tested API outputs without redesigning the UI.
- [ ] Surface target, weather and population provenance where relevant.
- [ ] Show actual held-out coverage and underperformance warnings.
- [ ] Add one reproducible run workflow: fetch → build → train → serve.
- [ ] Record a three-minute video using real computed results when available.
- [ ] Add confirmed team names and contribution roles.
- [ ] Complete docs/acceptance.md with evidence for every required outcome.

## P2: standout features after the full path works

- [ ] Grounded explainer with provider-configurable LLM and no-key template fallback.
- [ ] Claims restricted to actual model context with provenance tags.
- [ ] Historical replay with date banner and synchronized map/chart data.
- [ ] More pollutants and validated alerts.
- [ ] Higher-detail spatial visualization only if it improves interpretation.

## Working checkpoints

Each implementation step ends with a summary, changed files, actual test output
and several meaningful commit groups. Do not mark an item complete because its
screen exists or because a dependency has been installed.
