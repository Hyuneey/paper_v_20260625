from __future__ import annotations

import ast
import json
from pathlib import Path
import unittest

from experiments.argos_reproduction.multi_rule_runtime import isolation_arguments

ROOT = Path(__file__).resolve().parents[1]


class Task035aRuntimeGateTests(unittest.TestCase):
    def test_isolation_and_values_only_mount_contract(self):
        config = json.loads((ROOT / "configs/argos_reproduction/task035a_expanded_rule_cohort.json").read_text())
        args = " ".join(isolation_arguments(config))
        for value in ("--network none", "--read-only", "--cap-drop ALL", "--security-opt no-new-privileges", "--memory 256m", "--pids-limit 64", "--cpus 1"):
            self.assertIn(value, args)
        source = (ROOT / "experiments/argos_reproduction/multi_rule_runtime.py").read_text()
        self.assertIn("/input/input_values.npy", source); self.assertNotIn("/input/input_labels.npy", source)

    def test_host_runtime_has_no_dynamic_source_loading(self):
        source = (ROOT / "experiments/argos_reproduction/multi_rule_runtime.py").read_text()
        imports = {alias.name for node in ast.walk(ast.parse(source)) if isinstance(node, (ast.Import, ast.ImportFrom)) for alias in node.names}
        self.assertNotIn("importlib", imports); self.assertNotIn("runpy", imports)
        for token in ("eval(", "exec(", "compile("): self.assertNotIn(token, source)


if __name__ == "__main__": unittest.main()
