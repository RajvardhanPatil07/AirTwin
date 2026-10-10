# Implementation status and remaining roadmap

## Completed core path

- [x] OpenAQ station discovery, paginated hourly downloads and failure fallback.
- [x] Historical weather, live forecast context and archived 24/48/72-hour weather.
- [x] Hourly cleaning, explicit provenance, ignored Parquet and small offline sample.
- [x] Gap-aware lag/rolling/cyclical/wind/stagnation features without future target leakage.
- [x] Direct LightGBM models and quantile bounds for 1–24, 48 and 72 hours.
- [x] Winter holdout when available, purged TimeSeriesSplit and both baselines.
- [x] Computed metrics, per-sensor underperformance and generated model card.
- [x] FastAPI contract with health, stations, forecasts, backtests, hotspots and attribution.
- [x] Centralized YAML assumptions, IDW and wind-aware proxy source weights.
- [x] Three additive interventions, combined package and population-weighted ranking with source labels.
- [x] Bundled PCMC WorldPop 2020 modeled counts and selected OSM geometry; synthetic fallback retained.
- [x] Paired seasonal feature/model experiments, disjoint calibration and an exploratory station Local Moran report.
- [x] Existing frontend connected without redesign; mock fallback retained.
- [x] Exact TreeSHAP groups displayed separately from proxy source shares.
- [x] Grounded explanation endpoint and matching chat drawer; Gemini-only responses with explicit no-key errors.
- [x] Historical replay with date banner and pre-holdout forecast model.
- [x] Backend/math/API tests, frontend checks and CI offline training.

Completion means implementation exists; validation evidence is in model_card.md,
testing.md and the latest CI run. It does not mean the model outperforms persistence
at every station or that source-share hypotheses have been chemically validated.

## Remaining limitations and improvements

- [ ] Improve forecast skill using training/CV decisions; retain a new untouched
  evaluation period when selecting revised models after viewing current holdout.
- [ ] Evaluate station-specific models, larger historical coverage and source-domain shifts.
- [ ] Compare genuinely issue-time station/weather availability with provider publication delays.
- [ ] Train every 25–71-hour horizon independently instead of interpolating anchors.
- [ ] Prospectively verify interval coverage by station/season on a new uninspected period.
- [ ] Verify local road and industrial inventory completeness and measure emissions/activity; OSM geometry alone is insufficient.
- [ ] Replace dated WorldPop 2020 modeled counts with newer locally validated population evidence when available.
- [ ] Ground optional LLM answers with stronger claim verification beyond numeric/tag checks.
- [ ] Test a configured LLM provider; this build verifies the no-key path only.
- [ ] Add confirmed team names, final video link and optional public deployment.
- [ ] Additional pollutants, richer spatial rendering and validated alerting for Round 2.

BLH is optional and currently missing. Reanalysis still supplies issue-time weather
covariates retrospectively; this limitation is disclosed. Provider data freshness
is controlled by the source, not by how recently the fetch script was run.
