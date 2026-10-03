import { Routes, Route, Navigate } from 'react-router-dom';
import { useEffect, useState, type FormEvent, type ReactNode } from 'react';
import Layout from './components/Layout';
import Overview from './pages/Overview';
import ModelPerformance from './pages/ModelPerformance';
import DriftAnalysis from './pages/DriftAnalysis';
import HallucinationReport from './pages/HallucinationReport';
import Alerts from './pages/Alerts';
import Settings from './pages/Settings';
import AIInsights from './pages/AIInsights';

// // === Batch 06 Gaps & Frontend Mounts ===
import CFLlmCostLatencyDashboardsPage from './pages/CFLlmCostLatencyDashboardsPage';
import CFPromptRegressionDetectorPage from './pages/CFPromptRegressionDetectorPage';
import CFTraceReplayPage from './pages/CFTraceReplayPage';
import CFEvalHarnessIntegrationPage from './pages/CFEvalHarnessIntegrationPage';
import CFOpentelemetryCompatibilityPage from './pages/CFOpentelemetryCompatibilityPage';
import GapNoExplicitAnomalyPage from './pages/GapNoExplicitAnomalyPage';
import GapNoCostPage from './pages/GapNoCostPage';
import GapNoDriftPage from './pages/GapNoDriftPage';
import GapNoRootPage from './pages/GapNoRootPage';
import GapNoAuthenticationOrRbacLayerVisiblePage from './pages/GapNoAuthenticationOrRbacLayerVisiblePage';
import GapNoBillingUsageMeteringPage from './pages/GapNoBillingUsageMeteringPage';
import GapNoWebhooksForAlertDeliverySlackPagerdutyPage from './pages/GapNoWebhooksForAlertDeliverySlackPagerdutyPage';
import GapNoRetentionArchivalPoliciesForTelemetryPage from './pages/GapNoRetentionArchivalPoliciesForTelemetryPage';
import GapLimitedIntegrationsOnlyOwnSdkNoOpentelemetryPage from './pages/GapLimitedIntegrationsOnlyOwnSdkNoOpentelemetryPage';
import GapNoAuditLoggingPage from './pages/GapNoAuditLoggingPage';
import CodexCustomVizFeature from './pages/CodexCustomVizFeature';
import CodexOperationsFeature from './pages/CodexOperationsFeature';
import PromptInjectionExposure from './pages/PromptInjectionExposure';

function AuthGate({ children }: { children: ReactNode }) {
  const [authenticated, setAuthenticated] = useState(false);
  const [checking, setChecking] = useState(true);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  useEffect(() => {
    const token = sessionStorage.getItem('observability_access_token');
    if (!token) return setChecking(false);
    fetch('/api/auth/me', { headers: { Authorization: `Bearer ${token}` } })
      .then((response) => setAuthenticated(response.ok))
      .finally(() => setChecking(false));
  }, []);

  async function fillDemoCredentials() {
    setError('');
    const response = await fetch('/api/auth/demo-credentials');
    if (!response.ok) return setError('Demo credentials are unavailable.');
    const credentials = await response.json();
    setEmail(credentials.email);
    setPassword(credentials.password)

  }

  async function signIn(event: FormEvent) {
    event.preventDefault();
    setError('');
    const response = await fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    });
    if (!response.ok) return setError('Sign in failed.');
    const result = await response.json();
    sessionStorage.setItem('observability_access_token', result.token);
    setAuthenticated(true);
  }

  if (checking) return <main className="min-h-screen bg-gray-950 text-white grid place-items-center">Checking session…</main>;
  if (!authenticated) return <main className="min-h-screen bg-gray-950 text-white grid place-items-center p-6"><section className="w-full max-w-md rounded-2xl bg-gray-900 p-8 shadow-2xl"><h1 className="text-3xl font-bold">Observability Sign In</h1><p className="mt-2 text-gray-400">Access the authenticated model operations dashboard.</p><form className="mt-6 grid gap-4" onSubmit={signIn}><label>Email<input className="mt-1 w-full rounded-lg border border-gray-600 bg-gray-950 p-3" type="email" required value={email} onChange={(event) => setEmail(event.target.value)} /></label><label>Password<input className="mt-1 w-full rounded-lg border border-gray-600 bg-gray-950 p-3" type="password" required value={password} onChange={(event) => setPassword(event.target.value)} /></label>{error && <p role="alert" className="text-red-300">{error}</p>}<button type="button" className="rounded-lg border border-cyan-500 p-3" onClick={fillDemoCredentials}>Auto Fill Demo Credentials</button><button type="submit" className="rounded-lg bg-cyan-600 p-3 font-semibold">Sign In</button></form></section></main>;
  return children;
}

export default function App() {
  return (
    <AuthGate>
    <Routes>
        <Route path="/codex/custom-viz" element={<CodexCustomVizFeature />} />
        <Route path="/codex/operations" element={<CodexOperationsFeature />} />

      <Route path="/" element={<Layout />}>
        <Route index element={<Navigate to="/overview" replace />} />
        <Route path="overview" element={<Overview />} />
        <Route path="performance" element={<ModelPerformance />} />
        <Route path="drift" element={<DriftAnalysis />} />
        <Route path="hallucinations" element={<HallucinationReport />} />
        <Route path="alerts" element={<Alerts />} />
        <Route path="ai-insights" element={<AIInsights />} />
        <Route path="settings" element={<Settings />} />
        <Route path="prompt-injection" element={<PromptInjectionExposure />} />
      </Route>
    
          {/* // === Batch 06 Gaps & Frontend Mounts === */}
          <Route path="/cf-llm-cost-latency-dashboards" element={<CFLlmCostLatencyDashboardsPage />} />
          <Route path="/cf-prompt-regression-detector" element={<CFPromptRegressionDetectorPage />} />
          <Route path="/cf-trace-replay" element={<CFTraceReplayPage />} />
          <Route path="/cf-eval-harness-integration" element={<CFEvalHarnessIntegrationPage />} />
          <Route path="/cf-opentelemetry-compatibility" element={<CFOpentelemetryCompatibilityPage />} />
          <Route path="/gap-no-explicit-anomaly" element={<GapNoExplicitAnomalyPage />} />
          <Route path="/gap-no-cost" element={<GapNoCostPage />} />
          <Route path="/gap-no-drift" element={<GapNoDriftPage />} />
          <Route path="/gap-no-root" element={<GapNoRootPage />} />
          <Route path="/gap-no-authentication-or-rbac-layer-visible" element={<GapNoAuthenticationOrRbacLayerVisiblePage />} />
          <Route path="/gap-no-billing-usage-metering" element={<GapNoBillingUsageMeteringPage />} />
          <Route path="/gap-no-webhooks-for-alert-delivery-slack-pagerduty" element={<GapNoWebhooksForAlertDeliverySlackPagerdutyPage />} />
          <Route path="/gap-no-retention-archival-policies-for-telemetry" element={<GapNoRetentionArchivalPoliciesForTelemetryPage />} />
          <Route path="/gap-limited-integrations-only-own-sdk-no-opentelemetry" element={<GapLimitedIntegrationsOnlyOwnSdkNoOpentelemetryPage />} />
          <Route path="/gap-no-audit-logging" element={<GapNoAuditLoggingPage />} />
        </Routes>
    </AuthGate>
  );
}
