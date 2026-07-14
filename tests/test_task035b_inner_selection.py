import unittest

import numpy as np

from experiments.argos_reproduction.multi_rule_inner_selection import select_frozen_arms


class Task035BInnerSelectionTests(unittest.TestCase):
    def test_four_frozen_arms(self):
        truth = np.array([0, 1, 1, 0, 1, 0], dtype=np.int8)
        records = [{"rule_sha256": f"r{i}"} for i in range(10)]
        predictions = {f"r{i}": np.array([0, int(i % 2 == 0), int(i < 3), 0, int(i in {4, 5}), 0], dtype=np.int8) for i in range(10)}
        arms = select_frozen_arms(records, predictions, truth)
        self.assertEqual(set(arms), {"best_1", "top_3_or", "coverage_3_or", "all_10_or"})
        self.assertEqual(len(arms["top_3_or"]["rule_hashes"]), 3)
        self.assertEqual(len(set(arms["coverage_3_or"]["rule_hashes"])), 3)
        self.assertEqual(len(arms["all_10_or"]["rule_hashes"]), 10)


if __name__ == "__main__":
    unittest.main()
