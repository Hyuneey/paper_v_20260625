from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import unittest

from paperworks.v6.common import stable_hash_v1
import paperworks.v6.task039e3_r2r_utility_normal_only_authority_v1 as subject


ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "docs" / "task_reports"


def load(name: str) -> dict[str, object]:
    return json.loads((REPORTS / name).read_text(encoding="utf-8"))


def rehash(document: dict[str, object]) -> None:
    document["artifact_hash"] = stable_hash_v1(
        {key: value for key, value in document.items() if key != "artifact_hash"}
    )


class ReceiptBooleanSchemaMicrofixTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.authority = subject.build_common42_authority_v1(
            load("TASK-039E3_R2R_UTILITY_PROTOCOL_EXECUTABLE_EQUIVALENCE.json"),
            load("TASK-039E1_CONSTRUCTION_EVIDENCE_MANIFEST.json"),
        )

    def receipt(self) -> dict[str, object]:
        return subject.public_receipt_document_v1(
            authority=self.authority,
            private_registry_hash="a" * 64,
            builder_commit=subject.SCIENTIFIC_V1_COMMIT,
            builder_git_blob="b" * 40,
            builder_source_sha256="c" * 64,
            execution_timestamp="2026-08-19T00:00:00Z",
        )

    def assert_receipt_rejected(self, document: dict[str, object]) -> None:
        rehash(document)
        with self.assertRaises(subject.NormalOnlyAuthorityV1Error):
            subject.validate_public_receipt_v1(document, self.authority)

    def test_canonical_true_is_the_only_accepted_provenance_boolean(self) -> None:
        canonical = self.receipt()
        self.assertIs(
            canonical["construction_provenance"]["scientific_result_evaluable"], True
        )
        subject.validate_public_receipt_v1(canonical, self.authority)
        mutations: tuple[object, ...] = (
            False,
            1,
            1.0,
            0,
            0.0,
            -1,
            "true",
            "True",
            "false",
            None,
            [],
            {},
            [True],
            {"value": True},
        )
        for value in mutations:
            changed = deepcopy(canonical)
            changed["construction_provenance"]["scientific_result_evaluable"] = value
            with self.subTest(value=repr(value)):
                self.assert_receipt_rejected(changed)

    def test_every_receipt_boolean_field_uses_exact_bool_type_and_value(self) -> None:
        canonical = self.receipt()
        paths = (
            ("historical_e1_identity_restored", False),
            ("historical_numeric_identity_restored", False),
            ("t2_utility_scope_authorized", False),
            ("public_receipt_written_last", True),
            ("materialization_authorized", False),
        )
        for field, expected in paths:
            self.assertIs(type(canonical[field]), bool)
            self.assertIs(canonical[field], expected)
            for substitute in (1, 1.0, 0, 0.0):
                changed = deepcopy(canonical)
                changed[field] = substitute
                with self.subTest(field=field, substitute=repr(substitute)):
                    self.assert_receipt_rejected(changed)
        provenance = canonical["construction_provenance"]["scientific_result_evaluable"]
        self.assertIs(type(provenance), bool)
        self.assertIs(provenance, True)

    def test_bool_cannot_masquerade_as_any_receipt_integer(self) -> None:
        canonical = self.receipt()
        for field in ("record_count", "unique_key_count", "relation_count"):
            changed = deepcopy(canonical)
            changed[field] = True
            with self.subTest(scope="top", field=field):
                self.assert_receipt_rejected(changed)
        for field in subject.VALIDATION_COUNT_ALLOWED_KEYS_V1:
            changed = deepcopy(canonical)
            changed["validation_counts"][field] = True
            with self.subTest(scope="validation_counts", field=field):
                self.assert_receipt_rejected(changed)
        for index in range(2):
            for field in ("byte_size", "row_count"):
                changed = deepcopy(canonical)
                changed["normal_input_identities"][index][field] = True
                with self.subTest(scope=f"normal_identity_{index}", field=field):
                    self.assert_receipt_rejected(changed)

    def test_exact_key_closure_remains_enforced(self) -> None:
        top = self.receipt()
        top["random_unknown_field"] = True
        self.assert_receipt_rejected(top)
        nested = self.receipt()
        nested["construction_provenance"]["unknown_nested_field"] = True
        self.assert_receipt_rejected(nested)


if __name__ == "__main__":
    unittest.main()
