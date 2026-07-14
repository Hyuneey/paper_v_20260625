import hashlib
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_json(relative: str):
    with (ROOT / relative).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def stable_hash(value):
    encoded = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


class Task033E1ReportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.environment = read_json("docs/task_reports/TASK-033_ENVIRONMENT_REPORT.json")
        cls.report = read_json("docs/task_reports/TASK-033_E1_RUNTIME_REPORT.json")

    def test_environment_records_one_rootless_runtime_and_no_task028_resume(self):
        selection = self.environment["runtime_selection"]
        self.assertTrue(selection["exactly_one_runtime_selected"])
        self.assertEqual(selection["selected"], "wsl_native_rootless_podman")
        self.assertTrue(selection["wsl_native_rootless_podman"]["rootless"])
        self.assertFalse(self.environment["boundaries"]["task028_resumed"])
        self.assertFalse(self.environment["boundaries"]["docker_desktop_retried"])

    def test_isolation_controls_were_verified_before_rule_access(self):
        smoke = self.environment["harmless_isolation_smoke"]
        self.assertEqual(smoke["status"], "passed")
        self.assertTrue(smoke["network_none_verified"])
        self.assertTrue(smoke["read_only_root_verified"])
        self.assertTrue(smoke["cpu_limit_verified"])
        self.assertTrue(smoke["memory_limit_verified"])
        self.assertTrue(smoke["process_limit_verified"])
        self.assertTrue(smoke["timeout_verified"])
        self.assertFalse(smoke["captured_rule_accessed_during_preflight"])

    def test_e1_passed_with_exactly_two_fresh_runs_per_fixture(self):
        self.assertEqual(self.report["e1_status"], "passed_runtime_smoke")
        self.assertEqual(self.report["execution_count"], 8)
        self.assertEqual(len(self.report["fixtures"]), 4)
        for fixture in self.report["fixtures"]:
            self.assertEqual(len(fixture["runs"]), 2)
            self.assertEqual(fixture["replay_status"], "deterministic")
            for run in fixture["runs"]:
                self.assertEqual(run["process"]["exit_code"], 0)
                self.assertFalse(run["process"]["timed_out"])
                self.assertEqual(run["inference"]["output_count"], fixture["input_count"])
                self.assertTrue(run["inference"]["output_shape_valid"])
                self.assertTrue(run["inference"]["output_binary_domain_valid"])
                self.assertTrue(run["inference"]["output_finite"])

    def test_rule_image_and_report_hashes_are_bound(self):
        self.assertEqual(
            self.report["static_rule_verification"]["rule_sha256"],
            "e4855fd898efecf5b8cd542c05e12af2153384634ab6201146c92d8fdf2e0659",
        )
        self.assertEqual(
            self.report["image"]["image_digest"],
            "sha256:804b8062e8fadf2607e5f09c9b52a4ef77284164316500ab805d652a722e5751",
        )
        payload = dict(self.report)
        expected = payload.pop("report_hash")
        self.assertEqual(stable_hash(payload), expected)

    def test_reports_contain_no_raw_arrays_private_paths_or_performance_claims(self):
        serialized = json.dumps(
            {"environment": self.environment, "e1": self.report}, sort_keys=True
        )
        for forbidden in (
            "source_values",
            "target_values",
            "C:\\Users",
            "/mnt/c/",
            "artifacts/private_argos_reproduction",
            "OPENAI_API_KEY",
            "sk-proj-",
        ):
            self.assertNotIn(forbidden, serialized)
        self.assertFalse(self.report["performance_metrics_computed"])
        self.assertEqual(self.report["provider_calls"], 0)
        self.assertFalse(self.report["dataset_accessed"])
        self.assertFalse(self.report["raw_rule_source_included"])
        self.assertFalse(self.report["raw_output_arrays_included"])
        self.assertFalse(self.report["private_paths_included"])

    def test_future_matrix_marks_only_e1_executed(self):
        matrix = (ROOT / "docs/argos_reproduction/FUTURE_EXECUTION_EXPERIMENT_MATRIX.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("E1 Rule candidate runtime smoke (`executed`, TASK-033)", matrix)
        self.assertIn("E2-E10 remain `not_run`", matrix)


if __name__ == "__main__":
    unittest.main()
