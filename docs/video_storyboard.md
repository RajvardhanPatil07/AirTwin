# AirTwin submission video storyboard

Target length: **2:35–2:55**. Record at 1920×1080 if possible. Use Pune + PCMC,
not the Maharashtra-wide view, for the core ENR-01 story.

## Before recording

1. Start the backend and frontend from the exact submission branch.
2. Confirm the header says Pune + PCMC and select Bhosari if it is not already selected.
3. Check the data timestamp and source badge. Never call a synthetic/model value observed.
4. Wait for all five evidence cards to populate.
5. Keep the browser at 100% zoom and hide bookmarks/private tabs.
6. Do one dry run of the scenario sliders before starting the screen recording.
7. Do not depend on Ask AirTwin for the core recording; use it only as a verified bonus.

## 0:00–0:18 — problem

Screen: full AirTwin map and five evidence cards.

Voiceover:

> Most air-quality dashboards stop at showing where pollution is high. AirTwin is
> a city environmental digital twin for Pune and PCMC that goes one step further:
> it predicts PM2.5, tests the forecast against history, estimates likely source
> contributions and lets a planner compare interventions before acting.

Point briefly to the source badge and timestamp.

## 0:18–0:38 — 01 Observe

Click **01 · OBSERVE**.

Voiceover:

> We start from a selected location and its PM2.5 baseline. Every value is labeled
> observed, modeled or synthetic, so an interpolated hotspot is never presented as
> a new sensor measurement.

Show the map cells and one tooltip. Do not spend time toggling every map layer.

## 0:38–0:58 — 02 Predict

Click **02 · PREDICT**.

Voiceover:

> AirTwin forecasts PM2.5 from historical concentration, time patterns and weather.
> The card surfaces the forecast peak immediately, while this chart shows the full
> modeled horizon and uncertainty band.

If the selected target is synthetic or modeled, say so in one sentence.

## 0:58–1:18 — 03 Validate

Click **03 · VALIDATE**.

Voiceover:

> We do not present a forecast without a baseline. The model is evaluated on a
> chronological holdout and compared with persistence. If it loses, AirTwin shows
> that instead of hiding it.

Read the actual MAE / improvement shown on screen. Do not memorize a number.

## 1:18–1:38 — 04 Explain

Click **04 · EXPLAIN**.

Voiceover:

> Next we estimate likely local drivers across traffic, industry and road or
> construction dust, plus regional background. These are transparent proxy
> hypotheses, not laboratory source-apportionment measurements.

Open assumptions only if the screen remains uncluttered.

## 1:38–2:15 — 05 Act

Click **05 · ACT**.

Voiceover:

> This is the digital-twin part. A planner can test traffic restrictions,
> industrial controls and dust suppression. AirTwin recalculates the local
> concentration and the entire hotspot grid, then ranks actions by modeled
> population-weighted exposure reduction.

Change two or three sliders, let the **RESULTS OUTDATED** state appear, then click
**Run scenario**. Select the best individual action and briefly switch Before/After
on the map.

## 2:15–2:38 — why it is different

Screen: after-map plus action ranking.

Voiceover:

> So AirTwin connects five things in one auditable workflow: observe, predict,
> validate, explain and act. Instead of only telling a city that pollution is high,
> it helps compare what could reduce it, while keeping assumptions and provenance
> visible.

## 2:38–2:50 — close

Screen: pull back to the five evidence cards.

Voiceover:

> Our next step is stronger real-world spatial inputs and continued calibration,
> but the end-to-end decision loop already works. This is AirTwin.

End immediately. Do not finish with terminal windows or README scrolling.

## Recording backup path

If live environmental providers are unavailable, use the repository's explicit
offline/synthetic mode and say exactly that in the narration. A stable, honest demo
is stronger than a broken live-data claim.

## Thumbnail / first frame

Use the map with the five cards populated and the scenario after-map visible.
Suggested title overlay outside the product UI:

**AirTwin — From Pollution Maps to Action**
