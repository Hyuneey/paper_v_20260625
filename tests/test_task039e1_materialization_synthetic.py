from __future__ import annotations

import unittest

from paperworks.v6.task039e1_evidence_materialization_prep_v1 import (
    APPROVED_EVIDENCE_AUTHORITY,
    NUMERIC_ROLE_ORDER,
    WINDOW_NUMERIC_ROLES,
    ConstructionNumericRoleV1,
)
from tests.task039e1_support import (
    materialize_input,
    synthetic_materialization_input,
)


class SyntheticMaterializationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.item = synthetic_materialization_input()
        self.result = materialize_input(self.item)

    def test_valid_exact_materialization(self) -> None:
        private = self.result.private_evidence
        self.assertEqual(private.relation_binding_hash, self.item.relation.binding_hash)
        self.assertEqual(private.evidence_authority, APPROVED_EVIDENCE_AUTHORITY)
        self.assertEqual(
            tuple(binding.numeric_role for binding in private.numeric_bindings),
            NUMERIC_ROLE_ORDER,
        )
        self.assertEqual(
            {binding.source_parameter_record_hash for binding in private.numeric_bindings},
            {self.item.source_parameter.artifact_hash},
        )
        self.assertEqual(
            {binding.d2_confirmation_evidence_hash for binding in private.numeric_bindings},
            {self.item.d2_confirmation_record.artifact_hash},
        )
        self.assertEqual(
            {binding.target_parameter_record_hash for binding in private.numeric_bindings},
            {self.item.target_parameter.artifact_hash},
        )
        self.assertEqual(
            {binding.d1_fit_evidence_hash for binding in private.numeric_bindings},
            {self.item.d1_fit_record.artifact_hash},
        )
        self.assertEqual(
            {binding.window_constant_bundle_hash for binding in private.numeric_bindings},
            {self.item.window_constants.artifact_hash},
        )
        self.assertFalse(private.rule_generated)
        self.assertFalse(private.runtime_authority_granted)

    def test_e0_approved_bundle_uses_materialized_references(self) -> None:
        private = self.result.private_evidence
        by_role = {item.numeric_role: item for item in private.numeric_bindings}
        bundle = self.result.approved_numeric_bundle
        self.assertEqual(
            bundle.source_threshold_reference,
            by_role[
                ConstructionNumericRoleV1.SOURCE_STEP_THRESHOLD.value
            ].numeric_reference,
        )
        self.assertEqual(
            bundle.source_stability_reference,
            by_role[
                ConstructionNumericRoleV1.SOURCE_STABILITY_TOLERANCE.value
            ].numeric_reference,
        )
        self.assertEqual(
            bundle.target_scale_reference,
            by_role[
                ConstructionNumericRoleV1.TARGET_NOISE_SCALE.value
            ].numeric_reference,
        )
        self.assertEqual(
            bundle.preregistered_window_constant_references,
            tuple(by_role[role].numeric_reference for role in WINDOW_NUMERIC_ROLES),
        )
        bundle.assert_matches(self.item.relation)
        self.assertFalse(bundle.arbitrary_numeric_literals_allowed)

    def test_public_manifest_contains_no_private_numeric_values(self) -> None:
        manifest = self.result.public_manifest.to_dict()
        forbidden = {
            "numeric_value",
            "numeric_bindings",
            "source_step_threshold",
            "source_stability_tolerance",
            "target_noise_scale",
            "source_pre_window_seconds",
            "target_response_window_seconds",
        }
        self.assertTrue(forbidden.isdisjoint(manifest))
        self.assertFalse(manifest["private_numeric_values_included"])
        self.assertFalse(manifest["raw_hai_included"])
        self.assertEqual(manifest["approved_numeric_roles"], list(NUMERIC_ROLE_ORDER))

    def test_selected_horizon_is_omitted_when_public_policy_disallows_it(self) -> None:
        from dataclasses import replace

        hidden = replace(
            self.item,
            disclosure_policy=replace(
                self.item.disclosure_policy, selected_horizon_public=False
            ),
        )
        result = materialize_input(hidden)
        self.assertIsNone(result.public_manifest.selected_horizon_seconds)
        self.assertEqual(
            result.private_evidence.selected_horizon_seconds,
            self.item.relation.selected_delay_horizon_seconds,
        )


if __name__ == "__main__":
    unittest.main()
