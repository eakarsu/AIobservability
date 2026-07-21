from __future__ import annotations
import logging
import threading
import time
import uuid
from datetime import datetime, timezone
from typing import Optional
import httpx
from aiobserve.types import EventEnvelope, TelemetryEvent

logger = logging.getLogger("aiobserve")

class ObserveClient:
    """Ordered, payload-bound client for the authoritative collector contract."""
    def __init__(self, endpoint: str, api_key: str, tenant_id: str, project_id: str, batch_size: int = 50,
                 flush_interval: float = 5.0, max_buffer: int = 10_000, capture_content: bool = False,
                 enabled: bool = True):
        if not endpoint or not api_key or not tenant_id or not project_id: raise ValueError("endpoint_api_key_tenant_project_required")
        self.tenant_id, self.project_id, self.batch_size = tenant_id, project_id, batch_size
        self.flush_interval, self.max_buffer, self.capture_content, self.enabled = flush_interval, max_buffer, capture_content, enabled
        self._buffer: list[dict] = []; self._sequence: dict[str, int] = {}; self._lock = threading.RLock(); self._flush_timer = None
        self._client = httpx.Client(base_url=endpoint.rstrip("/"), headers={"X-API-Key": api_key}, timeout=10.0)
        if enabled: self._start_flush_timer()

    def emit(self, kind: str, payload: dict, trace_id: str, span_id: Optional[str] = None, parent_span_id: Optional[str] = None, **versions):
        with self._lock:
            if len(self._buffer) >= self.max_buffer: raise BufferError("telemetry_backpressure")
            sequence = self._sequence.get(trace_id, 0); self._sequence[trace_id] = sequence + 1
            envelope = EventEnvelope(self.tenant_id, self.project_id, kind, payload, trace_id, span_id or uuid.uuid4().hex,
                                     parent_span_id=parent_span_id, sequence=sequence, **versions).to_dict()
            self._buffer.append(envelope)
            should_flush = len(self._buffer) >= self.batch_size
        if should_flush: self.flush()
        return envelope["event_id"]

    def send_event(self, event: TelemetryEvent, kind: str = "trace"):
        if not self.enabled: return None
        payload = event.to_dict()
        if not self.capture_content:
            payload.pop("input_text", None); payload.pop("output_text", None)
        trace_id = event.trace_id or uuid.uuid4().hex
        return self.emit(kind, payload, trace_id, event.span_id, event.parent_span_id, model_version=event.model_version)

    def log(self, model_name: str, **kwargs):
        kwargs.setdefault("timestamp", datetime.now(timezone.utc)); self.send_event(TelemetryEvent(model_name=model_name, **kwargs))

    def flush(self):
        with self._lock:
            pending = list(self._buffer)
        delivered = 0
        for event in pending:
            try:
                response = self._client.post("/api/v1/authoritative/events", json=event)
                if response.status_code not in (202,): response.raise_for_status()
                delivered += 1
            except Exception as exc:
                logger.warning("telemetry flush stopped after %s events: %s", delivered, exc); break
        if delivered:
            with self._lock: del self._buffer[:delivered]
        return delivered

    def _start_flush_timer(self):
        self._flush_timer = threading.Timer(self.flush_interval, self._timer_flush); self._flush_timer.daemon = True; self._flush_timer.start()
    def _timer_flush(self):
        self.flush()
        if self.enabled: self._start_flush_timer()
    def trace(self, name: str): return TraceContext(self, name)
    def close(self):
        self.enabled = False
        if self._flush_timer: self._flush_timer.cancel()
        self.flush(); self._client.close()
    def __enter__(self): return self
    def __exit__(self, *_args): self.close()

class TraceContext:
    def __init__(self, client, name): self.client, self.name, self.trace_id = client, name, uuid.uuid4().hex
    def span(self, name): return SpanContext(self, name)
    def __enter__(self): return self
    def __exit__(self, *_args): return None

class SpanContext:
    def __init__(self, trace, name): self.trace, self.name, self.span_id, self._start, self._metadata, self._input, self._output = trace, name, uuid.uuid4().hex, None, {"span_name": name}, None, None
    def set_input(self, value): self._input = value
    def set_output(self, value): self._output = value
    def set_metadata(self, value): self._metadata.update(value)
    def __enter__(self): self._start = time.time(); return self
    def __exit__(self, exc_type, exc, _tb):
        event = TelemetryEvent(self.name, self._input, self._output, latency_ms=(time.time()-self._start)*1000, status="error" if exc_type else "success", error_message=str(exc) if exc else None, trace_id=self.trace.trace_id, span_id=self.span_id, metadata=self._metadata, timestamp=datetime.now(timezone.utc))
        self.trace.client.send_event(event)
