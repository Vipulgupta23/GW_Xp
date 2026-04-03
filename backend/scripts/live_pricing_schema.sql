-- Incometrix AI — Live pricing schema for top 20 cities
-- Run this after init_schema.sql

CREATE TABLE IF NOT EXISTS supported_cities (
  slug TEXT PRIMARY KEY,
  name TEXT UNIQUE NOT NULL,
  state TEXT,
  timezone TEXT NOT NULL DEFAULT 'Asia/Kolkata',
  grid_prefix TEXT UNIQUE NOT NULL,
  center_lat DOUBLE PRECISION NOT NULL,
  center_lng DOUBLE PRECISION NOT NULL,
  lat_min DOUBLE PRECISION NOT NULL,
  lat_max DOUBLE PRECISION NOT NULL,
  lng_min DOUBLE PRECISION NOT NULL,
  lng_max DOUBLE PRECISION NOT NULL,
  grid_origin_lat DOUBLE PRECISION NOT NULL,
  grid_origin_lng DOUBLE PRECISION NOT NULL,
  grid_rows INTEGER NOT NULL,
  grid_cols INTEGER NOT NULL,
  grid_step_deg DOUBLE PRECISION NOT NULL DEFAULT 0.009,
  pricing_enabled BOOLEAN NOT NULL DEFAULT TRUE,
  feature_status TEXT NOT NULL DEFAULT 'pending',
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS pricing_config_versions (
  version TEXT PRIMARY KEY,
  is_active BOOLEAN NOT NULL DEFAULT FALSE,
  config JSONB NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_pricing_config_active
ON pricing_config_versions ((is_active))
WHERE is_active = TRUE;

CREATE TABLE IF NOT EXISTS microgrid_features_current (
  grid_id VARCHAR(50) PRIMARY KEY REFERENCES microgrids(id) ON DELETE CASCADE,
  city_slug TEXT NOT NULL REFERENCES supported_cities(slug) ON DELETE CASCADE,
  feature_snapshot JSONB NOT NULL,
  observed_at TIMESTAMPTZ NOT NULL,
  expires_at TIMESTAMPTZ NOT NULL,
  source TEXT NOT NULL,
  source_status TEXT NOT NULL DEFAULT 'fresh',
  pricing_version TEXT REFERENCES pricing_config_versions(version),
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS microgrid_features_history (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  grid_id VARCHAR(50) NOT NULL REFERENCES microgrids(id) ON DELETE CASCADE,
  city_slug TEXT NOT NULL REFERENCES supported_cities(slug) ON DELETE CASCADE,
  feature_snapshot JSONB NOT NULL,
  observed_at TIMESTAMPTZ NOT NULL,
  expires_at TIMESTAMPTZ NOT NULL,
  source TEXT NOT NULL,
  source_status TEXT NOT NULL DEFAULT 'fresh',
  pricing_version TEXT REFERENCES pricing_config_versions(version),
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS pricing_quotes (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  worker_id UUID REFERENCES workers(id) ON DELETE CASCADE,
  plan_id VARCHAR(20) REFERENCES plans(id),
  resolved_grid_id VARCHAR(50) REFERENCES microgrids(id),
  resolved_city TEXT,
  pricing_version TEXT REFERENCES pricing_config_versions(version),
  feature_snapshot JSONB NOT NULL,
  feature_freshness JSONB NOT NULL,
  premium_breakdown JSONB NOT NULL,
  final_premium FLOAT NOT NULL,
  quote_status TEXT NOT NULL DEFAULT 'fresh',
  quoted_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE policies
  ADD COLUMN IF NOT EXISTS quote_id UUID REFERENCES pricing_quotes(id),
  ADD COLUMN IF NOT EXISTS pricing_version TEXT,
  ADD COLUMN IF NOT EXISTS resolved_grid_id VARCHAR(50),
  ADD COLUMN IF NOT EXISTS resolved_city TEXT,
  ADD COLUMN IF NOT EXISTS feature_snapshot JSONB,
  ADD COLUMN IF NOT EXISTS feature_freshness JSONB;

CREATE INDEX IF NOT EXISTS idx_supported_cities_enabled ON supported_cities(pricing_enabled);
CREATE INDEX IF NOT EXISTS idx_features_current_city ON microgrid_features_current(city_slug, expires_at);
CREATE INDEX IF NOT EXISTS idx_features_history_grid_time ON microgrid_features_history(grid_id, observed_at DESC);
CREATE INDEX IF NOT EXISTS idx_pricing_quotes_worker_time ON pricing_quotes(worker_id, quoted_at DESC);
