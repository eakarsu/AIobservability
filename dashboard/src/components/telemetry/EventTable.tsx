import type { TelemetryEvent } from '../../types';

interface Props {
  events: TelemetryEvent[];
  onSelect?: (event: TelemetryEvent) => void;
}

export default function EventTable({ events, onSelect }: Props) {
  return (
    <div className="bg-white rounded-lg shadow overflow-hidden">
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Time</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Model</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Latency</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Tokens</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Trace</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {events.map(event => (
              <tr
                key={event.id}
                onClick={() => onSelect?.(event)}
                className="hover:bg-gray-50 cursor-pointer transition-colors"
              >
                <td className="px-4 py-3 text-sm text-gray-600 whitespace-nowrap">
                  {new Date(event.timestamp).toLocaleString([], {
                    month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit', second: '2-digit',
                  })}
                </td>
                <td className="px-4 py-3 text-sm">
                  <span className="font-medium text-gray-900">{event.model_name}</span>
                  {event.model_provider && (
                    <span className="ml-1 text-xs text-gray-400">({event.model_provider})</span>
                  )}
                </td>
                <td className="px-4 py-3">
                  <span className={`inline-flex px-2 py-0.5 text-xs font-medium rounded-full ${
                    event.status === 'success'
                      ? 'bg-green-100 text-green-800'
                      : 'bg-red-100 text-red-800'
                  }`}>
                    {event.status}
                  </span>
                </td>
                <td className="px-4 py-3 text-sm text-gray-600">
                  {event.latency_ms ? `${event.latency_ms.toFixed(0)} ms` : '-'}
                </td>
                <td className="px-4 py-3 text-sm text-gray-600">
                  {event.input_tokens != null && event.output_tokens != null
                    ? `${event.input_tokens} / ${event.output_tokens}`
                    : '-'}
                </td>
                <td className="px-4 py-3 text-sm text-gray-400 font-mono text-xs">
                  {event.trace_id ? event.trace_id.slice(0, 8) : '-'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {events.length === 0 && (
        <div className="text-center py-8 text-gray-400">No events found</div>
      )}
    </div>
  );
}
