from __future__ import annotations

import unittest

import numpy as np

from paperworks.validation_v2.exp02_bindings_v2a import (
    Exp02BindingError,
    empirical_linear_quantiles_v1,
    extract_candidate_specific_events_v1,
)
from paperworks.profiling.task039d1_execution_optimization_v1 import (
    extract_sustained_step_events_linear_v1,
)


class Exp02BindingsV2ATests(unittest.TestCase):
    def test_quantile_uses_q_times_n_minus_one_linear_interpolation(self) -> None:
        self.assertEqual((2.5, 3.25, 3.7), empirical_linear_quantiles_v1((1.0, 2.0, 3.0, 4.0)))

    def test_quantile_rejects_empty_nonpositive_and_nonfinite(self) -> None:
        for values in ((), (0.0,), (1.0, float("nan"))):
            with self.subTest(values=values), self.assertRaises(Exp02BindingError):
                empirical_linear_quantiles_v1(values)

    def test_vectorized_event_scan_matches_frozen_reference(self) -> None:
        fixtures = (
            np.array([0.0] * 12 + [2.0] * 20 + [0.0] * 20, dtype=np.float64),
            np.array([1.0] * 11 + [-1.0] * 17 + [3.0] * 20, dtype=np.float64),
            np.array(([0.0] * 7 + [1.0] * 7) * 12, dtype=np.float64),
        )
        for values in fixtures:
            for threshold, tolerance in ((0.5, 0.0), (1.0, 0.1), (2.0, 0.5)):
                with self.subTest(threshold=threshold, tolerance=tolerance):
                    expected = extract_sustained_step_events_linear_v1(
                        values, source_step_threshold=threshold,
                        source_stability_tolerance=tolerance,
                    )
                    observed = extract_candidate_specific_events_v1(
                        values, threshold=threshold, tolerance=tolerance,
                    )
                    self.assertEqual(expected, observed)

    def test_event_scan_rejects_invalid_parameters(self) -> None:
        with self.assertRaises(Exp02BindingError):
            extract_candidate_specific_events_v1(np.zeros(20), threshold=0.0, tolerance=0.0)


if __name__ == "__main__":
    unittest.main()
