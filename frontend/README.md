# AirTwin PCMC frontend

React/Vite/TypeScript dashboard preserving the supplied Kombai screenshot.
Development and local preview connect to FastAPI through the same-origin `/backend` proxy.
Run `python3 scripts/dev.py` from the repository root to start both services without retraining.
For hosted builds, set `VITE_API_BASE_URL` to the public backend URL and configure
backend `CORS_ORIGINS` with the frontend origin. An empty API URL explicitly selects demo mode.

```sh
npm ci
npm run dev
```

Provider keys belong in the root backend `.env`, never frontend variables.
To change the public backend URL, copy `.env.example` to `.env` and restart Vite.
Set `VITE_API_BASE_URL=` explicitly for frontend-only illustrative demo mode.

## Working views

- Map: 12×12 grid, actual snapshot stations, proxy zones, layer toggles and after view.
- Forecast: LightGBM series, quantile band, source badge and exact TreeSHAP groups.
- Backtest: actual held-out series/model/persistence, computed metrics, coverage,
  seasonal baseline and underperformance warnings.
- Sources: proxy concentration shares; assumptions distinguish them from SHAP.
- Scenarios: three cuts, combined package and synthetic-population exposure ranking.
- Historical replay: labeled date/source, synchronized API queries and pre-holdout model.
- Ask AirTwin: actual-output context, optional LLM or grounded no-key template.

Initial API failure switches the whole input set to the synthetic mock with DEMO
DATA and a warning. Subsequent analysis failures show retry rather than mixing
real inputs with mock output. The backend can also train on the offline sample;
that is real model execution on synthetic targets, labeled SYNTHETIC TARGET · ML,
and distinct from the illustrative frontend mock.

## Consistency and caveats

One scenario result drives banner, cards, table and map; baseline station readings
stay unchanged in after view. Population is synthetic even when targets are observed.
Cell history/validation uses disclosed reference stations. Data timestamps and
stale warnings matter: successful API fetches do not guarantee current observations.
Forecast issue time is the last available snapshot, not automatically the wall clock.

Proxy zones are approximate. The basemap needs network; grid/charts/scenarios work
without tiles and display a notice. Fonts are bundled. Source labels and assumptions
must remain visible in screenshots and video.

## Checks

```sh
npm run lint
npm test
npm run build
npm run test:sites
```

See `../docs/api.md`, `src/types.ts`, `DESIGN.md` and `design-qa.md`. The original
mock calculations remain tested in `src/mocks/engine.ts`; they do not describe
backend model accuracy. Inter is SIL OFL; retain OpenStreetMap and provider credits.

## Guided frontend

The default screen is the reference-based eight-step AirTwin guide. It uses adapted Vengeance UI Spotlight Navbar and Animated Button components, Leaflet geography and Recharts visualizations. The guide connects through `/backend` to FastAPI for location estimates, map cells, forecasts, source proxies, scenarios, budget optimization, historical validation and Gemini Ask AirTwin. A failed initial connection switches to an explicitly labeled offline example; failed analyses show errors and Retry. Review exports backend results and their provenance as JSON. Advanced view retains the full dashboard. `src/guided.css` scopes the responsive guide theme, including dark and reduced-motion states. See `design-qa.md` and `docs/guided-evidence/` for verification.
