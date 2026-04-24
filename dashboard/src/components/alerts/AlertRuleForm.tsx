import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { createAlertRule } from '../../api/client';

export default function AlertRuleForm() {
  const queryClient = useQueryClient();
  const [form, setForm] = useState({
    name: '',
    metric_type: 'latency',
    condition: 'gt',
    threshold: 0,
    window_minutes: 5,
    webhook_url: '',
  });

  const mutation = useMutation({
    mutationFn: () =>
      createAlertRule({
        name: form.name,
        metric_type: form.metric_type,
        condition: form.condition,
        threshold: form.threshold,
        window_minutes: form.window_minutes,
        notification_channel: form.webhook_url ? { webhook_url: form.webhook_url } : {},
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['alertRules'] });
      setForm({ name: '', metric_type: 'latency', condition: 'gt', threshold: 0, window_minutes: 5, webhook_url: '' });
    },
  });

  return (
    <div className="bg-white rounded-lg shadow p-4">
      <h3 className="text-sm font-semibold text-gray-700 mb-3">Create Alert Rule</h3>
      <div className="grid grid-cols-2 gap-3">
        <div className="col-span-2">
          <label className="block text-xs text-gray-500 mb-1">Rule Name</label>
          <input
            type="text"
            value={form.name}
            onChange={e => setForm(f => ({ ...f, name: e.target.value }))}
            className="w-full border rounded px-3 py-2 text-sm"
            placeholder="High latency alert"
          />
        </div>
        <div>
          <label className="block text-xs text-gray-500 mb-1">Metric</label>
          <select
            value={form.metric_type}
            onChange={e => setForm(f => ({ ...f, metric_type: e.target.value }))}
            className="w-full border rounded px-3 py-2 text-sm"
          >
            <option value="latency">Latency (ms)</option>
            <option value="error_rate">Error Rate (%)</option>
            <option value="drift_score">Drift Score</option>
            <option value="hallucination_score">Hallucination Score</option>
            <option value="token_usage">Token Usage</option>
          </select>
        </div>
        <div>
          <label className="block text-xs text-gray-500 mb-1">Condition</label>
          <select
            value={form.condition}
            onChange={e => setForm(f => ({ ...f, condition: e.target.value }))}
            className="w-full border rounded px-3 py-2 text-sm"
          >
            <option value="gt">Greater than</option>
            <option value="lt">Less than</option>
            <option value="gte">Greater or equal</option>
            <option value="lte">Less or equal</option>
          </select>
        </div>
        <div>
          <label className="block text-xs text-gray-500 mb-1">Threshold</label>
          <input
            type="number"
            value={form.threshold}
            onChange={e => setForm(f => ({ ...f, threshold: parseFloat(e.target.value) || 0 }))}
            className="w-full border rounded px-3 py-2 text-sm"
            step="0.01"
          />
        </div>
        <div>
          <label className="block text-xs text-gray-500 mb-1">Window (min)</label>
          <input
            type="number"
            value={form.window_minutes}
            onChange={e => setForm(f => ({ ...f, window_minutes: parseInt(e.target.value) || 5 }))}
            className="w-full border rounded px-3 py-2 text-sm"
            min="1"
          />
        </div>
        <div className="col-span-2">
          <label className="block text-xs text-gray-500 mb-1">Webhook URL (optional)</label>
          <input
            type="url"
            value={form.webhook_url}
            onChange={e => setForm(f => ({ ...f, webhook_url: e.target.value }))}
            className="w-full border rounded px-3 py-2 text-sm"
            placeholder="https://hooks.slack.com/..."
          />
        </div>
        <div className="col-span-2">
          <button
            onClick={() => mutation.mutate()}
            disabled={!form.name || mutation.isPending}
            className="w-full bg-blue-600 text-white rounded py-2 text-sm font-medium hover:bg-blue-700 disabled:opacity-50 transition-colors"
          >
            {mutation.isPending ? 'Creating...' : 'Create Rule'}
          </button>
        </div>
      </div>
    </div>
  );
}
