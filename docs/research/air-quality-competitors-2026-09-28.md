# AirTwin secondary competitor reading — 28 September 2026

These six repositories solve adjacent air-quality problems. **They are not verified HackMatrix 5.0 entrants.** Each reports another hackathon. Only DelhiAir.AI below has a September 2026 repository creation/push. Hackathon affiliation is author-reported; no organizer acceptance, finalist status or award was independently verified. This note supplements the separate search for HackMatrix ENR01 teams.

Method: read each complete root README through GitHub's primary API, inspect repository metadata, recent default-branch commits and file trees, then read the implementation/documents linked below. Nothing was executed. Accuracy, latency, production readiness and competition scores remain author claims unless explicitly described as source observations. Repository creation is publication time, not necessarily development start; push time is not event participation evidence. `updated_at` includes metadata changes and is not a code-activity timestamp.

## Dates and event evidence

All timestamps below are UTC, 2026. The metadata/commit links are the primary evidence.

| Repository | Created | Latest push | Latest inspected commit | Reported event | September relevance |
|---|---|---|---|---|---|
| [ProjectAtmos](https://github.com/premkadam7/ProjectAtmos) | July 20 18:15:29 | July 22 17:58:10 | July 22 17:58:10 | ET AI Hackathon, PS5 | Older comparable |
| [Urban-Air-Unified](https://github.com/CyberKnight-cmd/Urban-Air-Unified) | July 20 18:26:21 | July 28 05:11:52 | July 28 05:11:37 | ET AI Hackathon 2.0 | Older comparable |
| [Vayu](https://github.com/vacoder-iitg/Vayu) | July 20 17:38:48 | July 21 09:12:35 | July 21 09:12:31 | ET AI 2.0 | Older comparable |
| [DelhiAir.AI](https://github.com/Debdip70/air-pollution-weather-forecasting) | September 10 05:33:03 | September 10 05:44:30 | September 10 05:43:33 | SIH 2026, SIH2600082 | September code publication |
| [AISEHack-2026](https://github.com/Vetri-78640/AISEHack-2026) | April 4 17:20:29 | April 5 05:18:02 | April 5 05:17:55 | ANRF AI-SE Hack, Phase 2 Theme 2 | Older comparable |
| [Breathe Lahore](https://github.com/shehzadbashir/breathe-lahore) | August 29 08:40:31 | August 29 09:34:00 | August 29 09:33:53 | Smart City Hackathon Lahore 2026 | Near September, but no September push |

Date sources: [Atmos metadata](https://api.github.com/repos/premkadam7/ProjectAtmos), [Atmos commits](https://github.com/premkadam7/ProjectAtmos/commits/main/); [Urban metadata](https://api.github.com/repos/CyberKnight-cmd/Urban-Air-Unified), [Urban commits](https://github.com/CyberKnight-cmd/Urban-Air-Unified/commits/main/); [Vayu metadata](https://api.github.com/repos/vacoder-iitg/Vayu), [Vayu commits](https://github.com/vacoder-iitg/Vayu/commits/main/); [DelhiAir metadata](https://api.github.com/repos/Debdip70/air-pollution-weather-forecasting), [DelhiAir commits](https://github.com/Debdip70/air-pollution-weather-forecasting/commits/main/); [AISE metadata](https://api.github.com/repos/Vetri-78640/AISEHack-2026), [AISE commits](https://github.com/Vetri-78640/AISEHack-2026/commits/main/); [Lahore metadata](https://api.github.com/repos/shehzadbashir/breathe-lahore), [Lahore commits](https://github.com/shehzadbashir/breathe-lahore/commits/main/). Breathe Lahore's September 19 `updated_at` must not be reported as September development.

## 1. ProjectAtmos — closest complete platform comparable

**README summary.** Delhi ward forecasting, explanatory SHAP categories, enforcement tickets, intervention simulation, vulnerable-facility overlays and an English/Hindi assistant. Next.js/React/Leaflet/Recharts frontend; FastAPI backend; Optuna-tuned LightGBM quantiles; Gemini contextual assistant. Data inputs include Open-Meteo CAMS, Sentinel-2 NDVI and OSM. The README reports a 24-hour PM2.5 RMSE of 29.90 versus persistence 32.27, with 72-hour extrapolation, and claims 60 tests including latency checks. It describes eight API routes spanning forecast, attribution, enforcement, vulnerabilities, simulation, chat and health; setup requires separate Python/npm installations and an optional Gemini key. It reports ET AI Hackathon 2026 PS5. [Complete README](https://github.com/premkadam7/ProjectAtmos/blob/main/README.md)

**Implementation reality.** Their own technical summary says roughly 40–45km CAMS resolution produces just three distinct pollutant series across 29 station locations; approximately 290 mapped wards use nearest-neighbor filling. It explicitly discloses Delhi-only boundaries, proxy attribution and an independently trained 24-hour model rather than independent 48/72-hour models. [Technical summary](https://github.com/premkadam7/ProjectAtmos/blob/main/PROJECT_SUMMARY.md)

The forecaster reads cached latest features, obtains 24-hour quantiles, and builds other hours with interpolation/extrapolation and cosine variation. Unknown ward IDs fall back to the first feature row. Displayed PM2.5/PM10 are derived from AQI rather than independently forecast. Intervention inference zeros selected pollutants and scales the resulting difference by duration; this is model sensitivity, not validated causal policy impact. [Forecaster and simulator source](https://github.com/premkadam7/ProjectAtmos/blob/main/backend/models/forecaster.py)

**Threat to AirTwin — inference.** Very high overlap and a strong municipal decision workflow; satellite vegetation and real facility/population inputs make useful targets for AirTwin. AirTwin's direct multi-horizon design is a defensible distinction against their explicitly extrapolated longer horizons. Their reported RMSE cannot be compared numerically with AirTwin's MAE on a different target/dataset. Neither project's proxy source categories establish measured emissions attribution.

## 2. Urban-Air-Unified — broad orchestration competitor

**README summary.** Team Outlaws reports ET AI Hackathon 2.0 submission and a completed roadmap. FastAPI integrates XGBoost prediction with live 168-hour Open-Meteo windows, geospatial wind plumes, OSMnx searches within 2km for facilities/factories, TinyDB analytics, audio advisories and a LangGraph GPT-4o-mini supervisor. The repository separates backend orchestration from ML/agent research through submodules; cloning must be recursive, dependencies use `uv`, and agent routes need an OpenAI key. The README links architecture, API, ML and frontend handoff documentation. Its claim of production scalability/completion is self-description, not independently established deployment or load evidence. [Complete README](https://github.com/CyberKnight-cmd/Urban-Air-Unified/blob/main/README.md)

**Implementation reality.** The inference wrapper calls the live-data pipeline, but on exceptions generates random pollutant predictions and random source percentages/confidence under `Fallback_Mock_Node`. This fallback should not be mistaken for successful sensor/model operation. [Inference source](https://github.com/CyberKnight-cmd/Urban-Air-Unified/blob/main/unified_backend/app/services/ml_inference.py)

Its plume is a wind-directed polygon constructed with geodesic points, suitable for visualization; this bounded source does not solve or validate a concentration transport field. [Plume source](https://github.com/CyberKnight-cmd/Urban-Air-Unified/blob/main/unified_backend/app/services/plume_model.py)

**Threat to AirTwin — inference.** Strong on integration breadth, agent-assisted operations and audible citizen communication. AirTwin could distinguish itself through reproducible observed-target forecasting and transparent failure/status handling. No independently comparable accuracy or operational reliability result was established in this reading.

## 3. VAYU — strongest feature and demo breadth

**README summary.** A Next.js/TypeScript/Zustand platform for six Indian cities: maps/ticker, four-sector source attribution, 72-hour forecasts, inspector queues, policy toggles, multilingual advisories, exposure/economic counters and downloadable briefing videos. Claude and Groq route explanation/translation/video tasks with fallbacks; OpenAQ/WAQI, FIRMS, Open-Meteo and OSM are listed integrations. Setup uses npm and optional provider/sensor keys; missing keys or outages trigger seeded demo profiles. Economic loss is a disclosed illustrative population/AQI-scaled allocation of a national annual estimate, not direct city loss measurement. The repository description reports ET AI 2.0. [Complete README](https://github.com/vacoder-iitg/Vayu/blob/main/README.md), [repository/event metadata](https://api.github.com/repos/vacoder-iitg/Vayu)

**Implementation reality.** The inspected forecast endpoint initializes from seeded city AQI and adds explicit diurnal, wind, humidity and time factors to produce twelve six-hour intervals. Bounds widen with fixed formulas. This endpoint is rule-based projection, not demonstrated trained forecasting. [Forecast route](https://github.com/vacoder-iitg/Vayu/blob/main/app/api/aqi/forecast/route.ts)

The validation endpoint uses seven seeded daily values, four evaluation windows and synthetic forecast formulas. Its computed RMSE/persistence comparison is not an observed-station holdout backtest. [Backtest route](https://github.com/vacoder-iitg/Vayu/blob/main/app/api/validation/forecast-backtest/route.ts)

**Threat to AirTwin — inference.** High presentation/workflow threat: languages, city comparisons, economic communication and briefing exports. AirTwin has a clearer route to a forecasting evidence advantage if it foregrounds observed holdouts, persistence comparisons and honest uncertainty; VAYU's rule-based routes should not be ranked as proven superior ML.

## 4. DelhiAir.AI / AERO-Coupler NCR — September 2026 comparable

**README summary.** Reports SIH2026 SIH2600082, with citizen AQI/safety guidance and policymaker atmospheric profiles, fire maps, station network, GRAP simulation, alert dispatch and system-health views. Next.js/TypeScript/Tailwind/Zustand/Recharts frontend and a 60-second automated demo. It promotes pollution-weather coupling, inversion/ventilation metrics and a 72-hour forecast, while also explicitly describing bundled mock forecasts and zero-key offline operation. Production data sources are listed as FIRMS, Open-Meteo, CPCB and WRF-Chem. Its 45% blindspot, reduction examples and sub-20ms claims should be treated as scenario/presentation assertions, not verified scientific evaluation. [Complete README](https://github.com/Debdip70/air-pollution-weather-forecasting/blob/main/README.md)

**Implementation reality.** The Next.js forecast API directly returns `baseForecast72h` from mock data with `source: mock`. The FastAPI forecast endpoint says WRF-Chem integration is future work and returns empty data. The station endpoint varies stored readings with random/time factors and random coordinates, reporting `real_time_simulation`. FIRMS has an actual API request path, but reading that code is not a live integration test. [Frontend forecast](https://github.com/Debdip70/air-pollution-weather-forecasting/blob/main/app/api/forecast/route.ts), [backend source](https://github.com/Debdip70/air-pollution-weather-forecasting/blob/main/backend/main.py)

GRAP state recalculates through the bundled mock service. [Simulation store](https://github.com/Debdip70/air-pollution-weather-forecasting/blob/main/store/useSimulationStore.ts)

**Threat to AirTwin — inference.** High scientific storytelling and demo-design relevance, but the inspected forecasting paths are demonstrations. AirTwin should learn from its inversion explanation and short scripted demo, while differentiating using actual model evaluation. This is the one September-published repository in the six, but evidence identifies SIH, not HackMatrix.

## 5. Code4CleanAir / AISEHack-2026 — specialized ML comparable

**README summary.** Reports ANRF AI-SE Hack Phase2 Theme2, April2026. Forecasts sixteen PM2.5 hours from ten historical hours on a 140×124 Delhi-NCR WRF-Chem grid. ResGRU-UNet combines spatial encoding/skip connections and recurrent temporal decoding; progressive training creates stable/spike experts with asymmetric quantile loss. Blending and a nonlinear peak boost target extreme episodes. The README reports Kaggle score 0.8834, validation episode SMAPE0.1296 and correlation0.9856 for its top model; it links Kaggle checkpoints and notebooks, describes sixteen feature channels and recommends a T4-class GPU. These remain team-reported metrics rather than organizer-verified leaderboard placement. [Complete README](https://github.com/Vetri-78640/AISEHack-2026/blob/main/README.md)

**Implementation/document caution.** Model1 uses q0.90, 20/80 stable/spike blending and curvature divisor800; Model2 uses q0.85, 30/70 and divisor1000. Their model documentation reports maxima of 12,608.7 and 6,161.3µg/m³ respectively, making output sanity/calibration an important validation question, not proof of failure. [Model1 notes](https://github.com/Vetri-78640/AISEHack-2026/blob/main/models/model-1/README.md), [Model2 notes](https://github.com/Vetri-78640/AISEHack-2026/blob/main/models/model-2/README.md)

**Threat to AirTwin — inference.** The most substantive specialized model-design benchmark among these six for spatiotemporal episodes; less direct as an end-to-end municipal digital-twin product. Grid prediction, different horizons/data and different scoring prevent an accuracy ranking against AirTwin. Consider episode-sensitive evaluation before adopting extra model complexity.

## 6. Breathe Lahore — citizen engagement comparable

**README summary.** Reports a solo Smart City Hackathon Lahore2026 project. A dependency-free HTML/CSS/JS dashboard covers ten zones, recursive 48-hour OLS forecasts, scenario/risk-profile advisories, English/Urdu/RTL, phone subscriptions, citizen reports and community-action counters. A pure-Python reference pipeline exports CSV/model artifacts; optional IQAir ingestion and messaging gateways are documented. The README describes fourteen training days and a seventy-two-hour holdout with scenario RMSE40–72µg/m³ and R²0.76–0.84. It explicitly states sensor streams are seeded simulation, notification delivery is simulated/dry-run by default, and live ingestion/expanded sensors/API/policy dashboards form the roadmap. MIT license; no build/key needed for the demo. [Complete README](https://github.com/shehzadbashir/breathe-lahore/blob/main/README.md)

**Participation evidence.** The Devpost kit still contains placeholders for repository, screenshots and demo links. This supports submission preparation, not independent proof that a finished entry was accepted. [Submission kit](https://github.com/shehzadbashir/breathe-lahore/blob/main/docs/DEVPOST_SUBMISSION.md)

**Implementation caution.** The optional live script fetches an IQAir city response and writes it to JSON; it prints `mainus` as if it were a PM2.5 concentration, which requires field-semantics checking before trust. It does not by itself demonstrate an ingested longitudinal station dataset. [Live-fetch source](https://github.com/shehzadbashir/breathe-lahore/blob/main/ml/fetch_livedata.py)

**Threat to AirTwin — inference.** Strong benchmark for accessible public communication, citizen reporting and realistic offline demonstration. Its simulation-based prototype metrics are not comparable with AirTwin's observed-target evaluation; learned OLS does not make simulated input observations real.

## What AirTwin should take from this reading

These are product/model comparables, not evidence that the six are competing at HackMatrix. Prioritize Atmos for close feature comparison, Urban for operational integration, VAYU for presentation breadth, DelhiAir for September demo storytelling, Code4CleanAir for episode-model research and Lahore for citizen accessibility.

The most useful differentiation is a defensible evidence chain: observed station targets; horizon-specific persistence comparisons; season/episode failures; visibly separate observed, modeled and synthetic data; and policy scenarios described as sensitivity estimates unless causal validation exists. AirTwin's documented direct horizons help against Atmos extrapolation and VAYU/DelhiAir rule/mock paths, but its proxy attribution, fixed-weather scenario assumptions and synthetic exposure geography still need honest disclosure. These comparisons are analytical judgments based on the scoped sources, not tested performance rankings.
