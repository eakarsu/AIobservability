from fastapi import APIRouter, Body, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import Identity, create_session_token, get_identity, verify_password

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/login")
async def login(body: dict = Body(...), db: AsyncSession = Depends(get_db)):
    email = str(body.get("email") or "").strip().lower()
    password = str(body.get("password") or "")
    if not email or not password: raise HTTPException(400, "email_and_password_required")
    row = (await db.execute(text("""SELECT u.id,u.email,u.password_hash,p.id AS project_id,p.tenant_id,p.name AS project_name,
      p.retention_days,up.role FROM observability_users u
      JOIN observability_user_projects up ON up.user_id=u.id AND up.status='active'
      JOIN projects p ON p.id=up.project_id AND p.is_active=TRUE
      WHERE lower(u.email)=:email AND u.status='active' ORDER BY up.created_at LIMIT 1"""), {"email": email})).mappings().first()
    if not row or not verify_password(password, row["password_hash"]): raise HTTPException(401, "invalid_credentials")
    identity = Identity(str(row["id"]), row["tenant_id"], str(row["project_id"]), row["role"], row["retention_days"])
    token = create_session_token(identity, str(row["id"]))
    return {"token": token, "user": {"id": str(row["id"]), "email": row["email"], "role": row["role"],
      "tenantId": row["tenant_id"], "projectId": str(row["project_id"]), "projectName": row["project_name"]}}

@router.get("/me")
async def me(identity: Identity = Depends(get_identity), db: AsyncSession = Depends(get_db)):
    row = (await db.execute(text("""SELECT u.id,u.email,p.name AS project_name FROM observability_users u
      JOIN observability_user_projects up ON up.user_id=u.id AND up.project_id=:project AND up.status='active'
      JOIN projects p ON p.id=up.project_id AND p.tenant_id=:tenant AND p.is_active=TRUE
      WHERE u.id=:user AND u.status='active'"""), {"user": identity.key_id, "project": identity.project_id, "tenant": identity.tenant_id})).mappings().first()
    if not row: raise HTTPException(401, "session_not_found")
    return {"user": {"id": str(row["id"]), "email": row["email"], "role": identity.role,
      "tenantId": identity.tenant_id, "projectId": identity.project_id, "projectName": row["project_name"]}}
