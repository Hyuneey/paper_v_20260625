from __future__ import annotations

import unittest

import numpy as np

from experiments.argos_reproduction.argos_source_faithful_metrics import (
    SOURCE_BLOBS,
    SOURCE_COMMIT,
    argos_label_aware_validation_diagnostics,
    smooth_labels,
    verify_frozen_synthetic_fidelity,
)


class Task034MetricFidelityTests(unittest.TestCase):
    def test_smoothing_matches_frozen_loop_expectation(self) -> None:
        actual = smooth_labels(np.asarray([0, 0, 1, 0, 0]), window_size=3)
        expected = np.asarray([1 / 3, 2 / 3, 1.0, 2 / 3, 1 / 3])
        np.testing.assert_allclose(actual, expected)

    def test_single_event_expected_metrics_and_threshold(self) -> None:
        result = argos_label_aware_validation_diagnostics(
            np.asarray([0, 0, 1, 0, 0]), np.asarray([0, 0, 1, 0, 0])
        )
        self.assertAlmostEqual(result["point_f1"]["f1"], 1.0)
        self.assertEqual(result["point_f1"]["threshold"], -1.0)
        self.assertAlmostEqual(result["point_f1_pa"]["f1"], 1.0)
        self.assertAlmostEqual(result["event_f1_pa"]["f1"], 1.0)
        self.assertAlmostEqual(result["event_f1_pa"]["threshold"], 1.0)

    def test_tie_policy_is_source_faithful_and_recorded(self) -> None:
        result = argos_label_aware_validation_diagnostics(
            np.asarray([0, 1, 0, 1]), np.asarray([0, 1, 0, 1])
        )
        self.assertIn("strict f1 improvement", result["tie_breaking_policy"])
        self.assertEqual(result["source_commit"], SOURCE_COMMIT)
        self.assertEqual(result["source_blobs"], SOURCE_BLOBS)

    def test_frozen_fidelity_gate_passes(self) -> None:
        self.assertEqual(verify_frozen_synthetic_fidelity()["status"], "passed")


if __name__ == "__main__":
    unittest.main()
