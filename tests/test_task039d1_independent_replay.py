from __future__ import annotations

import inspect
import json
import unittest
from pathlib import Path

import paperworks.profiling.task039d1_final_audit_v1 as audit_module
from paperworks.profiling.task039d1_execution_optimization_v1 import (
    audit_event_semantic_parity_v1,
    audit_isolation_semantic_parity_v1,
    audit_structural_complexity_v1,
)
from paperworks.profiling.task039d1_final_audit_v1 import (
    ARM_SUMMARY_HASH,
    replay_arm_summary_after_freeze_v1,
)


ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "docs" / "task_reports"


class TASK039D1IndependentReplayTests(unittest.TestCase):
    def test_replay_orchestration_does_not_call_d1_top_level(self) -> None:
        source = inspect.getsource(audit_module)
        self.assertNotIn("evaluate_arm_blind_fit_v1", source.replace(
            "This module deliberately does not call ``evaluate_arm_blind_fit_v1``.", ""
        ))
        for primitive in (
            "derive_multifile_source_screening_diagnostics_v1",
            "derive_multifile_robust_scale_v1",
            "extract_sustained_step_events_file_local_v1",
            "classify_multisource_isolation_v1",
            "evaluate_direction_candidate_v1",
            "select_direction_candidate_v1",
            "fit_candidate_passes_v1",
        ):
            self.assertIn(primitive, source)

    def test_complexity_parity_and_structural_guards_rerun(self) -> None:
        audit_event_semantic_parity_v1()
        audit_isolation_semantic_parity_v1()
        result = audit_structural_complexity_v1()
        self.assertEqual(result["event_extraction_complexity_class"], "linear_in_sequence_length")
        self.assertEqual(result["isolation_complexity_class"], "O(E log E)_with_fixed_12_source_context")

    def test_provenance_join_reproduces_committed_fit_only_summary(self) -> None:
        pair = json.loads((REPORTS / "TASK-039D1_PAIR_FIT_SUMMARY.json").read_text(encoding="utf-8"))
        provenance = json.loads((REPORTS / "TASK-039D0_PROVENANCE_ANALYSIS_VIEW.json").read_text(encoding="utf-8"))
        original = json.loads((REPORTS / "TASK-039D1_ARM_FIT_SUMMARY.json").read_text(encoding="utf-8"))
        # This test uses only frozen public statuses; the raw replay separately
        # binds the directional records before this join becomes reachable.
        directional = {
            "records": [
                {
                    "source": outcome["source"],
                    "target": outcome["target"],
                    "source_step_direction": direction,
                    "fit_result": outcome[f"{direction}_status"],
                }
                for outcome in pair["pair_outcomes"]
                for direction in ("step_up", "step_down")
            ]
        }
        observed = replay_arm_summary_after_freeze_v1(
            pair_summary=pair,
            provenance_document=provenance,
            original_arm_summary=original,
            directional_ledger=directional,
        )
        self.assertEqual(observed["artifact_hash"], ARM_SUMMARY_HASH)
        self.assertFalse(observed["winner_selected"])
        self.assertTrue(observed["same_pair_same_d1_outcome_across_all_origin_arms"])


if __name__ == "__main__":
    unittest.main()
