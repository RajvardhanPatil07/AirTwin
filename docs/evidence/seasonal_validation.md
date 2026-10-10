# Seasonal forecast validation

Dataset: 2025-03-27T16:00:00+05:30 to 2026-09-24T22:00:00+05:30.
Fingerprint: `cd3b2dcfa09df604a3150978dd356b81d1af450ab0bbb8f480d53f20727b0600`.

Pollution-only assumes 1 hour(s) of sensor publication delay.
Errors are µg/m³; positive skill means lower MAE than persistence.

| Inputs | Season | Horizon | Train / test pairs | MAE | RMSE | Persistence MAE | Hourly mean MAE | Skill | Band coverage |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| retrospective | monsoon_2025 | 6h | 9993 / 17525 | 5.91 | 16.00 | 7.32 | 20.96 | +19.2% | 71.1% |
| retrospective | post_monsoon_2025 | 6h | 27494 / 4866 | 13.02 | 39.61 | 15.05 | 32.98 | +13.5% | 74.7% |
| retrospective | winter_2025 | 6h | 32389 / 10135 | 24.56 | 37.30 | 32.53 | 53.24 | +24.5% | 81.1% |
| retrospective | summer_2026 | 6h | 45190 / 9513 | 10.44 | 21.62 | 15.94 | 17.95 | +34.5% | 82.1% |
| retrospective | monsoon_2025 | 24h | 9147 / 16750 | 6.98 | 22.30 | 7.80 | 22.52 | +10.5% | 72.2% |
| retrospective | post_monsoon_2025 | 24h | 25962 / 4700 | 17.39 | 56.65 | 17.65 | 35.18 | +1.5% | 77.3% |
| retrospective | winter_2025 | 24h | 30535 / 9640 | 20.01 | 31.27 | 21.81 | 52.51 | +8.2% | 90.3% |
| retrospective | summer_2026 | 24h | 42378 / 9279 | 11.53 | 24.04 | 12.79 | 18.43 | +9.9% | 78.7% |
| retrospective | monsoon_2025 | 72h | 8531 / 16537 | 9.22 | 30.47 | 10.03 | 20.11 | +8.0% | 65.2% |
| retrospective | post_monsoon_2025 | 72h | 24922 / 4515 | 25.22 | 66.68 | 28.15 | 32.92 | +10.4% | 62.7% |
| retrospective | winter_2025 | 72h | 29531 / 8981 | 25.09 | 36.75 | 29.19 | 54.88 | +14.0% | 89.2% |
| retrospective | summer_2026 | 72h | 40023 / 9261 | 13.17 | 25.55 | 15.88 | 18.41 | +17.1% | 80.1% |
| pollution_only | monsoon_2025 | 6h | 9932 / 17457 | 6.21 | 16.99 | 7.59 | 21.08 | +18.1% | 73.3% |
| pollution_only | post_monsoon_2025 | 6h | 27362 / 4851 | 13.38 | 36.91 | 15.69 | 33.13 | +14.7% | 73.1% |
| pollution_only | winter_2025 | 6h | 32245 / 10106 | 26.05 | 37.25 | 34.68 | 53.05 | +24.9% | 80.4% |
| pollution_only | summer_2026 | 6h | 44990 / 9491 | 10.95 | 21.87 | 16.31 | 17.82 | +32.9% | 81.5% |
| pollution_only | monsoon_2025 | 24h | 9130 / 16734 | 7.34 | 23.43 | 7.94 | 22.58 | +7.5% | 74.1% |
| pollution_only | post_monsoon_2025 | 24h | 25939 / 4693 | 18.71 | 57.06 | 18.44 | 35.12 | -1.4% | 73.6% |
| pollution_only | winter_2025 | 24h | 30495 / 9622 | 21.89 | 32.56 | 23.36 | 52.78 | +6.3% | 89.0% |
| pollution_only | summer_2026 | 24h | 42305 / 9253 | 12.10 | 24.80 | 13.45 | 18.44 | +10.0% | 78.5% |
| pollution_only | monsoon_2025 | 72h | 8547 / 16513 | 9.55 | 34.00 | 10.13 | 20.25 | +5.8% | 75.8% |
| pollution_only | post_monsoon_2025 | 72h | 24914 / 4528 | 27.64 | 67.61 | 28.46 | 32.58 | +2.9% | 59.3% |
| pollution_only | winter_2025 | 72h | 29535 / 8977 | 28.17 | 39.70 | 30.11 | 55.00 | +6.4% | 87.3% |
| pollution_only | summer_2026 | 72h | 40027 / 9274 | 14.66 | 27.60 | 16.32 | 18.42 | +10.2% | 79.2% |

## Interpretation and limits

- Retrospective inputs retain archived CAMS and reanalysis availability limitations.
- Pollution-only excludes all weather, CAMS and boundary-layer inputs; sensor publication delay is assumed, not verified.
- These are separately refitted evaluation models, not the serving-model metrics.
- Seasonal mean means a training-only target-hour average, not a climatology fitted to multiple years.
- Missing targets are not imputed; sparse valid pairs may underrepresent difficult hours.
- No causal intervention, health benefit or statewide accuracy is established.

## Skipped evaluations


Exact boundaries, input features, provenance and results are in the adjacent JSON file.
A failed baseline comparison remains a reported result; it is not removed from this table.
