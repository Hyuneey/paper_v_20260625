from __future__ import annotations

import copy
import unittest
from pathlib import Path

from scripts.audit_task039e3_r2r_d2_design_provenance_clarification_r1 import (
    D2_DESIGN_HASH,
    ProvenanceValidationError,
    expected_clarification_payload,
    stable_hash,
    validate_clarification,
    validate_original_freeze,
)


ROOT = Path(__file__).resolve().parents[1]


def document() -> dict[str, object]:
    payload = expected_clarification_payload()
    return {**payload, "artifact_hash": stable_hash(payload)}


class D2ProvenanceClarificationTests(unittest.TestCase):
    def test_original_freeze_and_design_hash(self) -> None:
        result = validate_original_freeze(ROOT)
        self.assertEqual(result["d2_design_hash"], D2_DESIGN_HASH)
        self.assertEqual(result["original_d2_artifacts_changed_count"], 0)

    def test_canonical_clarification(self) -> None:
        self.assertEqual(validate_clarification(document()), document()["artifact_hash"])

    def test_closed_schema_and_self_hash(self) -> None:
        value = document()
        value["unexpected"] = False
        payload = dict(value)
        payload.pop("artifact_hash")
        value["artifact_hash"] = stable_hash(payload)
        with self.assertRaises(ProvenanceValidationError):
            validate_clarification(value)

    def test_semantic_mutations_reject_after_rehash(self) -> None:
        mutations = {
            "codex_design_process_d0_prediction_content_read": True,
            "codex_design_process_d1_prediction_content_read": True,
            "codex_design_process_d0_metric_artifact_read": True,
            "codex_design_process_d1_metric_artifact_read": True,
            "project_level_d0_inner_baseline_results_known_before_d2_policy_selection": False,
            "project_level_d1_inner_baseline_results_known_before_d2_policy_selection": False,
            "project_level_inner_baseline_characterization_informed_d2_problem_formulation": False,
            "d2_result_observed_before_freeze": True,
            "d2_fusion_candidates_compared": 1,
            "d2_hyperparameter_search_performed": True,
        }
        for key, mutation in mutations.items():
            with self.subTest(key=key):
                value = copy.deepcopy(document())
                value[key] = mutation
                payload = dict(value)
                payload.pop("artifact_hash")
                value["artifact_hash"] = stable_hash(payload)
                with self.assertRaises(ProvenanceValidationError):
                    validate_clarification(value)


if __name__ == "__main__":
    unittest.main()
