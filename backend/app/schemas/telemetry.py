from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID
from typing import Optional

class TelemetryEventCreate(BaseModel):
    model_name: str
    model_provider: Optional[str] = None
    input_text: Optional[str] = None
    output_text: Optional[str] = None
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    latency_ms: Optional[float] = None
    status: str = "success"
    error_message: Optional[str] = None
    trace_id: Optional[str] = None
    span_id: Optional[str] = None
    parent_span_id: Optional[str] = None
    metadata: Optional[dict] = None
    tags: Optional[list] = None
    timestamp: Optional[datetime] = None

class TelemetryEventResponse(BaseModel):
    id: UUID
    project_id: UUID
    timestamp: datetime
    model_name: str
    model_provider: Optional[str]
    input_tokens: Optional[int]
    output_tokens: Optional[int]
    latency_ms: Optional[float]
    status: str
    trace_id: Optional[str]
    metadata: Optional[dict] = Field(None, validation_alias="extra_metadata")
    tags: Optional[list]

    class Config:
        from_attributes = True
        populate_by_name = True

class TelemetryEventDetail(TelemetryEventResponse):
    input_text: Optional[str]
    output_text: Optional[str]
    error_message: Optional[str]
    span_id: Optional[str]
    parent_span_id: Optional[str]
    hallucination_score: Optional[float] = None

class TelemetryBatchCreate(BaseModel):
    events: list[TelemetryEventCreate] = Field(..., max_length=100)

class IngestResponse(BaseModel):
    accepted: int
    event_ids: list[UUID]
