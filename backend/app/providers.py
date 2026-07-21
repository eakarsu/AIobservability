"""Typed outbound alert adapters with verifiable receipts."""
from __future__ import annotations
import os
import httpx

ADAPTERS = {
    "slack": ("SLACK_WEBHOOK_URL", None),
    "pagerduty": ("PAGERDUTY_EVENTS_URL", "PAGERDUTY_TOKEN"),
    "webhook": ("ALERT_WEBHOOK_URL", "ALERT_WEBHOOK_TOKEN"),
}

async def dispatch(delivery: dict) -> dict:
    if delivery["provider"] not in ADAPTERS:
        raise ValueError("unsupported_provider")
    url_name, token_name = ADAPTERS[delivery["provider"]]
    url, token = os.getenv(url_name), os.getenv(token_name) if token_name else None
    if not url or (token_name and not token):
        raise ValueError(f"provider_not_configured:{delivery['provider']}")
    headers = {"Idempotency-Key": delivery["idempotency_key"], "X-Payload-Hash": delivery["payload_hash"]}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    async with httpx.AsyncClient(timeout=float(os.getenv("PROVIDER_TIMEOUT_SECONDS", "10"))) as client:
        response = await client.post(url, json={"operation": delivery["operation"], "payload": delivery["payload"]}, headers=headers)
        response.raise_for_status()
        receipt = response.json()
    if not receipt.get("providerRequestId") or receipt.get("payloadHash") != delivery["payload_hash"]:
        raise ValueError("invalid_provider_receipt")
    return receipt
