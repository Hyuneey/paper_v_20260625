from __future__ import annotations

import json
from pathlib import Path
import unittest

from experiments.argos_reproduction.remediation_cohort_merge import _yield

ROOT = Path(__file__).resolve().parents[1]


class Task035arCombinedCohortTests(unittest.TestCase):
    def test_generation_yields_are_not_performance_metrics(self):
        result = _yield(90, 80, 75)
        self.assertEqual(result["response_yield"], 0.9)
        self.assertEqual(result["extraction_yield"], 0.8)
        self.assertEqual(result["executable_yield"], 0.75)

    def test_runtime_policy_matches_task035a(self):
        old = json.loads((ROOT / "configs/argos_reproduction/task035a_expanded_rule_cohort.json").read_text())
        new = json.loads((ROOT / "configs/argos_reproduction/task035ar_output_budget_remediation.json").read_text())
        self.assertEqual(new["runtime"], old["runtime"])
        self.assertEqual(new["image"], old["image"])
        self.assertEqual(new["isolation"], old["isolation"])


if __name__ == "__main__": unittest.main()
