# AirTwin finalv1 — implemented visual design

**Visual authority:** the user-provided `AirTwin_Full_Prompt_and_17_Design_Images(1).zip`,
especially `overview_municipal_approved.png`, the Map metric/ranked-area designs,
public and government Analytics references, and the Forecast/night/area-focus references.
Apple Maps images are styling inspiration only; no Apple imagery is included in AirTwin.

## Architecture

- **Overview**: immersive OpenStreetMap cartography, smooth source-labeled PM2.5 overlay, four floating cards.
- **Map**: metric selector, hotspot ranking, approximate locality search, map layers, details drawer.
- **Map → Analytics**: public AI questions and exposure tips plus an expandable workbench for backend-driven scenarios, proxy attribution, held-out model validation and model-based intervention budgeting.
- **Forecast**: 24/48/72-hour selected-reference PM2.5 chart, a matched spatial PM2.5 timeline where available (0, 3, 6, 9, 12, 18, 24h), selected-area focus, weather-aware night overlays and computed outlook cards.
- The welcome screen is separate; these are exactly three top-level application pages.

## Visual language

- Warm bone backgrounds, navy `#0b1f3a`, ocean `#1769aa`, gentle teal, restrained burgundy `#8d233b` for notable concerns.
- Thin translucent panels with calm shadows; generous spacing; responsive 8/12/16/24px rhythm.
- Full-bleed map behind Overview cards on desktops; stacked cards below the map on narrow devices.
- Map tiles are licensed public OpenStreetMap raster imagery with visible attribution. Key-restricted or proprietary map tiles are not used.
- The pollution raster is bilinear *visual smoothing* of real 12×12 modeled PM2.5 cells. It is never a higher-resolution measured data product.
- Accessible mouse/keyboard map marker selection, responsive controls, reduced-motion support and source-aware labels.

## Operational integrity

- **OBSERVED** is timestamped station evidence; **MODELED** includes CAMS, interpolation, forecasts and assumption-based scenario predictions; **SYNTHETIC** is explicitly labeled for offline/demo fallback.
- The UI never generates an official AQI, CO2, O2 or unsupported pollutant layer. Gas and PM10 markers use their provider units without borrowing PM2.5 color thresholds.
- The spatial forecast map uses only the backend's actual dated `/api/timeline` frames; a timestamp alignment check prevents combining grid frames with a location forecast issued at a different time.
- 48/72-hour location forecasts do **not** imply spatial maps beyond 24 hours. A fallback explicitly states when a compatible dated grid is unavailable.
- Selected source, metric, 24/48/72-hour horizon and Map Analytics view are preserved in shareable URLs and browser navigation.
- Questions use `/api/explain` when possible. Missing AI service produces a clearly identified non-AI evidence summary.
- Scenarios, source shares and planning costs are proxies/assumptions, not observed causal effects or authorized city operations.
- Secure public sign-in and privileged PMC/PCMC roles require an identity provider and role-protected server endpoints. Role screens remain locked rather than offering bogus access.

## Test status

- `npm run lint`, `npm test`, `npm run build`, `npm run test:sites`.
- GitHub Actions Quality checks also runs the Python backend and offline ML pipeline.
- GitHub Actions `finalv1-browser.yml` runs two separate Chromium journeys: visual synthetic-fallback screenshots across 1440px and 390px, and connected FastAPI-through-Vite checks for `/api/health`, station readings, forecast, spatial timeline, interventions and URL refresh state.
- Visual references are mockups, **not** proof of pollution measurements or forecast accuracy. Browser QA is still not a substitute for testing real upstream provider availability and production authentication.

## Files

- `src/pages/FinalExperience.tsx` — three-page app, source/forecast state, navigation.
- `src/components/FinalMap.tsx` and `SmoothHeatLayer.tsx` — interactive geography and labeled overlay.
- `src/components/ResearchWorkbench.tsx` — optional technical modeling.
- `src/lib/finalMetrics.ts`, `finalPlaces.ts`, `finalTimeline.ts`, `finalRoute.ts`, `finalOutlook.ts` — data contract adapters.
- `src/final.css` — layout, colors, responsiveness.

**Branch restriction:** implementation work stays on `finalv1`; do not change `dev/raj` or `main` without user authorization.
