# Forecast evidence and reproduction

The serving model card and the seasonal evaluation answer different questions.
[Model card](model_card.md) describes the deployed model's winter holdout.
[Seasonal results](evidence/seasonal_validation.md) evaluate separately fitted
models across complete calendar seasons at 6, 24 and 72 hours. Exact feature lists,
provenance, train/test boundaries and dataset fingerprints accompany the results
in [JSON](evidence/seasonal_validation.json).

## Reproduce

After installing the backend requirements and building the processed dataset:

```sh
python backend/scripts/validate_forecasts.py
python backend/scripts/validate_forecasts.py --policies pollution_only --latency-hours 6 --output docs/evidence/delay_6h.json
python scripts/validate_population.py --url http://127.0.0.1:8000
```

The population check needs a running PCMC API. Forecast validation never writes
serving model binaries or overwrites the model card. Raw environmental downloads
remain ignored. A fingerprint establishes which bytes were used; it does not
make those data available to another person. Re-fetching providers may change
coverage and results. Exact observed-run reproduction requires the same dataset
and exogenous inputs, shared separately subject to their provider terms.

`--offline` evaluates synthetic inputs only. The short committed sample cannot
establish multiple-season observational skill. No complete windows results in an
empty report with an explicit warning, not fabricated metrics.

## Input availability

- Retrospective uses existing features, including archived CAMS and reanalysis.
  These inputs do not reproduce historical long-lead availability or publication delays.
- Pollution-only removes all weather, CAMS and boundary-layer features. PM2.5
  observations become usable one hour after their valid time by default. Targets
  retain their original timestamps. The delay is a scenario assumption, not a
  measured OpenAQ service guarantee.
- Training targets end strictly before the first test issue time. Blend weights
  and bands are selected on purged rolling-origin training folds, never the holdout.
- Persistence uses the same available reading as the evaluated model. The hourly
  mean baseline uses only training targets. Missing hourly targets are not filled.

Only complete calendar windows are eligible; this dataset excludes partial summer
2025 and monsoon 2026. Missing sensor hours still reduce valid evaluation pairs.
The reported evidence spans four windows, not multiple independent years for each
season. Models are refitted for each window; later training may include earlier
evaluation periods, as in an expanding chronological backtest.

## Findings from the recorded observed run

The delayed pollution-only 24-hour October 2025 evaluation loses to persistence
by 1.4%. Winter 24-hour skill is +6.3%; summer 2026 is +10.0%. Its 72-hour October
band coverage is 59.3%, below the nominal 80% target. Do not present these bands
as reliably calibrated across all seasons. The ablation also changes available
rows, so differences between policies cannot be attributed solely to covariates.

Next experiments should measure actual sensor/provider publication lag, capture
issue-time forecast vintages, diagnose episode errors and evaluate interval
calibration on a separate chronological calibration window. These remain open
research work, not completed operational validation.

## Intervention evidence

[Population sensitivity](evidence/population_sensitivity.md) compares configured,
uniform and inverse-density synthetic profiles at the same total weight. It tests
whether a central ranking changes under those profiles. Pass-through/source
sensitivity is already shown in API/UI assumption bounds. No profile is census
data; no result establishes a causal concentration reduction or health benefit.
