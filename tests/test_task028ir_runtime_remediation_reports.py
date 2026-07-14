import json
import unittest
from pathlib import Path

from experiments.argos_reproduction.prompt_capture import sha256_json


REPO_ROOT = Path(__file__).resolve().parents[1]


class Task028IRRuntimeRemediationReportTests(unittest.TestCase):
    def _read(self, relative_path: str) -> dict:
        return json.loads((REPO_ROOT / relative_path).read_text(encoding="utf-8"))

    def _assert_report_hash(self, report: dict) -> None:
        expected = report.pop("report_hash")
        self.assertEqual(sha256_json(report), expected)

    def test_precleanup_inventory_preceded_host_changes(self):
        report = self._read(
            "docs/task_reports/TASK-028IR_PRECLEANUP_INVENTORY.json"
        )
        self.assertTrue(report["inventory_completed_before_cleanup"])
        self.assertFalse(report["host_changes_performed_before_report"])
        self.assertFalse(report["prior_user_data_assessment"]["prior_installation_detected"])
        self.assertIn("Ubuntu-22.04", report["wsl"]["unrelated_distributions_to_preserve"])
        self._assert_report_hash(report)

    def test_official_uninstaller_preceded_bounded_cleanup(self):
        report = self._read("docs/task_reports/TASK-028IR_CLEANUP_REPORT.json")
        attempt = report["official_uninstaller_attempt"]
        self.assertEqual(attempt["attempt_count"], 1)
        self.assertEqual(attempt["arguments"], ["uninstall"])
        self.assertFalse(attempt["undocumented_arguments_supplied_by_task"])
        self.assertTrue(report["deletion_manifest_written_before_deletion"])
        self.assertTrue(report["cleanup_executed"])
        self.assertTrue(
            report["post_cleanup_verification"][
                "all_manifested_residual_paths_absent"
            ]
        )
        self._assert_report_hash(report)

    def test_exactly_one_interactive_retry_is_consumed(self):
        config = self._read("configs/argos_reproduction/task028ir_cleanup_retry.json")
        report = self._read("docs/task_reports/TASK-028IR_RETRY_REPORT.json")
        retry = report["retry"]
        self.assertEqual(config["decision"]["docker_retry_count_allowed"], 1)
        self.assertEqual(retry["docker_retry_count"], 1)
        self.assertFalse(retry["additional_docker_retry_allowed"])
        self.assertEqual(retry["arguments"], ["install", "--user"])
        self.assertFalse(retry["automatic_license_acceptance"])
        self.assertFalse(retry["quiet_installation"])
        self.assertTrue(retry["user_facing_prompt_observed"])
        self.assertTrue(retry["retry_cancelled_by_researcher_decision"])
        self.assertFalse(retry["installer_process_running"])
        self.assertEqual(report["task_status"], "deferred_by_researcher")
        self.assertEqual(
            report["deferred_until"], "full_experiment_execution_phase"
        )
        self.assertTrue(report["installer_retry_consumed"])
        self._assert_report_hash(report)

    def test_security_claims_remain_unverified(self):
        report = self._read(
            "docs/task_reports/TASK-028IR_SECURITY_CONTROL_REPORT.json"
        )
        self.assertFalse(report["runtime_daemon_healthy"])
        self.assertFalse(report["harmless_container_test"]["attempted"])
        self.assertFalse(report["required_security_controls_supported"])
        self.assertEqual(report["task_status"], "deferred_by_researcher")
        self.assertTrue(all(not item["supported"] for item in report["controls"]))
        self._assert_report_hash(report)

    def test_reports_preserve_research_boundaries(self):
        paths = [
            "configs/argos_reproduction/task028ir_cleanup_retry.json",
            "docs/task_reports/TASK-028IR_PRECLEANUP_INVENTORY.json",
            "docs/task_reports/TASK-028IR_CLEANUP_REPORT.json",
            "docs/task_reports/TASK-028IR_RETRY_REPORT.json",
            "docs/task_reports/TASK-028IR_SECURITY_CONTROL_REPORT.json",
        ]
        text = "\n".join(
            (REPO_ROOT / path).read_text(encoding="utf-8") for path in paths
        )
        self.assertNotIn("C:\\Users\\", text)
        self.assertNotIn("OPENAI_API_KEY", text)
        self.assertNotIn("artifacts/private", text)

        retry = self._read("docs/task_reports/TASK-028IR_RETRY_REPORT.json")
        self.assertFalse(retry["captured_rule_accessed"])
        self.assertFalse(retry["captured_rule_executed"])
        self.assertFalse(retry["execution_approval_activated"])
        self.assertFalse(retry["provider_call_performed"])
        self.assertFalse(retry["task028_resume_allowed"])


if __name__ == "__main__":
    unittest.main()
