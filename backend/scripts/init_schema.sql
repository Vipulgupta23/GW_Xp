-- Incometrix AI — Complete Database Schema
-- Run this in Supabase SQL Editor (in this exact order)

-- Step 1: Enable PostGIS
CREATE EXTENSION IF NOT EXISTS postgis;

-- Step 2: Workers
CREATE TABLE IF NOT EXISTS workers (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email VARCHAR(255) UNIQUE NOT NULL,
  name VARCHAR(100),
  phone VARCHAR(15),
  platform VARCHAR(50) NOT NULL,
  platform_worker_id VARCHAR(100),
  zone_lat FLOAT NOT NULL DEFAULT 12.9352,
  zone_lng FLOAT NOT NULL DEFAULT 77.6245,
  grid_id VARCHAR(50),
  city VARCHAR(50) DEFAULT 'Bengaluru',
  persona VARCHAR(20) DEFAULT 'stabilizer',
  iss_score FLOAT DEFAULT 50.0,
  is_verified BOOLEAN DEFAULT FALSE,
  is_active BOOLEAN DEFAULT TRUE,
  avg_daily_earnings FLOAT DEFAULT 900.0,
  avg_hourly_earnings FLOAT DEFAULT 90.0,
  active_days_per_week FLOAT DEFAULT 5.0,
  peak_hour_ratio FLOAT DEFAULT 0.5,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Step 3: Microgrids (1km² risk zones)
CREATE TABLE IF NOT EXISTS microgrids (
  id VARCHAR(50) PRIMARY KEY,
  city VARCHAR(50) NOT NULL,
  center_lat FLOAT NOT NULL,
  center_lng FLOAT NOT NULL,
  grid_polygon GEOMETRY(POLYGON, 4326),
  flood_risk FLOAT DEFAULT 0.3,
  heat_index FLOAT DEFAULT 0.4,
  aqi_avg FLOAT DEFAULT 120.0,
  traffic_risk FLOAT DEFAULT 0.4,
  social_risk FLOAT DEFAULT 0.2,
  composite_risk FLOAT DEFAULT 0.35,
  last_updated TIMESTAMPTZ DEFAULT NOW()
);

-- Step 4: Plans
CREATE TABLE IF NOT EXISTS plans (
  id VARCHAR(20) PRIMARY KEY,
  name VARCHAR(60) NOT NULL,
  weekly_premium_base FLOAT NOT NULL,
  max_weekly_payout FLOAT NOT NULL,
  coverage_pct FLOAT NOT NULL,
  description TEXT,
  features JSONB DEFAULT '[]'
);

INSERT INTO plans (id, name, weekly_premium_base, max_weekly_payout, coverage_pct, description, features) VALUES
('basic',  'Incometrix Basic', 49,  1500, 0.60, 'New workers, low-risk zones',          '["60% income coverage","₹1,500 max/week","3 trigger types"]'),
('plus',   'Incometrix Plus',  79,  2500, 0.70, 'Regular workers, medium-risk zones',    '["70% income coverage","₹2,500 max/week","All 7 trigger types","Priority support"]'),
('pro',    'Incometrix Pro',   129, 4000, 0.80, 'Full-time workers, high-risk zones',    '["80% income coverage","₹4,000 max/week","All triggers + cyclone","Fastest payouts","ISS fast-track"]')
ON CONFLICT (id) DO NOTHING;

-- Step 5: Policies
CREATE TABLE IF NOT EXISTS policies (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  worker_id UUID REFERENCES workers(id) ON DELETE CASCADE,
  plan_id VARCHAR(20) REFERENCES plans(id),
  status VARCHAR(20) DEFAULT 'active',
  weekly_premium_actual FLOAT NOT NULL,
  premium_base FLOAT NOT NULL,
  zone_risk_multiplier FLOAT DEFAULT 1.0,
  seasonal_factor FLOAT DEFAULT 1.0,
  iss_discount FLOAT DEFAULT 1.0,
  persona_factor FLOAT DEFAULT 1.0,
  start_date DATE NOT NULL,
  end_date DATE NOT NULL,
  total_paid_this_week FLOAT DEFAULT 0,
  mock_payment_id VARCHAR(100),
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Step 6: Earning records
CREATE TABLE IF NOT EXISTS earning_records (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  worker_id UUID REFERENCES workers(id),
  record_date DATE NOT NULL,
  hour_slot INTEGER NOT NULL CHECK (hour_slot BETWEEN 0 AND 23),
  deliveries INTEGER DEFAULT 0,
  earnings FLOAT DEFAULT 0,
  was_active BOOLEAN DEFAULT TRUE,
  disruption_id UUID,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Step 7: Disruption events
CREATE TABLE IF NOT EXISTS disruption_events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  trigger_type VARCHAR(40) NOT NULL,
  grid_id VARCHAR(50) REFERENCES microgrids(id),
  city VARCHAR(50) NOT NULL,
  severity FLOAT NOT NULL,
  threshold FLOAT NOT NULL,
  weather_description VARCHAR(200),
  started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  ended_at TIMESTAMPTZ,
  is_active BOOLEAN DEFAULT TRUE,
  raw_data JSONB,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Step 8: Claims
CREATE TABLE IF NOT EXISTS claims (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  worker_id UUID REFERENCES workers(id),
  policy_id UUID REFERENCES policies(id),
  disruption_id UUID REFERENCES disruption_events(id),
  trigger_type VARCHAR(40),
  status VARCHAR(25) DEFAULT 'processing',
  actual_earnings FLOAT DEFAULT 0,
  simulated_earnings FLOAT DEFAULT 0,
  income_gap FLOAT DEFAULT 0,
  payout_amount FLOAT DEFAULT 0,
  coverage_pct FLOAT,
  fraud_score FLOAT DEFAULT 0,
  fraud_layer1_pass BOOLEAN DEFAULT TRUE,
  fraud_layer2_pass BOOLEAN DEFAULT TRUE,
  fraud_layer3_pass BOOLEAN DEFAULT TRUE,
  fraud_flags JSONB DEFAULT '[]',
  earning_simulation JSONB,
  hinglish_explanation TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  processed_at TIMESTAMPTZ
);

-- Step 9: Payouts
CREATE TABLE IF NOT EXISTS payouts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  claim_id UUID REFERENCES claims(id),
  worker_id UUID REFERENCES workers(id),
  amount FLOAT NOT NULL,
  upi_id VARCHAR(100) DEFAULT 'worker@upi',
  mock_payout_id VARCHAR(100),
  status VARCHAR(20) DEFAULT 'pending',
  whatsapp_shown BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  paid_at TIMESTAMPTZ
);

-- Step 10: ISS history
CREATE TABLE IF NOT EXISTS iss_history (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  worker_id UUID REFERENCES workers(id),
  iss_score FLOAT NOT NULL,
  consistency_score FLOAT,
  regularity_score FLOAT,
  zone_score FLOAT,
  fraud_score_component FLOAT,
  delta FLOAT DEFAULT 0,
  calculated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_workers_grid ON workers(grid_id);
CREATE INDEX IF NOT EXISTS idx_earning_records_worker_date ON earning_records(worker_id, record_date, hour_slot);
CREATE INDEX IF NOT EXISTS idx_claims_worker ON claims(worker_id);
CREATE INDEX IF NOT EXISTS idx_claims_status ON claims(status);
CREATE INDEX IF NOT EXISTS idx_disruption_active ON disruption_events(is_active, grid_id);
CREATE INDEX IF NOT EXISTS idx_policies_worker_active ON policies(worker_id, status);
CREATE INDEX IF NOT EXISTS idx_microgrids_geo ON microgrids USING GIST(grid_polygon);

-- PostGIS Lookup Function
CREATE OR REPLACE FUNCTION find_grid_by_point(p_lat FLOAT, p_lng FLOAT)
RETURNS TABLE(
    id VARCHAR, city VARCHAR, center_lat FLOAT, center_lng FLOAT,
    flood_risk FLOAT, heat_index FLOAT, aqi_avg FLOAT,
    traffic_risk FLOAT, social_risk FLOAT, composite_risk FLOAT
) AS $$
SELECT id, city, center_lat, center_lng,
       flood_risk, heat_index, aqi_avg,
       traffic_risk, social_risk, composite_risk
FROM microgrids
WHERE ST_Contains(
    grid_polygon,
    ST_SetSRID(ST_MakePoint(p_lng, p_lat), 4326)
)
LIMIT 1;
$$ LANGUAGE sql;
