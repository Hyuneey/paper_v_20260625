from __future__ import annotations

import unittest
from dataclasses import replace

from paperworks.v6.task039e2_execution_freeze_prep_v1 import (
    DIRECT_NUMBER_ROLE_REQUIREMENT,
    ProviderNeutralPromptEnvelopeV1,
    T2RetrievalCorpusPolicyV1,
    TASK039E2PreparationError,
    assert_private_input_boundary_v1,
    render_initial_prompt_v1,
    render_t2_followup_prompt_v1,
)
from tests.task039e2_support import (
    synthetic_hash,
    synthetic_prompt_template,
    synthetic_view,
)


class InputPromptAndRetrievalTests(unittest.TestCase):
    def test_t1_t1b_and_t2_call1_receive_exact_same_scientific_content(self) -> None:
        view = synthetic_view()
        prompts = [
            render_initial_prompt_v1(
                view=view,
                template=synthetic_prompt_template("T1"),
                call_number=1,
            ),
            *[
                render_initial_prompt_v1(
                    view=view,
                    template=synthetic_prompt_template("T1-B"),
                    call_number=index,
                )
                for index in (1, 2, 3)
            ],
            render_initial_prompt_v1(
                view=view,
                template=synthetic_prompt_template("T2_CALL_1"),
                call_number=1,
            ),
        ]
        self.assertEqual(
            {item.scientific_content_hash for item in prompts},
            {view.initial_evidence_corpus_hash},
        )
        self.assertTrue(
            all(item.scientific_content == prompts[0].scientific_content for item in prompts)
        )

    def test_t1b_calls_are_stateless_with_no_cross_call_memory(self) -> None:
        prompt = render_initial_prompt_v1(
            view=synthetic_view(),
            template=synthetic_prompt_template("T1-B"),
            call_number=2,
        )
        self.assertTrue(prompt.stateless_call)
        self.assertFalse(prompt.previous_t1b_proposal_visible)
        self.assertFalse(prompt.previous_t1b_verifier_result_visible)
        with self.assertRaisesRegex(TASK039E2PreparationError, "must remain false"):
            replace(prompt, previous_t1b_proposal_visible=True)

    def test_retrieve_re_presents_only_initial_corpus_identities(self) -> None:
        view = synthetic_view()
        policy = T2RetrievalCorpusPolicyV1(view.initial_evidence_corpus_hash)
        requested = tuple(dict.fromkeys(view.evidence_identities))[:3]
        representation = policy.targeted_represent(
            view=view,
            requested_evidence_identities=requested,
            retrieval_actions_already_used=0,
        )
        self.assertEqual(
            representation.underlying_corpus_hash,
            view.initial_evidence_corpus_hash,
        )
        self.assertFalse(representation.new_information_introduced)
        self.assertTrue(set(requested).issubset(set(view.evidence_identities)))

    def test_retrieve_rejects_new_evidence_and_second_action(self) -> None:
        view = synthetic_view()
        policy = T2RetrievalCorpusPolicyV1(view.initial_evidence_corpus_hash)
        with self.assertRaisesRegex(TASK039E2PreparationError, "new evidence"):
            policy.targeted_represent(
                view=view,
                requested_evidence_identities=(synthetic_hash("new-d1-measurement"),),
                retrieval_actions_already_used=0,
            )
        with self.assertRaisesRegex(TASK039E2PreparationError, "already exhausted"):
            policy.targeted_represent(
                view=view,
                requested_evidence_identities=(view.evidence_identities[0],),
                retrieval_actions_already_used=1,
            )

    def test_t2_followup_is_bounded_and_chain_of_thought_free(self) -> None:
        view = synthetic_view()
        policy = T2RetrievalCorpusPolicyV1(view.initial_evidence_corpus_hash)
        representation = policy.targeted_represent(
            view=view,
            requested_evidence_identities=(view.evidence_identities[0],),
            retrieval_actions_already_used=0,
        )
        prompt = render_t2_followup_prompt_v1(
            view=view,
            template=synthetic_prompt_template("T2_FOLLOWUP"),
            call_number=2,
            verifier_issue_codes=("numeric_reference_mismatch",),
            affected_fields=("source_threshold_reference",),
            previous_proposal_hash=synthetic_hash("previous-proposal"),
            retrieved=representation,
        )
        self.assertFalse(prompt.chain_of_thought_included)
        self.assertEqual(
            prompt.represented_evidence_identities,
            representation.represented_evidence_identities,
        )

    def test_raw_hai_label_utility_and_candidate_results_are_rejected(self) -> None:
        for key in (
            "raw_hai",
            "labels",
            "attacks",
            "test_outcomes",
            "utility_results",
            "candidate_method_performance",
        ):
            with self.subTest(key=key):
                with self.assertRaisesRegex(
                    TASK039E2PreparationError, "prohibited construction input"
                ):
                    assert_private_input_boundary_v1({key: [1, 2, 3]})
        with self.assertRaisesRegex(TASK039E2PreparationError, "raw_hai"):
            replace(synthetic_view(), raw_hai_included=True)

    def test_direct_number_roles_remain_unbound_until_later_freeze(self) -> None:
        template = synthetic_prompt_template("T1-DIRECT-NUMBER")
        view = synthetic_view()
        self.assertEqual(template.prompt_family, "T1-DIRECT-NUMBER")
        self.assertFalse(DIRECT_NUMBER_ROLE_REQUIREMENT.numeric_roles_bound)
        self.assertEqual(DIRECT_NUMBER_ROLE_REQUIREMENT.bound_numeric_roles, ())
        with self.assertRaisesRegex(TASK039E2PreparationError, "later E2 freeze"):
            DIRECT_NUMBER_ROLE_REQUIREMENT.assert_ready_for_call()
        with self.assertRaisesRegex(TASK039E2PreparationError, "initial prompt"):
            ProviderNeutralPromptEnvelopeV1(
                prompt_family="T1-DIRECT-NUMBER",
                template_contract_hash=template.artifact_hash,
                relation_identity=view.relation_identity,
                call_number=1,
                scientific_content=view.scientific_content_dict(),
                scientific_content_hash=view.initial_evidence_corpus_hash,
                stateless_call=True,
                verifier_issue_codes=("feedback_not_allowed",),
            )


if __name__ == "__main__":
    unittest.main()
