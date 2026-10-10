# Pune–PCMC live data and provider choices

AirTwin supports one bounded urban area: Pune and Pimpri-Chinchwad, including the reference locations inside the configured Pune–PCMC bounding box. This is urban model coverage, not a claim of complete Pune district coverage or neighborhood measurement resolution.

The backend refreshes Pune provider context every 15 minutes while running; the dashboard reads the cached results every 30 seconds. It samples CAMS/Open-Meteo at 25 named reference locations, fetches weather, and discovers observed OpenAQ PM2.5 monitors. Provider-published IITM AQI indices are a separate observed feed and never converted to PM2.5.

CAMS remains modeled with approximately 45 km source resolution. Historical LightGBM evaluation and missing-sensor replay use a separate sourced dataset; they do not validate current CAMS forecasts. Measurements preserve their original timestamps. Failed refreshes retain the last labeled cache. No statewide refresh, region selector or statewide API is supported.

Traffic, dust and industry source contributions and intervention responses are explicitly assumed proxies; this build does not ingest measured live traffic counts or continuous industrial emissions. See the [final-round workflow](final_round_workflow.md) and [data sources](data_sources.md).

## Recommended provider stack

| Provider | Data / provenance | Free or inexpensive access | Use in AirTwin |
| --- | --- | --- | --- |
| CPCB/CAAQMS via data.gov.in | Indian monitoring-station air quality; check timestamps and original units | Public catalog/API with account key | Best next observation adapter; not integrated yet |
| OpenAQ v3 | Station concentrations with upstream provider metadata | Key-based access; coverage/freshness varies | Integrated historical PCMC data and Pune–PCMC monitor discovery |
| Open-Meteo + CAMS | Modeled concentrations, weather and forecasts | Noncommercial free tier: 10,000 calls/day, 300,000/month; no uptime guarantee | Integrated Pune–PCMC modeled coverage and weather |
| OpenWeather Air Pollution | Modeled current, forecast and historical pollutants | Free plan includes Air Pollution API; 60 calls/minute and 1 million/month | Useful secondary provider; not integrated |
| Google Maps Air Quality | Aggregated/model-derived air quality | Global list: 10,000 monthly free events, then $5/1,000 in first paid tier; billing required | Optional alternative; not integrated |
| NASA FIRMS | Satellite fire detections, not ground PM2.5 | Free MAP_KEY | Next burning/upwind-fire proxy; not integrated |
| WorldPop | Modeled population estimates | Open datasets with dataset-specific attribution | India 2020 1 km counts integrated for PCMC grid |
| OpenStreetMap | Roads and land-use proxies, not measured traffic flow | ODbL open data; respect endpoint usage policy | Selected PCMC road/land-use geometry integrated |

Sources: [CPCB catalog](https://www.data.gov.in/resource/real-time-air-quality-index-various-locations),
[Open-Meteo pricing](https://open-meteo.com/en/pricing),
[OpenWeather pricing](https://openweathermap.org/price),
[Air Pollution API](https://openweathermap.org/api/air-pollution),
[Google global pricing](https://developers.google.com/maps/billing-and-pricing/pricing),
[FIRMS API](https://firms.modaps.eosdis.nasa.gov/web-services/),
[WorldPop](https://www.worldpop.org/), [OSM licensing](https://www.openstreetmap.org/copyright).

For a cheap paid fallback, Google at 36 locations every three hours for a 30-day
month needs `36×8×30 = 8,640` requests, within the listed free cap. Hourly sampling
needs 25,920 requests: approximately `$79.60` above that cap at the global first-tier
price, before taxes and other usage. This is a calculated budget example, not a
quote. India-specific eligibility/pricing may differ. Open-Meteo paid subscriptions
support commercial use; check the current checkout price instead of assuming a
fixed monthly fee.

CPCB catalog values may represent pollutant averages or subindices. Verify each
resource's units before using them as a concentration training target. WAQI is a
useful display option, but its pollutant AQI subindices must not be treated as
µg/m³, and its caching/redistribution terms need review:
[WAQI API terms](https://aqicn.org/api/).

## GitHub repositories

[open-meteo/open-meteo](https://github.com/open-meteo/open-meteo) and
[openaq/openaq-api](https://github.com/openaq/openaq-api) provide provider code.
They do not independently guarantee live measurements or uptime. A repository
usually contains an API client, server code or dated datasets; use provider APIs
for live ingestion and retain provenance rather than relying on an unverified
“live CSV” repository.

## Gemini chat

Put `GEMINI_API_KEY` in the ignored root `.env`, then restart the backend.
`GEMINI_MODEL=gemini-3.5-flash-lite` is the configurable default. Gemini receives
selected-location history, weather, forecast, SHAP when available, source shares,
applied scenario cuts, backtest availability/metrics, regional references and
limitations. Follow-up conversation is bounded to eight messages.

Answers must return structured claims citing evidence IDs and source types.
Numeric tokens are checked against cited records, and each displayed claim has
its provenance badge. These checks do not establish semantic or causal truth.
Missing keys, quota failures, network errors or unverifiable answers return an
explicit error; no template answer is substituted.

Gemini 2.5 Flash-Lite has a free tier; listed paid text input is $0.10 per million
tokens and output $0.40 per million. Quotas depend on the account/model. Check
[official Gemini pricing](https://ai.google.dev/gemini-api/docs/pricing).

Live Gemini generation has not been verified because no Gemini key is configured
in this workspace. Mocked provider contracts and explicit no-key behavior are tested.
