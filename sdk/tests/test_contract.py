import unittest
from aiobserve.types import EventEnvelope, canonical_hash

class ContractTests(unittest.TestCase):
    def test_all_event_kinds_have_payload_bound_envelopes(self):
        for kind in ("trace","prompt","response","tool_call","retrieval","evaluation","cost","feedback"):
            body=EventEnvelope("t","p",kind,{"kind":kind},"tr").to_dict()
            self.assertEqual(body["payload_hash"],canonical_hash(body["payload"]))
    def test_unknown_kind_fails(self):
        with self.assertRaisesRegex(ValueError,"unsupported_event_kind"): EventEnvelope("t","p","bad",{},"tr").to_dict()
