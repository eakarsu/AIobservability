from __future__ import annotations
import json
import os
import uuid
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Body, Depends, HTTPException, Query
import httpx
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.security import Identity, get_identity
from app.domain.observability import (PolicyError, authorize, incident_key, payload_hash,
    transition_incident, validate_envelope, validate_eval_run)
from app.providers import dispatch

router = APIRouter(prefix="/authoritative", tags=["Authoritative observability"])

def permitted(identity: Identity, action: str, project_id: str | None = None) -> None:
    try: authorize(identity.as_policy(), identity.tenant_id, action, project_id)
    except PolicyError as exc: raise HTTPException(403, str(exc)) from exc

@router.post("/ai/explain")
async def explain_observability(body: dict = Body(...), identity: Identity = Depends(get_identity), db: AsyncSession = Depends(get_db)):
    question = str(body.get("question") or "").strip()
    if not question: raise HTTPException(422, "question_required")
    permitted(identity, "read", identity.project_id)
    api_key = str(os.getenv("OPENROUTER_API_KEY") or "").strip()
    model = str(os.getenv("OPENROUTER_MODEL") or "").strip()
    base_url = str(os.getenv("OPENROUTER_BASE_URL") or "").strip().rstrip("/")
    if not api_key: raise HTTPException(503, "OPENROUTER_API_KEY_not_configured")
    if not model: raise HTTPException(503, "OPENROUTER_MODEL_not_configured")
    if base_url != "https://openrouter.ai/api/v1": raise HTTPException(503, "OPENROUTER_BASE_URL_invalid")
    event_count = (await db.execute(text("SELECT COUNT(*) FROM observability_events WHERE tenant_id=:tenant AND project_id=:project AND expires_at>NOW()"), {"tenant": identity.tenant_id, "project": identity.project_id})).scalar_one()
    prompt = f"Answer this observability question using only the supplied facts. Question: {question}\nFacts: active retained event count={event_count}. If more evidence is needed, say exactly which telemetry should be collected."
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(f"{base_url}/chat/completions", headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json", "X-Title": "AI Observability Platform"}, json={"model": model, "messages": [{"role": "system", "content": "You are a grounded LLM observability analyst. Never invent metrics."}, {"role": "user", "content": prompt}], "max_tokens": 1200})
    try: data = response.json()
    except ValueError as exc: raise HTTPException(502, "openrouter_invalid_json") from exc
    if not response.is_success or data.get("error"): raise HTTPException(502, "openrouter_request_failed")
    content = data.get("choices", [{}])[0].get("message", {}).get("content")
    if not isinstance(content, str) or not content.strip(): raise HTTPException(502, "openrouter_empty_response")
    result_id = str(uuid.uuid4())
    await db.execute(text("INSERT INTO observability_ai_results(id,tenant_id,project_id,user_id,endpoint,input_data,result,model) VALUES(:id,:tenant,:project,:user,'/api/v1/authoritative/ai/explain',CAST(:input AS jsonb),CAST(:result AS jsonb),:model)"), {"id": result_id, "tenant": identity.tenant_id, "project": identity.project_id, "user": identity.key_id, "input": json.dumps({"question": question, "event_count": event_count}), "result": json.dumps({"insight": content}), "model": model})
    await db.commit()
    return {"result_id": result_id, "insight": content, "model": data.get("model") or model}

@router.post("/events", status_code=202)
async def ingest_event(body: dict = Body(...), identity: Identity = Depends(get_identity), db: AsyncSession = Depends(get_db)):
    permitted(identity, "ingest", body.get("project_id"))
    try: event = validate_envelope(body)
    except PolicyError as exc: raise HTTPException(422, str(exc)) from exc
    if event["tenant_id"] != identity.tenant_id: raise HTTPException(403, "tenant_scope_denied")
    occurred = event.get("occurred_at") or datetime.now(timezone.utc).isoformat()
    result = await db.execute(text("""INSERT INTO observability_events(tenant_id,project_id,event_id,trace_id,span_id,parent_span_id,kind,schema_version,sequence,occurred_at,payload,payload_hash,model_version,prompt_version,retrieval_version,cost_micros,expires_at)
      VALUES(:tenant,:project,:event,:trace,:span,:parent,:kind,:schema,:sequence,:occurred,CAST(:payload AS jsonb),:hash,:model,:prompt,:retrieval,:cost,NOW()+(:retention||' days')::interval)
      ON CONFLICT(tenant_id,project_id,event_id) DO NOTHING RETURNING event_id"""), {"tenant": identity.tenant_id, "project": event["project_id"], "event": event["event_id"], "trace": event["trace_id"], "span": event["span_id"], "parent": event.get("parent_span_id"), "kind": event["kind"], "schema": event["schema_version"], "sequence": event["sequence"], "occurred": occurred, "payload": json.dumps(event["payload"]), "hash": event["payload_hash"], "model": event.get("model_version"), "prompt": event.get("prompt_version"), "retrieval": event.get("retrieval_version"), "cost": event.get("cost_micros"), "retention": identity.retention_days})
    if not result.first():
        existing = await db.execute(text("SELECT payload_hash FROM observability_events WHERE tenant_id=:t AND project_id=:p AND event_id=:e"), {"t": identity.tenant_id, "p": event["project_id"], "e": event["event_id"]})
        if existing.scalar_one() != event["payload_hash"]: raise HTTPException(409, "idempotency_payload_mismatch")
    await db.execute(text("INSERT INTO observability_audit(tenant_id,project_id,actor_id,actor_role,action,resource_type,resource_id,after_hash) VALUES(:t,:p,:a,:r,'event.ingested','event',:e,:h)"), {"t": identity.tenant_id, "p": event["project_id"], "a": identity.key_id, "r": identity.role, "e": event["event_id"], "h": event["payload_hash"]})
    await db.commit(); return {"event_id": event["event_id"], "payload_hash": event["payload_hash"]}

@router.get("/traces/{trace_id}")
async def trace(trace_id: str, project_id: str = Query(...), identity: Identity = Depends(get_identity), db: AsyncSession = Depends(get_db)):
    permitted(identity, "read", project_id)
    rows = await db.execute(text("SELECT event_id,trace_id,span_id,parent_span_id,kind,schema_version,sequence,occurred_at,payload,payload_hash,model_version,prompt_version,retrieval_version,cost_micros FROM observability_events WHERE tenant_id=:t AND project_id=:p AND trace_id=:trace AND expires_at>NOW() ORDER BY sequence,received_at LIMIT 5000"), {"t": identity.tenant_id, "p": project_id, "trace": trace_id})
    return {"trace_id": trace_id, "events": [dict(row) for row in rows.mappings()]}

@router.post("/evaluations", status_code=201)
async def evaluation(body: dict = Body(...), identity: Identity = Depends(get_identity), db: AsyncSession = Depends(get_db)):
    permitted(identity, "evaluate", body.get("project_id"))
    try: outcome = validate_eval_run(body)
    except PolicyError as exc: raise HTTPException(422, str(exc)) from exc
    run_id = body.get("id") or str(uuid.uuid4())
    await db.execute(text("INSERT INTO observability_eval_runs(id,tenant_id,project_id,dataset_id,dataset_version,model_version,prompt_version,evaluator_version,thresholds,metrics,accepted,failures,reproducibility_hash,created_by) VALUES(:id,:t,:p,:di,:dv,:mv,:pv,:ev,CAST(:th AS jsonb),CAST(:me AS jsonb),:ok,CAST(:fa AS jsonb),:rh,NULL)"), {"id": run_id, "t": identity.tenant_id, "p": body["project_id"], "di": body["dataset_id"], "dv": body["dataset_version"], "mv": body["model_version"], "pv": body["prompt_version"], "ev": body["evaluator_version"], "th": json.dumps(body["thresholds"]), "me": json.dumps(body["metrics"]), "ok": outcome["accepted"], "fa": json.dumps(outcome["failures"]), "rh": outcome["reproducibility_hash"]})
    await db.commit()
    if not outcome["accepted"]: raise HTTPException(422, {"id": run_id, **outcome})
    return {"id": run_id, **outcome}

@router.post("/signals", status_code=201)
async def signal(body: dict = Body(...), identity: Identity = Depends(get_identity), db: AsyncSession = Depends(get_db)):
    permitted(identity, "acknowledge", body.get("project_id"))
    required = ("project_id", "signal", "scope", "window_start", "severity", "route")
    if any(not body.get(k) for k in required): raise HTTPException(422, "incomplete_signal")
    if body["signal"] not in {"drift", "hallucination", "latency", "budget"}: raise HTTPException(422, "unsupported_signal")
    key = incident_key(identity.tenant_id, body["project_id"], body["signal"], body["scope"], body["window_start"]); incident_id = str(uuid.uuid4())
    result = await db.execute(text("INSERT INTO observability_incidents(id,tenant_id,project_id,dedupe_key,signal,scope,status,severity,route) VALUES(:id,:t,:p,:d,:s,:sc,'open',:sev,:r) ON CONFLICT(tenant_id,project_id,dedupe_key) DO UPDATE SET updated_at=NOW() RETURNING *"), {"id": incident_id, "t": identity.tenant_id, "p": body["project_id"], "d": key, "s": body["signal"], "sc": body["scope"], "sev": body["severity"], "r": body["route"]})
    row = dict(result.mappings().one())
    await db.execute(text("INSERT INTO observability_incident_history(tenant_id,incident_id,to_status,actor_id,owner_id) VALUES(:t,:id,'open',:actor,:owner)"), {"t": identity.tenant_id, "id": row["id"], "actor": identity.key_id, "owner": row.get("owner_id")})
    await db.commit(); return row

@router.post("/incidents/{incident_id}/transition")
async def change_incident(incident_id: str, body: dict = Body(...), identity: Identity = Depends(get_identity), db: AsyncSession = Depends(get_db)):
    row = (await db.execute(text("SELECT * FROM observability_incidents WHERE id=:id AND tenant_id=:t FOR UPDATE"), {"id": incident_id, "t": identity.tenant_id})).mappings().first()
    if not row: raise HTTPException(404, "incident_not_found")
    try: update = transition_incident(row["status"], body.get("target"), identity.role, body.get("owner_id"))
    except PolicyError as exc: raise HTTPException(422, str(exc)) from exc
    permitted(identity, "resolve" if body.get("target") == "resolved" else "acknowledge", str(row["project_id"]))
    await db.execute(text("UPDATE observability_incidents SET status=:s,owner_id=COALESCE(:o,owner_id),resolution=:r,updated_at=NOW() WHERE id=:id"), {"s": update["status"], "o": update["owner_id"], "r": body.get("resolution"), "id": incident_id})
    await db.execute(text("INSERT INTO observability_incident_history(tenant_id,incident_id,from_status,to_status,actor_id,owner_id,resolution) VALUES(:t,:id,:before,:after,:actor,:owner,:resolution)"), {"t": identity.tenant_id, "id": incident_id, "before": row["status"], "after": update["status"], "actor": identity.key_id, "owner": update["owner_id"], "resolution": body.get("resolution")})
    await db.execute(text("INSERT INTO observability_audit(tenant_id,project_id,actor_id,actor_role,action,resource_type,resource_id,before_hash,after_hash) VALUES(:t,:p,:a,:r,'incident.transitioned','incident',:id,:before,:after)"), {"t": identity.tenant_id, "p": row["project_id"], "a": identity.key_id, "r": identity.role, "id": incident_id, "before": payload_hash({"status": row["status"]}), "after": payload_hash({"status": update["status"]})})
    await db.commit(); return update

@router.delete("/retention/expired")
async def purge_expired(project_id: str = Query(...), limit: int = Query(1000, ge=1, le=10000), identity: Identity = Depends(get_identity), db: AsyncSession = Depends(get_db)):
    permitted(identity, "configure", project_id)
    removed = await db.execute(text("DELETE FROM observability_events WHERE ctid IN (SELECT ctid FROM observability_events WHERE tenant_id=:t AND project_id=:p AND expires_at<=NOW() LIMIT :limit) RETURNING event_id,payload_hash"), {"t": identity.tenant_id, "p": project_id, "limit": limit})
    values = [dict(row) for row in removed.mappings()]
    await db.execute(text("INSERT INTO observability_audit(tenant_id,project_id,actor_id,actor_role,action,resource_type,resource_id,metadata) VALUES(:t,:p,:a,:r,'retention.purged','project',:p,CAST(:metadata AS jsonb))"), {"t": identity.tenant_id, "p": project_id, "a": identity.key_id, "r": identity.role, "metadata": json.dumps({"count": len(values), "event_hashes": [v["payload_hash"] for v in values]})})
    await db.commit(); return {"purged": len(values)}

@router.post("/incidents/{incident_id}/deliveries", status_code=202)
async def queue_delivery(incident_id: str, body: dict = Body(...), identity: Identity = Depends(get_identity), db: AsyncSession = Depends(get_db)):
    incident = (await db.execute(text("SELECT project_id FROM observability_incidents WHERE id=:id AND tenant_id=:t"), {"id": incident_id, "t": identity.tenant_id})).first()
    if not incident: raise HTTPException(404, "incident_not_found")
    permitted(identity, "acknowledge", str(incident.project_id))
    if not body.get("provider") or not body.get("idempotency_key"): raise HTTPException(422, "delivery_identity_required")
    delivery_id = str(uuid.uuid4()); digest = payload_hash(body.get("payload", {}))
    row = await db.execute(text("INSERT INTO observability_provider_deliveries(id,tenant_id,project_id,provider,operation,idempotency_key,payload_hash,payload) VALUES(:id,:t,:p,:pr,'alert',:key,:h,CAST(:payload AS jsonb)) ON CONFLICT(tenant_id,provider,idempotency_key) DO UPDATE SET updated_at=observability_provider_deliveries.updated_at RETURNING *"), {"id": delivery_id, "t": identity.tenant_id, "p": str(incident.project_id), "pr": body.get("provider"), "key": body.get("idempotency_key"), "h": digest, "payload": json.dumps(body.get("payload", {}))}); await db.commit(); return dict(row.mappings().one())

@router.post("/deliveries/{delivery_id}/attempt")
async def attempt(delivery_id: str, identity: Identity = Depends(get_identity), db: AsyncSession = Depends(get_db)):
    row = (await db.execute(text("SELECT * FROM observability_provider_deliveries WHERE id=:id AND tenant_id=:t AND status IN ('queued','retrying') FOR UPDATE"), {"id": delivery_id, "t": identity.tenant_id})).mappings().first()
    if not row: raise HTTPException(404, "delivery_not_dispatchable")
    permitted(identity, "acknowledge", str(row["project_id"]))
    try:
        receipt = await dispatch(dict(row)); await db.execute(text("UPDATE observability_provider_deliveries SET status='confirmed',receipt=CAST(:r AS jsonb),attempts=attempts+1,updated_at=NOW() WHERE id=:id"), {"r": json.dumps(receipt), "id": delivery_id}); await db.commit(); return {"status": "confirmed", "receipt": receipt}
    except Exception as exc:
        await db.execute(text("UPDATE observability_provider_deliveries SET attempts=attempts+1,status=CASE WHEN attempts+1>=max_attempts THEN 'dead_letter' ELSE 'retrying' END,next_attempt_at=NOW()+(POWER(2,LEAST(attempts,8))||' seconds')::interval,last_error=:e,updated_at=NOW() WHERE id=:id"), {"e": str(exc), "id": delivery_id}); await db.commit(); raise HTTPException(503, "provider_delivery_failed") from exc
