# Offline fixture

`dataset_sample.csv` is deterministic synthetic data, not sensor observations.
One fictional centroid series has 2,952 hourly rows from 2025-10-01 to 2026-01-31.
Every target/weather row carries synthetic provenance. PM2.5 is µg/m³ and wind is m/s.

Regenerate explicitly with `python backend/scripts/generate_sample.py`.
The fixture is committed only to keep development and demo startup independent of APIs.
