from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import unittest

from scripts import audit_task039e3_r2r_d0_result_integrity_report_hash_remediation_r1 as audit


class TestD0ResultIntegrityReportHashRemediationR1(unittest.TestCase):
    def test_canonical_report_hash_scheme_and_body_hash(self) -> None:
        root = Path(__file__).parents[1]
        body = audit.historical_report_body_v1(root)
        self.assertEqual(audit.REPORT_HASH_SCHEME, "MARKDOWN_BODY_SHA256_BEFORE_INTEGRITY_FOOTER_V1")
        self.assertEqual(sha256(body).hexdigest(), audit.EXPECTED_REPORT_SELF_HASH)

    def test_corrected_lineage_values_accept_only_direct_parent_and_base(self) -> None:
        audit.validate_corrected_lineage_values_v1(
            True, audit.HISTORICAL_BLOCKER_COMMIT, audit.CORRECTED_REMEDIATION_BASE
        )
        for values in (
            (False, audit.HISTORICAL_BLOCKER_COMMIT, audit.CORRECTED_REMEDIATION_BASE),
            (True, audit.CORRECTED_REMEDIATION_BASE, audit.CORRECTED_REMEDIATION_BASE),
            (True, audit.HISTORICAL_BLOCKER_COMMIT, "0" * 40),
        ):
            with self.assertRaises(audit.ReportHashRemediationError):
                audit.validate_corrected_lineage_values_v1(*values)

    def test_self_hash_rejects_mutation(self) -> None:
        document = audit.self_hashed_v1({"artifact_type": "synthetic", "value": 1})
        audit.validate_self_hash_v1(document)
        document["value"] = 2
        with self.assertRaises(audit.ReportHashRemediationError):
            audit.validate_self_hash_v1(document)

    def test_builders_form_acyclic_deterministic_dag(self) -> None:
        report_hash = audit.EXPECTED_REPORT_SELF_HASH
        readiness = audit.build_readiness_v1(report_hash)
        bundle = audit.build_bundle_v1(report_hash, readiness["artifact_hash"])
        receipt = audit.build_receipt_v1(
            report_hash, readiness["artifact_hash"], bundle["artifact_hash"]
        )
        self.assertNotIn("r1_bundle_hash", readiness)
        self.assertNotIn("r1_receipt_hash", readiness)
        self.assertNotIn("r1_receipt_hash", bundle)
        self.assertNotIn("full_markdown_hash", bundle)
        self.assertNotIn("full_markdown_hash", receipt)

    def test_synthetic_footer_and_documents_validate(self) -> None:
        body = b"synthetic report\n"
        report_hash = sha256(body).hexdigest()
        readiness = audit.build_readiness_v1(report_hash)
        bundle = audit.build_bundle_v1(report_hash, readiness["artifact_hash"])
        receipt = audit.build_receipt_v1(
            report_hash, readiness["artifact_hash"], bundle["artifact_hash"]
        )
        report = audit.build_remediation_report_v1(
            report_hash,
            readiness["artifact_hash"],
            bundle["artifact_hash"],
            receipt["artifact_hash"],
        )
        patched = body + audit.footer_bytes_v1(
            report_hash, bundle["artifact_hash"], receipt["artifact_hash"]
        )
        outcome = audit.validate_provenance_v1(
            patched, body, readiness, bundle, receipt, report
        )
        self.assertTrue(outcome["markdown_body_byte_identical"])
        self.assertEqual(outcome["integrity_footer_count"], 1)

    def test_historical_blocker_is_reproduced(self) -> None:
        outcome = audit.reproduce_historical_blocker_v1(Path(__file__).parents[1])
        self.assertTrue(outcome["report_self_hash_missing"])
        self.assertTrue(outcome["bundle_binding_missing"])
        self.assertTrue(outcome["receipt_binding_missing"])
        self.assertEqual(outcome["blocker_code"], audit.HISTORICAL_BLOCKER_CODE)

    def test_frozen_public_artifacts_and_blocker_validate(self) -> None:
        outcome = audit.validate_frozen_public_artifacts_v1(Path(__file__).parents[1])
        self.assertEqual(outcome["scientific_audit_artifacts_unchanged_count"], 8)
        self.assertEqual(outcome["scientific_audit_artifact_mutations"], 0)
        self.assertTrue(outcome["historical_blocker_artifact_hash_match"])

    def test_strict_json_rejects_duplicate_members(self) -> None:
        with self.assertRaises(audit.ReportHashRemediationError):
            audit.strict_json_v1(b'{"a":1,"a":2}')

    def test_no_scientific_or_private_access_strings(self) -> None:
        source = (
            Path(__file__).parents[1]
            / "scripts/audit_task039e3_r2r_d0_result_integrity_report_hash_remediation_r1.py"
        ).read_text(encoding="utf-8")
        forbidden = (
            "HAI_DATA_ROOT",
            ".env.custody.local",
            "hai-test1.csv",
            "label-test1.csv",
            "hai-test2",
            "label-test2",
            "numpy",
            "pandas",
            "execute_authorized_d0_inner_v1(",
        )
        for token in forbidden:
            self.assertNotIn(token, source)

    def test_remediation_report_counters_are_all_zero(self) -> None:
        readiness = audit.build_readiness_v1(audit.EXPECTED_REPORT_SELF_HASH)
        bundle = audit.build_bundle_v1(
            audit.EXPECTED_REPORT_SELF_HASH, readiness["artifact_hash"]
        )
        receipt = audit.build_receipt_v1(
            audit.EXPECTED_REPORT_SELF_HASH,
            readiness["artifact_hash"],
            bundle["artifact_hash"],
        )
        report = audit.build_remediation_report_v1(
            audit.EXPECTED_REPORT_SELF_HASH,
            readiness["artifact_hash"],
            bundle["artifact_hash"],
            receipt["artifact_hash"],
        )
        for key in (
            "scientific_test1_feature_parses",
            "scientific_score_recomputations",
            "scientific_label_parses",
            "scientific_metric_recomputations",
            "authoritative_D0_executions",
            "D0_reruns",
            "D1_content_reads",
            "D2_executions",
            "test2_accesses",
        ):
            self.assertEqual(report[key], 0)


if __name__ == "__main__":
    unittest.main()
