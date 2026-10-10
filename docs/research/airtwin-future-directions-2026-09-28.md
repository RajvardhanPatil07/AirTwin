# Future directions for AirTwin

Research note, 28 September 2026. These are **proposals**, not features in the current build, and none is claimed to be globally unprecedented. The distinctive opportunity is to connect a forecast, a decision, new measurements, and a later audit in one public workflow. Source links below support feasibility or the need for safeguards; the particular AirTwin combinations are our synthesis.

## 1. A policy trial that grades its own forecast

Let an operator register a road-dust, traffic, or industrial action *before* it starts: location, timing, expected pollutant change, cost, weather assumptions, and a comparison area. Freeze the pre-action prediction. Afterward, compare observations in treated and matched untreated areas, adjust for weather and trends, and publish an effect estimate with uncertainty and a plain-language verdict. A result that contradicts the scenario should update its assumptions rather than disappear from the dashboard.

This extends the current hypothetical scenario engine into a prospective accountability study. It requires real action logs, adequate monitoring, a defensible comparison area, and statistical review. It must never present a simple before/after difference as causal proof. [EPA's accountability framework](https://assessments.epa.gov/risk/document/%26deid%3D364752) discusses the chain from intervention to emissions, exposure, and health; an [original difference-in-differences study](https://pubmed.ncbi.nlm.nih.gov/35842143/) uses geographically and meteorologically selected controls to assess air-pollution policy effects.

## 2. A sensor mission planner driven by what the model does not know

Show where an extra calibrated PM2.5 sensor or a short mobile survey would most reduce uncertainty, especially near schools, busy roads, industrial edges, and blank parts of the map. For each suggested site, show the question it would answer, expected coverage gain, power/security needs, and a nearby reference site for collocation. After deployment, compare the actual information gained with the recommendation.

This is an original decision loop built on AirTwin's forecast and spatial uncertainty; the site ranking would need a new, validated method. [EPA's Enhanced Air Sensor Guidebook](https://www.epa.gov/air-sensor-toolbox/how-use-air-sensors-air-sensor-guidebook) covers network design, siting, collocation, correction, and quality assurance. [EPA's siting guide](https://www.epa.gov/air-sensor-toolbox/guide-siting-and-installing-air-sensors) explains why placement and comparison with reference monitors matter.

## 3. Cleaner journeys with honest exposure estimates

Compare walking, cycling, and transit routes by time-varying *estimated* pollution exposure, travel time, accessibility, and road safety. A user could ask whether leaving 30 minutes later or taking a quieter parallel route changes the modeled exposure. Show the measured segments, interpolated segments, and uncertainty separately. A school route could emphasize crossings and safe paths rather than optimize PM2.5 alone.

This needs a much finer, independently checked street-level pollution surface, route data, and privacy-preserving handling of origins and destinations. A 12×12 city grid cannot justify street-by-street advice. [WHO's route brief](https://cdn.who.int/media/docs/librariesprovider2/euro-health-topics/air-quality/airqualitybriefs-pub-proposed-distribution_250924_bk_14-45-%281%29.pdf?download=true&sfvrsn=bc9aba83_1) discusses route and timing choices together with safety and access; [WHO's broader report](https://www.who.int/publications/i/item/WHO-EURO-2024-9115-48887-72806) cautions that evidence and feasibility vary by setting.

## 4. A budgeted, uncertainty-aware intervention portfolio

Let planners choose a budget and constraints, then compare packages of road, industrial, and dust actions across plausible weather, source-response, and implementation assumptions. Report the range of estimated concentration change, the worst affected neighborhoods, cost, and who gets the benefit. Add a fairness guardrail: a plan cannot improve the city average while leaving high-exposure communities worse off. Include a “what evidence would change this recommendation?” view.

This needs local cost and activity inventories, defensible response functions, and validated demographic data; the current scenario shares are proxies. The portfolio design is our synthesis. [WHO notes that exposure and vulnerability differ across social groups](https://www.who.int/teams/environment-climate-change-and-health/air-quality-energy-and-health/sectoral-interventions/ambient-air-pollution/health-equity). [EPA's air-quality management guidance](https://www.epa.gov/air-quality-management-process/managing-air-quality-ongoing-evaluation-progress) explicitly asks whether controls achieve goals and what their costs and benefits are.

## 5. Cross-check local stories with independent atmospheric evidence

For a large traffic or industrial intervention, add a separate “independent signal” panel: ground-station trends, wind direction, and Sentinel-5P tropospheric NO₂ columns. It could flag when a claimed local improvement is inconsistent with these signals, or when cloud cover and spatial resolution make a cross-check impossible. This would be a hypothesis check, never a direct conversion of satellite NO₂ into street-level PM2.5 or source attribution.

The idea combines existing ground forecasts with a different observation type. [Copernicus documents Sentinel-5P atmospheric products](https://documentation.dataspace.copernicus.eu/Data/SentinelMissions/Sentinel5P.html) and [the NO₂ column product and units](https://documentation.dataspace.copernicus.eu/APIs/SentinelHub/Data/S5PL2.html). [CAMS global forecasts](https://www.ecmwf.int/en/forecasts/datasets/cams-global-atmospheric-composition-forecasts-0) provide broader atmospheric context at roughly 40 km resolution, not neighborhood truth. NASA TEMPO should **not** be proposed as a Pune data source: [its field of view is North America](https://science.nasa.gov/mission/tempo/).

## 6. A forecast flight recorder

Every forecast and recommendation could keep a small public record of input observation times, provider/model versions, issue time, missing sensors, fallback path, assumptions, and later observed error. The interface could then answer: “What did AirTwin know at 8 a.m., and what changed by noon?” An automatic abstain state would avoid detailed claims when inputs are stale or coverage is weak.

This is a product design proposal, not a claim that current provider data is real time. It is feasible because [OpenAQ exposes measurement timestamps](https://docs.openaq.org/resources/measurements) and [sensor coverage and last-measurement metadata](https://docs.openaq.org/resources/sensors). [CAMS documents evaluation and quality-assurance reports](https://confluence.ecmwf.int/pages/viewpage.action?pageId=673323626); AirTwin would still need to version its own local artifacts and validate operational availability.

## Suggested README treatment

Feature four ideas in a concise **Future directions** section: policy trial, sensor mission planner, cleaner journeys, and budgeted/equitable portfolio. A short closing line can mention independent satellite checks and the forecast flight recorder. Link to this note for evidence and constraints. Keep all verbs prospective (“could,” “would require”), and label the current forecast and scenario engine separately from these proposals.
