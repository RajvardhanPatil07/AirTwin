# Frontend API contract

Status: adapter implemented; FastAPI endpoints are not implemented yet.
The definitive types are `frontend/src/types.ts`. No backend integration is claimed.

All concentrations use µg/m³. All responses have `source_type` and `assumptions`.
The adapter rejects missing provenance and missing assumptions for modeled responses.
Station and population provenance are independent of response-level provenance.

| Method / path | Query or body | Response type |
| --- | --- | --- |
| GET `/api/stations` | None | `StationsResponse`: `stations: Station[]` |
| GET `/api/hotspots` | `mode=before` | `HotspotsResponse`: `cells: Cell[]` |
| GET `/api/forecast` | `location_id`, `hours=24\|48\|72` | `ForecastResponse` |
| GET `/api/backtest` | `location_id` | `BacktestResponse` |
| GET `/api/attribution` | `location_id` | `AttributionResponse` |
| POST `/api/scenarios` | `{location_id, cuts: {traffic, industry, dust}}` | `ScenarioResponse` |

Cuts are percentages on a 0–100 scale (not fractions). UI limits: traffic 50,
industry 60, dust 70. Results include individual actions and `combined`, each
with its own full after-grid. The frontend uses those grids directly rather
than reapplying backend scenario math. Server hotspot after queries can be added
later if the contract changes to avoid transmitting duplicate grids.

## Data shapes

- `Station`: `id`, `name`, `short_name`, latitude/longitude, `pm25`, ISO timestamp,
  source type and assumptions. Synthetic demo locations are not monitoring stations.
- `Cell`: `id`, center, `bounds: [[south, west], [north, east]]`, concentration,
  background, population and its source type, `local_weights` (traffic/industry/dust),
  source type and assumptions.
- `SeriesPoint`: timestamp, nullable actual/predicted/persistence/p10/p90.
  Null distinguishes absent history/forecast points from zero concentration.
- `ForecastResponse`: location ID, series, history source type, source type,
  assumptions. Demo interval is explicitly illustrative.
- `BacktestResponse`: location ID, method, series, target source type, metrics,
  source type, assumptions. Metrics: `mae`, `rmse`, `r2`, `persistence_mae`,
  `improvement_percent`, `interval_coverage` (percent).
- `AttributionResponse`: location ID, background, shares (`name`, fraction `value`,
  color), source type, assumptions. Shares including background sum to one.
- `ScenarioResponse`: scenario ID, location ID, ranked `results`, source type,
  assumptions. Every result contains action ID/name/cuts/rank, before/after,
  reduction and its low/high range, reduction percent, exposure benefit,
  population provenance and after-grid cells. Reductions are positive magnitudes.

`local_weights` sum to one over local sources; concentration `shares` include
background. The simulator multiplies local weights by local excess, avoiding
double-discounting background. Population-weighted exposure benefit is the sum
of cell reductions × cell population, in person·µg/m³.

`/api/health`, `/api/explain`, SHAP groups, real backtests, historical replay,
and operational forecast weather are still pending backend work.
