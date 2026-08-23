from __future__ import annotations

import ast
import json
from pathlib import Path
import unittest

from scripts import remediate_task039e3_r2r_d2_v2_r5_execution_accounting_schema_parser_r3 as subject
from scripts import remediate_task039e3_r2r_d2_v2_r5_execution_accounting_schema_parser_r2 as r2


class AccountingSchemaParserR3Tests(unittest.TestCase):
    def test_blocker_without_status_accepted_when_schema_excludes_status(self) -> None:
        document = subject._synthetic_blocker(False)
        schema = subject.raw_literal_schema(subject._blocker_raw(document))
        subject.validate_blocker_document(
            document=document, schema_fields=schema, expected_hash=document["artifact_hash"],
            expected_type="SyntheticBlockerV1", expected_task="SYNTHETIC_TASK",
            expected_code="SYNTHETIC_BLOCKER", expected_class="SYNTHETIC_CLASS",
            status_required=False, expected_status=None,
        )
        self.assertNotIn("status", schema)

    def test_required_status_missing_is_rejected(self) -> None:
        document = subject._synthetic_blocker(False)
        schema = subject.raw_literal_schema(subject._blocker_raw(document))
        with self.assertRaises(subject.R3Error):
            subject.validate_blocker_document(
                document=document, schema_fields=schema, expected_hash=document["artifact_hash"],
                expected_type="SyntheticBlockerV1", expected_task="SYNTHETIC_TASK",
                expected_code="SYNTHETIC_BLOCKER", expected_class="SYNTHETIC_CLASS",
                status_required=True, expected_status="blocked_synthetic",
            )

    def test_lifecycle_state_requires_exact_binding(self) -> None:
        text = "| TASK | BLOCK; local | COMMIT | HASH |"
        self.assertTrue(subject.lifecycle_binding(text, "TASK", "COMMIT", "HASH"))
        self.assertFalse(subject.lifecycle_binding(text, "OTHER", "COMMIT", "HASH"))

    def test_filename_only_blocker_inference_rejected(self) -> None:
        self.assertFalse(subject.lifecycle_binding("BLOCKER.json BLOCK;", "TASK", "COMMIT", "HASH"))

    def test_blocker_hash_mismatch_rejected(self) -> None:
        document = subject._synthetic_blocker(False)
        with self.assertRaises(subject.R3Error):
            subject.validate_self_hash(document, "0" * 64)

    def test_blocker_code_mismatch_rejected(self) -> None:
        document = subject._synthetic_blocker(False)
        schema = subject.raw_literal_schema(subject._blocker_raw(document))
        with self.assertRaises(subject.R3Error):
            subject.validate_blocker_document(
                document=document, schema_fields=schema, expected_hash=document["artifact_hash"],
                expected_type="SyntheticBlockerV1", expected_task="SYNTHETIC_TASK",
                expected_code="WRONG", expected_class="SYNTHETIC_CLASS",
                status_required=False, expected_status=None,
            )

    def test_source_task_mismatch_rejected(self) -> None:
        document = subject._synthetic_blocker(False)
        schema = subject.raw_literal_schema(subject._blocker_raw(document))
        with self.assertRaises(subject.R3Error):
            subject.validate_blocker_document(
                document=document, schema_fields=schema, expected_hash=document["artifact_hash"],
                expected_type="SyntheticBlockerV1", expected_task="WRONG",
                expected_code="SYNTHETIC_BLOCKER", expected_class="SYNTHETIC_CLASS",
                status_required=False, expected_status=None,
            )

    def test_invented_status_rejected(self) -> None:
        old = subject._synthetic_blocker(False)
        schema = subject.raw_literal_schema(subject._blocker_raw(old))
        candidate = dict(old); candidate["status"] = "blocked_synthetic"
        candidate["artifact_hash"] = subject.stable_hash({k: v for k, v in candidate.items() if k != "artifact_hash"})
        with self.assertRaises(subject.R3Error):
            subject.validate_blocker_document(
                document=candidate, schema_fields=schema, expected_hash=candidate["artifact_hash"],
                expected_type="SyntheticBlockerV1", expected_task="SYNTHETIC_TASK",
                expected_code="SYNTHETIC_BLOCKER", expected_class="SYNTHETIC_CLASS",
                status_required=False, expected_status=None,
            )

    def test_literal_schema_extracts_multiple_keys_one_line(self) -> None:
        self.assertEqual(subject.raw_literal_schema(b'{"a":1,"b":2,"c":3}'), ("a", "b", "c"))

    def test_accounting_ast_multiple_keys_one_line(self) -> None:
        source = "def target():\n    accounting_core={'a':1,'b':2,'c':3}\n"
        self.assertEqual(r2.recover_dict_assignment_fields(
            source, function_name="target", assignment_name="accounting_core"
        ), ("a", "b", "c"))

    def test_actual_accounting_producer_exact(self) -> None:
        source = subject.PRODUCER_PATH.read_bytes().decode("utf-8")
        fields = r2.recover_dict_assignment_fields(
            source, function_name="_write_result_reports_v1", assignment_name="accounting_core"
        )
        self.assertEqual(len(fields), 36)
        self.assertIn("d1_metric_artifact_reads", fields)
        self.assertIn("d2_v1_metric_reads", fields)

    def test_fuzzy_alias_rejected(self) -> None:
        document = r2._synthetic_accounting()
        document["d1_metric_read"] = document.pop("d1_metric_artifact_reads")
        document["artifact_hash"] = subject.stable_hash({k: v for k, v in document.items() if k != "artifact_hash"})
        with self.assertRaises(r2.AccountingSchemaR2Error):
            r2._validate_synthetic(document, r2._synthetic_producer_source())

    def test_missing_accounting_field_rejected(self) -> None:
        document = r2._synthetic_accounting(); document.pop("d2_v1_metric_reads")
        document["artifact_hash"] = subject.stable_hash({k: v for k, v in document.items() if k != "artifact_hash"})
        with self.assertRaises(r2.AccountingSchemaR2Error):
            r2._validate_synthetic(document, r2._synthetic_producer_source())

    def test_wrong_type_and_value_counted(self) -> None:
        document = r2._synthetic_accounting()
        document["d1_metric_artifact_reads"] = False
        document["d2_v1_metric_reads"] = 1
        fields = r2.recover_dict_assignment_fields(
            r2._synthetic_producer_source(), function_name="_write_result_reports_v1",
            assignment_name="accounting_core",
        )
        audit = r2.build_inventory_and_audit(document, fields)
        self.assertEqual(audit.wrong_type_count, 1)
        self.assertEqual(audit.wrong_value_count, 1)

    def test_all_28_concepts_audited(self) -> None:
        document = r2._synthetic_accounting()
        fields = r2.recover_dict_assignment_fields(
            r2._synthetic_producer_source(), function_name="_write_result_reports_v1",
            assignment_name="accounting_core",
        )
        audit = r2.build_inventory_and_audit(document, fields)
        self.assertEqual(audit.full_semantic_concepts_required, 28)
        self.assertEqual(audit.exact_name_matches, 27)
        self.assertEqual(audit.schema_proven_name_corrections, 1)
        self.assertEqual(audit.unresolved_field_mismatches, 0)

    def test_incomplete_r5_snapshot_rejected(self) -> None:
        with self.assertRaises(subject.R3Error):
            subject.build_r5_snapshot({"metric_oracle_completed": True}, "TRIGGERS = {}", {})

    def test_report_schema_collision_rejected(self) -> None:
        with self.assertRaises(subject.R3Error):
            subject.validate_report_schema({"artifact_hash": "x", "reference_artifact_hash": "y"})

    def test_adversarial_contract_accepts_nothing(self) -> None:
        attacks, accepted = subject.adversarial_contract()
        self.assertGreaterEqual(attacks, 20)
        self.assertEqual(accepted, 0)

    def test_no_regex_or_line_parser_in_r3(self) -> None:
        source = Path(subject.__file__).read_text(encoding="utf-8")
        tree = ast.parse(source)
        imported = {
            alias.name for node in ast.walk(tree)
            if isinstance(node, (ast.Import, ast.ImportFrom))
            for alias in node.names
        }
        self.assertNotIn("re", imported)
        self.assertNotIn(".splitlines(", source)

    def test_no_scientific_paths_in_r3(self) -> None:
        source = Path(subject.__file__).read_text(encoding="utf-8")
        forbidden = (
            "DETECTOR_PREDICTION_ARTIFACT_V1.json", "RULE_PREDICTION_ARTIFACT_V1.json",
            "SOURCE_MAP.json", "NATIVE_HORIZON_MAP.json", "label-test1.csv", "test2.csv",
        )
        self.assertTrue(all(token not in source for token in forbidden))


if __name__ == "__main__":
    unittest.main()
