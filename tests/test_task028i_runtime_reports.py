import json
import unittest
from pathlib import Path

from experiments.argos_reproduction.prompt_capture import sha256_json


REPO_ROOT = Path(__file__).resolve().parents[1]


class Task028IRuntimeReportTests(unittest.TestCase):
    def _read(self, relative_path: str) -> dict:
        return json.loads((REPO_ROOT / relative_path).read_text(encoding="utf-8"))

    def _assert_report_hash(self, report: dict) -> None:
        expected = report.pop("report_hash")
        self.assertEqual(sha256_json(report), expected)

    def test_host_preflight_preceded_installation(self):
        report = self._read("docs/task_reports/TASK-028I_HOST_PREFLIGHT.json")
        self.assertTrue(report["preflight_completed_before_installation"])
        self.assertFalse(report["system_changes_performed_before_report"])
        self.assertEqual(report["wsl"]["default_version"], 2)
        self.assertFalse(report["restart"]["restart_pending"])
        self._assert_report_hash(report)

    def test_exactly_one_runtime_was_selected(self):
        config = self._read("configs/argos_reproduction/task028i_runtime_setup.json")
        report = self._read("docs/task_reports/TASK-028I_RUNTIME_INSTALL_REPORT.json")
        self.assertEqual(config["selected_runtime"], "Docker Desktop")
        self.assertEqual(report["runtime_selection"]["selected_runtime"], "Docker Desktop")
        self.assertFalse(report["runtime_selection"]["fallback_runtime_selected"])
        self.assertEqual(report["runtime_selection"]["runtimes_install_attempted"], 1)

    def test_official_installer_hash_and_signature_are_recorded(self):
        report = self._read("docs/task_reports/TASK-028I_RUNTIME_INSTALL_REPORT.json")
        installer = report["installer"]
        self.assertEqual(installer["source_domain"], "desktop.docker.com")
        self.assertEqual(installer["authenticode_status"], "Valid")
        self.assertEqual(installer["signer_subject"], "Docker Inc.")
        self.assertEqual(len(installer["sha256"]), 64)
        self.assertFalse(installer["tracked_installer"])
        self._assert_report_hash(report)

    def test_failed_install_does_not_claim_runtime_readiness(self):
        report = self._read("docs/task_reports/TASK-028I_RUNTIME_INSTALL_REPORT.json")
        self.assertEqual(report["task_status"], "blocked_environment")
        self.assertFalse(report["runtime_installed"])
        self.assertFalse(report["runtime_daemon_healthy"])
        self.assertFalse(report["task028_resume_allowed"])
        self.assertFalse(report["captured_rule_execution_allowed"])

    def test_security_controls_remain_unverified(self):
        report = self._read("docs/task_reports/TASK-028I_SECURITY_CONTROL_REPORT.json")
        self.assertFalse(report["harmless_container_test"]["attempted"])
        self.assertFalse(report["required_security_controls_supported"])
        self.assertTrue(all(not item["supported"] for item in report["controls"]))
        self.assertTrue(
            all(
                item["verification_status"] == "not_verified_no_healthy_runtime"
                for item in report["controls"]
            )
        )
        self._assert_report_hash(report)

    def test_reports_exclude_private_paths_credentials_and_research_access(self):
        paths = [
            "configs/argos_reproduction/task028i_runtime_setup.json",
            "docs/task_reports/TASK-028I_HOST_PREFLIGHT.json",
            "docs/task_reports/TASK-028I_RUNTIME_INSTALL_REPORT.json",
            "docs/task_reports/TASK-028I_SECURITY_CONTROL_REPORT.json",
        ]
        text = "\n".join((REPO_ROOT / path).read_text(encoding="utf-8") for path in paths)
        self.assertNotIn("C:\\Users\\", text)
        self.assertNotIn("OPENAI_API_KEY", text)
        self.assertNotIn("artifacts/private", text)

        install = self._read("docs/task_reports/TASK-028I_RUNTIME_INSTALL_REPORT.json")
        self.assertFalse(install["captured_rule_accessed"])
        self.assertFalse(install["captured_rule_executed"])
        self.assertFalse(install["task028_synthetic_inputs_prepared"])
        self.assertFalse(install["execution_approval_activated"])
        self.assertFalse(install["provider_call_performed"])


if __name__ == "__main__":
    unittest.main()
