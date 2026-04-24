from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone
import uuid
from app.core.database import get_db
from app.core.security import get_project_id
from app.models.telemetry import TelemetryEvent
from app.schemas.telemetry import TelemetryEventCreate, TelemetryBatchCreate, IngestResponse

router = APIRouter()

@router.post("/telemetry", response_model=IngestResponse, status_code=202)
async def ingest_telemetry(
    batch: TelemetryBatchCreate,
    project_id: str = Depends(get_project_id),
    db: AsyncSession = Depends(get_db),
):
    event_ids = []
    for event_data in batch.events:
        event_id = uuid.uuid4()
        event = TelemetryEvent(
            id=event_id,
            project_id=uuid.UUID(project_id),
            timestamp=event_data.timestamp or datetime.now(timezone.utc),
            model_name=event_data.model_name,
            model_provider=event_data.model_provider,
            input_text=event_data.input_text,
            output_text=event_data.output_text,
            input_tokens=event_data.input_tokens,
            output_tokens=event_data.output_tokens,
            latency_ms=event_data.latency_ms,
            status=event_data.status,
            error_message=event_data.error_message,
            trace_id=event_data.trace_id,
            span_id=event_data.span_id,
            parent_span_id=event_data.parent_span_id,
            extra_metadata=event_data.metadata or {},
            tags=event_data.tags or [],
        )
        db.add(event)
        event_ids.append(event_id)

    await db.commit()
    return IngestResponse(accepted=len(event_ids), event_ids=event_ids)

@router.post("/telemetry/single", response_model=IngestResponse, status_code=202)
async def ingest_single(
    event_data: TelemetryEventCreate,
    project_id: str = Depends(get_project_id),
    db: AsyncSession = Depends(get_db),
):
    batch = TelemetryBatchCreate(events=[event_data])
    return await ingest_telemetry(batch, project_id, db)
