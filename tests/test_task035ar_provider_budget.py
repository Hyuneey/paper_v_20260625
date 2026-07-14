from __future__ import annotations

import json
from pathlib import Path
import unittest
from unittest.mock import patch

from experiments.argos_reproduction.remediation_provider_capture import approval_blockers

ROOT = Path(__file__).resolve().parents[1]


class Task035arProviderBudgetTests(unittest.TestCase):
    def test_exact_budget_and_no_retry(self):
        config = json.loads((ROOT / "configs/argos_reproduction/task035ar_output_budget_remediation.json").read_text())
        approval = json.loads((ROOT / "configs/argos_reproduction/task035ar_provider_approval.json").read_text())
        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-not-a-real-key"}):
            self.assertEqual(approval_blockers(config, approval, True), [])
        self.assertEqual(approval["maximum_requests"], 100)
        self.assertEqual(approval["maximum_output_tokens_per_call"], 6000)
        self.assertFalse(approval["automatic_retry"]); self.assertFalse(approval["manual_retry"])
        self.assertFalse(approval["temperature_parameter_sent"]); self.assertFalse(approval["provider_seed_sent"])
        self.assertFalse(approval["reasoning_parameter_added"])

    def test_separate_approval_and_private_root(self):
        config = json.loads((ROOT / "configs/argos_reproduction/task035ar_output_budget_remediation.json").read_text())
        self.assertNotEqual(config["provider"]["approval_path"], "configs/argos_reproduction/task035a_provider_approval.json")
        self.assertNotEqual(config["private_root"], config["task035a"]["private_root"])


if __name__ == "__main__": unittest.main()
