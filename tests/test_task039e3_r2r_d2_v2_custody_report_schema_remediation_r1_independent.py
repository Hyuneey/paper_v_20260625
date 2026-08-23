from __future__ import annotations

import ast
from copy import deepcopy
from dataclasses import replace
import json
import unittest

from scripts import remediate_task039e3_r2r_d2_v2_custody_report_schema_r1 as subject


class IndependentCustodyReportSchemaRemediationR1Tests(unittest.TestCase):
    def test_module_has_no_private_locator_or_scientific_controller(self) -> None:
        path = subject.ROOT / "scripts/remediate_task039e3_r2r_d2_v2_custody_report_schema_r1.py"
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source)
        imported = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                imported.append(node.module or "")
        self.assertFalse(any("inner_execution" in name or "recovery_custody" in name for name in imported))
        self.assertNotIn("binding_locator(", source)
        self.assertNotIn("private_identity(", source)
        self.assertNotIn("execute_authorized", source)
        self.assertNotIn("label-test1", source)

    def test_permissive_json_duplicate_is_rejected_by_strict_parser(self) -> None:
        raw = b'{"hash":"first","hash":"second"}'
        self.assertEqual(json.loads(raw)["hash"], "second")
        with self.assertRaises(subject.ReportSchemaError):
            subject.strict_json_loads(raw)

    def test_self_hash_and_alias_collision_attacks(self) -> None:
        attacks = (
            (subject.SchemaFieldR1("self_hash", "artifact_hash"),),
            (subject.SchemaFieldR1("first", "self_hash"), subject.SchemaFieldR1("alias", "self_hash")),
            (subject.SchemaFieldR1("payload", "bundle_artifact_sha256"),),
            (subject.SchemaFieldR1("payload", "receipt_artifact_sha256"),),
        )
        for fields in attacks:
            with self.subTest(fields=fields), self.assertRaises(subject.ReportSchemaError):
                subject.validate_field_registry(fields)

    def test_unordered_serializer_does_not_define_identity(self) -> None:
        payload = {"z": 1, "a": 2}
        canonical = subject.canonical_json_bytes(payload)
        unordered = json.dumps(payload, sort_keys=False, separators=(",", ":")).encode()
        self.assertNotEqual(canonical, unordered)
        self.assertEqual(subject.canonical_self_hash(payload), subject.sha256(canonical).hexdigest())

    def test_reference_hash_cannot_be_overwritten_by_report_self_hash(self) -> None:
        completion = subject.D2V2PrivateCustodyBindingRemediationCompletionR1()
        reports, _ = subject.build_reports(
            completion,
            created_at_utc="2026-08-23T00:00:00Z",
            independent_attacks=20,
            accepted_invalid=0,
        )
        fusion = reports["FUSION_EVIDENCE_IDENTITY"]
        self.assertNotEqual(fusion["fusion_evidence_sha256"], fusion[subject.SELF_HASH_FIELD])
        mutated = {**fusion, "fusion_evidence_sha256": fusion[subject.SELF_HASH_FIELD]}
        with self.assertRaises(subject.ReportSchemaError):
            subject.validate_sealed_artifact(mutated)

    def test_bundle_and_receipt_hash_overwrite_attacks_rejected(self) -> None:
        completion = subject.D2V2PrivateCustodyBindingRemediationCompletionR1()
        reports, _ = subject.build_reports(
            completion,
            created_at_utc="2026-08-23T00:00:00Z",
            independent_attacks=20,
            accepted_invalid=0,
        )
        mutations = (
            {**reports["BUNDLE"], subject.SELF_HASH_FIELD: reports["RECEIPT"][subject.SELF_HASH_FIELD]},
            {**reports["RECEIPT"], "bundle_artifact_sha256": reports["RECEIPT"][subject.SELF_HASH_FIELD]},
        )
        for mutation in mutations:
            with self.subTest(), self.assertRaises(subject.ReportSchemaError):
                subject.validate_sealed_artifact(mutation)

    def test_generation_is_pure_and_does_not_revalidate_custody(self) -> None:
        completion = subject.D2V2PrivateCustodyBindingRemediationCompletionR1()
        before = deepcopy(completion)
        reports, markdown = subject.build_reports(
            completion,
            created_at_utc="2026-08-23T00:00:00Z",
            independent_attacks=20,
            accepted_invalid=0,
        )
        self.assertEqual(completion, before)
        self.assertEqual(reports["FUSION_EVIDENCE_IDENTITY"]["report_schema_revalidation_count"], 0)
        self.assertEqual(reports["METRIC_EVIDENCE_IDENTITY"]["report_schema_revalidation_count"], 0)
        subject.audit_markdown_bytes(markdown, reports)

    def test_private_mutation_and_data_access_flags_rejected(self) -> None:
        completion = subject.D2V2PrivateCustodyBindingRemediationCompletionR1()
        fields = (
            "private_evidence_copied", "private_evidence_moved",
            "private_evidence_rewritten", "private_evidence_repersisted",
            "scientific_prediction_parses", "label_parses",
            "test1_feature_accesses", "test2_accesses",
        )
        for field in fields:
            with self.subTest(field=field), self.assertRaises(subject.ReportSchemaError):
                subject.validate_completion(replace(completion, **{field: True if field.startswith("private_") else 1}))

    def test_report_set_is_exact_and_all_self_hashes_validate(self) -> None:
        reports, markdown = subject.build_reports(
            subject.D2V2PrivateCustodyBindingRemediationCompletionR1(),
            created_at_utc="2026-08-23T00:00:00Z",
            independent_attacks=20,
            accepted_invalid=0,
        )
        self.assertEqual(tuple(reports), subject.REPORT_NAMES)
        for report in reports.values():
            subject.validate_sealed_artifact(report)
            self.assertEqual(list(report).count(subject.SELF_HASH_FIELD), 1)
        subject.audit_markdown_bytes(markdown, reports)

    def test_historical_authorities_are_not_renamed(self) -> None:
        source = (subject.ROOT / "scripts/remediate_task039e3_r2r_d2_v2_custody_report_schema_r1.py").read_text(encoding="utf-8")
        self.assertIn("HISTORICAL_BLOCKER_SHA256", source)
        self.assertIn("fusion_evidence_sha256", source)
        self.assertIn("metric_evidence_sha256", source)
        self.assertIn("historical_artifacts_modified\": False", source)


if __name__ == "__main__":
    unittest.main()
