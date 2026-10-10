# AirTwin Phase 1: Live observed-target ML (dev/mayuresh)

## Implemented behavior

Pune–PCMC continues to load CAMS and Open-Meteo model context in the background. When an OpenAQ API key is configured, the refresh additionally backfills real hourly station measurements via the OpenAQ v3 /sensors/{id}/hours endpoint, using period.datetimeFrom.utc as the actual measurement hour. The observation table rejects synthetic and CAMS data.

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

On first successful hourly ingestion the backend creates a private airtwin.station_observations PostgreSQL table (not in Supabase's default exposed public schema). Without DATABASE_URL, a local SQLite file is used under data/raw/live_station_history.sqlite3. SQLite on ephemeral cloud storage is not durable.

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

- OpenAQ data may be delayed, incomplete, absent, or rate-limited. The 49-hour no-gap requirement is deliberately strict in this first version.
- Hourly historical measurements are different from the latest unaggregated observation.
- Current CAMS context is modeled, not 25 independent local monitors.
- Current provider refresh is hourly by default (minimum 15 minutes) and runs only while one Python backend scheduler is running.
- Changing frontend polling intervals will not make providers publish new measurements more quickly.
- Live uncertainty coverage needs independent operational verification. The historical model card does not validate current CAMS provider forecasts.
- If a production DB connection fails, do not silently claim that its history has been saved.
- No Supabase project or remote database was modified as part of this branch commit.
