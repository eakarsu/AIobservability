import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend,
} from 'recharts';
import type { HallucinationScore } from '../../types';

interface Props {
  data: HallucinationScore[];
  title?: string;
}

export default function HallucinationChart({ data, title = 'Hallucination Scores Over Time' }: Props) {
  const formatted = data
    .sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime())
    .map(h => ({
      time: new Date(h.timestamp).toLocaleString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' }),
      score: h.score,
      method: h.method,
    }));

  return (
    <div className="bg-white rounded-lg shadow p-4">
      <h3 className="text-sm font-semibold text-gray-700 mb-3">{title}</h3>
      <ResponsiveContainer width="100%" height={300}>
        <AreaChart data={formatted}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
          <XAxis dataKey="time" tick={{ fontSize: 10 }} />
          <YAxis tick={{ fontSize: 11 }} domain={[0, 1]} />
          <Tooltip
            formatter={(value: number) => [value.toFixed(4), 'Score']}
            contentStyle={{ fontSize: 12 }}
          />
          <Legend />
          <Area
            type="monotone"
            dataKey="score"
            stroke="#ef4444"
            fill="#fecaca"
            strokeWidth={2}
            name="Hallucination Score"
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
