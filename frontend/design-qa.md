# Guided frontend verification, 10 October 2026

final result: passed

## Target and evidence

Source visual: `../../output/ui-concepts/airtwin-guided-workflow.png`, 1122 × 1402 pixels, the exact eight-screen board attached by the user. The ShelfFiles attachment expired during work; the identical workspace source was opened and used for the final comparison.

Rendered preview: http://localhost:4173/.
Evidence: `docs/guided-evidence/desktop-place.png`, `desktop-overview.png`, `desktop-forecast.png`, `desktop-sources.png`, `desktop-actions.png`, `desktop-plan.png`, `desktop-evidence.png`, `desktop-review.png`; `mobile-place.png`, `mobile-step-2.png` through `mobile-step-8.png`, and `mobile-dark-review.png`.

Desktop CSS viewport 1280 × 900, screenshot 1280 × 900 or full document height. Mobile CSS viewport 390 × 844, full-page evidence 390 pixels wide. Evidence uses browser screenshot output at 1 pixel per CSS pixel. Native screenshot output was clipped by the side panel after resizing, so full-page browser captures were used instead. The reference is a storyboard; each individual board screen is implemented as one responsive screen, not the whole storyboard as a single page. Composition comparisons account for this scale difference.

## Visual comparison

Source and implementation were opened together in the same comparison input. Full-view checks cover the white/green hierarchy, left welcome form and right geographic map, overview columns, forecast and map split, source donut plus guide, action sliders with before/after maps, budget and plan choices, evidence comparison, and review summary.

Focused checks cover forecast date labels, compact map place/value popups, selected infeasible plans and review warnings. Inter is retained from the existing project and matches the supplied sans-serif direction. Larger desktop type and spacing adapt the small board cells to a real app. Panel radii, thin borders and green actions follow the selected design. Leaflet uses genuine OSM tiles and library geometry for the explicitly illustrative grid; charts use Recharts and icons use Lucide. The existing leaf identity is retained. Copy distinguishes examples from observations, assumed source shares, simulated action effects and offline assistant availability.

## Comparison history

- Initial map capture exposed a provider requiring an API key. Replaced it with OpenStreetMap tiles and recaptured the working geography.
- Early Recharts capture showed an incomplete animated donut. Disabled chart entrance animations and supplied initial dimensions; final `desktop-sources.png` shows the complete chart, and the fresh-load console has no errors or warnings.
- Reviewer found P2 multi-day forecast labels without dates, compact map popups obscured by zoom controls, and selected infeasible plans lacking a distinct warning treatment. Added dates, removed compact-map zoom controls and shortened tooltip copy, and applied amber constraint warnings in Plan and Review. Updated mobile steps 3, 5, 6 and 8 are the correction evidence.
- Independent reviewer disposition: ship for the bounded review of those three findings; all three resolved. The reviewer accepted the full responsive shell, stacked mobile content, scrolling navigation and illustrative-data labels. No claim of an exhaustive independent review is made.

## Interaction and build verification

Area search and Kothrud selection update the chosen location and map. All eight steps navigate. Forecast 6/24/72-hour controls and playback work. Offline assistant sends a visible availability response. Zero action reductions give 48 → 48; maximum reductions give 48 → 12. Budget and required-action changes update plan notices, including Review. Evidence station/period/coverage controls change the example chart. Review JSON download was opened and its numbers checked. Dark theme was captured. All mobile steps have document scrollWidth 390 at innerWidth 390.

Production build, changed-file ESLint, 14 existing Vitest tests and four Sites worker checks pass. Hosting files are preserved. Vengeance component provenance and MIT license are recorded under `src/components/ui/`.

## Limits and follow-up

The initial frontend build used illustrative data. The subsequent backend integration replaces guided results with API outputs and explicitly retains offline examples only when the initial connection fails. Current data is CAMS modeled coverage; source proxies and intervention responses remain assumptions. Historical validation is separate from provider forecast validation. Changes are not deployed. State lasts during guided navigation and resets when the guide remounts or the page reloads. The map needs network access for OSM tiles.

The design detector flagged Inter as a common font; retained deliberately for the supplied design and project typography. No other detector findings were returned. Selections persist during guided navigation; durable storage across reloads remains future work.

---

# Connected dashboard verification

Historical report: the sections below record earlier prototype revisions.
For the current connected workflow use [verification](../docs/verification.md);
for current forecast evidence use [model card](../docs/model_card.md) and
[seasonal validation](../docs/evidence/seasonal_validation.md). Earlier statements
about pooled skill or provider testing do not describe every later revision.

Final result: passed for the local hackathon prototype on 27 September 2026.
Reference: user screenshot and existing Kombai layout. URL: http://127.0.0.1:5173/.

## Visual comparison

Preserved the reference header, peach intervention banner, 60/40 map and insights
layout, tabs, hatch cards, blue action, three sliders, ranked table and assumptions.
Reviewed the desktop capture against the reference and inspected the scenario panel.
Intentional differences: real provider names/readings, one tooltip, data-age warning,
compact replay/chat controls and numerically consistent backend scenario results.
The attached reference is not redistributed.

Evidence: ../docs/screenshots/dashboard-desktop.jpg and dashboard-laptop.jpg.
These show OBSERVED station baselines, MODELED grid/scenarios and SYNTHETIC population.
The capture service draws at half scale inside its canvas. Evidence crops blank
canvas and normalizes display scale; no numbers, labels or UI elements are edited.

## Browser evidence

- 1920×1080: document 1920×1080; no horizontal overflow; one map tooltip.
- 1366×768: document 1366×768; all four ranking rows visible; chat control moved
  into the header so it cannot cover the result table.
- 390px mobile: document width 390px; stacked panels; provider timestamp retained.
- All five tabs work. Forecast 24/72h selection returns backend projections.
- Backtest displays Bhosari's computed holdout metrics and quantile coverage.
- Sources display four proxy categories, separate from TreeSHAP in Forecast.
- Three zero-cut sliders plus Run scenario produce identical before/after values,
  zero ranges and zero exposure benefits for all actions.
- Keyboard grid selection works; 154 accessible map targets (144 cells + 10 stations).
- Historical replay loads the held-out 7 January 2026 snapshot with a dated banner;
  exiting restores the current cached dataset. Replay forecasts use pre-holdout models.
- Ask AirTwin returns a tagged template grounded in actual API outputs without an
  LLM key; Escape closes it. Optional external-provider behavior is not live-tested.
- Light/dark themes work. Final browser console contains no warnings or errors.

## Automated evidence and limits

20 backend tests, 11 frontend tests and 4 hosting tests pass. Production TypeScript
build and ESLint pass. Tests cover leakage, purged splits, SHAP reconstruction,
IDW, normalized shares, additive scenarios, contracts, replay and invalid LLM numbers.
Third-party Python/Node deprecation warnings do not represent failed checks.

The latest observed snapshot is 24 September 2026 at 22:00 IST. A visible warning
states that it is cached historical data. Pooled model skill trails persistence;
the generated model card reports the measured loss. No causal policy effect,
real population count, operational forecast skill or strong LLM semantic guarantee
is claimed. This report is scoped to the tested local prototype, not accessibility
certification or production readiness.

## Backend integration verification

FastAPI was initially stopped; it now runs on 127.0.0.1:8000 and the Vite `/backend` proxy serves its API. Verified health, 72-hour forecast, attribution and historical backtest through the frontend origin. Guided source shares and maps use returned backend values. A zero-cut scenario preserved the baseline; a zero-budget package selected no actions and correctly reported the target infeasible. Budget controls persist during guided navigation.

Ask AirTwin was tested both through `/api/explain` and the guided browser form. The actual `gemini-3.5-flash-lite` response returned `gemini_evidence_checked` with baseline/limitations evidence citations; the UI displays the provider and distinguishes a deterministic fallback summary from an AI response. Evidence: `docs/guided-evidence/connected-chat.png`.

Stopped and restarted FastAPI to verify the explicit offline banner and Refresh connection recovery. Evidence: `docs/guided-evidence/backend-offline.png`. Current provider snapshots are modeled and do not imply fresh monitor observations. PostgreSQL is optional and unconfigured; local snapshot persistence works without attempting database writes.

Validation: TypeScript/Vite build and ESLint passed; 15 frontend unit tests, four Sites packaging checks, and 25 backend API/state/planning tests passed. Gemini checks numeric and provenance consistency; they do not prove semantic or causal correctness.

The browser evidence check exposed an existing seasonal-baseline crash: station backtests return an empty baseline object. The chart now renders that optional metric only when present, with a regression test for the actual station benchmark shape.
