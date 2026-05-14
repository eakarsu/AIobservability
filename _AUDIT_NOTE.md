# AIobservability — Audit Note

## Bucket: E — HAS_CODE_NO_AI (LLM router added)

The original audit (batch_06.md, section 4) reported "0 routes, 0 AI endpoints" with verdict `skeleton` and noted the project was "likely a framework or library, not a product." In reality the backend was a Python/FastAPI app with full telemetry, metrics, alerts, and projects routers — but no LLM-driven assist endpoints. The project is the right shape for AI-assisted observability (drift, hallucination, alerts) but had not yet wired in any LLM calls itself.

## Existing Backend (not modified)

Stack: Python 3.12, FastAPI 0.115, SQLAlchemy async, asyncpg/Postgres, APScheduler, scikit-learn/scipy/numpy. Backend at `/Users/erolakarsu/projects/AIobservability/backend/`.

Routers already present at `app/api/v1/`:
- `ingest.py` — telemetry ingestion (single + batch).
- `query.py` — metrics overview, latency/token timeseries, drift scores, hallucination scores, events list/detail.
- `alerts.py` — alert-rule CRUD and history.
- `projects.py` — project + API key management.

Background scheduler (`app/scheduler/`) runs drift detection and hallucination scoring jobs.

## What was added

- **`/Users/erolakarsu/projects/AIobservability/backend/app/api/v1/ai.py`** — new FastAPI router using `httpx` (already in `requirements.txt`) to call OpenRouter (`anthropic/claude-haiku-4.5` default, `process.env.OPENROUTER_MODEL` override). All endpoints reuse the existing `get_db`, `get_project_id` deps and pull from `TelemetryEvent`, `DriftScore`, `HallucinationScore`, `AlertRule`, `AlertFired`. Endpoints (10, all domain-specific to LLM observability):
  1. `POST /api/v1/ai/analyze-event` — root-cause a single suspicious event (latency / hallucination / error) using its input/output text.
  2. `POST /api/v1/ai/analyze-incident` — narrate a multi-event incident around an alert window with TL;DR + status-page draft.
  3. `POST /api/v1/ai/drift-narrative` — translate raw drift scores into plain language and recommended actions.
  4. `POST /api/v1/ai/compare-models` — head-to-head A/B summary across latency, error rate, hallucination, cost-proxy.
  5. `POST /api/v1/ai/cost-optimize` — token-spend optimization recommendations grouped by model.
  6. `POST /api/v1/ai/trace-analyze` — pipeline analysis from `trace_id` spans, including critical-path latency.
  7. `POST /api/v1/ai/prompt-regression` — baseline-vs-recent regression detector with calibrated confidence.
  8. `POST /api/v1/ai/hallucination-cluster` — theme-cluster high-hallucination samples and propose mitigations.
  9. `POST /api/v1/ai/alert-rule-suggest` — propose alert thresholds anchored in observed percentiles.
  10. `POST /api/v1/ai/explain-query` — grounded Q&A over the project's telemetry, with SQL when context is insufficient.
- **`/Users/erolakarsu/projects/AIobservability/backend/app/api/router.py`** — added `from app.api.v1 import ... ai` and `api_router.include_router(ai.router, tags=["AI Insights"])`.

## Validation

- `python3 -m py_compile app/api/v1/ai.py` — passed.
- `python3 -m py_compile app/api/router.py` — passed.
- Style matches existing routers exactly: same `APIRouter` shape, same `Depends(get_db)`, same `Depends(get_project_id)`, same `desc/and_/select` SQLAlchemy patterns.

## Configuration

The router needs `OPENROUTER_API_KEY` in the environment; if missing, endpoints respond `503 OPENROUTER_API_KEY not configured`. Default model `anthropic/claude-haiku-4.5` is overridable via `OPENROUTER_MODEL`. No new dependencies — `httpx` was already in `requirements.txt`.

## Apply pass 3 (frontend)

Pass 2 added 10 AI endpoints (`/api/v1/ai/*`) but no FE wiring. The Vite/React/Tailwind dashboard had Overview / ModelPerformance / DriftAnalysis / HallucinationReport / Alerts / Settings pages but no entry point for the AI insight endpoints.

Added an "AI Insights" page that exposes all 10 endpoints behind a left-rail tool selector with per-tool form schemas (event_id, alert_id, model_a/b, trace_id, free-text question, etc.). Output renders as plain text with optional debug context. 503 errors detected by string match render an "AI not configured" yellow callout.

- File added: `dashboard/src/pages/AIInsights.tsx`
- Files modified: `dashboard/src/App.tsx` (route), `dashboard/src/components/Sidebar.tsx` (nav), `dashboard/src/api/client.ts` (10 typed mutation helpers)
- Existing project uses `axios` + `@tanstack/react-query` — followed the same pattern (no new deps)
- Auth: project uses `X-API-Key` set via Settings page; API client already handles it
- Syntax check: `tsc --noEmit -p .` PASS (no errors)

## Apply pass 4 (mechanical backlog)

LEFT-AS-IS. No mechanical items remain — pass 2 already added 10 LLM-observability endpoints (analyze-event, analyze-incident, drift-narrative, compare-models, cost-optimize, trace-analyze, prompt-regression, hallucination-cluster, alert-rule-suggest, explain-query) which collectively absorb all of the audit's recommended AI / non-AI / custom-feature surface that is implementable without new infrastructure or vendor credentials. Pass 3 wired all 10 in the dashboard's `AIInsights` page. Anything still open (e.g. APM-vendor exporters, OTel collector deployment) is NEEDS-CREDS or NEEDS-PRODUCT-DECISION.

## Apply pass 5 (all backlog)

LEFT-AS-IS. Same reasoning as pass 4 — pass 2 already shipped the full 10-endpoint LLM-observability surface. All remaining audit items are NEEDS-CREDS (APM vendor exporters, OTel collector deployment) or require new infrastructure (e.g. trace ingestion from non-OTel sources). Adding more LLM endpoints would be gold-plating without product signal. No changes in this pass.
