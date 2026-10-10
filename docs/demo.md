# Bhosari decision demo: 2 minutes 45 seconds

One question: **Under the displayed assumptions, should a Bhosari user explore
industrial controls or dust suppression first?** The answer may remain uncertain.
Use the connected PCMC backend. Select the actual Bhosari station if available;
read its name and provenance. If absent, prepare an explicitly dated replay.

Prepare traffic 20%, industry 30%, dust 30%. Keep timestamp and source labels
visible. Read values from the running application; do not memorize numbers.

## 0:00–0:20: user and decision

“A facilities or environmental team in Bhosari needs to decide which pollution
control to investigate first. AirTwin forecasts PM2.5 and compares industrial
controls with dust suppression under visible assumptions.”

Describe this as an intended user until a real session is recorded. Do not claim
that a municipality or researcher has adopted the tool.

## 0:20–0:45: evidence available today

Select Bhosari. Read provider, source badge and date. State whether the snapshot
is cached or synthetic. Show one reading and explain that the surrounding grid
is interpolation. For PCMC, population is a WorldPop 2020 modeled estimate and
selected OSM zones are mapped geometry; scenario response remains assumed.

## 0:45–1:15: forecast before action

Open Forecast, then Backtest. Read the 24-hour prediction and displayed
station/reference validation result. Compare MAE with persistence.
“Skill varies with station and season. The band is evaluated historically;
it does not guarantee coverage for this episode.”

Keep statewide coverage, animations, health advice and chat for questions after
the demo. Winter pooled skill cannot establish Bhosari operational accuracy.

## 1:15–1:55: compare two actions

Run prepared cuts. Select Industrial controls and Dust suppression in turn.
Show local before/after concentration and the grid-wide exposure index.
Explain that these metrics cover different scopes.

“The index uses dated, modeled population. These cuts are not equal-cost options.
The central ranking depends on source shares and response coefficients.”

If ranges overlap, explain why the central estimate alone cannot establish a
reliable winner. Show one actual counterexample in the intervention stress report,
if present. An overlap alone is not a reversal.

## 1:55–2:15: consistency check

Set all cuts to zero and run again. Before and after must match, benefits must
be zero, and the application must not claim a winner.

## 2:15–2:45: evidence and next step

“Regional reports support the categories. We disclose local assumptions and test
ranking sensitivity. Next, an intended user will test this workflow and a
monitored pilot will validate an intervention response.”

Update that sentence only after real feedback is recorded. Show repository
evidence links and one verification result. End with the single decision and
what additional evidence would make it actionable.

## Before recording

- Verify submission commit, backend connection and timestamp.
- Rehearse to 2:45; the official limit is **3 minutes**, including intro/outro.
- Check zero-cut behavior before the take.
- Close unrelated tabs and hide credentials.
- Use the official PPT template without adding slides.
- Show real team roles and contributions.
- Check audio and Drive permissions from a separate viewer account.

PPT, video and sharing remain submission tasks. This script is not a completed
recording. See [intervention evidence](intervention_evidence.md),
[forecast challenger](evidence/forecast_challenger.md) and [feedback kit](user_feedback.md).
