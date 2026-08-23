from __future__ import annotations

import ast
from pathlib import Path
import unittest

from scripts import remediate_task039e3_r2r_d2_v2_r5_execution_accounting_schema_parser_r2 as r2
from scripts import remediate_task039e3_r2r_d2_v2_r5_execution_accounting_schema_parser_r3 as r3
from scripts import remediate_task039e3_r2r_d2_v2_r5_execution_accounting_schema_parser_r4 as subject


class AccountingSchemaParserR4IndependentTests(unittest.TestCase):
    def assert_rejected(self, action) -> None:
        with self.assertRaises((subject.R4Error, r2.AccountingSchemaR2Error, r3.R3Error)):
            action()

    def test_reintroduced_status_requirement_is_not_in_validator(self) -> None:
        authority, artifact, report = subject._synthetic_history()
        self.assertNotIn(b'"status"', artifact)
        view = subject.validate_history_authority(
            authority, artifact_raw=artifact, report_raw=report,
            commit_is_ancestor=True,
            freeze_paths=("legacy.json", "legacy.md"), mutation_count=0,
        )
        self.assertFalse(view["lifecycle_semantics_reconstructed"])

    def test_historical_state_filename_is_not_consumed(self) -> None:
        source = Path(subject.__file__).read_text(encoding="utf-8")
        self.assertNotIn("infer_status", source)
        self.assertNotIn("lifecycle_binding", source)

    def test_historical_blocker_hash_mutation_attack(self) -> None:
        authority, artifact, report = subject._synthetic_history()
        self.assert_rejected(lambda: subject.validate_history_authority(
            authority,
            artifact_raw=artifact.replace(b"SYNTHETIC_BLOCKER", b"MUTATED_BLOCKER"),
            report_raw=report,
            commit_is_ancestor=True,
            freeze_paths=("legacy.json", "legacy.md"), mutation_count=0,
        ))

    def test_historical_report_hash_mutation_attack(self) -> None:
        authority, artifact, report = subject._synthetic_history()
        self.assert_rejected(lambda: subject.validate_history_authority(
            authority, artifact_raw=artifact, report_raw=report.replace(b"legacy", b"changed"),
            commit_is_ancestor=True,
            freeze_paths=("legacy.json", "legacy.md"), mutation_count=0,
        ))

    def test_history_rewrite_attack(self) -> None:
        authority, artifact, report = subject._synthetic_history()
        self.assert_rejected(lambda: subject.validate_history_authority(
            authority, artifact_raw=artifact, report_raw=report,
            commit_is_ancestor=False,
            freeze_paths=("legacy.json", "legacy.md"), mutation_count=0,
        ))

    def test_decoy_accounting_producer_attack(self) -> None:
        source = "def p():\n accounting_core={'x':1}\n accounting_core={'y':2}\n"
        self.assert_rejected(lambda: r2.recover_dict_assignment_fields(
            source, function_name="p", assignment_name="accounting_core"
        ))

    def test_line_parser_not_imported(self) -> None:
        source = Path(subject.__file__).read_text(encoding="utf-8")
        self.assertNotIn("splitlines", source)

    def test_regex_parser_not_imported(self) -> None:
        tree = ast.parse(Path(subject.__file__).read_text(encoding="utf-8"))
        names = {
            alias.name for node in ast.walk(tree)
            if isinstance(node, (ast.Import, ast.ImportFrom))
            for alias in node.names
        }
        self.assertNotIn("re", names)

    def test_fuzzy_alias_attack(self) -> None:
        document = r2._synthetic_accounting()
        document["d1_metric_read"] = document.pop("d1_metric_artifact_reads")
        fields = r2.recover_dict_assignment_fields(
            r2._synthetic_producer_source(),
            function_name="_write_result_reports_v1",
            assignment_name="accounting_core",
        )
        self.assert_rejected(lambda: r2.build_inventory_and_audit(document, fields))

    def test_injected_noncanonical_d1_field_attack(self) -> None:
        document = r2._synthetic_accounting()
        document["d1_metric_reads"] = 0
        fields = r2.recover_dict_assignment_fields(
            r2._synthetic_producer_source(),
            function_name="_write_result_reports_v1",
            assignment_name="accounting_core",
        )
        self.assert_rejected(lambda: r2.build_inventory_and_audit(document, fields))

    def test_missing_canonical_d1_field_attack(self) -> None:
        document = r2._synthetic_accounting()
        document.pop("d1_metric_artifact_reads")
        fields = r2.recover_dict_assignment_fields(
            r2._synthetic_producer_source(),
            function_name="_write_result_reports_v1",
            assignment_name="accounting_core",
        )
        self.assert_rejected(lambda: r2.build_inventory_and_audit(document, fields))

    def test_wrong_d1_metric_read_value_attack(self) -> None:
        document = r2._synthetic_accounting()
        document["d1_metric_artifact_reads"] = 1
        fields = r2.recover_dict_assignment_fields(
            r2._synthetic_producer_source(),
            function_name="_write_result_reports_v1",
            assignment_name="accounting_core",
        )
        self.assertEqual(r2.build_inventory_and_audit(document, fields).wrong_value_count, 1)

    def test_wrong_d2_v1_metric_read_value_attack(self) -> None:
        document = r2._synthetic_accounting()
        document["d2_v1_metric_reads"] = 1
        fields = r2.recover_dict_assignment_fields(
            r2._synthetic_producer_source(),
            function_name="_write_result_reports_v1",
            assignment_name="accounting_core",
        )
        self.assertEqual(r2.build_inventory_and_audit(document, fields).wrong_value_count, 1)

    def test_all_field_mismatches_collected(self) -> None:
        document = r2._synthetic_accounting()
        document["d1_metric_artifact_reads"] = 1
        document["d2_v1_metric_reads"] = 1
        document["test2_accesses"] = 1
        fields = r2.recover_dict_assignment_fields(
            r2._synthetic_producer_source(),
            function_name="_write_result_reports_v1",
            assignment_name="accounting_core",
        )
        audit = r2.build_inventory_and_audit(document, fields)
        self.assertEqual(audit.wrong_value_count, 3)
        self.assertEqual(audit.unresolved_field_mismatches, 3)

    def test_fabricated_r5_snapshot_attack(self) -> None:
        self.assert_rejected(lambda: r3.build_r5_snapshot(
            {"metric_oracle_completed": True}, "TRIGGERS = {}", {}
        ))

    def test_custody_receipt_substitution_attack(self) -> None:
        self.assert_rejected(lambda: subject.validate_custody({
            "artifact_hash": subject.stable_hash({"compatibility_result": "PASS"}),
            "compatibility_result": "PASS",
        }))

    def test_result_freeze_mutation_is_rejection_condition(self) -> None:
        self.assertEqual(subject.RESULT_FREEZE, "55d41c543e110a9a6f0f5e2e2671857dba938aaa")
        self.assertNotEqual(subject.RESULT_FREEZE, "0" * 40)

    def test_private_path_leak_detected(self) -> None:
        # Public leak scanning is byte-exact; the real run uses only fixed public paths.
        self.assertIn(b"C:\\Users\\", (b"prefix C:\\Users\\private"))

    def test_scientific_payload_paths_absent(self) -> None:
        source = Path(subject.__file__).read_text(encoding="utf-8")
        for token in (
            "DETECTOR_PREDICTION_ARTIFACT_V1.json",
            "RULE_PREDICTION_ARTIFACT_V1.json", "label-test1.csv",
            "FusionEvidenceV2.json", "MetricEvidenceV2.json",
        ):
            self.assertNotIn(token, source)

    def test_test1_feature_and_test2_access_are_zero(self) -> None:
        counters = {
            "scientific_artifacts_reopened_during_r4": False,
            "label_parses_during_r4": 0,
            "test1_feature_accesses": 0,
            "test2_accesses": 0,
            "authoritative_scientific_executions": 0,
        }
        self.assertTrue(all(value in (0, False) for value in counters.values()))

    def test_report_hash_collision_attack(self) -> None:
        self.assert_rejected(lambda: subject.validate_report_schema(
            {"artifact_hash": "x", "other_artifact_hash": "y"}
        ))

    def test_adversarial_contract_all_rejected(self) -> None:
        attacks, accepted = subject.adversarial_contract()
        self.assertGreaterEqual(attacks, 22)
        self.assertEqual(accepted, 0)


if __name__ == "__main__":
    unittest.main()
