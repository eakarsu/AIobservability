import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  Activity,
  TrendingDown,
  AlertTriangle,
  Bell,
  Settings,
  Brain,
} from 'lucide-react';

const navItems = [
  { to: '/overview', icon: LayoutDashboard, label: 'Overview' },
  { to: '/performance', icon: Activity, label: 'Model Performance' },
  { to: '/drift', icon: TrendingDown, label: 'Drift Analysis' },
  { to: '/hallucinations', icon: AlertTriangle, label: 'Hallucinations' },
  { to: '/alerts', icon: Bell, label: 'Alerts' },
  { to: '/settings', icon: Settings, label: 'Settings' },
];

export default function Sidebar() {
  return (
    <aside className="w-64 bg-gray-900 text-white flex flex-col">
      <div className="p-4 border-b border-gray-700">
        <div className="flex items-center gap-2">
          <Brain className="w-8 h-8 text-blue-400" />
          <div>
            <h1 className="text-lg font-bold">AI Observe</h1>
            <p className="text-xs text-gray-400">Observability Platform</p>
          </div>
        </div>
      </div>
      <nav className="flex-1 py-4">
        {navItems.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              `flex items-center gap-3 px-4 py-3 text-sm transition-colors ${
                isActive
                  ? 'bg-blue-600 text-white border-r-2 border-blue-400'
                  : 'text-gray-300 hover:bg-gray-800 hover:text-white'
              }`
            }
          >
            <Icon className="w-5 h-5" />
            {label}
          </NavLink>
        ))}
      </nav>
      <div className="p-4 border-t border-gray-700 text-xs text-gray-500">
        AI Observability v1.0
      </div>
    </aside>
  );
}
