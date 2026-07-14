from __future__ import annotations

import json
from pathlib import Path
import unittest
import numpy as np

from experiments.argos_reproduction.multi_prompt_capture import build_request

ROOT = Path(__file__).resolve().parents[1]


class Task035aRequestManifestTests(unittest.TestCase):
    def test_identical_replicates_have_identical_request_hash(self):
        values = np.arange(10, dtype=float); labels = np.array([0, 1] * 5); indices = np.arange(10)
        first, first_hash = build_request(values, labels, indices, 1000)
        second, second_hash = build_request(values, labels, indices, 1000)
        self.assertEqual(first, second); self.assertEqual(first_hash, second_hash)
        self.assertNotIn("previous_rule", json.dumps(first).lower())

    def test_config_registers_exactly_100_slots(self):
        config = json.loads((ROOT / "configs/argos_reproduction/task035a_expanded_rule_cohort.json").read_text())
        self.assertEqual(config["design"]["kpi_count"] * config["design"]["anchors_per_kpi"] * config["design"]["replicates_per_anchor"], 100)


if __name__ == "__main__": unittest.main()
