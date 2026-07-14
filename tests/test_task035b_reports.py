import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class Task035BReportTests(unittest.TestCase):
    def test_config_has_frozen_boundaries(self):
        config = json.loads((ROOT / "configs/argos_reproduction/task035b_multi_rule_validation.json").read_text(encoding="utf-8"))
        self.assertEqual(config["design"]["executable_rule_count"], 146)
        self.assertEqual(config["design"]["total_primary_rules"], 100)
        self.assertFalse(config["boundaries"]["test_value_access"])
        self.assertFalse(config["boundaries"]["provider_calls"])

    def test_tracked_task035b_reports_contain_no_raw_arrays_or_private_paths(self):
        for path in (ROOT / "docs/task_reports").glob("TASK-035B_*.json"):
            text = path.read_text(encoding="utf-8").lower()
            self.assertNotIn("source_values", text)
            self.assertNotIn("target_values", text)
            self.assertNotIn("artifacts/private", text)


if __name__ == "__main__":
    unittest.main()
