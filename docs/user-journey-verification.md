# Desktop user journey verification

Tested locally on 11 October 2026 against the running frontend and backend.

| User's job | Journey checked | Result |
| --- | --- | --- |
| Resident: understand current air | Overview → Map → search Baner → select using keyboard → switch PM10 | Correct selected area, units and provenance; PM10 removes the PM2.5 surface |
| Resident: compare areas | Highest readings → shared provider group → select area | Equal model series share a group/rank; selecting a group updates map and details |
| Resident: decide what to do | Analytics → ask Gemini for resident and municipal steps using Baner PM10 | Live Gemini response includes sentences, separate action lists and evidence limitations |
| Resident: avoid stale advice | Change pollutant after receiving an answer | Previous answer clears |
| Resident: plan tomorrow | Forecast → 24/48/72 hours → keyboard slider to last hour | Selected dates, reference values and map frames update; normal map remains visible |
| Resident: return to an area | Browser Back → Forward → reload; grid-cell deep link | Page, location and horizon restore; reload starts at tomorrow within the saved horizon |
| Analyst: compare interventions | Research → What-if actions → compare | Backend returns individually labeled modeled reductions |
| Analyst: inspect source assumptions | Research → Source proxies → load | Proxy shares display with explicit limitations |
| Analyst: inspect historical skill | Research → Historical validation → load backtest | Observed Bhosari benchmark returned; persistence selected, with its separate station and historical scope disclosed |
| Planner: explore an illustrative budget | Research → Budget planning → compute → edit budget | Solver returns a hypothetical package; editing inputs clears the old result |
| Guest: understand account access | Account info | Verified sign-in and municipal execution are explicitly unavailable |
| User: recover from backend downtime | Backend restart → synthetic fallback → Refresh | Synthetic mode is explicit; refresh restores provider data |

## Fixes from this pass

- Grid-cell forecast history and future values now interpolate native CAMS anchors using the same IDW method as the map. Previously the chart used the nearest named reference. Weather remains a clearly documented nearest-reference estimate.
- Incomplete or invalid future spatial anchors return an availability error instead of a misleading grid forecast. Regression tests cover spatial agreement and invalid inputs.
- Area selection clears the old search text, preventing a previous area from remaining in the search box.
- Escape dismisses pollutant/ranking menus and area details. Browser history navigation clears an open pollutant menu.
- Editing intervention percentages, budget or reduction target invalidates old scenario/planning results and pending responses.

## Validation

- Backend suite: 110 tests passed.
- Frontend suite: 38 tests passed.
- Hosting contract: 4 tests passed.
- ESLint, TypeScript check and production build passed.
- Live API assertions: grid-cell chart/map agree at every published future frame within 24, 48 and 72 hours; unknown locations return 404 and invalid horizons return 422.
- Desktop browser checks at 1440 × 900: forecast chart renders and no horizontal page overflow.

## Presentation flow

1. Start at Overview and explain the source/freshness banner.
2. Open Map, search for Baner, and compare shared reference groups.
3. Open Analytics and ask: “What can residents and the municipality do to improve air quality here?”
4. Open Forecast, change the horizon and move the time slider.
5. Optionally show a read-only intervention comparison under Research & policy modeling.

## Current limits

No fresh observed monitor readings were available during this run. CAMS samples are coarse modeled estimates; equal neighborhood values are legitimate shared provider data. Local spatial error and provider forecast confidence are unvalidated. AQI, CO₂ and O₂ remain unavailable. Planning costs and responses are scenario assumptions. Secure municipal sign-in and execution are not connected. This is a desktop local verification, not certification of every device, production deployment or future provider response.
