CREATE TABLE IF NOT EXISTS sombra_intel_global (
  id UUID PRIMARY KEY,
  timestamp_utc TIMESTAMP,
  threat_type VARCHAR(100),
  severity VARCHAR(20),
  confidence FLOAT,
  findings TEXT,
  source_category VARCHAR(50),
  source_reliability FLOAT,
  indicators JSONB,
  routing JSONB,
  threat_score INTEGER,
  prediction JSONB,
  aging_status VARCHAR(20) DEFAULT 'ACTIVE',
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS sombra_client_profiles (
  client_id UUID PRIMARY KEY,
  client_name VARCHAR(200),
  industry_sector VARCHAR(100),
  geography VARCHAR(100),
  risk_score INTEGER DEFAULT 0,
  risk_trend VARCHAR(20) DEFAULT 'STABLE',
  digital_assets JSONB,
  executive_registry JSONB,
  threat_history JSONB,
  credential_history JSONB,
  brand_registry JSONB,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS sombra_blackbox (
  id UUID PRIMARY KEY,
  timestamp_utc TIMESTAMP DEFAULT NOW(),
  event_type VARCHAR(100),
  entity VARCHAR(100),
  detail JSONB,
  order_origin VARCHAR(50),
  rule_suspended VARCHAR(100),
  hash_sha256 VARCHAR(64)
);

CREATE INDEX IF NOT EXISTS idx_sombra_intel_global_threat_type
  ON sombra_intel_global(threat_type);

CREATE INDEX IF NOT EXISTS idx_sombra_intel_global_severity
  ON sombra_intel_global(severity);

CREATE INDEX IF NOT EXISTS idx_sombra_intel_global_timestamp_utc
  ON sombra_intel_global(timestamp_utc);

CREATE INDEX IF NOT EXISTS idx_sombra_blackbox_event_type
  ON sombra_blackbox(event_type);

CREATE OR REPLACE FUNCTION sombra_blackbox_append_only_guard()
RETURNS trigger AS $$
BEGIN
  RAISE EXCEPTION 'sombra_blackbox is append-only';
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_sombra_blackbox_no_update ON sombra_blackbox;
CREATE TRIGGER trg_sombra_blackbox_no_update
  BEFORE UPDATE ON sombra_blackbox
  FOR EACH ROW EXECUTE FUNCTION sombra_blackbox_append_only_guard();

DROP TRIGGER IF EXISTS trg_sombra_blackbox_no_delete ON sombra_blackbox;
CREATE TRIGGER trg_sombra_blackbox_no_delete
  BEFORE DELETE ON sombra_blackbox
  FOR EACH ROW EXECUTE FUNCTION sombra_blackbox_append_only_guard();
