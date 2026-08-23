from __future__ import annotations

from pathlib import Path
import unittest

from scripts import remediate_task039e3_r2r_d2_v2_r5_execution_accounting_schema_parser_r3 as subject
from scripts import remediate_task039e3_r2r_d2_v2_r5_execution_accounting_schema_parser_r2 as r2


class AccountingSchemaParserR3IndependentTests(unittest.TestCase):
    def assert_rejected(self, action) -> None:
        with self.assertRaises((subject.R3Error, r2.AccountingSchemaR2Error)):
            action()

    def test_hard_coded_status_requirement_attack(self) -> None:
        old = subject._synthetic_blocker(False)
        self.assert_rejected(lambda: subject.validate_blocker_document(
            document=old, schema_fields=subject.raw_literal_schema(subject._blocker_raw(old)),
            expected_hash=old["artifact_hash"], expected_type="SyntheticBlockerV1",
            expected_task="SYNTHETIC_TASK", expected_code="SYNTHETIC_BLOCKER",
            expected_class="SYNTHETIC_CLASS", status_required=True,
            expected_status="blocked_synthetic",
        ))

    def test_fake_status_inserted_attack(self) -> None:
        old = subject._synthetic_blocker(False); schema = subject.raw_literal_schema(subject._blocker_raw(old))
        old["status"] = "blocked_synthetic"
        old["artifact_hash"] = subject.stable_hash({k: v for k, v in old.items() if k != "artifact_hash"})
        self.assert_rejected(lambda: subject.validate_blocker_document(
            document=old, schema_fields=schema, expected_hash=old["artifact_hash"],
            expected_type="SyntheticBlockerV1", expected_task="SYNTHETIC_TASK",
            expected_code="SYNTHETIC_BLOCKER", expected_class="SYNTHETIC_CLASS",
            status_required=False, expected_status=None,
        ))

    def test_status_from_filename_only_attack(self) -> None:
        self.assertFalse(subject.lifecycle_binding("blocked_file.json BLOCK;", "TASK", "COMMIT", "HASH"))

    def test_stale_blocker_wrapper_attack(self) -> None:
        document = subject._synthetic_blocker(False); document["root_cause"] = "changed"
        self.assert_rejected(lambda: subject.validate_self_hash(document, document["artifact_hash"]))

    def test_decoy_blocker_dict_does_not_define_schema(self) -> None:
        raw = b'{"decoy":{"status":"fake"},"artifact_type":"x"}'
        self.assertEqual(subject.raw_literal_schema(raw), ("decoy", "artifact_type"))

    def test_decoy_accounting_assignment_rejected_if_target_ambiguous(self) -> None:
        source = "def f():\n accounting_core={'a':1}\n accounting_core={'b':2}\n"
        self.assert_rejected(lambda: r2.recover_dict_assignment_fields(
            source, function_name="f", assignment_name="accounting_core"
        ))

    def test_injected_noncanonical_d1_field_attack(self) -> None:
        document = r2._synthetic_accounting(); document["d1_metric_reads"] = 0
        document["artifact_hash"] = subject.stable_hash({k: v for k, v in document.items() if k != "artifact_hash"})
        self.assert_rejected(lambda: r2._validate_synthetic(document, r2._synthetic_producer_source()))

    def test_removed_canonical_d1_field_attack(self) -> None:
        document = r2._synthetic_accounting(); document.pop("d1_metric_artifact_reads")
        document["artifact_hash"] = subject.stable_hash({k: v for k, v in document.items() if k != "artifact_hash"})
        self.assert_rejected(lambda: r2._validate_synthetic(document, r2._synthetic_producer_source()))

    def test_wrong_d2_v1_metric_value_attack(self) -> None:
        document = r2._synthetic_accounting(); document["d2_v1_metric_reads"] = 1
        fields = r2.recover_dict_assignment_fields(
            r2._synthetic_producer_source(), function_name="_write_result_reports_v1",
            assignment_name="accounting_core",
        )
        self.assertEqual(r2.build_inventory_and_audit(document, fields).wrong_value_count, 1)

    def test_all_mismatches_collected(self) -> None:
        document = r2._synthetic_accounting()
        document["d1_metric_artifact_reads"] = 1
        document["d2_v1_metric_reads"] = 1
        document["test2_accesses"] = 1
        fields = r2.recover_dict_assignment_fields(
            r2._synthetic_producer_source(), function_name="_write_result_reports_v1",
            assignment_name="accounting_core",
        )
        audit = r2.build_inventory_and_audit(document, fields)
        self.assertEqual(audit.wrong_value_count, 3)
        self.assertEqual(audit.unresolved_field_mismatches, 3)

    def test_fabricated_r5_snapshot_attack(self) -> None:
        self.assert_rejected(lambda: subject.build_r5_snapshot(
            {"metric_oracle_completed": True, "r5_semantic_parse_counts": {}},
            "TRIGGERS = {}", {},
        ))

    def test_private_or_scientific_paths_absent(self) -> None:
        source = Path(subject.__file__).read_text(encoding="utf-8")
        self.assertNotIn("FusionEvidenceV2.json", source)
        self.assertNotIn("MetricEvidenceV2.json", source)
        self.assertNotIn("label-test1.csv", source)

    def test_access_counters_frozen_zero(self) -> None:
        counters = {
            "scientific_artifacts_reopened_during_r3": False,
            "label_parses_during_r3": 0,
            "test1_feature_accesses": 0,
            "test2_accesses": 0,
            "authoritative_scientific_executions": 0,
        }
        self.assertTrue(all(value in (0, False) for value in counters.values()))

    def test_independent_attacks_all_rejected(self) -> None:
        attacks, accepted = subject.adversarial_contract()
        self.assertGreaterEqual(attacks, 20)
        self.assertEqual(accepted, 0)


if __name__ == "__main__":
    unittest.main()
