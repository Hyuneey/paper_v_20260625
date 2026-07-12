import unittest

from experiments.argos_reproduction import mock_harness


class Task023ArgosHarnessTests(unittest.TestCase):
    def test_mock_harness_writes_report_without_execution(self):
        config_path = mock_harness.REPO_ROOT / "configs/argos_reproduction/task023_offline_harness.json"
        config = mock_harness.read_json(config_path)
        report = mock_harness.build_report(config, config_path)

        self.assertFalse(report["execution"]["generated_code_executed"])
        self.assertFalse(report["checks"]["provider_called"])
        self.assertFalse(report["checks"]["actual_llm_generated_python_executed"])
        self.assertTrue(report["checks"]["static_safety_passed"])
        self.assertTrue(report["checks"]["required_signature_valid"])
        self.assertIn("prompt_hash", report["hashes"])
        self.assertIn("mock_response_hash", report["hashes"])
        self.assertIn("rule_hash", report["hashes"])

    def test_safety_rejects_prohibited_exec(self):
        unsafe_code = "def inference(sample):\n    exec('print(1)')\n    return []\n"
        report = mock_harness.static_safety_checks(unsafe_code, allowed_imports=set())
        self.assertFalse(report["passed"])
        self.assertIn("PROHIBITED_CALL:exec", report["violations"])


if __name__ == "__main__":
    unittest.main()
