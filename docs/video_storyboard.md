# AirTwin Round 1 submission video storyboard

**Hard limit: 3:00.** The official Round 1 video must present **both the official
PPT and the developed prototype**. Do not create extra PPT slides for the video;
use only the organizer-provided template.

Recommended target: **2:45–2:55**.

## Before recording

1. Use the exact official PPT submitted to the organizers.
2. Start FastAPI and the frontend from the exact submission commit.
3. Open Pune + PCMC and select Bhosari or another verified location.
4. Check source badge and data timestamp.
5. Wait for the five evidence cards to populate.
6. Browser zoom 100%, 1920×1080 if possible; hide bookmarks/private tabs.
7. Rehearse the scenario once.
8. Do not make Ask AirTwin/Gemini a dependency of the core recording.

## 0:00–0:10 — PPT: team + track

Screen: official template's team/introduction slide.

Say the **registered team name**, member names, ENR-01 and the relevant track.
Do not spend time on biographies.

Suggested narration:

> We are [Team Name], and this is AirTwin for ENR-01: an urban environmental
> digital twin for actionable city air-quality decisions.

## 0:10–0:27 — PPT: problem understanding

Screen: official problem-statement content.

> Existing air-quality maps tell planners where PM2.5 is high, but not what is
> likely to happen next, what may be driving it, or which intervention could help.
> ENR-01 asks for forecasting, source categories, multiple actions, hotspot mapping
> and historical validation with observed and modeled results kept separate.

## 0:27–0:47 — PPT: proposed solution

Screen: the official template section where the proposed solution is explained.

Use one simple flow in the existing template content:

**Observe → Predict → Validate → Explain → Act**

> AirTwin connects those requirements into one decision loop: map the baseline,
> forecast PM2.5, validate against history, estimate transparent source proxies,
> and simulate traffic, industry and dust-control actions.

Mention the core stack in one sentence:

> React and Leaflet power the map, FastAPI serves the twin, and LightGBM provides
> the forecasting layer.

## 0:47–0:57 — PPT: innovation + future scope / impact

Use whichever official-template section covers these points; **do not add a slide**.

> The innovation is the shift from monitoring to intervention comparison. This
> Round-1 build is our Phase-1 working prototype; the next stage replaces proxy
> road, industrial and population layers with higher-quality operational inputs.

Transition immediately to the app.

## 0:57–1:13 — Prototype: 01 Observe

Screen: AirTwin map + judge journey. Click **01 · OBSERVE**.

> We start with the PM2.5 baseline and hotspot map. Every value is labeled observed,
> modeled or synthetic so an interpolated cell is never presented as a sensor.

Hover one hotspot. Keep the source badge/timestamp visible.

## 1:13–1:30 — Prototype: 02 Predict

Click **02 · PREDICT**.

> The forecasting model uses pollution history, temporal patterns and weather to
> estimate future PM2.5. The card surfaces the forecast signal while the chart shows
> the horizon and uncertainty.

If the current target is modeled/synthetic, state it in one short sentence.

## 1:30–1:47 — Prototype: 03 Validate

Click **03 · VALIDATE**.

> We also compare the model against simple historical baselines on a chronological
> holdout. If the model underperforms persistence, AirTwin shows that instead of
> hiding it.

Read the **actual** MAE/improvement visible in the recording.

## 1:47–2:04 — Prototype: 04 Explain

Click **04 · EXPLAIN**.

> AirTwin then separates likely local influence across traffic, industry and
> construction or road dust, plus regional background. These are transparent
> proxy hypotheses, not laboratory chemical source apportionment.

## 2:04–2:38 — Prototype: 05 Act

Click **05 · ACT**.

> Finally, planners can compare traffic restrictions, industrial controls and
> dust suppression. The twin recalculates the selected location and the hotspot
> grid and ranks actions by modeled population-weighted exposure reduction.

Move 2–3 sliders, show **RESULTS OUTDATED**, press **Run scenario**, select the
best individual action, then switch Before/After once.

## 2:38–2:52 — close: solution fit + social impact

Screen: after-map + five journey cards.

> AirTwin turns a pollution map into a transparent decision simulator: observe,
> predict, validate, explain and act. The goal is to help cities compare cleaner
> mobility, industrial and dust-control strategies while making assumptions and
> uncertainty visible.

## 2:52–2:57 — end

> This is AirTwin.

Stop. Leave 2–3 seconds of safety margin under the 3-minute hard limit.

## Recording rules

- Do not show terminal setup unless the app fails and there is no other option.
- Do not scroll the README in the final video.
- Do not claim measured policy impact, lives saved, or measured chemical source percentages.
- Do not quote an old accuracy number if the displayed run changed.
- If live providers are unavailable, use the explicit offline/synthetic mode and say so.
- Keep the video out of Git; put it in the submission Drive folder.
