from __future__ import annotations

import unittest

from paperworks.data.contracts_v2 import SplitRoleV2
from paperworks.v6.common import V6FoundationError
from paperworks.v6.detector_context_v1 import (
    DetectorContextPurposeV1,
    DetectorErrorContextV1,
    DetectorErrorDirectionV1,
)
from tests.task039p1b_support import detector_context, digest


class DetectorContextTests(unittest.TestCase):
    def test_development_fn_context(self) -> None:
        context = detector_context()
        self.assertTrue(context.primary_correction_direction)
        self.assertEqual(DetectorErrorContextV1.from_json(context.to_json()), context)

    def test_inner_utility_fn_context(self) -> None:
        context = detector_context(
            split_role=SplitRoleV2.INNER_UTILITY,
            split_manifest_id=digest("inner-split"),
            purpose=DetectorContextPurposeV1.INNER_UTILITY_ASSESSMENT,
        )
        self.assertEqual(context.split_role, SplitRoleV2.INNER_UTILITY)

    def test_false_positive_is_supplementary(self) -> None:
        context = detector_context(
            error_direction=DetectorErrorDirectionV1.FALSE_POSITIVE,
            supplementary_only=True,
            primary_correction_direction=False,
        )
        self.assertTrue(context.supplementary_only)
        with self.assertRaises(V6FoundationError):
            detector_context(
                error_direction=DetectorErrorDirectionV1.FALSE_POSITIVE,
                supplementary_only=False,
                primary_correction_direction=False,
            )

    def test_outer_and_sealed_roles_reject(self) -> None:
        for role in (
            SplitRoleV2.OUTER_VALIDATION,
            SplitRoleV2.SEALED_EVALUATION,
            SplitRoleV2.NORMAL_RELATION_CALIBRATION,
        ):
            with self.subTest(role=role), self.assertRaises(V6FoundationError):
                detector_context(split_role=role)

    def test_split_purpose_must_match(self) -> None:
        with self.assertRaises(V6FoundationError):
            detector_context(
                split_role=SplitRoleV2.INNER_UTILITY,
                purpose=DetectorContextPurposeV1.DEVELOPMENT_DIAGNOSTIC,
            )

    def test_missing_normal_evidence_reference(self) -> None:
        with self.assertRaises(V6FoundationError):
            detector_context(normal_relation_evidence_ref="")

    def test_reference_only_boundary(self) -> None:
        for field in (
            "raw_values_included",
            "outer_data_used",
            "sealed_data_used",
            "replaces_normal_evidence",
            "validity_authority_granted",
            "runtime_authority_granted",
        ):
            with self.subTest(field=field), self.assertRaises(V6FoundationError):
                detector_context(**{field: True})

    def test_raw_serialized_field_rejected(self) -> None:
        document = detector_context().to_dict()
        document["predictions"] = [0, 1]
        with self.assertRaises(V6FoundationError):
            DetectorErrorContextV1.from_dict(document)


if __name__ == "__main__":
    unittest.main()
