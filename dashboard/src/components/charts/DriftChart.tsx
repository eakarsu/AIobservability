import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend, ReferenceLine,
} from 'recharts';
import type { DriftScore } from '../../types';

interface Props {
  data: DriftScore[];
  title?: string;
}

export default function DriftChart({ data, title = 'Drift Scores Over Time' }: Props) {
  const formatted = data
    .sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime())
    .map(d => ({
      time: new Date(d.timestamp).toLocaleString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' }),
      score: d.score,
      metric: d.metric_name,
      model: d.model_name,
    }));

  return (
    <div className="bg-white rounded-lg shadow p-4">
      <h3 className="text-sm font-semibold text-gray-700 mb-3">{title}</h3>
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={formatted}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
          <XAxis dataKey="time" tick={{ fontSize: 10 }} />
          <YAxis tick={{ fontSize: 11 }} domain={[0, 1]} />
          <Tooltip
            formatter={(value: number) => [value.toFixed(4), 'Score']}
            labelFormatter={(label) => `Time: ${label}`}
            contentStyle={{ fontSize: 12 }}
          />
          <Legend />
          <ReferenceLine y={0.1} stroke="#f59e0b" strokeDasharray="5 5" label="Warning" />
          <ReferenceLine y={0.25} stroke="#ef4444" strokeDasharray="5 5" label="Critical" />
          <Line
            type="monotone"
            dataKey="score"
            stroke="#f97316"
            strokeWidth={2}
            dot={{ r: 3 }}
            name="Drift Score"
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
