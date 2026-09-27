# Attribution, intervention and data assumptions

The backend reads `config/assumptions.yaml`. API attribution returns that config;
modeled responses return plain-language assumptions. The frontend-only mock has
its own illustrative engine and is used only when the API is unavailable or demo
mode is explicitly selected.

## Data and time

- AOI: latitude 18.45–18.80, longitude 73.70–73.98.
- OpenAQ sensor IDs identify series; a location can contain replacement sensors.
- PM2.5 outside 0–1000 µg/m³ is rejected. Missing target hours are not imputed.
- All hour alignment uses Asia/Kolkata. Feature lags reindex to a complete hourly axis.
- Map/background use the most recent shared hour with at least two sensors when
  possible, within 24 hours of the latest dataset record. Older sensors are excluded.
- A source snapshot can itself be stale. The API/UI warn after 24 hours; they do
  not relabel cached data as a current live observation.
- Centroid weather is shared. Reanalysis is MODELED, not a station observation.
- Previous-run forecast values are aligned from valid time back to issue time for
  24/48/72-hour features. Missing values use issue-weather persistence.
- Shorter direct horizons use issue-weather persistence. BLH is missing when not
  supplied; no fabricated boundary-layer data are generated.
- The sample remains entirely SYNTHETIC. CAMS fallback targets remain MODELED.

## Background and local source hypotheses

Background = 15th percentile of concentrations at the shared snapshot hour,
capped at each cell's baseline. Local excess = max(baseline − background, 0).
IDW uses power 2 and a local distance approximation. A 12×12 grid is an
interpolation display, not 144 independent monitoring locations.

The hand-made `data/zones.geojson` outlines are SYNTHETIC proxy geometry, not
surveyed industrial boundaries or proof of active construction. Weights use:

- Traffic: assumed corridor proximity and a peak-hour multiplier at 8–10 and 18–20.
- Industry: approximate zone-center proximity with a 5 km decay scale and upwind
  cosine of meteorological wind-from direction, with a small minimum weight.
- Dust: construction proxy proximity with a 4 km decay scale and dryness/rain factor.

Raw weights normalize to one over local sources. Display concentration shares
include background and sum to one. SHAP weather/temporal/persistence/spatial groups
are displayed separately: they explain the forecast, not pollution source causes.

## Interventions and uncertainty

Traffic, industry and dust emission cuts are bounded to 50%, 60% and 70% respectively.
Central ΔPM2.5 = local excess × Σ(local weight × cut fraction) × 0.7.
Individual and combined packages use that exact function; central combined benefit
is additive before rounding. After concentration cannot fall below background.

Low/high sensitivity varies pass-through from 0.6 to 0.8 and aggregate source
scaling by ±20%; high reduction is capped at local excess. These are sensitivity
bounds, not empirically calibrated confidence intervals. Meteorology is held fixed.

## Population and benefit

Population follows an explicitly SYNTHETIC core-density curve. WorldPop is not used.
Exposure benefit = Σ(cell reduction × cell population), in person·µg/m³. It is not
a count of people protected, cumulative dose, avoided deaths or demonstrated policy
impact. Selected-location reduction and AOI-wide benefit have different scopes.

## Replay and forecast limitations

Historical replay selects a high held-out target hour and labels its date/source.
Its 24-hour forecast uses the pre-holdout model. Shorter points are interpolated
from the issue reading; replay is not a full archived operational forecast product.
The Backtest tab contains actual held-out predictions from the pre-holdout model.

Current serving models refit on all available data. Forecast horizons 1–24, 48
and 72 are direct; gaps from 25–71 hours are interpolated. Quantile bounds must be
interpreted alongside measured coverage and underperformance in the model card.
