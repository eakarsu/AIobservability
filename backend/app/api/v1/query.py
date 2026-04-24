from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text, and_, desc
from datetime import datetime, timezone, timedelta
from uuid import UUID
from typing import Optional
from app.core.database import get_db
from app.core.security import get_project_id
from app.models.telemetry import TelemetryEvent
from app.models.metrics import DriftScore, HallucinationScore
from app.schemas.telemetry import TelemetryEventResponse, TelemetryEventDetail
from app.schemas.metrics import OverviewMetrics, TimeSeriesResponse, MetricPoint, DriftScoreResponse, HallucinationScoreResponse

router = APIRouter()

@router.get("/metrics/overview", response_model=OverviewMetrics)
async def get_overview(
    project_id: str = Depends(get_project_id),
    window: str = Query("24h", description="Time window: 1h, 6h, 24h, 7d"),
    db: AsyncSession = Depends(get_db),
):
    hours = {"1h": 1, "6h": 6, "24h": 24, "7d": 168}.get(window, 24)
    since = datetime.now(timezone.utc) - timedelta(hours=hours)
    pid = UUID(project_id)

    result = await db.execute(
        select(
            func.count(TelemetryEvent.id).label("total"),
            func.coalesce(func.avg(TelemetryEvent.latency_ms), 0).label("avg_latency"),
            func.coalesce(func.percentile_cont(0.95).within_group(TelemetryEvent.latency_ms), 0).label("p95_latency"),
            func.coalesce(func.avg(TelemetryEvent.input_tokens), 0).label("avg_input"),
            func.coalesce(func.avg(TelemetryEvent.output_tokens), 0).label("avg_output"),
        ).where(
            and_(TelemetryEvent.project_id == pid, TelemetryEvent.timestamp >= since)
        )
    )
    row = result.one()

    error_result = await db.execute(
        select(func.count(TelemetryEvent.id)).where(
            and_(
                TelemetryEvent.project_id == pid,
                TelemetryEvent.timestamp >= since,
                TelemetryEvent.status == "error"
            )
        )
    )
    error_count = error_result.scalar() or 0
    error_rate = (error_count / row.total * 100) if row.total > 0 else 0

    last_hour = datetime.now(timezone.utc) - timedelta(hours=1)
    hour_result = await db.execute(
        select(func.count(TelemetryEvent.id)).where(
            and_(TelemetryEvent.project_id == pid, TelemetryEvent.timestamp >= last_hour)
        )
    )
    events_last_hour = hour_result.scalar() or 0

    drift_result = await db.execute(
        select(DriftScore.score).where(
            DriftScore.project_id == pid
        ).order_by(desc(DriftScore.timestamp)).limit(1)
    )
    latest_drift = drift_result.scalar_one_or_none()

    hall_result = await db.execute(
        select(func.avg(HallucinationScore.score)).where(
            and_(HallucinationScore.project_id == pid, HallucinationScore.timestamp >= since)
        )
    )
    hall_rate = hall_result.scalar() or 0

    return OverviewMetrics(
        total_events=row.total,
        avg_latency_ms=round(float(row.avg_latency), 2),
        p95_latency_ms=round(float(row.p95_latency), 2),
        error_rate=round(error_rate, 2),
        avg_input_tokens=round(float(row.avg_input), 1),
        avg_output_tokens=round(float(row.avg_output), 1),
        latest_drift_score=float(latest_drift) if latest_drift else None,
        hallucination_rate=round(float(hall_rate), 4),
        events_last_hour=events_last_hour,
    )

@router.get("/metrics/latency", response_model=TimeSeriesResponse)
async def get_latency_timeseries(
    project_id: str = Depends(get_project_id),
    model_name: Optional[str] = None,
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
    bucket: str = Query("5m", description="Bucket size: 1m, 5m, 15m, 1h"),
    db: AsyncSession = Depends(get_db),
):
    bucket_map = {"1m": "1 minute", "5m": "5 minutes", "15m": "15 minutes", "1h": "1 hour"}
    bucket_interval = bucket_map.get(bucket, "5 minutes")
    end = end or datetime.now(timezone.utc)
    start = start or (end - timedelta(hours=24))
    pid = UUID(project_id)

    query = text(f"""
        SELECT date_trunc('hour', timestamp) +
               (EXTRACT(MINUTE FROM timestamp)::int / {int(bucket_interval.split()[0])} * {int(bucket_interval.split()[0])}) * interval '1 minute' as bucket,
               AVG(latency_ms) as avg_latency
        FROM telemetry_events
        WHERE project_id = :pid AND timestamp >= :start AND timestamp <= :end
        {'AND model_name = :model_name' if model_name else ''}
        GROUP BY bucket
        ORDER BY bucket
    """)
    params = {"pid": str(pid), "start": start, "end": end}
    if model_name:
        params["model_name"] = model_name

    result = await db.execute(query, params)
    points = [MetricPoint(timestamp=row[0], value=round(row[1], 2)) for row in result.fetchall()]

    return TimeSeriesResponse(model_name=model_name, metric="latency_ms", points=points)

@router.get("/metrics/tokens", response_model=TimeSeriesResponse)
async def get_token_timeseries(
    project_id: str = Depends(get_project_id),
    model_name: Optional[str] = None,
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
    db: AsyncSession = Depends(get_db),
):
    end = end or datetime.now(timezone.utc)
    start = start or (end - timedelta(hours=24))
    pid = UUID(project_id)

    query = text("""
        SELECT date_trunc('hour', timestamp) as bucket,
               AVG(input_tokens + output_tokens) as avg_tokens
        FROM telemetry_events
        WHERE project_id = :pid AND timestamp >= :start AND timestamp <= :end
        GROUP BY bucket
        ORDER BY bucket
    """)
    result = await db.execute(query, {"pid": str(pid), "start": start, "end": end})
    points = [MetricPoint(timestamp=row[0], value=round(row[1], 2)) for row in result.fetchall()]

    return TimeSeriesResponse(model_name=model_name, metric="total_tokens", points=points)

@router.get("/metrics/drift", response_model=list[DriftScoreResponse])
async def get_drift_scores(
    project_id: str = Depends(get_project_id),
    model_name: Optional[str] = None,
    limit: int = Query(100, le=500),
    db: AsyncSession = Depends(get_db),
):
    pid = UUID(project_id)
    query = select(DriftScore).where(DriftScore.project_id == pid)
    if model_name:
        query = query.where(DriftScore.model_name == model_name)
    query = query.order_by(desc(DriftScore.timestamp)).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()

@router.get("/metrics/hallucinations", response_model=list[HallucinationScoreResponse])
async def get_hallucination_scores(
    project_id: str = Depends(get_project_id),
    limit: int = Query(100, le=500),
    db: AsyncSession = Depends(get_db),
):
    pid = UUID(project_id)
    result = await db.execute(
        select(HallucinationScore).where(
            HallucinationScore.project_id == pid
        ).order_by(desc(HallucinationScore.timestamp)).limit(limit)
    )
    return result.scalars().all()

@router.get("/events", response_model=list[TelemetryEventResponse])
async def list_events(
    project_id: str = Depends(get_project_id),
    model_name: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = Query(50, le=200),
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    pid = UUID(project_id)
    query = select(TelemetryEvent).where(TelemetryEvent.project_id == pid)
    if model_name:
        query = query.where(TelemetryEvent.model_name == model_name)
    if status:
        query = query.where(TelemetryEvent.status == status)
    query = query.order_by(desc(TelemetryEvent.timestamp)).offset(offset).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()

@router.get("/events/{event_id}", response_model=TelemetryEventDetail)
async def get_event(
    event_id: str,
    project_id: str = Depends(get_project_id),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(TelemetryEvent).where(
            and_(TelemetryEvent.id == UUID(event_id), TelemetryEvent.project_id == UUID(project_id))
        )
    )
    event = result.scalar_one_or_none()
    if not event:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Event not found")

    hall_result = await db.execute(
        select(func.avg(HallucinationScore.score)).where(HallucinationScore.event_id == UUID(event_id))
    )
    hall_score = hall_result.scalar()

    response = TelemetryEventDetail.model_validate(event)
    response.hallucination_score = float(hall_score) if hall_score else None
    return response
