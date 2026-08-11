from __future__ import annotations

import inspect
import unittest

from paperworks.profiling.task039d1_execution_optimization_v1 import (
    audit_isolation_semantic_parity_v1,
    classify_all_source_isolation_indexed_v1,
)
from paperworks.v6.continuous_step_protocol_v1 import SustainedStepEventV1
from paperworks.v6.relation_profiling_protocol_v1 import (
    FROZEN_SOURCES,
    classify_all_source_isolation_v1,
)


def event(index: int, direction: str = "step_up") -> SustainedStepEventV1:
    amplitude = 1.0 if direction == "step_up" else -1.0
    return SustainedStepEventV1(index, direction, 0.0, amplitude, amplitude, 1.0, 1.0)


class TASK039D1RIsolationOptimizationTests(unittest.TestCase):
    def _fixture(self) -> dict[str, tuple[SustainedStepEventV1, ...]]:
        return {source: () for source in FROZEN_SOURCES}

    def _parity(self, fixture: dict[str, tuple[SustainedStepEventV1, ...]]) -> None:
        self.assertEqual(
            classify_all_source_isolation_indexed_v1(fixture),
            classify_all_source_isolation_v1(fixture),
        )

    def test_preflight_parity_suite(self) -> None:
        audit_isolation_semantic_parity_v1()

    def test_inclusive_radius_and_same_source_exclusion(self) -> None:
        for offset, expected in ((-3, True), (-2, False), (0, False), (2, False), (3, True)):
            fixture = self._fixture()
            fixture[FROZEN_SOURCES[0]] = (event(50),)
            fixture[FROZEN_SOURCES[1]] = (event(50 + offset, "step_down"),)
            result = classify_all_source_isolation_indexed_v1(fixture)
            self.assertEqual(result[FROZEN_SOURCES[0]][0][1], expected)
            self._parity(fixture)
        fixture = self._fixture()
        fixture[FROZEN_SOURCES[0]] = (event(50), event(51))
        result = classify_all_source_isolation_indexed_v1(fixture)
        self.assertTrue(all(isolated for _, isolated in result[FROZEN_SOURCES[0]]))
        self._parity(fixture)

    def test_all_12_dense_and_sparse_context(self) -> None:
        dense = {
            source: tuple(event(index) for index in range(position, 360, 12))
            for position, source in enumerate(FROZEN_SOURCES)
        }
        sparse = {
            source: tuple(event(index) for index in range(position * 100, 9000, 1700))
            for position, source in enumerate(FROZEN_SOURCES)
        }
        self._parity(dense)
        self._parity(sparse)

    def test_uses_indexed_search_not_nested_other_event_scan(self) -> None:
        source = inspect.getsource(classify_all_source_isolation_indexed_v1)
        self.assertIn("bisect.bisect_left", source)
        self.assertNotIn("abs(event.event_index - other.event_index)", source)


if __name__ == "__main__":
    unittest.main()
