import unittest

from experiments.argos_reproduction.multi_rule_outer_validation import validate_selection_freeze


class Task035BSelectionFreezeTests(unittest.TestCase):
    def test_valid_freeze(self):
        validate_selection_freeze({"selection_split": "inner_selection", "outer_metrics_seen": False, "test_metrics_seen": False, "per_kpi": [{"kpi_id": str(i)} for i in range(10)]})

    def test_outer_seen_fails(self):
        with self.assertRaises(ValueError):
            validate_selection_freeze({"selection_split": "inner_selection", "outer_metrics_seen": True, "test_metrics_seen": False, "per_kpi": [{}] * 10})


if __name__ == "__main__":
    unittest.main()
