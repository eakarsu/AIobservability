import hashlib
import hmac
import json
import time
import base64
from dataclasses import dataclass
from fastapi import Header, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from app.core.database import get_db
from app.config import settings
from app.core.passwords import hash_password, verify_password
from app.models.projects import ApiKey, Project

@dataclass(frozen=True)
class Identity:
    key_id: str
    tenant_id: str
    project_id: str
    role: str
    retention_days: int
    def as_policy(self): return {"tenant_id": self.tenant_id, "project_ids": [self.project_id], "role": self.role}

def hash_api_key(key: str) -> str: return hashlib.sha256(key.encode()).hexdigest()

def _encode(value: bytes) -> str: return base64.urlsafe_b64encode(value).rstrip(b"=").decode()
def _decode(value: str) -> bytes: return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))

def create_session_token(identity: Identity, subject: str, ttl_seconds: int = 3600) -> str:
    payload = {"sub": subject, "tenant_id": identity.tenant_id, "project_id": identity.project_id,
               "role": identity.role, "iat": int(time.time()), "exp": int(time.time()) + ttl_seconds}
    encoded = _encode(json.dumps(payload, separators=(",", ":"), sort_keys=True).encode())
    signature = _encode(hmac.new(settings.secret_key.encode(), encoded.encode(), hashlib.sha256).digest())
    return f"obs1.{encoded}.{signature}"

def verify_session_token(token: str) -> dict:
    try:
        version, encoded, signature = token.split(".", 2)
        expected = _encode(hmac.new(settings.secret_key.encode(), encoded.encode(), hashlib.sha256).digest())
        if version != "obs1" or not hmac.compare_digest(signature, expected): raise ValueError("signature")
        payload = json.loads(_decode(encoded))
        if int(payload["exp"]) <= int(time.time()): raise ValueError("expired")
        return payload
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise HTTPException(401, "Invalid bearer token") from exc

async def get_identity(x_api_key: str | None = Header(None, alias="X-API-Key"), authorization: str | None = Header(None), db: AsyncSession = Depends(get_db)) -> Identity:
    if authorization and authorization.lower().startswith("bearer "):
        claims = verify_session_token(authorization[7:].strip())
        row = (await db.execute(text("""SELECT u.id,p.id AS project_id,up.role,p.tenant_id,p.retention_days
          FROM observability_users u JOIN observability_user_projects up ON up.user_id=u.id AND up.status='active'
          JOIN projects p ON p.id=up.project_id AND p.is_active=TRUE
          WHERE u.id=:user AND u.status='active' AND p.id=:project AND p.tenant_id=:tenant"""),
          {"user": claims.get("sub"), "project": claims.get("project_id"), "tenant": claims.get("tenant_id")})).one_or_none()
        if not row: raise HTTPException(401, "Session identity is no longer active")
        return Identity(str(row.id), row.tenant_id, str(row.project_id), row.role, row.retention_days)
    if not x_api_key: raise HTTPException(401, "X-API-Key or bearer token is required")
    row = (await db.execute(select(ApiKey.id, ApiKey.project_id, ApiKey.role, Project.tenant_id, Project.retention_days).join(Project, Project.id == ApiKey.project_id).where(ApiKey.key_hash == hash_api_key(x_api_key), ApiKey.is_active.is_(True), Project.is_active.is_(True)))).one_or_none()
    if not row: raise HTTPException(401, "Invalid API key")
    if not row.tenant_id: raise HTTPException(403, "API key project is not assigned to a tenant")
    return Identity(str(row.id), row.tenant_id, str(row.project_id), row.role, row.retention_days)

async def get_project_id(identity: Identity = Depends(get_identity)) -> str: return identity.project_id
