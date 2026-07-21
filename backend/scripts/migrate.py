"""Explicit migration command; application startup never mutates schema."""
from pathlib import Path
import os
import psycopg2

url = os.environ.get("SYNC_DATABASE_URL")
if not url:
    raise SystemExit("SYNC_DATABASE_URL is required")
directory = Path(__file__).resolve().parents[1] / "migrations"
with psycopg2.connect(url) as connection:
    with connection.cursor() as cursor:
        cursor.execute("CREATE TABLE IF NOT EXISTS schema_migrations (name TEXT PRIMARY KEY, applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW())")
        for path in sorted(directory.glob("*.sql")):
            cursor.execute("SELECT 1 FROM schema_migrations WHERE name=%s", (path.name,))
            if cursor.fetchone():
                continue
            sql = path.read_text().strip()
            if sql.startswith("BEGIN;"): sql = sql[len("BEGIN;"):].strip()
            if sql.endswith("COMMIT;"): sql = sql[:-len("COMMIT;")].strip()
            cursor.execute(sql)
            cursor.execute("INSERT INTO schema_migrations(name) VALUES (%s)", (path.name,))
            print(f"applied {path.name}")
