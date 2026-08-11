import json
import unittest

from paperworks.v6.task039e3_execution_prep_v1 import (
    MockProviderEventV1,
    MockProviderTransportV1,
    ProviderCallLedgerV1,
    ScientificRunAbortV1,
    TASK039E3PreparationError,
    build_mock_336_slot_schedule_v1,
)
from paperworks.v6.task039e3_orchestration_v1 import (
    ConstructionOutcomeLedgerV1,
    ConstructionOutcomeRecordV1,
    ConstructionProposalLedgerV1,
    PublicConstructionMetricsV1,
    aggregate_construction_metrics_v1,
    aggregate_direct_number_metrics_v1,
    run_t1b_v1,
)
from task039e3_support import make_evidence, valid_core_document


class Task039E3MetricsSchedulePublicTests(unittest.TestCase):
    def test_mock_schedule_has_exactly_336_content_independent_slots(self) -> None:
        hashes = tuple(make_evidence(index).relation.binding_hash for index in range(1, 43))
        slots = build_mock_336_slot_schedule_v1(hashes)
        self.assertEqual(len(slots), 336)
        self.assertEqual(len({slot.slot_hash for slot in slots}), 336)
        counts = {
            arm: sum(slot.arm == arm for slot in slots)
            for arm in ("T1", "T1-B", "T2", "T1-DIRECT-NUMBER")
        }
        self.assertEqual(
            counts,
            {"T1": 42, "T1-B": 126, "T2": 126, "T1-DIRECT-NUMBER": 42},
        )
        self.assertTrue(all(slot.scientific for slot in slots))

    def test_common_t1b_and_t2_metrics_follow_frozen_e0_fields(self) -> None:
        records = (
            ConstructionOutcomeRecordV1(
                "SYNTHETIC_RELATION_001",
                "T0",
                "accepted_proposal",
                0,
                0,
                1,
                0,
                True,
            ),
            ConstructionOutcomeRecordV1(
                "SYNTHETIC_RELATION_001",
                "T1",
                "no_rule",
                None,
                1,
                1,
                1,
                False,
                no_rule_reason="verifier_rejection",
            ),
            ConstructionOutcomeRecordV1(
                "SYNTHETIC_RELATION_001",
                "T1-B",
                "accepted_proposal",
                2,
                3,
                3,
                1,
                False,
            ),
            ConstructionOutcomeRecordV1(
                "SYNTHETIC_RELATION_001",
                "T2",
                "accepted_proposal",
                2,
                2,
                2,
                1,
                False,
                revise_count=1,
                feedback_path="revise",
            ),
            ConstructionOutcomeRecordV1(
                "SYNTHETIC_RELATION_002",
                "T2",
                "no_rule",
                None,
                3,
                3,
                3,
                False,
                revise_count=2,
                budget_exhaustion_count=1,
                no_rule_reason="budget_exhaustion",
            ),
        )
        metrics = aggregate_construction_metrics_v1(records)
        common = {
            "accepted_proposal_count",
            "accepted_proposal_rate",
            "no_rule_count",
            "no_rule_rate",
            "verifier_rejected_proposal_count",
            "first_call_admissible_rate",
            "eventual_admissible_rate",
            "generation_calls_consumed",
            "verifier_invocations",
            "retrieval_count",
            "revise_count",
            "budget_exhaustion_count",
        }
        for arm in ("T0", "T1", "T1-B", "T2"):
            self.assertTrue(common.issubset(metrics[arm]))
        self.assertEqual(metrics["T1-B"]["selected_call_index_distribution"]["2"], 1)
        self.assertEqual(metrics["T1-B"]["any_admissible_among_3_rate"], 1.0)
        self.assertEqual(metrics["T2"]["feedback_recovery_count"], 1)
        self.assertEqual(metrics["T2"]["accepted_after_revise"], 1)
        self.assertEqual(metrics["T2"]["no_rule_due_budget_exhaustion"], 1)

    def test_future_main_outcomes_require_exact_42_by_4_zero_skip(self) -> None:
        identities = tuple(
            f"SYNTHETIC_RELATION_{index:03d}" for index in range(1, 43)
        )
        ledger = ConstructionOutcomeLedgerV1()
        for identity in identities:
            for arm in ("T0", "T1", "T1-B", "T2"):
                ledger.append(
                    ConstructionOutcomeRecordV1(
                        identity,
                        arm,
                        "accepted_proposal",
                        0 if arm == "T0" else 1,
                        0 if arm == "T0" else 1,
                        1,
                        0,
                        True,
                    )
                )
        ledger.assert_complete_future_cohort(identities)

        incomplete = ConstructionOutcomeLedgerV1()
        for record in ledger.records[:-1]:
            incomplete.append(record)
        with self.assertRaises(TASK039E3PreparationError):
            incomplete.assert_complete_future_cohort(identities)

    def test_partial_failure_custody_retains_prior_completed_slot_hashes(self) -> None:
        evidence = make_evidence()
        transport = MockProviderTransportV1(
            (
                MockProviderEventV1("valid_proposal", valid_core_document(evidence)),
                MockProviderEventV1("http_500"),
                MockProviderEventV1("http_500"),
                MockProviderEventV1("http_500"),
            )
        )
        call_ledger = ProviderCallLedgerV1()
        with self.assertRaises(ScientificRunAbortV1) as captured:
            run_t1b_v1(
                relation_schedule_index=0,
                evidence=evidence,
                transport=transport,
                call_ledger=call_ledger,
                proposal_ledger=ConstructionProposalLedgerV1(),
                outcome_ledger=ConstructionOutcomeLedgerV1(),
            )
        receipt = captured.exception.receipt
        self.assertEqual(len(call_ledger.records), 2)
        self.assertEqual(len(receipt.completed_slot_record_hashes), 2)
        self.assertFalse(receipt.automatic_resume_authority)
        self.assertFalse(receipt.relation_skipping_allowed)

    def test_public_summary_contains_only_hashes_counts_rates_and_identity(self) -> None:
        call_ledger = ProviderCallLedgerV1()
        proposal_ledger = ConstructionProposalLedgerV1()
        outcome_ledger = ConstructionOutcomeLedgerV1()
        summary = PublicConstructionMetricsV1(
            provider_call_ledger_hash=call_ledger.ledger_hash,
            proposal_ledger_hash=proposal_ledger.ledger_hash,
            outcome_ledger_hash=outcome_ledger.ledger_hash,
            main_metrics=aggregate_construction_metrics_v1(()),
            direct_number_metrics=aggregate_direct_number_metrics_v1(()),
            scientific_slot_count=0,
        )
        serialized = json.dumps(summary.to_dict(), sort_keys=True).lower()
        self.assertFalse(summary.individual_proposals_public)
        self.assertFalse(summary.raw_private_evidence_public)
        self.assertFalse(summary.rendered_prompts_public)
        self.assertFalse(summary.credentials_public)
        self.assertNotIn("proposal_core", serialized)
        self.assertNotIn("numeric_bindings", serialized)
        self.assertNotIn("authorization", serialized)
        self.assertNotIn("api_key", serialized)


if __name__ == "__main__":
    unittest.main()
