import { Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/Layout';
import Overview from './pages/Overview';
import ModelPerformance from './pages/ModelPerformance';
import DriftAnalysis from './pages/DriftAnalysis';
import HallucinationReport from './pages/HallucinationReport';
import Alerts from './pages/Alerts';
import Settings from './pages/Settings';

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<Navigate to="/overview" replace />} />
        <Route path="overview" element={<Overview />} />
        <Route path="performance" element={<ModelPerformance />} />
        <Route path="drift" element={<DriftAnalysis />} />
        <Route path="hallucinations" element={<HallucinationReport />} />
        <Route path="alerts" element={<Alerts />} />
        <Route path="settings" element={<Settings />} />
      </Route>
    </Routes>
  );
}
