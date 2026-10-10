# What supports the intervention comparison

| Component | Evidence | What AirTwin may claim |
| --- | --- | --- |
| Traffic, industry and dust categories | MPCB Pune July 2024 report; PCMC Climate Action Plan 2026, section 5.3 | Regionally relevant categories to investigate |
| Source fraction at a Bhosari cell | Selected OSM mapped geometry, distance, wind and hourly profiles | A proxy hypothesis, not a measured local fraction or active emissions inventory |
| Background | Shared-hour or recent historical concentration percentile | A modeled floor, not measured regional transport |
| 0.7 response, 0.6–0.8 sensitivity | Project assumptions | Illustrative response coefficients, not empirical calibration |
| ±20% source scaling and wider stress range | Project assumptions | Tests of dependence on assumptions |
| Population | WorldPop India 2020 modeled counts area-allocated to PCMC cells | Dated comparative exposure index, not a current census or people protected |
| Emission cut to concentration reduction | Additive equation under fixed weather | A hypothetical scenario, not a validated policy effect |

## Sources checked 28 September 2026

- [MPCB Pune final emission inventory and source-apportionment report, July 2024](https://www.mpcb.gov.in/sites/default/files/Establishment%20of%20MPCB/Seniority%20list/2014/Pune_Final_EI_%26_SA_Report_July_2024.pdf).
- [PCMC Climate Action Plan 2026](https://www.pcmcindia.gov.in/pdf/Climate%20Action%20Plan%202026.pdf), section 5.3. The indexed section says that PCMC draws on Pune district findings in the absence of a dedicated PCMC source-apportionment study. Full PDFs exceeded the research browser's size limit; category support was checked from indexed excerpts, not a complete review of either report.
- [US EPA dynamic evaluation](https://www.epa.gov/cmaq/cmaq-dynamic-evaluation-and-trend-analysis) explains comparing simulated concentration changes against observed changes and separating emission and weather effects. This is a validation method, not a source for AirTwin's coefficients.

No numeric fraction or response range has been copied from these reports into
the model. A Pune-wide PM10 inventory fraction cannot be substituted for a
Bhosari PM2.5 concentration share. Regional evidence supports the categories;
it does not calibrate our geometry or coefficients.

## Reproduce the ranking checks

```sh
.venv311/bin/python scripts/validate_interventions.py
```

Use `--offline --output /tmp/intervention-sample.json` for synthetic smoke testing.
The report records target provenance, snapshot, fingerprint, exact cuts,
independent source multipliers, independent response factors and three population
profiles (WorldPop-configured, uniform and inverse-density). The latter two are
hypothetical alternatives scaled to the same total. It includes example parameters
for every observed winner.

The configured-range experiment uses source multipliers 0.8/1/1.2, renormalizes
source shares, and varies each action's pass-through independently at 0.6/0.7/0.8.
The wider stress experiment uses 0.5/1/1.5 and 0/0.7/1. These are hypothetical
tests. A zero response asks what happens if an emission cut does not produce
the assumed concentration reduction.

Demo cuts: traffic 20%, industry 30%, dust 30%. The separate equal-cut case uses
30% for all three. Neither controls cost or feasibility.

Read [computed results](evidence/intervention_sensitivity.md). Winner counts are
counts on a chosen grid, not probabilities. Selecting Bhosari shows local changes
while ranked exposure benefits cover the full Pune-PCMC grid.

## Answer to judges

“We compare transparent hypothetical actions. Regional reports support the source
categories. Local weights and response coefficients remain assumptions. We test
whether the leading action changes when those assumptions change, and record the
parameters that cause a reversal. A pilot must validate the response before
these comparisons support policy.”

## Pilot needed to validate an effect

1. Partner with a facilities or environmental team to define one feasible action and its implementation dates.
2. Record action intensity and monitoring availability; agree on a matched comparison site or period before inspecting outcomes.
3. Collect before/after concentrations and weather, documenting missing readings and concurrent activities.
4. Estimate changes with weather and comparison-site adjustment; report uncertainty and confounders.
5. Replace only supported parameters and evaluate predictions on a separate period.

No pilot has been conducted. This protocol does not establish causality by itself.
