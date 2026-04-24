from pydantic import BaseModel
from datetime import datetime
from uuid import UUID
from typing import Optional

class AlertRuleCreate(BaseModel):
    name: str
    metric_type: str
    condition: str
    threshold: float
    window_minutes: int = 5
    notification_channel: dict = {}
    cooldown_minutes: int = 30

class AlertRuleResponse(BaseModel):
    id: UUID
    project_id: UUID
    name: str
    metric_type: str
    condition: str
    threshold: float
    window_minutes: int
    notification_channel: dict
    is_active: bool
    cooldown_minutes: int
    created_at: datetime

    class Config:
        from_attributes = True

class AlertRuleUpdate(BaseModel):
    name: Optional[str] = None
    threshold: Optional[float] = None
    window_minutes: Optional[int] = None
    notification_channel: Optional[dict] = None
    is_active: Optional[bool] = None
    cooldown_minutes: Optional[int] = None

class AlertFiredResponse(BaseModel):
    id: UUID
    rule_id: UUID
    project_id: UUID
    triggered_at: datetime
    metric_value: float
    resolved_at: Optional[datetime]
    status: str
    details: Optional[dict]

    class Config:
        from_attributes = True
