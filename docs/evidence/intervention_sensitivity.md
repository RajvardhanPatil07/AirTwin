# Intervention ranking stress test

Snapshot: 2026-09-24T22:00:00+05:30.
Dataset fingerprint: `cd3b2dcfa09df604a3150978dd356b81d1af450ab0bbb8f480d53f20727b0600`.

| Cuts | Assumption range | Central leader | Cases | Winners (counts, not probabilities) | Changed |
| --- | --- | --- | --- | --- | --- |
| demo | configured_range | industry | 2187 | {'industry': 2142, 'traffic': 45} | True |
| demo | wide_stress | industry | 2187 | {'tie_or_zero': 81, 'dust': 204, 'industry': 1309, 'traffic': 593} | True |
| equal_cuts | configured_range | industry | 2187 | {'industry': 1773, 'traffic': 414} | True |
| equal_cuts | wide_stress | industry | 2187 | {'tie_or_zero': 81, 'dust': 175, 'industry': 1130, 'traffic': 801} | True |

## Interpretation

A ranking change provides a concrete counterexample to a universal winner claim.
No change establishes agreement only on this finite grid of assumptions.
The JSON records an example parameter combination for every winner or tie.

- Ranges are assumed stress tests, not empirically sourced response coefficients or confidence intervals.
- Configured-range testing varies each source and response independently; existing UI bounds use aggregate scaling.
- Winner counts describe an arbitrary finite grid, not probabilities of policy success.
- Scores cover the Pune-PCMC grid; selecting Bhosari does not make them Bhosari-only benefits.
- Geometry, meteorology and background are fixed. Equal cuts do not imply equal cost or feasibility.
- No causal concentration reduction, demographic count or health benefit is validated.

Category evidence and parameter status: [intervention evidence](../intervention_evidence.md).
