import random
import unittest

from experiments.argos_reproduction.balanced_rule_panel import select_balanced_panel


class Task035BBalancedPanelTests(unittest.TestCase):
    def setUp(self):
        self.rules = [{"rule_sha256": f"{index:064x}", "anchor_id": f"A{index % 5}"} for index in range(15)]
        self.anchors = ["A0", "A1", "A2", "A3", "A4"]

    def test_exact_ten_and_anchor_round_robin(self):
        selected = select_balanced_panel(self.rules, self.anchors)
        self.assertEqual(len(selected), 10)
        self.assertEqual([item["anchor_id"] for item in selected[:5]], self.anchors)

    def test_order_invariant(self):
        expected = select_balanced_panel(self.rules, self.anchors)
        shuffled = list(self.rules)
        random.Random(7).shuffle(shuffled)
        self.assertEqual(expected, select_balanced_panel(shuffled, self.anchors))


if __name__ == "__main__":
    unittest.main()
