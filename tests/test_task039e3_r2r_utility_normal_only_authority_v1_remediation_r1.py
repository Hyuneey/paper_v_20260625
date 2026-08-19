from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from paperworks.v6.common import stable_hash_v1
import paperworks.v6.task039e3_r2r_utility_normal_only_authority_v1 as subject


ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "docs" / "task_reports"
TIMESTAMP = "2026-08-19T00:00:00Z"


def load(name: str) -> dict[str, object]:
    return json.loads((REPORTS / name).read_text(encoding="utf-8"))


def rehash(document: dict[str, object]) -> None:
    document["artifact_hash"] = stable_hash_v1(
        {key: value for key, value in document.items() if key != "artifact_hash"}
    )


class NormalOnlyAuthorityRemediationR1Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.authority = subject.build_common42_authority_v1(
            load("TASK-039E3_R2R_UTILITY_PROTOCOL_EXECUTABLE_EQUIVALENCE.json"),
            load("TASK-039E1_CONSTRUCTION_EVIDENCE_MANIFEST.json"),
        )
        constants: dict[str, int | float] = {
            "source_pre_window_seconds": 5,
            "source_post_window_seconds": 5,
            "minimum_source_stability_fraction": 0.8,
            "source_refractory_seconds": 10,
            "cross_source_isolation_radius_seconds": 2,
            "target_baseline_window_seconds": 5,
            "target_response_window_seconds": 3,
        }
        values: dict[tuple[str, str], int | float] = {}
        for relation in cls.authority.relations:
            for role in subject.UTILITY_NUMERIC_ROLES:
                if role == "source_step_threshold":
                    value: int | float = 5.0
                elif role == "source_stability_tolerance":
                    value = 0.5
                elif role == "target_noise_scale":
                    value = 0.1
                else:
                    value = constants[role]
                values[(relation.relation_binding_hash, role)] = value
        cls.registry = subject.build_private_registry_document_v1(cls.authority, values)

    def test_common_authority_replay_rejects_all_seven_semantic_mutations(self) -> None:
        first = self.authority.relations[0]
        cases = {
            "relation_identity": "FOREIGN_RELATION",
            "semantic_execution_hash": "f" * 64,
            "source": "FOREIGN_SOURCE",
            "target": "FOREIGN_TARGET",
            "source_direction": "decrease" if first.source_direction == "increase" else "increase",
            "target_direction": "decrease" if first.target_direction == "increase" else "increase",
            "selected_horizon_seconds": 999,
        }
        for field, value in cases.items():
            mutated_relation = replace(first, **{field: value})
            mutated = replace(
                self.authority,
                relations=(mutated_relation, *self.authority.relations[1:]),
            )
            with self.subTest(field=field), self.assertRaises(subject.NormalOnlyAuthorityV1Error):
                subject.validate_canonical_common42_authority_v1(mutated)

    def test_definition_and_reference_replay_are_exact(self) -> None:
        self.assertEqual(
            subject.validate_canonical_common42_authority_v1(self.authority),
            subject.CANONICAL_AUTHORITY_DEFINITION_HASH,
        )
        self.assertEqual(len(self.authority.relations), 42)
        self.assertEqual(len(self.authority.reference_identities), 420)
        self.assertEqual(
            self.authority.utility_binding_set_hash,
            subject.CANONICAL_UTILITY_BINDING_SET_HASH,
        )

    def _assert_materializer_rejects_before_loader(
        self,
        *,
        private: Path,
        locator: Path,
        receipt: Path,
        environment: dict[str, str],
    ) -> None:
        with mock.patch.dict(os.environ, environment, clear=True), mock.patch.object(
            subject, "load_verified_normal_features_v1"
        ) as loader:
            with self.assertRaises(subject.NormalOnlyAuthorityV1Error):
                subject.materialize_normal_only_authority_v1(
                    feasibility_audit={}, dependency_matrix={}, common42_check={},
                    dataset_manifest={}, d1_data_access_audit={}, executable_equivalence={},
                    evidence_manifest={}, train1_path=private.parent / "train1.csv",
                    train2_path=private.parent / "train2.csv", private_destination=private,
                    local_locator_manifest=locator, public_receipt_path=receipt,
                    repository_root=ROOT, expected_builder_commit=subject.SCIENTIFIC_V1_COMMIT,
                    execution_timestamp=TIMESTAMP,
                )
            loader.assert_not_called()

    def test_output_preflight_rejects_five_cases_before_value_read(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            private, locator, receipt = root / "private.json", root / "locator.json", root / "receipt.json"
            cases = [
                (private, locator, receipt, {}),
                (private, locator, receipt, {subject.PRIVATE_LOCATOR_ENV: str(root / "other.json")}),
                (ROOT / "inside-private.json", locator, receipt, {subject.PRIVATE_LOCATOR_ENV: str(ROOT / "inside-private.json")}),
                (private, ROOT / "inside-locator.json", receipt, {subject.PRIVATE_LOCATOR_ENV: str(private)}),
            ]
            for case in cases:
                with self.subTest(case=str(case[0:2])):
                    self._assert_materializer_rejects_before_loader(
                        private=case[0], locator=case[1], receipt=case[2], environment=case[3]
                    )
            private.write_text("existing", encoding="utf-8")
            self._assert_materializer_rejects_before_loader(
                private=private, locator=locator, receipt=receipt,
                environment={subject.PRIVATE_LOCATOR_ENV: str(private)},
            )

    def test_builder_commit_is_pinned_and_real_r1_authorization_is_pending(self) -> None:
        with self.assertRaises(subject.NormalOnlyAuthorityV1Error):
            subject.verify_builder_checkout_v1(ROOT, expected_builder_commit="e" * 40)
        authorization = subject.canonical_materialization_execution_authorization_r1()
        self.assertEqual(authorization.scientific_v1_commit, subject.SCIENTIFIC_V1_COMMIT)
        self.assertEqual(authorization.control_revision, "R1")
        self.assertFalse(authorization.materialization_authorized)
        subject.validate_materialization_execution_authorization_r1(
            authorization, require_materialization_authorized=False
        )
        with self.assertRaises(subject.NormalOnlyAuthorityV1Error):
            subject.validate_materialization_execution_authorization_r1(authorization)

    def test_self_consistent_caller_authorization_is_rejected(self) -> None:
        canonical = subject.canonical_materialization_execution_authorization_r1()
        for field, value in (
            ("authority_version", "CALLER_VERSION"),
            ("scientific_v1_commit", "e" * 40),
            ("scientific_v1_source_blob", "e" * 40),
            ("common42_authority_definition_hash", "e" * 64),
            ("calibration_policy_hash", "e" * 64),
            ("normal_input_identity_set_hash", "e" * 64),
            ("materialization_authorized", True),
        ):
            changed = replace(canonical, **{field: value}, authorization_hash="0" * 64)
            changed = replace(changed, authorization_hash=stable_hash_v1(changed.payload()))
            with self.subTest(field=field), self.assertRaises(subject.NormalOnlyAuthorityV1Error):
                subject.validate_materialization_execution_authorization_r1(
                    changed, require_materialization_authorized=False
                )

    def test_canonical_cli_exposes_no_caller_selected_builder_argument(self) -> None:
        argv: list[str] = []
        for name in (
            "feasibility-audit", "dependency-matrix", "common42-check",
            "dataset-manifest", "d1-data-access-audit", "executable-equivalence",
            "evidence-manifest", "train1", "train2", "private-destination",
            "local-locator-manifest", "public-receipt", "repository-root",
        ):
            argv.extend((f"--{name}", "unused"))
        argv.extend(("--execution-timestamp", TIMESTAMP, "--expected-builder-commit", "e" * 40))
        with mock.patch("sys.stderr"), self.assertRaises(SystemExit):
            subject.main(argv)

    def test_public_receipt_is_closed_against_six_unknown_field_names(self) -> None:
        receipt = subject.public_receipt_document_v1(
            authority=self.authority,
            private_registry_hash=str(self.registry["artifact_hash"]),
            builder_commit=subject.SCIENTIFIC_V1_COMMIT,
            builder_git_blob="b" * 40,
            builder_source_sha256="c" * 64,
            execution_timestamp=TIMESTAMP,
        )
        self.assertEqual(set(receipt), subject.PUBLIC_RECEIPT_ALLOWED_KEYS_V1)
        self.assertEqual(len(receipt), 33)
        for field, value in (
            ("synthetic_threshold_preimage", 123.456), ("debug_value", 1.0),
            ("value_preview", [1.0]), ("numeric_summary", {"x": 1}),
            ("calibration_preview", "hidden"), ("private_path_backup", "C:/private/value.json"),
        ):
            mutated = deepcopy(receipt)
            mutated[field] = value
            rehash(mutated)
            with self.subTest(field=field), self.assertRaises(subject.NormalOnlyAuthorityV1Error):
                subject.validate_public_receipt_v1(mutated, self.authority)

    def test_public_receipt_nested_types_are_strict(self) -> None:
        receipt = subject.public_receipt_document_v1(
            authority=self.authority, private_registry_hash=str(self.registry["artifact_hash"]),
            builder_commit=subject.SCIENTIFIC_V1_COMMIT, builder_git_blob="b" * 40,
            builder_source_sha256="c" * 64, execution_timestamp=TIMESTAMP,
        )
        receipt["record_count"] = 420.0
        rehash(receipt)
        with self.assertRaises(subject.NormalOnlyAuthorityV1Error):
            subject.validate_public_receipt_v1(receipt, self.authority)

    def test_locator_file_inside_git_and_builder_cross_binding_fail(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            private, locator, receipt = root / "private.json", root / "locator.json", root / "receipt.json"
            with mock.patch.dict(os.environ, {subject.PRIVATE_LOCATOR_ENV: str(private)}):
                subject.finalize_materialization_atomically_v1(
                    registry=self.registry, authority=self.authority,
                    private_destination=private, local_locator_manifest=locator,
                    public_receipt_path=receipt, repository_root=ROOT,
                    builder_commit=subject.SCIENTIFIC_V1_COMMIT,
                    builder_git_blob="b" * 40, builder_source_sha256="c" * 64,
                    execution_timestamp=TIMESTAMP,
                )
                with tempfile.TemporaryDirectory(dir=ROOT) as inside:
                    copied = Path(inside) / "locator.json"
                    copied.write_bytes(locator.read_bytes())
                    with self.assertRaises(subject.NormalOnlyAuthorityV1Error):
                        subject.validate_local_locator_manifest_file_v1(copied, repository_root=ROOT)
                document = json.loads(locator.read_text(encoding="utf-8"))
                document["builder_commit"] = "e" * 40
                rehash(document)
                locator.write_text(json.dumps(document), encoding="utf-8")
                with self.assertRaises(subject.NormalOnlyAuthorityV1Error):
                    subject.validate_finalized_authority_v1(
                        authority=self.authority, private_destination=private,
                        local_locator_manifest=locator, public_receipt_path=receipt,
                        repository_root=ROOT,
                    )

    def test_scientific_invariants_are_unchanged(self) -> None:
        self.assertEqual(subject.CANONICAL_AUTHORITY_DEFINITION_HASH, "6e7a286a37a5048a7887e8bea69f9ec0a9c3ff76c538cbb475e886fba276e4de")
        self.assertEqual(subject.CALIBRATION_POLICY_HASH, "4f2622050637e3e83205dec59400fa6bf9ed2bd1a41f6b8ceb1900dc9f69b881")
        self.assertEqual(subject.NORMAL_TRAIN1_IDENTITY.sha256, "53007b0ba604fbf338e7ac2e08cd81d874b5d1388f3aecb213ddcba5bf2bec4a")
        self.assertEqual(subject.NORMAL_TRAIN2_IDENTITY.sha256, "0e520e82bf78a661ab19ce4967f3c766bd809820f457a9c90c365102d4534c56")
        self.assertFalse(subject.T2_UTILITY_SCOPE_AUTHORIZED)
        self.assertFalse(subject.HISTORICAL_E1_IDENTITY_RESTORED)
        self.assertFalse(subject.HISTORICAL_NUMERIC_IDENTITY_RESTORED)


if __name__ == "__main__":
    unittest.main()
