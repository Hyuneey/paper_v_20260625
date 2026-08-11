from __future__ import annotations

import ast
import inspect
import subprocess
import unittest
from pathlib import Path

from paperworks.profiling import task039d1_fit_v1 as d1
from paperworks.profiling.task039d1_execution_optimization_v1 import (
    ABORTED_COMMIT_A1,
    audit_structural_complexity_v1,
)
from paperworks.v6.continuous_step_protocol_v1 import evaluate_target_response_v1


ROOT = Path(__file__).resolve().parents[1]


class TASK039D1RHotPathTests(unittest.TestCase):
    def test_structural_complexity_audit(self) -> None:
        result = audit_structural_complexity_v1()
        self.assertEqual(result["event_extraction_complexity_class"], "linear_in_sequence_length")
        self.assertIn("E log E", result["isolation_complexity_class"])

    def test_no_whole_sequence_work_in_pair_loop(self) -> None:
        tree = ast.parse(inspect.getsource(d1.evaluate_arm_blind_fit_v1))
        pair_loop = next(
            node for node in ast.walk(tree)
            if isinstance(node, ast.For)
            and isinstance(node.target, ast.Tuple)
            and any(isinstance(item, ast.Name) and item.id == "identity" for item in node.target.elts)
        )
        names = {
            node.func.id
            for node in ast.walk(pair_loop)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
        }
        self.assertTrue(
            names.isdisjoint(
                {
                    "derive_multi_file_source_parameters_v1",
                    "derive_multi_file_target_scale_v1",
                    "extract_file_local_events_linear_v1",
                    "classify_all_source_isolation_indexed_v1",
                    "tuple",
                    "list",
                }
            )
        )

    def test_target_response_optimization_semantics_retained(self) -> None:
        values = tuple(float(index % 9 - 4) for index in range(100))
        for event_index in (5, 20, 37, 96):
            for horizon in (1, 5, 10, 30, 60):
                right_censored, response = d1.optimized_target_response_v1(
                    values,
                    event_index=event_index,
                    horizon_seconds=horizon,
                )
                reference = evaluate_target_response_v1(
                    values,
                    event_index=event_index,
                    horizon_seconds=horizon,
                    target_noise_scale=1.0,
                    target_direction="increase",
                )
                self.assertEqual(right_censored, reference.right_censored)
                self.assertEqual(response, reference.target_response)

    def test_patch_scope_and_frozen_d0_sources(self) -> None:
        changed = subprocess.run(
            ["git", "diff", "--name-only", ABORTED_COMMIT_A1],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.splitlines()
        forbidden_roots = (
            "src/paperworks/v6/continuous_step_protocol_v1.py",
            "src/paperworks/v6/relation_profiling_protocol_v1.py",
            "configs/v6/task039d0_relation_profiling_protocol.json",
            "docs/task_reports/TASK-039D0_",
        )
        self.assertFalse(any(item.startswith(forbidden_roots) for item in changed), changed)


if __name__ == "__main__":
    unittest.main()
