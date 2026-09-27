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
