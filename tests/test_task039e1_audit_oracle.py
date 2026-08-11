from __future__ import annotations

import unittest
from dataclasses import replace

from paperworks.v6.task039e1_audit_prep_v1 import (
    ROLE_ORIGINS,
    TASK039E1AuditPreparationError,
    audit_independent_relation_evidence_v1,
    audit_resolve_numeric_reference_v1,
    independent_numeric_reference_v1,
)
from tests.task039e1_audit_support import make_relation_fixture, synthetic_hash


class IndependentNumericReferenceOracleTests(unittest.TestCase):
    def test_valid_exact_materialization_reference_and_resolver(self) -> None:
        primitive, private, bundle, manifest = make_relation_fixture()
        roles = audit_independent_relation_evidence_v1(
            primitive, private, bundle, manifest
        )
        threshold = private.numeric_bindings[0]
        resolved = audit_resolve_numeric_reference_v1(
            proposal_numeric_reference=threshold.numeric_reference,
            relation_binding_hash=primitive.relation_binding_hash,
            numeric_role=threshold.numeric_role,
            private_evidence_record_hash=private.artifact_hash,
            private_evidence=private,
        )
        self.assertEqual(len(roles), 11)
        self.assertEqual(resolved.numeric_value, threshold.numeric_value)
        self.assertTrue(resolved.construction_only)
        self.assertFalse(resolved.runtime_authority_granted)

    def test_numeric_reference_binds_every_required_input(self) -> None:
        binding = make_relation_fixture()[1].numeric_bindings[0]
        baseline = binding.numeric_reference
        mutations = (
            {"numeric_value": binding.numeric_value + 0.125},
            {
                "numeric_role": "source_stability_tolerance",
                "value_origin": ROLE_ORIGINS["source_stability_tolerance"],
            },
            {"source_parameter_record_hash": synthetic_hash("changed-source")},
            {"target_parameter_record_hash": synthetic_hash("changed-target")},
            {"d1_evidence_record_hash": synthetic_hash("changed-d1")},
            {"d2_evidence_record_hash": synthetic_hash("changed-d2")},
            {"window_constant_bundle_hash": synthetic_hash("changed-window")},
        )
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                content = binding.reference_content()
                content.update(mutation)
                self.assertNotEqual(
                    independent_numeric_reference_v1(**content), baseline
                )

    def test_resolver_rejects_relation_mismatch(self) -> None:
        _, private, _, _ = make_relation_fixture()
        binding = private.numeric_bindings[0]
        with self.assertRaisesRegex(
            TASK039E1AuditPreparationError, "relation mismatch"
        ):
            audit_resolve_numeric_reference_v1(
                proposal_numeric_reference=binding.numeric_reference,
                relation_binding_hash=synthetic_hash("different-relation"),
                numeric_role=binding.numeric_role,
                private_evidence_record_hash=private.artifact_hash,
                private_evidence=private,
            )

    def test_resolver_rejects_wrong_role_and_modified_private_hash(self) -> None:
        _, private, _, _ = make_relation_fixture()
        binding = private.numeric_bindings[0]
        with self.assertRaisesRegex(
            TASK039E1AuditPreparationError, "numeric role"
        ):
            audit_resolve_numeric_reference_v1(
                proposal_numeric_reference=binding.numeric_reference,
                relation_binding_hash=private.relation_binding_hash,
                numeric_role="source_stability_tolerance",
                private_evidence_record_hash=private.artifact_hash,
                private_evidence=private,
            )
        changed = replace(private, confirmation_status="calibration_conflict")
        with self.assertRaisesRegex(
            TASK039E1AuditPreparationError, "private evidence hash"
        ):
            audit_resolve_numeric_reference_v1(
                proposal_numeric_reference=binding.numeric_reference,
                relation_binding_hash=private.relation_binding_hash,
                numeric_role=binding.numeric_role,
                private_evidence_record_hash=private.artifact_hash,
                private_evidence=changed,
            )


if __name__ == "__main__":
    unittest.main()
