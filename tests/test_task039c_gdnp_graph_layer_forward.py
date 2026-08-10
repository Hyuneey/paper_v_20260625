from __future__ import annotations

import ast
import unittest
from pathlib import Path

from paperworks.gdn.pyg_port_compatibility_v1 import (
    run_graph_layer_forward_parity_v1,
    run_index_semantics_gate_v1,
)


ROOT = Path(__file__).resolve().parents[1]


class Task039CGDNPGraphLayerForwardTests(unittest.TestCase):
    def test_independent_reference_has_no_pyg_or_project_layer_import(self) -> None:
        path = ROOT / "src/paperworks/gdn/pure_torch_graph_layer_reference_v1.py"
        tree = ast.parse(path.read_text(encoding="utf-8"))
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                imports.append(node.module or "")
        joined = "\n".join(imports)
        self.assertNotIn("torch_geometric", joined)
        self.assertNotIn("upstream_candidate_backend_v1", joined)

    def test_all_forward_fixtures_match(self) -> None:
        result = run_graph_layer_forward_parity_v1()
        self.assertEqual(result["status"], "passed_gdnp_graph_layer_forward_parity")
        self.assertEqual([item["fixture"] for item in result["fixtures"]], ["fixture_a", "fixture_b", "fixture_c"])

    def test_index_and_self_loop_semantics(self) -> None:
        result = run_index_semantics_gate_v1()
        self.assertEqual(result["node_dim"], 0)
        self.assertTrue(all(result["checks"].values()))


if __name__ == "__main__":
    unittest.main()
