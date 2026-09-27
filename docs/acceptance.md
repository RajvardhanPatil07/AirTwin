# ENR-01 acceptance evidence

| Requirement | Implementation/evidence | Limits |
| --- | --- | --- |
| Forecast PM2.5 for defined urban area | LightGBM direct forecasts; AOI and station/cell selection | Forecast origin is data timestamp; stale observations are warned |
| ≥3 source categories | Traffic, industry, dust and background with YAML assumptions | Proxy hypotheses, not measured chemical shares |
| ≥3 interventions | Individual and additive combined packages, after-grid and ranking | Pass-through and population are assumptions |
| Hotspots and historical validation | IDW grid plus winter held-out model/persistence series | Read actual model card; model can lose to persistence |
| Separate observed/modeled/synthetic | Dataset fields, typed responses, badges, warnings and replay banner | Weather/population/targets have independent provenance |
| API + frontend end to end | FastAPI endpoints and existing dashboard adapter | Local runtime; no public production service |
| Offline mode | Sample fallback and automatically regenerated trained models | Synthetic metrics are not real-world accuracy; map tiles need internet |
| Reproducibility | run_all.sh, pinned dependencies, tests, generated card and CI | Raw downloads/model binaries remain ignored |

## Submission checks

- [ ] Confirm the latest CI run passes for the submitted commit.
- [ ] Verify source timestamp and stale-data notice before recording.
- [ ] Read actual held-out metrics, including negative improvements.
- [ ] Demonstrate zero cuts, individual and combined action consistency.
- [ ] Show forecast explanation separately from source hypotheses.
- [ ] Keep assumptions and synthetic population labeling in the video.
- [ ] Confirm team members and add final video link externally.

Safe presentation: “The system trains on available hourly targets, serves forecasts
and held-out evidence, and compares transparent proxy interventions. Data
freshness, model underperformance and synthetic population are explicitly shown.”

Unsupported claims: measured source percentages; causal policy effect; people
saved/protected counts; medically validated benefits; guaranteed forecast accuracy.
