from __future__ import annotations

from copy import deepcopy
import json
import math
import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from paperworks.v6.common import canonical_json_v1, stable_hash_v1
import paperworks.v6.task039e3_r2r_utility_normal_only_authority_v1 as authority_v1
from paperworks.v6.task039e3_r2r_utility_normal_only_authority_v1 import (
    AUTHORITY_LINEAGE,
    AUTHORITY_VERSION,
    CALIBRATION_ROLE_SPECS,
    COMMON_RELATION_COUNT,
    EXECUTABLE_EQUIVALENCE_HASH,
    HISTORICAL_E1_IDENTITY_RESTORED,
    HISTORICAL_NUMERIC_IDENTITY_RESTORED,
    NORMAL_INPUT_IDENTITIES,
    NORMAL_TRAIN1_IDENTITY,
    NORMAL_TRAIN2_IDENTITY,
    PRIVATE_LOCATOR_ENV,
    T2_UTILITY_SCOPE_AUTHORIZED,
    UTILITY_NUMERIC_REFERENCE_COUNT,
    UTILITY_NUMERIC_ROLES,
    NormalOnlyAuthorityV1Error,
    authority_snapshot_v1,
    build_common42_authority_v1,
    build_private_registry_document_v1,
    calibrate_all_role_values_v1,
    derive_source_parameters_normal_only_v1,
    derive_target_scale_normal_only_v1,
    finalize_materialization_atomically_v1,
    new_reference_identity_v1,
    public_receipt_document_v1,
    validate_finalized_authority_v1,
    validate_local_locator_manifest_v1,
    validate_normal_input_authorities_v1,
    validate_private_registry_document_v1,
    validate_public_receipt_v1,
    validate_route_c_bindings_v1,
    load_verified_normal_features_v1,
)


ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "docs" / "task_reports"


def load(name: str) -> dict[str, object]:
    return json.loads((REPORTS / name).read_text(encoding="utf-8"))


def rehash(document: dict[str, object]) -> dict[str, object]:
    document["artifact_hash"] = stable_hash_v1(
        {key: value for key, value in document.items() if key != "artifact_hash"}
    )
    return document


WINDOWS: dict[str, int | float] = {
    "source_pre_window_seconds": 5,
    "source_post_window_seconds": 5,
    "minimum_source_stability_fraction": 0.8,
    "source_refractory_seconds": 10,
    "cross_source_isolation_radius_seconds": 2,
    "target_baseline_window_seconds": 5,
    "target_response_window_seconds": 3,
}


class NormalOnlyAuthorityV1Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.equivalence = load("TASK-039E3_R2R_UTILITY_PROTOCOL_EXECUTABLE_EQUIVALENCE.json")
        cls.manifest = load("TASK-039E1_CONSTRUCTION_EVIDENCE_MANIFEST.json")
        cls.authority = build_common42_authority_v1(cls.equivalence, cls.manifest)
        cls.role_values: dict[tuple[str, str], int | float] = {}
        for relation in cls.authority.relations:
            for role in UTILITY_NUMERIC_ROLES:
                if role == "source_step_threshold":
                    value: int | float = 5.0
                elif role == "source_stability_tolerance":
                    value = 0.5
                elif role == "target_noise_scale":
                    value = 1e-12
                else:
                    value = WINDOWS[role]
                cls.role_values[(relation.relation_binding_hash, role)] = value
        cls.registry = build_private_registry_document_v1(cls.authority, cls.role_values)

    def test_01_route_c_authorities_are_exact(self) -> None:
        validate_route_c_bindings_v1(
            load("TASK-039E3_R2R_UTILITY_AUTHORITY_RECONSTITUTION_FEASIBILITY_AUDIT.json"),
            load("TASK-039E3_R2R_UTILITY_AUTHORITY_DEPENDENCY_MATRIX.json"),
            load("TASK-039E3_R2R_UTILITY_COMMON42_AUTHORITY_CHECK.json"),
        )
        validate_normal_input_authorities_v1(
            load("TASK-039A_DATASET_MANIFEST_V2.json"),
            load("TASK-039D1_DATA_ACCESS_AUDIT.json"),
        )

    def test_02_common42_and_420_are_derived(self) -> None:
        self.assertEqual(len(self.authority.relations), COMMON_RELATION_COUNT)
        self.assertEqual(len(self.authority.reference_identities), UTILITY_NUMERIC_REFERENCE_COUNT)
        self.assertEqual(len(set(self.authority.reference_identities)), 420)
        self.assertEqual(self.equivalence["artifact_hash"], EXECUTABLE_EQUIVALENCE_HASH)

    def test_03_new_reference_identity_is_deterministic_and_value_independent(self) -> None:
        relation = self.authority.relations[0]
        observed = new_reference_identity_v1(relation, "source_step_threshold")
        self.assertEqual(observed, new_reference_identity_v1(relation, "source_step_threshold"))
        self.assertTrue(observed.startswith(f"{AUTHORITY_VERSION}:"))
        self.assertNotEqual(observed, relation.historical_reference("source_step_threshold"))

    def test_04_canonical_serialization_is_deterministic(self) -> None:
        second = build_private_registry_document_v1(self.authority, dict(reversed(tuple(self.role_values.items()))))
        self.assertEqual(self.registry["artifact_hash"], second["artifact_hash"])
        self.assertEqual(canonical_json_v1(self.registry), canonical_json_v1(second))

    def test_05_duplicate_logical_key_fails(self) -> None:
        bad = deepcopy(self.registry)
        bad["records"][-1] = deepcopy(bad["records"][0])
        rehash(bad)
        with self.assertRaises(NormalOnlyAuthorityV1Error):
            validate_private_registry_document_v1(bad, self.authority)

    def test_06_missing_record_fails(self) -> None:
        bad = deepcopy(self.registry)
        bad["records"].pop()
        rehash(bad)
        with self.assertRaises(NormalOnlyAuthorityV1Error):
            validate_private_registry_document_v1(bad, self.authority)

    def test_07_unexpected_relation_fails(self) -> None:
        bad = deepcopy(self.registry)
        record = bad["records"][0]
        record["relation_binding_hash"] = "f" * 64
        record["record_hash"] = stable_hash_v1({key: value for key, value in record.items() if key != "record_hash"})
        rehash(bad)
        with self.assertRaises(NormalOnlyAuthorityV1Error):
            validate_private_registry_document_v1(bad, self.authority)

    def test_08_wrong_semantic_execution_hash_fails(self) -> None:
        bad = deepcopy(self.registry)
        record = bad["records"][0]
        record["semantic_execution_hash"] = "e" * 64
        record["record_hash"] = stable_hash_v1({key: value for key, value in record.items() if key != "record_hash"})
        rehash(bad)
        with self.assertRaises(NormalOnlyAuthorityV1Error):
            validate_private_registry_document_v1(bad, self.authority)

    def test_09_wrong_common42_hash_fails(self) -> None:
        bad = deepcopy(self.registry)
        bad["common42_authority_hash"] = "d" * 64
        rehash(bad)
        with self.assertRaises(NormalOnlyAuthorityV1Error):
            validate_private_registry_document_v1(bad, self.authority)

    def test_10_wrong_train_identity_fails_before_value_reader(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            train1 = Path(directory) / "hai-train1.csv"
            train2 = Path(directory) / "hai-train2.csv"
            train1.write_text("not-authorized\n", encoding="utf-8")
            train2.write_text("not-authorized\n", encoding="utf-8")
            with mock.patch.object(authority_v1, "_read_verified_feature_columns") as reader:
                with self.assertRaises(NormalOnlyAuthorityV1Error):
                    load_verified_normal_features_v1(
                        train1_path=train1,
                        train2_path=train2,
                        required_features=frozenset({"P1_FCV01D"}),
                    )
                reader.assert_not_called()

    def test_11_nonfinite_numeric_result_fails(self) -> None:
        for value in (math.nan, math.inf, -math.inf):
            bad = dict(self.role_values)
            bad[(self.authority.relations[0].relation_binding_hash, "source_step_threshold")] = value
            with self.subTest(value=value), self.assertRaises(NormalOnlyAuthorityV1Error):
                build_private_registry_document_v1(self.authority, bad)

    def test_12_bool_string_and_integer_computed_values_fail(self) -> None:
        for value in (True, "5", 5):
            bad = dict(self.role_values)
            bad[(self.authority.relations[0].relation_binding_hash, "source_step_threshold")] = value
            with self.subTest(value=value), self.assertRaises(NormalOnlyAuthorityV1Error):
                build_private_registry_document_v1(self.authority, bad)

    def test_13_wrong_authority_version_fails(self) -> None:
        bad = deepcopy(self.registry)
        bad["authority_version"] = "TASK039E3_UTILITY_NORMAL_ONLY_AUTHORITY_V0"
        rehash(bad)
        with self.assertRaises(NormalOnlyAuthorityV1Error):
            validate_private_registry_document_v1(bad, self.authority)

    def test_14_historical_identity_reuse_fails(self) -> None:
        bad = deepcopy(self.registry)
        record = bad["records"][0]
        relation = self.authority.relations[0]
        record["new_reference_identity"] = relation.historical_reference(str(record["numeric_role"]))
        record["record_hash"] = stable_hash_v1({key: value for key, value in record.items() if key != "record_hash"})
        rehash(bad)
        with self.assertRaises(NormalOnlyAuthorityV1Error):
            validate_private_registry_document_v1(bad, self.authority)

    def test_15_public_receipt_exposes_no_values_or_paths(self) -> None:
        receipt = public_receipt_document_v1(
            authority=self.authority,
            private_registry_hash=str(self.registry["artifact_hash"]),
            builder_commit="a" * 40,
            builder_git_blob="b" * 40,
            builder_source_sha256="c" * 64,
            execution_timestamp="2026-08-19T00:00:00+00:00",
        )
        text = canonical_json_v1(receipt)
        self.assertNotIn("numeric_value", text)
        self.assertNotIn("private_path", text)
        self.assertEqual(validate_public_receipt_v1(receipt, self.authority), receipt["artifact_hash"])

    def test_16_public_receipt_rejects_forbidden_fields(self) -> None:
        receipt = public_receipt_document_v1(
            authority=self.authority,
            private_registry_hash=str(self.registry["artifact_hash"]),
            builder_commit="a" * 40,
            builder_git_blob="b" * 40,
            builder_source_sha256="c" * 64,
            execution_timestamp="2026-08-19T00:00:00+00:00",
        )
        for key, value in (("numeric_value", 1.0), ("private_path", "C:\\private\\registry.json")):
            bad = deepcopy(receipt)
            bad[key] = value
            rehash(bad)
            with self.subTest(key=key), self.assertRaises(NormalOnlyAuthorityV1Error):
                validate_public_receipt_v1(bad, self.authority)

    def test_17_atomic_finalization_and_write_last_contract(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            private = root / "private-registry.json"
            locator = root / "locator.json"
            receipt = root / "receipt.json"
            with mock.patch.dict(os.environ, {PRIVATE_LOCATOR_ENV: str(private)}):
                result = finalize_materialization_atomically_v1(
                    registry=self.registry,
                    authority=self.authority,
                    private_destination=private,
                    local_locator_manifest=locator,
                    public_receipt_path=receipt,
                    repository_root=ROOT,
                    builder_commit="a" * 40,
                    builder_git_blob="b" * 40,
                    builder_source_sha256="c" * 64,
                    execution_timestamp="2026-08-19T00:00:00+00:00",
                )
                self.assertEqual(result.write_order[-1], "public_receipt_written_last")
                self.assertEqual(
                    validate_finalized_authority_v1(
                        authority=self.authority,
                        private_destination=private,
                        local_locator_manifest=locator,
                        public_receipt_path=receipt,
                        repository_root=ROOT,
                    ),
                    self.registry["artifact_hash"],
                )

    def test_18_partial_output_cannot_be_authority(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            partial = root / ".registry.partial-test"
            partial.write_text(canonical_json_v1(self.registry), encoding="utf-8")
            missing_locator = root / "missing-locator.json"
            missing_receipt = root / "missing-receipt.json"
            with mock.patch.dict(os.environ, {PRIVATE_LOCATOR_ENV: str(partial)}):
                with self.assertRaises(NormalOnlyAuthorityV1Error):
                    validate_finalized_authority_v1(
                        authority=self.authority,
                        private_destination=partial,
                        local_locator_manifest=missing_locator,
                        public_receipt_path=missing_receipt,
                        repository_root=ROOT,
                    )

    def test_19_locator_manifest_schema_is_local_only(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "private.json"
            document = authority_v1.local_locator_manifest_document_v1(
                private_authority_path=path,
                private_authority_hash=str(self.registry["artifact_hash"]),
                public_receipt_hash="c" * 64,
                created_at="2026-08-19T00:00:00+00:00",
                builder_commit="a" * 40,
            )
            self.assertTrue(document["local_only"])
            self.assertTrue(document["must_not_be_committed"])
            validate_local_locator_manifest_v1(document, repository_root=ROOT)

    def test_20_frozen_calibration_functions_are_exercised_synthetically(self) -> None:
        ramp = tuple(float(index) for index in range(80))
        threshold, tolerance = derive_source_parameters_normal_only_v1(ramp, ramp)
        self.assertEqual((threshold, tolerance), (5.0, 0.5))
        self.assertEqual(derive_target_scale_normal_only_v1(ramp, ramp), 1e-12)

    def test_21_full_synthetic_calibration_produces_420_values(self) -> None:
        features = {item.source for item in self.authority.relations} | {
            item.target for item in self.authority.relations
        }
        ramp = tuple(float(index) for index in range(80))
        train1 = {feature: ramp for feature in features}
        train2 = {feature: ramp for feature in features}
        values = calibrate_all_role_values_v1(self.authority, train1, train2)
        self.assertEqual(len(values), UTILITY_NUMERIC_REFERENCE_COUNT)
        registry = build_private_registry_document_v1(self.authority, values)
        self.assertEqual(validate_private_registry_document_v1(registry, self.authority), registry["artifact_hash"])

    def test_22_calibration_role_map_is_complete_without_reinterpretation(self) -> None:
        self.assertEqual(tuple(item.numeric_role for item in CALIBRATION_ROLE_SPECS), UTILITY_NUMERIC_ROLES)
        self.assertEqual(len(CALIBRATION_ROLE_SPECS), 10)
        self.assertEqual(
            {item.source_function for item in CALIBRATION_ROLE_SPECS},
            {"derive_multi_file_source_parameters_v1", "derive_multi_file_target_scale_v1", "PreregisteredWindowConstantBundleV1"},
        )

    def test_23_historical_and_t2_boundaries_are_explicit(self) -> None:
        snapshot = authority_snapshot_v1()
        self.assertEqual(snapshot["authority_lineage"], AUTHORITY_LINEAGE)
        self.assertFalse(HISTORICAL_E1_IDENTITY_RESTORED)
        self.assertFalse(HISTORICAL_NUMERIC_IDENTITY_RESTORED)
        self.assertFalse(T2_UTILITY_SCOPE_AUTHORIZED)
        self.assertFalse(snapshot["real_data_authority_materialized"])
        self.assertFalse(snapshot["utility_executed"])

    def test_24_no_test_label_provider_or_api_dependency(self) -> None:
        source = (ROOT / "src/paperworks/v6/task039e3_r2r_utility_normal_only_authority_v1.py").read_text(encoding="utf-8")
        for forbidden in ("hai-test1.csv", "hai-test2.csv", "label-test", "OPENAI_API_KEY"):
            self.assertNotIn(forbidden, source)
        self.assertEqual(tuple(item.sha256 for item in NORMAL_INPUT_IDENTITIES), (
            NORMAL_TRAIN1_IDENTITY.sha256,
            NORMAL_TRAIN2_IDENTITY.sha256,
        ))


if __name__ == "__main__":
    unittest.main()
