import pathlib
import time
import unittest
from app.domain.observability import validate_envelope

ROOT = pathlib.Path(__file__).resolve().parents[2]

class ArchitectureContracts(unittest.TestCase):
    def test_startup_is_schema_read_only(self):
        source = (ROOT / "backend/app/main.py").read_text()
        self.assertNotIn("create_all", source)
        self.assertIn("to_regclass", source)

    def test_delivery_and_audit_contracts_are_durable(self):
        sql = (ROOT / "backend/migrations/001_authoritative_observability.sql").read_text()
        for token in ("dead_letter", "idempotency_key", "payload_hash", "append-only", "expires_at"):
            self.assertIn(token, sql)

    def test_envelope_validation_load_budget(self):
        start = time.perf_counter()
        for index in range(10_000):
            validate_envelope({"tenant_id":"t","project_id":"p","event_id":str(index),"trace_id":"tr","span_id":str(index),"kind":"trace","schema_version":1,"sequence":index,"payload":{"value":index}})
        self.assertLess(time.perf_counter() - start, 5.0)

    def test_delivery_attempts_reapply_project_scope(self):
        source = (ROOT / "backend/app/api/v1/authoritative.py").read_text()
        self.assertIn('permitted(identity, "acknowledge", str(incident.project_id))', source)
        self.assertIn('permitted(identity, "acknowledge", str(row["project_id"]))', source)
