from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
import inspect
import json
import os
from pathlib import Path
import shutil
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


def signature_for(relation: subject.CommonRelationAuthorityV1) -> dict[str, object]:
    return {
        "runtime_logic_family": "missing_expected_delayed_response",
        "selected_delay_horizon_seconds": relation.selected_horizon_seconds,
        "source": relation.source,
        "source_stability_reference": relation.historical_reference("source_stability_tolerance"),
        "source_step_direction": relation.source_direction,
        "source_threshold_reference": relation.historical_reference("source_step_threshold"),
        "target": relation.target,
        "target_response_direction": relation.target_direction,
        "target_scale_reference": relation.historical_reference("target_noise_scale"),
        "window_constant_references": {
            role: relation.historical_reference(role)
            for role in subject.UTILITY_NUMERIC_ROLES[3:]
        },
    }


def attacker_rehash_authority(
    authority: subject.NormalOnlyAuthorityDefinitionV1,
    field: str,
    value: object,
) -> subject.NormalOnlyAuthorityDefinitionV1:
    first = replace(authority.relations[0], **{field: value})
    if field != "semantic_execution_hash":
        first = replace(first, semantic_execution_hash=stable_hash_v1(signature_for(first)))
    relations = (first, *authority.relations[1:])
    references = tuple(
        subject.new_reference_identity_v1(relation, role)
        for relation in relations
        for role in subject.UTILITY_NUMERIC_ROLES
    )
    historical = sorted(
        relation.historical_reference(role)
        for relation in relations
        for role in subject.UTILITY_NUMERIC_ROLES
    )
    binding_set_hash = stable_hash_v1(
        {"historical_utility_reference_bindings": historical, "count": 420}
    )
    definition_hash = stable_hash_v1(
        {
            "authority_version": subject.AUTHORITY_VERSION,
            "authority_lineage": subject.AUTHORITY_LINEAGE,
            "common42_authority_hash": subject.COMMON42_AUTHORITY_CHECK_HASH,
            "executable_equivalence_hash": subject.EXECUTABLE_EQUIVALENCE_HASH,
            "normal_input_identity_set_hash": subject.NORMAL_INPUT_IDENTITY_SET_HASH,
            "calibration_policy_version": subject.CALIBRATION_POLICY_VERSION,
            "relations": [relation.to_identity_dict() for relation in relations],
            "new_reference_identities": list(references),
        }
    )
    return replace(
        authority,
        relations=relations,
        reference_identities=references,
        utility_binding_set_hash=binding_set_hash,
        authority_definition_hash=definition_hash,
    )


class FocusedIndependentR1Reaudit(unittest.TestCase):
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
                    numeric: int | float = 3.0
                elif role == "source_stability_tolerance":
                    numeric = 0.3
                elif role == "target_noise_scale":
                    numeric = 0.1
                else:
                    numeric = constants[role]
                values[(relation.relation_binding_hash, role)] = numeric
        cls.values = values
        cls.registry = subject.build_private_registry_document_v1(cls.authority, values)

    def test_01_common_replay_rejects_seven_self_rehashed_mutations(self) -> None:
        relation = self.authority.relations[0]
        cases = {
            "relation_identity": "directional_relation:caller-substitution",
            "semantic_execution_hash": "f" * 64,
            "source": "FOREIGN_SOURCE",
            "target": "FOREIGN_TARGET",
            "source_direction": "step_down" if relation.source_direction == "step_up" else "step_up",
            "target_direction": "decrease" if relation.target_direction == "increase" else "increase",
            "selected_horizon_seconds": 5 if relation.selected_horizon_seconds != 5 else 10,
        }
        for field, value in cases.items():
            mutated = attacker_rehash_authority(self.authority, field, value)
            for operation in (
                lambda: subject.validate_canonical_common42_authority_v1(mutated),
                lambda: subject.build_private_registry_document_v1(mutated, self.values),
                lambda: subject.public_receipt_document_v1(
                    authority=mutated,
                    private_registry_hash=str(self.registry["artifact_hash"]),
                    builder_commit=subject.SCIENTIFIC_V1_COMMIT,
                    builder_git_blob="b" * 40,
                    builder_source_sha256="c" * 64,
                    execution_timestamp=TIMESTAMP,
                ),
            ):
                with self.subTest(field=field, operation=operation), self.assertRaises(
                    subject.NormalOnlyAuthorityV1Error
                ):
                    operation()

    def test_02_canonical_common_replay_matches_all_minimal_invariants(self) -> None:
        self.assertEqual(
            subject.validate_canonical_common42_authority_v1(self.authority),
            "6e7a286a37a5048a7887e8bea69f9ec0a9c3ff76c538cbb475e886fba276e4de",
        )
        self.assertEqual(len(self.authority.relations), 42)
        self.assertEqual(len({item.relation_identity for item in self.authority.relations}), 42)
        self.assertEqual(len(self.authority.reference_identities), 420)
        self.assertEqual(len(set(self.authority.reference_identities)), 420)
        self.assertEqual(
            self.authority.utility_binding_set_hash,
            "55c315b463b60d44f43dfc8058bd85cea2dd6ef865eba421c8953cf7a808a089",
        )

    def _materializer_attempt(
        self,
        private: Path,
        locator: Path,
        receipt: Path,
        environment: dict[str, str],
        *,
        expect_loader: bool = False,
    ) -> None:
        with mock.patch.dict(os.environ, environment, clear=True), mock.patch.object(
            subject, "validate_route_c_bindings_v1"
        ), mock.patch.object(subject, "validate_normal_input_authorities_v1"), mock.patch.object(
            subject, "build_common42_authority_v1", return_value=self.authority
        ), mock.patch.object(
            subject, "verify_builder_checkout_v1", return_value=("b" * 40, "c" * 64)
        ), mock.patch.object(
            subject,
            "load_verified_normal_features_v1",
            side_effect=subject.NormalOnlyAuthorityV1Error("synthetic normal identity gate"),
        ) as loader, mock.patch.object(subject, "_read_verified_feature_columns") as reader:
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
            self.assertEqual(loader.call_count, 1 if expect_loader else 0)
            reader.assert_not_called()

    def test_03_preflight_five_invalid_cases_have_zero_value_reads(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            private, locator, receipt = root / "private.json", root / "locator.json", root / "receipt.json"
            cases = (
                (private, locator, receipt, {}),
                (private, locator, receipt, {subject.PRIVATE_LOCATOR_ENV: str(root / "other.json")}),
                (ROOT / "inside-private.json", locator, receipt, {subject.PRIVATE_LOCATOR_ENV: str(ROOT / "inside-private.json")}),
                (private, ROOT / "inside-locator.json", receipt, {subject.PRIVATE_LOCATOR_ENV: str(private)}),
            )
            for case in cases:
                with self.subTest(case=str(case[:2])):
                    self._materializer_attempt(*case[:3], case[3])
            private.write_text("existing synthetic output", encoding="utf-8")
            self._materializer_attempt(
                private, locator, receipt, {subject.PRIVATE_LOCATOR_ENV: str(private)}
            )

    def test_04_valid_preflight_reaches_normal_identity_gate_only(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            private, locator, receipt = root / "private.json", root / "locator.json", root / "receipt.json"
            self._materializer_attempt(
                private, locator, receipt, {subject.PRIVATE_LOCATOR_ENV: str(private)},
                expect_loader=True,
            )

    def test_05_builder_authority_and_pending_execution_authorization(self) -> None:
        arbitrary = "e" * 40
        with self.assertRaises(subject.NormalOnlyAuthorityV1Error):
            subject.verify_builder_checkout_v1(ROOT, expected_builder_commit=arbitrary)
        self.assertNotIn(
            "expected_builder_commit",
            inspect.signature(subject.materialize_normal_only_authority_r1).parameters,
        )
        authorization = subject.canonical_materialization_execution_authorization_r1()
        self.assertEqual(authorization.scientific_v1_commit, "d58757b63d21519bc39398ddcf96be1682e8b01a")
        self.assertIsNone(authorization.authorized_control_commit)
        self.assertIsNone(authorization.focused_independent_reaudit_receipt_hash)
        self.assertFalse(authorization.materialization_authorized)
        with self.assertRaises(subject.NormalOnlyAuthorityV1Error):
            subject.validate_materialization_execution_authorization_r1(authorization)

        mutations = (
            ("authority_version", "CALLER_VERSION"),
            ("control_revision", "R9"),
            ("scientific_v1_commit", arbitrary),
            ("scientific_v1_source_blob", "e" * 40),
            ("scientific_v1_source_raw_sha256", "e" * 64),
            ("common42_authority_definition_hash", "e" * 64),
            ("calibration_policy_hash", "e" * 64),
            ("normal_input_identity_set_hash", "e" * 64),
            ("materialization_authorized", True),
        )
        for field, value in mutations:
            candidate = replace(authorization, **{field: value}, authorization_hash="0" * 64)
            candidate = replace(candidate, authorization_hash=stable_hash_v1(candidate.payload()))
            with self.subTest(field=field), self.assertRaises(subject.NormalOnlyAuthorityV1Error):
                subject.validate_materialization_execution_authorization_r1(
                    candidate, require_materialization_authorized=False
                )

        arbitrary_control = replace(
            authorization,
            authorized_control_commit="e" * 40,
            authorized_control_source_blob="d" * 40,
            authorized_control_source_raw_sha256="c" * 64,
            focused_independent_reaudit_receipt_hash="b" * 64,
            materialization_authorized=True,
            authorization_hash="0" * 64,
        )
        arbitrary_control = replace(
            arbitrary_control, authorization_hash=stable_hash_v1(arbitrary_control.payload())
        )
        with self.assertRaises(subject.NormalOnlyAuthorityV1Error):
            subject.validate_materialization_execution_authorization_r1(arbitrary_control)

    def _receipt(self) -> dict[str, object]:
        return subject.public_receipt_document_v1(
            authority=self.authority,
            private_registry_hash=str(self.registry["artifact_hash"]),
            builder_commit=subject.SCIENTIFIC_V1_COMMIT,
            builder_git_blob="b" * 40,
            builder_source_sha256="c" * 64,
            execution_timestamp=TIMESTAMP,
        )

    def test_06_receipt_exact_closed_schema_and_public_boundary(self) -> None:
        receipt = self._receipt()
        self.assertEqual(set(receipt), subject.PUBLIC_RECEIPT_ALLOWED_KEYS_V1)
        for field, value in (
            ("synthetic_threshold_preimage", 1.5),
            ("debug_value", 2.0),
            ("numeric_summary", {"count": 1}),
            ("calibration_preview", "preview"),
            ("raw_values", [1.0]),
            ("private_path_backup", "C:/private/authority.json"),
            ("random_unknown_field", True),
        ):
            mutated = deepcopy(receipt)
            mutated[field] = value
            rehash(mutated)
            with self.subTest(field=field), self.assertRaises(subject.NormalOnlyAuthorityV1Error):
                subject.validate_public_receipt_v1(mutated, self.authority)
        for parent in ("validation_counts", "construction_provenance", "normal_input_identities"):
            mutated = deepcopy(receipt)
            target = mutated[parent][0] if parent == "normal_input_identities" else mutated[parent]
            target["unknown_nested"] = 1
            rehash(mutated)
            with self.subTest(parent=parent), self.assertRaises(subject.NormalOnlyAuthorityV1Error):
                subject.validate_public_receipt_v1(mutated, self.authority)
        serialized = json.dumps(receipt, sort_keys=True).lower()
        for forbidden in ("numeric_value", "raw_values", "label_values", "credential", "api_key"):
            self.assertNotIn(forbidden, serialized)
        self.assertFalse(subject._contains_absolute_path_value(receipt))

    def _finalized_custody(self, root: Path) -> tuple[Path, Path, Path]:
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
            subject.validate_finalized_authority_v1(
                authority=self.authority, private_destination=private,
                local_locator_manifest=locator, public_receipt_path=receipt,
                repository_root=ROOT,
            )
        return private, locator, receipt

    def test_07_locator_file_path_outside_git_is_replayed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            private, locator, receipt = self._finalized_custody(Path(directory))
            document = json.loads(locator.read_text(encoding="utf-8"))
            self.assertNotIn(ROOT.resolve(), Path(document["absolute_private_authority_path"]).resolve().parents)
            with tempfile.TemporaryDirectory(dir=ROOT) as inside_directory:
                copied = Path(inside_directory) / "locator.json"
                shutil.copyfile(locator, copied)
                with mock.patch.dict(os.environ, {subject.PRIVATE_LOCATOR_ENV: str(private)}), self.assertRaises(
                    subject.NormalOnlyAuthorityV1Error
                ):
                    subject.validate_finalized_authority_v1(
                        authority=self.authority, private_destination=private,
                        local_locator_manifest=copied, public_receipt_path=receipt,
                        repository_root=ROOT,
                    )
            with mock.patch.object(Path, "is_symlink", return_value=True), self.assertRaises(
                subject.NormalOnlyAuthorityV1Error
            ):
                subject.validate_local_locator_manifest_file_v1(locator, repository_root=ROOT)

    def test_08_locator_receipt_and_control_mutations_all_reject(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            private, locator, receipt = self._finalized_custody(Path(directory))
            original_locator = locator.read_text(encoding="utf-8")
            original_receipt = receipt.read_text(encoding="utf-8")
            locator_cases = (
                ("scientific_v1_commit", "e" * 40),
                ("builder_commit", "e" * 40),
                ("control_source_commit", "e" * 40),
                ("control_source_git_blob", "e" * 40),
                ("control_source_raw_sha256", "e" * 64),
            )
            receipt_cases = locator_cases
            with mock.patch.dict(os.environ, {subject.PRIVATE_LOCATOR_ENV: str(private)}):
                for field, value in locator_cases:
                    document = json.loads(original_locator)
                    document[field] = value
                    rehash(document)
                    locator.write_text(json.dumps(document), encoding="utf-8")
                    with self.subTest(kind="locator", field=field), self.assertRaises(subject.NormalOnlyAuthorityV1Error):
                        subject.validate_finalized_authority_v1(
                            authority=self.authority, private_destination=private,
                            local_locator_manifest=locator, public_receipt_path=receipt,
                            repository_root=ROOT,
                        )
                    locator.write_text(original_locator, encoding="utf-8")
                for field, value in receipt_cases:
                    document = json.loads(original_receipt)
                    document[field] = value
                    rehash(document)
                    receipt.write_text(json.dumps(document), encoding="utf-8")
                    with self.subTest(kind="receipt", field=field), self.assertRaises(subject.NormalOnlyAuthorityV1Error):
                        subject.validate_finalized_authority_v1(
                            authority=self.authority, private_destination=private,
                            local_locator_manifest=locator, public_receipt_path=receipt,
                            repository_root=ROOT,
                        )
                    receipt.write_text(original_receipt, encoding="utf-8")

        authorization = subject.canonical_materialization_execution_authorization_r1()
        for field, value in (
            ("authorized_control_commit", "e" * 40),
            ("authorized_control_source_blob", "e" * 40),
            ("authorized_control_source_raw_sha256", "e" * 64),
        ):
            mutated = replace(authorization, **{field: value}, authorization_hash="0" * 64)
            mutated = replace(mutated, authorization_hash=stable_hash_v1(mutated.payload()))
            with self.subTest(kind="authorization", field=field), self.assertRaises(subject.NormalOnlyAuthorityV1Error):
                subject.validate_materialization_execution_authorization_r1(
                    mutated, require_materialization_authorized=False
                )

    def test_09_minimal_scientific_and_access_boundaries(self) -> None:
        self.assertEqual(subject.COMMON_RELATION_COUNT, 42)
        self.assertEqual(subject.UTILITY_NUMERIC_REFERENCE_COUNT, 420)
        self.assertEqual(len(subject.HISTORICAL_MANIFEST_ROLES) * 42, 462)
        self.assertEqual(
            set(subject.HISTORICAL_MANIFEST_ROLES) - set(subject.UTILITY_NUMERIC_ROLES),
            {"selected_delay_horizon_seconds"},
        )
        self.assertEqual(subject.CANONICAL_AUTHORITY_DEFINITION_HASH, "6e7a286a37a5048a7887e8bea69f9ec0a9c3ff76c538cbb475e886fba276e4de")
        self.assertEqual(subject.CALIBRATION_POLICY_HASH, "4f2622050637e3e83205dec59400fa6bf9ed2bd1a41f6b8ceb1900dc9f69b881")
        self.assertEqual(subject.EXECUTABLE_EQUIVALENCE_HASH, "3efdce159bc5ac39825d4e4654428237e47205307f83aae7a133db6c5789f60f")
        self.assertEqual(subject.NORMAL_TRAIN1_IDENTITY.sha256, "53007b0ba604fbf338e7ac2e08cd81d874b5d1388f3aecb213ddcba5bf2bec4a")
        self.assertEqual(subject.NORMAL_TRAIN2_IDENTITY.sha256, "0e520e82bf78a661ab19ce4967f3c766bd809820f457a9c90c365102d4534c56")
        self.assertFalse(subject.T2_UTILITY_SCOPE_AUTHORIZED)
        self.assertFalse(subject.R1_MATERIALIZATION_AUTHORIZED)


if __name__ == "__main__":
    unittest.main()
