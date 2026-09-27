.PHONY: help frontend pipeline pipeline-live test check
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
