from __future__ import annotations

import ast
import json
from pathlib import Path
import unittest

from scripts import remediate_task039e3_r2r_d2_v2_r5_execution_accounting_schema_parser_r2 as subject


class AccountingSchemaParserR2Tests(unittest.TestCase):
    def test_multiple_dict_keys_on_one_line_are_all_extracted(self) -> None:
        source = "def target():\n    accounting_core = {'a': 1, 'b': 2, 'c': 3, 'd': 4, 'e': 5}\n"
        self.assertEqual(
            subject.recover_dict_assignment_fields(
                source, function_name="target", assignment_name="accounting_core"
            ),
            ("a", "b", "c", "d", "e"),
        )

    def test_dict_keys_over_multiple_lines_are_all_extracted(self) -> None:
        source = "def target():\n    accounting_core = {\n        'a': 1,\n        'b': 2,\n    }\n"
        self.assertEqual(
            subject.recover_dict_assignment_fields(
                source, function_name="target", assignment_name="accounting_core"
            ),
            ("a", "b"),
        )

    def test_ast_dict_extraction_is_structural(self) -> None:
        tree = ast.parse("x = {'alpha': 1, 'beta': 2}")
        node = tree.body[0]
        self.assertIsInstance(node, ast.Assign)
        self.assertEqual(subject.fields_from_dict_node(node.value), ("alpha", "beta"))

    def test_dataclass_fields_are_extracted(self) -> None:
        source = "from dataclasses import dataclass\n@dataclass\nclass Accounting:\n    a: int\n    b: bool = False\n"
        self.assertEqual(subject.recover_class_fields(source, class_name="Accounting"), ("a", "b"))

    def test_typeddict_fields_are_extracted(self) -> None:
        source = "from typing import TypedDict\nclass Accounting(TypedDict):\n    a: int\n    b: str\n"
        self.assertEqual(subject.recover_class_fields(source, class_name="Accounting"), ("a", "b"))

    def test_constructor_keyword_fields_are_extracted(self) -> None:
        source = "def build():\n    return Accounting(a=1, b=2, c=3)\n"
        self.assertEqual(
            subject.recover_constructor_keyword_fields(
                source, function_name="build", constructor_name="Accounting"
            ),
            ("a", "b", "c"),
        )

    def test_unrelated_dict_keys_are_excluded(self) -> None:
        source = (
            "DECOY = {'wrong': 1}\n"
            "def target():\n"
            "    decoy = {'also_wrong': 2}\n"
            "    accounting_core = {'right': 3}\n"
        )
        self.assertEqual(
            subject.recover_dict_assignment_fields(
                source, function_name="target", assignment_name="accounting_core"
            ),
            ("right",),
        )

    def test_ambiguous_target_producer_is_rejected(self) -> None:
        source = "def target():\n    accounting_core = {'a': 1}\n    accounting_core = {'b': 2}\n"
        with self.assertRaises(subject.AccountingSchemaR2Error):
            subject.recover_dict_assignment_fields(
                source, function_name="target", assignment_name="accounting_core"
            )

    def test_dynamic_dict_key_is_rejected(self) -> None:
        source = "def target():\n    accounting_core = {key: 1}\n"
        with self.assertRaises(subject.AccountingSchemaR2Error):
            subject.recover_dict_assignment_fields(
                source, function_name="target", assignment_name="accounting_core"
            )

    def test_duplicate_json_keys_are_rejected(self) -> None:
        with self.assertRaises(subject.AccountingSchemaR2Error):
            subject.strict_json_bytes(b'{"a":1,"a":2}')

    def test_canonical_d1_field_is_producer_schema(self) -> None:
        source = subject.PRODUCER_PATH.read_bytes().decode("utf-8")
        fields = subject.recover_dict_assignment_fields(
            source,
            function_name="_write_result_reports_v1",
            assignment_name="accounting_core",
        )
        self.assertIn("d1_metric_artifact_reads", fields)
        self.assertNotIn("d1_metric_reads", fields)
        self.assertEqual(len(fields), 36)

    def test_noncanonical_d1_alias_is_not_accepted(self) -> None:
        document = subject._synthetic_accounting()
        document["d1_metric_reads"] = document.pop("d1_metric_artifact_reads")
        document["artifact_hash"] = subject.stable_hash(
            {key: value for key, value in document.items() if key != "artifact_hash"}
        )
        with self.assertRaises(subject.AccountingSchemaR2Error):
            subject._validate_synthetic(document, subject._synthetic_producer_source())

    def test_missing_canonical_field_is_rejected(self) -> None:
        document = subject._synthetic_accounting()
        document.pop("d2_v1_metric_reads")
        document["artifact_hash"] = subject.stable_hash(
            {key: value for key, value in document.items() if key != "artifact_hash"}
        )
        with self.assertRaises(subject.AccountingSchemaR2Error):
            subject._validate_synthetic(document, subject._synthetic_producer_source())

    def test_wrong_field_type_is_counted(self) -> None:
        document = subject._synthetic_accounting()
        document["d1_metric_artifact_reads"] = False
        audit = subject.build_inventory_and_audit(
            document,
            subject.recover_dict_assignment_fields(
                subject._synthetic_producer_source(),
                function_name="_write_result_reports_v1",
                assignment_name="accounting_core",
            ),
        )
        self.assertEqual(audit.wrong_type_count, 1)
        self.assertGreater(audit.unresolved_field_mismatches, 0)

    def test_wrong_accounting_value_is_counted(self) -> None:
        document = subject._synthetic_accounting()
        document["d1_metric_artifact_reads"] = 1
        audit = subject.build_inventory_and_audit(
            document,
            subject.recover_dict_assignment_fields(
                subject._synthetic_producer_source(),
                function_name="_write_result_reports_v1",
                assignment_name="accounting_core",
            ),
        )
        self.assertEqual(audit.wrong_value_count, 1)

    def test_complete_inventory_audits_all_fields(self) -> None:
        document = subject._synthetic_accounting()
        audit = subject.build_inventory_and_audit(
            document,
            subject.recover_dict_assignment_fields(
                subject._synthetic_producer_source(),
                function_name="_write_result_reports_v1",
                assignment_name="accounting_core",
            ),
        )
        self.assertEqual(len(audit.inventory), 44)
        self.assertEqual(audit.full_semantic_concepts_required, 28)
        self.assertEqual(audit.exact_name_matches, 27)
        self.assertEqual(audit.schema_proven_name_corrections, 1)
        self.assertEqual(audit.unresolved_field_mismatches, 0)

    def test_incomplete_r5_oracle_snapshot_is_rejected(self) -> None:
        document = {**subject.R5_DIRECT_EXPECTED, "r5_semantic_parse_counts": subject.R5_PARSE_EXPECTED}
        snapshot = subject.audit_r5_snapshot(document)
        self.assertFalse(snapshot.complete)
        self.assertGreater(len(snapshot.missing_required_fields), 0)
        with self.assertRaises(subject.AccountingSchemaR2Error):
            subject._require_complete_snapshot(document)

    def test_adversarial_contract_rejects_every_mutation(self) -> None:
        attacks, accepted = subject.adversarial_contract()
        self.assertGreaterEqual(attacks, 18)
        self.assertEqual(accepted, 0)

    def test_r2_source_has_no_forbidden_schema_parser(self) -> None:
        source = Path(subject.__file__).read_text(encoding="utf-8")
        forbidden = ("import re", ".splitlines(", "re.findall", "re.match")
        self.assertTrue(all(token not in source for token in forbidden))

    def test_r2_source_has_no_scientific_artifact_paths(self) -> None:
        source = Path(subject.__file__).read_text(encoding="utf-8")
        forbidden = (
            "label-test1.csv",
            "DetectorPrediction",
            "RulePrediction",
            "CombinedPredictionV2.json",
            "FusionEvidenceV2",
            "MetricEvidenceV2",
            "test2.csv",
        )
        self.assertTrue(all(token not in source for token in forbidden))

    def test_task_boundary_forbids_scientific_and_label_access(self) -> None:
        task = (subject.ROOT / "TASKS/TASK-039E3-R2R-UTILITY-INNER-D2-V2-R5-EXECUTION-ACCOUNTING-SCHEMA-PARSER-REMEDIATION-R2.md").read_text(encoding="utf-8")
        self.assertIn("No scientific-oracle recomputation", task)
        self.assertIn("No label, test1 feature, test2, or OUTER access", task)


if __name__ == "__main__":
    unittest.main()
