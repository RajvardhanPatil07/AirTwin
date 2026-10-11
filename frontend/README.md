# AirTwin frontend

The React frontend for AirTwin, an environmental digital twin for Pune and Pimpri-Chinchwad. Users can inspect air quality, explore forecasts and compare hypothetical pollution controls through a map-based interface.

## Application pages

| Page | What it provides |
| --- | --- |
| Overview | Regional map, summary readings, location search and source/freshness information |
| Map | Area selection, pollutant readings, grouped provider rankings and location details |
| Forecast | Selected-area PM2.5 outlook for 24, 48 or 72 hours, time navigation and available spatial forecast frames |

Analytics sits within Map. It contains Ask AirTwin and a Research workbench for hypothetical interventions, source proxies, historical validation and budget planning. Guest entry is separate from the three main pages.

## Technology

React 19, TypeScript and Vite power the application. Leaflet renders maps with attributed CARTO/OpenStreetMap tiles. Recharts renders forecast charts. Tailwind CSS and application styles provide the interface, with Zod validation for selected API contracts.

## Run with the backend

From the repository root, after installing the Python and frontend dependencies:

```sh
python scripts/dev.py
```

Open [http://127.0.0.1:5188/](http://127.0.0.1:5188/). The launcher starts the backend on port 8000 and frontend on port 5188. Full setup instructions are in the [project README](../README.md).

To run the services separately, use two terminals:

```sh
# Repository root, with the Python environment activated:
python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000
```

```sh
cd frontend
npm ci
npm run dev -- --port 5188 --strictPort
```

## API connection and deployment

Vite forwards `/backend` requests to `http://127.0.0.1:8000` in development and preview. Set `AIRTWIN_BACKEND_URL` to change the proxy target.

For a separately hosted frontend, set `VITE_API_BASE_URL` to the public FastAPI URL before building and configure backend `CORS_ORIGINS` for the frontend origin. Leave the variable unset for the local proxy. An explicitly empty value selects demo mode.

Keep Gemini, OpenAQ and database credentials on the backend. Frontend `VITE_` variables are public build inputs.

```sh
npm run build
npm run preview -- --port 5188
```

The build outputs static assets to `dist/client` and runs the existing Sites packaging adapter. Static frontend hosting does not run the Python backend. Preserve the worker and hosting contract when changing deployment settings.

## Data behavior

- Readings carry observed, modeled or synthetic labels, timestamps and units.
- Equal neighborhood values can share a provider reference. Rankings group those shared readings rather than imply independent monitors.
- PM2.5 is the supported spatial grid layer. Other pollutant selectors depend on provider availability; official AQI, CO₂ and O₂ are not fabricated.
- The smooth heat overlay resamples the coarse backend grid for display. It adds no measured detail.
- Grid forecasts use backend spatial interpolation. Map frames must align with the selected forecast origin and available timeline; missing cells or unsupported times are not filled with current values.
- Initial API failure can show a labeled synthetic demonstration. Refresh connection allows users to retry the backend.
- Changing selected context clears outdated answers and analysis outputs where needed. Edited scenario and budget inputs invalidate previous results.

Source-proxy shares are assumptions, and SHAP explains forecast inputs. Hypothetical intervention results are not validated causal effects. Verified municipal sign-in and governmental execution are unavailable until backend authentication and authorization are connected.

## Checks

Run from `frontend`:

```sh
npm run lint
npm test
npm run build
npm run test:sites
```

Backend checks are listed in the project README. Local user journeys and remaining limitations are recorded in [user journey verification](../docs/user-journey-verification.md). Browser and mobile testing are needed before claiming visual behavior is fully verified.

## Source guide

| File | Responsibility |
| --- | --- |
| `src/App.tsx` | Application entry component |
| `src/pages/FinalExperience.tsx` | Guest entry, navigation, Overview, Map, Analytics and Forecast |
| `src/components/FinalMap.tsx` | Map interaction, location selection, search and overlays |
| `src/components/SmoothHeatLayer.tsx` | Visual resampling of the backend pollution grid |
| `src/components/ResearchWorkbench.tsx` | Scenario, source, validation and planning controls |
| `src/lib/api.ts` | Backend requests and fallback handling |
| `src/lib/finalMetrics.ts` | Readings, freshness, capabilities and provider-reference grouping |
| `src/lib/finalPlaces.ts` | Supported locality lookup |
| `src/lib/finalTimeline.ts` | Spatial forecast frame selection and alignment |
| `src/final.css` | Application styling |

Older `GuidedExperience` and `Dashboard` components remain in source as references; `FinalExperience` is the active application.

See [design rationale](DESIGN.md), [design checks](design-qa.md), [component attribution](src/components/ui/ATTRIBUTION.md) and the [backend API reference](../docs/api.md).
