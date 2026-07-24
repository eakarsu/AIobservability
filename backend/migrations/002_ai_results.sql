CREATE TABLE IF NOT EXISTS observability_ai_results (
  id UUID PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  project_id UUID NOT NULL REFERENCES projects(id),
  user_id UUID NOT NULL REFERENCES observability_users(id),
  endpoint TEXT NOT NULL,
  input_data JSONB NOT NULL,
  result JSONB NOT NULL,
  model TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS observability_ai_results_scope_idx
  ON observability_ai_results (tenant_id, project_id, user_id, created_at DESC);
