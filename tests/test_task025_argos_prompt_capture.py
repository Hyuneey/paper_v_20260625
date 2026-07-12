import csv
import shutil
import unittest
from pathlib import Path

from experiments.argos_reproduction import prompt_capture


class Task025ArgosPromptCaptureTests(unittest.TestCase):
    def test_system_prompt_comes_from_pinned_argos_template(self):
        prompt = prompt_capture.build_system_prompt(chunk_size=1000)

        self.assertEqual(
            prompt["source_path"],
            "external/argos/agent/prompts/detection.py",
        )
        self.assertIn("inference(sample: np.ndarray)", prompt["system_prompt"])
        self.assertIn("```python", prompt["system_prompt"])
        self.assertIn("Normal Rule 1", prompt["system_prompt"])
        self.assertIn("Abnormal Rule 1", prompt["system_prompt"])

    def test_chunk_selection_skips_normal_only_first_chunk(self):
        rows = [
            {"value": 1.0, "label": 0, "index": 0},
            {"value": 1.1, "label": 0, "index": 1},
            {"value": 1.2, "label": 0, "index": 2},
            {"value": 1.3, "label": 0, "index": 3},
            {"value": 1.0, "label": 0, "index": 4},
            {"value": 9.0, "label": 1, "index": 5},
            {"value": 1.2, "label": 0, "index": 6},
            {"value": 1.3, "label": 0, "index": 7},
        ]
        policy = {
            "chunk_size": 4,
            "train_test_split": 1.0,
            "val_split": 0.0,
        }

        chunk = prompt_capture.select_prompt_chunk(rows, policy)

        self.assertEqual(chunk["start_position"], 4)
        self.assertEqual(chunk["end_position_exclusive"], 8)
        self.assertEqual(chunk["label_counts"], {"0": 3, "1": 1})

    def test_provider_mode_refuses_without_approval_and_cli_flag(self):
        config = {
            "provider": {
                "mode": "provider",
                "required_credential_env": ["OPENAI_AZURE_API_KEY"],
            }
        }

        gate = prompt_capture.require_provider_gate(
            config,
            allow_real_provider_call=False,
            approval=None,
        )

        self.assertFalse(gate["real_provider_call_allowed"])
        self.assertIn("cli_allow_real_provider_call_missing", gate["blockers"])
        self.assertIn("approval_artifact_missing", gate["blockers"])
        self.assertIn("credential_missing:OPENAI_AZURE_API_KEY", gate["blockers"])

    def test_run_capture_writes_hash_reports_without_execution(self):
        private_root = (
            prompt_capture.REPO_ROOT
            / "artifacts"
            / "private_argos_reproduction"
            / "test_task025_capture"
        )
        if private_root.exists():
            shutil.rmtree(private_root)
        converted_path = private_root / "converted.csv"
        manifest_path = private_root / "task024_manifest.json"
        config_path = private_root / "task025_config.json"
        output_chunk_path = private_root / "chunk_report.json"
        output_capture_path = private_root / "capture_report.json"
        converted_path.parent.mkdir(parents=True, exist_ok=True)
        with converted_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=["value", "label", "index"])
            writer.writeheader()
            for row in [
                {"value": 1.0, "label": 0, "index": 0},
                {"value": 1.1, "label": 0, "index": 1},
                {"value": 1.2, "label": 0, "index": 2},
                {"value": 1.3, "label": 0, "index": 3},
                {"value": 1.0, "label": 0, "index": 4},
                {"value": 9.0, "label": 1, "index": 5},
                {"value": 1.2, "label": 0, "index": 6},
                {"value": 1.3, "label": 0, "index": 7},
            ]:
                writer.writerow(row)
        converted_hash = prompt_capture.sha256_file(converted_path)
        prompt_capture.write_json(
            manifest_path,
            {
                "converted_argos_csv": {
                    "converted_path": converted_path.relative_to(prompt_capture.REPO_ROOT).as_posix()
                }
            },
        )
        prompt_capture.write_json(
            config_path,
            {
                "mode": "train-LLM-only",
                "private_artifact_root": private_root.relative_to(prompt_capture.REPO_ROOT).as_posix(),
                "task024_manifest_path": manifest_path.relative_to(prompt_capture.REPO_ROOT).as_posix(),
                "frozen_inputs": {
                    "argos_commit": "6b24161ff08de069840a1fb4fbaecf7bf8e393f1",
                    "mode": "train-LLM-only",
                    "combined_mode_status": "deferred",
                    "kpi_source_commit": "test",
                    "selected_kpi_id": "test-kpi",
                    "converted_csv_sha256": converted_hash,
                },
                "chunk_selection": {
                    "chunk_size": 4,
                    "train_test_split": 1.0,
                    "val_split": 0.0,
                    "minimum_normal_count": 1,
                    "minimum_anomaly_count": 1,
                    "source": "synthetic_test",
                    "partition": "argos_train_df",
                    "scan_order": "increasing_start_position",
                    "selection_rule": "first eligible chunk",
                    "uses_generated_rule_performance": False,
                    "uses_detector_performance": False,
                },
                "provider": {
                    "mode": "mock",
                    "default_mode": "mock",
                    "allow_network": False,
                    "approval_path": "configs/argos_reproduction/task025_provider_approval.template.json",
                    "required_credential_env": [],
                    "manual_response_path": (
                        private_root / "manual.md"
                    ).relative_to(prompt_capture.REPO_ROOT).as_posix(),
                },
                "mock_response": (
                    "```python\n"
                    "import numpy as np\n\n"
                    "def inference(sample: np.ndarray) -> np.ndarray:\n"
                    "    return np.zeros(sample.shape[0], dtype=int)\n"
                    "```"
                ),
                "allowed_imports": ["numpy"],
                "boundaries": {
                    "real_provider_calls": False,
                    "actual_llm_generated_python_execution": False,
                    "benchmark_claims": False,
                },
                "output_chunk_manifest_path": output_chunk_path.relative_to(prompt_capture.REPO_ROOT).as_posix(),
                "output_capture_report_path": output_capture_path.relative_to(prompt_capture.REPO_ROOT).as_posix(),
            },
        )

        try:
            result = prompt_capture.run_capture(config_path)
        finally:
            if private_root.exists():
                shutil.rmtree(private_root)

        chunk_report = result["chunk_manifest"]
        capture_report = result["capture_report"]
        self.assertEqual(chunk_report["chunk"]["start_position"], 4)
        self.assertFalse(chunk_report["raw_rows_tracked"])
        self.assertTrue(capture_report["response_capture"]["code_extracted"])
        self.assertTrue(capture_report["response_capture"]["signature_valid"])
        self.assertFalse(capture_report["response_capture"]["execution_performed"])
        self.assertFalse(capture_report["prompt_retention"]["full_prompt_tracked"])
        self.assertNotIn("messages", capture_report)


if __name__ == "__main__":
    unittest.main()
