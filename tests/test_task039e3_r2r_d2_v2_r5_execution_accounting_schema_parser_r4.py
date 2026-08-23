from __future__ import annotations

import ast
import json
from pathlib import Path
import unittest

from scripts import remediate_task039e3_r2r_d2_v2_r5_execution_accounting_schema_parser_r2 as r2
from scripts import remediate_task039e3_r2r_d2_v2_r5_execution_accounting_schema_parser_r3 as r3
from scripts import remediate_task039e3_r2r_d2_v2_r5_execution_accounting_schema_parser_r4 as subject


class AccountingSchemaParserR4Tests(unittest.TestCase):
    def test_legacy_lifecycle_is_not_current_gate(self) -> None:
        self.assertEqual(
            subject.POLICY,
            "LEGACY_AUDIT_BLOCKER_LIFECYCLE_RECONSTRUCTION_IS_NOT_A_CURRENT_RESULT_INTEGRITY_PASS_GATE",
        )

    def test_legacy_blocker_without_status_is_preserved(self) -> None:
        authority, artifact, report = subject._synthetic_history()
        view = subject.validate_history_authority(
            authority, artifact_raw=artifact, report_raw=report,
            commit_is_ancestor=True,
            freeze_paths=("legacy.json", "legacy.md"), mutation_count=0,
        )
        self.assertFalse(view["lifecycle_semantics_reconstructed"])
        self.assertNotIn("status", json.loads(artifact))

    def test_mutated_blocker_hash_rejected(self) -> None:
        authority, artifact, report = subject._synthetic_history()
        with self.assertRaises(subject.R4Error):
            subject.validate_history_authority(
                authority, artifact_raw=artifact.replace(b"SYNTHETIC", b"MUTATED"),
                report_raw=report, commit_is_ancestor=True,
                freeze_paths=("legacy.json", "legacy.md"), mutation_count=0,
            )

    def test_missing_freeze_ancestry_rejected(self) -> None:
        authority, artifact, report = subject._synthetic_history()
        with self.assertRaises(subject.R4Error):
            subject.validate_history_authority(
                authority, artifact_raw=artifact, report_raw=report,
                commit_is_ancestor=False,
                freeze_paths=("legacy.json", "legacy.md"), mutation_count=0,
            )

    def test_missing_freeze_path_rejected(self) -> None:
        authority, artifact, report = subject._synthetic_history()
        with self.assertRaises(subject.R4Error):
            subject.validate_history_authority(
                authority, artifact_raw=artifact, report_raw=report,
                commit_is_ancestor=True, freeze_paths=("legacy.json",),
                mutation_count=0,
            )

    def test_post_freeze_mutation_rejected(self) -> None:
        authority, artifact, report = subject._synthetic_history()
        with self.assertRaises(subject.R4Error):
            subject.validate_history_authority(
                authority, artifact_raw=artifact, report_raw=report,
                commit_is_ancestor=True,
                freeze_paths=("legacy.json", "legacy.md"), mutation_count=1,
            )

    def test_duplicate_json_keys_rejected(self) -> None:
        with self.assertRaises(subject.R4Error):
            subject.strict_json(b'{"a":1,"a":2}')

    def test_ast_handles_all_keys_on_same_line(self) -> None:
        source = "def target():\n accounting_core={'a':1,'b':2,'c':3}\n"
        self.assertEqual(
            r2.recover_dict_assignment_fields(
                source, function_name="target", assignment_name="accounting_core"
            ),
            ("a", "b", "c"),
        )

    def test_decoy_producer_is_rejected_as_ambiguous(self) -> None:
        source = "def target():\n accounting_core={'a':1}\n accounting_core={'b':2}\n"
        with self.assertRaises(r2.AccountingSchemaR2Error):
            r2.recover_dict_assignment_fields(
                source, function_name="target", assignment_name="accounting_core"
            )

    def test_actual_producer_is_exact_and_unambiguous(self) -> None:
        source = subject.PRODUCER_PATH.read_bytes().decode("utf-8")
        fields = r2.recover_dict_assignment_fields(
            source, function_name="_write_result_reports_v1",
            assignment_name="accounting_core",
        )
        self.assertEqual(len(fields), 36)

    def test_canonical_d1_metric_field(self) -> None:
        self.assertEqual(r2.CANONICAL_D1_METRIC_FIELD, "d1_metric_artifact_reads")
        self.assertNotIn("d1_metric_reads", r2.CORE_EXPECTED)
        self.assertEqual(r2.CORE_EXPECTED["d1_metric_artifact_reads"], 0)

    def test_canonical_d2_v1_metric_field(self) -> None:
        self.assertEqual(r2.CORE_EXPECTED["d2_v1_metric_reads"], 0)

    def test_noncanonical_d1_field_rejected(self) -> None:
        document = r2._synthetic_accounting()
        document["d1_metric_reads"] = document.pop("d1_metric_artifact_reads")
        with self.assertRaises(r2.AccountingSchemaR2Error):
            r2.build_inventory_and_audit(
                document,
                r2.recover_dict_assignment_fields(
                    r2._synthetic_producer_source(),
                    function_name="_write_result_reports_v1",
                    assignment_name="accounting_core",
                ),
            )

    def test_missing_accounting_field_rejected(self) -> None:
        document = r2._synthetic_accounting()
        document.pop("d2_v1_metric_reads")
        with self.assertRaises(r2.AccountingSchemaR2Error):
            r2.build_inventory_and_audit(
                document,
                r2.recover_dict_assignment_fields(
                    r2._synthetic_producer_source(),
                    function_name="_write_result_reports_v1",
                    assignment_name="accounting_core",
                ),
            )

    def test_wrong_accounting_type_counted(self) -> None:
        document = r2._synthetic_accounting()
        document["d1_metric_artifact_reads"] = False
        audit = r2.build_inventory_and_audit(
            document,
            r2.recover_dict_assignment_fields(
                r2._synthetic_producer_source(),
                function_name="_write_result_reports_v1",
                assignment_name="accounting_core",
            ),
        )
        self.assertEqual(audit.wrong_type_count, 1)

    def test_wrong_accounting_value_counted(self) -> None:
        document = r2._synthetic_accounting()
        document["d2_v1_metric_reads"] = 1
        audit = r2.build_inventory_and_audit(
            document,
            r2.recover_dict_assignment_fields(
                r2._synthetic_producer_source(),
                function_name="_write_result_reports_v1",
                assignment_name="accounting_core",
            ),
        )
        self.assertEqual(audit.wrong_value_count, 1)

    def test_all_28_semantics_audited(self) -> None:
        audit = r2.build_inventory_and_audit(
            r2._synthetic_accounting(),
            r2.recover_dict_assignment_fields(
                r2._synthetic_producer_source(),
                function_name="_write_result_reports_v1",
                assignment_name="accounting_core",
            ),
        )
        self.assertEqual(audit.full_semantic_concepts_required, 28)
        self.assertEqual(audit.exact_name_matches, 27)
        self.assertEqual(audit.schema_proven_name_corrections, 1)
        self.assertEqual(audit.unresolved_field_mismatches, 0)

    def test_incomplete_r5_snapshot_rejected(self) -> None:
        with self.assertRaises(r3.R3Error):
            r3.build_r5_snapshot({"metric_oracle_completed": True}, "", {})

    def test_custody_mismatch_rejected(self) -> None:
        with self.assertRaises(subject.R4Error):
            subject.validate_custody({"artifact_hash": "0" * 64})

    def test_report_hash_collision_rejected(self) -> None:
        with self.assertRaises(subject.R4Error):
            subject.validate_report_schema(
                {"artifact_hash": "x", "referenced_artifact_hash": "y"}
            )

    def test_no_line_or_regex_accounting_parser(self) -> None:
        source = Path(subject.__file__).read_text(encoding="utf-8")
        tree = ast.parse(source)
        imported = {
            alias.name for node in ast.walk(tree)
            if isinstance(node, (ast.Import, ast.ImportFrom))
            for alias in node.names
        }
        self.assertNotIn("re", imported)
        self.assertNotIn("splitlines", source)

    def test_no_historical_lifecycle_reconstruction_call(self) -> None:
        source = Path(subject.__file__).read_text(encoding="utf-8")
        tree = ast.parse(source)
        attributes = {
            node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute)
        }
        self.assertNotIn("lifecycle_binding", attributes)
        self.assertNotIn("build_blocker_view", attributes)

    def test_no_scientific_or_label_paths(self) -> None:
        source = Path(subject.__file__).read_text(encoding="utf-8")
        forbidden = (
            "DETECTOR_PREDICTION_ARTIFACT_V1.json",
            "RULE_PREDICTION_ARTIFACT_V1.json",
            "SOURCE_MAP.json", "NATIVE_HORIZON_MAP.json",
            "FusionEvidenceV2.json", "MetricEvidenceV2.json",
            "label-test1.csv", "test2.csv",
        )
        self.assertTrue(all(token not in source for token in forbidden))

    def test_adversarial_contract_accepts_nothing(self) -> None:
        attacks, accepted = subject.adversarial_contract()
        self.assertGreaterEqual(attacks, 22)
        self.assertEqual(accepted, 0)


if __name__ == "__main__":
    unittest.main()
