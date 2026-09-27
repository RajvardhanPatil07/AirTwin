# ENR-01 acceptance and evidence checklist

This checklist distinguishes available demonstration behavior from required real
system evidence. Read it before making submission claims.

| Requirement | Current evidence | Verdict for full requirement |
| --- | --- | --- |
| Forecast at least one air indicator | PM2.5 UI and illustrative daily-cycle projection | Pending real forecast model |
| Defined urban area | Bounding box and six approximate Pune/PCMC locations | Defined, coordinates need verification |
| ≥3 source categories | Demo traffic/industry/dust/background shares and assumptions | Demo available; real proxy inputs pending |
| ≥3 actions | Traffic restriction, industry controls, dust suppression; combined package | Demo engine works |
| Hotspot map | 144 IDW-derived modeled cells, selectable locations, provenance styling | Demo available |
| Historical test validation | Synthetic seven-day persistence predictor and computed metrics | Pending real winter holdout |
| Observed vs modeled distinction | Source types, badges, synthetic warnings, no invented observed readings | Present in current demo/pipeline |
| End-to-end backend + frontend | API adapter exists, server does not | Pending |
| Offline sample | Committed sub-1 MB CSV and independent frontend fixtures | Present; basemap tiles still need network |
| Clean repository | Ignore rules and tracked-file hygiene CI | Automated check available |

## Required completion evidence

- [ ] Document exact target provider and station coverage.
- [ ] Commit scripts to regenerate a model; do not commit its binary.
- [ ] Generate metrics and model card from held-out predictions.
- [ ] Record persistence comparison, including negative improvement if applicable.
- [ ] Demonstrate real API responses powering all linked scenario displays.
- [ ] Confirm source shares sum to one and combined equals individual sums.
- [ ] Verify source badges in every chart, map layer and tooltip.
- [ ] Test API outage and missing-data behavior.
- [ ] Capture updated screenshots with provenance/date intact.
- [ ] Record the submission demo and keep video out of Git.

## Presentation claims that are safe now

“We have built an interactive, transparent simulation demo and an ingestion
pipeline. Current dashboard inputs are synthetic. The next milestone is a trained
24-hour forecast and real held-out validation.”

Claims that are not supported now: real forecast accuracy; measured industrial
source percentages; causal policy benefits; a specific number of people protected;
a complete digital twin; guaranteed regulatory or health usefulness.
