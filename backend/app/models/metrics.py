import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.core.database import Base

class DriftScore(Base):
    __tablename__ = "drift_scores"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    model_name = Column(String(128), nullable=False)
    metric_name = Column(String(64), nullable=False)
    score = Column(Float, nullable=False)
    p_value = Column(Float)
    reference_window_start = Column(DateTime(timezone=True))
    reference_window_end = Column(DateTime(timezone=True))
    test_window_start = Column(DateTime(timezone=True))
    test_window_end = Column(DateTime(timezone=True))
    details = Column(JSONB, default={})

    __table_args__ = (
        Index("idx_drift_project_time", "project_id", "timestamp"),
    )

class HallucinationScore(Base):
    __tablename__ = "hallucination_scores"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_id = Column(UUID(as_uuid=True), ForeignKey("telemetry_events.id"), nullable=False)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    score = Column(Float, nullable=False)
    method = Column(String(64), nullable=False)
    details = Column(JSONB, default={})

    __table_args__ = (
        Index("idx_hallucination_project_time", "project_id", "timestamp"),
    )
