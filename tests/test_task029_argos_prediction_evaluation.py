import json
import tempfile
import unittest
from pathlib import Path

from experiments.argos_reproduction.prediction_evaluation import (
    PredictionValidationError,
    calculate_confusion_counts,
    calculate_point_metrics,
    compose_prediction_labels,
    evaluate_prediction_arrays,
    run_protocol,
    sha256_json,
)


REPO_ROOT = Path(__file__).resolve().parents[1]


class Task029PredictionEvaluationTests(unittest.TestCase):
    def test_fn_fusion_uses_elementwise_max(self):
        combined = compose_prediction_labels(
            "combined_fn_max",
            rule_prediction_labels=[0, 1, 1, 0],
            detector_prediction_labels=[1, 0, 1, 0],
        )
        self.assertEqual(combined, (1, 1, 1, 0))

    def test_fp_fusion_uses_elementwise_min(self):
        combined = compose_prediction_labels(
            "combined_fp_min",
            rule_prediction_labels=[0, 1, 1, 0],
            detector_prediction_labels=[1, 0, 1, 0],
        )
        self.assertEqual(combined, (0, 0, 1, 0))

    def test_point_metrics_and_confusion_counts(self):
        counts = calculate_confusion_counts([0, 1, 0, 1], [0, 1, 1, 0])
        self.assertEqual(counts.true_positive, 1)
        self.assertEqual(counts.false_positive, 1)
        self.assertEqual(counts.true_negative, 1)
        self.assertEqual(counts.false_negative, 1)
        metrics = calculate_point_metrics(counts)
        self.assertEqual(metrics.precision, 0.5)
        self.assertEqual(metrics.recall, 0.5)
        self.assertEqual(metrics.point_f1, 0.5)

    def test_shape_and_binary_domain_are_enforced(self):
        with self.assertRaises(PredictionValidationError):
            compose_prediction_labels(
                "combined_fn_max",
                rule_prediction_labels=[0, 1],
                detector_prediction_labels=[0],
            )
        with self.assertRaises(PredictionValidationError):
            evaluate_prediction_arrays(
                ground_truth_labels=[0, 1],
                rule_prediction_labels=[0, 2],
                detector_prediction_labels=[0, 1],
            )
        with self.assertRaises(PredictionValidationError):
            evaluate_prediction_arrays(
                ground_truth_labels=[[0], [1]],
                rule_prediction_labels=[0, 1],
                detector_prediction_labels=[0, 1],
            )

    def test_required_prediction_inputs_are_enforced(self):
        with self.assertRaises(PredictionValidationError):
            compose_prediction_labels("rule_only")
        with self.assertRaises(PredictionValidationError):
            compose_prediction_labels("detector_only")

    def test_protocol_uses_synthetic_arrays_without_execution(self):
        config_path = REPO_ROOT / "configs/argos_reproduction/task029_evaluation_protocol.json"
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "report.json"
            report = run_protocol(config_path, output_path)
            persisted = json.loads(output_path.read_text(encoding="utf-8"))

        self.assertEqual(report, persisted)
        self.assertEqual(report["fixture"]["fixture_kind"], "synthetic_non_kpi_non_swat")
        self.assertFalse(report["boundaries"]["generated_code_loaded"])
        self.assertFalse(report["boundaries"]["generated_code_executed"])
        self.assertFalse(report["boundaries"]["captured_rule_accessed"])
        self.assertEqual(
            report["evaluation"]["compositions"]["combined_fn_max"][
                "confusion_counts"
            ]["false_negative"],
            0,
        )
        expected_hash = report.pop("report_hash")
        self.assertEqual(sha256_json(report), expected_hash)

    def test_harness_has_no_generated_code_loading_surface(self):
        source = (
            REPO_ROOT
            / "experiments/argos_reproduction/prediction_evaluation.py"
        ).read_text(encoding="utf-8")
        self.assertNotIn("importlib", source)
        self.assertNotIn("subprocess", source)
        self.assertNotIn("compile(", source)
        self.assertNotIn("exec(", source)
        self.assertNotIn("eval(", source)
        self.assertNotIn("rule_file", source)

    def test_audit_report_preserves_non_execution_boundaries(self):
        report_path = (
            REPO_ROOT / "docs/task_reports/TASK-029_AUDIT_REPORT.json"
        )
        report = json.loads(report_path.read_text(encoding="utf-8"))
        boundaries = report["boundaries"]

        self.assertEqual(report["task_status"], "complete_non_executing_audit")
        self.assertEqual(boundaries["provider_calls"], 0)
        self.assertFalse(boundaries["generated_code_loaded"])
        self.assertFalse(boundaries["generated_code_executed"])
        self.assertFalse(boundaries["captured_rule_accessed"])
        self.assertFalse(boundaries["kpi_accessed"])
        self.assertFalse(boundaries["swat_accessed"])
        self.assertFalse(boundaries["src_paperworks_changed"])
        expected_hash = report.pop("report_hash")
        self.assertEqual(sha256_json(report), expected_hash)

    def test_future_matrix_remains_not_run(self):
        matrix = (
            REPO_ROOT
            / "docs/argos_reproduction/FUTURE_EXECUTION_EXPERIMENT_MATRIX.md"
        ).read_text(encoding="utf-8")
        self.assertIn("All experiments are `not_run`", matrix)
        self.assertIn("E5 FN fusion", matrix)
        self.assertIn("E6 FP fusion", matrix)


if __name__ == "__main__":
    unittest.main()
