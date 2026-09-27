# Model card

## Status and intended use

**Not trained.** No LightGBM model, SHAP explanation or real station winter backtest
is shipped. The planned model forecasts PM2.5 for Pune/PCMC for exploratory urban
scenario comparison. It is not intended for clinical, regulatory or emergency use.

There are no measured real-world MAE, RMSE, R², improvement or calibrated interval
coverage values to report. The frontend's calculated synthetic demonstration
metrics must never be described as city forecast accuracy.

## Current demonstration

`frontend/src/mocks/engine.ts` creates deterministic synthetic history and a
sinusoidal future projection. The backtest predictor equals the same 24-hour
persistence baseline. Its seven-day synthetic sequence is chronological, but is
not the required winter holdout. Bounds are ±14 µg/m³ illustration, not trained
quantiles. Metrics are computed from the displayed pairs, rather than hardcoded.

## Planned target and training data

| Item | Planned specification | Current availability |
| --- | --- | --- |
| Indicator | PM2.5, µg/m³ | Pipeline/sample and frontend demo |
| AOI | Lat 18.45–18.80, lon 73.70–73.98 | Defined |
| Observed target | OpenAQ hourly station readings | Fetcher; real coverage unverified |
| Sparse fallback | CAMS modeled target, disclosed | Builder path implemented |
| Offline fixture | Synthetic sample | Committed; not real evaluation evidence |
| Weather | Issue-time-available horizon weather | Centroid reanalysis only; operational forecasts pending |
| Primary horizon | Direct 24-hour prediction | Not implemented |
| Optional horizons | 48/72 hours | UI demonstrations only |

## Feature and leakage plan

PM2.5 lags 1/2/3/6/12/24/48 hours; past-only rolling means/std at 6/24 hours;
hour/day/month with cyclical encodings; wind u/v, humidity, rain, stagnation and
winter indicators. Boundary-layer height is optional if available. Separate
features known at issue time from later realized weather.

Define issue timestamp and target timestamp explicitly. Build features per
station on a proper hourly time axis, so a gap is not confused with a one-hour
lag. Shift before rolling where needed. Split chronologically and exclude training
targets crossing the evaluation boundary. Fit encoders/imputers and seasonal
means on training data only. Archive weather availability must be documented;
retrospective reanalysis cannot silently masquerade as an operational forecast.

## Evaluation plan

1. Verify usable target dates and winter coverage before selecting a holdout.
2. Hold out the most recent available Nov–Jan interval; report exact dates.
3. Run TimeSeriesSplit inside training, with horizon-aware boundary separation.
4. Compare LightGBM with 24-hour persistence and training-only seasonal hourly mean.
5. Compute MAE, RMSE, R², improvement over persistence and p10–p90 coverage.
6. Report per-station results and sample counts, including model underperformance.
7. Generate metrics JSON and this model card from saved held-out predictions.

If CAMS/sample fallback lacks a winter period or observed targets, report the
limitation rather than calling that experiment an observed winter validation.

## Intervals and interpretation

The planned quantile models use alpha 0.1 and 0.9; evaluate empirical coverage
and interval order. Quantile labels alone do not guarantee calibration. SHAP
weather/temporal/persistence groups explain model feature contributions, not
traffic/industry/dust emission shares and not causal source effects.

## Limitations and release gate

Station sparsity, data gaps, synthetic fallback, centroid weather, approximate
spatial inputs and source-domain shifts limit usefulness. No public-health benefit
or emission-reduction accuracy has been measured. Before a trained release,
require reproducible training, generated metrics, provenance, leakage tests,
calibration disclosure and frontend/API integration evidence.
