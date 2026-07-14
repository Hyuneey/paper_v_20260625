import unittest

import numpy as np

from experiments.argos_reproduction.rule_prediction_diversity import diversity_diagnostics, prediction_jaccard


class Task035BDiversityTests(unittest.TestCase):
    def test_jaccard_and_unique_coverage(self):
        self.assertEqual(prediction_jaccard([0, 0], [0, 0]), 1.0)
        records = [{"rule_sha256": "a", "anchor_id": "x"}, {"rule_sha256": "b", "anchor_id": "y"}]
        report = diversity_diagnostics(records, {"a": np.array([0, 1, 0]), "b": np.array([0, 0, 1])}, [0, 1, 1])
        self.assertEqual(report["unique_true_positive_points_per_rule"], {"a": 1, "b": 1})


if __name__ == "__main__":
    unittest.main()
