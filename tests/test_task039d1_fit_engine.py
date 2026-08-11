from __future__ import annotations

import json
import unittest
from array import array
from pathlib import Path

from paperworks.profiling.task039d1_fit_v1 import (
    FIT_FILES,
    FROZEN_SOURCES,
    FROZEN_TARGETS,
    SELECTED_COLUMNS,
    evaluate_arm_blind_fit_v1,
    optimized_target_response_v1,
)
from paperworks.v6.continuous_step_protocol_v1 import evaluate_target_response_v1
from paperworks.v6.relation_profiling_protocol_v1 import (
    derive_multi_file_source_parameters_v1,
    derive_multi_file_target_scale_v1,
    rank_direction_horizon_v1,
    selected_fit_gate_v1,
)


ROOT = Path(__file__).resolve().parents[1]


def _synthetic_values() -> dict[str, dict[str, array]]:
    result: dict[str, dict[str, array]] = {}
    for file_index, file_name in enumerate(FIT_FILES):
        columns: dict[str, array] = {}
        source_values = [float((index // 6 + file_index) % 2) * 10.0 for index in range(180)]
        for source in FROZEN_SOURCES:
            columns[source] = array("d", source_values)
        for target_index, target in enumerate(FROZEN_TARGETS):
            columns[target] = array("d", [float((index + target_index) % 17) for index in range(180)])
        result[file_name] = columns
    return result


class Task039D1FitEngineTests(unittest.TestCase):
    def test_optimized_response_matches_accepted_scalar_helper(self) -> None:
        values = [0.0] * 8 + [3.0] * 80
        for horizon in (1, 5, 10, 30, 60):
            observed_censored, observed_response = optimized_target_response_v1(
                values, event_index=7, horizon_seconds=horizon
            )
            reference = evaluate_target_response_v1(
                values, event_index=7, horizon_seconds=horizon,
                target_noise_scale=1.0, target_direction="increase",
            )
            self.assertEqual(observed_censored, reference.right_censored)
            self.assertEqual(observed_response, reference.target_response)

    def test_response_right_censor_and_all_horizons(self) -> None:
        values = [0.0] * 10
        for horizon in (1, 5, 10, 30, 60):
            censored, response = optimized_target_response_v1(values, event_index=5, horizon_seconds=horizon)
            if horizon == 1:
                self.assertFalse(censored)
                self.assertEqual(response, 0.0)
            else:
                self.assertTrue(censored)
                self.assertIsNone(response)

    def test_multifile_source_and_target_derivation_remain_d0_helpers(self) -> None:
        values = _synthetic_values()
        source = derive_multi_file_source_parameters_v1(tuple(values[name][FROZEN_SOURCES[0]] for name in FIT_FILES))
        target = derive_multi_file_target_scale_v1(tuple(values[name][FROZEN_TARGETS[0]] for name in FIT_FILES))
        self.assertEqual(source["status"], "supported")
        self.assertGreaterEqual(source["source_step_threshold"], 5 * source["source_noise_scale"])
        self.assertGreater(target, 0)

    def test_selection_and_gate_use_selected_candidate_only(self) -> None:
        def record(direction: str, horizon: int, consistency: float, effect: float) -> dict:
            return {
                "target_direction": direction, "horizon_seconds": horizon,
                "pooled_directional_consistency": consistency,
                "pooled_robust_effect_ratio": effect,
                "train1_selected_consistency": consistency,
                "train1_opposite_consistency": 0.0,
                "train2_selected_consistency": consistency,
                "train2_opposite_consistency": 0.0,
            }
        selected = rank_direction_horizon_v1([
            record("increase", 60, 0.9, 1.0),
            record("decrease", 5, 0.8, 5.0),
        ])
        self.assertEqual(selected["horizon_seconds"], 60)
        self.assertFalse(selected_fit_gate_v1({
            **selected, "total_usable_responses": 20,
            "train1_usable_responses": 10, "train2_usable_responses": 10,
        }))

    def test_full_synthetic_engine_produces_12_12_94_and_47(self) -> None:
        identity = json.loads((ROOT / "docs/task_reports/TASK-039D0_PROFILING_IDENTITY_VIEW.json").read_text(encoding="utf-8"))
        result = evaluate_arm_blind_fit_v1(
            identity_view_document=identity,
            fit_values=_synthetic_values(),
            fit_file_bindings={FIT_FILES[0]: "1" * 64, FIT_FILES[1]: "2" * 64},
            execution_code_commit="3" * 40,
        )
        self.assertEqual(result["source_ledger"]["record_count"], 12)
        self.assertEqual(result["target_ledger"]["record_count"], 12)
        self.assertEqual(result["directional_ledger"]["record_count"], 94)
        pair = result["pair_summary"].to_dict()
        self.assertEqual(len(pair["pair_outcomes"]), 47)
        self.assertEqual(sum(pair["directional_status_counts"].values()), 94)
        self.assertFalse(pair["lower_ranked_fallback_used"])
        for record in result["directional_ledger"]["records"]:
            self.assertFalse(record["lower_ranked_fallback_used"])
            self.assertFalse(record["candidate_arm_evidence_visible"])

    def test_exact_fit_gate_boundaries(self) -> None:
        passing = {
            "total_usable_responses": 20, "train1_usable_responses": 5,
            "train2_usable_responses": 5, "pooled_directional_consistency": 0.70,
            "train1_selected_consistency": 0.60, "train1_opposite_consistency": 0.2,
            "train2_selected_consistency": 0.60, "train2_opposite_consistency": 0.2,
            "pooled_robust_effect_ratio": 2.0,
        }
        self.assertTrue(selected_fit_gate_v1(passing))
        for name, below in (
            ("total_usable_responses", 19), ("train1_usable_responses", 4),
            ("train2_usable_responses", 4), ("pooled_directional_consistency", 0.699),
            ("train1_selected_consistency", 0.599), ("train2_selected_consistency", 0.599),
            ("pooled_robust_effect_ratio", 1.999),
        ):
            with self.subTest(name=name):
                self.assertFalse(selected_fit_gate_v1({**passing, name: below}))


if __name__ == "__main__":
    unittest.main()
