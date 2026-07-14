from __future__ import annotations

import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class Task035aReportTests(unittest.TestCase):
    def test_tracked_reports_are_aggregate_only_when_present(self):
        for path in (ROOT / "docs/task_reports").glob("TASK-035A*.json"):
            text = path.read_text(encoding="utf-8"); payload = json.loads(text)
            self.assertNotIn("source_values", text); self.assertNotIn("target_values", text)
            self.assertNotIn('"raw_text"', text); self.assertNotIn('"messages"', text)
            self.assertNotIn('"rule_source"', text); self.assertNotIn('"complete_request"', text)
            self.assertFalse(payload.get("performance_metrics_computed", False))


if __name__ == "__main__": unittest.main()
