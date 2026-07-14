import unittest

from experiments.argos_reproduction.paired_kpi_bootstrap import paired_percentile_bootstrap


class Task035BBootstrapTests(unittest.TestCase):
    def test_frozen_seed_is_deterministic(self):
        first = paired_percentile_bootstrap([1, 2, 3], [0, 2, 4], resamples=100)
        second = paired_percentile_bootstrap([1, 2, 3], [0, 2, 4], resamples=100)
        self.assertEqual(first, second)
        self.assertEqual(first["kpi_win_count"], 1)
        self.assertEqual(first["kpi_tie_count"], 1)
        self.assertEqual(first["kpi_loss_count"], 1)


if __name__ == "__main__":
    unittest.main()
