from pydantic import BaseModel
from datetime import datetime
from uuid import UUID
from typing import Optional

class MetricPoint(BaseModel):
    timestamp: datetime
    value: float

class OverviewMetrics(BaseModel):
    total_events: int
    avg_latency_ms: float
    p95_latency_ms: float
    error_rate: float
    avg_input_tokens: float
    avg_output_tokens: float
    latest_drift_score: Optional[float]
    hallucination_rate: float
    events_last_hour: int

class TimeSeriesResponse(BaseModel):
    model_name: Optional[str]
    metric: str
    points: list[MetricPoint]

class DriftScoreResponse(BaseModel):
    id: UUID
    project_id: UUID
    timestamp: datetime
    model_name: str
    metric_name: str
    score: float
    p_value: Optional[float]
    details: Optional[dict]

    class Config:
        from_attributes = True

class HallucinationScoreResponse(BaseModel):
    id: UUID
    event_id: UUID
    timestamp: datetime
    score: float
    method: str
    details: Optional[dict]

    class Config:
        from_attributes = True
