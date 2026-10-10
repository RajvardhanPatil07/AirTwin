.PHONY: help frontend pipeline pipeline-live test check backend train run-all experiments hotspots spatial-inputs
PYTHON ?= python3
help:
	@echo "frontend: start Vite; pipeline: offline data build; pipeline-live: fetch providers; test: run tests; check: lint, build and tests"
frontend:
	cd frontend && npm run dev
pipeline:
	AIRTWIN_PYTHON="$(PYTHON)" bash scripts/pipeline.sh --offline
pipeline-live:
	AIRTWIN_PYTHON="$(PYTHON)" bash scripts/pipeline.sh --live
test:
	$(PYTHON) -m pytest backend/tests -q
	cd frontend && npm test
check: test
	cd frontend && npm run lint && npm run build && npm run test:sites
backend:
	$(PYTHON) -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000
train:
	$(PYTHON) backend/scripts/train_model.py
run-all:
	AIRTWIN_PYTHON="$(PYTHON)" bash scripts/run_all.sh --offline
experiments:
	$(PYTHON) backend/scripts/run_experiments.py
hotspots:
	$(PYTHON) backend/scripts/analyze_station_hotspots.py
spatial-inputs:
	$(PYTHON) backend/scripts/prepare_spatial_inputs.py
