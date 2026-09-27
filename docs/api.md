# Frontend API contract

Status: **implemented in `backend/app/main.py`**. The React adapter in
`frontend/src/lib/api.ts` consumes the same contract. All concentrations use µg/m³.
Every analytical response carries `source_type` and `assumptions`; station,
weather and population provenance remain separate.

Run the backend with:

```sh
python -m pip install -r backend/requirements-ml.txt
python -m uvicorn backend.app.main:app --reload --port 8000
```

Then start the frontend with `VITE_API_BASE_URL=http://localhost:8000`.
If the backend or its provenance contract fails, the existing frontend adapter
falls back to the explicitly synthetic browser demo.

| Method / path | Query or body | Response |
| --- | --- | --- |
| GET `/api/health` | None | service/data status |
| GET `/api/stations` | None | `StationsResponse` |
| GET `/api/hotspots` | `mode=before` | `HotspotsResponse` with 12×12 grid |
| GET `/api/forecast` | `location_id`, `hours=24|48|72` | recursive PM2.5 forecast |
| GET `/api/backtest` | `location_id` | chronological holdout + persistence baseline |
| GET `/api/attribution` | `location_id` | traffic/industry/dust/background proxy shares |
| POST `/api/scenarios` | `{location_id, cuts:{traffic,industry,dust}}` | ranked intervention results + after-grids |

## Forecast semantics

The backend trains a deterministic `HistGradientBoostingRegressor` from the
available dataset. It predicts one hour ahead from PM2.5 lags/rolling history,
calendar cycles and weather known at issue time. The final 20% of usable history
is held out chronologically for validation. Persistence predicts the next hour as
the latest PM2.5 value. Longer dashboard horizons recursively feed predictions
forward; future weather is held at its latest available value and this assumption
is returned to the client.

If the dataset is the committed sample, `target_source_type` / `history_source_type`
remain `synthetic`. Running the live ingestion pipeline is required before any
observed-data accuracy claim is supportable.

## Spatial and scenario semantics

Hotspot cells are MODELED inverse-distance interpolation of latest station values.
Traffic, industry and dust are transparent proximity/weather proxies, not measured
chemical source apportionment. The background is the 15th percentile of latest
station concentrations. Scenario cuts act only on local excess above background,
with central pass-through 0.70. Exposure ranking uses a SYNTHETIC population
surface and therefore supports relative comparison only.

Cuts are percentages and are clamped to the UI limits: traffic 50, industry 60,
dust 70. Each scenario result contains its own full after-grid; the frontend does
not recompute backend scenario math.
