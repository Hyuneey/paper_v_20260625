from __future__ import annotations

from dataclasses import asdict, replace
from hashlib import sha256
import json
from pathlib import Path
import unittest

from scripts import remediate_task039e3_r2r_d2_v2_r5_report_render_r1 as subject


class ReportRenderR1Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.snapshot = subject.R4CompletedIntegrityPreRenderSnapshotV1()

    def test_exact_snapshot_maps(self) -> None:
        model, rows, closure = subject.adapt_snapshot(self.snapshot)
        self.assertEqual(model.v2_attack_event_recall, 0.7857142857142857)
        self.assertEqual(len(rows), closure.required_report_fields)
        self.assertEqual(closure.missing_report_fields, 0)

    def test_mapping_uses_canonical_metric_names(self) -> None:
        model, _, _ = subject.adapt_snapshot(self.snapshot)
        body = subject.report_body(model)
        self.assertIn(b"6.915070855955625", body)
        self.assertNotIn(b"v2_recall", body)

    def test_missing_input_field_rejected(self) -> None:
        mapping = dict(subject.SOURCE_MAP)
        mapping["v2_normal_far"] = "missing"
        with self.assertRaises(subject.RenderR1Error):
            subject.adapt_snapshot(self.snapshot, mapping)

    def test_missing_report_field_rejected(self) -> None:
        mapping = dict(subject.SOURCE_MAP)
        mapping.pop("v2_normal_far")
        with self.assertRaises(subject.RenderR1Error):
            subject.adapt_snapshot(self.snapshot, mapping)

    def test_unknown_report_field_rejected(self) -> None:
        mapping = dict(subject.SOURCE_MAP)
        mapping["legacy_status"] = None
        with self.assertRaises(subject.RenderR1Error):
            subject.adapt_snapshot(self.snapshot, mapping)

    def test_duplicate_semantic_mapping_rejected(self) -> None:
        mapping = dict(subject.SOURCE_MAP)
        mapping["v2_normal_far"] = "v2_attack_event_recall"
        with self.assertRaises(subject.RenderR1Error):
            subject.adapt_snapshot(self.snapshot, mapping)

    def test_legacy_renderer_field_rejected(self) -> None:
        mapping = dict(subject.SOURCE_MAP)
        mapping["v2_attack_event_recall"] = "v2_recall"
        with self.assertRaises(subject.RenderR1Error):
            subject.adapt_snapshot(self.snapshot, mapping)

    def test_redundant_field_requirement_rejected(self) -> None:
        mapping = dict(subject.SOURCE_MAP)
        mapping["status"] = None
        with self.assertRaises(subject.RenderR1Error):
            subject.adapt_snapshot(self.snapshot, mapping)

    def test_wrong_type_rejected(self) -> None:
        with self.assertRaises(subject.RenderR1Error):
            subject.adapt_snapshot(replace(self.snapshot, attack_event_count=True))

    def test_metric_mutation_rejected(self) -> None:
        with self.assertRaises(subject.RenderR1Error):
            subject.adapt_snapshot(replace(self.snapshot, v2_normal_far=6.9))

    def test_accounting_mutation_rejected(self) -> None:
        with self.assertRaises(subject.RenderR1Error):
            subject.adapt_snapshot(replace(self.snapshot, exact_name_matches=26))

    def test_silent_default_rejected(self) -> None:
        constants = dict(subject.CONSTANT_VALUES)
        constants["completion_method"] = ""
        with self.assertRaises(subject.RenderR1Error):
            subject.adapt_snapshot(self.snapshot, constants=constants)

    def test_fuzzy_alias_rejected(self) -> None:
        mapping = dict(subject.SOURCE_MAP)
        mapping["v2_normal_far"] = "v2_normal_farr"
        with self.assertRaises(subject.RenderR1Error):
            subject.adapt_snapshot(self.snapshot, mapping)

    def test_duplicate_json_keys_rejected(self) -> None:
        with self.assertRaises(subject.RenderR1Error):
            subject.strict_json(b'{"a":1,"a":2}')

    def test_self_hash_collision_rejected(self) -> None:
        with self.assertRaises(subject.RenderR1Error):
            subject.seal({"artifact_hash": "x"})

    def test_referenced_hash_collision_rejected(self) -> None:
        with self.assertRaises(subject.RenderR1Error):
            subject.seal({"old_artifact_hash": "x"})

    def test_seal_round_trip(self) -> None:
        document = subject.seal({"artifact_type": "Synthetic", "x": 1})
        subject.validate_document(document)

    def test_markdown_lf_deterministic(self) -> None:
        model = subject.adapt_snapshot(self.snapshot)[0]
        body = subject.report_body(model)
        self.assertNotIn(b"\r", body)
        self.assertTrue(body.endswith(b"\n"))

    def test_renderer_forensic_finds_exact_drift(self) -> None:
        source = subject.R4_SOURCE_PATH.read_text(encoding="utf-8")
        result = subject.renderer_forensic(source)
        self.assertEqual(result["classification"], "RENDERER_USED_LEGACY_FIELD_NAME")

    def test_incomplete_renderer_forensic_rejected(self) -> None:
        with self.assertRaises(subject.RenderR1Error):
            subject.renderer_forensic("def report_body(x): return x\ndef write_reports(): pass\n")

    def test_build_outputs_is_in_memory(self) -> None:
        source = subject.R4_SOURCE_PATH.read_text(encoding="utf-8")
        outputs, markdown, canonical, closure = subject.build_outputs(
            self.snapshot, subject.renderer_forensic(source), "2026-08-23T00:00:00Z", 19, 0)
        self.assertEqual(canonical["result_integrity"], "PASS")
        self.assertIn("BUNDLE", outputs)
        self.assertIn("RECEIPT", outputs)
        self.assertEqual(closure.required_report_fields, closure.mapped_report_fields)
        self.assertIn(b"Report-Self-Hash", markdown)

    def test_report_model_mutation_rejected(self) -> None:
        model = subject.adapt_snapshot(self.snapshot)[0]
        with self.assertRaises(subject.RenderR1Error):
            subject.report_body(replace(model, v2_attack_event_recall=0.7))

    def test_r4_authority_rejects_empty(self) -> None:
        with self.assertRaises(subject.RenderR1Error):
            subject.validate_r4_authority({}, b"")

    def test_adversarial_contract_accepts_none(self) -> None:
        attacks, accepted = subject.adversarial_contract()
        self.assertGreaterEqual(attacks, 19)
        self.assertEqual(accepted, 0)

    def test_source_has_no_forbidden_scientific_paths(self) -> None:
        source = Path(subject.__file__).read_text(encoding="utf-8")
        forbidden = ("label-test1.csv", "DetectorPrediction", "RulePrediction",
                     "FusionEvidenceV2.json", "MetricEvidenceV2.json")
        for token in forbidden:
            self.assertNotIn(token, source)

    def test_source_has_no_fallback_chain(self) -> None:
        source = Path(subject.__file__).read_text(encoding="utf-8")
        self.assertNotIn(".get(\"v2_recall\"", source)
        self.assertNotIn(" or result.get", source)


if __name__ == "__main__":
    unittest.main()
