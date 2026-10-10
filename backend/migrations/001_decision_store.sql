-- AirTwin decision store v1. All concentration inputs retain explicit provenance.
-- Run with backend/app/services/decision_store.py (idempotent).
CREATE TABLE IF NOT EXISTS air_quality_samples (
  region TEXT NOT NULL CHECK (region IN ('pcmc', 'maharashtra')),
  location_id TEXT NOT NULL,
  sample_time TIMESTAMPTZ NOT NULL,
  source_type TEXT NOT NULL CHECK (source_type IN ('observed', 'modeled', 'synthetic')),
  provider TEXT NOT NULL,
  location_name TEXT NOT NULL,
  latitude DOUBLE PRECISION NOT NULL CHECK (latitude BETWEEN -90 AND 90),
  longitude DOUBLE PRECISION NOT NULL CHECK (longitude BETWEEN -180 AND 180),
  pm25_ugm3 DOUBLE PRECISION NOT NULL CHECK (pm25_ugm3 BETWEEN 0 AND 1000),
  imported_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (region, location_id, sample_time, source_type, provider)
);
CREATE INDEX IF NOT EXISTS aq_samples_latest_region
  ON air_quality_samples(region, sample_time DESC);
CREATE INDEX IF NOT EXISTS aq_samples_location_history
  ON air_quality_samples(region, location_id, sample_time DESC);
CREATE TABLE IF NOT EXISTS decision_runs (
  run_id UUID PRIMARY KEY,
  scenario_id TEXT NOT NULL,
  region TEXT NOT NULL CHECK (region IN ('pcmc', 'maharashtra')),
  location_id TEXT NOT NULL,
  replay_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  input_source_type TEXT NOT NULL CHECK (input_source_type IN ('observed', 'modeled', 'synthetic')),
  source_type TEXT NOT NULL DEFAULT 'modeled' CHECK (source_type = 'modeled'),
  cuts JSONB NOT NULL,
  summary JSONB NOT NULL,
  assumptions JSONB NOT NULL,
  algorithm_version TEXT NOT NULL DEFAULT 'proxy-scenarios-v1'
);
CREATE INDEX IF NOT EXISTS decision_runs_recent
  ON decision_runs(region, created_at DESC);
CREATE INDEX IF NOT EXISTS decision_runs_location
  ON decision_runs(region, location_id, created_at DESC);
CREATE TABLE IF NOT EXISTS forecast_evaluations (
  evaluation_id TEXT PRIMARY KEY,
  region TEXT NOT NULL,
  model_name TEXT NOT NULL,
  target_source_type TEXT NOT NULL CHECK (target_source_type IN ('observed','modeled','synthetic')),
  generated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  period_start TIMESTAMPTZ,
  period_end TIMESTAMPTZ,
  metrics JSONB NOT NULL,
  assumptions JSONB NOT NULL
);
CREATE INDEX IF NOT EXISTS forecast_evaluations_recent
  ON forecast_evaluations(region, generated_at DESC);
