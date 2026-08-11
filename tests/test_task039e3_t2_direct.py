import unittest

from paperworks.v6.task039e3_execution_prep_v1 import (
    MockProviderEventV1,
    MockProviderTransportV1,
    ProviderCallLedgerV1,
    ProviderCallSlotV1,
    TASK039E3PreparationError,
)
from paperworks.v6.task039e3_orchestration_v1 import (
    ConstructionOutcomeLedgerV1,
    ConstructionProposalLedgerV1,
    aggregate_direct_number_metrics_v1,
    retrieve_existing_evidence_v1,
    run_direct_number_v1,
    run_t2_v1,
)
from task039e3_support import (
    direct_number_payload,
    make_evidence,
    valid_core_document,
)


def _valid_events(evidence, count: int):
    return tuple(
        MockProviderEventV1("valid_proposal", valid_core_document(evidence))
        for _ in range(count)
    )


class Task039E3T2DirectTests(unittest.TestCase):
    def test_t2_admissible_call_one_stops_early(self) -> None:
        evidence = make_evidence()
        transport = MockProviderTransportV1(_valid_events(evidence, 1))
        outcome = run_t2_v1(
            relation_schedule_index=0,
            evidence=evidence,
            transport=transport,
            call_ledger=ProviderCallLedgerV1(),
            proposal_ledger=ConstructionProposalLedgerV1(),
            outcome_ledger=ConstructionOutcomeLedgerV1(),
        )
        self.assertEqual(outcome.accepted_call_index, 1)
        self.assertEqual(transport.calls, 1)
        self.assertEqual(outcome.revise_count, 0)
        self.assertEqual(outcome.retrieval_count, 0)

    def test_t2_revise_then_accept(self) -> None:
        evidence = make_evidence()
        transport = MockProviderTransportV1(_valid_events(evidence, 2))
        outcome = run_t2_v1(
            relation_schedule_index=0,
            evidence=evidence,
            transport=transport,
            call_ledger=ProviderCallLedgerV1(),
            proposal_ledger=ConstructionProposalLedgerV1(),
            outcome_ledger=ConstructionOutcomeLedgerV1(),
            synthetic_validity_faults=(
                "SYNTHETIC_REPAIRABLE_REVISE",
                None,
                None,
            ),
        )
        self.assertEqual(outcome.accepted_call_index, 2)
        self.assertEqual(outcome.revise_count, 1)
        self.assertEqual(outcome.feedback_path, "revise")
        self.assertEqual(transport.calls, 2)

    def test_t2_same_corpus_retrieve_then_accept(self) -> None:
        evidence = make_evidence()
        retrieval_identity = evidence.approved_evidence_identities[0]
        transport = MockProviderTransportV1(_valid_events(evidence, 2))
        outcome = run_t2_v1(
            relation_schedule_index=0,
            evidence=evidence,
            transport=transport,
            call_ledger=ProviderCallLedgerV1(),
            proposal_ledger=ConstructionProposalLedgerV1(),
            outcome_ledger=ConstructionOutcomeLedgerV1(),
            synthetic_validity_faults=(
                "SYNTHETIC_REPAIRABLE_RETRIEVE",
                None,
                None,
            ),
            retrieval_identity=retrieval_identity,
        )
        self.assertEqual(outcome.accepted_call_index, 2)
        self.assertEqual(outcome.retrieval_count, 1)
        self.assertEqual(outcome.feedback_path, "retrieve")
        self.assertEqual(transport.calls, 2)

    def test_t2_nonrepairable_stops_no_rule(self) -> None:
        evidence = make_evidence()
        transport = MockProviderTransportV1(_valid_events(evidence, 1))
        outcome = run_t2_v1(
            relation_schedule_index=0,
            evidence=evidence,
            transport=transport,
            call_ledger=ProviderCallLedgerV1(),
            proposal_ledger=ConstructionProposalLedgerV1(),
            outcome_ledger=ConstructionOutcomeLedgerV1(),
            synthetic_validity_faults=(
                "SYNTHETIC_NON_REPAIRABLE",
                None,
                None,
            ),
        )
        self.assertEqual(outcome.outcome, "no_rule")
        self.assertEqual(outcome.no_rule_reason, "non_repairable_issue")
        self.assertEqual(transport.calls, 1)

    def test_t2_unstructured_scientific_response_stops_no_rule(self) -> None:
        evidence = make_evidence()
        for scenario in (
            "provider_refusal",
            "schema_invalid_response",
            "incomplete_response",
        ):
            with self.subTest(scenario=scenario):
                transport = MockProviderTransportV1(
                    (MockProviderEventV1(scenario),)
                )
                outcome = run_t2_v1(
                    relation_schedule_index=0,
                    evidence=evidence,
                    transport=transport,
                    call_ledger=ProviderCallLedgerV1(),
                    proposal_ledger=ConstructionProposalLedgerV1(),
                    outcome_ledger=ConstructionOutcomeLedgerV1(),
                )
                self.assertEqual(outcome.outcome, "no_rule")
                self.assertEqual(outcome.generation_calls_consumed, 1)
                self.assertEqual(outcome.verifier_invocations, 0)
                self.assertEqual(transport.calls, 1)

    def test_t2_budget_exhaustion_has_no_call_four(self) -> None:
        evidence = make_evidence()
        transport = MockProviderTransportV1(_valid_events(evidence, 3))
        outcome = run_t2_v1(
            relation_schedule_index=0,
            evidence=evidence,
            transport=transport,
            call_ledger=ProviderCallLedgerV1(),
            proposal_ledger=ConstructionProposalLedgerV1(),
            outcome_ledger=ConstructionOutcomeLedgerV1(),
            synthetic_validity_faults=(
                "SYNTHETIC_REPAIRABLE_REVISE",
                "SYNTHETIC_REPAIRABLE_REVISE",
                "SYNTHETIC_REPAIRABLE_REVISE",
            ),
        )
        self.assertEqual(outcome.outcome, "no_rule")
        self.assertEqual(outcome.no_rule_reason, "budget_exhaustion")
        self.assertEqual(outcome.budget_exhaustion_count, 1)
        self.assertEqual(transport.calls, 3)
        with self.assertRaises(TASK039E3PreparationError):
            ProviderCallSlotV1(
                0, evidence.relation.binding_hash, "T2", 4, True
            )

    def test_t2_new_identity_and_second_retrieval_are_hard_failures(self) -> None:
        view = make_evidence().render_view()
        with self.assertRaises(TASK039E3PreparationError):
            retrieve_existing_evidence_v1(
                view=view,
                requested_evidence_identities=("SYNTHETIC_NEW_EVIDENCE",),
                retrieval_actions_already_used=0,
            )
        with self.assertRaises(TASK039E3PreparationError):
            retrieve_existing_evidence_v1(
                view=view,
                requested_evidence_identities=(view.approved_evidence_identities[0],),
                retrieval_actions_already_used=1,
            )

    def test_direct_number_exact_roles_and_normalized_errors(self) -> None:
        evidence = make_evidence()
        transport = MockProviderTransportV1(
            (
                MockProviderEventV1(
                    "valid_direct_number",
                    direct_number_payload(
                        threshold=987.125,
                        tolerance=654.375,
                        target_scale=643.75,
                    ),
                ),
            )
        )
        outcome = run_direct_number_v1(
            relation_schedule_index=0,
            evidence=evidence,
            transport=transport,
            call_ledger=ProviderCallLedgerV1(),
        )
        self.assertEqual(
            set(outcome.normalized_absolute_errors),
            {
                "source_step_threshold",
                "source_stability_tolerance",
                "target_noise_scale",
            },
        )
        self.assertEqual(outcome.normalized_absolute_errors["target_noise_scale"], 1.0)
        self.assertFalse(outcome.validity_authority)
        self.assertFalse(outcome.runtime_authority)

    def test_direct_number_invalid_and_sign_domain_metrics_remain_separate(self) -> None:
        evidence = make_evidence()
        invalid = run_direct_number_v1(
            relation_schedule_index=0,
            evidence=evidence,
            transport=MockProviderTransportV1(
                (MockProviderEventV1("schema_invalid_response"),)
            ),
            call_ledger=ProviderCallLedgerV1(),
        )
        sign_violation = run_direct_number_v1(
            relation_schedule_index=0,
            evidence=evidence,
            transport=MockProviderTransportV1(
                (
                    MockProviderEventV1(
                        "valid_direct_number",
                        direct_number_payload(threshold=-1.0),
                    ),
                )
            ),
            call_ledger=ProviderCallLedgerV1(),
        )
        metrics = aggregate_direct_number_metrics_v1((invalid, sign_violation))
        self.assertEqual(metrics["missing_number_rate"], 0.5)
        self.assertEqual(metrics["nonfinite_or_parse_failure_rate"], 0.5)
        self.assertEqual(metrics["sign_domain_violation_rate"], 0.5)
        self.assertNotIn("accepted_proposal_rate", metrics)


if __name__ == "__main__":
    unittest.main()
