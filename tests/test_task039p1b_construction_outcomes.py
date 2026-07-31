from __future__ import annotations

import unittest

from paperworks.v6.common import V6FoundationError
from paperworks.v6.normal_evidence_v1 import EvidenceStatusV1
from paperworks.v6.outcomes_v1 import (
    ConstructionActionTypeV1,
    ConstructionArmV1,
    ConstructionTerminalStatusV1,
    RuleConstructionOutcomeV1,
)
from tests.task039p1b_support import action, construction_outcome, digest


class ConstructionOutcomeTests(unittest.TestCase):
    def test_every_terminal_status(self) -> None:
        cases = (
            {},
            {
                "construction_arm": ConstructionArmV1.T2,
                "normal_evidence_status": EvidenceStatusV1.INSUFFICIENT_SUPPORT,
                "candidate_rule_ref": None,
                "action_history": (action(ConstructionActionTypeV1.NO_RULE),),
                "terminal_status": ConstructionTerminalStatusV1.NO_RULE,
                "reason_codes": ("insufficient_trigger_support",),
            },
            {
                "construction_arm": ConstructionArmV1.T1,
                "candidate_rule_ref": None,
                "provider_call_budget": 1,
                "provider_calls_used": 1,
                "token_budget": 100,
                "tokens_used": 0,
                "terminal_status": ConstructionTerminalStatusV1.PROVIDER_ERROR,
                "reason_codes": ("provider_transport_error",),
                "provider_failure": True,
            },
            {
                "construction_arm": ConstructionArmV1.T1,
                "candidate_rule_ref": None,
                "provider_call_budget": 1,
                "provider_calls_used": 1,
                "token_budget": 100,
                "tokens_used": 10,
                "terminal_status": ConstructionTerminalStatusV1.INVALID_OUTPUT,
                "reason_codes": ("invalid_json",),
                "invalid_output_detected": True,
            },
            {
                "construction_arm": ConstructionArmV1.T2,
                "candidate_rule_ref": None,
                "verifier_result_refs": (digest("rejecting-verifier"),),
                "terminal_status": ConstructionTerminalStatusV1.NON_REPAIRABLE_REJECTION,
                "reason_codes": ("policy_violation",),
            },
            {
                "construction_arm": ConstructionArmV1.T1_B,
                "candidate_rule_ref": None,
                "provider_call_budget": 2,
                "provider_calls_used": 2,
                "token_budget": 200,
                "tokens_used": 150,
                "independent_generation": True,
                "terminal_status": ConstructionTerminalStatusV1.BUDGET_EXHAUSTED,
                "reason_codes": ("provider_call_budget_exhausted",),
            },
        )
        for values in cases:
            with self.subTest(status=values.get("terminal_status", "candidate")):
                outcome = construction_outcome(**values)
                self.assertEqual(
                    RuleConstructionOutcomeV1.from_json(outcome.to_json()), outcome
                )

    def test_no_rule_is_not_failure_status(self) -> None:
        self.assertNotEqual(
            ConstructionTerminalStatusV1.NO_RULE,
            ConstructionTerminalStatusV1.PROVIDER_ERROR,
        )
        self.assertNotEqual(
            ConstructionTerminalStatusV1.NO_RULE,
            ConstructionTerminalStatusV1.INVALID_OUTPUT,
        )
        self.assertNotEqual(
            ConstructionTerminalStatusV1.NO_RULE,
            ConstructionTerminalStatusV1.NON_REPAIRABLE_REJECTION,
        )
        self.assertNotEqual(
            ConstructionTerminalStatusV1.NO_RULE,
            ConstructionTerminalStatusV1.BUDGET_EXHAUSTED,
        )

    def test_no_rule_requires_evidence_reason_and_action(self) -> None:
        base = {
            "construction_arm": ConstructionArmV1.T2,
            "normal_evidence_status": EvidenceStatusV1.INSUFFICIENT_SUPPORT,
            "candidate_rule_ref": None,
            "terminal_status": ConstructionTerminalStatusV1.NO_RULE,
            "reason_codes": ("insufficient_trigger_support",),
        }
        with self.assertRaises(V6FoundationError):
            construction_outcome(**base)
        with self.assertRaises(V6FoundationError):
            construction_outcome(**{
                **base,
                "action_history": (action(ConstructionActionTypeV1.NO_RULE),),
                "reason_codes": ("provider_error",),
            })
        with self.assertRaises(V6FoundationError):
            construction_outcome(**{
                **base,
                "action_history": (action(ConstructionActionTypeV1.NO_RULE),),
                "normal_evidence_status": EvidenceStatusV1.SUPPORTED,
            })

    def test_t0_restrictions(self) -> None:
        with self.assertRaises(V6FoundationError):
            construction_outcome(provider_call_budget=1)
        with self.assertRaises(V6FoundationError):
            construction_outcome(
                action_history=(action(ConstructionActionTypeV1.REVISE),)
            )

    def test_t1_restrictions(self) -> None:
        with self.assertRaises(V6FoundationError):
            construction_outcome(
                construction_arm=ConstructionArmV1.T1,
                provider_call_budget=2,
                provider_calls_used=2,
                token_budget=100,
                action_history=(action(ConstructionActionTypeV1.RETRIEVE),),
            )

    def test_t1b_requires_independent_no_feedback(self) -> None:
        with self.assertRaises(V6FoundationError):
            construction_outcome(
                construction_arm=ConstructionArmV1.T1_B,
                independent_generation=False,
            )
        with self.assertRaises(V6FoundationError):
            construction_outcome(
                construction_arm=ConstructionArmV1.T1_B,
                independent_generation=True,
                action_history=(action(feedback=True),),
            )

    def test_action_history_order_and_raw_fields(self) -> None:
        with self.assertRaises(V6FoundationError):
            construction_outcome(action_history=(action(index=1), action(index=0)))
        document = construction_outcome().to_dict()
        document["action_history"][0]["raw_prompt"] = "forbidden"
        with self.assertRaises(V6FoundationError):
            RuleConstructionOutcomeV1.from_dict(document)

    def test_outer_sealed_and_authority_fail_closed(self) -> None:
        for field in (
            "outer_data_used",
            "sealed_data_used",
            "validity_authority_granted",
            "runtime_authority_granted",
        ):
            with self.subTest(field=field), self.assertRaises(V6FoundationError):
                construction_outcome(**{field: True})


if __name__ == "__main__":
    unittest.main()
