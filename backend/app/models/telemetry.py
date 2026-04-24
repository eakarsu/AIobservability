import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, Text, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.core.database import Base

class TelemetryEvent(Base):
    __tablename__ = "telemetry_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, index=True)
    trace_id = Column(String(64), index=True)
    span_id = Column(String(64))
    parent_span_id = Column(String(64))
    model_name = Column(String(128), nullable=False, index=True)
    model_provider = Column(String(64))
    input_text = Column(Text)
    output_text = Column(Text)
    input_tokens = Column(Integer)
    output_tokens = Column(Integer)
    latency_ms = Column(Float)
    status = Column(String(32), default="success")
    error_message = Column(Text)
    extra_metadata = Column("metadata", JSONB, default={})
    tags = Column(JSONB, default=[])

    __table_args__ = (
        Index("idx_telemetry_project_time", "project_id", "timestamp"),
        Index("idx_telemetry_model_time", "model_name", "timestamp"),
    )
