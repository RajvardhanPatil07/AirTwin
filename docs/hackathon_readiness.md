# Hackathon improvements and remaining evidence

## Completed locally

- Independent source/response/population stress tests: 8,748 parameter combinations across demo and equal-cut cases. The leader changes even in the configured-range test. Counts describe a finite assumed grid, not probabilities.
- Regional category evidence and explicit parameter provenance: published reports support categories; local shares and response coefficients remain uncalibrated assumptions.
- Forecast challenger: purged fitting, a separate recent selection block and a disjoint calibration block, compared on 24 seasonal cases.
- Bhosari industrial-controls versus dust-suppression demo, planned for 2:45. Submission checklist corrected to the official 3-minute limit.
- Fifteen-minute user session instructions and a blank record. No participant results have been fabricated.
- Automated regression tests and offline CI smoke commands for the new evaluation tools.
- Paired 6/24/72-hour ablations and interval comparisons, with deterministic local reproduction; sourced PCMC WorldPop/OSM input and an exploratory station Local Moran report.

## Forecast decision

**Reject promotion of this challenger.** It improves MAE in only 2 of 24 cases.
Cases with at least 80% interval coverage increase from 9 to 10, but the worst
coverage is still 60.6%. Two challenger cases lose to persistence. In the delayed
October 2025 24-hour case, MAE worsens from 18.71 to 19.03 µg/m³; persistence is
18.44. More conservative selection does not prevent future seasonal shifts.

The serving model and its generated card remain unchanged. Existing seasonal
weaknesses remain visible. These windows were inspected before development;
they are development evidence, not a new blind evaluation. A future promotion
requires a protocol fixed before collecting a new test period, issue-time data
availability, and assessment of error and band width as well as coverage.

## User session status

**Founder self-test invited; actual responses pending.** Conduct the prepared session, record actual task
outcomes, implement relevant observed fixes and perform a retest. Materials alone
do not establish user relevance or endorsement. No external messages were sent.

## Verification

Local backend suite: **44 passed**, with one existing Starlette/AnyIO deprecation
warning. Observed-data forecast and intervention reports were generated using the
available dataset ending 24 September 2026. This does not establish fresh live
observations, operational forecast accuracy or causal intervention effects.

Local documentation links, tracked-file hygiene and whitespace checks passed.
New offline CI commands were exercised locally; remote CI is not claimed.
Small source-label changes passed lint, build and frontend tests. The live PCMC
dashboard and mapped-zones label were checked in the browser at narrow width;
this was not a full accessibility audit.

## Evidence links

- [Forecast challenger](evidence/forecast_challenger.md)
- [Intervention results](evidence/intervention_sensitivity.md)
- [Category evidence and assumptions](intervention_evidence.md)
- [Focused demo](demo.md)
- [User feedback kit](user_feedback.md)
- [Blank feedback record](user_feedback_record.md)
- [Paired experiment protocol](experiments_protocol.md)
- [Spatial source provenance](spatial_sources.md)
- [Station Local Moran report](evidence/station_local_moran.md)
