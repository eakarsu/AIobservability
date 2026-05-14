import { Routes, Route, Navigate } from 'react-router-dom';
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
        <Route path="ai-insights" element={<AIInsights />} />
        <Route path="settings" element={<Settings />} />
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
  );
}
