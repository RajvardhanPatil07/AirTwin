# Prioritized roadmap

## Implemented foundation

- [x] Preserve station-hour gaps instead of treating adjacent rows as adjacent hours.
- [x] Build PM2.5 lag/rolling, cyclical and issue-time weather features.
- [x] Train an executable scikit-learn gradient-boosting model.
- [x] Use chronological holdout validation and a persistence baseline.
- [x] Compute MAE/RMSE/R²/improvement/interval coverage from predictions.
- [x] Implement FastAPI health, stations, hotspots, forecast, backtest, attribution and scenarios.
- [x] Return provenance + assumptions from analytical endpoints.
- [x] Implement 12×12 hotspot grid, source proxies and three intervention categories.
- [x] Add backend model/spatial/API tests and CI coverage.

## P0: convert executable capability into strong observed evidence

- [ ] Run the live OpenAQ path and report sensors, dates, gaps, units and provider attribution.
- [ ] Verify whether adequate observed winter coverage exists; never relabel CAMS/sample fallback as observed.
- [ ] Save a reproducible metrics JSON for the exact submission dataset and date range.
- [ ] Compare the one-hour model with persistence and at least one seasonal/hour-of-day baseline.
- [ ] Replace held-constant future weather with archived/operational forecast weather if available.
- [ ] Record frontend screenshots/video while connected to `VITE_API_BASE_URL` and keep provenance visible.

## P0: improve source attribution inputs

- [ ] Replace approximate traffic anchor with sourced road-density / traffic-count features.
- [ ] Replace industrial anchors with verified industrial-zone polygons or emission inventory proxies.
- [ ] Add construction/road-dust proxy layer and explicit wind-direction convention.
- [ ] Keep forecast feature importance separate from source-share attribution.
- [ ] Replace synthetic population surface with a licensed population raster if time permits.

## P1: robustness and presentation

- [ ] Add multi-station/per-station metric table and explicit underperformance warnings.
- [ ] Add historical replay with synchronized map/chart issue timestamps.
- [ ] Add API cache invalidation/reload after rebuilding the processed dataset.
- [ ] Add provider/data timestamp panel to the frontend for backend mode.
- [ ] Verify approximate zone/location coordinates before final recording.

## P2: standout features after evidence is solid

- [ ] Grounded explainer restricted to current model/scenario outputs.
- [ ] Additional pollutants with pollutant-specific assumptions.
- [ ] Higher-detail spatial rendering only where it improves interpretation.
