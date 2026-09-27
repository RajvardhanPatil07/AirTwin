# HackMatrix 5.0 — Round 1 readiness

AirTwin's Round 1 goal is a **working Phase-1 prototype**, not a claim that the
full environmental digital twin is finished. The prototype should demonstrate the
complete decision loop while leaving clear technical depth for later rounds.

## Official Round 1 constraints

- Working prototype with at least 30–40% of the proposed solution demonstrable.
- Submit the official-template PPT, a video showing both the PPT and prototype,
  and a public GitHub repository.
- Do not add slides beyond the organizer-provided PPT template.
- Video duration: maximum 3 minutes.
- Submission window: 28 Sep 2026, 2:00 PM to 29 Sep 2026, 11:00 AM.
- Only the team leader submits through the same platform used for registration.
- GitHub commits should be meaningful, and every registered team member should
  contribute genuinely to the repository.

## Score-oriented readiness matrix

| Round 1 criterion | Points | AirTwin evidence now | Final pre-submission action |
| --- | ---: | --- | --- |
| GitHub Maintenance | 20 | Structured frontend/backend, CI, tests, issue/PR workflow, clean ignore rules, model/data docs | Make sure every registered member has a real contribution; close/triage Round-1 issues; verify exact submitted commit |
| UI/UX | 15 | Interactive city map, responsive dashboard, provenance badges, keyboard-accessible tabs, five-step judge journey | Final 1920×1080 QA; verify text is readable in screen recording |
| Tech Stack | 15 | React + TypeScript + Leaflet/Recharts, FastAPI, LightGBM, OpenAQ/Open-Meteo pipeline, optional Gemini explainer | Keep AI/ML central in PPT; do not let optional LLM distract from forecast model |
| Innovativeness | 10 | Moves from pollution monitoring to forecast + validation + source hypotheses + intervention simulation | Emphasize “from map to action,” not generic AQI monitoring |
| Problem Understanding & Solution Fit | 10 | Direct mapping to PM2.5 forecasting, ≥3 sources, ≥3 actions, hotspot map, historical validation, observed/modeled distinction | Keep ENR-01 acceptance table visible in README; explain assumptions |
| Documentation | 10 | README, model card, API, data report, assumptions, methodology, testing, demo and submission docs | Check every documented command/link on final commit |
| Presentation | 10 | Judge journey and timed storyboard | Use official PPT only; combine PPT + prototype in ≤3 minutes |
| Social Impact | 10 | Exposure-aware intervention comparison; SDG 3/11/13 framing | State intended planner/community benefit without claiming measured lives saved or causal health effects |

## What counts as the 30–40% Phase-1 prototype

The current competition prototype demonstrates:

1. **Observe** — PM2.5 baseline and hotspot map for Pune + PCMC.
2. **Predict** — ML PM2.5 forecasting using pollution history, time and weather.
3. **Validate** — chronological historical evaluation versus persistence/seasonal baselines.
4. **Explain** — transparent traffic, industry, dust and regional-background proxy shares.
5. **Act** — three intervention simulations plus a combined package and before/after grid.
6. **Provenance** — OBSERVED / MODELED / SYNTHETIC labeling throughout the demo.

That is the Round-1 vertical slice. It demonstrates every required ENR-01 idea
without claiming the finished city platform already exists.

## Proposed end-product scope

### Next 60%

- Sourced road-density and traffic-count layers instead of approximate traffic anchors.
- Verified industrial polygons / inventories and construction activity proxies.
- Licensed population raster instead of synthetic population weights.
- Better weather availability and interval calibration.
- Stable public deployment and data-refresh operations.

### Final product vision

- Higher-resolution city grid and multiple pollutants.
- Continuously refreshed environmental and mobility inputs.
- Robust uncertainty monitoring and drift detection.
- Historical policy replay and saved intervention portfolios.
- Planner-facing reports, alerts and APIs.
- Validation with city/domain stakeholders before operational use.

## The one sentence judges should remember

**AirTwin turns an air-quality map into an auditable decision simulator: it shows
what is happening, what may happen next, what may be contributing, and what
interventions could reduce modeled exposure.**
