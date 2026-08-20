from __future__ import annotations

import copy
from dataclasses import replace
import inspect
import json
from pathlib import Path
import unittest

from paperworks.v6 import task039e3_r2r_d0_detector_design_v1 as d0


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs" / "v6" / "task039e3_r2r_d0_pca_spe_detector_v1.json"


def _rehash_design(document: dict[str, object]) -> None:
    payload = copy.deepcopy(document)
    payload.pop("design_hash", None)
    document["design_hash"] = d0.stable_hash_v1(payload)


def _rehash_config(document: dict[str, object]) -> None:
    payload = copy.deepcopy(document)
    payload.pop("config_hash", None)
    document["config_hash"] = d0.stable_hash_v1(payload)


class D0DetectorDesignV1IndependentAudit(unittest.TestCase):
    def setUp(self) -> None:
        self.config = json.loads(CONFIG.read_text(encoding="utf-8"))
        self.canonical_design = copy.deepcopy(self.config["design"])

    def _assert_semantic_design_mutation_rejected(self, mutate) -> None:
        candidate = copy.deepcopy(self.canonical_design)
        mutate(candidate)
        _rehash_design(candidate)
        with self.assertRaises(d0.D0DetectorDesignError):
            d0.validate_d0_design_document_v1(candidate)

    def test_self_rehashed_scientific_policy_attacks_all_reject(self) -> None:
        mutations = (
            lambda d: d["threshold_policy"].__setitem__("alpha", 0.01),
            lambda d: d["threshold_policy"].__setitem__("upper_quantile", 0.995),
            lambda d: d["threshold_policy"].__setitem__("order_statistic_index", "LINEAR_INTERPOLATION"),
            lambda d: d["threshold_policy"].__setitem__("interpolation", "LINEAR"),
            lambda d: d["threshold_policy"].__setitem__("alarm_comparison_operator", "score >= threshold"),
            lambda d: d["threshold_policy"].__setitem__("label_tuning_allowed", True),
            lambda d: d["threshold_policy"].__setitem__("test_tuning_allowed", True),
            lambda d: d["threshold_policy"].__setitem__("d1_result_tuning_allowed", True),
            lambda d: d["pca_policy"].__setitem__("explained_variance_target", 0.99),
            lambda d: d["pca_policy"].__setitem__("component_selection", "CALLER_SELECTED_K"),
            lambda d: d["pca_policy"].__setitem__("randomized_algorithm_allowed", True),
            lambda d: d["pca_policy"].__setitem__("backend_family", "RANDOMIZED_PCA"),
            lambda d: d["pca_policy"].__setitem__("anomaly_score", "ABSOLUTE_RESIDUAL"),
            lambda d: d["pca_policy"].__setitem__("score_smoothing", True),
            lambda d: d["pca_policy"].__setitem__("temporal_dilation", True),
            lambda d: d["pca_policy"].__setitem__("point_adjustment", True),
            lambda d: d["preprocessing_policy"].__setitem__("ddof", 1),
            lambda d: d["preprocessing_policy"].__setitem__("scale_floor", 1e-6),
            lambda d: d["preprocessing_policy"].__setitem__("robust_scaler_allowed", True),
            lambda d: d["split_policy"].__setitem__("threshold_calibration_split", "TEST1"),
            lambda d: d["split_policy"].__setitem__("train4_tuning_allowed", True),
            lambda d: d["split_policy"].__setitem__("outer_sealed", False),
            lambda d: d["metric_compatibility"].__setitem__("attack_event_recall_formula", "POINT_RECALL"),
            lambda d: d["metric_compatibility"].__setitem__("normal_far_formula", "ALARM_POINTS_PER_HOUR"),
            lambda d: d["metric_compatibility"].__setitem__("alarm_episode_policy", "DILATED_EPISODES"),
            lambda d: d.__setitem__("detector_family", "ISOLATION_FOREST"),
            lambda d: d.__setitem__("detector_family", "GDN"),
            lambda d: d.__setitem__("detector_family", "NEURAL_AUTOENCODER"),
            lambda d: d.__setitem__("d0_authorized", True),
            lambda d: d.__setitem__("d2_authorized", True),
            lambda d: d.__setitem__("outer_authorized", True),
        )
        for mutate in mutations:
            with self.subTest(attack=mutate):
                self._assert_semantic_design_mutation_rejected(mutate)
        self.assertGreaterEqual(len(mutations), 31)

    def test_feature_membership_order_and_subset_attacks_reject(self) -> None:
        def swap(d):
            features = d["feature_schema"]["ordered_features"]
            features[0], features[1] = features[1], features[0]
            d["feature_schema"]["feature_order_hash"] = d0.stable_hash_v1({"features": features})

        def delete(d):
            features = d["feature_schema"]["ordered_features"]
            features.pop()
            d["feature_schema"]["feature_count"] = len(features)
            d["feature_schema"]["feature_order_hash"] = d0.stable_hash_v1({"features": features})

        def duplicate(d):
            features = d["feature_schema"]["ordered_features"]
            features[-1] = features[0]
            d["feature_schema"]["feature_order_hash"] = d0.stable_hash_v1({"features": features})

        def relation_union_22(d):
            features = d["feature_schema"]["ordered_features"][:22]
            d["feature_schema"]["ordered_features"] = features
            d["feature_schema"]["feature_count"] = 22
            d["feature_schema"]["feature_order_hash"] = d0.stable_hash_v1({"features": features})

        def endpoint_subset_24(d):
            features = d["feature_schema"]["ordered_features"][:24]
            d["feature_schema"]["ordered_features"] = features
            d["feature_schema"]["feature_count"] = 24
            d["feature_schema"]["feature_order_hash"] = d0.stable_hash_v1({"features": features})

        def caller_feature(d):
            features = d["feature_schema"]["ordered_features"]
            features[-1] = "P1_CALLER_SELECTED"
            d["feature_schema"]["feature_order_hash"] = d0.stable_hash_v1({"features": features})

        def foreign_feature(d):
            features = d["feature_schema"]["ordered_features"]
            features[-1] = "P3_LIT01"
            d["feature_schema"]["feature_order_hash"] = d0.stable_hash_v1({"features": features})

        for mutate in (swap, delete, duplicate, relation_union_22, endpoint_subset_24, caller_feature, foreign_feature):
            with self.subTest(attack=mutate.__name__):
                self._assert_semantic_design_mutation_rejected(mutate)

    def test_d1_dependency_and_access_escalations_reject(self) -> None:
        mutations = (
            lambda d: d["independence"].__setitem__("d1_performance_used_for_design", True),
            lambda d: d["independence"].__setitem__("d1_metric_artifact_read_for_design", True),
            lambda d: d["independence"].__setitem__("d1_prediction_content_read_for_design", True),
            lambda d: d["independence"].__setitem__("frozen_d1_rule_prediction_hash", "0" * 64),
            lambda d: d["independence"].__setitem__("gdn_primary_detector", True),
            lambda d: d.__setitem__("train1_value_reads", 1),
            lambda d: d.__setitem__("train2_value_reads", 1),
            lambda d: d.__setitem__("train3_value_reads", 1),
            lambda d: d.__setitem__("train4_value_reads", 1),
            lambda d: d.__setitem__("test1_value_reads", 1),
            lambda d: d.__setitem__("label_reads", 1),
            lambda d: d.__setitem__("test2_reads", 1),
            lambda d: d.__setitem__("detector_training_executions", 1),
            lambda d: d.__setitem__("detector_inner_executions", 1),
        )
        for mutate in mutations:
            with self.subTest(attack=mutate):
                self._assert_semantic_design_mutation_rejected(mutate)

    def test_config_and_factory_forgery_reject(self) -> None:
        config = copy.deepcopy(self.config)
        config["d1_metric_artifact_read_for_design"] = True
        _rehash_config(config)
        with self.assertRaises(d0.D0DetectorDesignError):
            d0.validate_d0_config_v1(config)

        issued = d0.build_d0_detector_design_v1()
        reconstructed = d0.D0DetectorDesignV1(**issued.to_public_dict())
        with self.assertRaises(d0.D0DetectorDesignError):
            d0.validate_d0_detector_design_v1(reconstructed)
        forged = replace(issued, d0_authorized=True)
        forged = replace(forged, design_hash=d0.stable_hash_v1(d0._design_payload(forged)))
        with self.assertRaises(d0.D0DetectorDesignError):
            d0.validate_d0_detector_design_v1(forged)

    def test_public_api_has_no_caller_scientific_controls(self) -> None:
        self.assertEqual(tuple(inspect.signature(d0.build_d0_detector_design_v1).parameters), ())
        forbidden = (
            "alpha",
            "variance_target",
            "k",
            "features",
            "feature_order",
            "scaler",
            "threshold",
            "calibration_split",
            "metric",
            "episode_policy",
            "d1_metric",
            "test1",
            "test2",
            "detector_family",
            "d2",
            "outer",
        )
        for name in forbidden:
            with self.subTest(name=name), self.assertRaises(TypeError):
                d0.build_d0_detector_design_v1(**{name: object()})

    def test_public_authority_contains_no_d1_performance_or_data_io(self) -> None:
        source = Path(d0.__file__).read_text(encoding="utf-8")
        forbidden = (
            "0.9285714285714286",
            "40.50255787059723",
            "D1_METRICS_V1.json",
            "D1_RULE_PREDICTION_ARTIFACT_V1.json",
            "numpy",
            "pandas",
            "read_csv",
            "open(",
        )
        for token in forbidden:
            with self.subTest(token=token):
                self.assertNotIn(token, source)


if __name__ == "__main__":
    unittest.main()
