import { useQuery } from '@tanstack/react-query';
import { fetchDriftScores } from '../api/client';
import DriftChart from '../components/charts/DriftChart';
import { TrendingDown, CheckCircle, AlertTriangle } from 'lucide-react';

export default function DriftAnalysis() {
  const { data: driftScores, isLoading } = useQuery({
    queryKey: ['drift'],
    queryFn: () => fetchDriftScores({ limit: 200 }),
  });

  if (isLoading) {
    return <div className="flex items-center justify-center h-64 text-gray-400">Loading drift analysis...</div>;
  }

  const scores = driftScores || [];

  // Group by metric name for summary
  const metricGroups = scores.reduce((acc, s) => {
    const key = s.metric_name;
    if (!acc[key]) acc[key] = [];
    acc[key].push(s);
    return acc;
  }, {} as Record<string, typeof scores>);

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <TrendingDown className="w-7 h-7 text-orange-500" />
        <h1 className="text-2xl font-bold text-gray-900">Drift Analysis</h1>
      </div>

      <div className="bg-white rounded-lg shadow p-4">
        <h3 className="text-sm font-semibold text-gray-700 mb-2">What is Model Drift?</h3>
        <p className="text-sm text-gray-500">
          Model drift occurs when the statistical properties of model inputs or outputs change over time,
          potentially degrading model performance. We monitor drift using KS tests, PSI, and Jensen-Shannon Divergence.
        </p>
      </div>

      {/* Summary cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {Object.entries(metricGroups).slice(0, 6).map(([metric, data]) => {
          const latest = data.sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())[0];
          const isDrifted = latest.score > 0.1;

          return (
            <div key={metric} className={`rounded-lg p-4 ${isDrifted ? 'bg-orange-50 border border-orange-200' : 'bg-green-50 border border-green-200'}`}>
              <div className="flex items-center gap-2 mb-1">
                {isDrifted ? (
                  <AlertTriangle className="w-4 h-4 text-orange-500" />
                ) : (
                  <CheckCircle className="w-4 h-4 text-green-500" />
                )}
                <span className="text-xs font-medium text-gray-600 truncate">{metric}</span>
              </div>
              <p className={`text-2xl font-bold ${isDrifted ? 'text-orange-600' : 'text-green-600'}`}>
                {latest.score.toFixed(4)}
              </p>
              <p className="text-xs text-gray-400">{latest.model_name}</p>
            </div>
          );
        })}
      </div>

      {scores.length > 0 ? (
        <DriftChart data={scores} />
      ) : (
        <div className="bg-white rounded-lg shadow p-8 text-center text-gray-400">
          <TrendingDown className="w-12 h-12 mx-auto mb-3 text-gray-300" />
          <p>No drift data available yet. Drift detection runs every 15 minutes.</p>
          <p className="text-xs mt-1">Ensure you have at least 48 hours of telemetry data.</p>
        </div>
      )}

      {/* Detailed scores table */}
      {scores.length > 0 && (
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <div className="px-4 py-3 border-b">
            <h3 className="text-sm font-semibold text-gray-700">Drift Score History</h3>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Time</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Model</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Metric</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Score</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">P-Value</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {scores.slice(0, 50).map(s => (
                  <tr key={s.id}>
                    <td className="px-4 py-2 text-sm text-gray-600">{new Date(s.timestamp).toLocaleString()}</td>
                    <td className="px-4 py-2 text-sm font-medium text-gray-900">{s.model_name}</td>
                    <td className="px-4 py-2 text-sm text-gray-600">{s.metric_name}</td>
                    <td className="px-4 py-2 text-sm font-mono">{s.score.toFixed(4)}</td>
                    <td className="px-4 py-2 text-sm font-mono">{s.p_value?.toFixed(4) || '-'}</td>
                    <td className="px-4 py-2">
                      <span className={`inline-flex px-2 py-0.5 text-xs font-medium rounded-full ${
                        s.score > 0.25 ? 'bg-red-100 text-red-800' :
                        s.score > 0.1 ? 'bg-yellow-100 text-yellow-800' :
                        'bg-green-100 text-green-800'
                      }`}>
                        {s.score > 0.25 ? 'Critical' : s.score > 0.1 ? 'Warning' : 'Normal'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
