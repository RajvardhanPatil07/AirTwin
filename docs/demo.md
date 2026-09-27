# Three-minute demonstration script

Use the default frontend without VITE_API_BASE_URL. Prepare it before recording;
keep visible provenance badges and assumptions. Use 1920×1080 if possible.

## 0:00–0:25: problem and scope

“Pollution maps tell us where concentrations are high. AirTwin asks what might
happen next, what may contribute, and which intervention could help more exposed
people. Our area is Pune and Pimpri-Chinchwad.”

State immediately: “The browser demo is synthetic for reproducibility. We also
have an executable backend model/API; observed-data accuracy is only claimed after
running the live provider pipeline and checking provenance.”

## 0:25–0:55: spatial view and honesty

Select Bhosari MIDC. Show one location tooltip, the modeled hatch grid, the
SYNTHETIC badge and fixed data timestamp. Toggle Hotspots and Zones to show the
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
SHAP will eventually explain forecast features separately.

## 2:00–2:35: forecast and validation plan

For the strongest demo, run the frontend against the FastAPI backend. Open Forecast
and Backtest, point out target provenance, the chronological holdout and persistence
baseline. If the target label is SYNTHETIC, say explicitly that the metrics prove
the pipeline works but do not establish Pune/PCMC forecast skill.

## 2:35–3:00: reproducibility and impact

Show README status, the backend API health response, test commands and GitHub
Actions. Summarize the next evidence milestone: observed provider coverage and
recorded holdout metrics. Use confirmed team names only and keep the actual
provenance badge visible while recording.

## Recording checklist

- Restart from a known default; close unrelated tabs and hide private data.
- Check map tiles and viewport before recording.
- Keep source labels and date visible.
- Do not commit video exports, archives or environment files.
- Link the final video externally after team approval; no video link exists yet.
