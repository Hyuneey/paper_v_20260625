from __future__ import annotations

import copy
import unittest

from paperworks.data.contracts_v2 import SplitRoleV2
from paperworks.v6.common import V6FoundationError
from paperworks.v6.normal_evidence_v1 import (
    CalibrationParameterReferenceV1,
    CalibrationParameterRoleV1,
    DistributionSummaryV1,
    EvidenceStatusV1,
    NormalRelationEvidenceV1,
    RelationStabilitySummaryV1,
    RelationSupportSummaryV1,
    ResponseDirectionV1,
    StabilityStatusV1,
)
from tests.task039p1b_support import (
    digest,
    magnitude_summary,
    stable_summary,
    supported_evidence,
)


class NormalEvidenceTests(unittest.TestCase):
    def test_supported_increase_and_decrease_round_trip(self) -> None:
        increase = supported_evidence()
        decrease = supported_evidence(
            response_direction=ResponseDirectionV1.DECREASE
        )
        self.assertEqual(
            NormalRelationEvidenceV1.from_json(increase.to_json()), increase
        )
        self.assertNotEqual(increase.artifact_hash, decrease.artifact_hash)
        self.assertFalse(increase.validity_authority_granted)

    def test_insufficient_support_may_omit_summaries(self) -> None:
        evidence = supported_evidence(
            evidence_status=EvidenceStatusV1.INSUFFICIENT_SUPPORT,
            evidence_insufficiency_reasons=("insufficient_trigger_support",),
            support_summary=RelationSupportSummaryV1(0, 0, 0, 0, 0),
            lag_summary=None,
            response_magnitude_summary=None,
            matched_normal_reference_refs=(),
            calibration_parameter_refs=(),
            stability_summary=RelationStabilitySummaryV1(
                StabilityStatusV1.NOT_ASSESSED,
                "not_assessed",
                0,
                None,
            ),
        )
        self.assertEqual(
            evidence.evidence_status, EvidenceStatusV1.INSUFFICIENT_SUPPORT
        )

    def test_unstable_requires_unstable_summary(self) -> None:
        unstable = RelationStabilitySummaryV1(
            StabilityStatusV1.UNSTABLE,
            "synthetic_replicates",
            2,
            0.9,
        )
        evidence = supported_evidence(
            evidence_status=EvidenceStatusV1.UNSTABLE,
            evidence_insufficiency_reasons=("unstable_lag",),
            stability_summary=unstable,
        )
        self.assertEqual(evidence.stability_summary.status, StabilityStatusV1.UNSTABLE)
        with self.assertRaises(V6FoundationError):
            supported_evidence(
                evidence_status=EvidenceStatusV1.UNSTABLE,
                evidence_insufficiency_reasons=("unstable_lag",),
                stability_summary=stable_summary(),
            )

    def test_support_count_equations(self) -> None:
        with self.assertRaises(V6FoundationError):
            RelationSupportSummaryV1(5, 3, 2, 1, 1)
        with self.assertRaises(V6FoundationError):
            RelationSupportSummaryV1(5, 4, 2, 1, 1)

    def test_distribution_order_and_count(self) -> None:
        with self.assertRaises(V6FoundationError):
            DistributionSummaryV1(
                3, 1.0, 0.5, 2.0, 3.0, "seconds", "synthetic", "lag"
            )
        with self.assertRaises(V6FoundationError):
            supported_evidence(
                response_magnitude_summary=DistributionSummaryV1(
                    4,
                    0.1,
                    0.2,
                    0.3,
                    0.4,
                    "unit",
                    "synthetic",
                    "absolute_response_magnitude",
                )
            )

    def test_magnitude_is_absolute(self) -> None:
        self.assertEqual(
            magnitude_summary().value_semantics, "absolute_response_magnitude"
        )
        with self.assertRaises(V6FoundationError):
            supported_evidence(
                response_magnitude_summary=DistributionSummaryV1(
                    3, -0.4, 0.1, 0.2, 0.3, "unit", "synthetic", "absolute_response_magnitude"
                )
            )

    def test_supported_requires_normal_reference_and_parameters(self) -> None:
        with self.assertRaises(V6FoundationError):
            supported_evidence(matched_normal_reference_refs=())
        with self.assertRaises(V6FoundationError):
            supported_evidence(
                calibration_parameter_refs=(
                    CalibrationParameterReferenceV1(
                        CalibrationParameterRoleV1.LAG, digest("lag-only")
                    ),
                )
            )
        with self.assertRaises(V6FoundationError):
            supported_evidence(
                lag_summary=DistributionSummaryV1(
                    0, 0.0, 0.0, None, 0.0, "seconds", "empty", "lag"
                )
            )

    def test_boundary_flags_fail_closed(self) -> None:
        for field in (
            "raw_values_included",
            "label_performance_used",
            "detector_context_used",
            "validity_authority_granted",
            "runtime_authority_granted",
        ):
            with self.subTest(field=field), self.assertRaises(V6FoundationError):
                supported_evidence(**{field: True})

    def test_prohibited_causal_claims_required(self) -> None:
        with self.assertRaises(V6FoundationError):
            supported_evidence(prohibited_claims=("physical_causality",))

    def test_split_and_cardinality_boundary(self) -> None:
        with self.assertRaises(V6FoundationError):
            supported_evidence(split_role=SplitRoleV2.INNER_UTILITY)
        with self.assertRaises(V6FoundationError):
            supported_evidence(target_variable="ACTUATOR_1")

    def test_hash_is_deterministic_and_self_verifying(self) -> None:
        left = supported_evidence()
        right = supported_evidence()
        self.assertEqual(left.artifact_hash, right.artifact_hash)
        document = left.to_dict()
        document["artifact_hash"] = digest("tampered")
        with self.assertRaises(V6FoundationError):
            NormalRelationEvidenceV1.from_dict(document)

    def test_serialized_input_is_not_mutated_and_unknown_fields_reject(self) -> None:
        source = supported_evidence().to_dict()
        original = copy.deepcopy(source)
        NormalRelationEvidenceV1.from_dict(source)
        self.assertEqual(source, original)
        source["raw_rows"] = []
        with self.assertRaises(V6FoundationError):
            NormalRelationEvidenceV1.from_dict(source)


if __name__ == "__main__":
    unittest.main()
