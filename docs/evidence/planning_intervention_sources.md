# Planning intervention evidence register

Reviewed 10 October 2026. This is a bounded primary-source review, not an exhaustive procurement or literature audit.

## What can currently be supported

The eight planner actions remain illustrative scenarios. Their costs, geographic response kernels, 24-hour response horizon and source-cut percentages are not verified local operating estimates. The companion `config/interventions-evidence.json` records documented unit costs as null and preserves the existing synthetic figures explicitly. No matching controlled local action study was verified in this search; this is a search limitation, not proof that none exists.

A policy citation supports the rationale for considering an action. It does not establish the action's cost or causal PM2.5 response. A city source share is not an intervention response, and a modeled sector scenario is not an observed treatment effect. Pune study results cannot automatically be assigned to individual PCMC neighborhoods.

## Verified primary sources and applicability

### Pune source apportionment and policy modeling, July 2024

[MPCB final Pune report](https://www.mpcb.gov.in/sites/default/files/Establishment%20of%20MPCB/Seniority%20list/2014/Pune_Final_EI_%26_SA_Report_July_2024.pdf), ES-2 / PDF page 3 and Chapter 6, printed pages 6.1 and 6.12 / PDF pages 179 and 190. The PDF was downloaded from MPCB and its text extracted locally because the web PDF renderer failed; 216 PDF pages.

The study sampled five Pune locations and used PMF for source apportionment. Its executive summary assigns 22% of PM2.5 to industry and 25% to fossil-fuel combustion. It also describes road dust as a major PM10 source. Chapter 6 evaluates cumulative sector-wide controls with dispersion modeling, including a five-year scenario. Those results are not one-day neighborhood PM2.5 experiments. Use this source as local context, not as a numerical calibration of the planner's traffic, dust and industry fractions or action cuts.

### Pune transport program budget, 2019

[MPCB Pune draft action plan](https://www.mpcb.gov.in/sites/default/files/pollution-index/severly-report/Pune_Action_Plan07112019.pdf), transport item 9, printed page 27 / PDF page 27.

The plan lists ₹10 crore for synchronized traffic / intelligent traffic systems, with a medium-term 2020 implementation timeline. This is a city program estimate associated with Smart City, PMPML and Traffic Police. There is no documented staffing, route length, days of operation or restriction-event denominator suitable for converting it into a Bhosari, Shivajinagar or Hadapsar one-day operating cost. No conversion was made; no inflation adjustment was made. Procurement, installation and operating components are not separated sufficiently for this purpose.

### Local construction dust-control budget, 2023

[MPCB-hosted Jorinco Specialities EIA executive summary, Bhare, Mulshi, Pune](https://www.mpcb.gov.in/sites/default/files/public_hearing/exe_summary/2023-10/Final%20Executive%20Summary__Jorinco%20Specialities%20Private%20Limited%20%28JSPL%29_Arin%20Bandyopadhyay_16.10.2023.pdf), printed page 23 / PDF page 24, construction air-pollution budget.

This project-proponent proposal lists ₹0.15 lakh capital and ₹0.5 lakh recurring expenditure for bundled construction air controls: sprinkling, stockpile covering, protective equipment and barricading. These are proposed site budgets, not awarded municipal road-service prices. The table supplies no comparable daily treated-road quantity and does not establish a daily recurrence unit. They were not transferred to Wakad, Pimpri or Katraj actions, prorated, or inflation-adjusted.

### Industrial remediation conditions, August 2021

[MPCB Consent Appraisal Committee booklets 7 and 8](https://mpcb.gov.in/sites/default/files/cac-meetings/minutes/WebhostlMoMBookletNo721092021.pdf), printed page 24 / PDF page 24, item 26, a Haveli, Pune facility.

The consent conditions require a fugitive-dust control upgrade within three months, supported by a ₹10 lakh bank guarantee. The guarantee is financial security for compliance, not a remediation price or inspector operating cost. This illustrates why an inspection does not guarantee next-day pollution reduction. Neither this guarantee nor facility capital investment was used to price Bhosari compliance or Chinchwad inspection.

### National operational guidance, 2019

[MoEFCC/CPCB National Clean Air Programme](https://prana.cpcb.gov.in/ncapDashboard/download_public_portal_file/NCAP_Report.pdf), printed page 32 / PDF page 45.

The dust-management action points address feasibility before mechanized sweeping, disposal of collected material and treated-water sprinkling. This supports recording equipment access, water availability and dust disposal as operational prerequisites. It does not supply a Pune unit rate or a quantified local PM2.5 effect. Historical guidance is evidence context, not a declaration of the current legal position.

## Action assumptions retained for reproducibility

| Action ID | Illustrative cost (INR per 24-hour scenario) | Assumed kernel radius (km) | Central source cut (%) | Sensitivity envelope (%) |
| --- | ---: | ---: | ---: | ---: |
| bhosari-traffic | 105,000 | 6 | 30 | 0–45 |
| shivajinagar-traffic | 95,000 | 5 | 25 | 0–37.5 |
| wakad-dust | 57,000 | 5 | 40 | 0–60 |
| pimpri-dust | 68,000 | 5 | 35 | 0–52.5 |
| bhosari-industry | 165,000 | 7 | 35 | 0–52.5 |
| hadapsar-traffic | 115,000 | 6 | 25 | 0–37.5 |
| katraj-dust | 44,000 | 5 | 30 | 0–45 |
| chinchwad-industry | 150,000 | 6 | 30 | 0–45 |

The envelope is an illustrative stress test, not an empirically estimated confidence interval: its lower end allows zero immediate benefit, and its upper end is 1.5 times the existing cut. Zero can represent failed implementation, an inspection without remediation or no detectable immediate ambient benefit. If a planner uses a narrower operating-response scenario for ranking, display that assumption separately and still disclose the zero-effect stress case; do not call that ranking a guaranteed benefit.

Cuts apply to the modeled local source-category contribution after geographic weighting. They are not percentages of total city PM2.5. Kernel radius is not a verified area served. The model horizon does not establish how long real intervention effects persist. The project limits of two traffic actions, two dust actions and one industry action are resource assumptions rather than surveyed agency capacities.

Traffic scope requires routes, diversions, police staffing and evaluation of displaced traffic. Dust scope requires road or lane length, repeat passes, equipment hours, water volume, collection and safe disposal. Industrial scope requires facility counts, verified noncompliance, specific corrective equipment and implementation lead time. These quantities are currently unknown; the proposed evidence map exposes those missing units rather than inventing them.

## Evidence needed before replacing scenario inputs

For each municipal action obtain an official BOQ, awarded unit rate or signed quotation that identifies the same service and jurisdiction. Record year, INR per crew-hour / lane-kilometer / vehicle-shift / inspected facility, exact quantity, contract term, taxes, fuel and equipment inclusion, and mobilization. Multiply the documented rate by an explicit operational quantity; retain both in the evidence register. Keep machine purchase and long-term capital remediation separate from daily service costs. Annual city spending cannot be divided by an invented number of actions.

For causal response obtain measured pilot or controlled local intervention results with pre/post time windows, untreated comparison sites, meteorology and traffic changes, pollutant identity and uncertainty. Calibrate source-emission changes separately from ambient concentration changes. Validate displacement, overlap and decay across actions before treating their combined benefit as a policy forecast.

Official procurement entry point: [PCMC tender portal](https://www.pcmcindia.gov.in/tender_options). Secondary tender mirrors and newspaper unit-rate claims were leads only, not accepted input evidence, because the matching official BOQ and scope were not verified during this review.
