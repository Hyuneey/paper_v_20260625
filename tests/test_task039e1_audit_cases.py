from __future__ import annotations

import unittest
from dataclasses import replace

from paperworks.v6.task039e1_audit_prep_v1 import (
    IndependentNumericBindingV1,
    TASK039E1AuditPreparationError,
    audit_independent_relation_evidence_v1,
    audit_public_manifest_sanitization_v1,
)
from tests.task039e1_audit_support import make_relation_fixture, synthetic_hash


class SyntheticMismatchTests(unittest.TestCase):
    def test_relation_identity_mismatches_fail_closed(self) -> None:
        cases = (
            ("source", "SYNTHETIC_WRONG_SOURCE", "relation source mismatch"),
            ("target", "SYNTHETIC_WRONG_TARGET", "relation target mismatch"),
            ("source_step_direction", "step_down", "source_step_direction mismatch"),
            (
                "target_response_direction",
                "increase",
                "target_response_direction mismatch",
            ),
            ("selected_delay_horizon", 999, "selected_delay_horizon mismatch"),
        )
        for field_name, changed_value, message in cases:
            with self.subTest(field_name=field_name):
                primitive, private, bundle, manifest = make_relation_fixture()
                self.assertNotEqual(getattr(private, field_name), changed_value)
                with self.assertRaisesRegex(TASK039E1AuditPreparationError, message):
                    audit_independent_relation_evidence_v1(
                        primitive,
                        replace(private, **{field_name: changed_value}),
                        bundle,
                        manifest,
                    )

    def test_wrong_parameter_evidence_and_window_bindings_fail_closed(self) -> None:
        cases = (
            ("source_parameter_record_hash", "source_parameter_record_hash"),
            ("target_parameter_record_hash", "target_parameter_record_hash"),
            ("d1_evidence_record_hash", "wrong D1"),
            ("d2_evidence_record_hash", "wrong D2"),
            ("window_constant_bundle_hash", "window_constant_bundle_hash"),
        )
        for field_name, message in cases:
            with self.subTest(field_name=field_name):
                primitive, private, bundle, manifest = make_relation_fixture()
                with self.assertRaisesRegex(TASK039E1AuditPreparationError, message):
                    audit_independent_relation_evidence_v1(
                        primitive,
                        replace(
                            private,
                            **{field_name: synthetic_hash(f"wrong-{field_name}")},
                        ),
                        bundle,
                        manifest,
                    )

    def test_d2_conflict_status_is_rejected(self) -> None:
        primitive, private, bundle, manifest = make_relation_fixture()
        with self.assertRaisesRegex(TASK039E1AuditPreparationError, "D2 conflict"):
            audit_independent_relation_evidence_v1(
                primitive,
                replace(private, confirmation_status="calibration_conflict"),
                bundle,
                manifest,
            )

    def test_changed_calibrated_values_invalidate_numeric_references(self) -> None:
        roles = (
            "source_step_threshold",
            "source_stability_tolerance",
            "target_noise_scale",
        )
        for role in roles:
            with self.subTest(role=role):
                primitive, private, bundle, manifest = make_relation_fixture()
                bindings = list(private.numeric_bindings)
                index = next(
                    i for i, item in enumerate(bindings) if item.numeric_role == role
                )
                bindings[index] = replace(
                    bindings[index], numeric_value=bindings[index].numeric_value + 1
                )
                with self.assertRaisesRegex(
                    TASK039E1AuditPreparationError, "numeric-reference"
                ):
                    audit_independent_relation_evidence_v1(
                        primitive,
                        replace(private, numeric_bindings=tuple(bindings)),
                        bundle,
                        manifest,
                    )

    def test_missing_and_duplicated_numeric_roles_are_rejected(self) -> None:
        primitive, private, bundle, manifest = make_relation_fixture()
        missing = (*private.numeric_bindings[:4], *private.numeric_bindings[5:])
        duplicate = (*private.numeric_bindings[:-1], private.numeric_bindings[0])
        with self.assertRaisesRegex(
            TASK039E1AuditPreparationError, "exactly eleven"
        ):
            audit_independent_relation_evidence_v1(
                primitive, replace(private, numeric_bindings=missing), bundle, manifest
            )
        with self.assertRaisesRegex(TASK039E1AuditPreparationError, "duplicated"):
            audit_independent_relation_evidence_v1(
                primitive,
                replace(private, numeric_bindings=duplicate),
                bundle,
                manifest,
            )

    def test_wrong_numeric_role_origin_is_rejected(self) -> None:
        primitive, private, bundle, manifest = make_relation_fixture()
        first = private.numeric_bindings[0]
        wrong = IndependentNumericBindingV1(
            **{**first.to_dict(), "value_origin": "d1_target_parameter_record"}
        )
        changed = replace(
            private, numeric_bindings=(wrong, *private.numeric_bindings[1:])
        )
        with self.assertRaisesRegex(TASK039E1AuditPreparationError, "origin"):
            audit_independent_relation_evidence_v1(
                primitive, changed, bundle, manifest
            )

    def test_public_calibrated_values_and_private_paths_are_rejected(self) -> None:
        manifest = make_relation_fixture()[3]
        documents = (
            {**manifest.to_dict(), "source_step_threshold": 123.0},
            {**manifest.to_dict(), "private_path": "C:\\private\\ledger.json"},
        )
        for document in documents:
            with self.subTest(document=document):
                with self.assertRaisesRegex(
                    TASK039E1AuditPreparationError, "public|private"
                ):
                    audit_public_manifest_sanitization_v1(document)

    def test_wrong_public_window_constant_is_rejected(self) -> None:
        primitive, private, bundle, manifest = make_relation_fixture()
        first = manifest.public_window_protocol_constants[0]
        constants = (
            replace(first, numeric_value=first.numeric_value + 1),
            *manifest.public_window_protocol_constants[1:],
        )
        with self.assertRaisesRegex(TASK039E1AuditPreparationError, "window constant"):
            audit_independent_relation_evidence_v1(
                primitive,
                private,
                bundle,
                replace(manifest, public_window_protocol_constants=constants),
            )

    def test_runtime_authority_preclaim_is_rejected(self) -> None:
        primitive, private, bundle, manifest = make_relation_fixture()
        with self.assertRaisesRegex(
            TASK039E1AuditPreparationError, "runtime authority"
        ):
            audit_independent_relation_evidence_v1(
                primitive,
                replace(private, runtime_authority_granted=True),
                bundle,
                manifest,
            )


if __name__ == "__main__":
    unittest.main()
