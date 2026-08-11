from __future__ import annotations

import unittest
from dataclasses import replace

from paperworks.v6.task039e1_audit_prep_v1 import (
    EXPECTED_NUMERIC_BINDINGS,
    EXPECTED_RELATIONS,
    NUMERIC_ROLES,
    PREPARATION_STATUS,
    TASK039E1AuditPreparationError,
    audit_synthetic_construction_evidence_dataset_v1,
)
from tests.task039e1_audit_support import (
    make_exact_synthetic_dataset,
    synthetic_hash,
)


class ExactAccountingTests(unittest.TestCase):
    def test_exact_42_by_11_accounting_and_e0_cohort_preservation(self) -> None:
        result = audit_synthetic_construction_evidence_dataset_v1(
            make_exact_synthetic_dataset()
        )
        self.assertEqual(result.audit_status, PREPARATION_STATUS)
        self.assertEqual(result.confirmed_relation_count, EXPECTED_RELATIONS)
        self.assertEqual(result.pair_context_count, 23)
        self.assertEqual(result.private_evidence_record_count, EXPECTED_RELATIONS)
        self.assertEqual(result.numeric_binding_count, EXPECTED_NUMERIC_BINDINGS)
        self.assertEqual(result.public_relation_primitive_count, EXPECTED_RELATIONS)
        self.assertEqual(result.approved_numeric_bundle_count, EXPECTED_RELATIONS)
        self.assertEqual(result.public_manifest_entry_count, EXPECTED_RELATIONS)
        self.assertEqual(result.skipped_relation_count, 0)
        self.assertEqual(
            result.role_frequencies, tuple((role, 42) for role in NUMERIC_ROLES)
        )
        self.assertTrue(result.e0_cohort_identity_preserved)
        self.assertTrue(result.public_private_separation_passed)
        self.assertFalse(result.real_result_audited)
        self.assertFalse(result.runtime_authority_granted)

    def test_changed_e0_cohort_identity_is_rejected(self) -> None:
        dataset = make_exact_synthetic_dataset()
        changed = replace(
            dataset,
            e0_cohort_identity_list_hash=synthetic_hash("wrong-e0-cohort"),
        )
        with self.assertRaisesRegex(TASK039E1AuditPreparationError, "E0 cohort"):
            audit_synthetic_construction_evidence_dataset_v1(changed)

    def test_duplicate_relation_is_rejected(self) -> None:
        dataset = make_exact_synthetic_dataset()
        changed = replace(
            dataset,
            public_relation_primitives=(
                dataset.public_relation_primitives[0],
                dataset.public_relation_primitives[0],
                *dataset.public_relation_primitives[2:],
            ),
        )
        with self.assertRaisesRegex(
            TASK039E1AuditPreparationError, "duplicate relation"
        ):
            audit_synthetic_construction_evidence_dataset_v1(changed)

    def test_ten_and_twelve_role_records_are_rejected(self) -> None:
        dataset = make_exact_synthetic_dataset()
        first = dataset.private_evidence_records[0]
        for bindings in (
            first.numeric_bindings[:10],
            (*first.numeric_bindings, first.numeric_bindings[0]),
        ):
            with self.subTest(binding_count=len(bindings)):
                private_records = (
                    replace(first, numeric_bindings=tuple(bindings)),
                    *dataset.private_evidence_records[1:],
                )
                with self.assertRaisesRegex(
                    TASK039E1AuditPreparationError, "exactly eleven"
                ):
                    audit_synthetic_construction_evidence_dataset_v1(
                        replace(dataset, private_evidence_records=private_records)
                    )


if __name__ == "__main__":
    unittest.main()
