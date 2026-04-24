import time
import functools
from datetime import datetime, timezone
from typing import Optional
from aiobserve.types import TelemetryEvent

def observe(client, model_name: str, model_provider: Optional[str] = None, tags: Optional[list] = None):
    """Decorator to automatically observe function calls."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            status = "success"
            error_message = None
            result = None

            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                status = "error"
                error_message = str(e)
                raise
            finally:
                latency_ms = (time.time() - start_time) * 1000

                # Try to extract input/output text
                input_text = None
                if args:
                    input_text = str(args[0]) if args else None
                elif "prompt" in kwargs:
                    input_text = str(kwargs["prompt"])
                elif "messages" in kwargs:
                    input_text = str(kwargs["messages"])

                output_text = str(result) if result is not None else None

                # Try to extract token counts from common response formats
                input_tokens = None
                output_tokens = None
                if hasattr(result, "usage"):
                    usage = result.usage
                    if hasattr(usage, "prompt_tokens"):
                        input_tokens = usage.prompt_tokens
                    if hasattr(usage, "completion_tokens"):
                        output_tokens = usage.completion_tokens

                event = TelemetryEvent(
                    model_name=model_name,
                    model_provider=model_provider,
                    input_text=input_text,
                    output_text=output_text,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    latency_ms=latency_ms,
                    status=status,
                    error_message=error_message,
                    tags=tags,
                    timestamp=datetime.now(timezone.utc),
                )
                client.send_event(event)

        return wrapper
    return decorator
