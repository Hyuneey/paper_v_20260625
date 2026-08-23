from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/remediate_task039e3_r2r_d2_v2_r5_execution_accounting_field_r1.py"
SPEC = importlib.util.spec_from_file_location("accounting_r1_independent_subject", SCRIPT)
assert SPEC and SPEC.loader
subject = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = subject
SPEC.loader.exec_module(subject)


class AccountingFieldRemediationIndependentTests(unittest.TestCase):
    def test_exact_mapping_is_not_permissive_aliasing(self) -> None:
        self.assertEqual(set(subject.R5_EXPECTED_TO_CANONICAL.values()).__len__(),
                         len(subject.R5_EXPECTED_TO_CANONICAL))
        self.assertEqual(sum(k != v for k, v in subject.R5_EXPECTED_TO_CANONICAL.items()), 1)
        self.assertNotIn("d1_metric_reads", subject.CORE_EXPECTED)

    def test_snapshot_requirement_contains_post_oracle_gates(self) -> None:
        self.assertIn("leakage_audit_completed", subject.REQUIRED_R5_SNAPSHOT_FIELDS)
        self.assertIn("report_schema_validation_completed", subject.REQUIRED_R5_SNAPSHOT_FIELDS)
        self.assertIn("v2_attack_event_recall", subject.REQUIRED_R5_SNAPSHOT_FIELDS)

    def test_unknown_and_duplicate_semantic_mapping_rejected_by_contract(self) -> None:
        original = dict(subject.R5_EXPECTED_TO_CANONICAL)
        try:
            subject.R5_EXPECTED_TO_CANONICAL["forged"] = "missing"
            with self.assertRaises(subject.AccountingRemediationError):
                from test_task039e3_r2r_d2_v2_r5_execution_accounting_field_remediation_r1 import synthetic_accounting, producer_source
                document = synthetic_accounting()
                subject.validate_accounting(document, producer_source(), str(document["artifact_hash"]))
        finally:
            subject.R5_EXPECTED_TO_CANONICAL.clear(); subject.R5_EXPECTED_TO_CANONICAL.update(original)

    def test_no_scientific_or_remote_operations(self) -> None:
        source = SCRIPT.read_text(encoding="utf-8")
        for token in ("csv", "pandas", "numpy", "requests", "urllib", "git push", "execute_authorized"):
            self.assertNotIn(token, source)

    def test_blocker_is_fail_closed(self) -> None:
        self.assertEqual(subject.BLOCKER_CODE,
                         "D2_V2_ACCOUNTING_REMEDIATION_R1_COMPLETION_EVIDENCE_REJECTED")
        self.assertIn("SNAPSHOT_INCOMPLETE", subject.ROOT_CAUSE)

    def test_adversarial_contract_rejects_every_case(self) -> None:
        attacks, accepted = subject.adversarial_contract()
        self.assertGreaterEqual(attacks, 17)
        self.assertEqual(accepted, 0)


if __name__ == "__main__":
    unittest.main()
