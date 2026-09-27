# Three-minute demonstration script

Use the default frontend without VITE_API_BASE_URL. Prepare it before recording;
keep visible provenance badges and assumptions. Use 1920×1080 if possible.

## 0:00–0:25: problem and scope

“Pollution maps tell us where concentrations are high. AirTwin asks what might
happen next, what may contribute, and which intervention could help more exposed
people. Our area is Pune and Pimpri-Chinchwad.”

State immediately: “This build uses synthetic demo inputs. Real ML and the API
are pending; we are showing the interaction and calculation workflow.”

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

Open Forecast and Backtest. Point out the illustrative forecast/band notices and
synthetic target. The demo predictor equals persistence; metrics are computed,
but this is not real forecasting skill. Explain the planned winter holdout and
baseline comparison. Never rename this demonstration “validated ML”.

## 2:35–3:00: reproducibility and impact

Show README status, test commands and the GitHub Actions workflow. Summarize the
next milestone and intended SDG 3/11/13 contribution. Use confirmed team names
only. If real backend/model work is completed later, update this script and
screenshots around the actual evidence before recording.

## Recording checklist

- Restart from a known default; close unrelated tabs and hide private data.
- Check map tiles and viewport before recording.
- Keep source labels and date visible.
- Do not commit video exports, archives or environment files.
- Link the final video externally after team approval; no video link exists yet.
