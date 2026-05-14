"""
AI assistance endpoints for the AI Observability Platform.

These endpoints use OpenRouter (Claude Haiku 4.5 by default) to interpret
the platform's own telemetry, drift scores, hallucination scores, and alerts
into actionable, human-readable insights for SREs and ML engineers.
"""
import os
from datetime import datetime, timezone, timedelta
from typing import Optional, List
from uuid import UUID

import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc

from app.core.database import get_db
from app.core.security import get_project_id
from app.models.telemetry import TelemetryEvent
from app.models.metrics import DriftScore, HallucinationScore
from app.models.alerts import AlertRule, AlertFired

router = APIRouter()

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


def _model() -> str:
    return os.getenv("OPENROUTER_MODEL", "anthropic/claude-haiku-4.5")


async def _call_openrouter(system_prompt: str, user_prompt: str, max_tokens: int = 2000) -> dict:
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise HTTPException(status_code=503, detail="OPENROUTER_API_KEY not configured")

    payload = {
        "model": _model(),
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "max_tokens": max_tokens,
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:3000",
        "X-Title": "AI Observability Platform",
    }
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(OPENROUTER_URL, json=payload, headers=headers)
        data = resp.json()
        if "error" in data:
            raise HTTPException(status_code=502, detail=f"OpenRouter error: {data['error']}")
        try:
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError):
            raise HTTPException(status_code=502, detail="Malformed OpenRouter response")
        return {
            "content": content,
            "model": _model(),
            "tokens_used": data.get("usage", {}).get("total_tokens"),
        }


# ---------------------------------------------------------------------------
# Request / response schemas
# ---------------------------------------------------------------------------
class AIInsightResponse(BaseModel):
    insight: str
    model: str
    tokens_used: Optional[int] = None
    context: Optional[dict] = None


class AnalyzeEventRequest(BaseModel):
    event_id: str
    expected_behavior: Optional[str] = Field(None, description="What the user expected the model to do")


class AnalyzeIncidentRequest(BaseModel):
    alert_id: Optional[str] = None
    window_minutes: int = 30
    include_sample_events: int = 10


class DriftNarrativeRequest(BaseModel):
    model_name: Optional[str] = None
    lookback_hours: int = 24


class CompareModelsRequest(BaseModel):
    model_a: str
    model_b: str
    lookback_hours: int = 24


class CostOptimizeRequest(BaseModel):
    lookback_hours: int = 168  # 7 days


class TraceAnalyzeRequest(BaseModel):
    trace_id: str


class PromptRegressionRequest(BaseModel):
    model_name: str
    baseline_hours: int = 168
    recent_hours: int = 24


class HallucinationClusterRequest(BaseModel):
    lookback_hours: int = 168
    min_score: float = 0.5
    sample_size: int = 30


class AlertRuleSuggestRequest(BaseModel):
    metric_focus: Optional[str] = Field(
        None,
        description="One of: latency, error_rate, drift, hallucination, tokens. Empty = all.",
    )


class ExplainQueryRequest(BaseModel):
    question: str = Field(..., description="Natural-language question about this project's telemetry")


# ---------------------------------------------------------------------------
# 1. POST /ai/analyze-event — explain a single suspicious event
# ---------------------------------------------------------------------------
@router.post("/ai/analyze-event", response_model=AIInsightResponse)
async def analyze_event(
    body: AnalyzeEventRequest,
    project_id: str = Depends(get_project_id),
    db: AsyncSession = Depends(get_db),
):
    pid = UUID(project_id)
    result = await db.execute(
        select(TelemetryEvent).where(
            and_(TelemetryEvent.id == UUID(body.event_id), TelemetryEvent.project_id == pid)
        )
    )
    event = result.scalar_one_or_none()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    hall_result = await db.execute(
        select(func.avg(HallucinationScore.score)).where(HallucinationScore.event_id == event.id)
    )
    hall_score = hall_result.scalar()

    user_prompt = f"""
Analyze this single LLM telemetry event and explain what likely happened.

EVENT:
- id: {event.id}
- timestamp: {event.timestamp}
- model: {event.model_name} ({event.model_provider or 'unknown provider'})
- latency_ms: {event.latency_ms}
- input_tokens: {event.input_tokens}, output_tokens: {event.output_tokens}
- status: {event.status}
- error: {event.error_message or 'none'}
- hallucination_score (avg): {hall_score if hall_score is not None else 'not scored'}
- tags: {event.tags}
- metadata: {event.extra_metadata}

INPUT (truncated to 2000 chars):
{(event.input_text or '')[:2000]}

OUTPUT (truncated to 2000 chars):
{(event.output_text or '')[:2000]}

EXPECTED BEHAVIOR (per requester): {body.expected_behavior or 'Not specified'}

Provide:
1. A 2-sentence summary of what the model did.
2. Likely root cause if this is a failure / hallucination / latency outlier.
3. Specific signals from the input/output that support your assessment (quote them).
4. Concrete next-step debugging actions (3-5 bullets).
5. A single confidence rating (low/medium/high) for your diagnosis.
"""
    system_prompt = (
        "You are an SRE analyst specialized in LLM telemetry. "
        "Be precise. Quote specific tokens or phrases from input/output when claiming a cause. "
        "Distinguish between model errors, prompt issues, infra issues, and data drift."
    )
    out = await _call_openrouter(system_prompt, user_prompt)
    return AIInsightResponse(insight=out["content"], model=out["model"], tokens_used=out["tokens_used"])


# ---------------------------------------------------------------------------
# 2. POST /ai/analyze-incident — narrate a multi-event incident around an alert
# ---------------------------------------------------------------------------
@router.post("/ai/analyze-incident", response_model=AIInsightResponse)
async def analyze_incident(
    body: AnalyzeIncidentRequest,
    project_id: str = Depends(get_project_id),
    db: AsyncSession = Depends(get_db),
):
    pid = UUID(project_id)
    anchor = datetime.now(timezone.utc)
    alert_obj = None
    if body.alert_id:
        ar = await db.execute(
            select(AlertFired).where(
                and_(AlertFired.id == UUID(body.alert_id), AlertFired.project_id == pid)
            )
        )
        alert_obj = ar.scalar_one_or_none()
        if not alert_obj:
            raise HTTPException(status_code=404, detail="Alert not found")
        anchor = alert_obj.triggered_at if hasattr(alert_obj, "triggered_at") else anchor

    window_start = anchor - timedelta(minutes=body.window_minutes)

    agg = await db.execute(
        select(
            func.count(TelemetryEvent.id).label("total"),
            func.coalesce(func.avg(TelemetryEvent.latency_ms), 0).label("avg_latency"),
            func.coalesce(
                func.percentile_cont(0.95).within_group(TelemetryEvent.latency_ms), 0
            ).label("p95"),
        ).where(
            and_(
                TelemetryEvent.project_id == pid,
                TelemetryEvent.timestamp >= window_start,
                TelemetryEvent.timestamp <= anchor,
            )
        )
    )
    row = agg.one()

    err_q = await db.execute(
        select(func.count(TelemetryEvent.id)).where(
            and_(
                TelemetryEvent.project_id == pid,
                TelemetryEvent.timestamp >= window_start,
                TelemetryEvent.timestamp <= anchor,
                TelemetryEvent.status == "error",
            )
        )
    )
    err_count = err_q.scalar() or 0

    sample_q = await db.execute(
        select(TelemetryEvent)
        .where(
            and_(
                TelemetryEvent.project_id == pid,
                TelemetryEvent.timestamp >= window_start,
                TelemetryEvent.timestamp <= anchor,
            )
        )
        .order_by(desc(TelemetryEvent.timestamp))
        .limit(body.include_sample_events)
    )
    samples = sample_q.scalars().all()

    samples_text = "\n".join(
        f"- {e.timestamp} | {e.model_name} | latency={e.latency_ms}ms | status={e.status} "
        f"| err={e.error_message or 'none'}"
        for e in samples
    ) or "No events in window."

    alert_block = ""
    if alert_obj:
        alert_block = (
            f"ALERT CONTEXT: id={alert_obj.id}, triggered_at={getattr(alert_obj,'triggered_at',None)}, "
            f"status={getattr(alert_obj,'status',None)}, payload={getattr(alert_obj,'payload',{})}"
        )

    user_prompt = f"""
Diagnose what is happening in this observability window.

WINDOW: {window_start.isoformat()} -> {anchor.isoformat()} ({body.window_minutes} min)
{alert_block}

AGGREGATE METRICS:
- total events: {row.total}
- avg latency (ms): {round(float(row.avg_latency), 2)}
- p95 latency (ms): {round(float(row.p95), 2)}
- error count: {err_count}
- error rate: {round((err_count / row.total * 100) if row.total else 0, 2)}%

RECENT EVENTS (most recent first):
{samples_text}

Produce an incident narrative:
1. One-paragraph TL;DR for an on-call engineer.
2. Most likely root cause with reasoning.
3. Blast radius (which models/users/clients are likely affected, based on patterns).
4. Three immediate mitigations (rollback, traffic shift, prompt fix, etc.).
5. Three follow-up investigations (queries to run, logs to grep, dashboards to inspect).
6. A draft 4-line status-page update suitable for stakeholders.
"""
    system_prompt = (
        "You are an LLM-application incident commander. "
        "Be specific and concise. Distinguish between provider-side failures, "
        "infrastructure/network issues, prompt regressions, and data drift. "
        "Always flag if the data is too sparse to draw a confident conclusion."
    )
    out = await _call_openrouter(system_prompt, user_prompt, max_tokens=2500)
    return AIInsightResponse(
        insight=out["content"],
        model=out["model"],
        tokens_used=out["tokens_used"],
        context={
            "window_start": window_start.isoformat(),
            "anchor": anchor.isoformat(),
            "total": row.total,
            "errors": err_count,
        },
    )


# ---------------------------------------------------------------------------
# 3. POST /ai/drift-narrative — explain drift in plain language
# ---------------------------------------------------------------------------
@router.post("/ai/drift-narrative", response_model=AIInsightResponse)
async def drift_narrative(
    body: DriftNarrativeRequest,
    project_id: str = Depends(get_project_id),
    db: AsyncSession = Depends(get_db),
):
    pid = UUID(project_id)
    since = datetime.now(timezone.utc) - timedelta(hours=body.lookback_hours)

    q = select(DriftScore).where(
        and_(DriftScore.project_id == pid, DriftScore.timestamp >= since)
    )
    if body.model_name:
        q = q.where(DriftScore.model_name == body.model_name)
    q = q.order_by(desc(DriftScore.timestamp)).limit(200)
    res = await db.execute(q)
    rows = res.scalars().all()

    if not rows:
        raise HTTPException(status_code=404, detail="No drift scores in window")

    drift_text = "\n".join(
        f"- {r.timestamp} | model={r.model_name} | metric={r.metric_name} | score={r.score:.4f} "
        f"| p={r.p_value if r.p_value is not None else 'n/a'} | details={r.details}"
        for r in rows[:60]
    )

    user_prompt = f"""
Translate raw drift scores into a plain-language story for a product manager.

SCOPE: model={body.model_name or 'all models'} | lookback={body.lookback_hours}h
ROW COUNT: {len(rows)}

DRIFT SCORES (most recent first, up to 60):
{drift_text}

Produce:
1. A 4-6 sentence story explaining what changed and when.
2. Whether this looks like input-distribution drift, output drift, or both.
3. Risk assessment (low/medium/high) and the user-facing impact.
4. Recommended actions: re-train? add eval set? roll back prompt? roll back model? throttle?
5. One sentence on whether the drift is actionable now or needs more evidence.
"""
    system_prompt = (
        "You are a model-quality analyst. Treat drift scores as signals, not facts. "
        "Distinguish covariate (input) drift from concept/label drift. Be calibrated about confidence."
    )
    out = await _call_openrouter(system_prompt, user_prompt, max_tokens=1800)
    return AIInsightResponse(insight=out["content"], model=out["model"], tokens_used=out["tokens_used"])


# ---------------------------------------------------------------------------
# 4. POST /ai/compare-models — A/B narrative summary for two models
# ---------------------------------------------------------------------------
@router.post("/ai/compare-models", response_model=AIInsightResponse)
async def compare_models(
    body: CompareModelsRequest,
    project_id: str = Depends(get_project_id),
    db: AsyncSession = Depends(get_db),
):
    pid = UUID(project_id)
    since = datetime.now(timezone.utc) - timedelta(hours=body.lookback_hours)

    async def _stats(model_name: str) -> dict:
        q = await db.execute(
            select(
                func.count(TelemetryEvent.id).label("n"),
                func.coalesce(func.avg(TelemetryEvent.latency_ms), 0).label("avg_lat"),
                func.coalesce(
                    func.percentile_cont(0.95).within_group(TelemetryEvent.latency_ms), 0
                ).label("p95"),
                func.coalesce(func.avg(TelemetryEvent.input_tokens), 0).label("avg_in"),
                func.coalesce(func.avg(TelemetryEvent.output_tokens), 0).label("avg_out"),
            ).where(
                and_(
                    TelemetryEvent.project_id == pid,
                    TelemetryEvent.model_name == model_name,
                    TelemetryEvent.timestamp >= since,
                )
            )
        )
        r = q.one()
        e = await db.execute(
            select(func.count(TelemetryEvent.id)).where(
                and_(
                    TelemetryEvent.project_id == pid,
                    TelemetryEvent.model_name == model_name,
                    TelemetryEvent.status == "error",
                    TelemetryEvent.timestamp >= since,
                )
            )
        )
        err = e.scalar() or 0
        h = await db.execute(
            select(func.avg(HallucinationScore.score)).where(
                and_(
                    HallucinationScore.project_id == pid,
                    HallucinationScore.timestamp >= since,
                )
            )
        )
        hall = h.scalar()
        return {
            "n": r.n,
            "avg_latency_ms": round(float(r.avg_lat), 2),
            "p95_latency_ms": round(float(r.p95), 2),
            "avg_input_tokens": round(float(r.avg_in), 1),
            "avg_output_tokens": round(float(r.avg_out), 1),
            "error_rate_pct": round((err / r.n * 100) if r.n else 0, 2),
            "avg_hallucination": round(float(hall), 4) if hall is not None else None,
        }

    a = await _stats(body.model_a)
    b = await _stats(body.model_b)

    user_prompt = f"""
Compare two models head-to-head over the last {body.lookback_hours}h.

MODEL A: {body.model_a}
{a}

MODEL B: {body.model_b}
{b}

Produce:
1. One-line winner per dimension (latency, cost-proxy via output tokens, error rate, hallucination, sample size).
2. Statistical-significance caution if either sample size is small (<200).
3. A practical recommendation: which model should serve which traffic, and why.
4. Risks of switching: loss aversion / capability gaps that the metrics don't capture.
5. The next 3 measurements you'd want to collect to make this decision more confidently.
"""
    system_prompt = (
        "You are an ML-ops analyst running a model bake-off. "
        "Always note when the data is too thin to make a confident call. Avoid recommending changes on weak evidence."
    )
    out = await _call_openrouter(system_prompt, user_prompt, max_tokens=1500)
    return AIInsightResponse(
        insight=out["content"],
        model=out["model"],
        tokens_used=out["tokens_used"],
        context={"a": a, "b": b},
    )


# ---------------------------------------------------------------------------
# 5. POST /ai/cost-optimize — token-spend optimization recommendations
# ---------------------------------------------------------------------------
@router.post("/ai/cost-optimize", response_model=AIInsightResponse)
async def cost_optimize(
    body: CostOptimizeRequest,
    project_id: str = Depends(get_project_id),
    db: AsyncSession = Depends(get_db),
):
    pid = UUID(project_id)
    since = datetime.now(timezone.utc) - timedelta(hours=body.lookback_hours)

    by_model = await db.execute(
        select(
            TelemetryEvent.model_name,
            func.count(TelemetryEvent.id).label("n"),
            func.coalesce(func.sum(TelemetryEvent.input_tokens), 0).label("in_tokens"),
            func.coalesce(func.sum(TelemetryEvent.output_tokens), 0).label("out_tokens"),
            func.coalesce(func.avg(TelemetryEvent.input_tokens), 0).label("avg_in"),
            func.coalesce(func.avg(TelemetryEvent.output_tokens), 0).label("avg_out"),
        )
        .where(and_(TelemetryEvent.project_id == pid, TelemetryEvent.timestamp >= since))
        .group_by(TelemetryEvent.model_name)
        .order_by(desc("out_tokens"))
        .limit(20)
    )
    rows = by_model.all()

    rows_text = "\n".join(
        f"- {r.model_name} | calls={r.n} | total_in={r.in_tokens} | total_out={r.out_tokens} "
        f"| avg_in={round(float(r.avg_in),1)} | avg_out={round(float(r.avg_out),1)}"
        for r in rows
    ) or "No usage in window."

    user_prompt = f"""
Recommend cost-optimizations for an LLM-powered application.

LOOKBACK: {body.lookback_hours}h
USAGE BY MODEL:
{rows_text}

Produce:
1. The single biggest cost driver (model + reason).
2. Three concrete cost-reduction moves ranked by expected savings (e.g., swap to a smaller model for a route, cache responses, trim system prompts, switch to streaming with early termination, batch). Be specific to the data above.
3. For each move: a rough percent-savings estimate and the risk to quality.
4. Two quick wins that are zero-risk (e.g., remove obviously stale system-prompt boilerplate, deduplicate identical prompts).
5. A measurement plan: what metrics to track post-change to verify no regression.
"""
    system_prompt = (
        "You are a cost-optimization analyst for LLM workloads. "
        "Quantify with explicit assumptions. Never recommend a change that would degrade quality without flagging it."
    )
    out = await _call_openrouter(system_prompt, user_prompt, max_tokens=1800)
    return AIInsightResponse(
        insight=out["content"],
        model=out["model"],
        tokens_used=out["tokens_used"],
        context={"rows": [dict(r._mapping) for r in rows]} if rows else None,
    )


# ---------------------------------------------------------------------------
# 6. POST /ai/trace-analyze — pull a trace's spans and analyze the pipeline
# ---------------------------------------------------------------------------
@router.post("/ai/trace-analyze", response_model=AIInsightResponse)
async def trace_analyze(
    body: TraceAnalyzeRequest,
    project_id: str = Depends(get_project_id),
    db: AsyncSession = Depends(get_db),
):
    pid = UUID(project_id)
    res = await db.execute(
        select(TelemetryEvent)
        .where(and_(TelemetryEvent.project_id == pid, TelemetryEvent.trace_id == body.trace_id))
        .order_by(TelemetryEvent.timestamp)
    )
    spans = res.scalars().all()
    if not spans:
        raise HTTPException(status_code=404, detail="No spans for trace")

    spans_text = "\n".join(
        f"- {e.timestamp} | span={e.span_id} parent={e.parent_span_id} | "
        f"model={e.model_name} | latency={e.latency_ms}ms | status={e.status} | "
        f"in_tok={e.input_tokens} out_tok={e.output_tokens} | err={e.error_message or 'none'}"
        for e in spans
    )

    total_lat = sum((s.latency_ms or 0) for s in spans)
    total_in = sum((s.input_tokens or 0) for s in spans)
    total_out = sum((s.output_tokens or 0) for s in spans)

    user_prompt = f"""
Analyze a multi-step LLM pipeline trace.

TRACE: {body.trace_id}
SPANS: {len(spans)}
TOTAL LATENCY: {total_lat:.0f}ms
TOTAL INPUT TOKENS: {total_in}
TOTAL OUTPUT TOKENS: {total_out}

SPAN TIMELINE:
{spans_text}

Provide:
1. A pipeline reconstruction (which span called which) based on parent_span_id.
2. The critical-path latency contributors (top 3 spans by latency).
3. Any redundant or wasteful calls (duplicate prompts, retries with no backoff, etc.).
4. Whether this trace exhibits any obvious anti-patterns (over-eager retrieval, runaway agent loop, mis-wired tool call).
5. Three optimizations specific to this trace.
"""
    system_prompt = (
        "You are an LLM-pipeline performance analyst. Build a mental model of the call graph from parent_span_id. "
        "Be precise about which span is the bottleneck."
    )
    out = await _call_openrouter(system_prompt, user_prompt, max_tokens=1800)
    return AIInsightResponse(
        insight=out["content"],
        model=out["model"],
        tokens_used=out["tokens_used"],
        context={"span_count": len(spans), "total_latency_ms": total_lat},
    )


# ---------------------------------------------------------------------------
# 7. POST /ai/prompt-regression — compare baseline vs recent quality signals
# ---------------------------------------------------------------------------
@router.post("/ai/prompt-regression", response_model=AIInsightResponse)
async def prompt_regression(
    body: PromptRegressionRequest,
    project_id: str = Depends(get_project_id),
    db: AsyncSession = Depends(get_db),
):
    pid = UUID(project_id)
    now = datetime.now(timezone.utc)
    baseline_start = now - timedelta(hours=body.baseline_hours + body.recent_hours)
    baseline_end = now - timedelta(hours=body.recent_hours)
    recent_start = baseline_end

    async def _bucket_stats(start, end):
        q = await db.execute(
            select(
                func.count(TelemetryEvent.id).label("n"),
                func.coalesce(func.avg(TelemetryEvent.latency_ms), 0).label("avg_lat"),
                func.coalesce(func.avg(TelemetryEvent.output_tokens), 0).label("avg_out"),
            ).where(
                and_(
                    TelemetryEvent.project_id == pid,
                    TelemetryEvent.model_name == body.model_name,
                    TelemetryEvent.timestamp >= start,
                    TelemetryEvent.timestamp < end,
                )
            )
        )
        r = q.one()
        e = await db.execute(
            select(func.count(TelemetryEvent.id)).where(
                and_(
                    TelemetryEvent.project_id == pid,
                    TelemetryEvent.model_name == body.model_name,
                    TelemetryEvent.status == "error",
                    TelemetryEvent.timestamp >= start,
                    TelemetryEvent.timestamp < end,
                )
            )
        )
        err = e.scalar() or 0
        return {
            "n": r.n,
            "avg_latency_ms": round(float(r.avg_lat), 2),
            "avg_output_tokens": round(float(r.avg_out), 1),
            "error_count": err,
            "error_rate_pct": round((err / r.n * 100) if r.n else 0, 2),
        }

    base = await _bucket_stats(baseline_start, baseline_end)
    recent = await _bucket_stats(recent_start, now)

    user_prompt = f"""
Detect possible prompt or model regression.

MODEL: {body.model_name}
BASELINE WINDOW: last {body.baseline_hours}h before recent ({base})
RECENT WINDOW: last {body.recent_hours}h ({recent})

Provide:
1. A clear yes/no verdict on whether a regression is plausible, with one sentence of justification.
2. Which dimensions changed materially (latency, error rate, output verbosity).
3. Possible causes ranked by likelihood (prompt edit, model version flip on provider side, infra latency, traffic-mix shift).
4. Three diagnostic next steps (eval-set rerun, A/B split, prompt diff against repo).
5. Statistical caveats given the sample sizes.
"""
    system_prompt = (
        "You are an ML-ops detective. Be calibrated. A change in average is not a regression unless it's outside expected noise. "
        "Always cite when sample size is too small."
    )
    out = await _call_openrouter(system_prompt, user_prompt, max_tokens=1500)
    return AIInsightResponse(
        insight=out["content"],
        model=out["model"],
        tokens_used=out["tokens_used"],
        context={"baseline": base, "recent": recent},
    )


# ---------------------------------------------------------------------------
# 8. POST /ai/hallucination-cluster — surface common hallucination themes
# ---------------------------------------------------------------------------
@router.post("/ai/hallucination-cluster", response_model=AIInsightResponse)
async def hallucination_cluster(
    body: HallucinationClusterRequest,
    project_id: str = Depends(get_project_id),
    db: AsyncSession = Depends(get_db),
):
    pid = UUID(project_id)
    since = datetime.now(timezone.utc) - timedelta(hours=body.lookback_hours)

    q = await db.execute(
        select(
            HallucinationScore.id,
            HallucinationScore.score,
            HallucinationScore.method,
            HallucinationScore.timestamp,
            HallucinationScore.event_id,
            TelemetryEvent.input_text,
            TelemetryEvent.output_text,
            TelemetryEvent.model_name,
        )
        .join(TelemetryEvent, TelemetryEvent.id == HallucinationScore.event_id)
        .where(
            and_(
                HallucinationScore.project_id == pid,
                HallucinationScore.timestamp >= since,
                HallucinationScore.score >= body.min_score,
            )
        )
        .order_by(desc(HallucinationScore.score))
        .limit(body.sample_size)
    )
    rows = q.all()
    if not rows:
        raise HTTPException(status_code=404, detail="No hallucination samples meet threshold")

    samples = "\n\n".join(
        f"--- sample {i+1} (model={r.model_name}, method={r.method}, score={r.score:.3f}) ---\n"
        f"INPUT: {((r.input_text or '')[:500])}\n"
        f"OUTPUT: {((r.output_text or '')[:500])}"
        for i, r in enumerate(rows)
    )

    user_prompt = f"""
Cluster these high-hallucination samples into themes.

LOOKBACK: {body.lookback_hours}h | min_score: {body.min_score} | sample size: {len(rows)}

SAMPLES:
{samples}

Produce:
1. 3-6 themes describing common hallucination patterns (e.g., "fabricates citations", "confuses similar entities", "out-of-date facts", "instruction ignoring").
2. For each theme: 1-2 representative sample numbers, frequency estimate, and the likely root cause (training data, prompt design, retrieval miss, etc.).
3. Recommended mitigations per theme (prompt addendum, retrieval add, refusal trigger, eval addition).
4. The single highest-priority theme to fix first, with reasoning.
"""
    system_prompt = (
        "You are an evaluation analyst studying LLM hallucinations. "
        "Be precise about which root cause aligns with each theme. "
        "Never claim more than the data supports — say 'unclear from sample' when warranted."
    )
    out = await _call_openrouter(system_prompt, user_prompt, max_tokens=2200)
    return AIInsightResponse(insight=out["content"], model=out["model"], tokens_used=out["tokens_used"])


# ---------------------------------------------------------------------------
# 9. POST /ai/alert-rule-suggest — propose alert rules from observed data
# ---------------------------------------------------------------------------
@router.post("/ai/alert-rule-suggest", response_model=AIInsightResponse)
async def alert_rule_suggest(
    body: AlertRuleSuggestRequest,
    project_id: str = Depends(get_project_id),
    db: AsyncSession = Depends(get_db),
):
    pid = UUID(project_id)
    since = datetime.now(timezone.utc) - timedelta(hours=24 * 7)

    base_q = await db.execute(
        select(
            func.count(TelemetryEvent.id).label("n"),
            func.coalesce(func.avg(TelemetryEvent.latency_ms), 0).label("avg_lat"),
            func.coalesce(
                func.percentile_cont(0.95).within_group(TelemetryEvent.latency_ms), 0
            ).label("p95"),
            func.coalesce(
                func.percentile_cont(0.99).within_group(TelemetryEvent.latency_ms), 0
            ).label("p99"),
        ).where(and_(TelemetryEvent.project_id == pid, TelemetryEvent.timestamp >= since))
    )
    base = base_q.one()

    err_q = await db.execute(
        select(func.count(TelemetryEvent.id)).where(
            and_(
                TelemetryEvent.project_id == pid,
                TelemetryEvent.timestamp >= since,
                TelemetryEvent.status == "error",
            )
        )
    )
    err_count = err_q.scalar() or 0

    existing_q = await db.execute(
        select(AlertRule).where(AlertRule.project_id == pid).limit(50)
    )
    existing = existing_q.scalars().all()
    existing_text = "\n".join(
        f"- {r.name}: {r.metric_type} {r.condition} {r.threshold} (window {r.window_minutes}m)"
        for r in existing
    ) or "No existing alert rules."

    user_prompt = f"""
Recommend alert rules for this project's actual traffic profile.

7-DAY BASELINE:
- events: {base.n}
- avg latency: {round(float(base.avg_lat), 2)}ms
- p95 latency: {round(float(base.p95), 2)}ms
- p99 latency: {round(float(base.p99), 2)}ms
- errors (7d): {err_count}
- error rate (7d): {round((err_count / base.n * 100) if base.n else 0, 2)}%

EXISTING ALERT RULES:
{existing_text}

FOCUS: {body.metric_focus or 'all'}

Recommend 3-6 specific alert rules in this exact format per rule:
- name: short title
- metric: latency_p95 | latency_p99 | error_rate_pct | drift_score | hallucination_avg | output_token_avg
- condition: > | >= | <
- threshold: numeric value (justify with the baseline above)
- window_minutes: 5/15/30/60
- cooldown_minutes
- channel: email | slack | pagerduty
- rationale (1 sentence)

Avoid alerts that would have fired during the baseline window unless the baseline itself looks pathological — say so explicitly when proposing tightening.
"""
    system_prompt = (
        "You are an alerting designer for LLM workloads. "
        "Propose thresholds anchored in observed percentiles, not made-up numbers. "
        "Avoid alert fatigue — never recommend more than 6 alerts in one batch."
    )
    out = await _call_openrouter(system_prompt, user_prompt, max_tokens=1500)
    return AIInsightResponse(insight=out["content"], model=out["model"], tokens_used=out["tokens_used"])


# ---------------------------------------------------------------------------
# 10. POST /ai/explain-query — natural-language Q&A grounded in this project
# ---------------------------------------------------------------------------
@router.post("/ai/explain-query", response_model=AIInsightResponse)
async def explain_query(
    body: ExplainQueryRequest,
    project_id: str = Depends(get_project_id),
    db: AsyncSession = Depends(get_db),
):
    pid = UUID(project_id)
    since = datetime.now(timezone.utc) - timedelta(hours=24)

    overview_q = await db.execute(
        select(
            func.count(TelemetryEvent.id).label("n"),
            func.coalesce(func.avg(TelemetryEvent.latency_ms), 0).label("avg_lat"),
        ).where(and_(TelemetryEvent.project_id == pid, TelemetryEvent.timestamp >= since))
    )
    o = overview_q.one()

    by_model_q = await db.execute(
        select(
            TelemetryEvent.model_name,
            func.count(TelemetryEvent.id).label("n"),
        )
        .where(and_(TelemetryEvent.project_id == pid, TelemetryEvent.timestamp >= since))
        .group_by(TelemetryEvent.model_name)
        .order_by(desc("n"))
        .limit(8)
    )
    by_model = by_model_q.all()
    by_model_text = "\n".join(f"- {r.model_name}: {r.n} calls" for r in by_model) or "(no recent traffic)"

    user_prompt = f"""
Answer the user's question using ONLY the project context provided. Do not invent metrics.

USER QUESTION:
{body.question}

PROJECT CONTEXT (last 24h):
- total events: {o.n}
- avg latency: {round(float(o.avg_lat), 2)}ms
- top models by call count:
{by_model_text}

Schema available to query if more is needed:
- telemetry_events(project_id, timestamp, model_name, latency_ms, input_tokens, output_tokens, status, error_message, trace_id, span_id, parent_span_id, tags, metadata)
- drift_scores(project_id, timestamp, model_name, metric_name, score, p_value)
- hallucination_scores(project_id, event_id, timestamp, score, method)
- alert_rules, alerts_fired

If the question can be answered from the context above, do so directly.
Otherwise, write the SQL query (or list of queries) the user should run, and explain what each one would tell them.
End with a single follow-up question that would unblock a more useful answer.
"""
    system_prompt = (
        "You are an observability copilot. Be grounded in the data. "
        "When the data is insufficient, say so and propose the exact query needed. "
        "Never fabricate numbers."
    )
    out = await _call_openrouter(system_prompt, user_prompt, max_tokens=1500)
    return AIInsightResponse(insight=out["content"], model=out["model"], tokens_used=out["tokens_used"])
