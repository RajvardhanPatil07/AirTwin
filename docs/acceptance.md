# ENR-01 acceptance and evidence checklist

This checklist separates implemented capability from evidence that still depends
on real provider coverage.

| Requirement | Current evidence | Remaining evidence gap |
| --- | --- | --- |
| Forecast at least one air indicator | Runtime PM2.5 HistGradientBoosting model + 24/48/72 recursive serving | Run on adequate observed history before claiming city accuracy |
| Defined urban area | Pune/PCMC AOI bounding box and station coordinates | Verify all production coordinates/providers |
| ≥3 source categories | Backend traffic, industry, dust + regional background proxy shares | Replace anchors/proxies with sourced road/industry/construction inputs |
| ≥3 actions | Backend traffic restriction, industrial controls, dust suppression + combined package | Validate pass-through assumptions with domain evidence |
| Hotspot map | Backend 12×12 IDW grid with MODELED provenance | Denser observed monitoring would improve representativeness |
| Historical validation | Chronological final-20% holdout + persistence baseline + computed metrics | Observed winter holdout when coverage permits |
| Observed vs modeled distinction | Provenance carried through stations, grids, forecast, backtest and scenarios | Keep this invariant for future features |
| End-to-end backend + frontend | FastAPI contract implemented; frontend adapter already compatible | Run UI with `VITE_API_BASE_URL` and capture submission evidence |
| Offline sample | Committed sub-1 MB synthetic CSV | Never present it as observed evidence |
| Clean repository | Ignore rules + split CI for pipeline/backend/frontend | Keep generated models/data out of Git |

## Required completion evidence before strong real-world claims

- [ ] Document exact observed target provider, sensors, dates, gaps and units.
- [x] Implement reproducible runtime training without committing model binaries.
- [x] Compute held-out metrics and persistence comparison in code.
- [x] Implement API responses for forecast, backtest, attribution, hotspots and scenarios.
- [x] Test source shares, zero-cut behavior, combined actions and API provenance.
- [ ] Run the live pipeline and record observed-data metrics (including poor results).
- [ ] Capture updated screenshots/video with backend provenance and date visible.
- [ ] Replace approximate source anchors with sourced spatial proxy layers if time permits.

## Presentation claim that is safe now

“AirTwin has an end-to-end executable forecasting and scenario backend. The model
uses chronological validation and compares against persistence. The repository
ships a synthetic fallback for reproducibility, so observed city accuracy is only
claimed after running the live provider pipeline and inspecting its provenance.”

Still unsupported without additional evidence: measured industrial source
percentages, causal policy benefits, a specific number of people protected,
regulatory-grade accuracy, or guaranteed health outcomes.
