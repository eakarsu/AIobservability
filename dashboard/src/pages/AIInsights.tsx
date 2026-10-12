import ReadableAIResult from '../components/ReadableAIResult';

import FullAIExamples, { useFullAIExamples } from "../components/FullAIExamples";
import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import {
  AIInsightResponse,
  aiAnalyzeEvent,
  aiAnalyzeIncident,
  aiDriftNarrative,
  aiCompareModels,
  aiCostOptimize,
  aiTraceAnalyze,
  aiPromptRegression,
  aiHallucinationCluster,
  aiAlertRuleSuggest,
  aiExplainQuery,
} from '../api/client';
import { Sparkles, Loader2, AlertCircle } from 'lucide-react';

type ToolKey =
  | 'analyze-event'
  | 'analyze-incident'
  | 'drift-narrative'
  | 'compare-models'
  | 'cost-optimize'
  | 'trace-analyze'
  | 'prompt-regression'
  | 'hallucination-cluster'
  | 'alert-rule-suggest'
  | 'explain-query';

interface Tool {
  key: ToolKey;
  label: string;
  description: string;
}

const TOOLS: Tool[] = [
  { key: 'analyze-event', label: 'Analyze Event', description: 'Root-cause a single suspicious event by ID.' },
  { key: 'analyze-incident', label: 'Analyze Incident', description: 'Narrate a multi-event incident around an alert window.' },
  { key: 'drift-narrative', label: 'Drift Narrative', description: 'Translate raw drift scores into plain language.' },
  { key: 'compare-models', label: 'Compare Models', description: 'A/B summary across latency, errors, hallucinations, cost.' },
  { key: 'cost-optimize', label: 'Cost Optimize', description: 'Token-spend recommendations grouped by model.' },
  { key: 'trace-analyze', label: 'Trace Analyze', description: 'Pipeline analysis for a given trace_id.' },
  { key: 'prompt-regression', label: 'Prompt Regression', description: 'Baseline vs recent regression detector.' },
  { key: 'hallucination-cluster', label: 'Hallucination Cluster', description: 'Theme-cluster high-hallucination samples.' },
  { key: 'alert-rule-suggest', label: 'Alert Rule Suggest', description: 'Propose alert thresholds anchored in observed percentiles.' },
  { key: 'explain-query', label: 'Explain (Q&A)', description: 'Grounded Q&A over the project telemetry.' },
];

interface Inputs {
  event_id: string;
  expected_behavior: string;
  alert_id: string;
  window_minutes: string;
  include_sample_events: string;
  drift_model_name: string;
  drift_lookback_hours: string;
  cmp_model_a: string;
  cmp_model_b: string;
  cmp_lookback_hours: string;
  cost_lookback_hours: string;
  trace_id: string;
  pr_model_name: string;
  pr_baseline_hours: string;
  pr_recent_hours: string;
  hc_lookback_hours: string;
  hc_min_score: string;
  hc_sample_size: string;
  ar_metric_focus: string;
  question: string;
}

const DEFAULT_INPUTS: Inputs = {
  event_id: '',
  expected_behavior: '',
  alert_id: '',
  window_minutes: '30',
  include_sample_events: '10',
  drift_model_name: '',
  drift_lookback_hours: '24',
  cmp_model_a: '',
  cmp_model_b: '',
  cmp_lookback_hours: '24',
  cost_lookback_hours: '168',
  trace_id: '',
  pr_model_name: '',
  pr_baseline_hours: '168',
  pr_recent_hours: '24',
  hc_lookback_hours: '168',
  hc_min_score: '0.5',
  hc_sample_size: '30',
  ar_metric_focus: '',
  question: '',
};

function toInt(v: string, fallback: number): number {
  const n = parseInt(v, 10);
  return Number.isFinite(n) ? n : fallback;
}

function toFloat(v: string, fallback: number): number {
  const n = parseFloat(v);
  return Number.isFinite(n) ? n : fallback;
}

export default function AIInsights() {
  const fullAIExamples = useFullAIExamples();

  const [activeTool, setActiveTool] = useState<ToolKey>('analyze-event');
  const [inputs, setInputs] = useState<Inputs>(DEFAULT_INPUTS);

  const update = (k: keyof Inputs) => (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    setInputs(prev => ({ ...prev, [k]: e.target.value }));
  };

  const mutation = useMutation<AIInsightResponse, Error, void>({
    mutationFn: async () => {
      switch (activeTool) {
        case 'analyze-event':
          return aiAnalyzeEvent({
            event_id: inputs.event_id,
            ...(inputs.expected_behavior ? { expected_behavior: inputs.expected_behavior } : {}),
          });
        case 'analyze-incident':
          return aiAnalyzeIncident({
            ...(inputs.alert_id ? { alert_id: inputs.alert_id } : {}),
            window_minutes: toInt(inputs.window_minutes, 30),
            include_sample_events: toInt(inputs.include_sample_events, 10),
          });
        case 'drift-narrative':
          return aiDriftNarrative({
            ...(inputs.drift_model_name ? { model_name: inputs.drift_model_name } : {}),
            lookback_hours: toInt(inputs.drift_lookback_hours, 24),
          });
        case 'compare-models':
          return aiCompareModels({
            model_a: inputs.cmp_model_a,
            model_b: inputs.cmp_model_b,
            lookback_hours: toInt(inputs.cmp_lookback_hours, 24),
          });
        case 'cost-optimize':
          return aiCostOptimize({
            lookback_hours: toInt(inputs.cost_lookback_hours, 168),
          });
        case 'trace-analyze':
          return aiTraceAnalyze({ trace_id: inputs.trace_id });
        case 'prompt-regression':
          return aiPromptRegression({
            model_name: inputs.pr_model_name,
            baseline_hours: toInt(inputs.pr_baseline_hours, 168),
            recent_hours: toInt(inputs.pr_recent_hours, 24),
          });
        case 'hallucination-cluster':
          return aiHallucinationCluster({
            lookback_hours: toInt(inputs.hc_lookback_hours, 168),
            min_score: toFloat(inputs.hc_min_score, 0.5),
            sample_size: toInt(inputs.hc_sample_size, 30),
          });
        case 'alert-rule-suggest':
          return aiAlertRuleSuggest({
            ...(inputs.ar_metric_focus ? { metric_focus: inputs.ar_metric_focus } : {}),
          });
        case 'explain-query':
          return aiExplainQuery({ question: inputs.question });
      }
    },
  });

  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    mutation.reset();
    mutation.mutate();
  };

  const errorMessage = mutation.error
    ? (mutation.error as unknown as { response?: { data?: { detail?: string } }; message?: string }).response?.data?.detail
      || (mutation.error as Error).message
    : null;

  const isUnconfigured = typeof errorMessage === 'string' && errorMessage.toLowerCase().includes('openrouter_api_key');

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <Sparkles className="w-7 h-7 text-purple-500" />
        <h1 className="text-2xl font-bold text-gray-900">AI Insights</h1>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
        <div className="lg:col-span-1 bg-white rounded-lg shadow p-3 space-y-1">
          {TOOLS.map(t => (
            <button
              key={t.key}
              onClick={() => { setActiveTool(t.key); mutation.reset(); }}
              className={`w-full text-left rounded px-3 py-2 text-sm transition-colors ${
                activeTool === t.key
                  ? 'bg-purple-100 text-purple-800 font-medium'
                  : 'hover:bg-gray-50 text-gray-700'
              }`}
            >
              <div className="font-medium">{t.label}</div>
              <div className="text-xs text-gray-500 mt-0.5 leading-tight">{t.description}</div>
            </button>
          ))}
        </div>

        <div className="lg:col-span-3 space-y-4">
          <form onSubmit={submit} className="bg-white rounded-lg shadow p-4 space-y-3" data-full-ai-workspace="AIInsights"><FullAIExamples controller={fullAIExamples} />
            <h2 className="text-sm font-semibold text-gray-700 uppercase tracking-wide">
              {TOOLS.find(t => t.key === activeTool)?.label}
            </h2>

            {activeTool === 'analyze-event' && (
              <>
                <Field label="Event ID" required>
                  <input className={inputClass} value={inputs.event_id} onChange={update('event_id')} placeholder="evt_..." required data-full-ai-field={fullAIExamples.bind({ current: inputs.event_id, change: update('event_id'), label: "inputs.event_id", manual: false, json: false }, "p1-7700", undefined)} />
                </Field>
                <Field label="Expected behavior (optional)">
                  <textarea className={inputClass} rows={2} value={inputs.expected_behavior} onChange={update('expected_behavior')} data-full-ai-field={fullAIExamples.bind({ current: inputs.expected_behavior, change: update('expected_behavior'), label: "inputs.expected_behavior", manual: false, json: false }, "p1-7922", undefined)} />
                </Field>
              </>
            )}

            {activeTool === 'analyze-incident' && (
              <>
                <Field label="Alert ID (optional)">
                  <input className={inputClass} value={inputs.alert_id} onChange={update('alert_id')} data-full-ai-field={fullAIExamples.bind({ current: inputs.alert_id, change: update('alert_id'), label: "inputs.alert_id", manual: false, json: false }, "p1-8237", undefined)} />
                </Field>
                <div className="grid grid-cols-2 gap-3">
                  <Field label="Window (minutes)">
                    <input type="number" className={inputClass} value={inputs.window_minutes} onChange={update('window_minutes')} data-full-ai-field={fullAIExamples.bind({ current: inputs.window_minutes, change: update('window_minutes'), label: "inputs.window_minutes", manual: false, json: false }, "p1-8477", undefined)} />
                  </Field>
                  <Field label="Sample events">
                    <input type="number" className={inputClass} value={inputs.include_sample_events} onChange={update('include_sample_events')} data-full-ai-field={fullAIExamples.bind({ current: inputs.include_sample_events, change: update('include_sample_events'), label: "inputs.include_sample_events", manual: false, json: false }, "p1-8685", undefined)} />
                  </Field>
                </div>
              </>
            )}

            {activeTool === 'drift-narrative' && (
              <>
                <Field label="Model name (optional)">
                  <input className={inputClass} value={inputs.drift_model_name} onChange={update('drift_model_name')} data-full-ai-field={fullAIExamples.bind({ current: inputs.drift_model_name, change: update('drift_model_name'), label: "inputs.drift_model_name", manual: false, json: false }, "p1-9036", undefined)} />
                </Field>
                <Field label="Lookback (hours)">
                  <input type="number" className={inputClass} value={inputs.drift_lookback_hours} onChange={update('drift_lookback_hours')} data-full-ai-field={fullAIExamples.bind({ current: inputs.drift_lookback_hours, change: update('drift_lookback_hours'), label: "inputs.drift_lookback_hours", manual: false, json: false }, "p1-9231", undefined)} />
                </Field>
              </>
            )}

            {activeTool === 'compare-models' && (
              <>
                <div className="grid grid-cols-2 gap-3">
                  <Field label="Model A" required>
                    <input className={inputClass} value={inputs.cmp_model_a} onChange={update('cmp_model_a')} required data-full-ai-field={fullAIExamples.bind({ current: inputs.cmp_model_a, change: update('cmp_model_a'), label: "inputs.cmp_model_a", manual: false, json: false }, "p1-9610", undefined)} />
                  </Field>
                  <Field label="Model B" required>
                    <input className={inputClass} value={inputs.cmp_model_b} onChange={update('cmp_model_b')} required data-full-ai-field={fullAIExamples.bind({ current: inputs.cmp_model_b, change: update('cmp_model_b'), label: "inputs.cmp_model_b", manual: false, json: false }, "p1-9810", undefined)} />
                  </Field>
                </div>
                <Field label="Lookback (hours)">
                  <input type="number" className={inputClass} value={inputs.cmp_lookback_hours} onChange={update('cmp_lookback_hours')} data-full-ai-field={fullAIExamples.bind({ current: inputs.cmp_lookback_hours, change: update('cmp_lookback_hours'), label: "inputs.cmp_lookback_hours", manual: false, json: false }, "p1-10029", undefined)} />
                </Field>
              </>
            )}

            {activeTool === 'cost-optimize' && (
              <Field label="Lookback (hours)">
                <input type="number" className={inputClass} value={inputs.cost_lookback_hours} onChange={update('cost_lookback_hours')} data-full-ai-field={fullAIExamples.bind({ current: inputs.cost_lookback_hours, change: update('cost_lookback_hours'), label: "inputs.cost_lookback_hours", manual: false, json: false }, "p1-10321", undefined)} />
              </Field>
            )}

            {activeTool === 'trace-analyze' && (
              <Field label="Trace ID" required>
                <input className={inputClass} value={inputs.trace_id} onChange={update('trace_id')} required data-full-ai-field={fullAIExamples.bind({ current: inputs.trace_id, change: update('trace_id'), label: "inputs.trace_id", manual: false, json: false }, "p1-10596", undefined)} />
              </Field>
            )}

            {activeTool === 'prompt-regression' && (
              <>
                <Field label="Model name" required>
                  <input className={inputClass} value={inputs.pr_model_name} onChange={update('pr_model_name')} required data-full-ai-field={fullAIExamples.bind({ current: inputs.pr_model_name, change: update('pr_model_name'), label: "inputs.pr_model_name", manual: false, json: false }, "p1-10871", undefined)} />
                </Field>
                <div className="grid grid-cols-2 gap-3">
                  <Field label="Baseline (hours)">
                    <input type="number" className={inputClass} value={inputs.pr_baseline_hours} onChange={update('pr_baseline_hours')} data-full-ai-field={fullAIExamples.bind({ current: inputs.pr_baseline_hours, change: update('pr_baseline_hours'), label: "inputs.pr_baseline_hours", manual: false, json: false }, "p1-11130", undefined)} />
                  </Field>
                  <Field label="Recent (hours)">
                    <input type="number" className={inputClass} value={inputs.pr_recent_hours} onChange={update('pr_recent_hours')} data-full-ai-field={fullAIExamples.bind({ current: inputs.pr_recent_hours, change: update('pr_recent_hours'), label: "inputs.pr_recent_hours", manual: false, json: false }, "p1-11345", undefined)} />
                  </Field>
                </div>
              </>
            )}

            {activeTool === 'hallucination-cluster' && (
              <div className="grid grid-cols-3 gap-3">
                <Field label="Lookback (hours)">
                  <input type="number" className={inputClass} value={inputs.hc_lookback_hours} onChange={update('hc_lookback_hours')} data-full-ai-field={fullAIExamples.bind({ current: inputs.hc_lookback_hours, change: update('hc_lookback_hours'), label: "inputs.hc_lookback_hours", manual: false, json: false }, "p1-11723", undefined)} />
                </Field>
                <Field label="Min score">
                  <input type="number" step="0.05" className={inputClass} value={inputs.hc_min_score} onChange={update('hc_min_score')} data-full-ai-field={fullAIExamples.bind({ current: inputs.hc_min_score, change: update('hc_min_score'), label: "inputs.hc_min_score", manual: false, json: false }, "p1-11927", undefined)} />
                </Field>
                <Field label="Sample size">
                  <input type="number" className={inputClass} value={inputs.hc_sample_size} onChange={update('hc_sample_size')} data-full-ai-field={fullAIExamples.bind({ current: inputs.hc_sample_size, change: update('hc_sample_size'), label: "inputs.hc_sample_size", manual: false, json: false }, "p1-12135", undefined)} />
                </Field>
              </div>
            )}

            {activeTool === 'alert-rule-suggest' && (
              <Field label="Metric focus (optional)">
                <select className={inputClass} value={inputs.ar_metric_focus} onChange={update('ar_metric_focus')} data-full-ai-field={fullAIExamples.bind({ current: inputs.ar_metric_focus, change: update('ar_metric_focus'), label: "inputs.ar_metric_focus", manual: false, json: false }, "p1-12434", undefined)}>
                  <option value="">All metrics</option>
                  <option value="latency">Latency</option>
                  <option value="error_rate">Error rate</option>
                  <option value="drift">Drift</option>
                  <option value="hallucination">Hallucination</option>
                  <option value="tokens">Tokens</option>
                </select>
              </Field>
            )}

            {activeTool === 'explain-query' && (
              <Field label="Question" required>
                <textarea className={inputClass} rows={3} value={inputs.question} onChange={update('question')} placeholder="e.g. Why did p95 latency spike yesterday afternoon?" required data-full-ai-field={fullAIExamples.bind({ current: inputs.question, change: update('question'), label: "inputs.question", manual: false, json: false }, "p1-13075", undefined)} />
              </Field>
            )}

            <div className="pt-2">
              <button
                type="submit"
                disabled={mutation.isPending}
                className="bg-purple-600 text-white rounded px-4 py-2 text-sm font-medium hover:bg-purple-700 disabled:opacity-50 inline-flex items-center gap-2"
              >
                {mutation.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
                {mutation.isPending ? 'Generating insight...' : 'Generate insight'}
              </button>
            </div>
          </form>

          {isUnconfigured && (
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 flex gap-3">
              <AlertCircle className="w-5 h-5 text-yellow-600 flex-shrink-0 mt-0.5" />
              <div>
                <h3 className="text-sm font-semibold text-yellow-800">AI not configured</h3>
                <p className="text-xs text-yellow-700 mt-1">
                  The backend reports <code>OPENROUTER_API_KEY not configured</code>. Set the environment variable on the
                  observability backend and restart it to enable AI Insights.
                </p>
              </div>
            </div>
          )}

          {errorMessage && !isUnconfigured && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex gap-3">
              <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
              <div>
                <h3 className="text-sm font-semibold text-red-800">Request failed</h3>
                <p className="text-xs text-red-700 mt-1 font-mono break-all">{errorMessage}</p>
              </div>
            </div>
          )}

          {mutation.data && (
            <div className="bg-white rounded-lg shadow p-4 space-y-3">
              <div className="flex items-center justify-between text-xs text-gray-500">
                <span>Model: <code className="text-gray-700">{mutation.data.model}</code></span>
                {mutation.data.tokens_used != null && <span>{mutation.data.tokens_used} tokens</span>}
              </div>
              <ReadableAIResult value={mutation.data.insight} />
              {mutation.data.context && Object.keys(mutation.data.context).length > 0 && (
                <details className="text-xs text-gray-500">
                  <summary className="cursor-pointer hover:text-gray-700">Context (debug)</summary>
                  <ReadableAIResult value={mutation.data.context} />
                </details>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

const inputClass = 'w-full border rounded px-3 py-2 text-sm';

function Field({ label, required, children }: { label: string; required?: boolean; children: React.ReactNode }) {
  return (
    <label className="block">
      <span className="block text-xs text-gray-600 mb-1">{label}{required && <span className="text-red-500"> *</span>}</span>
      {children}
    </label>
  );
}
