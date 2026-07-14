import unittest

import numpy as np

from experiments.argos_reproduction.direct_event_metrics import compose_or, direct_pa_free_metrics, maximum_overlap_matching


class Task035BEventMetricTests(unittest.TestCase):
    def test_point_counts_and_direct_metrics(self):
        result = direct_pa_free_metrics([0, 1, 1, 0], [0, 1, 0, 1])
        self.assertEqual((result["true_positive"], result["false_positive"], result["true_negative"], result["false_negative"]), (1, 1, 1, 1))
        self.assertEqual(result["point_f1"], 0.5)
        self.assertFalse(result["point_adjustment"])

    def test_event_matching_is_one_to_one(self):
        matches = maximum_overlap_matching([(0, 6)], [(0, 2), (4, 6)])
        self.assertEqual(len(matches), 1)

    def test_or_is_elementwise_maximum(self):
        np.testing.assert_array_equal(compose_or([[0, 1, 0], [1, 0, 0]]), [1, 1, 0])


if __name__ == "__main__":
    unittest.main()
