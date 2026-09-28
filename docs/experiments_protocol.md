# Paired forecast development experiments

The [full report](evidence/paired_experiments.md) and [machine-readable evidence](evidence/paired_experiments.json)
compare persistence, hourly mean, LightGBM, a selection-fold LightGBM/persistence
blend, and histogram gradient boosting. Each policy/season/horizon uses the same
test station-hour rows for each model and feature arm; `test_row_fingerprint`
records that identity. Models are trained once per arm on the same fit block.

The fixed chronological sequence is fit → blend-weight selection → residual
calibration → test, with a 48-hour history embargo between blocks. The
history/weather/weather+CAMS feature arms are predictive ablations. CAMS is
the final addition; weather and CAMS are not measured source contributions.
Pollution-only is a separate one-hour sensor-latency assumption and cannot be
compared directly with retrospective weather/CAMS as an arm on identical rows.

Two intervals are evaluated on the same disjoint calibration block: an
empirical signed-log-residual interval and a symmetric absolute-log-residual
split-conformal interval with finite-order statistic. Both target 80% nominal
coverage. The conformal interval has **no unconditional prospective coverage
guarantee here**, because hourly targets overlap and conditions shift over time.
Station-level metrics accompany the split-conformal results. Test results do
not select or promote a serving model. The evaluation windows have already
been inspected, so the comparison is development evidence rather than a new
blind holdout.

At 24 hours in winter 2025, the retrospective weather+CAMS LightGBM blend
records MAE 20.50 µg/m³ versus persistence 21.81 on the same rows, with
90.96% observed split-conformal coverage. The history-only blend is 21.23;
weather-only is 21.63. In summer 2026, the weather+CAMS blend is 11.46
versus persistence 12.79, but its interval covers only 67.4%, below the
80% target. These are retrospective results and do not establish that
weather/CAMS were available at each real forecast issue time. The
pollution-only winter 24-hour blend is 23.32 versus persistence 23.36,
showing little benefit under that stricter input policy. Values are rounded
from the JSON and apply to these inspected windows only.

To reproduce the exact saved report in the pinned Python 3.11 environment:

```sh
python backend/scripts/run_experiments.py --horizons 6 24 72 --n-estimators 100 \
  --verify docs/evidence/paired_experiments.json \
  --output /tmp/airtwin-paired-reproduction.json
```

Verification checks the dataset fingerprint, code hashes, package versions,
fold rows, metrics and calibration outputs at absolute tolerance 1e-8. It
passed locally on 28 September 2026. Independent-machine reproduction and
prospective provider-timestamp capture remain outstanding. The runner does
not overwrite trained serving artifacts. For the bundled synthetic sample,
use `--offline` and treat all accuracy numbers as pipeline checks only.
