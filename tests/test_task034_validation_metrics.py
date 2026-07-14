from __future__ import annotations

import unittest

import numpy as np

from experiments.argos_reproduction.kpi_validation_metrics import (
    KpiValidationMetricError,
    direct_binary_validation_diagnostics,
)


class Task034ValidationMetricTests(unittest.TestCase):
    def test_direct_binary_metrics_are_pa_free_and_threshold_free(self) -> None:
        result = direct_binary_validation_diagnostics(
            np.asarray([0, 1, 1, 0]), np.asarray([0, 1, 0, 1])
        )
        self.assertEqual(
            result["confusion_counts"],
            {"true_positive": 1, "false_positive": 1, "true_negative": 1, "false_negative": 1},
        )
        self.assertEqual(result["precision"], 0.5)
        self.assertEqual(result["recall"], 0.5)
        self.assertEqual(result["point_f1"], 0.5)
        self.assertEqual(result["point_adjustment"], "disabled")
        self.assertEqual(result["threshold_optimization"], "none")

    def test_zero_division_is_zero(self) -> None:
        result = direct_binary_validation_diagnostics(np.zeros(4), np.zeros(4))
        self.assertEqual(result["precision"], 0.0)
        self.assertEqual(result["recall"], 0.0)
        self.assertEqual(result["point_f1"], 0.0)

    def test_invalid_binary_domain_fails(self) -> None:
        with self.assertRaises(KpiValidationMetricError):
            direct_binary_validation_diagnostics(np.asarray([0, 2]), np.asarray([0, 1]))


if __name__ == "__main__":
    unittest.main()
