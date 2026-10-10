# AirTwin Phase 1: Live observed-target ML (dev/mayuresh)

## Implemented behavior

Pune–PCMC continues to load CAMS and Open-Meteo model context in the background. When an OpenAQ API key is configured, the refresh discovers PM2.5 sensors even if their most recent measurement is older than 24 hours. Eligible sensors are used only for historical backfilling via the OpenAQ v3 /sensors/{id}/hours endpoint, using period.datetimeFrom.utc as the actual measurement hour. The 24-hour freshness gate remains mandatory for showing a station as a live observed point. The observation table rejects synthetic and CAMS data.

At actual OpenAQ monitor locations, AirTwin attempts LightGBM inference using an observed-target model artifact, 49 contiguous recent measured hours, and properly aligned CAMS and weather covariates. If prerequisites fail, the existing CAMS forecast remains available and is explicitly labeled with a fallback reason. Named CAMS points and IDW grid cells do not claim independent station-level ML accuracy.

The forecast API adds optional metadata: forecast_provider, model_id, model_version, issued_at, input_cutoff and fallback_reason. Existing client response shapes remain compatible.

## Required configuration

Install the pinned backend requirements with Python 3.11. Configure these environment variables locally in an ignored .env file or backend service:

    OPENAQ_API_KEY=YOUR_KEY
    DATABASE_URL=YOUR_POSTGRES_URI
    LIVE_REFRESH_ENABLED=1
    LIVE_REFRESH_SECONDS=3600
    LIVE_HISTORY_MAX_SENSORS=12

Never commit real credentials or paste them in chat. The existing model and user interface do not need a Supabase JavaScript client or an anon key. For Supabase, create an AirTwin project close to the backend region, open Connect in the Supabase dashboard and obtain a PostgreSQL connection URI. Use the correct direct/session/transaction pooling mode for your hosting setup.

On first successful hourly ingestion the backend creates a private airtwin.station_observations PostgreSQL table (not in Supabase's default exposed public schema). PCMC snapshots include history_sensor_candidates (OpenAQ station metadata, not measured values) and history_ingestion (number of attempted sensors, accepted hourly rows, and failures). Without DATABASE_URL, a local SQLite file is used under data/raw/live_station_history.sqlite3. SQLite on ephemeral cloud storage is not durable.

## Model artifact warning

The repository ignores backend/models/forecast.joblib. A clean environment might train a model using the committed synthetic sample. The live dispatcher rejects artifacts unless report.target_source_types is exactly observed and the artifact version matches the code.

For a real trained model, provide a verified observed-target dataset, run the existing live historical pipeline and model training, and verify its model card. Never claim accuracy from a synthetic-trained artifact. A trusted observed-target binary model must be provisioned separately for the live backend.

## Local tests

Run on branch dev/mayuresh, using the repository root:

    python -m pip install -r backend/requirements.txt
    python -m pytest backend/tests/test_live_phase1.py -q
    python -m pytest backend/tests -q
    python scripts/check_repository.py
    python scripts/dev.py

Inspect these local endpoints:

- http://127.0.0.1:8000/api/health
- http://127.0.0.1:8000/api/stations?region=pcmc
- http://127.0.0.1:8000/api/forecast?region=pcmc&location_id=openaq-123&hours=24 (replace 123 with a real observed sensor ID)

Inspect forecast_provider, model_id, fallback_reason, history_source_type, issued_at and input_cutoff. The CAMS provider branch will not expose live LightGBM's SHAP or historical confidence bands.

## Notes on data freshness, cost and reliability

- The first-use PostgreSQL schema/table creation is guarded by a transaction-scoped advisory lock so simultaneous history workers or backend processes cannot race to create the same schema. Failed history operations may be request failures or persistence failures; inspect backend traces before attributing them to OpenAQ.
- OpenAQ data may be delayed, incomplete, absent, or rate-limited. A historical backfill does not make a stale station live. The 49-hour no-gap requirement and live freshness gate remain strict in this first version.
- Hourly historical measurements are different from the latest unaggregated observation.
- Current CAMS context is modeled, not 25 independent local monitors.
- Current provider refresh is hourly by default (minimum 15 minutes) and runs only while one Python backend scheduler is running.
- Changing frontend polling intervals will not make providers publish new measurements more quickly.
- Live uncertainty coverage needs independent operational verification. The historical model card does not validate current CAMS provider forecasts.
- If a production DB connection fails, do not silently claim that its history has been saved.
- No Supabase project or remote database was modified as part of this branch commit.


## One-time measured-history backfill and observed-target training (Windows)

The hourly server refresh is intentionally cheap (96 hours on first use; then
8 hours). It does **not** acquire long-range historical data or change stale
measurements into live data. From the repo root with a working Supabase connection:

```powershell
python backend/scripts/backfill_openaq_history.py --days 45 --max-sensors 23
python backend/scripts/export_observed_history.py --days 90 --min-station-hours 720
python backend/scripts/fetch_weather.py
python backend/scripts/build_dataset.py
python backend/scripts/train_observed_model.py
```

The first command requests paged genuine OpenAQ `/hours` records, keeps
individual station identities, and stores only observed PM2.5 in private
PostgreSQL. Maximum lookback is 90 days (matching persistence retention).
The second command aborts without overwriting existing training input unless
a station has at least 720 distinct actual observed hours; it never exports
modeled or synthetic PM2.5 as observed.

Inspect `backend/models/metrics.json` and
`docs/model_card.md` to verify that `target_source_types` is exactly
`["observed"]`, with a chronological holdout and improvement against
persistence. The weather script uses separately labeled reanalysis inputs.
Before treating validation as representative, inspect missing weather data
and gaps in the observed target timeline. If external weather requests fail,
do not mistake the fallback sample for weather reanalysis.

Even when this trains an observed-target model, serving it live requires an
OpenAQ station with a fresh measurement and a complete 49-hour recent window,
plus correctly aligned CAMS/weather features. No amount of backfilling
fixes an upstream source publishing data days late. The model artifact is
ignored by Git and must be provisioned independently to any deployed backend.


## Optional historical observed monitor map overlay

The dedicated `GET /api/observed-history?region=pcmc` endpoint returns the
latest stored genuine PM2.5 hour per station **only when older than 24 h**.
It reads the same private Supabase table, or local SQLite when no database is
configured, and reports each monitor's timestamp and age in hours. The
frontend offers an opt-in **Past readings** map layer with purple outlined
markers and an explicit `OBSERVED · HISTORICAL (NOT LIVE)` tooltip.

These historical observations never enter the live stations endpoint,
current hotspot colors, live coverage counts, scenarios or operational model
inference. If Supabase is temporarily unreachable the overlay disappears
without breaking the modeled main dashboard.

### Fail-closed observed model training

The observed-specific training entrypoint refuses to overwrite a working model
if the processed targets are not **exclusively OBSERVED OpenAQ PM2.5**, if
there are fewer than 720 distinct measurement hours for the best-covered
station, or if its weather inputs are synthetic/missing entirely.
It uses the existing chronological held-out validation from `model.train`,
and prints its measured-versus-persistence error after training.
The general `train_model.py --offline` remains available solely for
separately labeled offline synthetic demonstration testing.

## Transient provider HTTPS failures

The live Pune/PCMC and Maharashtra CAMS/Open-Meteo refresh, and OpenAQ
requests called through `state_data.get_payload`, retry HTTPS connection
resets (including Windows WinError 10054), timeouts, HTTP 429, and HTTP
5xx with a maximum of four attempts and bounded backoff. Bad credentials,
HTTP 400/401/403 and other non-retryable requests fail immediately.

If retries are exhausted, the existing background refresh keeps the
last **timestamped** provider cache and adds a warning; it must not
relabel the cached CAMS values as fresh or create made-up observations.
A successful `/api/health` indicates the API responds, not that
the upstream providers necessarily succeeded on the most recent refresh.
