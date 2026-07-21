"""Provision one explicitly acknowledged dashboard administrator."""
import os
import sys
import uuid
from pathlib import Path
import psycopg2

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.core.passwords import hash_password

if os.environ.get("BOOTSTRAP_ACKNOWLEDGEMENT") != "create-initial-admin":
    raise SystemExit("BOOTSTRAP_ACKNOWLEDGEMENT=create-initial-admin is required")
email = (os.environ.get("PROVISION_ADMIN_EMAIL") or os.environ.get("ADMIN_EMAIL") or "").strip().lower()
password = os.environ.get("PROVISION_ADMIN_PASSWORD") or os.environ.get("ADMIN_PASSWORD") or ""
tenant_id = os.environ.get("GOVERNANCE_TENANT_ID") or ""
project_name = os.environ.get("PROVISION_COMPANY_NAME") or "Runtime Acceptance Observability"
if not email or len(password) < 12 or not tenant_id:
    raise SystemExit("Admin email, password of at least 12 characters, and tenant id are required")
url = os.environ.get("SYNC_DATABASE_URL") or os.environ.get("DATABASE_URL")
if not url: raise SystemExit("SYNC_DATABASE_URL is required")

with psycopg2.connect(url) as connection:
    with connection.cursor() as cursor:
        cursor.execute("SELECT id FROM projects WHERE tenant_id=%s AND name=%s", (tenant_id, project_name))
        row = cursor.fetchone()
        project_id = str(row[0]) if row else str(uuid.uuid4())
        if not row:
            cursor.execute("INSERT INTO projects(id,name,tenant_id,retention_days,is_active) VALUES(%s,%s,%s,30,TRUE)", (project_id, project_name, tenant_id))
        cursor.execute("SELECT id FROM observability_users WHERE lower(email)=lower(%s)", (email,))
        row = cursor.fetchone()
        user_id = str(row[0]) if row else str(uuid.uuid4())
        password_hash = hash_password(password)
        if row:
            cursor.execute("UPDATE observability_users SET password_hash=%s,status='active' WHERE id=%s", (password_hash, user_id))
        else:
            cursor.execute("INSERT INTO observability_users(id,email,password_hash,status) VALUES(%s,%s,%s,'active')", (user_id, email, password_hash))
        cursor.execute("""INSERT INTO observability_user_projects(user_id,project_id,role,status) VALUES(%s,%s,'admin','active')
          ON CONFLICT(user_id,project_id) DO UPDATE SET role='admin',status='active'""", (user_id, project_id))
print(f"Provisioned observability administrator for {email}")
