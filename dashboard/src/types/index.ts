export interface Project {
  id: string;
  name: string;
  description: string | null;
  created_at: string;
  is_active: boolean;
}

export interface ApiKeyResponse {
  id: string;
  key_prefix: string;
  is_active: boolean;
  created_at: string;
  raw_key?: string;
}

export interface OverviewMetrics {
  total_events: number;
  avg_latency_ms: number;
  p95_latency_ms: number;
  error_rate: number;
  avg_input_tokens: number;
  avg_output_tokens: number;
  latest_drift_score: number | null;
  hallucination_rate: number;
  events_last_hour: number;
}

export interface MetricPoint {
  timestamp: string;
  value: number;
}

export interface TimeSeriesResponse {
  model_name: string | null;
  metric: string;
  points: MetricPoint[];
}

export interface TelemetryEvent {
  id: string;
  project_id: string;
  timestamp: string;
  model_name: string;
  model_provider: string | null;
  input_tokens: number | null;
  output_tokens: number | null;
  latency_ms: number | null;
  status: string;
  trace_id: string | null;
  metadata: Record<string, unknown> | null;
  tags: string[] | null;
}

export interface TelemetryEventDetail extends TelemetryEvent {
  input_text: string | null;
  output_text: string | null;
  error_message: string | null;
  span_id: string | null;
  parent_span_id: string | null;
  hallucination_score: number | null;
}

export interface DriftScore {
  id: string;
  project_id: string;
  timestamp: string;
  model_name: string;
  metric_name: string;
  score: number;
  p_value: number | null;
  details: Record<string, unknown> | null;
}

export interface HallucinationScore {
  id: string;
  event_id: string;
  timestamp: string;
  score: number;
  method: string;
  details: Record<string, unknown> | null;
}

export interface AlertRule {
  id: string;
  project_id: string;
  name: string;
  metric_type: string;
  condition: string;
  threshold: number;
  window_minutes: number;
  notification_channel: Record<string, string>;
  is_active: boolean;
  cooldown_minutes: number;
  created_at: string;
}

export interface AlertFired {
  id: string;
  rule_id: string;
  project_id: string;
  triggered_at: string;
  metric_value: number;
  resolved_at: string | null;
  status: string;
  details: Record<string, unknown> | null;
}
