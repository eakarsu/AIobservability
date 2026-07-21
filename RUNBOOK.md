# Authoritative observability runbook

1. Install dependencies in `backend/` and copy `.env.example` to `.env`; generate unique database credentials and a 32+ character secret.
2. Run `SYNC_DATABASE_URL=... python3 backend/scripts/migrate.py` as the migration role. Startup is read-only and fails if `observability_events` is absent.
3. Provision a tenant on `projects.tenant_id`, choose retention, and create API keys with the smallest role. Never share a key across tenants.
4. Run `./start.sh backend`. The only production API is `/api/v1/authoritative`; generated gap and direct-model routes are not mounted.
5. Watch queue depth, event ordering conflicts, expired-event volume, evaluation failures, open incidents, and `dead_letter` deliveries. A dead letter is replayed only after the provider fault is fixed and its payload hash is verified.

Telemetry payloads are recursively redacted before storage. Retention is stamped per event. Audit rows are append-only. Provider credentials stay in the secret manager; receipts must echo the payload hash. Restore tests must verify trace ordering, evaluation reproducibility, incident deduplication, and tenant isolation.
