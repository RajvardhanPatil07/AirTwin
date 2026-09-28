# Teammate 2 PR brief: keep the synthetic map consistent through the timeline

**Start point:** latest `main` on [AirTwin](https://github.com/RajvardhanPatil07/AirTwin). [PR #11](https://github.com/RajvardhanPatil07/AirTwin/pull/11) is already merged; check for newer changes before starting. Work in your own clean clone/branch, suggested `fix/synthetic-timeline-surface`. Do not copy another contributor's uncommitted workspace changes.

## Problem and user-visible result

PR #11 makes the offline `/api/hotspots` baseline nonuniform using synthetic map anchors. `Runtime.timeline()` still interpolates every timeline frame from the single original synthetic station. When a user selects +3 h or another forecast hour, the dashboard replaces the varied map with a uniform grid. The timeline assumption also calls hour 0 an "observed snapshot" even when the input is the synthetic fixture.

Make the timeline use a consistent spatial display policy. Hour 0 must agree cell-for-cell with the baseline hotspot snapshot. Future frames should preserve a clearly labeled illustrative spatial pattern for the one-station synthetic fixture while using the forecast from the single original model reference. Do not create independent station forecasts for fake anchors.

## Ownership and boundaries

Own `backend/app/services/runtime.py`, `backend/tests/test_api.py` (or a focused timeline API test file), and `docs/api.md`. Use the `interpolation_anchors()` helper already introduced by PR #11; Teammate 1 owns its internal station-anchor correction in `spatial.py`. Your PR should remain compatible whether Teammate 1 merges before or after it. Do not edit `spatial.py`, model training, observed/modeled multi-station logic, frontend design, or intervention formulas. The current maintainer workspace has unrelated uncommitted work; branch from remote `main`.

## Acceptance criteria

1. On the offline single-station fixture, `/api/timeline` hour 0 cell values match `/api/hotspots?mode=before` by cell ID and timestamp.
2. At a future hour with a forecast, the synthetic grid remains nonuniform and deterministic; all future cell values are derived from the one original station forecast and explicitly illustrative map anchors.
3. Timeline station lists still contain only the original synthetic station. No anchor is labeled `observed` or presented as a monitoring location.
4. For real multi-station snapshots, existing forecast interpolation behavior is unchanged. For missing forecasts or replay, preserve the current error/skip behavior.
5. Timeline response assumptions distinguish synthetic hour 0 from an observed shared-hour snapshot, and disclose that future synthetic spatial variation is a visual assumption, not separately validated grid forecasting.

## Validation and PR handoff

Add an API regression test that requests both endpoints and compares hour 0, then selects a future frame and checks variation and provenance. Run `python -m pytest backend/tests -q`, `python scripts/check_documentation.py`, and the existing frontend checks if you touch frontend code. Follow `.github/PULL_REQUEST_TEMPLATE.md`; include actual test output and a local demo screenshot of the baseline and +3 h map with source labels visible. Do not commit raw provider data, models, keys, environments, or build outputs. Suggested title: **Keep synthetic hotspot variation through forecast timeline**.

The fix is ready for review when changing timeline hours no longer makes the offline map flat, and the API does not describe synthetic inputs as observations. It does not establish real-world spatial forecast skill.
