from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

from paperworks.v6.common import stable_hash_v1


ROOT = Path(__file__).resolve().parents[1]
REPORT_ROOT = ROOT / "docs/task_reports"
JSON_REPORTS = (
    "TASK-039BR0_SOURCE_EXCLUSION_SUMMARY.json",
    "TASK-039BR0_CONTINUOUS_SOURCE_READINESS.json",
    "TASK-039BR0_HAIEND_ROUTE_READINESS.json",
    "TASK-039BR0_RULE_V1_COMPATIBILITY.json",
    "TASK-039BR0_RELATION_FAMILY_DECISION.json",
    "TASK-039BR0_DATA_ACCESS_AUDIT.json",
)


class TASK039BR0ReportTests(unittest.TestCase):
    def _load(self, name: str) -> dict[str, object]:
        return json.loads((REPORT_ROOT / name).read_text(encoding="utf-8"))

    def test_all_json_reports_have_valid_self_hashes(self) -> None:
        for name in JSON_REPORTS:
            with self.subTest(name=name):
                payload = self._load(name)
                observed = payload.pop("artifact_hash")
                self.assertEqual(observed, stable_hash_v1(payload))

    def test_frozen_task039b_result_is_unchanged(self) -> None:
        report = self._load("TASK-039BR0_SOURCE_EXCLUSION_SUMMARY.json")
        metrics = {item["process_id"]: item for item in report["frozen_metrics"]}
        self.assertEqual(metrics["P1"]["total_variables"], 37)
        self.assertEqual(metrics["P3"]["total_variables"], 7)
        self.assertEqual(metrics["P1"]["eligible_discrete_control_sources"], 0)
        self.assertEqual(metrics["P3"]["eligible_discrete_control_sources"], 0)
        self.assertEqual(metrics["P1"]["screened_pairs"], 0)
        self.assertEqual(metrics["P3"]["screened_pairs"], 0)
        self.assertTrue(report["no_process_selected"])

    def test_route_and_claim_boundary(self) -> None:
        report = self._load("TASK-039BR0_RELATION_FAMILY_DECISION.json")
        self.assertEqual(
            report["recommended_route"],
            "versioned_continuous_step_delayed_response_on_HAI",
        )
        self.assertEqual(report["next_task"], "TASK-039BR1")
        self.assertFalse(report["process_selected"])
        self.assertFalse(report["task039c_authorized"])
        self.assertFalse(report["task039b_gate_lowered"])
        self.assertFalse(report["weighted_score_used"])

    def test_continuous_readiness_does_not_select_process_or_pairs(self) -> None:
        report = self._load("TASK-039BR0_CONTINUOUS_SOURCE_READINESS.json")
        self.assertEqual(report["ready_process_ids"], ["P1", "P3"])
        self.assertFalse(report["source_target_pairs_evaluated"])
        self.assertFalse(report["process_selected"])

    def test_haiend_payload_boundary(self) -> None:
        report = self._load("TASK-039BR0_HAIEND_ROUTE_READINESS.json")
        self.assertEqual(report["file_count"], 10)
        self.assertFalse(report["payload_downloaded_or_opened"])
        self.assertFalse(report["binary_or_discrete_claim_made"])
        self.assertFalse(report["row_synchronization_claim_made"])

    def test_rule_v1_remains_unchanged(self) -> None:
        report = self._load("TASK-039BR0_RULE_V1_COMPATIBILITY.json")
        self.assertEqual(
            report["continuous_source_route_classification"],
            "requires_versioned_rule_semantics",
        )
        self.assertFalse(report["rule_v1_modified"])

    def test_data_access_boundary(self) -> None:
        report = self._load("TASK-039BR0_DATA_ACCESS_AUDIT.json")
        for key in (
            "test_file_access_count",
            "label_file_access_count",
            "attack_summary_access_count",
            "private_custody_access_count",
            "prohibited_data_access_count",
        ):
            self.assertEqual(report[key], 0)
        self.assertFalse(report["normal_guard_feature_values_accessed"])
        self.assertFalse(report["p2_p4_feature_values_accessed"])

    def test_public_reports_contain_no_sensitive_payload(self) -> None:
        paths = tuple(REPORT_ROOT / name for name in JSON_REPORTS) + (
            REPORT_ROOT / "TASK-039BR0_REPORT.md",
        )
        for path in paths:
            text = path.read_text(encoding="utf-8")
            lowered = text.lower()
            with self.subTest(path=path.name):
                self.assertNotRegex(text, r"[A-Za-z]:\\")
                self.assertNotIn("attack_start", lowered)
                self.assertNotIn("attack_end", lowered)
                self.assertNotIn("attack_target", lowered)
                self.assertNotIn("target_controller", lowered)
                self.assertNotIn("raw_window", lowered)
                self.assertNotIn("raw_sequence", lowered)
                self.assertIsNone(re.search(r"20\d\d-\d\d-\d\d[ T]\d\d:\d\d:\d\d", text))

    def test_required_final_boundary_wording(self) -> None:
        report = (REPORT_ROOT / "TASK-039BR0_REPORT.md").read_text(encoding="utf-8")
        self.assertIn(
            "TASK-039BR0 explains why the original binary/discrete delayed-response MVP",
            report,
        )
        self.assertIn("TASK-039C remains unauthorized", report)


if __name__ == "__main__":
    unittest.main()
