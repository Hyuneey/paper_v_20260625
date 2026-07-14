from __future__ import annotations

import json
from pathlib import Path
import unittest
from unittest.mock import patch

from experiments.argos_reproduction.multi_provider_capture import approval_blockers

ROOT = Path(__file__).resolve().parents[1]


class Task035aProviderBudgetTests(unittest.TestCase):
    def test_exact_budget_and_no_retry(self):
        config = json.loads((ROOT / "configs/argos_reproduction/task035a_expanded_rule_cohort.json").read_text())
        approval = json.loads((ROOT / "configs/argos_reproduction/task035a_provider_approval.json").read_text())
        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-not-a-real-key"}):
            self.assertEqual(approval_blockers(config, approval, True), [])
        self.assertEqual(approval["maximum_requests_per_slot"], 1)
        self.assertFalse(approval["automatic_retry"]); self.assertFalse(approval["manual_retry_under_same_decision"])

    def test_consumed_task026q_approval_is_not_reused(self):
        config = json.loads((ROOT / "configs/argos_reproduction/task035a_expanded_rule_cohort.json").read_text())
        self.assertNotIn("task026q", config["provider"]["approval_path"].lower())


if __name__ == "__main__": unittest.main()
