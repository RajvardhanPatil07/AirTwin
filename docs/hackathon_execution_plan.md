# AirTwin hackathon execution plan

This plan is aligned to HackMatrix 5.0 Round 1. The objective is a compelling
**Phase-1 prototype** with enough of the final vision implemented to demonstrate
the complete ENR-01 loop, without pretending the end product is finished.

## Round 1 objective

The official evaluation heavily rewards repository quality, UI/UX and technical
implementation. AirTwin should therefore optimize for **trustworthy evidence +
clear product flow**, not another last-minute feature.

The product story is:

1. **Observe** — where is PM2.5 high?
2. **Predict** — what may happen next?
3. **Validate** — how did the model behave on historical held-out data?
4. **Explain** — which local source proxies may contribute?
5. **Act** — how do three intervention options change modeled pollution?

The frontend exposes this as a five-card judge journey.

## Current Phase-1 prototype

Already demonstrable:

- Pune + PCMC city-first dashboard.
- PM2.5 hotspot grid and selectable locations.
- ML forecasting with weather/time/history features.
- Historical backtest and baseline comparison.
- Traffic, industry, dust and regional-background source hypotheses.
- Traffic restriction, industrial control and dust-suppression scenarios.
- Before/after grid and exposure-weighted comparison.
- OBSERVED / MODELED / SYNTHETIC provenance.
- Responsive UI, tests, CI and reproducible startup.
- Optional historical replay, Maharashtra context and grounded explainer.

For Round 1, this should be presented as the implemented vertical slice of a larger
operational twin, not as the final municipal platform.

## Priority until submission

### P0 — score protection

1. Verify all registered members are collaborators and have **genuine commits**.
2. Keep repository free of ZIPs, videos, binaries and generated build output.
3. Run the complete CI/local checks on the exact submitted commit.
4. Verify README commands and public repository access.
5. Finish the official PPT **without adding slides**.
6. Record the combined PPT + prototype video under 3 minutes.
7. Verify the Drive folder and public sharing before the deadline.

### P1 — evidence quality

Only if P0 is safe:

- Refresh usable observed Pune/PCMC data.
- Regenerate model/data reports.
- Verify Bhosari plus one second location for the recording path.
- Fix any visible stale-data/provenance mismatch.
- Make one real UI polish improvement if something is hard to read at 1080p.

### P2 — do not chase before Round 1

Do not spend submission time on authentication, mobile apps, 3D city rendering,
blockchain, additional pollutants, notification systems, or another AI feature.
They add scope without improving the current judging evidence.

## After Round 1 selection

Focus on the official final-round requirement: a working end product with deeper
AI/ML integration. Priorities:

- sourced traffic/road network inputs;
- verified industrial/construction layers;
- licensed population data;
- calibrated uncertainty and stronger held-out evaluation;
- production-style data refresh/deployment;
- multi-pollutant expansion only after PM2.5 remains reliable.

See [Round 1 readiness](round1_readiness.md) and
[submission checklist](submission_checklist.md).
