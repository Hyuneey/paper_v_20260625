from __future__ import annotations

from dataclasses import replace
import unittest

from paperworks.v6.task039e1_evidence_materialization_prep_v1 import (
    ConstructionNumericRoleV1,
    TASK039E1PreparationError,
    materialize_construction_evidence_collection_v1,
    resolve_private_numeric_reference_v1,
)
from tests.task039e1_support import (
    materialize_input,
    synthetic_materialization_input,
    synthetic_source_parameter,
    synthetic_target_parameter,
)


class MaterializationMismatchTests(unittest.TestCase):
    def setUp(self) -> None:
        self.item = synthetic_materialization_input()

    def _fails(self, **changes):
        with self.assertRaises(TASK039E1PreparationError):
            materialize_input(replace(self.item, **changes))

    def test_wrong_source_and_target_fail_closed(self) -> None:
        self._fails(
            source_parameter=replace(
                self.item.source_parameter, source="SYNTHETIC_WRONG_SOURCE"
            )
        )
        self._fails(
            target_parameter=replace(
                self.item.target_parameter, target="SYNTHETIC_WRONG_TARGET"
            )
        )

    def test_wrong_source_and_target_directions_fail_closed(self) -> None:
        self._fails(
            relation=replace(
                self.item.relation, source_step_direction="step_down"
            )
        )
        self._fails(
            relation=replace(
                self.item.relation, target_response_direction="decrease"
            )
        )

    def test_wrong_horizon_fails_closed(self) -> None:
        self._fails(
            relation=replace(
                self.item.relation,
                selected_delay_horizon_seconds=(
                    self.item.relation.selected_delay_horizon_seconds + 1
                ),
            )
        )

    def test_wrong_d1_and_d2_record_hashes_fail_closed(self) -> None:
        self._fails(
            relation=replace(self.item.relation, fit_evidence_reference="f" * 64)
        )
        self._fails(
            relation=replace(
                self.item.relation, confirmation_evidence_reference="e" * 64
            )
        )
        self._fails(
            d2_confirmation_record=replace(
                self.item.d2_confirmation_record,
                d1_directional_record_hash="d" * 64,
            )
        )
        self._fails(
            d2_confirmation_record=replace(
                self.item.d2_confirmation_record,
                source_parameter_record_hash="c" * 64,
            )
        )

    def test_unconfirmed_or_retuned_d2_record_fails_closed(self) -> None:
        self._fails(
            d2_confirmation_record=replace(
                self.item.d2_confirmation_record,
                confirmation_status="calibration_conflict",
            )
        )
        self._fails(
            d2_confirmation_record=replace(
                self.item.d2_confirmation_record,
                fit_parameters_reused_without_retuning=False,
            )
        )

    def test_modified_numeric_value_fails_closed(self) -> None:
        self._fails(
            source_parameter=replace(
                self.item.source_parameter,
                source_step_threshold=(
                    self.item.source_parameter.source_step_threshold + 0.001
                ),
            )
        )

    def test_missing_source_threshold_and_target_scale_fail_closed(self) -> None:
        self._fails(
            source_parameter=synthetic_source_parameter(
                source_noise_scale=None,
                source_step_threshold=None,
                source_stability_tolerance=None,
                parameter_status="unsupported",
            )
        )
        self._fails(
            target_parameter=synthetic_target_parameter(
                target_noise_scale=None,
                parameter_status="unsupported",
            )
        )

    def test_duplicate_relation_fails_closed(self) -> None:
        with self.assertRaisesRegex(
            TASK039E1PreparationError, "duplicate relation"
        ):
            materialize_construction_evidence_collection_v1(
                (self.item, self.item)
            )


class NumericReferenceResolverTests(unittest.TestCase):
    def setUp(self) -> None:
        self.result = materialize_input(synthetic_materialization_input())
        self.private = self.result.private_evidence
        self.threshold = next(
            item
            for item in self.private.numeric_bindings
            if item.numeric_role
            == ConstructionNumericRoleV1.SOURCE_STEP_THRESHOLD.value
        )

    def test_valid_reference_resolves_construction_only_value(self) -> None:
        resolved = resolve_private_numeric_reference_v1(
            proposal_numeric_reference=self.threshold.numeric_reference,
            relation_binding_hash=self.private.relation_binding_hash,
            numeric_role=self.threshold.numeric_role,
            private_evidence_record_hash=self.private.artifact_hash,
            private_evidence=self.private,
        )
        self.assertEqual(resolved.numeric_value, self.threshold.numeric_value)
        self.assertTrue(resolved.construction_only)
        self.assertFalse(resolved.runtime_authority_granted)

    def test_wrong_numeric_role_and_bindings_fail_closed(self) -> None:
        cases = (
            {
                "numeric_role": ConstructionNumericRoleV1.TARGET_NOISE_SCALE.value
            },
            {"relation_binding_hash": "a" * 64},
            {"private_evidence_record_hash": "b" * 64},
            {"proposal_numeric_reference": "c" * 64},
        )
        base = {
            "proposal_numeric_reference": self.threshold.numeric_reference,
            "relation_binding_hash": self.private.relation_binding_hash,
            "numeric_role": self.threshold.numeric_role,
            "private_evidence_record_hash": self.private.artifact_hash,
            "private_evidence": self.private,
        }
        for changes in cases:
            with self.subTest(changes=changes), self.assertRaises(
                TASK039E1PreparationError
            ):
                resolve_private_numeric_reference_v1(**{**base, **changes})

    def test_modified_private_numeric_value_breaks_manifest_hash_binding(self) -> None:
        modified_binding = replace(
            self.threshold,
            numeric_value=self.threshold.numeric_value + 0.001,
        )
        modified = replace(
            self.private,
            numeric_bindings=tuple(
                modified_binding if item is self.threshold else item
                for item in self.private.numeric_bindings
            ),
        )
        with self.assertRaisesRegex(
            TASK039E1PreparationError, "private evidence hash mismatch"
        ):
            resolve_private_numeric_reference_v1(
                proposal_numeric_reference=modified_binding.numeric_reference,
                relation_binding_hash=modified.relation_binding_hash,
                numeric_role=modified_binding.numeric_role,
                private_evidence_record_hash=(
                    self.result.public_manifest.private_evidence_record_hash
                ),
                private_evidence=modified,
            )


if __name__ == "__main__":
    unittest.main()
