# Synthetic population sensitivity

Snapshot: 2026-09-24T22:00:00+05:30.
Dataset fingerprint: `cd3b2dcfa09df604a3150978dd356b81d1af450ab0bbb8f480d53f20727b0600`.
Cuts: traffic 20%, industry 30%, dust 30%.

| Population assumption | Leading individual action | Traffic index | Industry index | Dust index |
| --- | --- | --- | --- | --- |
| configured_synthetic | industry | 310673 | 351292 | 329496 |
| uniform_synthetic | industry | 306244 | 339277 | 330574 |
| edge_weighted_synthetic | industry | 299728 | 335245 | 327856 |

Index units: synthetic person·µg/m³. These are comparative weights, not people protected.
Uniform assigns equal weight to each cell. Edge-weighted uses inverse configured population, then rescales to the same total.
Leading action changed across these profiles: False.
Agreement across three profiles does not establish robustness to every population distribution.

Fixed meteorology, geometry, source proxies and cuts. All three population profiles are hypothetical, normalized to the same synthetic total. No demographic, causal or health validation.
