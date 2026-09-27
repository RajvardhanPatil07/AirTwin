# AirTwin hackathon execution plan

This branch is the **competition-ready core milestone**: the goal is not to finish
every research idea, but to make the ENR-01 loop undeniable in a short judge demo.

## Winning product story

AirTwin should answer five questions in order:

1. **Observe** — where is PM2.5 high right now / at the selected data timestamp?
2. **Predict** — what may happen next?
3. **Validate** — did the forecast beat a simple persistence baseline historically?
4. **Explain** — which local source proxies are most relevant, with assumptions?
5. **Act** — which of three interventions produces the largest modeled reduction?

The frontend now exposes these as a five-card evidence journey. Clicking a card
opens the corresponding evidence tab, so the same sequence can be used in the
submission video and live judging.

## Milestone 1 — core demo (~35% competition readiness)

Completed / present in the repository:

- City-first Pune + PCMC startup state.
- Pollution hotspot map with source/provenance labels.
- PM2.5 forecasting and 24/48/72-hour views.
- Historical backtest against persistence and seasonal baselines.
- Traffic, industry, dust and regional-background source hypotheses.
- Three individual intervention controls plus a combined package.
- Before/after map state and population-weighted action ranking.
- Strict OBSERVED / MODELED / SYNTHETIC distinction.
- Clickable Observe → Predict → Validate → Explain → Act judge journey.
- Offline fallback, tests and reproducible startup path.
- Optional Maharashtra context and Ask AirTwin remain bonus features, not the
  core pitch.

This is enough for a strong first-round video because every required ENR-01 outcome
has visible evidence. Do not add more screens until this path is stable on the
recording machine.

## Milestone 2 — evidence strength (35 → 60%)

Priority order:

1. Refresh the latest usable observed Pune/PCMC data and record exact timestamps.
2. Re-run training and preserve the generated holdout metrics.
3. Verify Bhosari and at least one other location for a clean demo path.
4. Replace approximate proxy geometry with sourced road / industrial / construction
   data where licensing and time allow.
5. Calibrate or clearly weaken uncertainty claims if interval coverage is poor.

Winning criterion: judges should trust the evidence even when the model is imperfect.

## Milestone 3 — product polish (60 → 80%)

- Deploy a stable public demo if hackathon rules allow it.
- Add a single saved demo scenario rather than more controls.
- Improve loading/failure copy and recording-safe responsive layout.
- Add a compact methodology drawer linking each number to its assumption.
- Use Ask AirTwin only after a real provider-backed run is verified; never make the
  LLM the core demo dependency.

Winning criterion: a judge can understand the product without the presenter explaining
the interface.

## Milestone 4 — submission (80 → 100%)

- Record the 2.5–3 minute video from the storyboard.
- Capture final desktop screenshots with provenance and timestamps visible.
- Re-run CI on the exact submitted commit.
- Add team names/roles and final video link.
- Practice a 30-second problem statement and 30-second technical defense.
- Prepare answers for: data freshness, source attribution assumptions, forecast
  baseline, intervention causality and synthetic population.

## What not to build before the video

Avoid spending time on authentication, user accounts, a mobile app, 3D city models,
additional pollutants, blockchain, notifications or another AI assistant. None of
those improve the ENR-01 scoring loop as much as trustworthy evidence and a clear
before/after intervention story.
