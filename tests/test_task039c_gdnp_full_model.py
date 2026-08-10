from __future__ import annotations

import unittest

from paperworks.gdn.pyg_port_compatibility_v1 import (
    run_gnn_layer_parity_v1,
    run_tiny_full_gdn_gate_v1,
)


class Task039CGDNPFullModelTests(unittest.TestCase):
    def test_gnn_layer_eval_and_train_modes_match(self) -> None:
        result = run_gnn_layer_parity_v1()
        self.assertEqual(result["status"], "passed_gdnp_gnn_layer_parity")
        self.assertEqual([item["mode"] for item in result["modes"]], ["evaluation", "training"])

    def test_tiny_complete_gdn_forward_backward_and_step(self) -> None:
        result = run_tiny_full_gdn_gate_v1()
        self.assertEqual(result["status"], "passed_gdnp_tiny_full_gdn_gate")
        self.assertEqual(result["forward_output_shape"], [2, 6])
        self.assertEqual(result["learned_graph_shape"], [6, 5])
        self.assertTrue(result["same_seed_initial_output_equal"])


if __name__ == "__main__":
    unittest.main()
