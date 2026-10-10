# AirTwin-PCMC versus AIRTWIN-X

Reviewed 28 September 2026. Scope: public main-branch source and documentation; no competitor pipeline, tests, deployed interface, or user study was executed. Competitor numerical results are repository-reported, not independently reproduced. Local comparison uses AirTwin-PCMC documentation and the parent review of its implementation.

## Assessment

AIRTWIN-X is a serious competitor and currently has broader statistical research and more systematic experiment reporting. It is not demonstrably better overall: AirTwin-PCMC is closer to Pune/PCMC and provides a broader multi-action decision workflow and model serving. Both remain prototypes with substantial assumptions. No head-to-head accuracy claim is supported, and HackMatrix 5.0 participation was not organizer-confirmed.

| Dimension | Evidence and assessment |
|---|---|
| Problem fit | AirTwin-PCMC targets Pune/PCMC; AIRTWIN-X trains and evaluates on Delhi 2014–2020. Its own limitations disclaim external generalisation. AirTwin is closer to the stated municipal problem. |
| Research breadth | AIRTWIN-X reports five expanding chronological folds, persistence, eleven model families/baselines, temporal/weather/spatial ablations, conformal intervals, SHAP, spatial statistics, and a DiD policy analysis. This is a substantive strength. |
| Operational workflow | AirTwin has forecast serving and multiple intervention controls. AIRTWIN-X reads stored forecasts and replays historical data; its scenario repository deliberately ignores the requested traffic-reduction percentage when calculating the result and returns the historical DiD effect. Dose response is explicitly NOT ESTIMATED. |
| Visual ambition | AIRTWIN-X has a 3D view and Deck.gl maps. Buildings use illustrative massing, pollution surfaces use interpolation, and no controlled usability study establishes that 3D improves decisions. Neither project has demonstrated high-fidelity atmospheric physics. |
| Intervention validity | AIRTWIN-X has a more substantive empirical analysis, but its effect is null and unstable across treatment thresholds. AirTwin has broader controls, but source shares and fixed-weather linear responses are proxies rather than established causal effects. Neither can claim validated policy impact. |
| Forecast accuracy | AirTwin reports 24h MAE 20.01 versus persistence 21.81; AIRTWIN-X reports 38.41 versus 42.51. Different cities, observations, folds and aggregation make these unsuitable for ranking. |

## What the code substantiates

The [experiment runner](https://github.com/prakharagrawal191/AIRTWIN-X/blob/main/ml/experiment/runner.py) builds station-grouped future PM2.5 targets, uses the same usable observations for model/persistence comparisons, fits transforms inside train-only pipelines, writes predictions and run provenance, and records fold-level results. The [splitter](https://github.com/prakharagrawal191/AIRTWIN-X/blob/main/ml/splits/walk_forward.py) uses global timestamps and ordered train/embargo/calibration/embargo/test blocks. These are real safeguards, not README-only features.

The [conformal implementation](https://github.com/prakharagrawal191/AIRTWIN-X/blob/main/ml/uncertainty/conformal.py) calibrates absolute residuals on a separate calibration block and measures empirical coverage on test observations. Its reported best 24h model reaches 82.5% coverage against a nominal 90%, with mean width 123.8 µg/m³. Having uncertainty estimates is useful; their undercoverage prevents calling these reliably calibrated 90% operational intervals. [Reported results](https://github.com/prakharagrawal191/AIRTWIN-X/blob/main/docs/results.md)

The [intervention diagnostics](https://github.com/prakharagrawal191/AIRTWIN-X/blob/main/ml/intervention/diagnostics.py) invoke pre-trend, placebo and robustness checks and classify the causal status. The reported historical odd-even effect is +1.38% with interval −4.25% to +7.34%, p=0.6375; its sign changes across assignment thresholds. The repository appropriately labels it sensitivity only. This strengthens research honesty, not evidence of pollution reduction. [Results](https://github.com/prakharagrawal191/AIRTWIN-X/blob/main/docs/results.md), [scenario repository](https://github.com/prakharagrawal191/AIRTWIN-X/blob/main/backend/app/repositories/duckdb_repo.py)

## Material qualifications

1. **The headline winners are selected retrospectively.** The [results generator](https://github.com/prakharagrawal191/AIRTWIN-X/blob/main/scripts/21_generate_results.py) sorts fold-averaged test skill across experiment/model combinations and selects the best at each horizon. Those are useful benchmark winners; no independent holdout after this selection is demonstrated in this reviewed scope. Runner skill is an average of fold ratios, so headline skill need not equal one minus the ratio of headline average MAEs.
2. **Some protocol claims were corrected after the results.** The [methodology](https://github.com/prakharagrawal191/AIRTWIN-X/blob/main/docs/methodology.md) explicitly records on September 2 that hyperparameter grids were never searched, eleven models ran despite a narrower original plan, and MLP early stopping uses a randomly shuffled inner validation set. That stays inside training and does not imply external test leakage, but it limits blanket claims of frozen-protocol compliance.
3. **Data-quality flags are weaker than the intended policy.** Methodology §2.2 admits the gap detector checks newly inserted timestamps rather than existing empty cells; 32.9% of regularised concentration rows are NaN but all rows were flagged VALID. The runner excludes missing present/future PM2.5 from evaluation. This is a quality-metadata failure, not evidence of invented target observations. The range-flagging configuration/schema mismatch is also documented; PM2.5 has no recorded range violations.
4. **Documentation has drift.** [Limitations](https://github.com/prakharagrawal191/AIRTWIN-X/blob/main/docs/limitations.md) still marks clean raw re-download unverified while the later [research record](https://github.com/prakharagrawal191/AIRTWIN-X/blob/main/docs/research.md) reports a September 1 CPCB re-download check. Other old descriptions of the model list likewise differ from the corrected methodology. Assess the current code and dated corrections together.
5. **Breadth is not deployment evidence.** The project explicitly disclaims live ingestion, generalisation beyond Delhi, causal scenario effects, algorithmic novelty, high-fidelity physics and a controlled interpretability study. [Limitations](https://github.com/prakharagrawal191/AIRTWIN-X/blob/main/docs/limitations.md)

## What AirTwin should improve

Prioritise repeated chronological evaluation with fold-level and seasonal results, empirical interval coverage, measured feature ablations, and a compact disclosure of synthetic/proxy inputs. Preserve AirTwin’s local problem fit and working multi-action workflow, while making clear that its scenario outcomes are assumptions until independently validated. Compare both models only after running them on the same station data, horizons, cutoff dates and baseline.
