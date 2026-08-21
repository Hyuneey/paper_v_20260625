from __future__ import annotations

import copy
import unittest

from scripts.audit_task039e3_r2r_d2_design_provenance_clarification_r1 import (
    ProvenanceValidationError,
    expected_clarification_payload,
    stable_hash,
    validate_clarification,
)


def canonical() -> dict[str, object]:
    payload = expected_clarification_payload()
    return {**payload, "artifact_hash": stable_hash(payload)}


class IndependentD2ProvenanceAttacks(unittest.TestCase):
    def test_all_semantic_attacks_are_rejected(self) -> None:
        attacks = [
            ("project_level_d0_inner_baseline_results_known_before_d2_policy_selection", False),
            ("project_level_d1_inner_baseline_results_known_before_d2_policy_selection", False),
            ("codex_design_process_d0_prediction_content_read", True),
            ("codex_design_process_d1_prediction_content_read", True),
            ("codex_design_process_d0_metric_artifact_read", True),
            ("codex_design_process_d1_metric_artifact_read", True),
            ("d2_result_observed_before_freeze", True),
            ("d2_prediction_content_observed_before_freeze", True),
            ("d2_metric_observed_before_freeze", True),
            ("d2_fusion_candidates_compared", 2),
            ("d2_hyperparameter_search_performed", True),
            ("distinct_source_count", 3),
            ("distinct_source_count_metric_tuned", True),
            ("same_second_window_tuned", True),
            ("temporal_window_parameter_exists", True),
            ("d2_design_hash", "0" * 64),
            ("d0_detector_prediction_artifact_hash", "1" * 64),
            ("d1_rule_prediction_artifact_hash", "2" * 64),
            ("test2_accessed_during_this_clarification", True),
            ("test2_accesses", 1),
            ("d2_executions", 1),
            ("design_semantics_changed", True),
            ("provenance_clarified", False),
            ("remote_egress_status", "PUSHED"),
            ("push_attempted", True),
        ]
        accepted = 0
        for key, mutation in attacks:
            value = copy.deepcopy(canonical())
            value[key] = mutation
            payload = dict(value)
            payload.pop("artifact_hash")
            value["artifact_hash"] = stable_hash(payload)
            try:
                validate_clarification(value)
            except ProvenanceValidationError:
                continue
            accepted += 1
        self.assertEqual(len(attacks), 25)
        self.assertEqual(accepted, 0)


if __name__ == "__main__":
    unittest.main()
