import json
import os
import shutil
import unittest
from pathlib import Path
from unittest import mock

from experiments.argos_reproduction import prompt_capture, provider_capture, rule_static_analysis


class Task026ArgosRealCaptureTests(unittest.TestCase):
    def setUp(self):
        self.private_root = (
            prompt_capture.REPO_ROOT
            / "artifacts"
            / "private_argos_reproduction"
            / self.id().split(".")[-1]
        )
        if self.private_root.exists():
            shutil.rmtree(self.private_root)
        self.private_root.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        if self.private_root.exists():
            shutil.rmtree(self.private_root)

    def _write_base_files(self, capture_mode="manual_capture"):
        request = {
            "messages": [
                {"role": "system", "content": "system prompt"},
                {"role": "user", "content": "user prompt"},
            ]
        }
        request_path = self.private_root / "task025" / "complete_request.json"
        task025_report_path = self.private_root / "task025_capture_report.json"
        approval_path = self.private_root / "approval.json"
        config_path = self.private_root / "task026_config.json"
        output_capture_path = self.private_root / "capture_report.json"
        output_static_path = self.private_root / "static_report.json"
        manual_response_path = self.private_root / "manual_response.md"
        manual_metadata_path = self.private_root / "manual_response_metadata.json"

        prompt_capture.write_json(request_path, request)
        prompt_capture.write_json(
            task025_report_path,
            {
                "private_artifacts": {
                    "complete_request_path": request_path.relative_to(prompt_capture.REPO_ROOT).as_posix()
                }
            },
        )
        prompt_capture.write_json(
            approval_path,
            {
                "decision_id": "DEC-028",
                "decision_status": "open",
                "approved": False,
                "provider": None,
                "model": None,
                "model_version_identifier": None,
                "temperature": None,
                "max_calls": 1,
                "max_input_tokens": None,
                "max_output_tokens": None,
                "max_cost_usd": None,
                "credential_env_vars": [],
                "prompt_response_retention": {},
                "approved_by": None,
                "approval_date": None,
            },
        )
        config = {
            "capture_mode": capture_mode,
            "approval_path": approval_path.relative_to(prompt_capture.REPO_ROOT).as_posix(),
            "task025_capture_report_path": task025_report_path.relative_to(prompt_capture.REPO_ROOT).as_posix(),
            "private_artifact_root": self.private_root.relative_to(prompt_capture.REPO_ROOT).as_posix(),
            "manual_capture": {
                "response_path": manual_response_path.relative_to(prompt_capture.REPO_ROOT).as_posix(),
                "metadata_path": manual_metadata_path.relative_to(prompt_capture.REPO_ROOT).as_posix(),
            },
            "request_timeout_seconds": 1,
            "allowed_imports": ["numpy"],
            "frozen_inputs": {
                "complete_request_hash": prompt_capture.sha256_json(request),
                "argos_commit": "6b24161ff08de069840a1fb4fbaecf7bf8e393f1",
                "mode": "train-LLM-only",
                "combined_mode_status": "deferred",
                "selected_kpi_id": "test-kpi",
                "converted_csv_sha256": "test-sha",
                "chunk_start_position": 0,
                "chunk_end_position_exclusive": 4,
                "chunk_hash": "test-chunk",
            },
            "boundaries": {
                "generated_python_execution": False,
                "kpi_performance_evaluation": False,
                "src_paperworks_changes": False,
            },
            "output_capture_report_path": output_capture_path.relative_to(prompt_capture.REPO_ROOT).as_posix(),
            "output_static_analysis_path": output_static_path.relative_to(prompt_capture.REPO_ROOT).as_posix(),
        }
        prompt_capture.write_json(config_path, config)
        return {
            "config_path": config_path,
            "approval_path": approval_path,
            "manual_response_path": manual_response_path,
            "manual_metadata_path": manual_metadata_path,
        }

    def test_static_analysis_reports_structure_without_execution(self):
        response = (
            "```python\n"
            "import numpy as np\n\n"
            "# Normal Rule 1: stable values remain normal\n"
            "# Abnormal Rule 1: values above a threshold are anomalous\n"
            "def inference(sample: np.ndarray) -> np.ndarray:\n"
            "    values = sample[:, 0]\n"
            "    labels = np.zeros(sample.shape[0], dtype=int)\n"
            "    labels[values > 2.5] = 1\n"
            "    return labels\n"
            "```"
        )

        analysis = rule_static_analysis.analyze_response(response, {"numpy"})

        self.assertEqual(analysis["code_fence_count"], 1)
        self.assertEqual(analysis["inference_definition_count"], 1)
        self.assertEqual(analysis["syntax_parse_status"], "parsed")
        self.assertEqual(analysis["required_signature_status"], "valid")
        self.assertTrue(analysis["static_safety_passed"])
        self.assertIn("numpy", analysis["imported_modules"])
        self.assertIn("Gt", analysis["comparison_operators_used"])
        self.assertIn(2.5, analysis["threshold_like_numeric_constants"])
        self.assertTrue(analysis["normal_rule_comments_exist"])
        self.assertTrue(analysis["abnormal_rule_comments_exist"])
        self.assertFalse(analysis["execution_performed"])

    def test_missing_manual_response_writes_pending_reports(self):
        paths = self._write_base_files(capture_mode="manual_capture")

        result = provider_capture.run_capture(paths["config_path"])

        capture_report = result["capture_report"]
        static_report = result["static_report"]
        self.assertEqual(
            capture_report["capture_status"],
            "not_captured_pending_approval_or_manual_response",
        )
        self.assertEqual(capture_report["pending_reason"], "manual_response_file_missing")
        self.assertEqual(capture_report["provider_metadata"]["request_count"], 0)
        self.assertFalse(capture_report["execution_performed"])
        self.assertEqual(static_report["analysis_status"], "not_available_no_response_captured")

    def test_manual_capture_statically_analyzes_one_response_without_execution(self):
        paths = self._write_base_files(capture_mode="manual_capture")
        paths["manual_response_path"].write_text(
            "```python\n"
            "import numpy as np\n\n"
            "def inference(sample: np.ndarray) -> np.ndarray:\n"
            "    values = sample[:, 0]\n"
            "    labels = np.zeros(sample.shape[0], dtype=int)\n"
            "    labels[values > 3.0] = 1\n"
            "    return labels\n"
            "```\n",
            encoding="utf-8",
        )
        prompt_capture.write_json(
            paths["manual_metadata_path"],
            {
                "model": "manual-test-model",
                "interface": "manual_test_fixture",
                "capture_date": "2026-07-13",
                "usage": {"input_tokens": 10, "output_tokens": 20},
            },
        )

        result = provider_capture.run_capture(paths["config_path"])

        capture_report = result["capture_report"]
        static_report = result["static_report"]
        self.assertEqual(capture_report["capture_status"], "captured")
        self.assertEqual(capture_report["capture_type"], "manual_exploratory_capture")
        self.assertIsNotNone(capture_report["response_hash"])
        self.assertIsNotNone(capture_report["rule_hash"])
        self.assertFalse(capture_report["generated_python_executed"])
        self.assertFalse(capture_report["performance_metric_reported"])
        self.assertEqual(static_report["analysis_status"], "completed")
        self.assertFalse(static_report["analysis"]["execution_performed"])
        self.assertEqual(static_report["analysis"]["required_signature_status"], "valid")

    def test_api_capture_blocks_without_approval_flag_or_credentials(self):
        paths = self._write_base_files(capture_mode="api_capture")

        result = provider_capture.run_capture(paths["config_path"], allow_real_provider_call=False)

        capture_report = result["capture_report"]
        self.assertEqual(
            capture_report["capture_status"],
            "not_captured_pending_approval_or_manual_response",
        )
        self.assertIn("approval_not_true", capture_report["blockers"])
        self.assertIn("dec028_not_resolved", capture_report["blockers"])
        self.assertIn("cli_allow_real_provider_call_missing", capture_report["blockers"])
        self.assertIn("provider_not_supported_by_task026_api_client", capture_report["blockers"])
        self.assertEqual(capture_report["provider_metadata"]["request_count"], 0)

    def test_api_provider_error_is_not_reported_as_captured_rule_response(self):
        paths = self._write_base_files(capture_mode="api_capture")
        prompt_capture.write_json(
            paths["approval_path"],
            {
                "decision_id": "DEC-028",
                "decision_status": "resolved",
                "approved": True,
                "provider": "openai_responses",
                "model": "missing-model",
                "model_version_identifier": "missing-model",
                "temperature": 0,
                "max_calls": 1,
                "max_input_tokens": 100,
                "max_output_tokens": 100,
                "max_cost_usd": 1.0,
                "credential_env_vars": [],
                "prompt_response_retention": {},
                "approved_by": "test",
                "approval_date": "2026-07-13",
            },
        )

        fake_provider_result = {
            "raw_json": {
                "error": {
                    "type": "invalid_request_error",
                    "code": None,
                    "message": "Model not found missing-model",
                }
            },
            "raw_text": "",
            "http_status_code": 404,
            "duration_seconds": 0.1,
            "request_count": 1,
            "request_id": None,
            "usage": None,
            "model_reported": None,
            "provider_error": {
                "type": "invalid_request_error",
                "code": None,
                "message": "Model not found missing-model",
            },
        }

        with mock.patch.object(
            provider_capture,
            "approval_blockers",
            return_value=[],
        ), mock.patch.object(
            provider_capture,
            "call_openai_responses_once",
            return_value=fake_provider_result,
        ):
            result = provider_capture.run_capture(paths["config_path"], allow_real_provider_call=True)

        capture_report = result["capture_report"]
        static_report = result["static_report"]
        self.assertEqual(capture_report["capture_status"], "provider_error_no_rule_response")
        self.assertEqual(capture_report["provider_metadata"]["http_status_code"], 404)
        self.assertEqual(capture_report["provider_metadata"]["request_count"], 1)
        self.assertIsNone(capture_report["rule_hash"])
        self.assertFalse(capture_report["generated_python_executed"])
        self.assertEqual(static_report["analysis_status"], "not_available_provider_error_or_empty_response")

    def test_openai_request_omits_temperature_when_approval_temperature_is_null(self):
        captured_payloads = []

        class FakeResponse:
            status = 200

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

            def read(self):
                return json.dumps(
                    {
                        "id": "resp_test",
                        "model": "gpt-5.6-luna",
                        "output_text": "```python\nimport numpy as np\n\ndef inference(sample: np.ndarray) -> np.ndarray:\n    return np.zeros(sample.shape[0], dtype=int)\n```",
                    }
                ).encode("utf-8")

        def fake_urlopen(request, timeout):
            captured_payloads.append(json.loads(request.data.decode("utf-8")))
            return FakeResponse()

        with mock.patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}), mock.patch.object(
            provider_capture.urllib.request,
            "urlopen",
            side_effect=fake_urlopen,
        ):
            result = provider_capture.call_openai_responses_once(
                {"messages": [{"role": "user", "content": "test"}]},
                {
                    "credential_env_vars": ["OPENAI_API_KEY"],
                    "model": "gpt-5.6-luna",
                    "max_output_tokens": 100,
                    "temperature": None,
                },
                timeout_seconds=1,
            )

        self.assertEqual(result["request_count"], 1)
        self.assertEqual(captured_payloads[0]["model"], "gpt-5.6-luna")
        self.assertNotIn("temperature", captured_payloads[0])

    def test_provider_call_receipt_blocks_a_second_api_request(self):
        paths = self._write_base_files(capture_mode="api_capture")
        approval = {
            "decision_id": "DEC-029",
            "decision_status": "resolved",
            "approved": True,
            "provider": "openai_responses",
            "model": "gpt-5.6-luna",
            "model_version_identifier": "gpt-5.6-luna",
            "temperature": None,
            "max_calls": 1,
            "max_input_tokens": 20000,
            "max_output_tokens": 2000,
            "max_cost_usd": 1.0,
            "credential_env_vars": ["OPENAI_API_KEY"],
            "prompt_response_retention": {"raw_response_retention": "ignored_private_only"},
            "approved_by": "Hyuneey",
            "approval_date": "2026-07-13",
        }
        prompt_capture.write_json(paths["approval_path"], approval)
        config = provider_capture.read_json(paths["config_path"])
        config.update(
            {
                "task_id": "TASK-026R",
                "artifact_namespace": "task026r",
                "report_statement": "TASK-026R one-shot remediation capture.",
            }
        )
        prompt_capture.write_json(paths["config_path"], config)
        fake_provider_result = {
            "raw_json": {},
            "raw_text": (
                "```python\nimport numpy as np\n\n"
                "def inference(sample: np.ndarray) -> np.ndarray:\n"
                "    return np.zeros(sample.shape[0], dtype=int)\n```"
            ),
            "http_status_code": 200,
            "duration_seconds": 0.1,
            "request_count": 1,
            "request_id": "resp_test",
            "usage": {"input_tokens": 10, "output_tokens": 20},
            "model_reported": "gpt-5.6-luna",
            "provider_error": None,
        }

        with mock.patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}), mock.patch.object(
            provider_capture,
            "call_openai_responses_once",
            return_value=fake_provider_result,
        ) as provider_call:
            first = provider_capture.run_capture(
                paths["config_path"], allow_real_provider_call=True
            )
            second = provider_capture.run_capture(
                paths["config_path"], allow_real_provider_call=True
            )

        self.assertEqual(first["capture_report"]["task_id"], "TASK-026R")
        self.assertEqual(
            first["capture_report"]["artifact_type"],
            "task026r_real_llm_capture_report",
        )
        self.assertEqual(provider_call.call_count, 1)
        self.assertIn("provider_call_already_attempted", second["capture_report"]["blockers"])
        receipt = provider_capture.read_json(
            self.private_root / "metadata" / "provider_call_receipt.json"
        )
        self.assertEqual(receipt["status"], "completed")
        self.assertFalse(receipt["temperature_parameter_sent"])
        self.assertEqual(receipt["request_count"], 1)


if __name__ == "__main__":
    unittest.main()
