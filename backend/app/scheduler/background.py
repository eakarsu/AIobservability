"""APScheduler-based background scheduler — replaces Celery + Redis."""
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from app.config import settings

logger = logging.getLogger("ai_observability.scheduler")

scheduler = BackgroundScheduler(daemon=True)


def start_scheduler():
    """Start all background jobs."""
    from app.scheduler.tasks import run_drift_detection, run_hallucination_scoring, run_alert_evaluation

    # Drift detection every N minutes
    scheduler.add_job(
        run_drift_detection,
        trigger=IntervalTrigger(minutes=settings.drift_detection_interval_minutes),
        id="drift_detection",
        name="Drift Detection",
        replace_existing=True,
        max_instances=1,
    )

    # Hallucination scoring every 2 minutes
    if settings.hallucination_scoring_enabled:
        scheduler.add_job(
            run_hallucination_scoring,
            trigger=IntervalTrigger(minutes=2),
            id="hallucination_scoring",
            name="Hallucination Scoring",
            replace_existing=True,
            max_instances=1,
        )

    # Alert evaluation every N seconds
    scheduler.add_job(
        run_alert_evaluation,
        trigger=IntervalTrigger(seconds=settings.alert_evaluation_interval_seconds),
        id="alert_evaluation",
        name="Alert Evaluation",
        replace_existing=True,
        max_instances=1,
    )

    scheduler.start()
    logger.info("Background scheduler started with drift detection, hallucination scoring, and alert evaluation.")


def stop_scheduler():
    """Gracefully shut down the scheduler."""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Background scheduler stopped.")
