from __future__ import annotations

import json
import unittest
from pathlib import Path

from paperworks.v6.common import stable_hash_v1


ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "docs" / "task_reports"


def _load(name: str) -> dict[str, object]:
    return json.loads((REPORTS / name).read_text(encoding="utf-8"))


class Task039E3R1ATimeoutAuthorityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.authority = _load("TASK-039E3_R1A_TIMEOUT_AUTHORITY.json")
        self.audit = _load("TASK-039E3_R1A_DATA_ACCESS_AUDIT.json")
        self.receipt = _load("TASK-039E3_R1A_RECEIPT.json")

    def test_timeout_is_prospective_per_attempt_authority(self) -> None:
        self.assertEqual(self.authority["urlopen_timeout_seconds"], 30.0)
        self.assertIsNone(self.authority["authoritative_e2_timeout_seconds"])
        self.assertEqual(self.authority["timeout_scope"], "each_transport_attempt")
        self.assertIsNone(self.authority["total_logical_request_deadline_seconds"])
        self.assertFalse(self.authority["retroactive_e2_reinterpretation"])
        self.assertFalse(self.authority["e2_timeout_duration_frozen"])
        self.assertTrue(self.authority["e2_timeout_failure_class_frozen"])

    def test_retry_and_probe_limits_are_unchanged(self) -> None:
        self.assertEqual(self.authority["maximum_transport_retries_per_logical_request"], 2)
        self.assertEqual(self.authority["maximum_transport_attempts_per_logical_request"], 3)
        self.assertEqual(self.authority["fixed_retry_wait_seconds"], [2, 4])
        self.assertEqual(self.authority["scientific_generation_retries"], 0)
        self.assertEqual(self.authority["historical_capability_probe_count"], 1)
        self.assertEqual(self.authority["maximum_additional_recovery_probes"], 1)
        self.assertEqual(self.authority["maximum_cumulative_capability_probes"], 2)
        self.assertEqual(self.authority["third_capability_probe"], "prohibited")

    def test_timeout_is_uniform_and_nonadaptive(self) -> None:
        self.assertTrue(self.authority["uniform_across_provider_arms"])
        self.assertFalse(self.authority["arm_specific_timeout"])
        self.assertTrue(self.authority["no_adaptive_timeout"])
        self.assertNotIn("T0", self.authority["provider_request_arms"])

    def test_only_offline_recovery_implementation_is_authorized(self) -> None:
        authority = self.authority["authority"]
        self.assertTrue(authority["recovery_implementation_authorized"])
        for field in (
            "provider_contact_authorized",
            "recovery_probe_authorized",
            "scientific_execution_authorized",
            "rule_v2_authorized",
            "runtime_authority",
            "utility_evaluation_authorized",
            "winner_selected",
        ):
            self.assertFalse(authority[field])

    def test_offline_data_boundary(self) -> None:
        self.assertFalse(self.audit["api_key_accessed"])
        self.assertFalse(self.audit["api_key_presence_checked"])
        self.assertFalse(self.audit["provider_contacted"])
        self.assertFalse(self.audit["capability_probe_executed"])
        self.assertEqual(self.audit["openai_transport_attempts"], 0)
        self.assertEqual(self.audit["scientific_calls"], 0)
        self.assertFalse(self.audit["real_e1_private_evidence_accessed"])
        self.assertFalse(self.audit["historical_e3_private_root_accessed"])

    def test_artifact_self_hashes_and_receipt_bindings(self) -> None:
        for artifact in (self.authority, self.audit, self.receipt):
            expected = artifact["self_hash"]
            payload = {key: value for key, value in artifact.items() if key != "self_hash"}
            self.assertEqual(expected, stable_hash_v1(payload))
        self.assertEqual(self.receipt["timeout_authority_hash"], self.authority["self_hash"])
        self.assertEqual(self.receipt["data_access_audit_hash"], self.audit["self_hash"])
        self.assertEqual(
            self.receipt["next_authorized_task"],
            "TASK-039E3-R1B_RECOVERY_IMPLEMENTATION",
        )


if __name__ == "__main__":
    unittest.main()
