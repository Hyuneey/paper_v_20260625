from __future__ import annotations

from dataclasses import asdict, replace
import json
from pathlib import Path
import unittest

from scripts import remediate_task039e3_r2r_d2_v2_r5_report_render_r1 as subject


class ReportRenderR1IndependentTests(unittest.TestCase):
    def setUp(self) -> None:
        self.snapshot = subject.R4CompletedIntegrityPreRenderSnapshotV1()
        self.model = subject.adapt_snapshot(self.snapshot)[0]

    def test_old_r3_name_attack(self) -> None:
        mapping = dict(subject.SOURCE_MAP); mapping["v2_normal_far"] = "v2_far"
        with self.assertRaises(subject.RenderR1Error): subject.adapt_snapshot(self.snapshot, mapping)

    def test_status_attack(self) -> None:
        mapping = dict(subject.SOURCE_MAP); mapping["status"] = None
        with self.assertRaises(subject.RenderR1Error): subject.adapt_snapshot(self.snapshot, mapping)

    def test_d1_metric_alias_attack(self) -> None:
        with self.assertRaises(subject.RenderR1Error):
            subject.adapt_snapshot(replace(self.snapshot, canonical_d1_metric_field="d1_metric_reads"))

    def test_drop_canonical_d1_field_attack(self) -> None:
        with self.assertRaises(subject.RenderR1Error):
            subject.adapt_snapshot(replace(self.snapshot, canonical_d1_metric_field=""))

    def test_v2_far_change_attack(self) -> None:
        with self.assertRaises(subject.RenderR1Error):
            subject.report_body(replace(self.model, v2_normal_far=7.0))

    def test_recall_rounding_attack(self) -> None:
        with self.assertRaises(subject.RenderR1Error):
            subject.report_body(replace(self.model, v2_attack_event_recall=0.786))

    def test_zero_to_null_attack(self) -> None:
        values = asdict(self.model); values["d0_missed_recovery_rate"] = None
        with self.assertRaises(subject.RenderR1Error):
            subject.report_body(subject.D2V2ResultIntegrityCompletionReportModelR1(**values))

    def test_v1_substitution_attack(self) -> None:
        with self.assertRaises(subject.RenderR1Error):
            subject.report_body(replace(self.model, v2_alarm_episodes=46))

    def test_omit_custody_attack(self) -> None:
        with self.assertRaises(subject.RenderR1Error):
            subject.adapt_snapshot(replace(self.snapshot, custody_compatibility_pass=False))

    def test_private_path_attack(self) -> None:
        source = Path(subject.__file__).read_text(encoding="utf-8")
        self.assertNotIn("C:\\\\Users\\\\", source)
        self.assertNotIn("/home/", source)

    def test_active_source_set_attack(self) -> None:
        source = Path(subject.__file__).read_text(encoding="utf-8")
        self.assertNotIn("active_source_set", source)

    def test_duplicate_self_hash_attack(self) -> None:
        with self.assertRaises(subject.RenderR1Error):
            subject.seal({"artifact_hash": "a", "artifact_hash_2": "b"})

    def test_duplicate_json_attack(self) -> None:
        with self.assertRaises(subject.RenderR1Error):
            subject.strict_json(b'{"artifact_type":"x","artifact_type":"y"}')

    def test_stale_bundle_footer_attack(self) -> None:
        with self.assertRaises(subject.RenderR1Error):
            subject.validate_markdown(b"body\n<!-- BEGIN D2 V2 R5 REPORT RENDER R1 COMPLETION PROVENANCE V1 -->\n", "x", "y")

    def test_scientific_oracle_call_absent(self) -> None:
        source = Path(subject.__file__).read_text(encoding="utf-8")
        self.assertNotIn("build_r5_snapshot(", source)
        self.assertNotIn("fusion_oracle(", source)

    def test_accounting_reaudit_call_absent(self) -> None:
        source = Path(subject.__file__).read_text(encoding="utf-8")
        self.assertNotIn("build_inventory_and_audit(", source)
        self.assertNotIn("ACCOUNTING_PATH.read", source)

    def test_label_reopen_absent(self) -> None:
        source = Path(subject.__file__).read_text(encoding="utf-8")
        self.assertNotIn("label-test1", source)

    def test_test2_reopen_absent(self) -> None:
        source = Path(subject.__file__).read_text(encoding="utf-8")
        self.assertNotIn("hai-23.05/test2", source)

    def test_authority_hash_mutation_rejected(self) -> None:
        document = subject.seal({"artifact_type": "x", "authority_sha256": "a" * 64})
        mutated = dict(document); mutated["authority_sha256"] = "b" * 64
        with self.assertRaises(subject.RenderR1Error):
            subject.validate_document(mutated)

    def test_all_builtin_attacks_rejected(self) -> None:
        attacks, accepted = subject.adversarial_contract()
        self.assertEqual(accepted, 0)
        self.assertGreaterEqual(attacks, 19)


if __name__ == "__main__":
    unittest.main()
