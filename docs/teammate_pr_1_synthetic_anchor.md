# Teammate 1 PR brief: make the synthetic map agree with its source marker

**Start point:** latest `main` on [AirTwin](https://github.com/RajvardhanPatil07/AirTwin). [PR #11](https://github.com/RajvardhanPatil07/AirTwin/pull/11) is already merged; check for newer changes before starting. Work in your own clean clone/branch, suggested `fix/synthetic-anchor-consistency`. Do not copy another contributor's uncommitted workspace changes.

## Problem and user-visible result

PR #11 gives the one-station offline fixture six illustrative synthetic anchors, making `/api/hotspots` nonuniform. Its `interpolation_anchors()` output omits the original synthetic station. The committed fixture's station is at 18.625 N, 73.84 E with PM2.5 about 63.51 µg/m³ at the latest sample hour, but the PR's IDW factors give about 73.46 µg/m³ at those same coordinates. A demo station marker and the surrounding surface therefore disagree.

Make IDW honor the original synthetic reading exactly at its coordinates while preserving spatial variation elsewhere. Keep the single fixture time series as the only forecast/model reference. Extra anchors are visualization assumptions, never new observed stations.

## Ownership and boundaries

Own `backend/app/services/spatial.py`, `backend/tests/test_scenarios.py`, and the synthetic-map explanation in `docs/assumptions.md`. Coordinate with Teammate 2, who owns `runtime.py`, the timeline API test, and `docs/api.md`. Do not revert their edits or change model training, real OpenAQ data, statewide interpolation, frontend design, or intervention coefficients. The current maintainer workspace also has unrelated uncommitted work; branch from remote `main` so it stays safe.

## Acceptance criteria

1. For exactly one `source_type='synthetic'` station, `idw(station.latitude, station.longitude, interpolation_anchors([station]))` equals that station's PM2.5 (within floating-point tolerance).
2. The offline 12×12 `/api/hotspots` grid still has meaningful, deterministic variation; the same input gives the same grid on repeated runs. Do not rely on a desired fixed concentration range if the fixture value changes.
3. For observed or modeled station inputs, and for multiple stations, the input points and IDW behavior are unchanged.
4. `/api/stations` still exposes only the original synthetic station. Added map anchors must not appear as observed stations, model training rows, or independent measurements.
5. Assumptions explicitly explain the synthetic anchor construction and that map variation is illustrative, not a measured spatial gradient.

## Validation and PR handoff

Run the relevant backend unit/API tests, then `python -m pytest backend/tests -q` and `python scripts/check_documentation.py`. In the PR description, use `.github/PULL_REQUEST_TEMPLATE.md`: describe the mismatch and resulting behavior, report actual test output, and include a before/after local demo screenshot with the SYNTHETIC label visible. Do not commit raw provider data, models, keys, environments, or build outputs. Suggested title: **Fix synthetic station and map surface consistency**.

The fix is ready for review when a teammate can reproduce the equality check and the offline grid remains varied. It is not evidence that the real PCMC map became more accurate.
