from __future__ import annotations

import json
import unittest
from dataclasses import replace
from pathlib import Path

from paperworks.v6.task039e0_rule_construction_prep_v1 import (
    FairGenerationBudgetPolicyV1,
)
from paperworks.v6.task039e0_rule_construction_protocol_v1 import (
    ConstructionEvidenceMaterializationPolicyV1,
    FairGenerationBudgetPolicyV2,
    LLMDirectNumberEvaluationPolicyV1,
    T1BSelectionPolicyV1,
    T2DeterministicControllerPolicyV1,
    TASK039E0ProtocolError,
    TASK039E0ValidityPolicyV2,
    load_confirmed_relation_cohort_v1,
    source_blob_sha256_v1,
    validity_issue_action_map_v1,
)


ROOT = Path(__file__).resolve().parents[1]


def _document(name: str):
    return json.loads((ROOT / "docs" / "task_reports" / name).read_text(encoding="utf-8"))


class CohortFreezeTests(unittest.TestCase):
    def test_exact_public_confirmed_cohort(self) -> None:
        source = _document("TASK-039D2_DIRECTIONAL_CONFIRMATION_SUMMARY.json")
        cohort = load_confirmed_relation_cohort_v1(source)
        self.assertEqual(len(cohort.relations), 42)
        self.assertEqual(len({(r.source, r.target) for r in cohort.relations}), 23)
        self.assertEqual(len({r.relation_identity for r in cohort.relations}), 42)
        self.assertFalse(cohort.private_numeric_values_included)

    def test_conflicts_are_not_included(self) -> None:
        source = _document("TASK-039D2_DIRECTIONAL_CONFIRMATION_SUMMARY.json")
        cohort = load_confirmed_relation_cohort_v1(source)
        confirmed_refs = {item.d2_confirmation_record_hash for item in cohort.relations}
        conflicts = {
            item["private_confirmation_record_hash"]
            for item in source["relations"]
            if item["confirmation_status"] == "calibration_conflict"
        }
        self.assertEqual(len(conflicts), 3)
        self.assertTrue(confirmed_refs.isdisjoint(conflicts))

    def test_wrong_public_hash_fails_closed(self) -> None:
        source = _document("TASK-039D2_DIRECTIONAL_CONFIRMATION_SUMMARY.json")
        source["artifact_hash"] = "0" * 64
        with self.assertRaises(TASK039E0ProtocolError):
            load_confirmed_relation_cohort_v1(source)


class BudgetAndTimingTests(unittest.TestCase):
    def test_prep_v1_history_remains_identity_blind(self) -> None:
        historical = FairGenerationBudgetPolicyV1(
            policy_id="SYNTHETIC_PREP_V1",
            t1b_total_generation_calls=3,
            t2_maximum_total_generation_calls=3,
        )
        self.assertTrue(historical.frozen_before_relation_identities_visible)

    def test_authoritative_v2_truthful_timing_and_budget(self) -> None:
        budget = FairGenerationBudgetPolicyV2()
        value = budget.to_dict()
        self.assertTrue(value["relation_identities_visible_at_budget_freeze"])
        self.assertTrue(value["confirmed_relation_count_known_at_budget_freeze"])
        self.assertFalse(value["calibrated_private_numeric_values_visible_at_budget_freeze"])
        self.assertFalse(value["construction_evidence_bundles_materialized_at_budget_freeze"])
        self.assertFalse(value["rule_proposals_visible_at_budget_freeze"])
        self.assertEqual(
            (value["t0_calls_per_relation"], value["t1_calls_per_relation"],
             value["t1b_calls_per_relation"], value["t2_maximum_calls_per_relation"]),
            (0, 1, 3, 3),
        )
        self.assertEqual(value["t1b_fixed_total_calls"], 126)
        self.assertEqual(value["t2_maximum_total_calls"], 126)

    def test_unequal_or_extended_budget_rejected(self) -> None:
        with self.assertRaises(TASK039E0ProtocolError):
            replace(FairGenerationBudgetPolicyV2(), t1b_calls_per_relation=4)
        with self.assertRaises(TASK039E0ProtocolError):
            replace(FairGenerationBudgetPolicyV2(), result_dependent_extra_calls=True)
        with self.assertRaises(TASK039E0ProtocolError):
            replace(FairGenerationBudgetPolicyV2(), scientific_generation_retries="retry_once")

    def test_transport_and_scientific_failures_are_separate(self) -> None:
        value = FairGenerationBudgetPolicyV2().to_dict()
        self.assertIn("provider_5xx", value["transport_retry_allowed_reasons"])
        self.assertIn("verifier_rejected_response", value["response_failures_consume_scientific_call"])


class T1BAndControllerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.budget = FairGenerationBudgetPolicyV2()
        source_hash = source_blob_sha256_v1(ROOT, "src/paperworks/v6/task039e0_validity_v1.py")
        self.validity = TASK039E0ValidityPolicyV2(self.budget.artifact_hash, source_hash)
        self.controller = T2DeterministicControllerPolicyV1(
            self.budget.artifact_hash, self.validity.artifact_hash
        )

    def test_t1b_runs_three_and_selects_lowest_admissible(self) -> None:
        policy = T1BSelectionPolicyV1(self.budget.artifact_hash)
        self.assertEqual(policy.select((False, True, True)), 2)
        self.assertEqual(policy.select((True, True, True)), 1)
        self.assertIsNone(policy.select((False, False, False)))
        with self.assertRaises(TASK039E0ProtocolError):
            policy.select((True, False))
        value = policy.to_dict()
        self.assertTrue(value["all_calls_run_even_after_admissible"])
        self.assertFalse(value["prior_proposal_visible"])
        self.assertFalse(value["verifier_feedback_visible"])

    def test_controller_accepts_admissible(self) -> None:
        self.assertEqual(
            self.controller.next_action(
                validity_status="admissible", issue_codes=(), calls_consumed=1,
                retrieval_used=False, retrievable_slice_exists=False,
            ),
            "accept",
        )

    def test_controller_stops_nonrepairable(self) -> None:
        self.assertEqual(
            self.controller.next_action(
                validity_status="rejected",
                issue_codes=("VALIDITY_RELATION_IDENTITY_MISMATCH",),
                calls_consumed=1, retrieval_used=False, retrievable_slice_exists=False,
            ),
            "no_rule",
        )

    def test_controller_retrieves_once_then_revises(self) -> None:
        kwargs = dict(
            validity_status="rejected",
            issue_codes=("VALIDITY_NUMERIC_REFERENCE_MISMATCH",),
            calls_consumed=1,
            retrievable_slice_exists=True,
        )
        self.assertEqual(self.controller.next_action(retrieval_used=False, **kwargs), "retrieve")
        self.assertEqual(self.controller.next_action(retrieval_used=True, **kwargs), "revise")

    def test_controller_revises_structural_issue(self) -> None:
        self.assertEqual(
            self.controller.next_action(
                validity_status="rejected", issue_codes=("VALIDITY_MALFORMED_DSL",),
                calls_consumed=1, retrieval_used=False, retrievable_slice_exists=False,
            ),
            "revise",
        )

    def test_controller_never_adds_fourth_call(self) -> None:
        self.assertEqual(
            self.controller.next_action(
                validity_status="rejected", issue_codes=("VALIDITY_MALFORMED_DSL",),
                calls_consumed=3, retrieval_used=False, retrievable_slice_exists=False,
            ),
            "no_rule",
        )

    def test_issue_mapping_is_closed(self) -> None:
        mapping = validity_issue_action_map_v1()
        self.assertEqual(len(mapping), 25)
        self.assertEqual(mapping["VALIDITY_PROHIBITED_DATA_REFERENCE"]["repairability"], "non_repairable")
        self.assertEqual(mapping["VALIDITY_NUMERIC_REFERENCE_MISMATCH"]["t2_action_class"], "retrieve")


class EvidenceAblationAndAuthorityTests(unittest.TestCase):
    def test_materialization_is_42_records_without_hai(self) -> None:
        cohort = _document("TASK-039E0_CONFIRMED_RELATION_COHORT.json")
        policy = ConstructionEvidenceMaterializationPolicyV1(
            cohort["artifact_hash"], cohort["identity_list_hash"]
        ).to_dict()
        self.assertEqual(policy["expected_record_count"], 42)
        self.assertFalse(policy["raw_hai_allowed"])
        self.assertTrue(policy["e1_result_requires_independent_audit_before_generation"])

    def test_direct_number_formula_and_isolation(self) -> None:
        policy = LLMDirectNumberEvaluationPolicyV1(FairGenerationBudgetPolicyV2().artifact_hash)
        self.assertEqual(policy.normalized_absolute_error(12.0, 10.0), 0.2)
        self.assertEqual(policy.normalized_absolute_error(1.0, 0.0), 1e12)
        value = policy.to_dict()
        self.assertEqual(value["designated_comparator"], "T1")
        self.assertEqual(value["generation_calls_per_relation"], 1)
        self.assertFalse(value["validity_authority_granted"])

    def test_e1_authority_is_materialization_only(self) -> None:
        auth = _document("TASK-039E1_AUTHORIZATION.json")
        self.assertTrue(auth["d1_source_private_ledger_read_authorized"])
        self.assertTrue(auth["d2_private_confirmation_ledger_read_authorized"])
        for field in (
            "hai_access_authorized", "train1_train2_train3_reread_authorized",
            "llm_calls_authorized", "t0_generation_authorized",
            "t1_t1b_t2_generation_authorized", "rule_v2_materialization_authorized",
            "agent_execution_authorized", "detector_runtime_authorized",
        ):
            self.assertFalse(auth[field])


if __name__ == "__main__":
    unittest.main()

