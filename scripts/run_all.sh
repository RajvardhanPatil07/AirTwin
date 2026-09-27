#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python_bin="${AIRTWIN_PYTHON:-python3}"
mode="${1:---offline}"
if [[ "$mode" != "--offline" && "$mode" != "--live" ]]; then
  echo "Usage: bash scripts/run_all.sh [--offline|--live]" >&2
  exit 2
fi
AIRTWIN_PYTHON="$python_bin" bash scripts/pipeline.sh "$mode"
if [[ "$mode" == "--offline" ]]; then
  "$python_bin" backend/scripts/train_model.py --offline
else
  "$python_bin" backend/scripts/train_model.py
fi
exec "$python_bin" -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000
