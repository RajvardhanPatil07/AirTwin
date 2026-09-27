# Calculation methodology

Scope: current TypeScript demo engine. These equations describe implemented
calculations, not calibrated environmental science. Source of truth:
`frontend/src/mocks/engine.ts`. Planned backend work is in roadmap.md.

## 1. Domain and inputs

AOI: south 18.45, north 18.80, west 73.70, east 73.98. The grid is 12×12, with
centers at the midpoint of each latitude/longitude rectangle. Six synthetic
location inputs and a fixed synthetic timestamp initialize the view. Coordinates
are approximate; readings are deliberately not represented as observations.

## 2. Inverse-distance interpolation

The local distance approximation is:

```text
d² = (cell_lat − location_lat)²
   + [(cell_lon − location_lon) × cos(cell_lat)]²
weight = 1 / d²
PM2.5_cell = Σ(weight × location_PM2.5) / Σ(weight)
```

Latitude is converted to radians for the cosine. An exact-location tolerance of
1e−12 returns that location's reading directly, avoiding a division by zero.
This is a local planar approximation suitable for demonstrating the AOI, not a
geodesic dispersion calculation. Cells do not have independent observations.

## 3. Regional background and local excess

Sort simultaneous input concentrations and linearly interpolate their 15th
percentile using index `(n−1)×0.15`.

```text
background_cell = min(regional_background, before_cell)
local_excess = max(before_cell − background_cell, 0)
```

Capping prevents a low-concentration cell from being raised to regional
background during a zero-cut scenario. The background cannot be reduced by
local interventions in this demonstration.

## 4. Proxy weighting

The demo uses spatial proximity only. For point `(lat, lon)`:

```text
proximity(a,b) = exp(−[(lat−a)² + (lon−b)²] / 0.003)
traffic_raw  = 0.6 + 0.5 × proximity(18.63,73.80)
industry_raw = 0.3 + 2.5 × [proximity(18.62,73.85) + proximity(18.76,73.86)]
dust_raw     = 0.5 + 0.6 × proximity(18.59,73.74)
local_weight_source = source_raw / Σ(raw_sources)
```

These constants are arbitrary illustrative assumptions, not emission inventory
measurements. The demo does not use OSM road density, time-of-day traffic,
industrial polygon area, upwind cosine or construction dryness. The implemented backend uses time profiles, upwind weighting and dryness, as
documented in assumptions.md. The frontend fallback uses only these simpler
illustrative formulas. Neither engine uses a measured emissions inventory.

For positive concentration C, displayed total shares are:

```text
source_share = local_weight_source × local_excess / C
background_share = background / C
```

The four displayed shares sum to one. The engine's seed values are positive;
the backend defines zero-concentration shares as 100% background.

## 5. Action cuts and central result

Cuts are percentages: 20 means 20%, not a 0.20 input. Clamp UI/demo ranges:
traffic 0–50, industry 0–60, dust 0–70. The individual packages retain only one
cut; combined uses all three.

```text
weighted_cut = Σ(local_weight_source × clamped_cut_source / 100)
ΔC = local_excess × weighted_cut × 0.7
after = max(background, before − ΔC)
reduction_percent = 100 × ΔC / before
```

The simulator applies cuts to local weights, not background-inclusive shares.
For fixed inputs and pass-through, combined ΔC equals the sum of individual ΔC.
With these cut bounds, the central reduction does not exhaust local excess, so
background clamping does not break this additivity. Display rounding can differ
slightly from a sum of table strings.

## 6. Sensitivity range

```text
low  = local_excess × weighted_cut × 0.6 × 0.8
high = min(local_excess, local_excess × weighted_cut × 0.8 × 1.2)
```

This varies pass-through and aggregate source scaling. It is a sensitivity
bracket, not a probabilistic confidence interval or a independently normalized
perturbation of every source share. Do not describe it as 80% calibrated coverage.

## 7. Synthetic population and exposure benefit

```text
population_cell = round(700 + 9000 × exp(−[(lat−18.60)² + (lon−73.83)²]/0.009))
benefit = Σ[(before_cell − after_cell) × population_cell]
```

Actions sort by descending benefit. Selected-location concentration reduction
and AOI-wide population benefit have different spatial scope. Benefit units are
person·µg/m³; there is no duration term, health dose response or count of protected
people. Combined exposure benefit also equals the sum of individual benefits.

## 8. Synthetic forecast and backtest

History is a deterministic sinusoidal sequence around each seed. Future values
use a daily cycle; ±14 µg/m³ bounds are illustrative. The backtest has 168 hourly
targets. Both predictor and persistence use the same reading 24 hours earlier.
No trained model or winter holdout is involved.

```text
MAE  = mean(abs(predicted − actual))
RMSE = sqrt(mean((predicted − actual)²))
R²   = 1 − Σ(error²) / Σ((actual − mean_actual)²)
improvement_percent = 100 × (1 − model_MAE / persistence_MAE)
coverage_percent = 100 × count(p10 ≤ actual ≤ p90) / evaluated_count
```

Actual UI metrics are computed from the series. This documentation does not
publish demo numbers as city forecast evidence. See model_card.md for the
separate requirements governing future real-model evaluation.

## Implemented backend (distinct from the frontend-only mock above)

The backend reads all constants from `config/assumptions.yaml`. Its local distance
uses kilometers, industry weights incorporate wind-from direction and zone-center
proximity, traffic uses an assumed corridor/hour profile, and dust uses humidity/
rain plus construction-zone proximity. These are still proxy assumptions.
`docs/assumptions.md` describes the full current backend method.

LightGBM direct forecasts now cover hours 1–24, 48 and 72; intervening horizons are
interpolated. Features are built on a complete station-hour axis. Archived forecast
weather is aligned to issue time for 24/48/72-hour models. Target-calendar features
are known in advance; rolling statistics use past values; current PM2.5 is known
at the issue timestamp. Data gaps remain gaps rather than shortening a lag.

The real holdout model is trained before the earliest test issue time. Purged CV
also excludes targets reaching each validation origin. Seasonal hourly means use
training data only. Serving models are subsequently refit on available targets;
stored holdout predictions are never replaced by refit-model predictions.
Read generated model_card.md for actual target provenance and computed metrics.
