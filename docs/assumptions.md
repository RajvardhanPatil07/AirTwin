# Phase 1 assumptions

- AOI bounding box: longitude 73.70–73.98, latitude 18.45–18.80.
- City centroid weather: latitude 18.625, longitude 73.84. This loses local variation.
- OpenAQ sensor IDs identify target series; multiple sensors at a location remain separate.
- Initial coverage threshold: at least one sensor with 720 valid station-hours.
  Continuity and winter coverage still need evaluation in Phase 2.
- Weather reanalysis is modeled, not an observed station weather measurement or a
  historically available forecast. Phase 2 must avoid claiming operational performance
  when evaluated with future reanalysis features.
- CAMS is a modeled concentration target; it does not become observed after training.
- The synthetic fixture uses deterministic daily/seasonal signals for debugging only.
- No missing target hours are imputed. No chemical source attribution has been implemented.
- Named zone coordinates remain unverified; no zone polygons are shipped yet.

Source attribution formulas, intervention pass-through assumptions, and population
provenance will be added in Phase 4 before modeled benefits are exposed.

## Frontend prototype assumptions

The frontend now demonstrates attribution and interventions using synthetic fixtures
in `frontend/src/mocks/engine.ts`. These are separate from the Phase 1 dataset and
are not a fitted model or measured source apportionment. No backend source engine
or zone GeoJSON has been implemented yet; frontend zone outlines are illustrative.

- Six named demo locations use synthetic PM2.5 values and approximate coordinates.
- A 12×12 grid uses inverse-distance weighting with power 2.
- Regional background uses the 15th percentile of simultaneous demo concentrations,
  capped at each location's concentration. Local excess cannot be negative.
- Traffic, industry, and dust proxy weights are normalized over local excess.
  Background and local concentration shares sum to one.
- Central intervention reduction is local excess × the sum of local source weights
  × emission cuts × 0.7. Individual and combined actions use the same calculation.
- Low/high reduction varies pass-through from 0.6 to 0.8 and weights by ±20%,
  capped at local excess. These are illustrative sensitivity bounds.
- Exposure benefit sums concentration reduction × synthetic cell population;
  it is not a count of people protected.
- Forecast curves and bands are illustrative. Backtest metrics are computed from
  synthetic series using a persistence predictor; they are not real ML validation.
