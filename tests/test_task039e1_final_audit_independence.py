from __future__ import annotations

import unittest
from pathlib import Path

from paperworks.v6.task039e1_final_audit_v1 import (
    DATA_ACCESS_AUDIT_HASH,
    EXECUTION_RECEIPT_HASH,
    MATERIALIZATION_RESULT_HASH,
    PUBLIC_COHORT_HASH,
    PUBLIC_MANIFEST_HASH,
    verify_self_hash_v1,
)
import json


ROOT = Path(__file__).resolve().parents[1]


class FinalAuditIndependenceTests(unittest.TestCase):
    def test_oracle_has_no_production_materializer_or_runner_import(self) -> None:
        source = (ROOT / "src/paperworks/v6/task039e1_final_audit_v1.py").read_text(
            encoding="utf-8"
        )
        self.assertNotIn("import paperworks.v6.task039e1_evidence_materialization_v1", source)
        self.assertNotIn("from paperworks.v6.task039e1_evidence_materialization_v1", source)
        self.assertNotIn("resolve_private_numeric_reference_v1", source)
        self.assertNotIn("materialize_from_ledgers_v1", source)

    def test_runner_has_no_hai_or_model_loader(self) -> None:
        source = (ROOT / "scripts/run_task039e1_final_audit.py").read_text(
            encoding="utf-8"
        ).casefold()
        for forbidden in (
            "hai_data_root", "load_authorized_train", "pandas", "read_csv",
            "openai", "anthropic", "provider.call", "materialize_from_ledgers_v1",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, source)

    def test_frozen_public_e1_self_hashes(self) -> None:
        expected = {
            "TASK-039E1_CONSTRUCTION_EVIDENCE_MANIFEST.json": PUBLIC_MANIFEST_HASH,
            "TASK-039E1_CONSTRUCTION_EVIDENCE_COHORT.json": PUBLIC_COHORT_HASH,
            "TASK-039E1_MATERIALIZATION_RESULT.json": MATERIALIZATION_RESULT_HASH,
            "TASK-039E1_DATA_ACCESS_AUDIT.json": DATA_ACCESS_AUDIT_HASH,
            "TASK-039E1_EXECUTION_RECEIPT.json": EXECUTION_RECEIPT_HASH,
        }
        for name, artifact_hash in expected.items():
            document = json.loads(
                (ROOT / "docs/task_reports" / name).read_text(encoding="utf-8")
            )
            with self.subTest(name=name):
                self.assertEqual(artifact_hash, verify_self_hash_v1(document))


if __name__ == "__main__":
    unittest.main()
