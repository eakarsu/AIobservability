import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, Integer, Boolean, DateTime, ForeignKey, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.core.database import Base
import enum

class MetricType(str, enum.Enum):
    LATENCY = "latency"
    ERROR_RATE = "error_rate"
    DRIFT_SCORE = "drift_score"
    HALLUCINATION_SCORE = "hallucination_score"
    TOKEN_USAGE = "token_usage"

class Condition(str, enum.Enum):
    GT = "gt"
    LT = "lt"
    GTE = "gte"
    LTE = "lte"

class AlertStatus(str, enum.Enum):
    FIRING = "firing"
    RESOLVED = "resolved"
    ACKNOWLEDGED = "acknowledged"

class AlertRule(Base):
    __tablename__ = "alert_rules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    name = Column(String(256), nullable=False)
    metric_type = Column(SAEnum(MetricType), nullable=False)
    condition = Column(SAEnum(Condition), nullable=False)
    threshold = Column(Float, nullable=False)
    window_minutes = Column(Integer, default=5)
    notification_channel = Column(JSONB, default={})
    is_active = Column(Boolean, default=True)
    cooldown_minutes = Column(Integer, default=30)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

class AlertFired(Base):
    __tablename__ = "alerts_fired"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    rule_id = Column(UUID(as_uuid=True), ForeignKey("alert_rules.id"), nullable=False)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    triggered_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    metric_value = Column(Float, nullable=False)
    resolved_at = Column(DateTime(timezone=True))
    status = Column(SAEnum(AlertStatus), default=AlertStatus.FIRING)
    details = Column(JSONB, default={})
