from __future__ import annotations

import ast
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class Task034ContainerRuntimeTests(unittest.TestCase):
    def test_config_freezes_validation_only_isolation(self) -> None:
        config = json.loads(
            (ROOT / "configs/argos_reproduction/task034_e2_kpi_validation.json").read_text(encoding="utf-8")
        )
        self.assertEqual(config["isolation"]["network"], "none")
        self.assertEqual(config["isolation"]["memory_limit"], "512m")
        self.assertEqual(config["isolation"]["timeout_seconds"], 120)
        self.assertFalse(config["boundaries"]["test_partition_parsing"])
        self.assertFalse(config["boundaries"]["phase2_ground_truth_package_access"])

    def test_host_wrapper_has_no_generated_source_loader(self) -> None:
        path = ROOT / "experiments/argos_reproduction/kpi_validation_runner.py"
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source)
        imported = {
            alias.name
            for node in ast.walk(tree)
            if isinstance(node, (ast.Import, ast.ImportFrom))
            for alias in node.names
        }
        self.assertNotIn("importlib", imported)
        self.assertNotIn("runpy", imported)
        for prohibited in ("eval(", "exec(", "compile("):
            self.assertNotIn(prohibited, source)

    def test_container_command_mounts_values_not_labels(self) -> None:
        source = (ROOT / "experiments/argos_reproduction/kpi_validation_runner.py").read_text(encoding="utf-8")
        self.assertIn("/input/validation_values.npy", source)
        self.assertNotIn("/input/validation_labels.npy", source)
        self.assertIn("str(image[\"image_id\"])", source)

    def test_dedicated_image_is_non_root_and_metric_free(self) -> None:
        containerfile = (ROOT / "containers/argos_rule_validation/Containerfile").read_text(encoding="utf-8")
        self.assertIn("USER 1000:1000", containerfile)
        self.assertNotIn("scikit", containerfile.lower())
        self.assertNotIn("argos", containerfile.lower().replace("argos_rule_validation", ""))


if __name__ == "__main__":
    unittest.main()
