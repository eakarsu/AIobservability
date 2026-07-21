import unittest

from app.domain.observability import (
    PolicyError, authorize, delivery_receipt, ingestion_decision, payload_hash,
    transition_incident, validate_envelope, validate_eval_run,
)


class ObservabilityDomainTests(unittest.TestCase):
    def envelope(self):
        return {"tenant_id": "t1", "project_id": "p1", "event_id": "e1", "trace_id": "tr1", "span_id": "s1", "kind": "tool_call", "schema_version": 1, "sequence": 0, "payload": {"token": "bad", "result": "ok"}}

    def test_envelope_redacts_and_hashes(self):
        value = validate_envelope(self.envelope())
        self.assertEqual(value["payload"]["token"], "[REDACTED]")
        self.assertEqual(len(value["payload_hash"]), 64)

    def test_envelope_rejects_bad_sequence(self):
        value = self.envelope(); value["sequence"] = -1
        with self.assertRaisesRegex(PolicyError, "invalid_sequence"): validate_envelope(value)

    def test_tenant_and_role_scope(self):
        authorize({"tenant_id": "t1", "role": "viewer", "project_ids": ["p1"]}, "t1", "read", "p1")
        with self.assertRaisesRegex(PolicyError, "tenant_scope_denied"): authorize({"tenant_id": "t2", "role": "admin"}, "t1", "read")

    def test_eval_is_reproducible_and_fails_threshold(self):
        result = validate_eval_run({"project_id": "p", "dataset_id": "d", "dataset_version": "1", "model_version": "m", "prompt_version": "p", "evaluator_version": "e", "thresholds": {"faithfulness": .9}, "metrics": {"faithfulness": .8}})
        self.assertFalse(result["accepted"]); self.assertEqual(result["failures"], ["faithfulness"])

    def test_eval_fails_closed_on_missing_metric(self):
        with self.assertRaisesRegex(PolicyError, "complete_numeric_evaluation_required"):
            validate_eval_run({"project_id": "p", "dataset_id": "d", "dataset_version": "1", "model_version": "m", "prompt_version": "p", "evaluator_version": "e", "thresholds": {"faithfulness": .9}, "metrics": {}})

    def test_backpressure_is_explicit(self):
        self.assertFalse(ingestion_decision(100, 100, 20)["accepted"])
        self.assertTrue(ingestion_decision(50, 100, 0)["accepted"])

    def test_incident_needs_owner_and_valid_transition(self):
        with self.assertRaisesRegex(PolicyError, "incident_owner_required"): transition_incident("open", "acknowledged", "operator")
        self.assertEqual(transition_incident("open", "acknowledged", "operator", "u1")["status"], "acknowledged")

    def test_provider_receipt_is_payload_bound(self):
        body = {"trace": "x"}
        receipt = delivery_receipt("collector", body, "i1", {"provider_request_id": "r1", "payload_hash": payload_hash(body)})
        self.assertEqual(receipt["idempotency_key"], "i1")


if __name__ == "__main__":
    unittest.main()
