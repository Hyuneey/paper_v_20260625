from __future__ import annotations

import unittest

from paperworks.gdn.pyg_port_compatibility_v1 import run_graph_layer_backward_parity_v1


class Task039CGDNPGraphLayerBackwardTests(unittest.TestCase):
    def test_gradients_and_one_step_optimizer_match(self) -> None:
        result = run_graph_layer_backward_parity_v1()
        self.assertEqual(result["status"], "passed_gdnp_graph_layer_backward_parity")
        self.assertEqual(result["one_step_optimizer"], "Adam(lr=0.001)")
        self.assertTrue(result["gradient_maximum_absolute_errors"])
        self.assertTrue(result["optimizer_parameter_maximum_absolute_errors"])


if __name__ == "__main__":
    unittest.main()
