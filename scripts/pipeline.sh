#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
mode="${1:---offline}"
if [[ "$mode" != "--offline" && "$mode" != "--live" ]]; then
  echo "Usage: bash scripts/pipeline.sh [--offline|--live]" >&2
  exit 2
fi
python_bin="${AIRTWIN_PYTHON:-python3}"
if [[ "$mode" == "--offline" ]]; then
  "$python_bin" backend/scripts/fetch_openaq.py --offline
  "$python_bin" backend/scripts/fetch_weather.py --offline
  "$python_bin" backend/scripts/fetch_exogenous.py --offline
  "$python_bin" backend/scripts/build_dataset.py --offline
else
  "$python_bin" backend/scripts/fetch_openaq.py --months 18
  "$python_bin" backend/scripts/fetch_weather.py
  "$python_bin" backend/scripts/fetch_exogenous.py
  "$python_bin" backend/scripts/build_dataset.py
fi
