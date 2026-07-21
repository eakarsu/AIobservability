"""Pure, deterministic policy for telemetry, evaluations, and incidents."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Mapping


EVENT_KINDS = {
    "trace", "prompt", "response", "tool_call", "retrieval", "evaluation",
    "cost", "feedback",
}
INCIDENT_TRANSITIONS = {
    "open": {"acknowledged", "resolved"},
    "acknowledged": {"resolved"},
    "resolved": {"reopened"},
    "reopened": {"acknowledged", "resolved"},
}
ROLES = {
    "viewer": {"read"},
    "operator": {"read", "ingest", "acknowledge"},
    "evaluator": {"read", "evaluate"},
    "admin": {"read", "ingest", "evaluate", "acknowledge", "resolve", "configure"},
}
SENSITIVE_KEYS = {"password", "secret", "token", "authorization", "api_key", "cookie", "ssn", "input_text", "output_text", "prompt", "response", "content"}


class PolicyError(ValueError):
    """A stable, user-safe domain rejection."""


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def payload_hash(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode()).hexdigest()


def redact(value: Any) -> Any:
    if isinstance(value, list):
        return [redact(item) for item in value]
    if isinstance(value, dict):
        return {
            key: "[REDACTED]" if key.lower() in SENSITIVE_KEYS else redact(item)
            for key, item in value.items()
        }
    return value


def authorize(identity: Mapping[str, Any], tenant_id: str, action: str, project_id: str | None = None) -> None:
    if not tenant_id or identity.get("tenant_id") != tenant_id:
        raise PolicyError("tenant_scope_denied")
    if action not in ROLES.get(str(identity.get("role")), set()):
        raise PolicyError("role_scope_denied")
    projects = identity.get("project_ids")
    if project_id and projects not in (None, "*") and project_id not in projects:
        raise PolicyError("project_scope_denied")


def validate_envelope(envelope: Mapping[str, Any]) -> dict[str, Any]:
    required = ("tenant_id", "project_id", "event_id", "trace_id", "span_id", "kind", "schema_version", "sequence", "payload")
    missing = [field for field in required if envelope.get(field) in (None, "")]
    if missing:
        raise PolicyError(f"missing_fields:{','.join(missing)}")
    if envelope["kind"] not in EVENT_KINDS:
        raise PolicyError("unsupported_event_kind")
    if not isinstance(envelope["sequence"], int) or envelope["sequence"] < 0:
        raise PolicyError("invalid_sequence")
    if not isinstance(envelope["schema_version"], int) or envelope["schema_version"] < 1:
        raise PolicyError("invalid_schema_version")
    supplied = envelope.get("payload_hash")
    if supplied and supplied != payload_hash(envelope["payload"]):
        raise PolicyError("payload_hash_mismatch")
    cleaned = dict(envelope)
    cleaned["payload"] = redact(envelope["payload"])
    cleaned["payload_hash"] = payload_hash(cleaned["payload"])
    return cleaned


def validate_eval_run(run: Mapping[str, Any]) -> dict[str, Any]:
    for field in ("project_id", "dataset_id", "dataset_version", "model_version", "prompt_version", "evaluator_version"):
        if not run.get(field):
            raise PolicyError(f"missing_{field}")
    thresholds = run.get("thresholds")
    metrics = run.get("metrics")
    if not isinstance(thresholds, dict) or not thresholds or not isinstance(metrics, dict):
        raise PolicyError("metrics_and_thresholds_required")
    if any(not isinstance(value, (int, float)) for value in thresholds.values()) or any(
        name not in metrics or not isinstance(metrics[name], (int, float)) for name in thresholds
    ):
        raise PolicyError("complete_numeric_evaluation_required")
    failures = sorted(name for name, minimum in thresholds.items() if metrics.get(name, float("-inf")) < minimum)
    return {**run, "accepted": not failures, "failures": failures, "reproducibility_hash": payload_hash(run)}


def ingestion_decision(queue_depth: int, capacity: int, oldest_age_seconds: float) -> dict[str, Any]:
    if capacity <= 0 or queue_depth < 0:
        raise PolicyError("invalid_capacity")
    ratio = queue_depth / capacity
    if ratio >= 1:
        return {"accepted": False, "reason": "backpressure", "retry_after_seconds": max(1, int(oldest_age_seconds / 2) or 1)}
    return {"accepted": True, "reason": "accepted", "pressure": round(ratio, 4)}


def incident_key(tenant_id: str, project_id: str, signal: str, scope: str, window_start: str) -> str:
    return payload_hash({"tenant": tenant_id, "project": project_id, "signal": signal, "scope": scope, "window": window_start})


def transition_incident(current: str, target: str, actor_role: str, owner_id: str | None = None) -> dict[str, Any]:
    if target not in INCIDENT_TRANSITIONS.get(current, set()):
        raise PolicyError("invalid_incident_transition")
    if target == "acknowledged" and not owner_id:
        raise PolicyError("incident_owner_required")
    action = "resolve" if target == "resolved" else "acknowledge"
    if action not in ROLES.get(actor_role, set()):
        raise PolicyError("incident_action_denied")
    return {"status": target, "owner_id": owner_id, "changed_at": datetime.now(timezone.utc).isoformat()}


def delivery_receipt(provider: str, payload: Mapping[str, Any], idempotency_key: str, receipt: Mapping[str, Any]) -> dict[str, Any]:
    if not provider or not idempotency_key or not receipt.get("provider_request_id"):
        raise PolicyError("incomplete_provider_receipt")
    expected = payload_hash(payload)
    if receipt.get("payload_hash") != expected:
        raise PolicyError("provider_receipt_payload_mismatch")
    return {"provider": provider, "idempotency_key": idempotency_key, "payload_hash": expected, "receipt": dict(receipt)}
