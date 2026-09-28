# Implemented API contract

FastAPI serves `/api`; interactive OpenAPI documentation is at
`http://127.0.0.1:8000/docs`. `frontend/src/types.ts` and `backend/app/schemas.py`
share the contract. Provider credentials never appear in responses.

All concentrations are µg/m³. Responses carry `source_type`; modeled responses
carry `assumptions[]`. Nested station/history/target/population/weather provenance
is independent. Null chart points mean absence, not zero.

| Method / path | Inputs | Response |
| --- | --- | --- |
| GET `/health` | None | Status, dataset rows/time, target provenance and warnings |
| GET `/stations` | optional replay_at | Stations at shared snapshot, warnings, weather, proxy zones |
| GET `/hotspots` | mode=before\|after, scenario_id, replay_at | 144 modeled cells; after returns combined scenario grid |
| GET `/forecast` | location_id, hours=1–72, replay_at | History + forecast + quantiles + TreeSHAP groups |
| GET `/backtest` | location_id, replay_at | Held-out target/model/persistence series and metrics |
| GET `/attribution` | location_id, replay_at | Background, shares and complete assumptions config |
| POST `/scenarios` | location_id, cuts, optional replay_at | Ranked actions with selected-location values and after grids |
| GET `/timeline` | region, replay_at | Snapshot + forecast frames (0–72 h; ≤24 h in replay) of station and grid PM2.5 |
| GET `/replay` | None | High held-out target timestamp and reference location |
| POST `/explain` | location_id, question, optional replay_at | Evidence-checked Gemini answer (`gemini_evidence_checked`) or labeled `grounded_summary` fallback |

`replay_at` is an ISO timestamp with timezone offset. Snapshot selection never
fills a missing observation. Replay forecasts use the pre-holdout 24-hour model;
hours >24 are rejected in replay mode. The UI reloads all data when replay changes.

Timeline hour 0 uses the same grid values as `/hotspots?mode=before`. For the
one-station SYNTHETIC fixture, future frames use illustrative spatial anchors
scaled from that station's forecast. These anchors are not extra observations or
independent forecasts. For real multi-station inputs, future frames continue to
interpolate per-station forecasts by IDW.

## Scenario request

```json
{
  "location_id": "12304615",
  "cuts": {"traffic": 20, "industry": 30, "dust": 30}
}
```

IDs above are an example from the fetched dataset, not guaranteed future IDs.
Discover current IDs through `/stations`. Cuts are percentages, bounded to
traffic 0–50, industry 0–60 and dust 0–70. The response returns `combined`,
`traffic`, `industry`, `dust`, ranked by AOI-wide exposure reduction.

Each result includes `before`, `after`, positive `reduction`, low/high sensitivity,
percentage reduction, `exposure_benefit`, `exposure_benefit_low`,
`exposure_benefit_high`, synthetic population provenance and a
full `cells[]` after-grid. One selected result drives every frontend scenario view.
Scenario IDs are held in a bounded in-memory cache and disappear on restart.

## Shapes and interpretation

- Station: ID/name/short_name, coordinates, concentration, timestamp, provenance.
- Cell: ID/center/bounds, concentration/background, population/provenance,
  local_weights, modeled provenance/assumptions. Bounds are latitude/longitude pairs.
- Forecast: history provenance and reference sensor, nullable series, source and
  assumptions, TreeSHAP groups/base/prediction, forecast-weather context.
- Backtest: target provenance, method, series, metrics, pooled seasonal baseline,
  purged CV details, `skill[]` per horizon (AirTwin, LightGBM-only, persistence, seasonal,
  CAMS MAE, blend weight, band coverage) and validation-reference assumptions.
- Metrics: MAE/RMSE in concentration units, R², persistence MAE, improvement percent
  and interval coverage percent. Negative improvement is a model loss.
- Attribution: four total concentration shares summing to one, separate from
  normalized local excess weights used by scenarios.
- Explanation: evidence-cited Gemini claims and source-tagged answer, gemini_evidence_checked,
  context built from actual location/model/attribution/scenario/backtest outputs.

Grid forecasts/history and validation reference a nearby station. If a current
sensor lacks holdout data, backtest uses a disclosed nearest held-out reference
sensor; that result must not be interpreted as selected-sensor accuracy.

## Errors and fallback

Unknown IDs/scenarios and unavailable replay timestamps produce 404; malformed
inputs, cut limits and unsupported replay horizons produce 422. The frontend
initially falls back as a complete synthetic demo if the API is unavailable or
fails provenance checks. Later analysis failures show a retry state.

The backend falls back to the sample if processed input is missing/unreadable and
regenerates models when artifacts are absent/mismatched. Such targets remain
SYNTHETIC and trigger warnings. Stale data are reported rather than relabeled live.

## Local examples

```sh
curl http://127.0.0.1:8000/api/health
curl http://127.0.0.1:8000/api/stations
curl 'http://127.0.0.1:8000/api/forecast?location_id=12304615&hours=24'
```

No environmental API key is required by local frontend requests; keys stay on
the backend machine. CORS permits the local Vite origins on port 5173.

## Regional queries

Stations, hotspots, forecast, backtest and attribution accept `region=pcmc|maharashtra`
(default pcmc for backward compatibility). Scenario and explain bodies accept `region`.
Explain also accepts `cuts`, `hours` and bounded `history`. State forecasts have null
SHAP/p10/p90; state backtests return `available=false`, `metrics=null`, `series=[]`.
Stations include regional bounds/boundary, coverage, pollutant units and weather.
Gemini configuration, network or verification failures return 200 with `method=grounded_summary`
and the reason in `assumptions`; the summary is built only from computed outputs.
