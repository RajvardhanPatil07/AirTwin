# AirTwin finalv1 — map-first environmental application

This is the complete redesigned frontend on the **finalv1** branch. The former guided eight-step interface is archived in source and is no longer the default view.

## Main application pages

| Page | User functions |
| --- | --- |
| **Overview** | Full-bleed live-provider/synthetic-fallback map, four accessible summary cards, location search and clear source labels |
| **Map** | Location selection, ranked reference readings, available pollutant switching, observed monitors versus interpolated modeled cells, detailed area drawer |
| **Forecast** | 24/48/72-hour PM2.5 trend, selected-location outlook, backend spatial forecast frames, day/night effects and focus mode |

**Analytics** is a subview of Map, not a fourth page. It contains the connected Ask AirTwin service, public exposure guidance and a collapsible Research workbench for four backend computations: hypothetical traffic/industry/dust scenarios, source-proxy attribution, historical validation and budget optimization.

## Map and numerical integrity

- Uses Leaflet and correctly attributed CARTO/OpenStreetMap basemaps, not copied Apple map tiles.
- Its smooth heat overlay is only a visual resampling of the backend's existing coarse 12×12 modeled grid. It is not additional observed or street-level data.
- Uses API timestamps, µg/m³ units and OBSERVED/MODELED/SYNTHETIC source labels. Data older than 24 hours remains marked stale.
- Does not fabricate official AQI or CO2/O2. Unsupported pollutant selectors remain disabled. PM10, NO2, SO2 and ozone depend on actual provider availability.
- For available backend spatial forecasts, renders /api/timeline output at 0, 3, 6, 9, 12, 18 and 24 hours. The 48/72-hour chart remains supported, but the spatial map is not falsely extrapolated beyond its final frame.
- No public user can execute governmental actions. Scenarios are non-operational models. Secure public registration and authenticated PMC/PCMC privileges require a real identity-provider/backend role-integration; until provided, these options are explicitly locked.

## Start on Windows

**PowerShell 1 — FastAPI server**, working directory C:\Users\mayur\AirTwin\backend:

~~~powershell
cd C:\Users\mayur\AirTwin\backend
..\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
~~~

**PowerShell 2 — Vite frontend**, working directory C:\Users\mayur\AirTwin:

~~~powershell
cd C:\Users\mayur\AirTwin
git fetch origin
git switch finalv1
git pull --ff-only origin finalv1
cd frontend
npm ci
npm run dev
~~~

Visit the URL printed by Vite, usually http://localhost:5173. Vite forwards /backend requests to the running FastAPI instance. To deploy separately, set frontend VITE_API_BASE_URL to the public FastAPI URL and configure backend CORS_ORIGINS for the frontend origin. Keep Gemini/OpenAQ/database secrets on the server, not in VITE_ variables.

## Verification

~~~sh
npm run lint
npm test
npm run build
npm run test:sites
~~~

GitHub Actions on this branch also runs Python offline-backend validation and **AirTwin finalv1 browser QA**, which starts Vite in Chromium, exercises guest entry, Map, ranked selection, Analytics scenarios, Forecast, and a mobile-width overflow check. Screenshots of the tested offline application are downloadable from that workflow's artifact. They are labeled synthetic and not proof of live observed data.

| Source | Responsibility |
| --- | --- |
| src/pages/FinalExperience.tsx | Guest entry, three-page navigation, API-based cards, Map/Analytics/Forecast views |
| src/components/FinalMap.tsx | Licensed Leaflet tiles, clickable stations and grid, locality search, focus mode |
| src/components/SmoothHeatLayer.tsx | Visualized 12×12 backend PM2.5 interpolation |
| src/components/ResearchWorkbench.tsx | Modeled scenario, source, backtest and planning API clients |
| src/lib/finalMetrics.ts | Typed metrics, provenance, freshness and capability gating |
| src/lib/finalPlaces.ts | Named localities resolved to existing modeled cells, never invented sensors |
| src/lib/finalTimeline.ts | Honest selection of available spatial forecast frames |
| src/final.css | Approved warm-bone / ocean-blue visual direction |

See DESIGN.md for visual rationale and ../docs/api.md for backend contracts. Older GuidedExperience/Dashboard files remain as archived references only.
