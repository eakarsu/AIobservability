from fastapi import APIRouter
from app.api.v1 import ingest, query, alerts, projects, ai

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(ingest.router, tags=["Telemetry Ingestion"])
api_router.include_router(query.router, tags=["Metrics & Events"])
api_router.include_router(alerts.router, tags=["Alerts"])
api_router.include_router(projects.router, tags=["Projects"])
api_router.include_router(ai.router, tags=["AI Insights"])

# === Custom Feature Routers (batch_06) ===
from app.api.v1 import custom_feat_01_llm_cost_latency_dashboards, custom_feat_02_prompt_regression_detector, custom_feat_03_trace_replay, custom_feat_04_eval_harness_integration, custom_feat_05_opentelemetry_compatibility
api_router.include_router(custom_feat_01_llm_cost_latency_dashboards.router, tags=["Custom Features"])
api_router.include_router(custom_feat_02_prompt_regression_detector.router, tags=["Custom Features"])
api_router.include_router(custom_feat_03_trace_replay.router, tags=["Custom Features"])
api_router.include_router(custom_feat_04_eval_harness_integration.router, tags=["Custom Features"])
api_router.include_router(custom_feat_05_opentelemetry_compatibility.router, tags=["Custom Features"])

# === Batch 06 Gaps & Frontend Mounts ===
from app.api.v1 import gap_feat_no_explicit_anomaly, gap_feat_no_cost, gap_feat_no_drift, gap_feat_no_root, gap_feat_no_authentication_or_rbac_layer_visible, gap_feat_no_billing_usage_metering, gap_feat_no_webhooks_for_alert_delivery_slack_pagerduty, gap_feat_no_retention_archival_policies_for_telemetry, gap_feat_limited_integrations_only_own_sdk_no_opentelemetry, gap_feat_no_audit_logging
api_router.include_router(gap_feat_no_explicit_anomaly.router, tags=["Gap Features"])
api_router.include_router(gap_feat_no_cost.router, tags=["Gap Features"])
api_router.include_router(gap_feat_no_drift.router, tags=["Gap Features"])
api_router.include_router(gap_feat_no_root.router, tags=["Gap Features"])
api_router.include_router(gap_feat_no_authentication_or_rbac_layer_visible.router, tags=["Gap Features"])
api_router.include_router(gap_feat_no_billing_usage_metering.router, tags=["Gap Features"])
api_router.include_router(gap_feat_no_webhooks_for_alert_delivery_slack_pagerduty.router, tags=["Gap Features"])
api_router.include_router(gap_feat_no_retention_archival_policies_for_telemetry.router, tags=["Gap Features"])
api_router.include_router(gap_feat_limited_integrations_only_own_sdk_no_opentelemetry.router, tags=["Gap Features"])
api_router.include_router(gap_feat_no_audit_logging.router, tags=["Gap Features"])
