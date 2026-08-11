from __future__ import annotations

import unittest

from paperworks.v6.task039e0_rule_construction_prep_v1 import (
    AGENT_EXECUTION_AUTHORIZED,
    AGENT_RUN,
    D2_RESULT_CONSUMED,
    DETECTOR_RUNTIME_AUTHORIZED,
    FROZEN_ARM_PROTOCOLS,
    FROZEN_METRIC_POLICY,
    FROZEN_RUNTIME_BOUNDARY,
    FROZEN_VALIDITY_UTILITY_POLICY,
    HAI_ACCESSED,
    LLM_CALLED,
    REAL_CONFIRMED_RELATION_IDENTITY_CONSUMED,
    RULE_V2_CREATED,
    RULE_V2_EXECUTION_AUTHORIZED,
    CallAcceptedStateV1,
    ConstructionArmProtocolV1,
    FairGenerationBudgetPolicyV1,
    FutureGenerationCallRecordV1,
    LLMDirectNumberAblationPolicyV1,
    T2ControlActionV1,
    TASK039E0PreparationError,
    assert_preparation_boundary_v1,
    forecast_t2_budget_transition_v1,
)
from paperworks.v6.outcomes_v1 import ConstructionArmV1
from tests.task039e0_support import (
    synthetic_budget,
    synthetic_digest,
)


class ConstructionArmProtocolTests(unittest.TestCase):
    def test_all_four_main_arms_are_frozen(self) -> None:
        protocols = {item.arm: item for item in FROZEN_ARM_PROTOCOLS}
        self.assertEqual(set(protocols), set(ConstructionArmV1))
        self.assertTrue(protocols[ConstructionArmV1.T0].deterministic_template)
        self.assertFalse(protocols[ConstructionArmV1.T0].llm_generation)
        self.assertTrue(protocols[ConstructionArmV1.T1].one_shot)
        self.assertTrue(
            protocols[ConstructionArmV1.T1_B].independent_generation
        )
        self.assertFalse(
            protocols[ConstructionArmV1.T1_B].verifier_feedback_allowed
        )
        self.assertEqual(
            protocols[ConstructionArmV1.T2].allowed_control_actions,
            ("revise", "retrieve", "no_rule"),
        )

    def test_arm_semantics_cannot_be_relaxed(self) -> None:
        with self.assertRaisesRegex(
            TASK039E0PreparationError, "differs from the frozen comparison"
        ):
            ConstructionArmProtocolV1(
                arm=ConstructionArmV1.T1_B,
                deterministic_template=False,
                llm_generation=True,
                one_shot=False,
                independent_generation=True,
                verifier_feedback_allowed=True,
                allowed_control_actions=("revise",),
                generation_call_budget_binding=(
                    "equals_t2_maximum_generation_calls"
                ),
            )


class FairBudgetTests(unittest.TestCase):
    def test_t1b_t2_call_budget_equality_is_mandatory(self) -> None:
        budget = synthetic_budget()
        self.assertEqual(budget.t0_total_generation_calls, 0)
        self.assertEqual(budget.t1_total_generation_calls, 1)
        self.assertEqual(
            budget.t1b_total_generation_calls,
            budget.t2_maximum_total_generation_calls,
        )
        with self.assertRaisesRegex(
            TASK039E0PreparationError, "must equal"
        ):
            synthetic_budget(t1b_total_generation_calls=4)

    def test_result_dependent_calls_and_hidden_retries_are_rejected(self) -> None:
        with self.assertRaises(TASK039E0PreparationError):
            synthetic_budget(result_dependent_extra_calls=True)
        with self.assertRaises(TASK039E0PreparationError):
            synthetic_budget(scientific_generation_retry_policy="retry_once")

    def test_concrete_budget_has_no_production_default(self) -> None:
        with self.assertRaises(TypeError):
            FairGenerationBudgetPolicyV1()  # type: ignore[call-arg]


class T2ControlProtocolTests(unittest.TestCase):
    def setUp(self) -> None:
        self.budget = synthetic_budget()

    def test_revise_retrieve_and_no_rule_actions(self) -> None:
        revise = T2ControlActionV1(
            "revise", verifier_feedback_hash=synthetic_digest("feedback")
        )
        revised = forecast_t2_budget_transition_v1(
            calls_consumed=1, action=revise, budget=self.budget
        )
        self.assertEqual((revised.calls_after, revised.state), (2, "active"))

        retrieve = T2ControlActionV1(
            "retrieve",
            retrieved_evidence_reference=synthetic_digest("retrieval"),
        )
        retrieved = forecast_t2_budget_transition_v1(
            calls_consumed=1, action=retrieve, budget=self.budget
        )
        self.assertEqual((retrieved.calls_after, retrieved.state), (1, "active"))

        no_rule = T2ControlActionV1(
            "no_rule", no_rule_reason_code="insufficient_rule_specificity"
        )
        stopped = forecast_t2_budget_transition_v1(
            calls_consumed=1, action=no_rule, budget=self.budget
        )
        self.assertEqual((stopped.calls_after, stopped.state), (1, "no_rule"))

    def test_maximum_budget_exhaustion_cannot_add_a_call(self) -> None:
        transition = forecast_t2_budget_transition_v1(
            calls_consumed=3,
            action=T2ControlActionV1(
                "revise", verifier_feedback_hash=synthetic_digest("feedback")
            ),
            budget=self.budget,
        )
        self.assertEqual(transition.state, "budget_exhausted")
        self.assertEqual(transition.calls_after, 3)

    def test_unbounded_agent_action_is_rejected(self) -> None:
        with self.assertRaisesRegex(
            TASK039E0PreparationError, "not allowed"
        ):
            T2ControlActionV1("reflect")
        with self.assertRaises(ValueError):
            T2ControlActionV1(
                "no_rule", no_rule_reason_code="unbounded free text reason"
            )


class ReproducibilityAndAblationTests(unittest.TestCase):
    def test_future_call_receipt_records_required_reproducibility(self) -> None:
        record = FutureGenerationCallRecordV1(
            construction_arm=ConstructionArmV1.T2,
            model_identifier="synthetic_model",
            provider_identifier="synthetic_provider",
            prompt_template_version="synthetic_prompt_v1",
            temperature=0.0,
            decoding_settings={"top_p": 1.0, "max_tokens": 256},
            seed=7,
            seed_exposed=True,
            call_number=2,
            evidence_bundle_hash=synthetic_digest("evidence"),
            verifier_feedback_hash=synthetic_digest("feedback"),
            proposal_hash=synthetic_digest("proposal"),
            accepted_state=CallAcceptedStateV1.ACCEPTED,
            total_calls_consumed=2,
            independent_generation=False,
        )
        self.assertEqual(record.call_number, 2)
        self.assertFalse(record.runtime_authority_granted)

    def test_t1b_receipts_must_be_independent_and_feedback_free(self) -> None:
        base = {
            "construction_arm": ConstructionArmV1.T1_B,
            "model_identifier": "synthetic_model",
            "provider_identifier": "synthetic_provider",
            "prompt_template_version": "synthetic_prompt_v1",
            "temperature": 0.0,
            "decoding_settings": {},
            "seed": None,
            "seed_exposed": False,
            "call_number": 1,
            "evidence_bundle_hash": synthetic_digest("evidence"),
            "verifier_feedback_hash": None,
            "proposal_hash": synthetic_digest("proposal"),
            "accepted_state": CallAcceptedStateV1.CANDIDATE_PROPOSED,
            "total_calls_consumed": 1,
            "independent_generation": True,
        }
        FutureGenerationCallRecordV1(**base)
        with self.assertRaises(TASK039E0PreparationError):
            FutureGenerationCallRecordV1(
                **{**base, "independent_generation": False}
            )
        with self.assertRaises(TASK039E0PreparationError):
            FutureGenerationCallRecordV1(
                **{
                    **base,
                    "verifier_feedback_hash": synthetic_digest("feedback"),
                }
            )

    def test_direct_number_ablation_is_isolated_and_non_authorizing(self) -> None:
        budget = synthetic_budget()
        policy = LLMDirectNumberAblationPolicyV1(
            policy_id="SYNTHETIC_DIRECT_NUMBER_ABLATION_V1",
            designated_main_comparator=ConstructionArmV1.T1,
            comparator_budget_policy_hash=budget.artifact_hash,
        )
        self.assertTrue(policy.isolated_from_main_arms)
        self.assertFalse(policy.replaces_main_calibrated_method)
        self.assertFalse(policy.execute_in_preparation)
        self.assertFalse(policy.runtime_authority_granted)


class SeparationAndBoundaryTests(unittest.TestCase):
    def test_validity_utility_no_rule_and_abstention_are_separate(self) -> None:
        self.assertTrue(FROZEN_VALIDITY_UTILITY_POLICY.validity_is_label_free)
        self.assertFalse(
            FROZEN_VALIDITY_UTILITY_POLICY.utility_may_influence_validity
        )
        self.assertFalse(FROZEN_METRIC_POLICY.no_rule_is_system_failure)
        self.assertFalse(FROZEN_METRIC_POLICY.abstention_is_no_rule)
        self.assertNotEqual(
            FROZEN_METRIC_POLICY.no_rule_rate_formula,
            FROZEN_METRIC_POLICY.abstention_rate_formula,
        )

    def test_runtime_is_llm_free_and_requires_later_governance(self) -> None:
        self.assertFalse(FROZEN_RUNTIME_BOUNDARY.runtime_llm_allowed)
        self.assertFalse(
            FROZEN_RUNTIME_BOUNDARY.proposal_auto_authorizes_runtime
        )
        self.assertTrue(FROZEN_RUNTIME_BOUNDARY.later_governance_required)

    def test_prep_authority_constants_remain_false(self) -> None:
        for value in (
            D2_RESULT_CONSUMED,
            REAL_CONFIRMED_RELATION_IDENTITY_CONSUMED,
            HAI_ACCESSED,
            LLM_CALLED,
            AGENT_RUN,
            RULE_V2_CREATED,
            RULE_V2_EXECUTION_AUTHORIZED,
            AGENT_EXECUTION_AUTHORIZED,
            DETECTOR_RUNTIME_AUTHORIZED,
        ):
            self.assertFalse(value)

    def test_any_real_or_executable_input_fails_closed(self) -> None:
        assert_preparation_boundary_v1()
        for field in (
            "d2_result",
            "confirmed_real_relation_identity",
            "hai_input",
            "provider",
            "agent",
        ):
            with self.subTest(field=field), self.assertRaisesRegex(
                TASK039E0PreparationError, "accepts no real result"
            ):
                assert_preparation_boundary_v1(**{field: object()})


if __name__ == "__main__":
    unittest.main()
