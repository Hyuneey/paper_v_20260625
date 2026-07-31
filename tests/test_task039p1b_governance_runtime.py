from __future__ import annotations

import unittest

from paperworks.v6.common import V6FoundationError
from paperworks.v6.outcomes_v1 import (
    ConstructionTerminalStatusV1,
    GovernanceDecisionV1,
    RuntimeDispositionV1,
    project_runtime_disposition,
)
from tests.task039p1b_support import governance_outcome


class GovernanceAndRuntimeTests(unittest.TestCase):
    def test_selected_rule_round_trip(self) -> None:
        outcome = governance_outcome()
        self.assertEqual(type(outcome).from_json(outcome.to_json()), outcome)
        self.assertFalse(outcome.authority_binding_verified)

    def test_no_op_is_valid_rule_utility_decision(self) -> None:
        outcome = governance_outcome(
            decision=GovernanceDecisionV1.NO_OP,
            decision_reason_codes=("tie_prefers_no_op",),
            applied_rule_ref=None,
        )
        self.assertEqual(outcome.decision, GovernanceDecisionV1.NO_OP)
        self.assertNotEqual(outcome.decision.value, ConstructionTerminalStatusV1.NO_RULE.value)
        self.assertNotEqual(outcome.decision.value, RuntimeDispositionV1.ABSTAIN.value)

    def test_no_op_cannot_mean_verifier_rejection(self) -> None:
        with self.assertRaises(V6FoundationError):
            governance_outcome(
                decision=GovernanceDecisionV1.NO_OP,
                decision_reason_codes=("verifier_rejection",),
                applied_rule_ref=None,
            )

    def test_applied_rule_consistency(self) -> None:
        with self.assertRaises(V6FoundationError):
            governance_outcome(applied_rule_ref=None)
        with self.assertRaises(V6FoundationError):
            governance_outcome(
                decision=GovernanceDecisionV1.NO_OP,
                decision_reason_codes=("identity_not_worse",),
            )

    def test_validity_utility_outer_sealed_boundary(self) -> None:
        for field, value in (
            ("label_performance_used", False),
            ("outer_data_used", True),
            ("sealed_data_used", True),
            ("authority_binding_verified", True),
            ("validity_reassessed", True),
            ("utility_assessment_only", False),
            ("runtime_authority_granted", True),
        ):
            with self.subTest(field=field), self.assertRaises(V6FoundationError):
                governance_outcome(**{field: value})

    def test_runtime_projection_evaluated_nonviolation(self) -> None:
        disposition = project_runtime_disposition(
            {
                "status": "evaluated",
                "abstained": False,
                "violation_detected": False,
            }
        )
        self.assertEqual(disposition, RuntimeDispositionV1.EVALUATED)

    def test_runtime_projection_evaluated_violation(self) -> None:
        disposition = project_runtime_disposition(
            {
                "status": "evaluated",
                "abstained": False,
                "violation_detected": True,
            }
        )
        self.assertEqual(disposition, RuntimeDispositionV1.EVALUATED)

    def test_runtime_projection_abstention(self) -> None:
        disposition = project_runtime_disposition(
            {
                "status": "abstained",
                "abstained": True,
                "violation_detected": False,
            }
        )
        self.assertEqual(disposition, RuntimeDispositionV1.ABSTAIN)

    def test_runtime_projection_rejects_inconsistency(self) -> None:
        invalid = (
            {"status": "abstained", "abstained": True, "violation_detected": True},
            {"status": "abstained", "abstained": False, "violation_detected": False},
            {"status": "evaluated", "abstained": True, "violation_detected": False},
            {"status": "unknown", "abstained": False, "violation_detected": False},
        )
        for mapping in invalid:
            with self.subTest(mapping=mapping), self.assertRaises(V6FoundationError):
                project_runtime_disposition(mapping)

    def test_runtime_projection_inspects_only_bounded_shape(self) -> None:
        with self.assertRaises(V6FoundationError):
            project_runtime_disposition(
                {
                    "status": "evaluated",
                    "abstained": False,
                    "violation_detected": False,
                    "rule_hash": "not-inspected",
                }
            )


if __name__ == "__main__":
    unittest.main()
