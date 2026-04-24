import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { fetchOverview, fetchLatencyTimeseries, fetchEvents } from '../api/client';
import LatencyChart from '../components/charts/LatencyChart';
import EventTable from '../components/telemetry/EventTable';
import EventDetail from '../components/telemetry/EventDetail';
import { Activity, Clock, AlertTriangle, Zap, Hash, TrendingDown } from 'lucide-react';

export default function Overview() {
  const [window, setWindow] = useState('24h');
  const [selectedEventId, setSelectedEventId] = useState<string | null>(null);

  const { data: overview, isLoading } = useQuery({
    queryKey: ['overview', window],
    queryFn: () => fetchOverview(window),
  });

  const { data: latency } = useQuery({
    queryKey: ['latency', window],
    queryFn: () => fetchLatencyTimeseries({ bucket: '1h' }),
  });

  const { data: events } = useQuery({
    queryKey: ['recentEvents'],
    queryFn: () => fetchEvents({ limit: 10 }),
  });

  if (isLoading) {
    return <div className="flex items-center justify-center h-64 text-gray-400">Loading dashboard...</div>;
  }

  const stats = [
    { label: 'Total Events', value: overview?.total_events.toLocaleString() || '0', icon: Activity, color: 'text-blue-600', bg: 'bg-blue-50' },
    { label: 'Avg Latency', value: `${overview?.avg_latency_ms.toFixed(0) || 0} ms`, icon: Clock, color: 'text-green-600', bg: 'bg-green-50' },
    { label: 'P95 Latency', value: `${overview?.p95_latency_ms.toFixed(0) || 0} ms`, icon: Zap, color: 'text-purple-600', bg: 'bg-purple-50' },
    { label: 'Error Rate', value: `${overview?.error_rate.toFixed(1) || 0}%`, icon: AlertTriangle, color: overview?.error_rate && overview.error_rate > 5 ? 'text-red-600' : 'text-green-600', bg: overview?.error_rate && overview.error_rate > 5 ? 'bg-red-50' : 'bg-green-50' },
    { label: 'Events/Hour', value: overview?.events_last_hour.toLocaleString() || '0', icon: Hash, color: 'text-indigo-600', bg: 'bg-indigo-50' },
    { label: 'Drift Score', value: overview?.latest_drift_score?.toFixed(3) || 'N/A', icon: TrendingDown, color: overview?.latest_drift_score && overview.latest_drift_score > 0.1 ? 'text-orange-600' : 'text-green-600', bg: overview?.latest_drift_score && overview.latest_drift_score > 0.1 ? 'bg-orange-50' : 'bg-green-50' },
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Dashboard Overview</h1>
        <select
          value={window}
          onChange={e => setWindow(e.target.value)}
          className="border rounded px-3 py-1.5 text-sm"
        >
          <option value="1h">Last 1 hour</option>
          <option value="6h">Last 6 hours</option>
          <option value="24h">Last 24 hours</option>
          <option value="7d">Last 7 days</option>
        </select>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        {stats.map(stat => (
          <div key={stat.label} className={`${stat.bg} rounded-lg p-4`}>
            <div className="flex items-center gap-2 mb-1">
              <stat.icon className={`w-4 h-4 ${stat.color}`} />
              <span className="text-xs text-gray-500">{stat.label}</span>
            </div>
            <p className={`text-xl font-bold ${stat.color}`}>{stat.value}</p>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {latency && <LatencyChart data={latency.points} title="Latency Trend (1h buckets)" />}
        <div className="bg-white rounded-lg shadow p-4">
          <h3 className="text-sm font-semibold text-gray-700 mb-3">Hallucination Rate</h3>
          <div className="flex items-center justify-center h-[280px]">
            <div className="text-center">
              <p className={`text-5xl font-bold ${
                overview?.hallucination_rate && overview.hallucination_rate > 0.3 ? 'text-red-500' : 'text-green-500'
              }`}>
                {((overview?.hallucination_rate || 0) * 100).toFixed(1)}%
              </p>
              <p className="text-sm text-gray-400 mt-2">Average hallucination score</p>
              <div className="mt-4 flex items-center gap-2 justify-center">
                <div className="w-3 h-3 rounded-full bg-green-400" />
                <span className="text-xs text-gray-500">&lt;10% Good</span>
                <div className="w-3 h-3 rounded-full bg-yellow-400 ml-2" />
                <span className="text-xs text-gray-500">10-30% Warning</span>
                <div className="w-3 h-3 rounded-full bg-red-400 ml-2" />
                <span className="text-xs text-gray-500">&gt;30% Critical</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div>
        <h2 className="text-lg font-semibold text-gray-900 mb-3">Recent Events</h2>
        {events && (
          <EventTable
            events={events}
            onSelect={e => setSelectedEventId(e.id)}
          />
        )}
      </div>

      {selectedEventId && (
        <EventDetail
          eventId={selectedEventId}
          onClose={() => setSelectedEventId(null)}
        />
      )}
    </div>
  );
}
