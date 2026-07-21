from aiobserve.types import EventEnvelope, TelemetryEvent

__all__ = ["ObserveClient", "EventEnvelope", "TelemetryEvent", "observe"]
__version__ = "1.0.0"

def __getattr__(name):
    if name == "ObserveClient":
        from aiobserve.client import ObserveClient
        return ObserveClient
    if name == "observe":
        from aiobserve.decorators import observe
        return observe
    raise AttributeError(name)
