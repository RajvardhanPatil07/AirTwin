# Planning behavior and evidence

The planner compares 24-hour scenarios for Pune and PCMC. Results are population-weighted reductions over the modeled city grid. They are not measured policy impacts.

## Baseline and replay

The planning baseline shows the original measurement timestamp, age at the forecast issue and current wall-clock age, eligible observed PM2.5 monitors, modeled references, discovered sensors and coverage limitations. Observations more than three hours old are not eligible for spatial forecasting. Future timestamps are rejected. Stored observations retain their dates and cannot masquerade as a live snapshot.

With insufficient eligible observed inputs or no eligible spatial artifact, the planner uses the provider forecast when available and labels CAMS explicitly. A snapshot without a forecast is labeled snapshot interpolation. Historical replay evaluates freshness at the historical issue time; it remains labeled historical replay. The guided replay uses the documented observed dataset and excludes the withheld monitor from predictors. Its later observed target is displayed only as a retrospective check.

## Selecting a forecaster

An observed station with enough complete hourly history compares 24-hour LightGBM and persistence on separate chronological fit, selection and test periods. Fit targets precede selection origins; selection targets precede test origins. Lower selection MAE chooses the method, with ties retaining persistence. The untouched later test reports both candidates and the selected method by represented season. A short history cannot validate missing seasons or other stations. Intermediate hourly values are interpolation, not separately tested horizons.

The spatial artifact similarly separates fitting, method selection, interval calibration and later testing, with a monitor withheld from fitting and selection. It compares LightGBM with spatial persistence at each horizon and simulated sensor-loss level. The evidence table reports actual monitor/season groups rather than claiming universal accuracy. Its benchmark does not validate today's CAMS forecast. The legacy pooled observed-model serving path retains persistence if its horizon benchmark does not beat persistence; this historical serving gate is not an independent test of its own selected performance.

Rebuild the local spatial artifact after deployment or when the observed dataset changes:

```sh
.venv311/bin/python backend/scripts/train_resilience.py
```

The trusted local model file is generated under `backend/models` and is ignored by Git. The versioned report and predictions under `docs/evidence` record the evaluated run.

## Package decisions

The planner enumerates operationally feasible packages, then applies the budget. Users can select maximum central modeled benefit, lowest spending meeting the central target, or strongest minimum benefit in the declared conditional operating stress cases. An infeasible target has no cheapest qualifying package. The selected package drives its displayed before/after grid and cost sensitivity.

The full response envelope includes zero effect and is an assumed sensitivity range, not a confidence interval. Conditional operating stress ranking assumes actions operate and must not be interpreted as a guaranteed benefit. Forecast bands and intervention responses are separate sources of uncertainty.

The explanation reconciles source-category contributions, population-weighted background and local excess, the budget-constrained maximum, and the maximum with only the budget removed. Operational limits remain. When a target is reachable at a larger budget, the planner reports the actual minimum package cost. Otherwise it explains why increased spending alone cannot reach it.

## Evidence still required

See [the intervention evidence register](evidence/planning_intervention_sources.md) and `config/interventions-evidence.json`. Official local documents support action rationale and operational prerequisites, but do not establish comparable daily municipal action costs or causal neighborhood PM2.5 responses. Documented unit costs therefore remain null. Existing scenario costs and response parameters remain explicitly assumed; no city program budget, bank guarantee or bundled capital expense was converted into a daily action price.

Replace these inputs only with matching BOQs, awarded service rates or scoped quotations, and measured pilots or suitable controlled local intervention studies. Duration, distance-decay radius, source shares and implementation limits also need empirical calibration. Current observed coverage and represented historical seasons limit the claims that can be made.

## Verification

Backend regression tests check package choice, target feasibility, minimum budget, category reconciliation, zero-effect response ranges, chronology and leakage boundaries, stale/future observations, and persistence serving when ML loses or lacks a benchmark. Frontend tests and the production TypeScript build verify integration. Browser checks cover current provider mode, observed replay, feasible/infeasible targets, selection changes and the forecast evidence view.

```sh
cd backend
../.venv311/bin/python -m pytest -q
```

```sh
cd frontend
npm test -- --run
npm run build
```
