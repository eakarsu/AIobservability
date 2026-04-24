import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend,
} from 'recharts';
import type { MetricPoint } from '../../types';

interface Props {
  data: MetricPoint[];
  title?: string;
}

export default function TokenUsageChart({ data, title = 'Token Usage Over Time' }: Props) {
  const formatted = data.map(p => ({
    time: new Date(p.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    tokens: Math.round(p.value),
  }));

  return (
    <div className="bg-white rounded-lg shadow p-4">
      <h3 className="text-sm font-semibold text-gray-700 mb-3">{title}</h3>
      <ResponsiveContainer width="100%" height={280}>
        <BarChart data={formatted}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
          <XAxis dataKey="time" tick={{ fontSize: 11 }} />
          <YAxis tick={{ fontSize: 11 }} />
          <Tooltip formatter={(value: number) => [value, 'Avg Tokens']} contentStyle={{ fontSize: 12 }} />
          <Legend />
          <Bar dataKey="tokens" fill="#8b5cf6" name="Avg Total Tokens" radius={[2, 2, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
