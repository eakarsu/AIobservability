import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { fetchAlertRules, fetchAlertHistory, deleteAlertRule } from '../api/client';
import AlertList from '../components/alerts/AlertList';
import AlertRuleForm from '../components/alerts/AlertRuleForm';
import { Bell, Trash2 } from 'lucide-react';

export default function Alerts() {
  const queryClient = useQueryClient();

  const { data: rules } = useQuery({
    queryKey: ['alertRules'],
    queryFn: fetchAlertRules,
  });

  const { data: history } = useQuery({
    queryKey: ['alertHistory'],
    queryFn: () => fetchAlertHistory({ limit: 50 }),
  });

  const deleteMutation = useMutation({
    mutationFn: deleteAlertRule,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['alertRules'] }),
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <Bell className="w-7 h-7 text-blue-500" />
        <h1 className="text-2xl font-bold text-gray-900">Alerts</h1>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-4">
          {/* Active rules */}
          <div className="bg-white rounded-lg shadow">
            <div className="px-4 py-3 border-b">
              <h3 className="text-sm font-semibold text-gray-700">Alert Rules</h3>
            </div>
            {rules && rules.length > 0 ? (
              <div className="divide-y">
                {rules.map(rule => (
                  <div key={rule.id} className="p-4 flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-gray-900">{rule.name}</p>
                      <p className="text-xs text-gray-500 mt-0.5">
                        {rule.metric_type} {rule.condition} {rule.threshold} (window: {rule.window_minutes}m)
                      </p>
                    </div>
                    <div className="flex items-center gap-3">
                      <span className={`inline-flex px-2 py-0.5 text-xs font-medium rounded-full ${
                        rule.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-600'
                      }`}>
                        {rule.is_active ? 'Active' : 'Disabled'}
                      </span>
                      <button
                        onClick={() => deleteMutation.mutate(rule.id)}
                        className="p-1 text-gray-400 hover:text-red-500 transition-colors"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="p-6 text-center text-gray-400 text-sm">No alert rules configured</div>
            )}
          </div>

          {/* Alert history */}
          <div>
            <h3 className="text-sm font-semibold text-gray-700 mb-2">Alert History</h3>
            <AlertList alerts={history || []} />
          </div>
        </div>

        <div>
          <AlertRuleForm />
        </div>
      </div>
    </div>
  );
}
