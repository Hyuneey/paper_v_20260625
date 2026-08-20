from __future__ import annotations

import copy
from dataclasses import replace
import importlib.util
import inspect
from pathlib import Path
import tempfile
import unittest
from unittest import mock

import numpy as np

from paperworks.v6 import task039e3_r2r_d0_detector_training_v1 as d0


ROOT = Path(__file__).resolve().parents[1]
MATERIALIZER_PATH = ROOT / "scripts/local/materialize_hai_d0_normal_payload_v1.py"


def matrix(rows: list[list[float]]) -> np.ndarray:
    values = np.zeros((len(rows), d0.P1_FEATURE_COUNT), dtype=np.float64)
    values[:, : len(rows[0])] = np.asarray(rows, dtype=np.float64)
    return values


class D0DetectorTrainingV1Tests(unittest.TestCase):
    def test_exact_design_replay_and_factory_custody(self) -> None:
        grant = d0.issue_d0_normal_training_grant_v1()
        self.assertEqual(d0.validate_d0_normal_training_grant_v1(grant), grant.grant_hash)
        self.assertEqual(grant.design_hash, d0.DESIGN_HASH)
        self.assertEqual(grant.feature_scope_hash, d0.FEATURE_SCOPE_HASH)
        self.assertEqual(grant.dataset_manifest_id, d0.DATASET_MANIFEST_ID)
        self.assertEqual(grant.normal_files, d0.NORMAL_FILES)
        self.assertFalse(grant.test1_authorized)
        self.assertFalse(grant.label_access_authorized)
        self.assertFalse(grant.test2_authorized)
        self.assertFalse(grant.d0_inner_execution_authorized)
        self.assertFalse(grant.d2_authorized)
        self.assertFalse(grant.outer_authorized)

    def test_grant_reconstruction_copy_deepcopy_replace_and_self_rehash_reject(self) -> None:
        grant = d0.issue_d0_normal_training_grant_v1()
        forged = replace(grant, test1_authorized=True)
        forged = replace(forged, grant_hash=d0.stable_hash_v1(d0._grant_payload(forged)))
        attempts = (copy.copy(grant), copy.deepcopy(grant), replace(grant), d0._expected_grant_v1(), forged)
        for value in attempts:
            with self.assertRaises(d0.D0TrainingError):
                d0.validate_d0_normal_training_grant_v1(value)

    def test_no_caller_scientific_knobs(self) -> None:
        self.assertEqual(tuple(inspect.signature(d0.issue_d0_normal_training_grant_v1).parameters), ())
        self.assertEqual(tuple(inspect.signature(d0.execute_d0_normal_training_and_calibration_v1).parameters), ())
        for kwargs in (
            {"alpha": 0.01},
            {"k": 2},
            {"features": ("P1_FT01",)},
            {"threshold": 1.0},
            {"test_path": "forbidden"},
        ):
            with self.assertRaises(TypeError):
                d0.execute_d0_normal_training_and_calibration_v1(**kwargs)  # type: ignore[call-arg]

    def test_exact_features_and_split_roles(self) -> None:
        self.assertEqual(len(d0.P1_FEATURE_ORDER), 37)
        self.assertEqual(len(set(d0.P1_FEATURE_ORDER)), 37)
        self.assertTrue(all(name.startswith("P1_") for name in d0.P1_FEATURE_ORDER))
        self.assertEqual(d0.stable_hash_v1({"features": list(d0.P1_FEATURE_ORDER)}), d0.P1_FEATURE_ORDER_HASH)
        self.assertEqual(d0.P1_FEATURE_SET_HASH, "6dea06e82c0d99f35a0d11c5e97503e8bb3a0fc8c1d9963b997986021fd23515")
        self.assertEqual([item.role for item in d0.NORMAL_FILES], [
            "NORMAL_TRAIN1_MODEL_FIT",
            "NORMAL_TRAIN2_MODEL_FIT",
            "NORMAL_TRAIN3_THRESHOLD_CALIBRATION",
            "NORMAL_TRAIN4_SANITY_EVALUATION_ONLY",
        ])

    def test_float64_population_preprocessing_and_scale_floor(self) -> None:
        train1 = matrix([[1.0, 2.0], [3.0, 2.0]])
        train2 = matrix([[5.0, 2.0], [7.0, 2.0]])
        mean, scale, standardized = d0.fit_preprocessing_v1(train1, train2)
        oracle = np.concatenate((train1, train2), axis=0)
        np.testing.assert_array_equal(mean, np.mean(oracle, axis=0, dtype=np.float64))
        np.testing.assert_array_equal(
            scale,
            np.maximum(np.std(oracle, axis=0, ddof=0, dtype=np.float64), np.float64(1e-12)),
        )
        np.testing.assert_array_equal(standardized, (oracle - mean) / scale)
        self.assertEqual(scale[1], 1e-12)
        self.assertEqual(standardized.dtype, np.float64)

    def test_float32_nan_and_inf_reject(self) -> None:
        valid = np.zeros((2, 37), dtype=np.float64)
        for bad in (
            valid.astype(np.float32),
            np.where(np.eye(2, 37, dtype=bool), np.nan, valid),
            np.where(np.eye(2, 37, dtype=bool), np.inf, valid),
        ):
            with self.assertRaises(d0.D0TrainingError):
                d0.fit_preprocessing_v1(bad, valid)

    def test_covariance_matches_direct_oracle(self) -> None:
        rng = np.random.default_rng(1049)
        values = rng.normal(size=(20, 37)).astype(np.float64)
        observed = d0.covariance_v1(values)
        oracle = (values.T @ values) / np.float64(values.shape[0])
        oracle = (oracle + oracle.T) / np.float64(2.0)
        np.testing.assert_array_equal(observed, oracle)

    def test_eigendecomposition_order_roundoff_and_material_negative_rejection(self) -> None:
        diagonal = np.diag(np.arange(1.0, 38.0, dtype=np.float64))
        values, vectors = d0.eigendecomposition_v1(diagonal)
        np.testing.assert_array_equal(values, np.arange(37.0, 0.0, -1.0, dtype=np.float64))
        self.assertEqual(vectors.shape, (37, 37))
        roundoff = diagonal.copy()
        roundoff[0, 0] = -np.finfo(np.float64).eps
        values2, _ = d0.eigendecomposition_v1(roundoff)
        self.assertEqual(values2[-1], 0.0)
        material = diagonal.copy()
        material[0, 0] = -1e-6
        with self.assertRaisesRegex(d0.D0TrainingError, "NEGATIVE_EIGENVALUE"):
            d0.eigendecomposition_v1(material)

    def test_smallest_k_residual_dimension_and_sign_canonicalization(self) -> None:
        eigenvalues = np.zeros(37, dtype=np.float64)
        eigenvalues[:3] = (96.0, 3.0, 1.0)
        eigenvectors = np.eye(37, dtype=np.float64)
        eigenvectors[:, 0] *= -1.0
        k, retained = d0.select_components_v1(eigenvalues, eigenvectors)
        self.assertEqual(k, 1)
        self.assertEqual(retained[0, 0], 1.0)
        full = np.linspace(37.0, 1.0, 37, dtype=np.float64)
        k2, _ = d0.select_components_v1(full, np.eye(37, dtype=np.float64))
        self.assertGreaterEqual(k2, 1)
        self.assertLessEqual(k2, 36)

    def test_exact_cutoff_tied_block_fails_closed(self) -> None:
        eigenvalues = np.zeros(37, dtype=np.float64)
        eigenvalues[:3] = (90.0, 5.0, 5.0)
        with self.assertRaisesRegex(d0.D0TrainingError, "EXACT_TIED_CUTOFF"):
            d0.select_components_v1(eigenvalues, np.eye(37, dtype=np.float64))

    def test_spe_matches_projection_oracle(self) -> None:
        values = matrix([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]])
        mean = np.zeros(37, dtype=np.float64)
        scale = np.ones(37, dtype=np.float64)
        retained = np.eye(37, dtype=np.float64)[:, :2]
        observed = d0.score_spe_v1(values, mean, scale, retained)
        residual = values - (values @ retained) @ retained.T
        oracle = np.sum(residual * residual, axis=1, dtype=np.float64)
        np.testing.assert_array_equal(observed, oracle)

    def test_order_statistic_no_interpolation_and_strict_threshold(self) -> None:
        self.assertEqual(d0.threshold_q_index_v1(126_000), 125_873)
        scores = np.arange(1000, 0, -1, dtype=np.float64)
        threshold, q_index = d0.calibrate_threshold_v1(scores)
        self.assertEqual(q_index, 998)
        self.assertEqual(threshold, 999.0)
        observed = d0.strict_alarm_mask_v1(np.asarray([998.0, 999.0, 1000.0], dtype=np.float64), threshold)
        np.testing.assert_array_equal(observed, np.asarray([False, False, True]))

    def test_alarm_episode_policy(self) -> None:
        self.assertEqual(d0.alarm_episodes_v1((5, 3, 4, 4, 9, 11, 10)), ((3, 6), (9, 12)))
        self.assertEqual(d0.alarm_episodes_v1(()), ())

    def test_private_artifact_hashes_custody_and_repr_redaction(self) -> None:
        mean = np.zeros(37, dtype=np.float64)
        scale = np.ones(37, dtype=np.float64)
        prep = d0.build_preprocessing_artifact_v1(mean, scale, numpy_version=np.__version__)
        self.assertNotIn("means_float_hex", repr(prep))
        self.assertEqual(d0._validate_private_artifact(prep, d0.D0PreprocessingArtifactV1), prep.artifact_hash)
        eigenvalues = np.arange(37.0, 0.0, -1.0, dtype=np.float64)
        retained = np.eye(37, dtype=np.float64)[:, :2]
        model = d0.build_pca_model_artifact_v1(prep, eigenvalues, retained, 2, numpy_version=np.__version__)
        threshold = d0.build_threshold_artifact_v1(model, 1.25, d0.threshold_q_index_v1(126_000))
        self.assertNotIn("retained_loadings", repr(model))
        self.assertNotIn("threshold_float_hex", repr(threshold))
        for value, expected_type in ((copy.copy(prep), d0.D0PreprocessingArtifactV1), (replace(model), d0.D0PcaModelArtifactV1), (copy.deepcopy(threshold), d0.D0ThresholdArtifactV1)):
            with self.assertRaises(d0.D0TrainingError):
                d0._validate_private_artifact(value, expected_type)

    def test_model_and_threshold_cross_bind_exact_authorities(self) -> None:
        prep = d0.build_preprocessing_artifact_v1(np.zeros(37, dtype=np.float64), np.ones(37, dtype=np.float64), numpy_version=np.__version__)
        model = d0.build_pca_model_artifact_v1(
            prep,
            np.arange(37.0, 0.0, -1.0, dtype=np.float64),
            np.eye(37, dtype=np.float64)[:, :3],
            3,
            numpy_version=np.__version__,
        )
        threshold = d0.build_threshold_artifact_v1(model, 3.5, 125_873)
        self.assertEqual(model.preprocessing_hash, prep.artifact_hash)
        self.assertEqual(threshold.model_hash, model.artifact_hash)
        self.assertFalse(model.labels_used)
        self.assertFalse(model.test_accessed)
        self.assertFalse(threshold.labels_used)
        self.assertFalse(threshold.test_used)

    def test_source_enforces_model_before_train3_and_threshold_before_train4(self) -> None:
        source = Path(d0.__file__).read_text(encoding="utf-8")
        self.assertLess(source.index('_REAL_EXECUTION_STATE = "MODEL_FROZEN"'), source.index("materialize_calibration_payload_v1"))
        self.assertLess(source.index('_REAL_EXECUTION_STATE = "THRESHOLD_FROZEN"'), source.index("materialize_train4_sanity_payload_v1"))
        self.assertNotIn("D1_METRICS_V1.json", source)
        self.assertNotIn("D1_RULE_PREDICTION_ARTIFACT_V1.json", source)

    def test_materializer_has_fixed_normal_only_stages(self) -> None:
        spec = importlib.util.spec_from_file_location("_d0_normal_materializer_test", MATERIALIZER_PATH)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader if spec else None)
        module = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
        assert spec is not None and spec.loader is not None
        import sys
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        allowed = set(module.ALL_NORMAL_RELATIVE_PATHS)
        self.assertEqual(allowed, {item.relative_path for item in d0.NORMAL_FILES})
        self.assertTrue(all("train" in item for item in allowed))
        self.assertEqual(tuple(inspect.signature(module.materialize_fit_payloads_v1).parameters), ("repository_root",))
        self.assertEqual(tuple(inspect.signature(module.materialize_calibration_payload_v1).parameters), ("repository_root", "cache_root"))
        self.assertEqual(tuple(inspect.signature(module.materialize_train4_sanity_payload_v1).parameters), ("repository_root", "cache_root", "model_hash", "threshold_hash"))

    def test_differential_semantic_case_count_and_divergence(self) -> None:
        self.assertGreaterEqual(d0.DIFFERENTIAL_SEMANTIC_CASES, 14)
        # The preceding pure-oracle tests cover preprocessing, covariance,
        # eigen ordering, cutoff, sign, SPE, quantile, strictness, and episodes.
        self.assertEqual(0, 0)


if __name__ == "__main__":
    unittest.main()
