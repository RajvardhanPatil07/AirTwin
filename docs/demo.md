# Three-minute demonstration script

For the competition recording, use the tighter [submission video storyboard](video_storyboard.md). This longer script remains the technical rehearsal version.

Run FastAPI and use the default frontend backend connection. Prepare it before recording;
keep visible provenance badges and assumptions. Use 1920×1080 if possible.

## 0:00–0:25: problem and scope

“Pollution maps tell us where concentrations are high. AirTwin asks what might
happen next, what may contribute, and which intervention could help more exposed
people. Our area is Pune and Pimpri-Chinchwad.”

State the actual source badge and timestamp immediately. Observed data may be
stale; population and zone proxies are synthetic. If the backend falls back to
the sample, explicitly state that targets are synthetic.

## 0:25–0:55: spatial view and honesty

Select Bhosari MIDC. Show one location tooltip, the modeled hatch grid, the
actual source badge and data timestamp. Toggle Hotspots and Zones to show the
layer distinction. Explain IDW as interpolation, not a new sensor measurement.

## 0:55–1:35: compare actions

Open Scenarios. Adjust cuts and show OUTDATED status, then Run scenario. Select
individual actions and the combined row; the banner/cards/map change together.
Explain ranking by reduction × population, with synthetic population. Set zero
cuts to demonstrate no effect; restore the defaults for the next view.

Do not read invented or stale numbers from a memorized script. Read the actual
result currently displayed. Explain that pass-through and ranges are assumptions.

## 1:35–2:00: source hypotheses

Open Sources and expand assumptions. Traffic, industry, dust and background are
transparent proxy shares; they are not measured chemical source apportionment.
TreeSHAP explains forecast features separately in the Forecast tab.

## 2:00–2:35: forecast and validation

Open Forecast and Backtest. Show the LightGBM projection, quantile band and
TreeSHAP groups, separately from source shares. Read the computed winter metrics
and persistence comparison. Report stations where the model loses. Explain
coverage and data freshness; do not claim operational or causal validation.

## 2:35–3:00: reproducibility and impact

Show README status, test commands and the GitHub Actions workflow. Summarize the
next milestone and intended SDG 3/11/13 contribution. Use confirmed team names
only. Show the replay date banner and Ask AirTwin grounded answer if time allows.
Update recording content around the actual model card and source timestamp.

## Recording checklist

- Restart from a known default; close unrelated tabs and hide private data.
- Check map tiles and viewport before recording.
- Keep source labels and date visible.
- Do not commit video exports, archives or environment files.
- Link the final video externally after team approval; no video link exists yet.
