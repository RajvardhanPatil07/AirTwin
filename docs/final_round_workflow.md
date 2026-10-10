# Live feed and final-round workflow

This build preserves the dashboard and integrates the observed-input forecast guard from `dev/mayuresh` (59e36da). It replaces the standalone simulated planner idea in `dev/parth2` (c61fe66) with backend package enumeration and historical spatial validation. The starting main revision was 001d539; existing local changes were retained.

## Run and reproduce

Use the existing setup in the README, then start both services:

```sh
python scripts/dev.py
```

The backend checks public providers every 900 seconds by default. The dashboard checks cached results every 30 seconds. A provider's measurement timestamp stays distinct from the retrieval timestamp. Keeping the backend process running is required; browser animation does not manufacture measurements.

With sourced historical observations already downloaded and processed, reproduce spatial evidence and test the running API:

```sh
.venv311/bin/python backend/scripts/train_resilience.py
.venv311/bin/python scripts/verify_live_workflow.py
```

Training requires the real processed dataset; the model binary and provider caches are ignored by Git. Deployment must provision these artifacts or regenerate them. Never load joblib files from untrusted sources. Existing deployment instructions still apply; this change has been verified locally, not published to a production host.

## What is live

`GET /api/feed` serves the public [IITM Pune station page](https://ews.tropmet.res.in/pune/index.php) indices. Eight nonzero stations had fresh provider timestamps during verification on October 10, 2026. These are observed, provider-published **AQI indices**, not measured PM2.5 concentrations. Zero placeholders are omitted. The HTML adapter fails visibly if the upstream format changes and retains the last cache with its original timestamps. Public accessibility does not establish redistribution rights; retain source attribution and confirm provider terms before public redistribution.

OpenAQ discovery succeeded with the configured credential, but newest Pune PM2.5 location updates were October 7. Fresh measured PM2.5 is therefore unavailable in this verification. CAMS via Open-Meteo supplies processed modeled concentration/weather context. [Open-Meteo documentation](https://open-meteo.com/en/docs/air-quality-api) describes a roughly 45 km global product: interpolated reference points do not become independent neighborhood sensors. AQI indices never enter PM2.5 target training or get converted into concentrations.

The live forecast dispatcher needs sufficient contiguous, recent observed concentration inputs and an eligible observed-target artifact; otherwise it labels the provider fallback and unavailable forecast uncertainty. Refreshing the UI cannot make delayed physical observations fresh.

## Demonstration

1. Inspect the live feed: source, indicator, measurement time, retrieval time and freshness. Inspect Forecast and Sources for separately labeled modeled concentrations and assumed traffic/industry/dust contributions.
2. Open Planner and load the evaluated sensor replay. With complete observations, compare the preferred budget-constrained 24-hour package and three feasible alternatives.
3. Set sensor loss to 25%, 50% or 75%. Remaining observed monitors drive the spatial forecast; unavailable readings cannot influence grid background. Forecast bands enter declared package stress cases.
4. Withhold Gavalinagar from replay inputs. Its readings were also excluded from fitting, calibration and development neighbor predictors. Compare the modeled 24-hour point and interval against its separately labeled later observed target.
5. Reduce the budget and mark an industrial action unavailable. Recompute the selection; inspect cost sensitivity, instability and infeasible target messaging. The package containing all eight actions displays budget, resource and availability violations.
6. Return to live mode. Packages from another snapshot/replay cannot remain on the current map. Same-snapshot previous results may remain during a control recalculation, explicitly marked outdated.

## Evidence and interpretation

[Historical evaluation](evidence/sensor_resilience.json) and paired predictions ([6 hours](evidence/sensor_resilience_predictions_6h.csv.gz), [24 hours](evidence/sensor_resilience_predictions_24h.csv.gz), [72 hours](evidence/sensor_resilience_predictions_72h.csv.gz)) record earlier fitting, separate calibration and later testing, seed, dates and exact paired IDW/persistence baselines. Three horizons (6/24/72 hours), four loss levels and all/withheld scopes yield 24 evaluation groups. When a monitor is unavailable, persistence is explicitly spatial persistence rather than unavailable own-monitor persistence.

At 24 hours and zero sensor loss, withheld-monitor MAE was about 5.23 µg/m³ versus IDW 5.58. High empirical interval coverage comes with wide bands; nominal bands are not guaranteed under temporal or spatial distribution shift. One withheld location does not independently validate every grid cell.

[Four API scenarios and live provenance](evidence/live_workflow.json.gz) record the actual requests and outputs. Costs, source activity, population weights and response factors remain synthetic or proxy assumptions. The objective maximizes the minimum population-weighted modeled reduction across 48 declared stress cases. Case stability is a sensitivity fraction, not a probability of policy success. Source shares are not causal measured source apportionment, and concentration reductions are not measured health outcomes.

Cost sensitivity re-filters all enumerated packages under a 20% cost increase. Benefit rankings stay unchanged because this perturbation changes costs only. Regional background is retained and uses the same forecast cutoff as the concentration baseline. No-action remains feasible at zero budget; a target can still be infeasible.

[Captured verification commands](evidence/verification.txt): 63 backend tests, 14 frontend tests, four Sites tests, lint, production build, documentation checks and all four API scenarios passed.

## Sole supported region

Pune–PCMC is now the only dashboard and API region. The statewide selector, scheduler and sample were removed. The bounded urban map includes Pune and PCMC reference locations; it does not claim exhaustive district or street-level monitoring.
