# Validation and test coverage

## Automated commands

Run from root in the Python environment:

```sh
python -m pytest backend/tests -q
bash scripts/pipeline.sh --offline
python scripts/check_repository.py
```

Run from frontend:

```sh
npm run lint
npm test
npm run build
npm run test:sites
```

`make check PYTHON=.venv/bin/python` combines tests, lint, build and hosting tests.
CI additionally exercises the offline pipeline. Tests do not need provider keys.

## What the suites prove

**Python pipeline:** outlier rejection/duplicate averaging; provenance preservation;
missing-weather merge; sample size/labels/hour continuity; missing-key fallback;
weather outage fallback; sparse/CAMS failure fallback without rewriting the sample.

**TypeScript engine:** zero cuts; combined concentration/exposure additivity;
normalized source/local shares; exact-location IDW; background/maximum cut behavior;
computed persistence demonstration/provenance; nonnegative sensitivity ranges.

**API adapter:** no request when the backend is explicitly disabled; explicit initial demo
fallback; rejection of invalid response provenance and missing modeled assumptions.
This is not full runtime schema validation of every nested response field.

**Hosting worker:** static assets, SPA routing and worker behavior supplied by the
prototype runtime. It does not test a FastAPI server.

## Browser checks

Use 1920×1080 and 1366×768, plus a narrow mobile viewport. Check all tabs,
location/cell selection, map layers, before/after views, slider outdated status,
Run scenario, zero cuts, ranked action selection, assumptions and themes.
Verify one tooltip, keyboard access, no horizontal overflow and no console errors.
The recorded frontend QA report is frontend/design-qa.md.

## What remains unproven

Backend tests now verify gap-aware/no-future features, horizon forecast alignment,
purged temporal boundaries, metrics, IDW, zero cuts/additivity, SHAP reconstruction,
API contracts/CORS/errors, replay and template explanations. The model card contains
real held-out evidence for the downloaded dataset. Live optional LLM integration,
strong interval calibration, real population and causal policy effects remain unproven.

## Interpreting a green CI badge

Green means the checked commit passed the configured jobs. It does not guarantee live APIs are available or the model is accurate. Inspect
job logs and commit SHA. Do not keep a manually written “all tests pass” claim if
changes have not been validated.
