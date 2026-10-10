# AirTwin finalv1 agent instructions

This branch is the user-approved **complete frontend redesign**, based on the
uploaded `AirTwin_Full_Prompt_and_17_Design_Images(1).zip` brief and its
17 reference images. The current design authority is `DESIGN.md`, **not** the
2026-09 eight-step guide or old dense glass dashboard.

## Hard requirements

- Keep exactly three main app pages: Overview, Map, Forecast. Map contains
  Analytics as a subview. Welcome/guest entry is separate.
- Preserve working FastAPI endpoints and the truthful source types:
  OBSERVED / MODELED / SYNTHETIC, real measurement timestamps, known units.
- Use actual backend data, never the values printed in reference mockups.
  Offline mock engine is allowed only when conspicuously labeled synthetic.
- Map tiles: use licensed OSM/CARTO or another attributed licensed provider.
  The Apple screenshot is a visual reference only; never copy its tiles.
- The only currently supported spatial gridded layer is PM2.5;
  no fake AQI/CO2/O2 pollutant measurement layers.
- Only authenticated and **server-verified** PMC/PCMC employees can get
  municipal tools; until backend auth exists, do not activate those controls.
- Preserve the existing Site worker/hosting contract and `frontend/tests` files.
- Respect reduced motion, keyboard input, responsive layouts, and readable maps.

## Implementation map

- `src/App.tsx`: mounts finalv1 three-page experience.
- `src/pages/FinalExperience.tsx`: role-safe guest entry, Overview, Map,
  Forecast, Analytics, deep-link/browser navigation.
- `src/components/FinalMap.tsx`: live interactive Leaflet map + provider
  attribution + separate measured and modeled overlays.
- `src/lib/finalMetrics.ts`: normalized metric and provenance adapter.
- `src/final.css`: approved bone/ocean visual system.
- Old `GuidedExperience.tsx` and `Dashboard.tsx` are retained as references;
  they are not the finalv1 entry point.

## Verification before deploy

`npm run lint`, `npm test`, `npm run build`, `npm run test:sites`
inside `frontend`, plus project backend CI. Fix warnings that materially
affect correctness. Browser screenshot and mobile keyboard/map tests are
a prerequisite for calling visual polish fully verified.

**Branch restriction:** all finalv1 frontend changes belong on `finalv1`.
Do not modify or merge `dev/raj` or `main` without new user permission.
