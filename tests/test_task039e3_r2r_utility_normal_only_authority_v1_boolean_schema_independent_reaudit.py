from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import unittest
from typing import Any

from paperworks.v6.common import stable_hash_v1
from paperworks.v6 import task039e3_r2r_utility_normal_only_authority_v1 as subject


ROOT = Path(__file__).resolve().parents[1]

EXPECTED_BOOLEAN_PATHS = {
    ("historical_e1_identity_restored",),
    ("historical_numeric_identity_restored",),
    ("construction_provenance", "scientific_result_evaluable"),
    ("t2_utility_scope_authorized",),
    ("public_receipt_written_last",),
    ("materialization_authorized",),
}

EXPECTED_INTEGER_PATHS = {
    ("record_count",),
    ("unique_key_count",),
    ("relation_count",),
    ("validation_counts", "records"),
    ("validation_counts", "unique_keys"),
    ("validation_counts", "missing"),
    ("validation_counts", "duplicates"),
    ("validation_counts", "unexpected"),
    ("validation_counts", "nonfinite"),
    ("normal_input_identities", 0, "byte_size"),
    ("normal_input_identities", 0, "row_count"),
    ("normal_input_identities", 1, "byte_size"),
    ("normal_input_identities", 1, "row_count"),
}


def _rehash(document: dict[str, Any]) -> dict[str, Any]:
    document["artifact_hash"] = stable_hash_v1(
        {key: value for key, value in document.items() if key != "artifact_hash"}
    )
    return document


def _mutated_receipt(
    receipt: dict[str, Any], path: tuple[str | int, ...], value: object
) -> dict[str, Any]:
    mutated = deepcopy(receipt)
    parent: Any = mutated
    for component in path[:-1]:
        parent = parent[component]
    parent[path[-1]] = value
    return _rehash(mutated)


def _exact_type_paths(
    value: object,
    expected_type: type[object],
    prefix: tuple[str | int, ...] = (),
) -> set[tuple[str | int, ...]]:
    if type(value) is expected_type:
        return {prefix}
    if type(value) is dict:
        found: set[tuple[str | int, ...]] = set()
        for key, child in value.items():
            found.update(_exact_type_paths(child, expected_type, (*prefix, key)))
        return found
    if type(value) is list:
        found = set()
        for index, child in enumerate(value):
            found.update(_exact_type_paths(child, expected_type, (*prefix, index)))
        return found
    return set()


class BooleanSchemaIndependentReauditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        equivalence = json.loads(
            (
                ROOT
                / "docs"
                / "task_reports"
                / "TASK-039E3_R2R_UTILITY_PROTOCOL_EXECUTABLE_EQUIVALENCE.json"
            ).read_text(encoding="utf-8")
        )
        evidence_manifest = json.loads(
            (
                ROOT
                / "docs"
                / "task_reports"
                / "TASK-039E1_CONSTRUCTION_EVIDENCE_MANIFEST.json"
            ).read_text(encoding="utf-8")
        )
        cls.authority = subject.build_common42_authority_v1(
            equivalence, evidence_manifest
        )
        cls.receipt = subject.public_receipt_document_v1(
            authority=cls.authority,
            private_registry_hash="11" * 32,
            builder_commit="ab" * 20,
            builder_git_blob="cd" * 20,
            builder_source_sha256="ef" * 32,
            execution_timestamp="2026-08-19T16:30:00+09:00",
        )

    def assertReceiptRejected(self, receipt: dict[str, Any]) -> None:
        with self.assertRaises(subject.NormalOnlyAuthorityV1Error):
            subject.validate_public_receipt_v1(receipt, self.authority)

    def test_scientific_result_evaluable_true_only_historical_attacks(self) -> None:
        path = ("construction_provenance", "scientific_result_evaluable")
        accepted = _mutated_receipt(self.receipt, path, True)
        self.assertEqual(
            subject.validate_public_receipt_v1(accepted, self.authority),
            accepted["artifact_hash"],
        )

        for invalid in (False, 1, 1.0, 0, 0.0, "true", None):
            with self.subTest(invalid=invalid, invalid_type=type(invalid).__name__):
                self.assertReceiptRejected(_mutated_receipt(self.receipt, path, invalid))

    def test_every_public_receipt_boolean_position_is_exact_bool(self) -> None:
        self.assertEqual(
            _exact_type_paths(self.receipt, bool), EXPECTED_BOOLEAN_PATHS
        )
        non_booleans = (1, 1.0, 0, 0.0, "true", None)
        for path in sorted(EXPECTED_BOOLEAN_PATHS, key=repr):
            original = self._value_at(path)
            self.assertIs(type(original), bool)
            for invalid in non_booleans:
                with self.subTest(path=path, invalid=invalid):
                    self.assertReceiptRejected(
                        _mutated_receipt(self.receipt, path, invalid)
                    )
            with self.subTest(path=path, wrong_boolean=not original):
                self.assertReceiptRejected(
                    _mutated_receipt(self.receipt, path, not original)
                )

    def test_every_public_receipt_integer_position_rejects_bool(self) -> None:
        self.assertEqual(_exact_type_paths(self.receipt, int), EXPECTED_INTEGER_PATHS)
        for path in sorted(EXPECTED_INTEGER_PATHS, key=repr):
            for invalid in (False, True):
                with self.subTest(path=path, invalid=invalid):
                    self.assertReceiptRejected(
                        _mutated_receipt(self.receipt, path, invalid)
                    )

    def test_unknown_fields_remain_closed_at_every_receipt_object_layer(self) -> None:
        object_paths = (
            (),
            ("validation_counts",),
            ("construction_provenance",),
            ("normal_input_identities", 0),
            ("normal_input_identities", 1),
        )
        for path in object_paths:
            mutated = deepcopy(self.receipt)
            target: Any = mutated
            for component in path:
                target = target[component]
            target["independent_reaudit_unknown"] = "closed"
            with self.subTest(path=path):
                self.assertReceiptRejected(_rehash(mutated))

    def test_minimal_receipt_and_authority_invariants_are_unchanged(self) -> None:
        receipt = self.receipt
        self.assertEqual(
            subject.validate_public_receipt_v1(receipt, self.authority),
            receipt["artifact_hash"],
        )
        self.assertEqual(receipt["record_count"], 420)
        self.assertEqual(receipt["unique_key_count"], 420)
        self.assertEqual(receipt["relation_count"], 42)
        self.assertEqual(receipt["validation_counts"]["missing"], 0)
        self.assertEqual(receipt["validation_counts"]["duplicates"], 0)
        self.assertEqual(receipt["validation_counts"]["unexpected"], 0)
        self.assertEqual(receipt["validation_counts"]["nonfinite"], 0)
        self.assertIs(receipt["historical_e1_identity_restored"], False)
        self.assertIs(receipt["historical_numeric_identity_restored"], False)
        self.assertIs(receipt["t2_utility_scope_authorized"], False)
        self.assertIs(receipt["public_receipt_written_last"], True)
        self.assertIs(receipt["materialization_authorized"], False)

        snapshot = subject.authority_snapshot_v1()
        self.assertEqual(snapshot["construction_result_validity"], "UNCHANGED")
        self.assertEqual(snapshot["terminal_custody_validity"], "UNCHANGED")
        self.assertIs(snapshot["utility_executed"], False)
        self.assertIs(snapshot["real_data_authority_materialized"], False)

    def _value_at(self, path: tuple[str | int, ...]) -> object:
        value: Any = self.receipt
        for component in path:
            value = value[component]
        return value


if __name__ == "__main__":
    unittest.main()
