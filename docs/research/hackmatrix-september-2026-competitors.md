# AirTwin competitor review: September 2026 / HackMatrix 5.0

Research date: 28 September 2026. Scope: public GitHub projects matching AirTwin's urban air-quality forecasting, explainability, GIS and intervention workflow, prioritizing September 2026 and HackMatrix 5.0.

## Main finding

Two close September candidates emerged: **Shubham21042007/Hackmatrics** explicitly identifies **ENR01, Pune/PCMC**; **Krushna-Pisal/AeroTwin** documents a working Pune PM2.5 modeling pipeline. Neither can be called an organizer-confirmed registered HackMatrix 5.0 participant from the public evidence reviewed. Hackmatrics is a particularly strong problem-statement match; AeroTwin is a close technical competitor whose event affiliation remains unknown.

Do not interpret “close competitor” as “better model.” No competitor was installed or benchmarked independently. Their reports describe different data, stations and dates from AirTwin, so raw MAEs cannot establish superiority.

## September candidate inventory

| Project | GitHub repository created / last pushed, UTC | Evidence of participation | Assessment |
| --- | --- | --- | --- |
| [Hackmatrics](https://github.com/Shubham21042007/Hackmatrics) | 25 Sep / 25 Sep 2026 | README names ENR01 and Pune/PCMC; PRD says hackathon. No organizer confirmation | Most direct problem-statement match; public snapshot describes planning/data collection |
| [AeroTwin](https://github.com/Krushna-Pisal/AeroTwin) | 27 Sep / 27 Sep 2026 | No event statement in README reviewed | Closest implemented local forecasting competitor |
| [VayuShield](https://github.com/sharathrachar/VayuShield) | 27 Sep / 27 Sep 2026 | README says designed for SIH | Secondary September comparable; vehicle-emission indicators are a distinct angle |
| [EcoTwin AI](https://github.com/Roshni61/innovation4) | 1 Sep / 1 Sep 2026 | README says international hackathon, unnamed | Broader sustainability prototype; weaker PM2.5 forecasting overlap |
| [HackMatrix-ENR03](https://github.com/jahnavikulkarni-ai/HackMatrix-ENR03) | 27 Sep / 27 Sep 2026 | Explicit HackMatrix 5.0 ENR-03 claim | Same-event adjacent environmental project, different problem: microplastics |

Dates above are repository metadata obtained through GitHub search/API, not proof of when development started or completed. [GitHub repository API](https://docs.github.com/en/rest/repos/repos#get-a-repository). Check a project's current metadata using its `/repos/OWNER/REPO` endpoint; for example [AeroTwin metadata](https://api.github.com/repos/Krushna-Pisal/AeroTwin) and [Hackmatrics metadata](https://api.github.com/repos/Shubham21042007/Hackmatrics).

## 1. Hackmatrics: read the README and full PRD

Sources: [README](https://github.com/Shubham21042007/Hackmatrics/blob/main/README.md), [PRD](https://github.com/Shubham21042007/Hackmatrics/blob/main/PRD.md).

**Problem and audience.** The proposed system serves urban decision makers with a map-led workflow: observe pollution, forecast PM2.5, explain model influences, simulate controls, compare outcomes and validate forecasts. Pune/PCMC is the pilot; ENR01 is explicitly named.

**Planned MVP.** Multi-source ingestion; hourly PM2.5 prediction initially at 1/3/6 hours with 12/24 hours optional; hotspot maps; weather/traffic/industrial indicators; grouped SHAP explanations; traffic restriction, industrial controls and combined intervention; historical chronological validation; clear observed/forecast/scenario labels. Replay, uncertainty, impact maps, emerging hotspots and alerts are recommended extras. Satellite/IoT, optimization, natural-language querying, multiple cities and multiple pollutants are stretch work.

**Model and scenario design.** The PRD proposes persistence first, then linear regression, random forest and XGBoost/LightGBM. Traffic features can include road density, proximity and time-of-day proxies; industry features can use zones, distances and activity indicators. Scenarios would alter relevant inputs and rerun the trained predictor. SHAP values would be grouped into traffic, industry, weather, history, temporal and spatial categories. The PRD correctly separates predictive influence from causal source apportionment; rerunning a predictor would still not independently prove policy effectiveness.

**Data/architecture.** Proposed OpenAQ/CPCB/data.gov.in targets, Open-Meteo weather, OSM geography, municipal traffic or documented proxies and industrial GIS. Proposed React/TypeScript map frontend, FastAPI backend, tree models/SHAP, GeoPandas/Shapely and PostgreSQL/PostGIS. The PRD specifies timestamps, units, sources, quality status, temporal splits, model metadata and API routes. These are requirements, not evidence that those components run.

**Presentation.** The PRD contains a first-round presentation plan and a fixed demo journey covering map, hotspot, forecast, explanation, three scenarios and validation. Example concentrations and reductions are explicitly illustrative.

**Current evidence and threat.** The README says data collection and verification before prototype development. The inspected main-branch tree lists README.md and PRD.md. That supports a strong plan, not a demonstrated application. My assessment: high conceptual overlap, limited demonstrated implementation in this snapshot. AirTwin should demonstrate its integrated working workflow and measured baseline comparison rather than claim uniqueness for the idea alone.

## 2. AeroTwin: technical competitor worth watching

Sources reviewed: [README](https://github.com/Krushna-Pisal/AeroTwin/blob/main/README.md), [data policy](https://github.com/Krushna-Pisal/AeroTwin/blob/main/docs/data_policy.md), [initial evaluation](https://github.com/Krushna-Pisal/AeroTwin/blob/main/docs/model_evaluation.md), [V2 evaluation](https://github.com/Krushna-Pisal/AeroTwin/blob/main/docs/v2_model_evaluation.md), [horizon analysis](https://github.com/Krushna-Pisal/AeroTwin/blob/main/docs/forecast_horizon_analysis.md), [winter errors](https://github.com/Krushna-Pisal/AeroTwin/blob/main/docs/winter_error_analysis.md), [weather-source evaluation](https://github.com/Krushna-Pisal/AeroTwin/blob/main/docs/weather_source_evaluation.md).

**Implemented scope.** Its README provides download, inspection, cleaning, model-training and backtest commands for Pune PM2.5, using CPCB observations republished by OpenCity. It explicitly excludes the older unlabelled wide matrices from training and says the frontend is outside this step. This makes it a substantive data/model competitor, but does not establish an end-to-end map/scenario product.

**Forecast evidence.** Initial global XGBoost +24-hour model uses PM2.5 lags, calendar/station features and available weather. V2 broadens evaluation to ten stations, with training before January 2025, validation January–June and test July–December 2025. Reported test MAE: persistence **11.52**, lags-only **11.88**, and lags plus weather **12.41 µg/m³**. No V2 candidate passes its promotion criteria; the report retains persistence as the production 24-hour forecast. These are repository-reported results, not rerun here.

**Where it is strong.** The documentation examines source labels, missing weather, station exclusions, time boundaries, monthly/station-wise performance and failure to outperform persistence. Its horizon report finds a stronger 12-hour candidate, showing that model usefulness varies by horizon. This evidence discipline could appeal to technical judges even without a broad dashboard.

**Limits that matter.** The V2 evaluation says traffic, industry, dust and citizen observations are not used. Its stated +0000 timestamp versus apparent local diurnal cycle remains unresolved; no timezone relabeling is claimed. Winter analysis exposes large missed peaks and December degradation. The README excludes the frontend from the documented step. Earlier documents describe older model versions; use V2 for the latest reported production decision rather than mix their metrics.

**Comparison with AirTwin.** AeroTwin's raw errors are not directly comparable to AirTwin's winter holdout because the station selection and periods differ. AirTwin's strongest documented differentiation is the integrated map, forecast/replay, intervention comparison and visible provenance. AirTwin's source shares and response coefficients remain assumptions. This comparison was written before the sourced PCMC WorldPop/OSM update; the statewide and fallback views still use synthetic proxies. Neither project's documentation establishes causal intervention validity.

## 3. VayuShield: September comparable from SIH

Source: [full README](https://github.com/sharathrachar/VayuShield/blob/main/README.md).

The README describes ambient pollutants, meteorology, traffic congestion, NASA fire hotspots and aggregated Pollution Under Control certificate indicators feeding a grid-level XGBoost forecast at 24/48/72 hours. Its documented stack combines React/Leaflet/Recharts, a Java Spring Boot backend, MySQL/H2 and a Python FastAPI ML service. It supplies an eleven-step judge demo covering the map, inversion/traffic, PUC verification, forecasts, contributor ranking and alerts.

Its distinctive angle is combining air quality with aggregate vehicle-emission inspection information. However, the README explicitly refers to demo certified PUC records; architecture and feature descriptions alone do not validate historical forecast skill, uncertainty coverage or live feed completeness. The stated event is SIH, not HackMatrix 5.0. Treat it as product-positioning inspiration and an unbenchmarked comparable.

## 4. EcoTwin AI: broader September hackathon prototype

Source: [full README](https://github.com/Roshni61/innovation4/blob/main/README.md).

Team Cloud_Coders describes a campus/smart-city environmental twin with a Leaflet hotspot map, AQI/carbon/green-cover dashboard, climate alerts, tree/solar/waste scenarios, a carbon calculator, SDG tracker, downloadable report and chatbot. It is a React/Vite static frontend. Its own documentation describes real-time-style KPIs, simulated alerts and a mockData.js module. The sensing/modeling pipeline is described at a conceptual level; the README supplies no historical forecast evaluation.

Its strength is breadth and presentation. Its overlap with AirTwin is maps and scenarios rather than documented pollutant forecasting evidence. The hackathon is unnamed and HackMatrix participation is unverified.

## 5. Same-event adjacent project: microplastics

[HackMatrix-ENR03 README](https://github.com/jahnavikulkarni-ai/HackMatrix-ENR03/blob/main/README.md) explicitly states a portable microplastics screening system for HackMatrix 5.0 ENR-03. The short README does not support claims about accuracy, deployed hardware or a working demo. This is an environmental-track neighbor, not a same-problem air-quality competitor. Registration/finalist status was not confirmed through the organizer.

## Stronger external benchmarks

The separate [six-project technical review](air-quality-competitors-2026-09-28.md) covers ATMOS, Urban-Air-Unified, VAYU, DelhiAir.AI, Code4CleanAir and Breathe Lahore. Only DelhiAir.AI's checked created/pushed dates are in September 2026; the rest are earlier projects. They are other-hackathon comparables, not established HackMatrix 5.0 rivals.

## What this means for the AirTwin pitch

These are my judgments from the reviewed documentation, not organizer rankings:

1. The general forecast + explain + simulate idea is shared. Lead with a concrete Pune/PCMC decision and a working before/after comparison.
2. Demonstrate model value against persistence on the same held-out rows, including stations/seasons where it loses. A complex model is not automatically a better forecast.
3. Separate TreeSHAP forecast explanations from heuristic source shares and modeled interventions. Explain how each is computed.
4. Show uncertainty and ranking sensitivity. Synthetic population cannot establish people protected or health outcomes.
5. Show data origin and freshness. A recent Git push is not a recent environmental observation.
6. Present working evidence before stretch features. Competitor PRDs can list the same ideas; integrated behavior is more persuasive.

## Search coverage and limits

Searches combined web search with public GitHub repository search, including README content: `"HackMatrix 5.0" in:readme` (9 matches), `"HackMatrix" in:readme created:2026-09-01..2026-09-28` (18), `"HackMatrix" in:readme pushed:2026-09-01..2026-09-28` (24), `"ENR01" in:readme` (3), `"ENR-01" in:readme` (7), `"environmental digital twin" in:readme created:2026-09-01..2026-09-28` (10), and broader Pune/twin queries. The relevant result sets reported `incomplete_results=false` and fit on one 100-result page. Counts refer to the checked query snapshots, not the number of eligible competitors.

False positives included a Linux desktop named HackMatrix, unrelated ENR matches, event trackers, different HackMatrix editions and other problem tracks. The official [HackMatrix website](https://hackmatrix.gfgpccoe.in/) did not expose a readable public participant list in the retrieved page. Public repository search cannot reveal private repos, unlabelled submissions, deleted projects or unpublished teams. Therefore this is a sourced shortlist, not an exhaustive or confirmed roster. Some GitHub searches briefly hit rate limits; successful subsequent queries supplied the result sets above.

Local AirTwin comparison was based on directly read README and hackathon-readiness documentation. Its graph index generation was 27 Sep 2026 19:18 UTC; coverage flagged README metadata changes and excluded docs, so graph absence was not used to assess local implementation.
