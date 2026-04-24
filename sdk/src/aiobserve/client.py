import time
import threading
import logging
from datetime import datetime, timezone
from typing import Optional
import httpx
from aiobserve.types import TelemetryEvent

logger = logging.getLogger("aiobserve")

class ObserveClient:
    """Client for sending telemetry to the AI Observability Platform."""

    def __init__(
        self,
        endpoint: str = "http://localhost:8000",
        api_key: str = "",
        project_id: Optional[str] = None,
        batch_size: int = 50,
        flush_interval: float = 5.0,
        enabled: bool = True,
    ):
        self.endpoint = endpoint.rstrip("/")
        self.api_key = api_key
        self.project_id = project_id
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self.enabled = enabled

        self._buffer: list[dict] = []
        self._lock = threading.Lock()
        self._flush_timer: Optional[threading.Timer] = None
        self._client = httpx.Client(
            base_url=self.endpoint,
            headers={"X-API-Key": self.api_key},
            timeout=10.0,
        )

        if self.enabled:
            self._start_flush_timer()

    def send_event(self, event: TelemetryEvent):
        """Add a telemetry event to the buffer."""
        if not self.enabled:
            return

        with self._lock:
            self._buffer.append(event.to_dict())
            if len(self._buffer) >= self.batch_size:
                self._flush_buffer()

    def log(
        self,
        model_name: str,
        input_text: Optional[str] = None,
        output_text: Optional[str] = None,
        input_tokens: Optional[int] = None,
        output_tokens: Optional[int] = None,
        latency_ms: Optional[float] = None,
        status: str = "success",
        error_message: Optional[str] = None,
        metadata: Optional[dict] = None,
        tags: Optional[list] = None,
        **kwargs,
    ):
        """Convenience method to log a telemetry event."""
        event = TelemetryEvent(
            model_name=model_name,
            input_text=input_text,
            output_text=output_text,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            latency_ms=latency_ms,
            status=status,
            error_message=error_message,
            metadata=metadata,
            tags=tags,
            timestamp=datetime.now(timezone.utc),
            **kwargs,
        )
        self.send_event(event)

    def flush(self):
        """Manually flush the buffer."""
        with self._lock:
            self._flush_buffer()

    def _flush_buffer(self):
        """Send buffered events to the server."""
        if not self._buffer:
            return

        events = self._buffer.copy()
        self._buffer.clear()

        try:
            response = self._client.post(
                "/api/v1/telemetry",
                json={"events": events},
            )
            if response.status_code != 202:
                logger.warning(f"Failed to send telemetry: {response.status_code} {response.text}")
        except Exception as e:
            logger.error(f"Error sending telemetry: {e}")
            # Re-add events to buffer for retry
            with self._lock:
                self._buffer.extend(events)

    def _start_flush_timer(self):
        """Start periodic flush timer."""
        self._flush_timer = threading.Timer(self.flush_interval, self._timer_flush)
        self._flush_timer.daemon = True
        self._flush_timer.start()

    def _timer_flush(self):
        """Timer callback to flush buffer."""
        self.flush()
        if self.enabled:
            self._start_flush_timer()

    def trace(self, name: str):
        """Create a trace context."""
        return TraceContext(self, name)

    def close(self):
        """Flush remaining events and close."""
        self.enabled = False
        if self._flush_timer:
            self._flush_timer.cancel()
        self.flush()
        self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


class TraceContext:
    """Context manager for tracing a pipeline."""

    def __init__(self, client: ObserveClient, name: str):
        self.client = client
        self.name = name
        import uuid
        self.trace_id = str(uuid.uuid4())[:16]
        self._spans: list[dict] = []

    def span(self, name: str):
        return SpanContext(self, name)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass


class SpanContext:
    """Context manager for a single span within a trace."""

    def __init__(self, trace: TraceContext, name: str):
        self.trace = trace
        self.name = name
        import uuid
        self.span_id = str(uuid.uuid4())[:16]
        self._start_time: Optional[float] = None
        self._metadata: dict = {"span_name": name}
        self._input_text: Optional[str] = None
        self._output_text: Optional[str] = None

    def set_input(self, text: str):
        self._input_text = text

    def set_output(self, text: str):
        self._output_text = text

    def set_metadata(self, metadata: dict):
        self._metadata.update(metadata)

    def __enter__(self):
        self._start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        latency = (time.time() - self._start_time) * 1000 if self._start_time else None
        status = "error" if exc_type else "success"
        error_msg = str(exc_val) if exc_val else None

        event = TelemetryEvent(
            model_name=self.name,
            input_text=self._input_text,
            output_text=self._output_text,
            latency_ms=latency,
            status=status,
            error_message=error_msg,
            trace_id=self.trace.trace_id,
            span_id=self.span_id,
            metadata=self._metadata,
            timestamp=datetime.now(timezone.utc),
        )
        self.trace.client.send_event(event)
