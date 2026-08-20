"""Focused R1 factory-custody tests for evaluator authorities."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import fields, replace
import gc
import unittest
import weakref

import paperworks.v6.task039e3_r2r_utility_evaluator_authority_v1 as authority_v1
from paperworks.v6.task039e3_r2r_utility_evaluator_types_v1 import (
    UtilityEvaluatorV1Error,
)
import paperworks.v6.task039e3_r2r_utility_evaluator_v1 as evaluator_v1
from tests.test_task039e3_r2r_utility_evaluator_v1_independent_authority import (
    build_lower_v4_authority,
)


ORIGINAL_IMPLEMENTATION_IDENTITY = (
    "332e367cdc0da21b281c5de43f6a735d7dc68bc87efafe90976d89d7f9dc3330"
)
EXPECTED_R2_IMPLEMENTATION_IDENTITY = (
    "e7a61070c0be96e305f6706b90308c9976bc8d521c8b97adea93836c3fd28cef"
)
EXPECTED_BUNDLE_HASH = "0510da125dd8a799c988927ba49ecb784cad5ea12b05b41e31406effe23051c9"


def exact_reconstruction(value: object) -> object:
    return type(value)(**{field.name: getattr(value, field.name) for field in fields(value)})


class EvaluatorAuthorityCustodyR1Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.v4_authority = build_lower_v4_authority()
        cls.bundle = authority_v1.build_evaluator_authority_bundle_v1(cls.v4_authority)
        cls.implementation = evaluator_v1.build_evaluator_implementation_authority_v1(
            cls.bundle
        )

    def test_factory_issued_bundle_and_current_implementation_pass(self) -> None:
        self.assertEqual(
            authority_v1.validate_evaluator_authority_bundle_v1(self.bundle),
            EXPECTED_BUNDLE_HASH,
        )
        self.assertEqual(
            evaluator_v1.validate_evaluator_implementation_authority_v1(
                self.implementation, self.bundle
            ),
            EXPECTED_R2_IMPLEMENTATION_IDENTITY,
        )
        self.assertEqual(
            self.implementation.control_revision,
            evaluator_v1.UTILITY_EVALUATOR_CONTROL_REVISION,
        )
        self.assertEqual(evaluator_v1.UTILITY_EVALUATOR_CONTROL_REVISION, "R2")

    def test_bundle_reconstruction_deepcopy_and_noop_replace_reject(self) -> None:
        candidates = (
            exact_reconstruction(self.bundle),
            deepcopy(self.bundle),
            replace(self.bundle),
        )
        for candidate in candidates:
            with self.subTest(candidate=type(candidate).__name__), self.assertRaises(
                UtilityEvaluatorV1Error
            ):
                authority_v1.validate_evaluator_authority_bundle_v1(candidate)  # type: ignore[arg-type]

    def test_implementation_reconstruction_deepcopy_and_noop_replace_reject(self) -> None:
        candidates = (
            exact_reconstruction(self.implementation),
            deepcopy(self.implementation),
            replace(self.implementation),
        )
        for candidate in candidates:
            with self.subTest(candidate=type(candidate).__name__), self.assertRaises(
                UtilityEvaluatorV1Error
            ):
                evaluator_v1.validate_evaluator_implementation_authority_v1(
                    candidate, self.bundle  # type: ignore[arg-type]
                )

    def test_issued_field_mutations_and_original_identity_reject(self) -> None:
        changed_bundle = authority_v1.build_evaluator_authority_bundle_v1(self.v4_authority)
        object.__setattr__(changed_bundle, "main_descriptor_hash", "f" * 64)
        with self.assertRaises(UtilityEvaluatorV1Error):
            authority_v1.validate_evaluator_authority_bundle_v1(changed_bundle)

        changed_implementation = evaluator_v1.build_evaluator_implementation_authority_v1(
            self.bundle
        )
        object.__setattr__(
            changed_implementation,
            "implementation_identity",
            ORIGINAL_IMPLEMENTATION_IDENTITY,
        )
        with self.assertRaises(UtilityEvaluatorV1Error):
            evaluator_v1.validate_evaluator_implementation_authority_v1(
                changed_implementation, self.bundle
            )
        self.assertNotEqual(
            self.implementation.implementation_identity,
            ORIGINAL_IMPLEMENTATION_IDENTITY,
        )

    def test_weakref_registries_cleanup_automatically(self) -> None:
        temporary_bundle = authority_v1.build_evaluator_authority_bundle_v1(self.v4_authority)
        bundle_id = id(temporary_bundle)
        bundle_ref = weakref.ref(temporary_bundle)
        self.assertIn(bundle_id, authority_v1._ISSUED_EVALUATOR_AUTHORITY_BUNDLES)
        del temporary_bundle
        gc.collect()
        self.assertIsNone(bundle_ref())
        self.assertNotIn(bundle_id, authority_v1._ISSUED_EVALUATOR_AUTHORITY_BUNDLES)

        temporary_implementation = evaluator_v1.build_evaluator_implementation_authority_v1(
            self.bundle
        )
        implementation_id = id(temporary_implementation)
        implementation_ref = weakref.ref(temporary_implementation)
        self.assertIn(
            implementation_id,
            evaluator_v1._ISSUED_EVALUATOR_IMPLEMENTATION_AUTHORITIES,
        )
        del temporary_implementation
        gc.collect()
        self.assertIsNone(implementation_ref())
        self.assertNotIn(
            implementation_id,
            evaluator_v1._ISSUED_EVALUATOR_IMPLEMENTATION_AUTHORITIES,
        )

    def test_stale_id_only_entries_do_not_grant_custody(self) -> None:
        forged_bundle = exact_reconstruction(self.bundle)
        forged_bundle_id = id(forged_bundle)
        authority_v1._ISSUED_EVALUATOR_AUTHORITY_BUNDLES[forged_bundle_id] = (
            weakref.ref(self.bundle),
            forged_bundle.bundle_hash,  # type: ignore[attr-defined]
        )
        try:
            with self.assertRaises(UtilityEvaluatorV1Error):
                authority_v1.validate_evaluator_authority_bundle_v1(forged_bundle)  # type: ignore[arg-type]
        finally:
            authority_v1._ISSUED_EVALUATOR_AUTHORITY_BUNDLES.pop(forged_bundle_id, None)

        forged_implementation = exact_reconstruction(self.implementation)
        forged_implementation_id = id(forged_implementation)
        evaluator_v1._ISSUED_EVALUATOR_IMPLEMENTATION_AUTHORITIES[
            forged_implementation_id
        ] = (
            weakref.ref(self.implementation),
            forged_implementation.implementation_identity,  # type: ignore[attr-defined]
            forged_implementation.evaluator_authority_bundle_hash,  # type: ignore[attr-defined]
        )
        try:
            with self.assertRaises(UtilityEvaluatorV1Error):
                evaluator_v1.validate_evaluator_implementation_authority_v1(
                    forged_implementation, self.bundle  # type: ignore[arg-type]
                )
        finally:
            evaluator_v1._ISSUED_EVALUATOR_IMPLEMENTATION_AUTHORITIES.pop(
                forged_implementation_id, None
            )

    def test_semantic_validation_does_not_issue_expected_copies(self) -> None:
        bundle_registry_size = len(authority_v1._ISSUED_EVALUATOR_AUTHORITY_BUNDLES)
        implementation_registry_size = len(
            evaluator_v1._ISSUED_EVALUATOR_IMPLEMENTATION_AUTHORITIES
        )
        authority_v1.validate_evaluator_authority_bundle_v1(self.bundle)
        evaluator_v1.validate_evaluator_implementation_authority_v1(
            self.implementation, self.bundle
        )
        self.assertEqual(
            len(authority_v1._ISSUED_EVALUATOR_AUTHORITY_BUNDLES),
            bundle_registry_size,
        )
        self.assertEqual(
            len(evaluator_v1._ISSUED_EVALUATOR_IMPLEMENTATION_AUTHORITIES),
            implementation_registry_size,
        )


if __name__ == "__main__":
    unittest.main()
