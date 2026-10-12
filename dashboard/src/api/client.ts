import axios from 'axios';
import type {
  OverviewMetrics,
  TimeSeriesResponse,
  TelemetryEvent,
  TelemetryEventDetail,
  DriftScore,
  HallucinationScore,
  AlertRule,
  AlertFired,
  Project,
  ApiKeyResponse,
} from '../types';

const API_BASE = import.meta.env.VITE_API_URL || '/api/v1';

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.request.use(config => {
  const token = sessionStorage.getItem('observability_access_token');
  if (token) config.headers.set('Authorization', `Bearer ${token}`);
  return config;
});

function records<T>(payload: unknown, name: string): T[] {
  const rows = Array.isArray(payload) ? payload
    : payload && typeof payload === 'object' && 'data' in payload ? (payload as { data: unknown }).data
    : undefined;
  if (!Array.isArray(rows)) throw new TypeError(`${name} response must contain an array of records`);
  return rows as T[];
}

// Set API key for all requests
export function setApiKey(key: string) {
  api.defaults.headers.common['X-API-Key'] = key;
}

// Projects
export const fetchProjects = () => api.get('/authoritative/projects').then(r => records<Project>(r.data, 'Projects'));
export const createProject = (data: { name: string; description?: string }) =>
  api.post<Project>('/projects', data).then(r => r.data);
export const createApiKey = (projectId: string) =>
  api.post<ApiKeyResponse>(`/projects/${projectId}/api-keys`).then(r => r.data);

// Metrics
export const fetchOverview = (window = '24h') =>
  api.get<OverviewMetrics>('/metrics/overview', { params: { window } }).then(r => r.data);

export const fetchLatencyTimeseries = (params?: { model_name?: string; bucket?: string }) =>
  api.get<TimeSeriesResponse>('/metrics/latency', { params }).then(r => r.data);

export const fetchTokenTimeseries = (params?: { model_name?: string }) =>
  api.get<TimeSeriesResponse>('/metrics/tokens', { params }).then(r => r.data);

export const fetchDriftScores = (params?: { model_name?: string; limit?: number }) =>
  api.get('/metrics/drift', { params }).then(r => records<DriftScore>(r.data, 'Drift scores'));

export const fetchHallucinationScores = (params?: { limit?: number }) =>
  api.get('/metrics/hallucinations', { params }).then(r => records<HallucinationScore>(r.data, 'Hallucination scores'));

// Events
export const fetchEvents = (params?: { model_name?: string; status?: string; limit?: number; offset?: number }) =>
  api.get('/authoritative/events', { params }).then(r => records<TelemetryEvent>(r.data, 'Events'));

export const fetchEventDetail = (eventId: string) =>
  api.get<TelemetryEventDetail>(`/authoritative/events/${encodeURIComponent(eventId)}`).then(r => r.data);

// Alerts
export const fetchAlertRules = () => api.get('/alerts/rules').then(r => records<AlertRule>(r.data, 'Alert rules'));
export const createAlertRule = (data: {
  name: string;
  metric_type: string;
  condition: string;
  threshold: number;
  window_minutes?: number;
  notification_channel?: Record<string, string>;
}) => api.post<AlertRule>('/alerts/rules', data).then(r => r.data);
export const updateAlertRule = (ruleId: string, data: Partial<AlertRule>) =>
  api.put<AlertRule>(`/alerts/rules/${ruleId}`, data).then(r => r.data);
export const deleteAlertRule = (ruleId: string) =>
  api.delete(`/alerts/rules/${ruleId}`);
export const fetchAlertHistory = (params?: { status?: string; limit?: number }) =>
  api.get('/alerts/history', { params }).then(r => records<AlertFired>(r.data, 'Alert history'));

// AI Insights
export interface AIInsightResponse {
  insight: string;
  model: string;
  tokens_used?: number | null;
  context?: Record<string, unknown> | null;
}

export const aiAnalyzeEvent = (body: { event_id: string; expected_behavior?: string }) =>
  api.post<AIInsightResponse>('/ai/analyze-event', body).then(r => r.data);

export const aiAnalyzeIncident = (body: { alert_id?: string; window_minutes?: number; include_sample_events?: number }) =>
  api.post<AIInsightResponse>('/ai/analyze-incident', body).then(r => r.data);

export const aiDriftNarrative = (body: { model_name?: string; lookback_hours?: number }) =>
  api.post<AIInsightResponse>('/ai/drift-narrative', body).then(r => r.data);

export const aiCompareModels = (body: { model_a: string; model_b: string; lookback_hours?: number }) =>
  api.post<AIInsightResponse>('/ai/compare-models', body).then(r => r.data);

export const aiCostOptimize = (body: { lookback_hours?: number }) =>
  api.post<AIInsightResponse>('/ai/cost-optimize', body).then(r => r.data);

export const aiTraceAnalyze = (body: { trace_id: string }) =>
  api.post<AIInsightResponse>('/ai/trace-analyze', body).then(r => r.data);

export const aiPromptRegression = (body: { model_name: string; baseline_hours?: number; recent_hours?: number }) =>
  api.post<AIInsightResponse>('/ai/prompt-regression', body).then(r => r.data);

export const aiHallucinationCluster = (body: { lookback_hours?: number; min_score?: number; sample_size?: number }) =>
  api.post<AIInsightResponse>('/ai/hallucination-cluster', body).then(r => r.data);

export const aiAlertRuleSuggest = (body: { metric_focus?: string }) =>
  api.post<AIInsightResponse>('/ai/alert-rule-suggest', body).then(r => r.data);

export const aiExplainQuery = (body: { question: string }) =>
  api.post<AIInsightResponse>('/ai/explain-query', body).then(r => r.data);

export const scanPromptInjection = (body: { prompt: string; tool_access: string[]; retrieved_context: string }) =>
  api.post('/prompt-injection/scan', body).then(r => r.data);
