-- Claim management refinement schema
-- Run this in Supabase SQL Editor after init_schema.sql

ALTER TABLE claims
  ADD COLUMN IF NOT EXISTS claim_origin TEXT NOT NULL DEFAULT 'auto',
  ADD COLUMN IF NOT EXISTS eligible_payout_amount FLOAT DEFAULT 0,
  ADD COLUMN IF NOT EXISTS held_payout_amount FLOAT DEFAULT 0,
  ADD COLUMN IF NOT EXISTS reviewed_by TEXT,
  ADD COLUMN IF NOT EXISTS reviewed_at TIMESTAMPTZ,
  ADD COLUMN IF NOT EXISTS review_reason TEXT,
  ADD COLUMN IF NOT EXISTS resolution_note TEXT,
  ADD COLUMN IF NOT EXISTS batch_id UUID,
  ADD COLUMN IF NOT EXISTS is_batch_paused BOOLEAN DEFAULT FALSE,
  ADD COLUMN IF NOT EXISTS ring_review_flag BOOLEAN DEFAULT FALSE;

CREATE TABLE IF NOT EXISTS claim_events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  claim_id UUID NOT NULL REFERENCES claims(id) ON DELETE CASCADE,
  event_type TEXT NOT NULL,
  actor_type TEXT NOT NULL DEFAULT 'system',
  actor_id TEXT,
  note TEXT,
  metadata JSONB NOT NULL DEFAULT '{}',
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_claim_events_claim_time ON claim_events(claim_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_claims_origin_status ON claims(claim_origin, status);
