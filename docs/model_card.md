# Model card

## Status and intended use

**Executable prototype model.** `backend/app/services/forecasting.py` trains a
scikit-learn `HistGradientBoostingRegressor` at runtime from the processed dataset
(or the committed synthetic sample when no processed data exists). The model
forecasts PM2.5 for exploratory AirTwin scenario comparison. It is not intended
for clinical, regulatory or emergency use.

The repository still does **not** claim measured city-level accuracy by default.
The committed fallback target is synthetic; observed validation is only possible
after the live pipeline produces adequate observed station history.

## Implemented forecast

- Target: next-hour PM2.5.
- Features: current PM2.5, 1/3/24-hour lags, 6/24-hour rolling means, calendar
  cycles and weather available at issue time.
- Missing hours are reindexed as gaps so row adjacency cannot masquerade as a
  one-hour lag.
- Validation: final 20% of usable rows held out chronologically (bounded to 48
  hours–14 days when coverage permits); no shuffled split.
- Baseline: one-hour persistence (`y[t+1] = y[t]`).
- Metrics: MAE, RMSE, R², improvement over persistence, empirical interval coverage.
- 24/48/72-hour UI forecasts: recursive one-hour rollout.
- Future weather assumption: latest available weather is held constant.
- Interval: training-residual p10/p90 diagnostic band; not a calibrated regulatory
  confidence interval.

## Provenance behavior

Model output is always `MODELED`. Historical targets keep the dataset source type:
`OBSERVED`, `MODELED` or `SYNTHETIC`. A CAMS fallback therefore never becomes an
observed target, and the committed fixture never becomes evidence of real skill.

## Leakage controls

Features are built on a regular hourly index. PM2.5 lags and rolling windows contain
only values available at forecast issue time, and the target is shifted to the next
hour. The chronological test period is never shuffled into training. Current
weather can be used for next-hour prediction; retrospective reanalysis is not
silently treated as archived future-weather forecasts.

## Limitations / next evidence gate

A stronger submission should still document exact live station coverage, validate
on a sufficiently long observed winter period when available, compare multiple
seasonal baselines, and replace held-constant future weather with archived or
operational weather forecasts. Source-proxy attribution is separate from model
feature importance and must not be described as causal source apportionment.
