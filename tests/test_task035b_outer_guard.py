import inspect
import unittest

from experiments.argos_reproduction import multi_rule_outer_validation as outer


class Task035BOuterGuardTests(unittest.TestCase):
    def test_outer_has_no_selection_algorithm(self):
        source = inspect.getsource(outer)
        self.assertNotIn("select_frozen_arms", source)
        self.assertIn("_load_outer_labels_after_prediction_freeze", source)
        self.assertIn("outer_individual_metrics_computed\": False", source)


if __name__ == "__main__":
    unittest.main()
