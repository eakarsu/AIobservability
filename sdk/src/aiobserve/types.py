from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional
import hashlib
import json
import uuid

EVENT_KINDS = {"trace", "prompt", "response", "tool_call", "retrieval", "evaluation", "cost", "feedback"}

def canonical_hash(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return hashlib.sha256(encoded).hexdigest()

@dataclass
class EventEnvelope:
    tenant_id: str
    project_id: str
    kind: str
    payload: dict
    trace_id: str
    span_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    parent_span_id: Optional[str] = None
    schema_version: int = 1
    sequence: int = 0
    occurred_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    model_version: Optional[str] = None
    prompt_version: Optional[str] = None
    retrieval_version: Optional[str] = None
    cost_micros: Optional[int] = None

    def to_dict(self) -> dict:
        if self.kind not in EVENT_KINDS: raise ValueError("unsupported_event_kind")
        if not self.tenant_id or not self.project_id or not self.trace_id: raise ValueError("tenant_project_trace_required")
        value = {key: item for key, item in self.__dict__.items() if item is not None}
        value["payload_hash"] = canonical_hash(self.payload)
        return value

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
    span_id: Optional[str] = field(default_factory=lambda: uuid.uuid4().hex)
    parent_span_id: Optional[str] = None
    metadata: Optional[dict] = None
    tags: Optional[list] = None
    timestamp: Optional[datetime] = None
    model_version: Optional[str] = None

    def to_dict(self) -> dict:
        return {key: item.isoformat() if isinstance(item, datetime) else item for key, item in self.__dict__.items() if item is not None}
