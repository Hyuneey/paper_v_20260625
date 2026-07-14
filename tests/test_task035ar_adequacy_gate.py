from __future__ import annotations

import json
from pathlib import Path
import unittest

from experiments.argos_reproduction.remediation_cohort_merge import evaluate_adequacy

ROOT = Path(__file__).resolve().parents[1]


class Task035arAdequacyGateTests(unittest.TestCase):
    def setUp(self):
        self.thresholds = json.loads((ROOT / "configs/argos_reproduction/task035ar_output_budget_remediation.json").read_text())["adequacy"]
        self.summary = {
            "remediation_requests_sent": 100, "remediation_retries": 0,
            "total_registered_slots": 200, "terminal_slot_count": 200,
            "selected_kpi_count": 10, "anchor_count": 50,
            "remediation_non_empty_responses": 90, "remediation_executable_rules": 75,
            "cumulative_executable_rules": 130, "minimum_cumulative_executable_per_kpi": 8,
            "minimum_cumulative_distinct_per_kpi": 6, "kpis_with_at_least_10_executable": 8,
            "anchors_with_at_least_2_executable": 35,
        }

    def test_exact_thresholds_pass(self):
        self.assertEqual(evaluate_adequacy(self.summary, self.thresholds), "passed_balanced_generation_cohort")

    def test_each_gate_fails_closed(self):
        cases = {
            "remediation_non_empty_responses": "insufficient_remediation_response_yield",
            "remediation_executable_rules": "insufficient_remediation_rule_yield",
            "cumulative_executable_rules": "insufficient_combined_rule_yield",
            "minimum_cumulative_executable_per_kpi": "insufficient_kpi_balance",
            "minimum_cumulative_distinct_per_kpi": "insufficient_kpi_balance",
            "kpis_with_at_least_10_executable": "insufficient_kpi_balance",
            "anchors_with_at_least_2_executable": "insufficient_anchor_coverage",
        }
        for field, expected in cases.items():
            with self.subTest(field=field):
                summary = dict(self.summary)
                threshold_key = {
                    "remediation_non_empty_responses": "minimum_remediation_non_empty_responses",
                    "remediation_executable_rules": "minimum_remediation_executable_rules",
                    "cumulative_executable_rules": "minimum_cumulative_executable_rules",
                    "minimum_cumulative_executable_per_kpi": "minimum_cumulative_executable_rules_per_kpi",
                    "minimum_cumulative_distinct_per_kpi": "minimum_cumulative_distinct_rules_per_kpi",
                    "kpis_with_at_least_10_executable": "minimum_kpis_with_at_least_10_executable_rules",
                    "anchors_with_at_least_2_executable": "minimum_anchors_with_at_least_2_executable_rules",
                }[field]
                summary[field] = self.thresholds[threshold_key] - 1
                self.assertEqual(evaluate_adequacy(summary, self.thresholds), expected)


if __name__ == "__main__": unittest.main()
