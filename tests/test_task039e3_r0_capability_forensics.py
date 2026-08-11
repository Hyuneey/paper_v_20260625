from __future__ import annotations

import json
from pathlib import Path
import tempfile
from types import MappingProxyType
import unittest

from paperworks.v6.task039e3_r0_capability_forensics_v1 import (
    EXACT_MODEL,
    TASK039E3R0ForensicError,
    audit_private_custody_v1,
    classify_historical_checker_subcondition_v1,
    frozen_checker_outcome_v1,
    reconcile_public_capability_v1,
    reproduce_shallow_serialization_defect_v1,
    scan_public_text_v1,
    stable_hash_v1,
    verify_self_hash_v1,
    with_self_hash_v1,
)


class CapabilityForensicUnitTests(unittest.TestCase):
    def test_offline_oracle_matches_exact_commit_a_checker(self) -> None:
        from paperworks.v6.task039e3_execution_prep_v1 import (
            MockProviderResponseV1,
            parse_capability_response_v1,
        )

        for snapshot, structured in (
            (EXACT_MODEL, True),
            ("other", True),
            (EXACT_MODEL, False),
            ("other", False),
        ):
            response = MockProviderResponseV1(
                response_present=True,
                outcome="successful_response",
                status_code=200,
                model=EXACT_MODEL,
                content=json.dumps(
                    {
                        "model_snapshot": snapshot,
                        "structured_output_supported": structured,
                    }
                ),
                refusal=False,
                finish_reason="stop",
                response_id="SYNTHETIC_R0",
            )
            self.assertEqual(
                parse_capability_response_v1(response).status,
                frozen_checker_outcome_v1(snapshot, structured),
            )

    def test_historical_checker_decision_table_and_missing_payload(self) -> None:
        self.assertEqual(frozen_checker_outcome_v1(EXACT_MODEL, True), "pass")
        self.assertEqual(frozen_checker_outcome_v1("other", True), "block_snapshot")
        self.assertEqual(frozen_checker_outcome_v1(EXACT_MODEL, False), "block_snapshot")
        self.assertEqual(frozen_checker_outcome_v1("other", False), "block_snapshot")
        self.assertEqual(
            classify_historical_checker_subcondition_v1({"parse_status": "block_snapshot"}),
            "unable_to_determine",
        )
        self.assertEqual(
            classify_historical_checker_subcondition_v1(
                {"parsed_capability_payload": {"model_snapshot": "other", "structured_output_supported": True}}
            ),
            "synthetic_snapshot_self_report_mismatch",
        )
        self.assertEqual(
            classify_historical_checker_subcondition_v1(
                {"parsed_capability_payload": {"model_snapshot": EXACT_MODEL, "structured_output_supported": False}}
            ),
            "synthetic_structured_support_self_report_false",
        )

    def test_self_hash_and_public_leak_scan(self) -> None:
        artifact = with_self_hash_v1({"artifact_type": "synthetic_audit_fixture", "safe": True})
        self.assertEqual(verify_self_hash_v1(artifact), artifact["artifact_hash"])
        tampered = dict(artifact, safe=False)
        with self.assertRaises(TASK039E3R0ForensicError):
            verify_self_hash_v1(tampered)
        self.assertEqual(scan_public_text_v1('{"safe":true}'), ())
        self.assertIn("bearer ", scan_public_text_v1("Bearer secret"))

    def test_nested_immutable_serialization_defect_reproduces(self) -> None:
        result = reproduce_shallow_serialization_defect_v1()
        self.assertTrue(result["reproduced"])
        self.assertEqual(result["exception_class"], "TypeError")
        self.assertEqual(result["triggering_logical_type"], "mappingproxy")

    def test_actual_historical_public_writer_reproduces_mappingproxy_failure(self) -> None:
        from paperworks.v6.task039e3_scientific_execution_v1 import (
            write_public_artifacts_v1,
        )

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "docs/task_reports").mkdir(parents=True)
            document = {"usage": MappingProxyType({"total_tokens": 101})}
            with self.assertRaisesRegex(
                TypeError, "Object of type mappingproxy is not JSON serializable"
            ):
                write_public_artifacts_v1(root, {"capability": document})
        # The production writer is intentionally not repaired by R0.

    def test_private_custody_hash_chain_and_public_reconciliation(self) -> None:
        fixture_root = Path(__file__).resolve().parents[1]
        public = json.loads(
            (fixture_root / "docs/task_reports/TASK-039E3_CAPABILITY_GATE.json").read_text(encoding="utf-8")
        )
        # Reconstruct the exact single custody record without reading any external root.
        slot = {
            "artifact_type": "scientific_provider_call_slot_v1",
            "relation_schedule_index": None,
            "relation_binding_hash": "187a2cd53811634cfdad0e5c4b26e710b169c08edf7c03a285185a080c90ce91",
            "arm": "CAPABILITY",
            "arm_local_call_number": 1,
            "scientific": False,
            "schedule_hash": "6db63485387924b28e9ce498aae46412a127ba69055a28e72880e1afffa4c4ca",
        }
        content = {
            "sequence_index": 0,
            "previous_record_hash": None,
            "slot": slot,
            "slot_hash": stable_hash_v1(slot),
            "request_hash": "fc35aa1ce3f68eb8635a634bf47050f0ba4cda7caf2caa4e13a947845cdd3138",
            "response_present": True,
            "provider_response_metadata": {
                "outcome": "successful_response",
                "status_code": 200,
                "model": EXACT_MODEL,
                "response_id": "chatcmpl-EBoZnPrUfDXlKbhytq3eLqCXslFAO",
                "finish_reason": "stop",
                "response_hash": "66ec9309faa1499e1150081775582e7c4f08d4dc86b67b734b9faf30f7f7b2f8",
                "token_usage": {"completion_tokens": 27, "prompt_tokens": 74, "total_tokens": 101},
            },
            "transport_attempts": [{
                "attempt_number": 1,
                "outcome": "successful_response",
                "response_present": True,
                "status_code": 200,
                "retry_eligible": False,
                "planned_retry_delay_seconds": None,
            }],
            "parse_status": "block_snapshot",
            "proposal_core_hash": None,
            "terminal_slot_state": "completed_invalid_response",
            "api_key_stored": False,
            "authorization_header_stored": False,
            "chain_of_thought_stored": False,
        }
        record = dict(content, record_hash=stable_hash_v1(content))
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for name in (
                "construction_outcomes.jsonl",
                "direct_number.jsonl",
                "proposals_validity.jsonl",
            ):
                (root / name).write_text("", encoding="utf-8")
            (root / "provider_calls.jsonl").write_text(
                json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n",
                encoding="utf-8",
            )
            audited = audit_private_custody_v1(root)
        self.assertEqual(audited["logical_capability_slots"], 1)
        self.assertEqual(audited["logical_scientific_slots"], 0)
        reconciliation = reconcile_public_capability_v1(record, public)
        self.assertTrue(reconciliation["reconstructible_fields_match"])
        self.assertFalse(reconciliation["exact_full_reconciliation_established"])


if __name__ == "__main__":
    unittest.main()
