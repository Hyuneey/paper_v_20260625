from __future__ import annotations

import unittest

from paperworks.data import SplitRole
from paperworks.data.contracts import stable_hash
from paperworks.evaluation import (
    EvaluationConfig,
    EvaluationError,
    EvaluationMetric,
    EvaluationProtocol,
    assert_final_test_access_allowed,
    compute_auprc,
    compute_auroc,
    compute_pa_free_point_metrics,
    compute_point_adjusted_supplement,
    compute_range_iou,
    evaluate_point_predictions,
    validate_artifact_provenance,
    validate_config_frozen,
)


DATASET_MANIFEST_ID = "a" * 64
VALIDATION_SPLIT_ID = "b" * 64
TEST_SPLIT_ID = "c" * 64
CONFIG_ARTIFACT_ID = "d" * 64
PREDICTION_ARTIFACT_ID = "e" * 64


def config(**overrides) -> EvaluationConfig:
    values = {
        "config_name": "task014_synthetic_harness",
        "thresholds_frozen": True,
        "candidate_k_frozen": True,
        "prompt_config_frozen": True,
        "fusion_weights_frozen": True,
        "point_adjusted_supplementary_enabled": False,
    }
    values.update(overrides)
    return EvaluationConfig(**values)


def protocol(**overrides) -> EvaluationProtocol:
    values = {
        "dataset_name": "synthetic",
        "dataset_status": "synthetic_fixture",
        "terms_of_use_status": "not_applicable_synthetic_fixture",
        "dataset_manifest_id": DATASET_MANIFEST_ID,
        "split_manifest_ids": {
            "validation": VALIDATION_SPLIT_ID,
            "test": TEST_SPLIT_ID,
        },
        "dec007_resolved": False,
        "final_test_access_approved": False,
        "config": config(),
    }
    values.update(overrides)
    return EvaluationProtocol(**values)


def provenance() -> dict[str, str]:
    return {
        "dataset_manifest": DATASET_MANIFEST_ID,
        "split_manifest": VALIDATION_SPLIT_ID,
        "config": CONFIG_ARTIFACT_ID,
        "runtime_or_prediction_artifact": PREDICTION_ARTIFACT_ID,
    }


class EvaluationHarnessTests(unittest.TestCase):
    def test_pa_free_point_metrics_are_correct(self) -> None:
        metrics = {metric.name: metric.value for metric in compute_pa_free_point_metrics([0, 1, 1, 0], [0, 1, 0, 1])}

        self.assertEqual(metrics["pa_free_tp"], 1)
        self.assertEqual(metrics["pa_free_fp"], 1)
        self.assertEqual(metrics["pa_free_fn"], 1)
        self.assertEqual(metrics["pa_free_tn"], 1)
        self.assertEqual(metrics["pa_free_precision"], 0.5)
        self.assertEqual(metrics["pa_free_recall"], 0.5)
        self.assertEqual(metrics["pa_free_f1"], 0.5)

    def test_auroc_and_auprc_are_correct(self) -> None:
        labels = [0, 0, 1, 1]
        scores = [0.1, 0.4, 0.35, 0.8]

        self.assertAlmostEqual(compute_auroc(labels, scores), 0.75)
        self.assertAlmostEqual(compute_auprc(labels, scores), (1.0 + 2 / 3) / 2)

    def test_point_adjusted_is_supplementary_only(self) -> None:
        metrics = compute_point_adjusted_supplement([0, 1, 1, 0], [0, 1, 0, 0])

        self.assertTrue(all(not metric.primary for metric in metrics))
        self.assertTrue(all(metric.point_adjusted for metric in metrics))
        self.assertIn("point_adjusted_f1", {metric.name for metric in metrics})
        with self.assertRaises(EvaluationError):
            EvaluationMetric("point_adjusted_f1", 1.0, "point", primary=True, point_adjusted=True)

    def test_range_iou_is_correct(self) -> None:
        metric = compute_range_iou([(1, 4)], [(2, 5)])

        self.assertEqual(metric.name, "range_iou")
        self.assertAlmostEqual(metric.value, 2 / 4)

    def test_sealed_test_guard_blocks_unresolved_dec007(self) -> None:
        with self.assertRaisesRegex(EvaluationError, "DEC-007"):
            assert_final_test_access_allowed(protocol(), SplitRole.TEST)

    def test_validation_evaluation_allowed_without_final_test_access(self) -> None:
        report = evaluate_point_predictions(
            labels=[0, 1, 1, 0],
            predictions=[0, 1, 0, 1],
            scores=[0.1, 0.9, 0.2, 0.8],
            split_role=SplitRole.VALIDATION,
            protocol=protocol(),
            artifact_provenance=provenance(),
            code_commit="abc123",
            created_at="2026-06-25T00:00:00Z",
        )

        self.assertEqual(report.split_role, SplitRole.VALIDATION)
        self.assertFalse(report.sealed_test_audit.final_test_accessed)
        self.assertIn("pa_free_f1", {metric.name for metric in report.primary_metrics})
        self.assertIn("auroc", {metric.name for metric in report.primary_metrics})
        self.assertTrue(report.limitations)

    def test_config_freezing_guard(self) -> None:
        with self.assertRaisesRegex(EvaluationError, "frozen"):
            validate_config_frozen(config(thresholds_frozen=False))

        with self.assertRaisesRegex(EvaluationError, "frozen"):
            evaluate_point_predictions(
                labels=[0, 1],
                predictions=[0, 1],
                scores=None,
                split_role=SplitRole.VALIDATION,
                protocol=protocol(config=config(candidate_k_frozen=False)),
                artifact_provenance=provenance(),
            )

    def test_artifact_provenance_guard(self) -> None:
        with self.assertRaisesRegex(EvaluationError, "missing artifact"):
            validate_artifact_provenance({"dataset_manifest": DATASET_MANIFEST_ID})

        bad = provenance()
        bad["config"] = "short"
        with self.assertRaisesRegex(EvaluationError, "64-character"):
            validate_artifact_provenance(bad)

    def test_report_is_deterministic_and_contains_no_raw_sequences(self) -> None:
        kwargs = dict(
            labels=[0, 1, 1, 0],
            predictions=[0, 1, 0, 1],
            scores=[0.1, 0.9, 0.2, 0.8],
            split_role=SplitRole.VALIDATION,
            protocol=protocol(config=config(point_adjusted_supplementary_enabled=True)),
            artifact_provenance=provenance(),
            code_commit="abc123",
            created_at="2026-06-25T00:00:00Z",
        )
        first = evaluate_point_predictions(**kwargs)
        second = evaluate_point_predictions(**kwargs)

        self.assertEqual(first.to_dict(), second.to_dict())
        self.assertEqual(first.report_id, second.report_id)
        rendered = str(first.to_dict())
        self.assertNotIn("normal.csv", rendered)
        self.assertNotIn("attack.csv", rendered)
        self.assertNotIn("merged.csv", rendered)
        self.assertNotIn("[10, 10, 10", rendered)
        self.assertIn("point_adjusted_f1", {metric.name for metric in first.supplementary_metrics})

    def test_final_test_access_requires_explicit_resolution_and_frozen_config(self) -> None:
        approved = protocol(
            dataset_status="official_verified",
            terms_of_use_status="verified",
            dec007_resolved=True,
            final_test_access_approved=True,
        )
        audit = assert_final_test_access_allowed(approved, SplitRole.TEST)

        self.assertTrue(audit.final_test_accessed)
        self.assertTrue(audit.final_test_access_approved)

    def test_protocol_hash_changes_with_config(self) -> None:
        first = protocol()
        second = protocol(config=config(point_adjusted_supplementary_enabled=True))

        self.assertNotEqual(first.protocol_hash, second.protocol_hash)
        self.assertEqual(len(stable_hash(first.to_dict())), 64)


if __name__ == "__main__":
    unittest.main()
