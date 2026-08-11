from __future__ import annotations

import json
import unittest
from pathlib import Path

from paperworks.v6.schema_registry_v1 import load_v6_schema_registry_v1
from paperworks.v6.task039e1_final_audit_v1 import (
    E1_PRIVATE_LEDGER_HASH,
    MATERIALIZATION_RESULT_HASH,
    PUBLIC_COHORT_HASH,
    READINESS,
    STATUS,
    verify_self_hash_v1,
)


ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "docs/task_reports"


class FinalAuditResultTests(unittest.TestCase):
    def test_passing_audit_is_self_hashed_and_exact(self) -> None:
        audit = json.loads(
            (REPORTS / "TASK-039E1_FINAL_AUDIT.json").read_text(encoding="utf-8")
        )
        self.assertEqual(
            "7eca927e8bfaf123eb19ce828d3bdec6f9724e810e40ec49babdf59d3a7bfd9b",
            verify_self_hash_v1(audit),
        )
        self.assertEqual(STATUS, audit["status"])
        self.assertEqual(READINESS, audit["readiness"])
        self.assertEqual([], audit["findings"]["blocking"])
        self.assertEqual(42, audit["independent_replay"]["private_records_reproduced"])
        self.assertEqual(462, audit["independent_replay"]["numeric_references_reproduced"])

    def test_e2_authorizes_configuration_freeze_only(self) -> None:
        authorization = json.loads(
            (REPORTS / "TASK-039E2_AUTHORIZATION.json").read_text(encoding="utf-8")
        )
        self.assertEqual(
            "5a68559bc0e95c6e92061cbf5762ed3359817537f3cbe0c5ae885774d14250ff",
            verify_self_hash_v1(authorization),
        )
        self.assertEqual(MATERIALIZATION_RESULT_HASH, authorization["e1_materialization_result_hash"])
        self.assertEqual(PUBLIC_COHORT_HASH, authorization["e1_construction_evidence_cohort_hash"])
        self.assertEqual(E1_PRIVATE_LEDGER_HASH, authorization["e1_private_ledger_hash"])
        for field in (
            "provider_model_call_authorized",
            "real_t0_generation_authorized",
            "real_t1_t1b_t2_generation_authorized",
            "direct_number_execution_authorized",
            "rule_v2_authorized",
            "detector_runtime_authorized",
            "hai_test_labels_attacks_authorized",
        ):
            self.assertFalse(authorization[field], field)

    def test_new_artifact_schemas_are_registered(self) -> None:
        registry = load_v6_schema_registry_v1(repository_root=ROOT)
        self.assertIn("task039e1_final_audit_v1", registry.artifact_types)
        self.assertIn("task039e2_authorization_v1", registry.artifact_types)


if __name__ == "__main__":
    unittest.main()
