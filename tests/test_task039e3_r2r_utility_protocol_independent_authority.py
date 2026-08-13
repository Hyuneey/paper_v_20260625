from __future__ import annotations

import json
from pathlib import Path
import unittest

from paperworks.v6.common import stable_hash_v1


ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "docs" / "task_reports"


def _document(name: str) -> dict[str, object]:
    return json.loads((REPORTS / name).read_text(encoding="utf-8"))


class IndependentGovernanceAuditTests(unittest.TestCase):
    def test_protocol_bundle_and_receipt_self_verify(self) -> None:
        for name, expected in (
            ("TASK-039E3_R2R_UTILITY_PROTOCOL_BUNDLE.json", "189c662b83e82ed47137d7e67f52ff97580662ef65e696a5d5715d2dddaae86d"),
            ("TASK-039E3_R2R_UTILITY_PROTOCOL_RECEIPT.json", "f6db67c4ec4c3f64f0acc8031e27f583fc3192029170184e42dd721dbaf15949"),
        ):
            value = _document(name)
            self.assertEqual(value["artifact_hash"], expected)
            self.assertEqual(
                value["artifact_hash"],
                stable_hash_v1({key: item for key, item in value.items() if key != "artifact_hash"}),
            )

    def test_authority_remains_closed(self) -> None:
        authority = _document("TASK-039E3_R2R_UTILITY_PROTOCOL_AUTHORITY_POLICY.json")
        for field in (
            "inner_label_access",
            "outer_label_access",
            "sealed_evaluation",
            "rule_v2",
            "production_runtime",
            "deployment",
            "winner",
            "provider",
            "utility_execution",
            "utility_evaluator_implementation",
        ):
            self.assertFalse(authority[field])

    def test_claim_boundary_and_summary_label_exclusion(self) -> None:
        event = _document("TASK-039E3_R2R_UTILITY_PROTOCOL_EVENT_POLICY.json")
        self.assertEqual(
            event["primary_scope_wording"],
            "P1-bounded rule-set utility against HAI labeled attack events",
        )
        self.assertFalse(event["summary_label_required"])
        self.assertEqual(event["point_adjustment"], "PROHIBITED")

    def test_no_rule_no_op_detector_direct_and_origin_boundaries(self) -> None:
        no_rule = _document("TASK-039E3_R2R_UTILITY_PROTOCOL_NO_RULE_POLICY.json")
        authority = _document("TASK-039E3_R2R_UTILITY_PROTOCOL_AUTHORITY_POLICY.json")
        statistics = _document("TASK-039E3_R2R_UTILITY_PROTOCOL_STATISTICS_POLICY.json")
        metrics = _document("TASK-039E3_R2R_UTILITY_PROTOCOL_METRIC_POLICY.json")
        self.assertEqual(no_rule["utility_driven_no_op_selection"], "DEFERRED")
        self.assertFalse(no_rule["select_rule_or_no_op_operation_used"])
        self.assertEqual(authority["claims"]["U1"], "TESTABLE_AFTER_AUTHORIZED_LABEL_ACCESS")
        self.assertEqual(metrics["direct_number_utility"], "NOT_APPLICABLE")
        self.assertEqual(statistics["candidate_origin"], "EXPLORATORY_NONEXCLUSIVE_DESCRIPTIVE_ONLY")
        self.assertEqual(authority["claims"]["U2"], "NOT_TESTABLE_IDENTICAL_T0_T1_T1B_PREDICTIONS")

    def test_custody_public_private_boundary(self) -> None:
        custody = _document("TASK-039E3_R2R_UTILITY_PROTOCOL_CUSTODY_POLICY.json")
        public = set(custody["future_public_prohibited"])
        self.assertTrue({"raw_label_arrays", "attack_timestamps", "raw_test_rows", "raw_sensor_traces", "private_local_paths", "credentials"}.issubset(public))
        self.assertTrue(custody["private_artifacts_bound_by_public_hashes"])

    def test_hidden_degree_of_freedom_scan_is_nonzero(self) -> None:
        open_choices = {
            "logical_physical_mapping",
            "source_universe_binding",
            "numeric_private_resolver_authority",
            "event_f1_custody_preimage",
            "binary_label_input_validation",
            "normal_exposure_cross_binding",
            "t2_materiality_margin",
            "u6_cost_comparator",
            "abstention_opportunity_enumeration",
        }
        self.assertEqual(len(open_choices), 9)


if __name__ == "__main__":
    unittest.main()
