# Verification of the connected intervention workflow

## 28 September 2026 follow-up

The current local frontend passed 14 tests, ESLint, TypeScript/Vite build and
four hosting tests. Backend full suite passed 34 tests before the final delayed
sampling regression was added; all three validation-specific tests then passed.
The connected `/backend` runtime checker passed on observed targets with
`gemini_evidence_checked`; the cached dataset origin remains 24 September 2026
22:00 IST. This does not establish current live data or provider uptime.

At 390×844, document width equaled viewport width. Keyboard Enter selected
Industrial controls and updated the displayed after concentration and selected
benefit. Home set all cuts to zero, old results were marked outdated, and Run
scenario produced equal before/after values, zero benefits and no claimed winner.
Forecast showed separate observed history, modeled predictions and TreeSHAP
explanation. This is a bounded recheck, not a new full accessibility audit.

Twenty-four seasonal forecast evaluations and three synthetic population
profiles were computed from the local dataset on 27 September; those are
historical stress tests, predating the sourced PCMC spatial input. Results and limitations are in
[validation protocol](validation_protocol.md). Documentation link and tracked-file
checks passed. New CI steps exercise the connected offline API and validation CLI.
The original 27 September evidence below is retained as a dated historical record.

Recorded during the 27 September 2026 work session. These checks cover local
changes applied to a fresh GitHub clone; they are not a new remote CI run.

## Clean setup

Cloned the GitHub repository into a separate temporary checkout, created a new
Python 3.11 environment, installed pinned Python requirements and ran `npm ci`.
No local `.env`, observed downloads, processed data or saved model binaries were
copied into the clone. Node 26.5.0 was used locally; CI remains configured for Node 22.

The offline fetch/build/train pipeline completed on 2,952 explicitly synthetic
records. The backend served on port 8011 and the frontend on port 5191 with the
Vite `/backend` proxy. The runtime checker passed against both the API and proxy;
without credentials the explanation method was `grounded_summary`.

## Automated checks

- Python: 32 tests passed in the separate environment, including exposure bounds
  and accepting provider claim arrays without weakening numeric evidence checks.
- Frontend: 14 tests passed, including individual-action ranking, zero-benefit,
  overlapping/separated bounds and missing sensitivity metadata.
- Hosting: 4 tests passed. Type checks, ESLint, Vite build, tracked-file hygiene
  and whitespace checks passed.
- Deprecation notices from Starlette's AnyIO alias and Node's module API remain;
  they did not prevent these checks from completing.

## Local observed data and generated AI

`python scripts/verify_runtime.py --url http://127.0.0.1:5188/backend --require-gemini`
passed against the connected application. It verified real API/model execution,
three actions plus combined additivity, exposure bounds, zero cuts and matching
after-grid. Explanation method: `gemini_evidence_checked`.

The browser also displayed a generated Gemini answer for Bhosari identifying
Industrial controls as the leading individual action at the applied cuts. The
comparison correctly disclosed overlapping exposure-benefit bounds.

Observed targets remain dated 24 September 2026 at 22:00 IST. Startup and data
freshness are separate facts: the dashboard labels this stale snapshot and uses
its timestamp as forecast origin. No new environmental observations were invented.

## Browser and resilience checks

- Laptop (1366×768) and mobile (390×844) layouts inspected. Mobile document width
  equaled viewport width. Ranked rows reflow into labeled readable entries.
- Keyboard Home/End changed sliders and showed RESULTS OUTDATED. After running
  zero cuts, baseline and after matched, all benefits were zero and no winner was claimed.
- Forecast, Backtest and Sources tabs displayed their separate evidence. The
  healthy local page reported no console errors during the check.
- Both themes were checked at mobile width. AI drawer stayed within the viewport;
  Escape closed it and restored trigger focus. Loading text appeared during AI requests.
- The isolated API was deliberately stopped: failed scenario execution retained
  its previous result with Retry analysis; AI exposed Retry explanation.
- Reloading with that API absent used an entirely labeled synthetic dashboard,
  with Retry backend and disabled AI generation. Restarting it and retrying restored
  the trained backend connection without refreshing the page.

Screenshots were saved outside the repository to avoid committing transient demo
images. The post-change design audit is `anti-slop/audit-001-2026-09-27.md`.

## Limits

Tests establish these implementation behaviours for this run. They do not certify
all screens, guarantee provider uptime or prove semantic correctness of AI answers.
Intervention ranges are assumption bounds, not statistical confidence intervals.
An overlap does not demonstrate a simulated reversal of the central ranking.
