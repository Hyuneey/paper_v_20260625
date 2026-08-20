from __future__ import annotations

import copy
from dataclasses import replace
import inspect
import json
from pathlib import Path
import unittest

from paperworks.v6 import task039e3_r2r_d0_detector_design_v1 as d0
from paperworks.v6.task039e3_r2r_utility_evaluator_metrics_v1 import (
    ALARM_EPISODE_POLICY,
    ATTACK_EVENT_RECALL_FORMULA,
    NORMAL_FAR_FORMULA,
)


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs/v6/task039e3_r2r_d0_pca_spe_detector_v1.json"


class D0DetectorDesignV1Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.design = d0.build_d0_detector_design_v1()

    def test_canonical_design_and_factory_custody(self) -> None:
        self.assertEqual(
            d0.validate_d0_detector_design_v1(self.design),
            d0.D0_DETECTOR_DESIGN_HASH,
        )
        self.assertEqual(self.design.detector_id, "D0_PCA_SPE_V1")
        self.assertEqual(self.design.detector_family, "PCA_RECONSTRUCTION_SPE")
        self.assertEqual(self.design.training_mode, "NORMAL_ONLY")
        self.assertEqual(self.design.calibration_mode, "NORMAL_ONLY")
        self.assertFalse(self.design.scientific_llm)
        self.assertFalse(self.design.randomized_training)
        self.assertFalse(self.design.random_seed_required)

    def test_reconstruction_copy_deepcopy_replace_and_self_rehash_reject(self) -> None:
        attempts = [
            copy.copy(self.design),
            copy.deepcopy(self.design),
            replace(self.design),
            d0._build_expected_d0_detector_design_v1(),
        ]
        forged = replace(self.design, detector_family="ISOLATION_FOREST")
        forged = replace(forged, design_hash=d0.stable_hash_v1(d0._design_payload(forged)))
        attempts.append(forged)
        for value in attempts:
            with self.subTest(value=value.detector_family):
                with self.assertRaises(d0.D0DetectorDesignError):
                    d0.validate_d0_detector_design_v1(value)

    def test_factory_accepts_no_caller_hyperparameters(self) -> None:
        self.assertEqual(tuple(inspect.signature(d0.build_d0_detector_design_v1).parameters), ())
        for kwargs in (
            {"alpha": 0.01},
            {"variance_target": 0.99},
            {"feature_order": ("P1_FT01",)},
            {"detector_family": "GDN"},
            {"threshold": 1.0},
        ):
            with self.assertRaises(TypeError):
                d0.build_d0_detector_design_v1(**kwargs)  # type: ignore[call-arg]

    def test_complete_public_p1_feature_scope(self) -> None:
        schema = self.design.feature_schema
        self.assertEqual(schema.feature_count, 37)
        self.assertEqual(len(schema.ordered_features), 37)
        self.assertEqual(len(set(schema.ordered_features)), 37)
        self.assertTrue(all(name.startswith("P1_") for name in schema.ordered_features))
        self.assertEqual(schema.feature_order_hash, d0.P1_FEATURE_ORDER_HASH)
        self.assertEqual(schema.feature_set_hash, d0.P1_FEATURE_SET_HASH)
        self.assertEqual(
            d0.stable_hash_v1({"features": list(schema.ordered_features)}),
            d0.P1_FEATURE_ORDER_HASH,
        )
        self.assertTrue(schema.canonical_source_column_order)
        self.assertTrue(schema.timestamp_excluded)
        self.assertTrue(schema.labels_excluded)
        self.assertTrue(schema.attack_metadata_excluded)
        self.assertFalse(schema.feature_values_read_for_design)

    def test_split_roles_are_exact_and_fail_closed(self) -> None:
        split = self.design.split_policy
        self.assertEqual(
            split.model_fit_splits,
            ("NORMAL_TRAIN1_MODEL_FIT", "NORMAL_TRAIN2_MODEL_FIT"),
        )
        self.assertEqual(split.threshold_calibration_split, "NORMAL_TRAIN3_THRESHOLD_CALIBRATION")
        self.assertEqual(split.normal_sanity_split, "NORMAL_TRAIN4_SANITY_EVALUATION_ONLY")
        self.assertEqual(split.inner_evaluation_split, "TEST1_INNER_UTILITY_EVALUATION_ONLY")
        self.assertEqual(split.inner_metric_split, "LABEL_TEST1_INNER_METRIC_EVALUATION_ONLY")
        self.assertEqual(split.outer_feature_split, "TEST2_SEALED_OUTER")
        self.assertTrue(split.outer_sealed)
        self.assertFalse(split.train4_tuning_allowed)
        self.assertFalse(split.test1_selection_allowed)
        self.assertFalse(split.test1_label_selection_allowed)

    def test_preprocessing_pca_and_threshold_are_exact(self) -> None:
        prep = self.design.preprocessing_policy
        pca = self.design.pca_policy
        threshold = self.design.threshold_policy
        self.assertEqual(prep.ddof, 0)
        self.assertEqual(prep.scale_floor, 1e-12)
        self.assertFalse(prep.robust_scaler_allowed)
        self.assertFalse(prep.minmax_scaler_allowed)
        self.assertFalse(prep.caller_scaler_allowed)
        self.assertEqual(pca.backend_family, "NUMPY_LINEAR_ALGEBRA")
        self.assertEqual(pca.explained_variance_target, 0.95)
        self.assertEqual(pca.anomaly_score, "SQUARED_PREDICTION_ERROR")
        self.assertFalse(pca.randomized_algorithm_allowed)
        self.assertTrue(pca.residual_dimension_mandatory)
        self.assertEqual(
            pca.exact_eigenvalue_tie_at_cutoff,
            "FAIL_CLOSED_IF_CUTOFF_SPLITS_EXACT_TIED_EIGENVALUE_BLOCK",
        )
        self.assertEqual(threshold.alpha, 0.001)
        self.assertEqual(threshold.upper_quantile, 0.999)
        self.assertEqual(threshold.order_statistic_index, "ceil(0.999*n)-1_zero_based_after_ascending_sort")
        self.assertEqual(threshold.alarm_comparison_operator, "score > threshold")
        self.assertFalse(threshold.equality_is_alarm)
        self.assertFalse(threshold.label_tuning_allowed)
        self.assertFalse(threshold.d1_result_tuning_allowed)
        self.assertFalse(threshold.test_tuning_allowed)

    def test_alarm_and_metric_compatibility_matches_d1_authority(self) -> None:
        metric = self.design.metric_compatibility
        self.assertEqual(metric.alarm_episode_policy, ALARM_EPISODE_POLICY)
        self.assertEqual(metric.attack_event_recall_formula, ATTACK_EVENT_RECALL_FORMULA)
        self.assertEqual(metric.normal_far_formula, NORMAL_FAR_FORMULA)
        self.assertFalse(metric.metric_selection_allowed)

    def test_d1_independence_and_future_d2_binding(self) -> None:
        independence = self.design.independence
        self.assertFalse(independence.d1_performance_used_for_design)
        self.assertFalse(independence.d1_metric_artifact_read_for_design)
        self.assertFalse(independence.d1_prediction_content_read_for_design)
        self.assertTrue(independence.d1_rule_prediction_hash_bound_for_future_d2)
        self.assertEqual(
            independence.frozen_d1_rule_prediction_hash,
            "58c3c49f9657f68d35c830b12eeb493ce4bbf7669c90f04813fb80246c3c2682",
        )
        self.assertFalse(independence.gdn_primary_detector)
        self.assertFalse(independence.detector_selected_for_expected_d1_outperformance)

    def test_future_artifacts_and_detector_context_are_non_authorizing(self) -> None:
        future = self.design.future_artifact_contract
        self.assertTrue(future.prediction_label_blind)
        self.assertEqual(future.detector_error_context_split_role, "INNER_UTILITY")
        self.assertEqual(future.detector_error_context_purpose, "INNER_UTILITY_ASSESSMENT")
        self.assertEqual(future.detector_error_context_primary_direction, "FALSE_NEGATIVE")
        self.assertTrue(future.detector_error_context_supplementary_only)
        self.assertFalse(future.detector_error_context_validity_authority)
        self.assertFalse(future.detector_error_context_runtime_authority)
        self.assertFalse(future.d2_policy_frozen_in_this_task)

    def test_no_data_access_training_execution_or_authorization(self) -> None:
        for field in (
            "train1_value_reads",
            "train2_value_reads",
            "train3_value_reads",
            "train4_value_reads",
            "test1_value_reads",
            "label_reads",
            "test2_reads",
            "detector_training_executions",
            "detector_inner_executions",
        ):
            self.assertEqual(getattr(self.design, field), 0)
        self.assertFalse(self.design.d0_authorized)
        self.assertFalse(self.design.d2_authorized)
        self.assertFalse(self.design.outer_authorized)

    def test_tracked_config_is_exact_and_self_hashed(self) -> None:
        document = json.loads(CONFIG.read_text(encoding="utf-8"))
        self.assertEqual(document, d0.canonical_config_document_v1())
        self.assertEqual(d0.validate_d0_config_v1(document), document["config_hash"])
        self.assertEqual(
            d0.validate_d0_design_document_v1(document["design"]),
            d0.D0_DETECTOR_DESIGN_HASH,
        )

    def test_design_artifacts_do_not_encode_d1_performance(self) -> None:
        texts = (
            Path(d0.__file__).read_text(encoding="utf-8"),
            CONFIG.read_text(encoding="utf-8"),
        )
        forbidden = (
            "0.9285714285714286",
            "40.50255787059723",
            '"alarm_count":788',
            '"alarm_episode_count":626',
            "D1_METRICS_V1.json",
            "D1_RULE_PREDICTION_ARTIFACT_V1.json",
        )
        for text in texts:
            for token in forbidden:
                self.assertNotIn(token, text)


if __name__ == "__main__":
    unittest.main()
