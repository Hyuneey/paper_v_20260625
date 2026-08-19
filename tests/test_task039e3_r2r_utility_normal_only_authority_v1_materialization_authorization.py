from __future__ import annotations

from dataclasses import replace
import inspect
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest import mock

from paperworks.v6.common import stable_hash_v1
from paperworks.v6 import task039e3_r2r_utility_normal_only_authority_v1 as subject


ROOT = Path(__file__).resolve().parents[1]


def rehash(document: dict[str, object]) -> dict[str, object]:
    document["artifact_hash"] = stable_hash_v1(
        {key: value for key, value in document.items() if key != "artifact_hash"}
    )
    return document


def external_document() -> dict[str, object]:
    document = subject.canonical_materialization_execution_authorization_r1().to_dict()
    document.update(
        {
            "authorized_control_commit": "a" * 40,
            "authorized_control_source_blob": "b" * 40,
            "authorized_control_source_raw_sha256": "c" * 64,
            "focused_independent_reaudit_receipt_hash": "d" * 64,
            "materialization_authorized": True,
        }
    )
    return rehash(document)


def interface_audit(
    authorization: subject.MaterializationExecutionAuthorizationR1,
) -> dict[str, object]:
    document: dict[str, object] = {
        "artifact_type": subject.MATERIALIZATION_AUTHORIZATION_INTERFACE_AUDIT_ARTIFACT_TYPE,
        "schema_version": subject.MATERIALIZATION_AUTHORIZATION_SCHEMA_VERSION,
        "status": subject.MATERIALIZATION_AUTHORIZATION_INTERFACE_AUDIT_STATUS,
        "interface_commit": authorization.authorized_control_commit,
        "interface_source_git_blob": authorization.authorized_control_source_blob,
        "interface_source_raw_sha256": authorization.authorized_control_source_raw_sha256,
        "independent_audit_commit": "e" * 40,
        "independent_tests_passed": 10,
        "independent_tests_failed": 0,
        "scientific_change": False,
        "authorization_control_change": True,
        "protocol_audit_closure_hash": subject.PROTOCOL_AUDIT_CLOSURE_HASH,
        "protocol_audit_receipt_hash": subject.PROTOCOL_AUDIT_RECEIPT_HASH,
        "remaining_blockers": 0,
        "access_counters": {
            "hai_normal_value_accesses": 0,
            "hai_test_value_accesses": 0,
            "hai_label_accesses": 0,
            "train3_value_accesses": 0,
            "utility_computations": 0,
            "provider_calls": 0,
            "api_key_access": False,
            "scientific_llm_calls": 0,
        },
    }
    return rehash(document)


class MaterializationAuthorizationInterfaceTests(unittest.TestCase):
    def test_pending_in_source_authority_stays_non_authoritative(self) -> None:
        pending = subject.canonical_materialization_execution_authorization_r1()
        self.assertIsNone(subject.AUTHORIZED_R1_CONTROL_COMMIT)
        self.assertIsNone(subject.AUTHORIZED_R1_CONTROL_SOURCE_BLOB)
        self.assertIsNone(subject.AUTHORIZED_R1_CONTROL_SOURCE_RAW_SHA256)
        self.assertIsNone(subject.AUTHORIZED_R1_FOCUSED_REAUDIT_RECEIPT_HASH)
        self.assertFalse(subject.R1_MATERIALIZATION_AUTHORIZED)
        self.assertFalse(pending.materialization_authorized)
        with self.assertRaises(subject.NormalOnlyAuthorityV1Error):
            subject.validate_materialization_execution_authorization_r1(pending)

    def test_external_document_has_exact_closed_schema_and_strict_types(self) -> None:
        canonical = external_document()
        authorization = subject.materialization_execution_authorization_from_document_r1(
            canonical
        )
        self.assertTrue(authorization.materialization_authorized)
        self.assertEqual(authorization.scope, subject.MATERIALIZATION_AUTHORIZATION_SCOPE)
        for mutation in (
            {"unknown": "field"},
            {"materialization_authorized": 1},
            {"materialization_authorized": 1.0},
            {"materialization_authorized": "true"},
            {"materialization_authorized": None},
            {"train3_access": 0},
            {"test_access": 0.0},
            {"label_access": "false"},
            {"provider_access": None},
            {"utility_execution": []},
        ):
            changed = json.loads(json.dumps(canonical))
            changed.update(mutation)
            rehash(changed)
            with self.subTest(mutation=mutation), self.assertRaises(
                subject.NormalOnlyAuthorityV1Error
            ):
                subject.materialization_execution_authorization_from_document_r1(changed)

    def test_every_frozen_scientific_and_scope_mutation_rejects(self) -> None:
        canonical = external_document()
        mutations = {
            "authority_version": "OTHER",
            "control_revision": "R2",
            "scientific_v1_commit": "f" * 40,
            "scientific_v1_source_blob": "f" * 40,
            "scientific_v1_source_raw_sha256": "f" * 64,
            "common42_authority_definition_hash": "f" * 64,
            "calibration_policy_hash": "f" * 64,
            "executable_equivalence_hash": "f" * 64,
            "normal_input_identity_set_hash": "f" * 64,
            "protocol_audit_closure_hash": "f" * 64,
            "protocol_audit_receipt_hash": "f" * 64,
            "scope": "BROADER_SCOPE",
            "normal_train1_sha256": "f" * 64,
            "normal_train2_sha256": "f" * 64,
            "train3_access": True,
            "test_access": True,
            "label_access": True,
            "provider_access": True,
            "utility_execution": True,
            "materialization_authorized": False,
        }
        for field, value in mutations.items():
            changed = json.loads(json.dumps(canonical))
            changed[field] = value
            rehash(changed)
            with self.subTest(field=field), self.assertRaises(
                subject.NormalOnlyAuthorityV1Error
            ):
                subject.materialization_execution_authorization_from_document_r1(changed)

    def test_arbitrary_self_hashed_control_is_not_in_memory_authority(self) -> None:
        authorization = subject.materialization_execution_authorization_from_document_r1(
            external_document()
        )
        with self.assertRaises(subject.NormalOnlyAuthorityV1Error):
            subject.validate_materialization_execution_authorization_r1(authorization)
        with self.assertRaises(subject.NormalOnlyAuthorityV1Error):
            subject.verify_authorized_builder_checkout_r1(ROOT, authorization)

    def test_interface_audit_exactly_binds_control_and_zero_access(self) -> None:
        authorization = subject.materialization_execution_authorization_from_document_r1(
            external_document()
        )
        document = interface_audit(authorization)
        authorization = replace(
            authorization,
            focused_independent_reaudit_receipt_hash=str(document["artifact_hash"]),
            authorization_hash="0" * 64,
        )
        authorization = replace(
            authorization, authorization_hash=stable_hash_v1(authorization.payload())
        )
        self.assertEqual(
            subject.validate_materialization_authorization_interface_audit_r1(
                document, authorization
            ),
            document["artifact_hash"],
        )
        for field, value in (
            ("interface_commit", "f" * 40),
            ("interface_source_git_blob", "f" * 40),
            ("interface_source_raw_sha256", "f" * 64),
            ("scientific_change", True),
            ("authorization_control_change", False),
            ("remaining_blockers", 1),
        ):
            changed = json.loads(json.dumps(document))
            changed[field] = value
            rehash(changed)
            with self.subTest(field=field), self.assertRaises(
                subject.NormalOnlyAuthorityV1Error
            ):
                subject.validate_materialization_authorization_interface_audit_r1(
                    changed, authorization
                )

    def test_canonical_materializer_accepts_no_caller_authorization_choice(self) -> None:
        parameters = inspect.signature(subject.materialize_normal_only_authority_r1).parameters
        self.assertNotIn("authorization", parameters)
        self.assertNotIn("authorization_path", parameters)
        self.assertNotIn("expected_builder_commit", parameters)
        with mock.patch.object(
            subject,
            "load_committed_materialization_execution_authorization_r1",
            side_effect=subject.NormalOnlyAuthorityV1Error("synthetic authorization stop"),
        ) as authorization_loader, mock.patch.object(
            subject, "load_verified_normal_features_v1"
        ) as feature_loader:
            with self.assertRaises(subject.NormalOnlyAuthorityV1Error):
                subject.materialize_normal_only_authority_r1(
                    feasibility_audit={}, dependency_matrix={}, common42_check={},
                    dataset_manifest={}, d1_data_access_audit={}, executable_equivalence={},
                    evidence_manifest={}, train1_path=Path("train1.csv"),
                    train2_path=Path("train2.csv"), private_destination=Path("private.json"),
                    local_locator_manifest=Path("locator.json"),
                    public_receipt_path=Path("receipt.json"), repository_root=ROOT,
                    execution_timestamp="2026-08-19T00:00:00+09:00",
                )
            authorization_loader.assert_called_once_with(ROOT)
            feature_loader.assert_not_called()

    def test_cli_checks_authorization_before_caller_metadata_documents(self) -> None:
        argv: list[str] = []
        for name in (
            "feasibility-audit", "dependency-matrix", "common42-check",
            "dataset-manifest", "d1-data-access-audit", "executable-equivalence",
            "evidence-manifest", "train1", "train2", "private-destination",
            "local-locator-manifest", "public-receipt", "repository-root",
        ):
            argv.extend((f"--{name}", "synthetic"))
        argv.extend(("--execution-timestamp", "2026-08-19T00:00:00+09:00"))
        with mock.patch.object(
            subject,
            "load_committed_materialization_execution_authorization_r1",
            side_effect=subject.NormalOnlyAuthorityV1Error("synthetic authorization stop"),
        ), mock.patch.object(subject, "_load_json_document") as metadata_loader:
            with self.assertRaises(subject.NormalOnlyAuthorityV1Error):
                subject.main(argv)
            metadata_loader.assert_not_called()

    def test_authorized_loader_derives_exact_common_feature_union(self) -> None:
        authorization = subject.materialization_execution_authorization_from_document_r1(
            external_document()
        )
        relation = subject.CommonRelationAuthorityV1(
            relation_identity="relation",
            relation_binding_hash="1" * 64,
            semantic_execution_hash="2" * 64,
            source="P1_SOURCE",
            target="P1_TARGET",
            source_direction="increase",
            target_direction="increase",
            selected_horizon_seconds=1,
            historical_reference_pairs=tuple(),
        )
        authority = subject.NormalOnlyAuthorityDefinitionV1(
            relations=(relation,),
            reference_identities=tuple(),
            utility_binding_set_hash="3" * 64,
            authority_definition_hash=subject.CANONICAL_AUTHORITY_DEFINITION_HASH,
        )
        with mock.patch.object(
            subject, "validate_canonical_common42_authority_v1"
        ), mock.patch.object(
            subject, "validate_materialization_execution_authorization_r1"
        ), mock.patch.object(
            subject, "load_verified_normal_features_v1", return_value=({}, {})
        ) as loader:
            subject._load_authorized_normal_features_r1(
                authority=authority,
                authorization=authorization,
                train1_path=Path("train1.csv"),
                train2_path=Path("train2.csv"),
            )
        self.assertEqual(
            loader.call_args.kwargs["required_features"],
            frozenset({"P1_SOURCE", "P1_TARGET"}),
        )

    def test_scientific_identity_constants_are_unchanged(self) -> None:
        self.assertEqual(subject.COMMON_RELATION_COUNT, 42)
        self.assertEqual(subject.UTILITY_NUMERIC_REFERENCE_COUNT, 420)
        self.assertEqual(
            subject.CANONICAL_AUTHORITY_DEFINITION_HASH,
            "6e7a286a37a5048a7887e8bea69f9ec0a9c3ff76c538cbb475e886fba276e4de",
        )
        self.assertEqual(
            subject.CALIBRATION_POLICY_HASH,
            "4f2622050637e3e83205dec59400fa6bf9ed2bd1a41f6b8ceb1900dc9f69b881",
        )
        self.assertEqual(
            subject.EXECUTABLE_EQUIVALENCE_HASH,
            "3efdce159bc5ac39825d4e4654428237e47205307f83aae7a133db6c5789f60f",
        )
        self.assertEqual(
            subject.NORMAL_INPUT_IDENTITY_SET_HASH,
            "cc502d87daf19a1511f868c1c767045a4457d505d195b0214f244d1910fe0cda",
        )
        self.assertFalse(subject.T2_UTILITY_SCOPE_AUTHORIZED)

    def test_frozen_calibration_dependencies_match_and_are_clean(self) -> None:
        for path, expected_blob, expected_raw in (
            (
                subject.RELATION_PROFILING_SOURCE,
                subject.RELATION_PROFILING_GIT_BLOB,
                subject.RELATION_PROFILING_RAW_SHA256,
            ),
            (
                subject.E1_MATERIALIZATION_SOURCE,
                subject.E1_MATERIALIZATION_GIT_BLOB,
                subject.E1_MATERIALIZATION_RAW_SHA256,
            ),
        ):
            blob = subprocess.run(
                ["git", "-C", str(ROOT), "rev-parse", f"HEAD:{path}"],
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
            raw = subprocess.run(
                ["git", "-C", str(ROOT), "show", f"HEAD:{path}"],
                check=True,
                capture_output=True,
            ).stdout
            dirty = subprocess.run(
                ["git", "-C", str(ROOT), "status", "--porcelain", "--", path],
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
            with self.subTest(path=path):
                self.assertEqual(blob, expected_blob)
                self.assertEqual(subject.sha256(raw).hexdigest(), expected_raw)
                self.assertEqual(dirty, "")


if __name__ == "__main__":
    unittest.main()
