# AirTwin PCMC frontend

React + Vite + TypeScript, Tailwind CSS, React Leaflet, and Recharts. The visual
reference is the provided Kombai civic dashboard screenshot, not a new design.

```sh
npm ci
npm run dev
```

No API keys or backend are required for the frontend demo. Fonts are bundled
locally. The OpenStreetMap basemap requires network access; if tiles fail, the
grid, location markers, charts, and scenarios remain usable with an explicit notice.

```sh
npm run build
npm run lint
npm test
```

To connect a future backend, copy `.env.example` to `.env`, set
`VITE_API_BASE_URL`, and restart Vite. These variables are public configuration;
never put an API key in a `VITE_` variable. The exact contract is in `src/types.ts`
and `../docs/api.md`. If initial loading fails, the entire dashboard switches to
synthetic demo data with a warning. A later request failure displays a retry state,
so real inputs are never silently combined with synthetic analysis.

## What works

- Interactive 12×12 grid, six selectable demo locations, illustrative zone outlines,
  map layer toggles, and before/after views.
- Three emission-cut sliders, a combined package, uncertainty ranges, and ranking
  by computed population-weighted exposure reduction.
- One selected scenario response drives the banner, concentration cards, result table,
  and map. Markers remain at their original baseline in after view.
- Overview, illustrative forecast, synthetic backtest, proxy source shares, and
  assumptions. Real LightGBM/SHAP work is a later backend step.
- Light/dark themes, responsive layout, keyboard map selection, and one map tooltip.

## Demo provenance

`src/mocks/engine.ts` contains synthetic input readings and populations plus all
demo calculations. The location values follow the visual reference; they are
**not observations**. The forecast is an illustrative daily-cycle projection,
not a trained ML forecast. Its interval is illustrative, not calibrated.

The backtest predictor is 24-hour persistence on a deterministic synthetic series.
MAE, RMSE, R², baseline improvement, and interval coverage are computed from the
displayed series; they do not establish real-world accuracy. There is no winter
holdout or TimeSeriesSplit validation yet.

Scenario cuts apply to local-excess weights normalized across traffic, industry,
and dust. Regional background is capped at each cell's baseline. Combined benefits
equal the sum of individual actions, including exposure benefit, before rounding.
Display rounding can cause tiny differences when summing visible table values.
The benefit unit is person·µg/m³, not a number of people protected.

The source screenshot's contour logo is reused as a small supplied raster asset.
Inter is supplied by `@fontsource/inter` (SIL Open Font License); map tiles retain
OpenStreetMap attribution. Approximate zone geometry is illustrative and unverified.
