from __future__ import annotations

import ast
from pathlib import Path
import unittest

from scripts import audit_task039e3_r2r_d0_result_integrity_report_hash_remediation_r1 as audit


class TestD0ResultIntegrityReportHashRemediationR1Independent(unittest.TestCase):
    def test_all_required_mutation_attacks_fail_closed(self) -> None:
        attacks, accepted_invalid = audit.run_adversarial_suite_v1()
        self.assertEqual(attacks, 27)
        self.assertEqual(accepted_invalid, 0)

    def test_validator_is_public_git_and_tracked_document_only(self) -> None:
        path = (
            Path(__file__).parents[1]
            / "scripts/audit_task039e3_r2r_d0_result_integrity_report_hash_remediation_r1.py"
        )
        tree = ast.parse(path.read_text(encoding="utf-8"))
        imports = {
            alias.name
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        }
        imported_from = {
            node.module
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.module is not None
        }
        self.assertFalse({"numpy", "pandas", "csv", "os"}.intersection(imports))
        self.assertFalse(any(name.startswith("paperworks") for name in imported_from))

    def test_validator_has_no_network_or_remote_mutation_command(self) -> None:
        source = (
            Path(__file__).parents[1]
            / "scripts/audit_task039e3_r2r_d0_result_integrity_report_hash_remediation_r1.py"
        ).read_text(encoding="utf-8")
        for token in ("git push", "git fetch", "git pull", "http://", "https://"):
            self.assertNotIn(token, source)

    def test_closed_scientific_hash_set_is_exact(self) -> None:
        self.assertEqual(len(audit.SCIENTIFIC_AUDIT_ARTIFACTS), 8)
        self.assertEqual(
            set(audit.SCIENTIFIC_AUDIT_ARTIFACTS),
            {
                "freeze_audit",
                "score_oracle",
                "prediction_audit",
                "label_independence_audit",
                "metric_oracle",
                "accounting_audit",
                "leakage_audit",
                "independent_audit",
            },
        )

    def test_remediation_artifacts_cannot_bind_full_patched_markdown_hash(self) -> None:
        readiness = audit.build_readiness_v1(audit.EXPECTED_REPORT_SELF_HASH)
        bundle = audit.build_bundle_v1(
            audit.EXPECTED_REPORT_SELF_HASH, readiness["artifact_hash"]
        )
        receipt = audit.build_receipt_v1(
            audit.EXPECTED_REPORT_SELF_HASH,
            readiness["artifact_hash"],
            bundle["artifact_hash"],
        )
        for document in (readiness, bundle, receipt):
            self.assertNotIn("full_markdown_hash", document)
            self.assertNotIn("patched_markdown_hash", document)


if __name__ == "__main__":
    unittest.main()
