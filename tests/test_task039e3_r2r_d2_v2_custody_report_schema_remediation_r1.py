from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict, replace
import unittest

from scripts import remediate_task039e3_r2r_d2_v2_custody_report_schema_r1 as subject


class CustodyReportSchemaRemediationR1Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.common = {
            "schema_version": "1.0.0",
            "task_id": "SYNTHETIC",
            "created_at_utc": "2026-08-23T00:00:00Z",
            "status": "synthetic",
        }

    def seal(self, payload: dict[str, object]) -> dict[str, object]:
        return subject.seal_artifact(
            self.common,
            "SyntheticArtifactV1",
            payload,
            allowed_semantic_fields=frozenset(payload),
        )

    def test_exact_frozen_identities(self) -> None:
        self.assertEqual(subject.FUSION_EVIDENCE_SHA256, "9fd5563b76cb4af0cf68383e1e2b9d10da9e6fd35a667d4a68d6eb5f8db2e8cb")
        self.assertEqual(subject.METRIC_EVIDENCE_SHA256, "3e3f20b5b1a9387cd3bed4ad17e4232e714cc588d7df1c2a37dfd69bcd1a8513")
        self.assertEqual(subject.COMBINED_PREDICTION_SHA256, "31035da56e140141917437df5b3473b803153621c7e1022830cccde52f61c0b3")
        self.assertEqual(subject.CUSTODY_MODULE_IDENTITY_SHA256, "c0e3faafdab0cb84e2f8e62b9380c243b0faee9ab38cc014de36fed5464d62e6")

    def test_reserved_self_hash_appears_exactly_once(self) -> None:
        artifact = self.seal({"semantic_value": 1})
        self.assertEqual(list(artifact).count(subject.SELF_HASH_FIELD), 1)
        self.assertEqual(subject.validate_sealed_artifact(artifact), artifact[subject.SELF_HASH_FIELD])

    def test_duplicate_json_keys_rejected_at_any_level(self) -> None:
        for raw in (b'{"x":1,"x":2}', b'{"outer":{"x":1,"x":2}}'):
            with self.subTest(raw=raw), self.assertRaises(subject.ReportSchemaError) as caught:
                subject.strict_json_loads(raw)
            self.assertEqual(caught.exception.code, subject.COLLISION_ERROR)

    def test_dataclass_alias_collision_rejected(self) -> None:
        fields = (
            subject.SchemaFieldR1("first", "same"),
            subject.SchemaFieldR1("second", "same"),
        )
        with self.assertRaises(subject.ReportSchemaError):
            subject.validate_field_registry(fields)

    def test_reserved_payload_hash_collision_rejected(self) -> None:
        for name in (subject.SELF_HASH_FIELD, "bundle_artifact_sha256", "receipt_artifact_sha256"):
            with self.subTest(name=name), self.assertRaises(subject.ReportSchemaError):
                subject.validate_field_registry((subject.SchemaFieldR1("payload", name),))

    def test_unknown_field_rejected(self) -> None:
        with self.assertRaises(subject.ReportSchemaError):
            subject.seal_artifact(
                self.common,
                "SyntheticArtifactV1",
                {"known": 1, "unknown": 2},
                allowed_semantic_fields=frozenset({"known"}),
            )

    def test_private_payload_and_path_rejected(self) -> None:
        with self.assertRaises(subject.ReportSchemaError):
            self.seal({"private_payload": "secret"})
        with self.assertRaises(subject.ReportSchemaError):
            self.seal({"note": "C:\\private\\artifact.json"})

    def test_self_hash_changes_with_semantic_payload(self) -> None:
        first = self.seal({"semantic_value": 1})
        second = self.seal({"semantic_value": 2})
        self.assertNotEqual(first[subject.SELF_HASH_FIELD], second[subject.SELF_HASH_FIELD])

    def test_post_hash_overwrite_rejected(self) -> None:
        artifact = self.seal({"semantic_value": 1})
        with self.assertRaises(subject.ReportSchemaError):
            subject.validate_sealed_artifact({**artifact, subject.SELF_HASH_FIELD: "0" * 64})

    def test_role_specific_referenced_hashes_preserved(self) -> None:
        completion = subject.D2V2PrivateCustodyBindingRemediationCompletionR1()
        reports, _ = subject.build_reports(
            completion,
            created_at_utc="2026-08-23T00:00:00Z",
            independent_attacks=20,
            accepted_invalid=0,
        )
        fusion = reports["FUSION_EVIDENCE_IDENTITY"]
        metric = reports["METRIC_EVIDENCE_IDENTITY"]
        self.assertEqual(fusion["fusion_evidence_sha256"], subject.FUSION_EVIDENCE_SHA256)
        self.assertEqual(metric["metric_evidence_sha256"], subject.METRIC_EVIDENCE_SHA256)
        self.assertNotIn("fusion_evidence_sha256", metric)
        self.assertEqual(list(fusion).count(subject.SELF_HASH_FIELD), 1)

    def test_wrong_authorities_and_namespaces_rejected(self) -> None:
        completion = subject.D2V2PrivateCustodyBindingRemediationCompletionR1()
        mutations = (
            {"fusion_evidence_sha256": "0" * 64},
            {"metric_evidence_sha256": "0" * 64},
            {"combined_prediction_sha256": "0" * 64},
            {"original_custody_producer_identity_sha256": "0" * 64},
            {"fusion_logical_namespace_match": False},
            {"metric_logical_namespace_match": False},
            {"unknown_field_count": 1},
        )
        for mutation in mutations:
            with self.subTest(mutation=mutation), self.assertRaises(subject.ReportSchemaError):
                subject.validate_completion(replace(completion, **mutation))

    def test_reports_consume_immutable_completion_without_validation_rerun(self) -> None:
        completion = subject.D2V2PrivateCustodyBindingRemediationCompletionR1()
        before = asdict_for_test(completion)
        reports, markdown = subject.build_reports(
            completion,
            created_at_utc="2026-08-23T00:00:00Z",
            independent_attacks=20,
            accepted_invalid=0,
        )
        self.assertEqual(asdict_for_test(completion), before)
        self.assertEqual(reports["INDEPENDENT_AUDIT"]["private_identity_revalidations"], 0)
        self.assertNotIn(b"private artifact path", markdown.lower())

    def test_bundle_and_receipt_generation_do_not_mutate_reports(self) -> None:
        completion = subject.D2V2PrivateCustodyBindingRemediationCompletionR1()
        reports, markdown = subject.build_reports(
            completion,
            created_at_utc="2026-08-23T00:00:00Z",
            independent_attacks=20,
            accepted_invalid=0,
        )
        snapshot = deepcopy(reports)
        for document in reports.values():
            subject.validate_sealed_artifact(document)
        subject.audit_markdown_bytes(markdown, reports)
        self.assertEqual(reports, snapshot)

    def test_canonical_raw_json_roundtrip(self) -> None:
        artifact = self.seal({"semantic_value": 1})
        raw = subject.canonical_json_bytes(artifact, pretty=True)
        subject.audit_json_bytes(raw, artifact)

    def test_forbidden_operations_are_fixed_at_zero(self) -> None:
        completion = subject.D2V2PrivateCustodyBindingRemediationCompletionR1()
        for field in (
            "scientific_prediction_parses", "source_map_scientific_parses",
            "native_horizon_scientific_parses", "combined_prediction_scientific_parses",
            "label_parses", "metric_computations", "test1_feature_accesses",
            "test2_accesses", "authoritative_scientific_executions",
        ):
            with self.subTest(field=field), self.assertRaises(subject.ReportSchemaError):
                subject.validate_completion(replace(completion, **{field: 1}))

    def test_adversarial_audit_closes(self) -> None:
        attacks, accepted = subject.adversarial_audit()
        self.assertGreaterEqual(attacks, 16)
        self.assertEqual(accepted, 0)


def asdict_for_test(value: object) -> dict[str, object]:
    return asdict(value)  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
