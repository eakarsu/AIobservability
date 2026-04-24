"""Background tasks that run on a schedule — replaces Celery workers."""
import uuid
import logging
import json
from datetime import datetime, timezone, timedelta
from sqlalchemy import text
from app.core.database import get_sync_db
from app.engines.drift_engine import DriftEngine
from app.engines.hallucination_engine import HallucinationEngine
from app.scheduler.notifiers import send_webhook, send_email_alert

logger = logging.getLogger("ai_observability.scheduler")

_drift_engine = DriftEngine()
_hallucination_engine = HallucinationEngine()


# ---------------------------------------------------------------------------
# Drift Detection (runs every 15 minutes)
# ---------------------------------------------------------------------------
def run_drift_detection():
    """Run drift detection for all active projects and models."""
    logger.info("Starting drift detection...")
    session = get_sync_db()
    try:
        result = session.execute(text("""
            SELECT DISTINCT project_id, model_name
            FROM telemetry_events
            WHERE timestamp > NOW() - INTERVAL '7 days'
        """))
        combinations = result.fetchall()

        for project_id, model_name in combinations:
            try:
                _detect_drift_for_model(session, str(project_id), model_name)
            except Exception as e:
                logger.error(f"Drift detection failed for {project_id}/{model_name}: {e}")

        logger.info(f"Drift detection complete. Checked {len(combinations)} model(s).")
    finally:
        session.close()


def _detect_drift_for_model(session, project_id: str, model_name: str):
    now = datetime.now(timezone.utc)
    ref_start = now - timedelta(hours=48)
    ref_end = now - timedelta(hours=24)
    test_start = now - timedelta(hours=24)
    test_end = now

    ref_result = session.execute(text("""
        SELECT latency_ms, input_tokens, output_tokens
        FROM telemetry_events
        WHERE project_id = :pid AND model_name = :model
        AND timestamp >= :start AND timestamp < :end_t
        AND latency_ms IS NOT NULL
    """), {"pid": project_id, "model": model_name, "start": ref_start, "end_t": ref_end})
    ref_data = ref_result.fetchall()

    test_result = session.execute(text("""
        SELECT latency_ms, input_tokens, output_tokens
        FROM telemetry_events
        WHERE project_id = :pid AND model_name = :model
        AND timestamp >= :start AND timestamp < :end_t
        AND latency_ms IS NOT NULL
    """), {"pid": project_id, "model": model_name, "start": test_start, "end_t": test_end})
    test_data = test_result.fetchall()

    if len(ref_data) < 30 or len(test_data) < 30:
        return

    features = {
        "latency_ms": ([r[0] for r in ref_data], [r[0] for r in test_data]),
        "input_tokens": ([r[1] for r in ref_data if r[1] is not None], [r[1] for r in test_data if r[1] is not None]),
        "output_tokens": ([r[2] for r in ref_data if r[2] is not None], [r[2] for r in test_data if r[2] is not None]),
    }

    for feature_name, (ref_values, test_values) in features.items():
        if len(ref_values) < 10 or len(test_values) < 10:
            continue

        results = _drift_engine.detect_drift(ref_values, test_values)

        for metric_name, score_data in results.items():
            session.execute(text("""
                INSERT INTO drift_scores (id, project_id, timestamp, model_name, metric_name, score, p_value,
                    reference_window_start, reference_window_end, test_window_start, test_window_end, details)
                VALUES (:id, :pid, :ts, :model, :metric, :score, :pval, :ref_start, :ref_end, :test_start, :test_end, :details)
            """), {
                "id": str(uuid.uuid4()),
                "pid": project_id,
                "ts": now,
                "model": model_name,
                "metric": f"{feature_name}_{metric_name}",
                "score": score_data["score"],
                "pval": score_data.get("p_value"),
                "ref_start": ref_start,
                "ref_end": ref_end,
                "test_start": test_start,
                "test_end": test_end,
                "details": "{}",
            })

    session.commit()


# ---------------------------------------------------------------------------
# Hallucination Scoring (runs every 2 minutes — scores unscored events)
# ---------------------------------------------------------------------------
def run_hallucination_scoring():
    """Score unscored telemetry events for hallucination."""
    logger.info("Starting hallucination scoring...")
    session = get_sync_db()
    scored = 0
    try:
        result = session.execute(text("""
            SELECT te.id, te.project_id, te.input_text, te.output_text
            FROM telemetry_events te
            LEFT JOIN hallucination_scores hs ON te.id = hs.event_id
            WHERE te.input_text IS NOT NULL
            AND te.output_text IS NOT NULL
            AND hs.id IS NULL
            ORDER BY te.timestamp DESC
            LIMIT 50
        """))
        events = result.fetchall()

        for event_id, project_id, input_text, output_text in events:
            try:
                scores = _hallucination_engine.detect_hallucination(input_text, output_text)
                for method, score_data in scores.items():
                    session.execute(text("""
                        INSERT INTO hallucination_scores (id, event_id, project_id, timestamp, score, method, details)
                        VALUES (:id, :event_id, :pid, :ts, :score, :method, :details)
                    """), {
                        "id": str(uuid.uuid4()),
                        "event_id": str(event_id),
                        "pid": str(project_id),
                        "ts": datetime.now(timezone.utc),
                        "score": score_data["score"],
                        "method": method,
                        "details": "{}",
                    })
                scored += 1
            except Exception as e:
                logger.error(f"Hallucination scoring failed for event {event_id}: {e}")

        session.commit()
        logger.info(f"Hallucination scoring complete. Scored {scored} event(s).")
    finally:
        session.close()


# ---------------------------------------------------------------------------
# Alert Evaluation (runs every 60 seconds)
# ---------------------------------------------------------------------------
METRIC_QUERIES = {
    "latency": """
        SELECT AVG(latency_ms) FROM telemetry_events
        WHERE project_id = :pid AND timestamp >= :since AND latency_ms IS NOT NULL
    """,
    "error_rate": """
        SELECT COUNT(*) FILTER (WHERE status = 'error') * 100.0 / NULLIF(COUNT(*), 0)
        FROM telemetry_events
        WHERE project_id = :pid AND timestamp >= :since
    """,
    "drift_score": """
        SELECT AVG(score) FROM drift_scores
        WHERE project_id = :pid AND timestamp >= :since
    """,
    "hallucination_score": """
        SELECT AVG(score) FROM hallucination_scores
        WHERE project_id = :pid AND timestamp >= :since
    """,
    "token_usage": """
        SELECT AVG(input_tokens + output_tokens) FROM telemetry_events
        WHERE project_id = :pid AND timestamp >= :since AND input_tokens IS NOT NULL
    """,
}

CONDITION_OPS = {
    "gt": lambda v, t: v > t,
    "lt": lambda v, t: v < t,
    "gte": lambda v, t: v >= t,
    "lte": lambda v, t: v <= t,
}


def run_alert_evaluation():
    """Evaluate all active alert rules."""
    session = get_sync_db()
    alerts_triggered = 0
    try:
        rules = session.execute(text("""
            SELECT id, project_id, name, metric_type, condition, threshold,
                   window_minutes, notification_channel, cooldown_minutes
            FROM alert_rules WHERE is_active = true
        """)).fetchall()

        for rule in rules:
            try:
                rule_id, project_id, name, metric_type, condition, threshold, \
                    window_minutes, notification_channel, cooldown_minutes = rule

                since = datetime.now(timezone.utc) - timedelta(minutes=window_minutes)

                query = METRIC_QUERIES.get(metric_type)
                if not query:
                    continue

                result = session.execute(text(query), {"pid": str(project_id), "since": since})
                metric_value = result.scalar()

                if metric_value is None:
                    continue

                condition_fn = CONDITION_OPS.get(condition)
                if not condition_fn:
                    continue

                if condition_fn(float(metric_value), float(threshold)):
                    recent = session.execute(text("""
                        SELECT id FROM alerts_fired
                        WHERE rule_id = :rid AND triggered_at > :cooldown_since
                        AND status = 'firing'
                    """), {
                        "rid": str(rule_id),
                        "cooldown_since": datetime.now(timezone.utc) - timedelta(minutes=cooldown_minutes),
                    }).fetchone()

                    if recent:
                        continue

                    alert_id = str(uuid.uuid4())
                    session.execute(text("""
                        INSERT INTO alerts_fired (id, rule_id, project_id, triggered_at, metric_value, status, details)
                        VALUES (:id, :rid, :pid, :ts, :val, 'firing', :details)
                    """), {
                        "id": alert_id,
                        "rid": str(rule_id),
                        "pid": str(project_id),
                        "ts": datetime.now(timezone.utc),
                        "val": float(metric_value),
                        "details": "{}",
                    })
                    alerts_triggered += 1

                    # Send notifications
                    if isinstance(notification_channel, str):
                        try:
                            notification_channel = json.loads(notification_channel)
                        except Exception:
                            notification_channel = {}
                    if isinstance(notification_channel, dict):
                        alert_info = {
                            "alert_id": alert_id,
                            "rule_name": name,
                            "metric_type": metric_type,
                            "metric_value": float(metric_value),
                            "threshold": float(threshold),
                            "condition": condition,
                            "triggered_at": datetime.now(timezone.utc).isoformat(),
                        }
                        if "webhook_url" in notification_channel:
                            send_webhook(notification_channel["webhook_url"], alert_info)
                        if "email" in notification_channel:
                            send_email_alert(notification_channel["email"], alert_info)
                else:
                    session.execute(text("""
                        UPDATE alerts_fired SET status = 'resolved', resolved_at = :now
                        WHERE rule_id = :rid AND status = 'firing'
                    """), {"rid": str(rule_id), "now": datetime.now(timezone.utc)})

            except Exception as e:
                logger.error(f"Alert evaluation failed for rule {rule_id}: {e}")

        session.commit()

        if alerts_triggered:
            logger.info(f"Alert evaluation: {alerts_triggered} alert(s) triggered.")
    finally:
        session.close()
