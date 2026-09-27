# Connected dashboard verification

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

## Maharashtra extension — 27 September 2026

Preserved the existing layout, typography and scenario controls. Tested the live
state view at 1920×1080, 1366×768 and 390×844. Region selection, additional pollutant
readings, scenario response, statewide validation-unavailable card and PCMC measured
backtest were checked. Horizontal document overflow was zero at the two smaller
sizes; the map had one tooltip. Modeled reference markers are translucent/dashed.
Gemini no-key error appeared visibly with no canned answer. Real LLM success remains
unverified until a Gemini key is configured. Responsive map bounds refit on resize.
