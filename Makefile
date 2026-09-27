.PHONY: help frontend backend pipeline pipeline-live test test-pipeline test-backend check
PYTHON ?= python3
help:
	@echo "frontend: start Vite; backend: start FastAPI; pipeline: offline data build; pipeline-live: fetch providers; test: all tests; check: full quality suite"
frontend:
	cd frontend && npm run dev
backend:
	$(PYTHON) -m uvicorn backend.app.main:app --reload --port 8000
pipeline:
	AIRTWIN_PYTHON="$(PYTHON)" bash scripts/pipeline.sh --offline
pipeline-live:
	AIRTWIN_PYTHON="$(PYTHON)" bash scripts/pipeline.sh --live
test-pipeline:
	$(PYTHON) -m pytest backend/tests/test_pipeline.py -q
test-backend:
	$(PYTHON) -m pytest backend/tests/test_forecasting.py backend/tests/test_twin.py backend/tests/test_api.py -q
test: test-pipeline test-backend
	cd frontend && npm test
check: test
	cd frontend && npm run lint && npm run build && npm run test:sites
