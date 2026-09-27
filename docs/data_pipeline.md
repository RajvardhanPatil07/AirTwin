# Data pipeline and dataset contract

## Execution

`bash scripts/pipeline.sh --offline` runs OpenAQ fetch, weather fetch and dataset
build in order. Each script has an explicit offline mode and sample fallback.
`--live` requests providers; live coverage has not been validated in this release.
The frontend fixtures do not load this output yet.

## Stages

| Script | Input | Output | Failure behavior |
| --- | --- | --- | --- |
| fetch_openaq.py | Key, bbox, last 18 months by default | data/raw/air_quality.csv | Keep partial sensor records; no usable result → sample |
| fetch_weather.py | Target timestamps, city centroid | data/raw/weather.csv | Archive failure/missing input → sample weather |
| build_dataset.py | Target/weather CSVs | data/processed/dataset.parquet | Sparse targets → CAMS; unavailable path → full sample |
| generate_sample.py | Deterministic synthetic recipe | data/sample/dataset_sample.csv | Explicit regeneration only |

Raw/processed files are ignored. Normal builds preserve the committed fixture.
`build_dataset.py --update-sample` deliberately replaces it with a bounded subset;
review provenance and diff before committing such a change.

## Target schema

| Column | Meaning |
| --- | --- |
| timestamp | ISO datetime, normalized to Asia/Kolkata and floored to hour |
| station_id | OpenAQ sensor ID string, CAMS centroid ID, or fictional sample ID |
| station_name | Provider/location name, not evidence of measured provenance |
| latitude / longitude | Coordinates in decimal degrees |
| pm25 | PM2.5 concentration in µg/m³ |
| source_type | observed, modeled or synthetic target provenance |
| target_provider | OpenAQ, Open-Meteo CAMS or synthetic recipe identification |

OpenAQ PM2.5 units are checked; unsupported units are skipped, not converted
silently. Invalid timestamps/coordinates/targets are dropped. PM2.5 below zero
or above 1000 is removed; zero and 1000 are accepted by the current cleaning rule.
Duplicate hours with the same identity/provenance are averaged. Missing hours
remain absent. Feature construction must later account for those gaps explicitly.

## Weather schema

| Column | Units |
| --- | --- |
| temperature_2m | °C |
| relative_humidity_2m | % |
| wind_speed_10m | m/s |
| wind_direction_10m | degrees |
| precipitation | mm |
| weather_source_type | modeled, synthetic or missing |
| weather_provider | Provider/recipe name, or unavailable |

Weather timestamps are joined many-to-one; duplicate weather hours retain the
first record. Missing weather remains null with explicit missing provenance.
Centroid weather is shared across all targets. Boundary-layer height and forecast
weather are not currently fetched.

## Coverage and CAMS fallback

A sensor with at least 720 cleaned observed rows passes the initial threshold.
This does not check continuous coverage, recent coverage or winter coverage.
When observed data pass, only observed targets are retained. When insufficient,
CAMS requests 92 past days with a one-day forecast allowance; dates from the last
five days onward are excluded before export. This is recent modeled output,
not 12–18 months of historical observed readings.

CAMS also fetches matching centroid weather. Any failed build path falls back
to the complete synthetic sample. Logs report final row count, target source
counts and missing weather count. No trained model consumes the output yet.

## HTTP behavior

Shared requests use a 45-second timeout and up to four attempts. HTTP 429/5xx
retry delays are bounded; Retry-After is capped at 60 seconds. Pagination requests
1000 rows per page until empty/short results or the reported count is reached.
A real provider shape/API change may still trigger sample fallback: inspect logs
rather than assuming successful execution means observed data were downloaded.

## Offline fixture

The sample has 2,952 synthetic hourly rows from October 2025 through January 2026
at one fictional centroid location. It is below 1 MB. It supports pipeline testing
and future split mechanics, not city forecasting claims. Target and weather labels
are synthetic independently. Regenerate only deliberately and inspect the result.

## Implemented model and forecast-weather path

`fetch_weather.py` also fetches forecast context and archived previous-run weather
for lead times 24/48/72 hours. Archive valid timestamps are shifted back by the
lead time before joining at model issue time. Columns are
`forecast_24_temperature_2m` and the analogous horizon/variable names. Missing
archive values use issue-weather persistence during feature building. Future
realized reanalysis is never shifted into horizon features.

`backend/scripts/train_model.py` trains direct LightGBM/quantile models, evaluates
a separate chronological holdout, runs purged TimeSeriesSplit, saves ignored
artifacts/metrics and generates docs/model_card.md. `scripts/run_all.sh` executes
fetch → build → train → serve. Startup regenerates artifacts if necessary without
silently claiming a real-data model when only the synthetic sample is available.


## Dense Pune + PCMC runtime map

The city runtime deliberately separates **measurement density** from **display
resolution**.

- OpenAQ remains the observed PM2.5 anchor source.
- The runtime now keeps each station's freshest reading inside the configured
  maximum-age window instead of requiring all stations to report in the same
  exact hour.
- Interpolation applies spatial IDW plus exponential recency decay with a
  configurable 6-hour half-life, so a stale sensor contributes less than an
  equally distant fresh sensor.
- The Pune + PCMC grid is 48 × 48 (2,304 MODELED cells), up from 12 × 12. This is display/model resolution, not sensor count.
- Every station preserves its own observation timestamp. Grid cells remain
  MODELED and must never be described as 576 physical sensors.
- Centroid weather remains a limitation of the current training dataset; denser
  station-specific meteorology is future work.

This improves useful spatial density without inventing observations.


## Sparse-anchor scenario background

With only one spatial PM2.5 anchor, a spatial 15th-percentile background equals
the station itself. That leaves zero local excess and makes every intervention
mathematically produce a 0% reduction. When fewer than three spatial anchors are
available, AirTwin now uses the 15th percentile of the previous 30 days of target
history as an explicitly MODELED background fallback, capped at the lowest current
anchor. This enables a meaningful offline/sparse-data scenario while remaining a
stated assumption rather than a measured chemical background concentration.
