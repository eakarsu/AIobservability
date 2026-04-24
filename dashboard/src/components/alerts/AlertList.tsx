import type { AlertFired } from '../../types';
import { AlertTriangle, CheckCircle, Clock } from 'lucide-react';

interface Props {
  alerts: AlertFired[];
}

const statusConfig = {
  firing: { icon: AlertTriangle, color: 'text-red-500', bg: 'bg-red-50', label: 'Firing' },
  resolved: { icon: CheckCircle, color: 'text-green-500', bg: 'bg-green-50', label: 'Resolved' },
  acknowledged: { icon: Clock, color: 'text-yellow-500', bg: 'bg-yellow-50', label: 'Acknowledged' },
};

export default function AlertList({ alerts }: Props) {
  if (alerts.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow p-6 text-center text-gray-400">
        No alerts
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow divide-y">
      {alerts.map(alert => {
        const config = statusConfig[alert.status as keyof typeof statusConfig] || statusConfig.firing;
        const Icon = config.icon;

        return (
          <div key={alert.id} className={`p-4 flex items-start gap-3 ${config.bg}`}>
            <Icon className={`w-5 h-5 mt-0.5 ${config.color}`} />
            <div className="flex-1">
              <div className="flex items-center justify-between">
                <span className={`text-sm font-medium ${config.color}`}>{config.label}</span>
                <span className="text-xs text-gray-400">
                  {new Date(alert.triggered_at).toLocaleString()}
                </span>
              </div>
              <p className="text-sm text-gray-700 mt-1">
                Metric value: <span className="font-mono font-medium">{alert.metric_value.toFixed(4)}</span>
              </p>
              {alert.resolved_at && (
                <p className="text-xs text-gray-400 mt-1">
                  Resolved: {new Date(alert.resolved_at).toLocaleString()}
                </p>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
