from __future__ import annotations

import json
import unittest
from pathlib import Path

from paperworks.profiling.task039d1_execution_optimization_v1 import (
    ABORTED_COMMIT_A1,
    D0_PROTOCOL_BUNDLE_HASH,
    D1_AUTHORIZATION_HASH,
    RECOVERY_STATUS,
    verify_recovery_artifact_v1,
)
from paperworks.v6.schema_registry_v1 import load_v6_schema_registry_v1


ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "docs" / "task_reports"


class TASK039D1RRecoveryReceiptTests(unittest.TestCase):
    def _load(self, name: str) -> dict[str, object]:
        return json.loads((REPORTS / name).read_text(encoding="utf-8"))

    def test_complexity_receipt_is_closed_and_passed(self) -> None:
        receipt = self._load("TASK-039D1R_EXECUTION_COMPLEXITY_RECEIPT.json")
        verify_recovery_artifact_v1(receipt)
        self.assertEqual(receipt["status"], RECOVERY_STATUS)
        self.assertEqual(receipt["original_aborted_commit_a"], ABORTED_COMMIT_A1)
        self.assertEqual(receipt["d0_protocol_bundle_hash"], D0_PROTOCOL_BUNDLE_HASH)
        self.assertEqual(receipt["d1_authorization_hash"], D1_AUTHORIZATION_HASH)
        self.assertFalse(receipt["scientific_formulas_changed"])
        self.assertFalse(receipt["d0_policies_changed"])
        self.assertEqual(receipt["unresolved_execution_complexity_defects"], [])
        self.assertFalse(receipt["hai_values_accessed_during_recovery_implementation"])

    def test_aborted_record_proves_no_reused_scientific_result(self) -> None:
        record = self._load("TASK-039D1_ABORTED_EXECUTION_RECORD.json")
        verify_recovery_artifact_v1(record)
        self.assertEqual(record["original_d1_commit_a"], ABORTED_COMMIT_A1)
        self.assertEqual(record["terminal_status"], "failed_task039d1_scientific_execution")
        self.assertTrue(record["train1_accessed"] and record["train2_accessed"])
        for key in (
            "train3_accessed", "train4_accessed", "test_accessed", "labels_accessed",
            "attacks_accessed", "private_ledgers_produced", "scientific_outcomes_frozen",
            "provenance_joined", "rule_v2_authorized", "task039d2_authorized",
            "aborted_outputs_reused",
        ):
            self.assertFalse(record[key], key)

    def test_recovery_schemas_registered(self) -> None:
        registry = load_v6_schema_registry_v1(repository_root=ROOT)
        self.assertEqual(len(registry.artifact_types), 112)
        self.assertIn("task039d1_execution_complexity_receipt_v1", registry.artifact_types)
        self.assertIn("task039d1_aborted_execution_record_v1", registry.artifact_types)


if __name__ == "__main__":
    unittest.main()
