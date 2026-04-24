import { useQuery } from '@tanstack/react-query';
import { fetchEventDetail } from '../../api/client';
import { X } from 'lucide-react';

interface Props {
  eventId: string;
  onClose: () => void;
}

export default function EventDetail({ eventId, onClose }: Props) {
  const { data: event, isLoading } = useQuery({
    queryKey: ['event', eventId],
    queryFn: () => fetchEventDetail(eventId),
  });

  if (isLoading) {
    return (
      <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg p-8">Loading...</div>
      </div>
    );
  }

  if (!event) return null;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-3xl max-h-[90vh] overflow-auto">
        <div className="flex items-center justify-between p-4 border-b">
          <h2 className="text-lg font-semibold">Event Details</h2>
          <button onClick={onClose} className="p-1 hover:bg-gray-100 rounded">
            <X className="w-5 h-5" />
          </button>
        </div>
        <div className="p-4 space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <InfoField label="Model" value={event.model_name} />
            <InfoField label="Provider" value={event.model_provider || '-'} />
            <InfoField label="Status" value={event.status} />
            <InfoField label="Latency" value={event.latency_ms ? `${event.latency_ms.toFixed(1)} ms` : '-'} />
            <InfoField label="Input Tokens" value={event.input_tokens?.toString() || '-'} />
            <InfoField label="Output Tokens" value={event.output_tokens?.toString() || '-'} />
            <InfoField label="Trace ID" value={event.trace_id || '-'} />
            <InfoField
              label="Hallucination Score"
              value={event.hallucination_score != null ? event.hallucination_score.toFixed(4) : 'Not scored'}
              highlight={event.hallucination_score != null && event.hallucination_score > 0.5}
            />
          </div>

          {event.input_text && (
            <div>
              <label className="block text-xs font-medium text-gray-500 uppercase mb-1">Input</label>
              <pre className="bg-gray-50 rounded p-3 text-sm text-gray-700 whitespace-pre-wrap max-h-40 overflow-auto">
                {event.input_text}
              </pre>
            </div>
          )}

          {event.output_text && (
            <div>
              <label className="block text-xs font-medium text-gray-500 uppercase mb-1">Output</label>
              <pre className="bg-gray-50 rounded p-3 text-sm text-gray-700 whitespace-pre-wrap max-h-40 overflow-auto">
                {event.output_text}
              </pre>
            </div>
          )}

          {event.error_message && (
            <div>
              <label className="block text-xs font-medium text-gray-500 uppercase mb-1">Error</label>
              <pre className="bg-red-50 rounded p-3 text-sm text-red-700 whitespace-pre-wrap">
                {event.error_message}
              </pre>
            </div>
          )}

          {event.metadata && Object.keys(event.metadata).length > 0 && (
            <div>
              <label className="block text-xs font-medium text-gray-500 uppercase mb-1">Metadata</label>
              <pre className="bg-gray-50 rounded p-3 text-sm text-gray-600 whitespace-pre-wrap">
                {JSON.stringify(event.metadata, null, 2)}
              </pre>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function InfoField({ label, value, highlight }: { label: string; value: string; highlight?: boolean }) {
  return (
    <div>
      <dt className="text-xs font-medium text-gray-500 uppercase">{label}</dt>
      <dd className={`mt-1 text-sm font-medium ${highlight ? 'text-red-600' : 'text-gray-900'}`}>
        {value}
      </dd>
    </div>
  );
}
