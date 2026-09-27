# Contributing to AirTwin

Keep changes understandable to a student presenter and reviewable by a teammate.
The repository is a frontend demo and ingestion pipeline, not a finished ML service.
Start by reading README status, docs/roadmap.md and docs/assumptions.md.

## Local development

Use Node 22 for the frontend and Python 3.11 for ingestion. Install with `npm ci`
and `python -m pip install -r backend/requirements.txt` in a virtual environment.
The default frontend and `bash scripts/pipeline.sh --offline` need no keys.
Do not replace the sample unless that replacement is the purpose of your change.

## Branch and review workflow

1. Open or select a focused issue with acceptance criteria.
2. Create a short descriptive branch, such as `feat/winter-backtest`.
3. Make small commits that each explain one change.
4. Run affected checks, then the complete checks before merge.
5. Open a PR using the template; explain limitations and attach visual evidence.
6. Request teammate review. Resolve feedback without rewriting unrelated code.

Do not manufacture commit counts: splitting code into coherent modules and tests
is useful; repeated whitespace-only or empty commits are not. Never backdate
commits, invent team authors, or credit someone without their contribution.

Example commit subjects:

- `feat: preserve station provenance in forecast responses`
- `fix: prevent future target leakage in lag features`
- `test: verify combined scenario additivity`
- `docs: explain synthetic exposure weights`
- `ci: validate offline sample fallback`

## Data and model rules

- Preserve observed/modeled/synthetic provenance in data and response types.
- Target provenance does not establish weather or population provenance.
- No raw dumps, model binaries, keys, environments, videos or generated builds.
- Fixture CSVs must remain below 1 MB and describe their origin.
- Use chronological evaluation. Compute metrics; never type desirable results.
- Keep proxy attribution separate from SHAP feature explanations.
- When formulas change, update assumptions, documentation and meaningful tests.
- Do not silently mix real inputs with synthetic analysis after an API failure.

## Frontend rules

Preserve the selected screenshot direction in frontend/DESIGN.md. Respect the
canonical types in frontend/src/types.ts. Keep one selected scenario result as the
source for the map, banner, cards and ranking. Test zero cuts, narrow layouts,
keyboard selection, theme changes and errors. A label must describe what the data
is, not what a future version hopes it will be.

## Required checks

```sh
python -m pytest backend/tests -q
bash scripts/pipeline.sh --offline
cd frontend
npm run lint
npm test
npm run build
npm run test:sites
```

Also run `python scripts/check_repository.py` from root after staging intended
files. It checks tracked/staged file paths and sizes, not credential contents.
Review `git diff --cached` for secrets and unexpected files before committing.

## Dependency and documentation changes

Commit package-lock.json with package.json changes; use exact Python requirement
versions. Separate planned dependencies from the executable pipeline. Include
release notes for user-visible changes. Broken links, unavailable commands and
misleading screenshots are bugs, just like failed tests.
