import { useQuery } from '@tanstack/react-query';
import { fetchLatencyTimeseries, fetchTokenTimeseries, fetchEvents } from '../api/client';
import LatencyChart from '../components/charts/LatencyChart';
import TokenUsageChart from '../components/charts/TokenUsageChart';
import EventTable from '../components/telemetry/EventTable';
import { useState } from 'react';
import EventDetail from '../components/telemetry/EventDetail';

export default function ModelPerformance() {
  const [selectedEventId, setSelectedEventId] = useState<string | null>(null);

  const { data: latency } = useQuery({
    queryKey: ['latency-perf'],
    queryFn: () => fetchLatencyTimeseries({ bucket: '5m' }),
  });

  const { data: tokens } = useQuery({
    queryKey: ['tokens-perf'],
    queryFn: () => fetchTokenTimeseries(),
  });

  const { data: events } = useQuery({
    queryKey: ['events-perf'],
    queryFn: () => fetchEvents({ limit: 20 }),
  });

  const { data: errors } = useQuery({
    queryKey: ['events-errors'],
    queryFn: () => fetchEvents({ status: 'error', limit: 10 }),
  });

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">Model Performance</h1>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {latency && <LatencyChart data={latency.points} title="Latency Distribution (5m buckets)" />}
        {tokens && <TokenUsageChart data={tokens.points} />}
      </div>

      <div>
        <h2 className="text-lg font-semibold text-gray-900 mb-3">Recent Invocations</h2>
        {events && (
          <EventTable events={events} onSelect={e => setSelectedEventId(e.id)} />
        )}
      </div>

      {errors && errors.length > 0 && (
        <div>
          <h2 className="text-lg font-semibold text-red-600 mb-3">Recent Errors</h2>
          <EventTable events={errors} onSelect={e => setSelectedEventId(e.id)} />
        </div>
      )}

      {selectedEventId && (
        <EventDetail eventId={selectedEventId} onClose={() => setSelectedEventId(null)} />
      )}
    </div>
  );
}
