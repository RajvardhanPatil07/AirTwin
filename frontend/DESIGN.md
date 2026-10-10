# AirTwin finalv1 — map-first municipal design

**Visual authority (11 October 2026):** the user-provided
\`AirTwin_Full_Prompt_and_17_Design_Images(1).zip\`, particularly
\`overview_municipal_approved.png\`, Map's metric/ranked-area references,
public/government Analytics views, forecast city/night and Baner focus images.
The Apple Maps screenshot is a cartographic *reference*, not a licensed tile source.

## Product structure

Exactly three main pages: **Overview**, **Map**, and **Forecast**.
**Analytics** is a subview under Map, not a fourth primary page. Welcome/guest
entry is separate. Public browsing does not require an account.

The frontend's new entry point is \`src/pages/FinalExperience.tsx\`. It
uses \`src/components/FinalMap.tsx\`, \`src/lib/finalMetrics.ts\`, and
\`src/final.css\`. The former guided experience and advanced dashboard remain in
the repository for reference; they are no longer mounted by the default App.

## Tokens and composition

- Bone/off-white background, navy \`#0b1f3a\`, ocean \`#1769aa\`, warm mist glass.
- Restrained burgundy \`#8d233b\` for hazards, teal for calmer spatial overlays.
- Map 60–70% of Overview width, with four compact cards on the side.
- Moderately blurred glass cards on the map, not a full-page frosted overlay.
- React Leaflet and genuinely licensed CARTO/OSM raster tiles with attribution.
- Coarse PM2.5 IDW cells are shown as an *interpolated modeled layer*, never
  described as a street-level measured heatmap. Clickable stations are separate.
- Forecast sky effects are interpretive and never reported as meteorological
  measurements. Reduced-motion users see no simulated atmosphere.

## Scientific and access boundaries

- The UI reflects the actual provider-returned concentrations, units, timestamps,
  and source types. No mockup numerics are wired to the production interface.
- Only PM2.5 has a spatial grid forecast-independent baseline. Other pollutants
  appear only when provider station/reference data supports their values.
- A published standards-compliant AQI layer, CO2 and O2 are **unavailable** on
  the present API. Do not convert individual hourly PM2.5 into official AQI.
- Source labels: OBSERVED, MODELED, SYNTHETIC; timestamps and freshness stay visible.
- Scenario interventions and employee actions require **server-verified employee
  authorization**. The current API has no supported authentication service, so
  public/employee account entry is deliberately not activated. Guest and
  public-data questions are available; do not mistake a role button for access.
- Historical validation remains separate from provider forecasts; model errors
  must not be misrepresented as live forecast confidence.
- Map forecast view labels the spatial grid as the *latest baseline* because the
  API does not currently expose a corresponding forecast grid for each hour.

## Validation

Use \`npm run lint\`, \`npm test\`, \`npm run build\`, and
\`npm run test:sites\` in the \`frontend\` folder.
The existing backend quality suite is still run by GitHub Actions.
Before production, integrate real verified user roles and conduct
browser-based responsive/a11y testing with a reachable tile provider.
