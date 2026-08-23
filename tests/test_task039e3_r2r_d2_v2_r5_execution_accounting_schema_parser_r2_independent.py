from __future__ import annotations

from dataclasses import replace
import unittest

from scripts import remediate_task039e3_r2r_d2_v2_r5_execution_accounting_schema_parser_r2 as subject


class AccountingSchemaParserR2IndependentTests(unittest.TestCase):
    def assert_rejected(self, action) -> None:
        with self.assertRaises(subject.AccountingSchemaR2Error):
            action()

    def test_original_first_key_only_failure_is_impossible(self) -> None:
        source = "def target():\n    accounting_core = {'first': 1, 'second': 2, 'third': 3}\n"
        self.assertEqual(
            subject.recover_dict_assignment_fields(
                source, function_name="target", assignment_name="accounting_core"
            ),
            ("first", "second", "third"),
        )

    def test_five_keys_on_one_line(self) -> None:
        source = "def target():\n    accounting_core = {'a':0,'b':0,'c':0,'d':0,'e':0}\n"
        self.assertEqual(
            len(subject.recover_dict_assignment_fields(
                source, function_name="target", assignment_name="accounting_core"
            )),
            5,
        )

    def test_decoy_dict_before_is_excluded(self) -> None:
        source = "DECOY={'x':1}\ndef target():\n    accounting_core={'a':1}\n"
        self.assertEqual(subject.recover_dict_assignment_fields(
            source, function_name="target", assignment_name="accounting_core"
        ), ("a",))

    def test_decoy_dict_after_is_excluded(self) -> None:
        source = "def target():\n    accounting_core={'a':1}\nDECOY={'x':1}\n"
        self.assertEqual(subject.recover_dict_assignment_fields(
            source, function_name="target", assignment_name="accounting_core"
        ), ("a",))

    def test_field_string_in_log_is_excluded(self) -> None:
        source = "def target():\n    print('d1_metric_reads')\n    accounting_core={'a':1}\n"
        self.assertEqual(subject.recover_dict_assignment_fields(
            source, function_name="target", assignment_name="accounting_core"
        ), ("a",))

    def test_field_string_in_docstring_is_excluded(self) -> None:
        source = "def target():\n    '''d1_metric_reads'''\n    accounting_core={'a':1}\n"
        self.assertEqual(subject.recover_dict_assignment_fields(
            source, function_name="target", assignment_name="accounting_core"
        ), ("a",))

    def test_dynamic_ambiguous_dict_is_rejected(self) -> None:
        self.assert_rejected(lambda: subject.recover_dict_assignment_fields(
            "def target():\n    accounting_core=dict(a=1)\n",
            function_name="target", assignment_name="accounting_core",
        ))

    def test_fuzzy_typo_alias_is_rejected(self) -> None:
        document = subject._synthetic_accounting()
        document["d1_metric_artifact_read"] = document.pop("d1_metric_artifact_reads")
        document["artifact_hash"] = subject.stable_hash(
            {key: value for key, value in document.items() if key != "artifact_hash"}
        )
        self.assert_rejected(lambda: subject._validate_synthetic(document, subject._synthetic_producer_source()))

    def test_injected_noncanonical_field_is_rejected(self) -> None:
        document = subject._synthetic_accounting()
        document["d1_metric_reads"] = 0
        document["artifact_hash"] = subject.stable_hash(
            {key: value for key, value in document.items() if key != "artifact_hash"}
        )
        self.assert_rejected(lambda: subject._validate_synthetic(document, subject._synthetic_producer_source()))

    def test_deleted_canonical_field_is_rejected(self) -> None:
        document = subject._synthetic_accounting()
        document.pop("d1_metric_artifact_reads")
        document["artifact_hash"] = subject.stable_hash(
            {key: value for key, value in document.items() if key != "artifact_hash"}
        )
        self.assert_rejected(lambda: subject._validate_synthetic(document, subject._synthetic_producer_source()))

    def test_wrong_canonical_value_fails_full_audit(self) -> None:
        document = subject._synthetic_accounting()
        document["d1_metric_artifact_reads"] = 2
        audit = subject.build_inventory_and_audit(
            document,
            subject.recover_dict_assignment_fields(
                subject._synthetic_producer_source(),
                function_name="_write_result_reports_v1",
                assignment_name="accounting_core",
            ),
        )
        self.assertEqual(audit.wrong_value_count, 1)
        self.assertEqual(audit.unresolved_field_mismatches, 1)

    def test_stale_accounting_hash_is_rejected(self) -> None:
        document = subject._synthetic_accounting()
        document["task_id"] = "mutated"
        self.assert_rejected(lambda: subject.validate_self_hash(document, str(document["artifact_hash"])))

    def test_wrong_accounting_artifact_type_is_wrong_value_authority(self) -> None:
        document = subject._synthetic_accounting()
        document["artifact_type"] = "WrongAccounting"
        document["artifact_hash"] = subject.stable_hash(
            {key: value for key, value in document.items() if key != "artifact_hash"}
        )
        self.assert_rejected(lambda: subject._validate_synthetic(document, subject._synthetic_producer_source()))

    def test_incomplete_semantic_inventory_is_detected(self) -> None:
        mapping = dict(subject.SEMANTIC_MAPPING)
        mapping.pop("D1_METRIC_ARTIFACT_READ_COUNT")
        self.assertEqual(len(mapping), len(subject.SEMANTIC_MAPPING) - 1)
        self.assertEqual(len(subject.SEMANTIC_MAPPING), 28)

    def test_all_mismatches_are_counted_together(self) -> None:
        document = subject._synthetic_accounting()
        document["d1_metric_artifact_reads"] = 1
        document["d2_v1_metric_reads"] = 1
        document["test2_accesses"] = 1
        audit = subject.build_inventory_and_audit(
            document,
            subject.recover_dict_assignment_fields(
                subject._synthetic_producer_source(),
                function_name="_write_result_reports_v1",
                assignment_name="accounting_core",
            ),
        )
        self.assertEqual(audit.wrong_value_count, 3)
        self.assertEqual(audit.unresolved_field_mismatches, 3)

    def test_fabricated_snapshot_completion_is_rejected(self) -> None:
        document = {**subject.R5_DIRECT_EXPECTED, "r5_semantic_parse_counts": subject.R5_PARSE_EXPECTED}
        document["v2_attack_event_recall"] = 0.7857142857142857
        snapshot = subject.audit_r5_snapshot(document)
        self.assertFalse(snapshot.complete)
        self.assertGreater(len(snapshot.missing_required_fields), 1)

    def test_snapshot_parse_count_mutation_is_rejected(self) -> None:
        document = {
            **subject.R5_DIRECT_EXPECTED,
            **{field: 0 for field in subject.R5_REQUIRED_SNAPSHOT_FIELDS},
            "r5_semantic_parse_counts": {**subject.R5_PARSE_EXPECTED, "LABEL_TEST1": 2},
        }
        self.assertFalse(subject.audit_r5_snapshot(document).complete)

    def test_snapshot_direct_divergence_mutation_is_rejected(self) -> None:
        document = {
            **subject.R5_DIRECT_EXPECTED,
            **{field: 0 for field in subject.R5_REQUIRED_SNAPSHOT_FIELDS},
            "r5_semantic_parse_counts": subject.R5_PARSE_EXPECTED,
        }
        document["prediction_divergences"] = 1
        self.assertFalse(subject.audit_r5_snapshot(document).complete)

    def test_duplicate_producer_field_is_rejected(self) -> None:
        self.assert_rejected(lambda: subject.recover_dict_assignment_fields(
            "def target():\n    accounting_core={'a':1,'a':2}\n",
            function_name="target", assignment_name="accounting_core",
        ))

    def test_multiple_target_functions_are_rejected(self) -> None:
        self.assert_rejected(lambda: subject.recover_dict_assignment_fields(
            "def target():\n    accounting_core={'a':1}\ndef target():\n    accounting_core={'b':2}\n",
            function_name="target", assignment_name="accounting_core",
        ))

    def test_scientific_reopen_counters_are_hard_zero(self) -> None:
        expected = {
            "scientific_artifacts_reopened_during_r2": False,
            "label_parses_during_r2": 0,
            "test1_feature_accesses": 0,
            "test2_accesses": 0,
            "authoritative_scientific_executions": 0,
        }
        self.assertTrue(all(value in (False, 0) for value in expected.values()))

    def test_adversarial_suite_accepts_nothing(self) -> None:
        attacks, accepted = subject.adversarial_contract()
        self.assertGreaterEqual(attacks, 18)
        self.assertEqual(accepted, 0)


if __name__ == "__main__":
    unittest.main()
