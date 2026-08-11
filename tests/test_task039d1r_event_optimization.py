from __future__ import annotations

import ast
import inspect
import unittest
from collections.abc import Iterator, Sequence

from paperworks.profiling.task039d1_execution_optimization_v1 import (
    audit_event_semantic_parity_v1,
    extract_file_local_events_linear_v1,
    extract_sustained_step_events_linear_v1,
)
from paperworks.v6.relation_profiling_protocol_v1 import FIT_FILES, extract_file_local_events_v1


class CountingSequence(Sequence[float]):
    def __init__(self, size: int) -> None:
        self.size = size
        self.element_reads = 0

    def __len__(self) -> int:
        return self.size

    def __getitem__(self, index: int) -> float:
        if index < 0:
            index += self.size
        if index < 0 or index >= self.size:
            raise IndexError(index)
        self.element_reads += 1
        return 0.0

    def __iter__(self) -> Iterator[float]:
        for index in range(self.size):
            yield self[index]


class TASK039D1REventOptimizationTests(unittest.TestCase):
    def _parity(self, values: Sequence[float], threshold: float, tolerance: float) -> None:
        files = {FIT_FILES[0]: values, FIT_FILES[1]: tuple(values)}
        expected = extract_file_local_events_v1(
            files,
            source_step_threshold=threshold,
            source_stability_tolerance=tolerance,
        )
        observed = extract_file_local_events_linear_v1(
            files,
            source_step_threshold=threshold,
            source_stability_tolerance=tolerance,
        )
        self.assertEqual(observed, expected)

    def test_preflight_parity_suite(self) -> None:
        audit_event_semantic_parity_v1()

    def test_threshold_and_direction_boundaries(self) -> None:
        self._parity([0.0] * 10 + [1.0] * 20, 1.0, 0.0)
        self._parity([0.0] * 10 + [1.0] * 20, 1.0000000001, 0.0)
        self._parity([2.0] * 10 + [-1.0] * 20, 2.0, 0.0)
        self._parity([-3.5] * 10 + [-1.25] * 20, 1.0, 0.0)

    def test_stability_boundaries_and_equal_levels(self) -> None:
        # Four of five values lie exactly at the median/tolerance boundary.
        values = [0.0] * 5 + [0.0, 0.0, 0.0, 0.0, 2.0] + [5.0] * 20
        self._parity(values, 1.0, 0.0)
        values_below = [0.0] * 5 + [0.0, 0.0, 0.0, 2.0, 3.0] + [5.0] * 20
        self._parity(values_below, 1.0, 0.0)
        self._parity([1.0] * 40, 0.5, 0.0)

    def test_boundaries_clustering_ties_dense_and_long_sparse(self) -> None:
        self._parity([0.0] * 4 + [5.0] * 30, 1.0, 0.0)
        self._parity([0.0] * 12 + [2.0] * 7 + [0.0] * 7 + [2.0] * 20, 1.0, 0.0)
        dense = [float((index // 6) % 2) for index in range(240)]
        self._parity(dense, 0.5, 0.0)
        sparse = [0.0] * 250 + [2.0] * 250 + [0.0] * 250
        self._parity(sparse, 1.0, 0.0)

    def test_complete_sequence_is_read_and_validated_once(self) -> None:
        for size in (400, 800):
            sequence = CountingSequence(size)
            metrics: dict[str, int] = {}
            extract_sustained_step_events_linear_v1(
                sequence,
                source_step_threshold=1.0,
                source_stability_tolerance=0.0,
                metrics=metrics,
            )
            self.assertEqual(sequence.element_reads, size)
            self.assertEqual(metrics["complete_sequence_validation_count"], 1)
            self.assertEqual(metrics["validated_element_count"], size)
            self.assertEqual(metrics["event_index_evaluation_count"], size - 9)

    def test_no_full_sequence_materialization_inside_event_loop(self) -> None:
        tree = ast.parse(inspect.getsource(extract_sustained_step_events_linear_v1))
        loop = next(node for node in ast.walk(tree) if isinstance(node, ast.For))
        forbidden = []
        for node in ast.walk(loop):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                if node.func.id in {"tuple", "list", "_normalize_sequence_once_v1"}:
                    forbidden.append(node.func.id)
        self.assertEqual(forbidden, [])


if __name__ == "__main__":
    unittest.main()
