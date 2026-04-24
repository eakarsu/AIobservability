from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
import uuid

@dataclass
class TelemetryEvent:
    model_name: str
    input_text: Optional[str] = None
    output_text: Optional[str] = None
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    latency_ms: Optional[float] = None
    status: str = "success"
    error_message: Optional[str] = None
    model_provider: Optional[str] = None
    trace_id: Optional[str] = None
    span_id: Optional[str] = field(default_factory=lambda: str(uuid.uuid4())[:16])
    parent_span_id: Optional[str] = None
    metadata: Optional[dict] = None
    tags: Optional[list] = None
    timestamp: Optional[datetime] = None

    def to_dict(self) -> dict:
        data = {}
        for key, value in self.__dict__.items():
            if value is not None:
                if isinstance(value, datetime):
                    data[key] = value.isoformat()
                else:
                    data[key] = value
        return data
