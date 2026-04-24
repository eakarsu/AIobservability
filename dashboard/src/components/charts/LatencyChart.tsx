import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend,
} from 'recharts';
import type { MetricPoint } from '../../types';

interface Props {
  data: MetricPoint[];
  title?: string;
}

export default function LatencyChart({ data, title = 'Latency Over Time' }: Props) {
  const formatted = data.map(p => ({
    time: new Date(p.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    latency: p.value,
  }));

  return (
    <div className="bg-white rounded-lg shadow p-4">
      <h3 className="text-sm font-semibold text-gray-700 mb-3">{title}</h3>
      <ResponsiveContainer width="100%" height={280}>
        <LineChart data={formatted}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
          <XAxis dataKey="time" tick={{ fontSize: 11 }} />
          <YAxis tick={{ fontSize: 11 }} label={{ value: 'ms', angle: -90, position: 'insideLeft' }} />
          <Tooltip
            formatter={(value: number) => [`${value.toFixed(1)} ms`, 'Latency']}
            contentStyle={{ fontSize: 12 }}
          />
          <Legend />
          <Line
            type="monotone"
            dataKey="latency"
            stroke="#3b82f6"
            strokeWidth={2}
            dot={false}
            name="Avg Latency (ms)"
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
