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

// Set API key for all requests
export function setApiKey(key: string) {
  api.defaults.headers.common['X-API-Key'] = key;
}

// Projects
export const fetchProjects = () => api.get<Project[]>('/projects').then(r => r.data);
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
  api.get<DriftScore[]>('/metrics/drift', { params }).then(r => r.data);

export const fetchHallucinationScores = (params?: { limit?: number }) =>
  api.get<HallucinationScore[]>('/metrics/hallucinations', { params }).then(r => r.data);

// Events
export const fetchEvents = (params?: { model_name?: string; status?: string; limit?: number; offset?: number }) =>
  api.get<TelemetryEvent[]>('/events', { params }).then(r => r.data);

export const fetchEventDetail = (eventId: string) =>
  api.get<TelemetryEventDetail>(`/events/${eventId}`).then(r => r.data);

// Alerts
export const fetchAlertRules = () => api.get<AlertRule[]>('/alerts/rules').then(r => r.data);
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
  api.get<AlertFired[]>('/alerts/history', { params }).then(r => r.data);
