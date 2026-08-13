from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
import unittest

from paperworks.v6.common import stable_hash_v1
from paperworks.v6.task039e3_orchestration_v1 import ConstructionOutcomeRecordV1, DirectNumberOutcomeV1, aggregate_construction_metrics_v1, aggregate_direct_number_metrics_v1
from paperworks.v6.task039e3_scientific_execution_v1 import _direct_summary
from task039e3_terminal_audit_support import final_private_root, public_root, relation_binding_to_identity, verified_artifact


class TerminalMetricsAuditTests(unittest.TestCase):
    def setUp(self) -> None:
        final = final_private_root()
        self.provider = verified_artifact(final / "TASK039E3_R2R_SCIENTIFIC_PROVIDER_LEDGER.json")["records"]
        self.proposals = verified_artifact(final / "TASK039E3_R2R_PROPOSAL_VALIDITY_LEDGER.json")["records"]
        self.outcomes_raw = verified_artifact(final / "TASK039E3_R2R_CONSTRUCTION_OUTCOME_LEDGER.json")["records"]
        self.direct_raw = verified_artifact(final / "TASK039E3_R2R_DIRECT_NUMBER_LEDGER.json")["records"]
        self.construction_metrics = verified_artifact(public_root() / "TASK-039E3_R2R_CONSTRUCTION_METRICS.json")
        self.direct_metrics = verified_artifact(public_root() / "TASK-039E3_R2R_DIRECT_NUMBER_METRICS.json")
        self.summary = verified_artifact(public_root() / "TASK-039E3_R2R_EXECUTION_SUMMARY.json")
        self.receipt = verified_artifact(public_root() / "TASK-039E3_R2R_EXECUTION_RECEIPT.json")

    def test_proposal_hashes_validity_counts_and_explained_missing_proposal(self) -> None:
        self.assertEqual(Counter(record["arm"] for record in self.proposals), {"T0": 42, "T1": 42, "T1-B": 125, "T2": 42})
        record_hashes = set()
        for record in self.proposals:
            project = record["project_proposal"]
            validity = record["validity_result"]
            self.assertEqual(stable_hash_v1({key: value for key, value in project.items() if key != "proposal_hash"}), record["proposal_hash"])
            self.assertEqual(project["proposal_hash"], record["proposal_hash"])
            self.assertEqual(stable_hash_v1({key: value for key, value in validity.items() if key != "artifact_hash"}), record["validity_hash"])
            self.assertEqual(validity["artifact_hash"], record["validity_hash"])
            self.assertEqual(project["relation_identity"], record["relation_identity"])
            self.assertNotIn(record["record_hash"], record_hashes)
            record_hashes.add(record["record_hash"])
        missing = [record for record in self.provider if record["slot"]["arm"] != "T1-DIRECT-NUMBER" and record["proposal_core_hash"] is None]
        self.assertEqual(len(missing), 1)
        item = missing[0]
        self.assertEqual((item["slot"]["arm"], item["slot"]["relation_schedule_index"], item["slot"]["arm_local_call_number"]), ("T1-B", 19, 2))
        self.assertEqual(item["parse_status"], "schema_parse_failure")
        self.assertTrue(item["response_present"])
        identity = relation_binding_to_identity(self.proposals, item["slot"]["relation_binding_hash"])
        outcome = next(record for record in self.outcomes_raw if record["relation_identity"] == identity and record["arm"] == "T1-B")
        self.assertEqual(outcome["outcome"], "accepted_proposal")
        self.assertEqual(outcome["accepted_call_index"], 1)
        self.assertEqual(outcome["generation_calls_consumed"], 3)
        self.assertEqual(outcome["verifier_invocations"], 2)
        self.assertEqual(outcome["verifier_rejected_proposal_count"], 0)

    def test_proposal_record_hash_preimage_is_omitted_from_terminal_custody(self) -> None:
        """Freeze the result-authority blocker without reading E1 or repairing source."""

        self.assertTrue(all("proposal_envelope" not in record for record in self.proposals))
        working = final_private_root().parent / "scientific_r2r_v1/proposals_working.jsonl"
        working_records = [json.loads(line) for line in working.read_text(encoding="utf-8").splitlines()]
        self.assertEqual(working_records, self.proposals)
        source = (Path(__file__).parents[1] / "src/paperworks/v6/task039e3_orchestration_v1.py").read_text(encoding="utf-8")
        formula = source[source.index("    def record_hash(self) -> str:", source.index("class ConstructionProposalRecordV1")):]
        formula = formula[: formula.index("class ConstructionProposalLedgerV1")]
        self.assertIn('"proposal_envelope": _envelope_to_dict(self.proposal_envelope)', formula)
        self.assertIn('"proposal_hash": self.proposal_hash', formula)
        self.assertIn('"validity_hash": self.validity_hash', formula)
        # The recorded values are preserved and well formed, but their complete
        # preimages cannot be reconstructed from either preserved terminal log.
        self.assertEqual(len({record["record_hash"] for record in self.proposals}), 251)
        self.assertTrue(all(len(record["record_hash"]) == 64 for record in self.proposals))

    def test_parse_statuses_and_t2_call_one_termination(self) -> None:
        by_arm = {
            arm: Counter(record["parse_status"] for record in self.provider if record["slot"]["arm"] == arm)
            for arm in ("T1", "T1-B", "T2", "T1-DIRECT-NUMBER")
        }
        self.assertEqual(by_arm["T1"], {"valid_structured": 42})
        self.assertEqual(by_arm["T1-B"], {"valid_structured": 125, "schema_parse_failure": 1})
        self.assertEqual(by_arm["T2"], {"valid_structured": 42})
        self.assertEqual(by_arm["T1-DIRECT-NUMBER"], {"valid_structured": 42})
        t2 = [record for record in self.outcomes_raw if record["arm"] == "T2"]
        self.assertTrue(all(record["generation_calls_consumed"] == 1 for record in t2))
        self.assertEqual(Counter((record["outcome"], record["no_rule_reason"]) for record in t2), {("accepted_proposal", None): 39, ("no_rule", "non_repairable_issue"): 3})
        self.assertEqual(sum(record["retrieval_count"] for record in t2), 0)
        self.assertEqual(sum(record["revise_count"] for record in t2), 0)
        self.assertEqual(sum(record["budget_exhaustion_count"] for record in t2), 0)

    def test_construction_and_direct_metrics_recompute_exactly(self) -> None:
        outcomes = tuple(ConstructionOutcomeRecordV1(**{key: value for key, value in record.items() if key != "artifact_hash"}) for record in self.outcomes_raw)
        direct = tuple(
            DirectNumberOutcomeV1(
                relation_identity=record["relation_identity"], parse_status=record["parse_status"],
                normalized_absolute_errors=record["normalized_absolute_errors"], missing_number=record["missing_number"],
                nonfinite_or_parse_failure=record["nonfinite_or_parse_failure"], sign_domain_violation_roles=tuple(record["sign_domain_violation_roles"]),
                generation_calls_consumed=record["generation_calls_consumed"], validity_authority=record["validity_authority"], runtime_authority=record["runtime_authority"],
            ) for record in self.direct_raw
        )
        self.assertEqual(aggregate_construction_metrics_v1(outcomes), self.construction_metrics["main_metrics"])
        direct_summary = _direct_summary(aggregate_direct_number_metrics_v1(direct), direct)
        for key, value in direct_summary.items():
            self.assertEqual(self.direct_metrics[key], value)
        self.assertEqual(self.direct_metrics["missing_number_rate"], 0.0)
        self.assertEqual(self.direct_metrics["nonfinite_or_parse_failure_rate"], 0.0)
        self.assertEqual(self.direct_metrics["sign_domain_violation_rate"], 0.0)

    def test_fresh_historical_lifetime_capability_and_integrity_accounting(self) -> None:
        typed = self.receipt["typed_accounting"]
        self.assertEqual(typed, self.summary["typed_accounting"])
        self.assertEqual((typed["historical_original_r2_scientific_logical_calls"], typed["historical_zero_contact_r2r_scientific_logical_calls"], typed["historical_partial_r2r_scientific_logical_calls"], typed["historical_scientific_logical_calls_total"]), (1, 0, 5, 6))
        self.assertEqual((typed["r2r_scientific_logical_calls"], typed["lifetime_scientific_logical_call_attempts"]), (252, 258))
        self.assertEqual((typed["r2r_scientific_transport_attempts"], typed["r2r_scientific_transport_retries"], typed["scientific_generation_retries"]), (252, 0, 0))
        self.assertEqual((typed["cumulative_real_provider_capability_probes"], typed["additional_capability_probes"], typed["historical_partial_records_reused"]), (2, 0, 0))
        self.assertEqual(self.receipt["postcontact_integrity_status"], "verified_unchanged")
        self.assertFalse(self.receipt["historical_partial_results_reused"])
        self.assertFalse(self.receipt["rule_v2_authorized"])
        self.assertFalse(self.receipt["runtime_authority"])
        self.assertFalse(self.receipt["utility_evaluation_authorized"])
        self.assertFalse(self.receipt["winner_selected"])


if __name__ == "__main__":
    unittest.main()
