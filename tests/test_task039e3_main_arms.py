import unittest

from paperworks.v6.task039e3_execution_prep_v1 import (
    MAIN_PROMPT_HASH,
    MockProviderEventV1,
    MockProviderTransportV1,
    ProviderCallLedgerV1,
)
from paperworks.v6.task039e3_orchestration_v1 import (
    ConstructionOutcomeLedgerV1,
    ConstructionProposalLedgerV1,
    run_t0_v1,
    run_t1_v1,
    run_t1b_v1,
    wrap_and_verify_core_v1,
)
from task039e3_support import make_evidence, valid_core, valid_core_document


class Task039E3MainArmTests(unittest.TestCase):
    def test_t0_has_zero_provider_calls_and_one_deterministic_validity(self) -> None:
        evidence = make_evidence()
        proposals = ConstructionProposalLedgerV1()
        outcomes = ConstructionOutcomeLedgerV1()
        outcome = run_t0_v1(
            evidence=evidence,
            proposal_ledger=proposals,
            outcome_ledger=outcomes,
        )
        self.assertEqual(outcome.outcome, "accepted_proposal")
        self.assertEqual(outcome.generation_calls_consumed, 0)
        self.assertEqual(outcome.verifier_invocations, 1)
        self.assertEqual(len(proposals.records), 1)
        self.assertEqual(proposals.records[0].validity_result.status, "admissible")

    def test_t0_rejection_is_recorded_without_repair_or_fallback(self) -> None:
        outcome = run_t0_v1(
            evidence=make_evidence(),
            proposal_ledger=ConstructionProposalLedgerV1(),
            outcome_ledger=ConstructionOutcomeLedgerV1(),
            synthetic_validity_fault="SYNTHETIC_NON_REPAIRABLE",
        )
        self.assertEqual(outcome.outcome, "no_rule")
        self.assertEqual(outcome.verifier_rejected_proposal_count, 1)
        self.assertEqual(outcome.revise_count, 0)
        self.assertEqual(outcome.retrieval_count, 0)

    def test_t1_exactly_one_call_accepts_admissible(self) -> None:
        evidence = make_evidence()
        transport = MockProviderTransportV1(
            (MockProviderEventV1("valid_proposal", valid_core_document(evidence)),)
        )
        outcome = run_t1_v1(
            relation_schedule_index=0,
            evidence=evidence,
            transport=transport,
            call_ledger=ProviderCallLedgerV1(),
            proposal_ledger=ConstructionProposalLedgerV1(),
            outcome_ledger=ConstructionOutcomeLedgerV1(),
        )
        self.assertEqual(transport.calls, 1)
        self.assertEqual(outcome.outcome, "accepted_proposal")
        self.assertEqual(outcome.accepted_call_index, 1)

    def test_t1_validity_rejection_becomes_no_rule_without_second_call(self) -> None:
        evidence = make_evidence()
        transport = MockProviderTransportV1(
            (MockProviderEventV1("valid_proposal", valid_core_document(evidence)),)
        )
        outcome = run_t1_v1(
            relation_schedule_index=0,
            evidence=evidence,
            transport=transport,
            call_ledger=ProviderCallLedgerV1(),
            proposal_ledger=ConstructionProposalLedgerV1(),
            outcome_ledger=ConstructionOutcomeLedgerV1(),
            synthetic_validity_fault="SYNTHETIC_NON_REPAIRABLE",
        )
        self.assertEqual(transport.calls, 1)
        self.assertEqual(outcome.outcome, "no_rule")

    def test_t1_refusal_invalid_and_incomplete_yield_no_rule(self) -> None:
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
                proposals = ConstructionProposalLedgerV1()
                outcome = run_t1_v1(
                    relation_schedule_index=0,
                    evidence=evidence,
                    transport=transport,
                    call_ledger=ProviderCallLedgerV1(),
                    proposal_ledger=proposals,
                    outcome_ledger=ConstructionOutcomeLedgerV1(),
                )
                self.assertEqual(transport.calls, 1)
                self.assertEqual(outcome.outcome, "no_rule")
                self.assertEqual(outcome.verifier_invocations, 0)
                self.assertEqual(len(proposals.records), 0)

    def test_t1b_always_uses_three_stateless_calls_and_no_early_stop(self) -> None:
        evidence = make_evidence()
        transport = MockProviderTransportV1(
            tuple(
                MockProviderEventV1("valid_proposal", valid_core_document(evidence))
                for _ in range(3)
            )
        )
        call_ledger = ProviderCallLedgerV1()
        proposals = ConstructionProposalLedgerV1()
        outcome = run_t1b_v1(
            relation_schedule_index=0,
            evidence=evidence,
            transport=transport,
            call_ledger=call_ledger,
            proposal_ledger=proposals,
            outcome_ledger=ConstructionOutcomeLedgerV1(),
        )
        self.assertEqual(transport.calls, 3)
        self.assertEqual(len(call_ledger.records), 3)
        self.assertEqual(len(proposals.records), 3)
        self.assertEqual(len(set(transport.request_hashes)), 1)
        self.assertEqual(outcome.accepted_call_index, 1)

    def test_t1b_selects_lowest_admissible_index_after_all_three_calls(self) -> None:
        evidence = make_evidence()
        transport = MockProviderTransportV1(
            tuple(
                MockProviderEventV1("valid_proposal", valid_core_document(evidence))
                for _ in range(3)
            )
        )
        outcome = run_t1b_v1(
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
        self.assertEqual(transport.calls, 3)
        self.assertEqual(outcome.accepted_call_index, 2)

    def test_t1b_response_failures_do_not_prevent_all_three_calls(self) -> None:
        evidence = make_evidence()
        transport = MockProviderTransportV1(
            (
                MockProviderEventV1("provider_refusal"),
                MockProviderEventV1(
                    "valid_proposal", valid_core_document(evidence)
                ),
                MockProviderEventV1("schema_invalid_response"),
            )
        )
        proposals = ConstructionProposalLedgerV1()
        outcome = run_t1b_v1(
            relation_schedule_index=0,
            evidence=evidence,
            transport=transport,
            call_ledger=ProviderCallLedgerV1(),
            proposal_ledger=proposals,
            outcome_ledger=ConstructionOutcomeLedgerV1(),
        )
        self.assertEqual(transport.calls, 3)
        self.assertEqual(outcome.accepted_call_index, 2)
        self.assertEqual(outcome.verifier_invocations, 1)
        self.assertEqual(outcome.verifier_rejected_proposal_count, 0)
        self.assertEqual(len(proposals.records), 1)

    def test_e0_validity_v2_covers_admissible_repairable_and_nonrepairable(self) -> None:
        evidence = make_evidence()
        core = valid_core(evidence)
        cases = (
            (None, "admissible", None),
            ("SYNTHETIC_REPAIRABLE_REVISE", "rejected", "repairable"),
            ("SYNTHETIC_REPAIRABLE_RETRIEVE", "rejected", "repairable"),
            ("SYNTHETIC_NON_REPAIRABLE", "rejected", "non_repairable"),
        )
        for fault, status, repairability in cases:
            with self.subTest(fault=fault):
                record = wrap_and_verify_core_v1(
                    core=core,
                    evidence=evidence,
                    arm="T1",
                    call_number=1,
                    prompt_hash=MAIN_PROMPT_HASH,
                    synthetic_validity_fault=fault,
                )
                self.assertEqual(record.validity_result.status, status)
                self.assertEqual(
                    record.validity_result.verifier_version,
                    "task039e0_validity_v2",
                )
                if repairability is not None:
                    self.assertIn(
                        repairability,
                        {issue.repairability for issue in record.validity_result.issues},
                    )


if __name__ == "__main__":
    unittest.main()
