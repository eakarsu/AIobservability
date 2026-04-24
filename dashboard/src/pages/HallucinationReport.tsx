import { useQuery } from '@tanstack/react-query';
import { fetchHallucinationScores, fetchEvents } from '../api/client';
import HallucinationChart from '../components/charts/HallucinationChart';
import EventTable from '../components/telemetry/EventTable';
import EventDetail from '../components/telemetry/EventDetail';
import { useState } from 'react';
import { AlertTriangle, Eye } from 'lucide-react';

export default function HallucinationReport() {
  const [selectedEventId, setSelectedEventId] = useState<string | null>(null);

  const { data: scores, isLoading } = useQuery({
    queryKey: ['hallucinations'],
    queryFn: () => fetchHallucinationScores({ limit: 200 }),
  });

  const { data: events } = useQuery({
    queryKey: ['events-hall'],
    queryFn: () => fetchEvents({ limit: 20 }),
  });

  if (isLoading) {
    return <div className="flex items-center justify-center h-64 text-gray-400">Loading hallucination report...</div>;
  }

  const halScores = scores || [];

  // Summary stats
  const avgScore = halScores.length > 0
    ? halScores.reduce((sum, s) => sum + s.score, 0) / halScores.length
    : 0;
  const highRisk = halScores.filter(s => s.score > 0.5).length;
  const medRisk = halScores.filter(s => s.score > 0.2 && s.score <= 0.5).length;

  // Group by method
  const methodGroups = halScores.reduce((acc, s) => {
    if (!acc[s.method]) acc[s.method] = [];
    acc[s.method].push(s);
    return acc;
  }, {} as Record<string, typeof halScores>);

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <Eye className="w-7 h-7 text-red-500" />
        <h1 className="text-2xl font-bold text-gray-900">Hallucination Report</h1>
      </div>

      <div className="bg-white rounded-lg shadow p-4">
        <h3 className="text-sm font-semibold text-gray-700 mb-2">About Hallucination Detection</h3>
        <p className="text-sm text-gray-500">
          Hallucinations occur when AI models generate incorrect, fabricated, or unsupported information.
          We detect them using semantic similarity analysis, NLI contradiction checking, and heuristic patterns.
        </p>
      </div>

      {/* Summary cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white rounded-lg shadow p-4 text-center">
          <p className="text-xs text-gray-500 uppercase">Avg Score</p>
          <p className={`text-3xl font-bold mt-1 ${avgScore > 0.3 ? 'text-red-500' : 'text-green-500'}`}>
            {(avgScore * 100).toFixed(1)}%
          </p>
        </div>
        <div className="bg-white rounded-lg shadow p-4 text-center">
          <p className="text-xs text-gray-500 uppercase">Total Scored</p>
          <p className="text-3xl font-bold mt-1 text-blue-500">{halScores.length}</p>
        </div>
        <div className="bg-red-50 rounded-lg shadow p-4 text-center">
          <p className="text-xs text-red-500 uppercase">High Risk (&gt;50%)</p>
          <p className="text-3xl font-bold mt-1 text-red-600">{highRisk}</p>
        </div>
        <div className="bg-yellow-50 rounded-lg shadow p-4 text-center">
          <p className="text-xs text-yellow-600 uppercase">Medium Risk (20-50%)</p>
          <p className="text-3xl font-bold mt-1 text-yellow-600">{medRisk}</p>
        </div>
      </div>

      {halScores.length > 0 ? (
        <HallucinationChart data={halScores} />
      ) : (
        <div className="bg-white rounded-lg shadow p-8 text-center text-gray-400">
          <AlertTriangle className="w-12 h-12 mx-auto mb-3 text-gray-300" />
          <p>No hallucination scores available yet.</p>
          <p className="text-xs mt-1">Scores are computed asynchronously after events are ingested.</p>
        </div>
      )}

      {/* Method breakdown */}
      {Object.keys(methodGroups).length > 0 && (
        <div className="bg-white rounded-lg shadow p-4">
          <h3 className="text-sm font-semibold text-gray-700 mb-3">Detection Method Breakdown</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {Object.entries(methodGroups).map(([method, data]) => {
              const avg = data.reduce((s, d) => s + d.score, 0) / data.length;
              return (
                <div key={method} className="border rounded-lg p-3">
                  <p className="text-sm font-medium text-gray-700 capitalize">{method.replace('_', ' ')}</p>
                  <p className="text-2xl font-bold text-gray-900 mt-1">{(avg * 100).toFixed(1)}%</p>
                  <p className="text-xs text-gray-400">{data.length} samples</p>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Events table */}
      <div>
        <h2 className="text-lg font-semibold text-gray-900 mb-3">Recent Events (click to see scores)</h2>
        {events && (
          <EventTable events={events} onSelect={e => setSelectedEventId(e.id)} />
        )}
      </div>

      {selectedEventId && (
        <EventDetail eventId={selectedEventId} onClose={() => setSelectedEventId(null)} />
      )}
    </div>
  );
}
