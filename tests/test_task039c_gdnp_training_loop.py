from __future__ import annotations

import unittest

from paperworks.gdn.pyg_port_compatibility_v1 import run_tiny_training_loop_gate_v1


class Task039CGDNPTinyTrainingLoopTests(unittest.TestCase):
    def test_real_scientific_path_completes_synthetic_training(self) -> None:
        result = run_tiny_training_loop_gate_v1()
        self.assertEqual(result["status"], "passed_gdnp_tiny_training_loop_gate")
        self.assertGreaterEqual(result["training_batch_count"], 2)
        self.assertEqual(result["validation_batch_count"], 1)
        self.assertEqual(result["synthetic_candidate_count"], 144)
        self.assertTrue(result["best_state_captured_and_reloaded"])


if __name__ == "__main__":
    unittest.main()
