BEGIN;
CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE TABLE IF NOT EXISTS projects (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(), name VARCHAR(256) NOT NULL,
  description VARCHAR(1024), created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  is_active BOOLEAN NOT NULL DEFAULT TRUE
);
CREATE TABLE IF NOT EXISTS api_keys (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(), project_id UUID NOT NULL REFERENCES projects(id),
  key_hash VARCHAR(128) NOT NULL, key_prefix VARCHAR(12) NOT NULL,
  is_active BOOLEAN NOT NULL DEFAULT TRUE, created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
ALTER TABLE projects ADD COLUMN IF NOT EXISTS tenant_id TEXT;
ALTER TABLE projects ADD COLUMN IF NOT EXISTS retention_days INTEGER NOT NULL DEFAULT 30 CHECK (retention_days BETWEEN 1 AND 3650);
ALTER TABLE projects DROP CONSTRAINT IF EXISTS projects_name_key;
CREATE UNIQUE INDEX IF NOT EXISTS projects_tenant_name_unique ON projects (tenant_id, name) WHERE tenant_id IS NOT NULL;
ALTER TABLE api_keys ADD COLUMN IF NOT EXISTS role TEXT NOT NULL DEFAULT 'viewer' CHECK (role IN ('viewer','operator','evaluator','admin'));
CREATE INDEX IF NOT EXISTS projects_tenant_idx ON projects (tenant_id, id);

CREATE TABLE IF NOT EXISTS observability_users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(), email TEXT NOT NULL,
  password_hash TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active','disabled')),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE UNIQUE INDEX IF NOT EXISTS observability_users_email_unique ON observability_users (lower(email));
CREATE TABLE IF NOT EXISTS observability_user_projects (
  user_id UUID NOT NULL REFERENCES observability_users(id), project_id UUID NOT NULL REFERENCES projects(id),
  role TEXT NOT NULL CHECK (role IN ('viewer','operator','evaluator','admin')),
  status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active','revoked')),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), PRIMARY KEY (user_id,project_id)
);

CREATE TABLE IF NOT EXISTS observability_events (
  tenant_id TEXT NOT NULL, project_id UUID NOT NULL REFERENCES projects(id), event_id TEXT NOT NULL,
  trace_id TEXT NOT NULL, span_id TEXT NOT NULL, parent_span_id TEXT, kind TEXT NOT NULL,
  schema_version INTEGER NOT NULL CHECK (schema_version > 0), sequence BIGINT NOT NULL CHECK (sequence >= 0),
  occurred_at TIMESTAMPTZ NOT NULL, received_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), payload JSONB NOT NULL,
  payload_hash CHAR(64) NOT NULL, model_version TEXT, prompt_version TEXT, retrieval_version TEXT,
  cost_micros BIGINT CHECK (cost_micros >= 0), expires_at TIMESTAMPTZ NOT NULL,
  PRIMARY KEY (tenant_id, project_id, event_id), UNIQUE (tenant_id, project_id, trace_id, span_id, sequence)
);
CREATE INDEX IF NOT EXISTS observability_trace_idx ON observability_events (tenant_id, project_id, trace_id, sequence);
CREATE INDEX IF NOT EXISTS observability_expiry_idx ON observability_events (expires_at);

CREATE TABLE IF NOT EXISTS observability_eval_runs (
  id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL, project_id UUID NOT NULL REFERENCES projects(id), dataset_id TEXT NOT NULL,
  dataset_version TEXT NOT NULL, model_version TEXT NOT NULL, prompt_version TEXT NOT NULL, evaluator_version TEXT NOT NULL,
  thresholds JSONB NOT NULL, metrics JSONB NOT NULL, accepted BOOLEAN NOT NULL, failures JSONB NOT NULL,
  reproducibility_hash CHAR(64) NOT NULL, created_by UUID, created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS observability_incidents (
  id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL, project_id UUID NOT NULL REFERENCES projects(id), dedupe_key CHAR(64) NOT NULL,
  signal TEXT NOT NULL, scope TEXT NOT NULL, status TEXT NOT NULL CHECK (status IN ('open','acknowledged','resolved','reopened')),
  severity TEXT NOT NULL CHECK (severity IN ('info','warning','critical')), owner_id TEXT, route TEXT,
  resolution TEXT, opened_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (tenant_id, project_id, dedupe_key)
);
CREATE TABLE IF NOT EXISTS observability_incident_history (
 id BIGSERIAL PRIMARY KEY, tenant_id TEXT NOT NULL, incident_id TEXT NOT NULL REFERENCES observability_incidents(id),
 from_status TEXT, to_status TEXT NOT NULL, actor_id TEXT NOT NULL, owner_id TEXT, resolution TEXT,
 occurred_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS observability_provider_deliveries (
  id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL, project_id UUID NOT NULL REFERENCES projects(id), provider TEXT NOT NULL,
  operation TEXT NOT NULL, idempotency_key TEXT NOT NULL, payload_hash CHAR(64) NOT NULL, payload JSONB NOT NULL,
  status TEXT NOT NULL DEFAULT 'queued' CHECK (status IN ('queued','leased','retrying','confirmed','dead_letter')),
  attempts INTEGER NOT NULL DEFAULT 0 CHECK (attempts >= 0), max_attempts INTEGER NOT NULL DEFAULT 5 CHECK (max_attempts > 0),
  next_attempt_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), last_error TEXT, receipt JSONB, created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), UNIQUE (tenant_id, provider, idempotency_key)
);
CREATE TABLE IF NOT EXISTS observability_audit (
  id BIGSERIAL PRIMARY KEY, tenant_id TEXT NOT NULL, project_id UUID, actor_id TEXT NOT NULL, actor_role TEXT NOT NULL,
  action TEXT NOT NULL, resource_type TEXT NOT NULL, resource_id TEXT NOT NULL, before_hash CHAR(64), after_hash CHAR(64),
  metadata JSONB NOT NULL DEFAULT '{}'::jsonb, occurred_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE OR REPLACE FUNCTION observability_audit_immutable() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN RAISE EXCEPTION 'observability_audit is append-only'; END; $$;
DROP TRIGGER IF EXISTS observability_audit_no_update ON observability_audit;
CREATE TRIGGER observability_audit_no_update BEFORE UPDATE OR DELETE ON observability_audit FOR EACH ROW EXECUTE FUNCTION observability_audit_immutable();
COMMIT;
