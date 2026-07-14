from __future__ import annotations

import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class Task035arReportTests(unittest.TestCase):
    def test_tracked_reports_are_aggregate_only_when_present(self):
        forbidden = ("source_values", "target_values", '"raw_text"', '"messages"', '"rule_source"', '"complete_request"')
        for path in (ROOT / "docs/task_reports").glob("TASK-035AR*.json"):
            text = path.read_text(encoding="utf-8"); payload = json.loads(text)
            for token in forbidden: self.assertNotIn(token, text)
            self.assertFalse(payload.get("performance_metrics_computed", False))

    def test_original_task035a_status_is_immutable(self):
        report = json.loads((ROOT / "docs/task_reports/TASK-035A_COHORT_ADEQUACY_REPORT.json").read_text())
        self.assertEqual(report["status"], "insufficient_rule_yield")


if __name__ == "__main__": unittest.main()
