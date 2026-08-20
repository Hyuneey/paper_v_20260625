from __future__ import annotations

import importlib.util
import inspect
from pathlib import Path
import unittest

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "d0_integrity_audit_v1",
    ROOT / "scripts/audit_task039e3_r2r_d0_model_threshold_integrity_v1.py",
)
assert SPEC is not None and SPEC.loader is not None
AUDIT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AUDIT)


class D0ModelThresholdIntegrityAuditTests(unittest.TestCase):
    def test_public_freeze_audit_passes(self) -> None:
        result = AUDIT.run_public_audit_v1()
        self.assertTrue(result["frozen_result_commit_verified"])
        self.assertEqual(result["post_freeze_mutation_count"], 0)
        self.assertTrue(result["training_implementation_hash_match"])

    def test_oracle_never_imports_authoritative_training_module(self) -> None:
        source = inspect.getsource(AUDIT)
        self.assertNotIn("import task039e3_r2r_d0_detector_training_v1", source)
        self.assertNotIn("from paperworks.v6.task039e3_r2r_d0_detector_training_v1", source)

    def test_preprocessing_is_population_float64_with_floor(self) -> None:
        first = np.zeros((3, AUDIT.FEATURE_COUNT), dtype=np.float64)
        second = np.ones((2, AUDIT.FEATURE_COUNT), dtype=np.float64)
        first[:, 0] = np.array([1.0, 2.0, 3.0])
        second[:, 0] = np.array([4.0, 5.0])
        mean, scale, standardized = AUDIT.independent_preprocessing_oracle_v1(first, second)
        combined = np.concatenate((first, second), axis=0)
        np.testing.assert_array_equal(mean, np.mean(combined, axis=0, dtype=np.float64))
        np.testing.assert_array_equal(scale, np.maximum(np.std(combined, axis=0, ddof=0), 1e-12))
        self.assertEqual(standardized.dtype, np.float64)
        self.assertEqual(standardized.shape, (5, AUDIT.FEATURE_COUNT))

    def test_nonfinite_and_float32_are_rejected(self) -> None:
        valid = np.zeros((2, AUDIT.FEATURE_COUNT), dtype=np.float64)
        for invalid in (
            valid.astype(np.float32),
            np.where(np.arange(valid.size).reshape(valid.shape) == 0, np.nan, valid),
            np.where(np.arange(valid.size).reshape(valid.shape) == 0, np.inf, valid),
        ):
            with self.subTest(dtype=str(invalid.dtype), finite=bool(np.isfinite(invalid).all())):
                with self.assertRaises(AUDIT.D0IntegrityAuditError):
                    AUDIT.independent_preprocessing_oracle_v1(invalid, valid)

    def test_pca_oracle_is_deterministic_and_canonical(self) -> None:
        generator = np.random.default_rng(3903)
        standardized = generator.normal(size=(300, AUDIT.FEATURE_COUNT)).astype(np.float64)
        values, retained, k, tied = AUDIT.independent_pca_oracle_v1(standardized)
        self.assertTrue(np.all(values[:-1] >= values[1:]))
        self.assertFalse(tied)
        self.assertGreaterEqual(k, 1)
        self.assertLess(k, AUDIT.FEATURE_COUNT)
        for column in range(k):
            anchor = int(np.argmax(np.abs(retained[:, column])))
            self.assertGreaterEqual(retained[anchor, column], 0.0)

    def test_exact_tied_cutoff_fails_closed(self) -> None:
        standardized = np.eye(AUDIT.FEATURE_COUNT, dtype=np.float64)
        with self.assertRaises(AUDIT.D0IntegrityAuditError):
            AUDIT.independent_pca_oracle_v1(standardized)

    def test_spe_matches_projection_oracle(self) -> None:
        generator = np.random.default_rng(1)
        values = generator.normal(size=(7, AUDIT.FEATURE_COUNT)).astype(np.float64)
        mean = np.zeros(AUDIT.FEATURE_COUNT, dtype=np.float64)
        scale = np.ones(AUDIT.FEATURE_COUNT, dtype=np.float64)
        retained = np.eye(AUDIT.FEATURE_COUNT, dtype=np.float64)[:, :3]
        observed = AUDIT.independent_spe_oracle_v1(values, mean, scale, retained)
        expected = np.sum(values[:, 3:] ** 2, axis=1, dtype=np.float64)
        np.testing.assert_allclose(observed, expected, rtol=0.0, atol=1e-14)

    def test_threshold_order_statistic_has_no_interpolation(self) -> None:
        scores = np.arange(1, 126001, dtype=np.float64)[::-1].copy()
        threshold, q_index = AUDIT.independent_threshold_oracle_v1(scores)
        self.assertEqual(q_index, AUDIT.EXPECTED_Q_INDEX)
        self.assertEqual(threshold, float(q_index + 1))
        self.assertFalse(threshold > threshold)
        self.assertTrue(np.nextafter(threshold, np.inf) > threshold)

    def test_alarm_episode_oracle_deduplicates_sorts_and_merges(self) -> None:
        self.assertEqual(
            AUDIT.independent_alarm_episodes_v1((8, 2, 3, 3, 7, 11)),
            ((2, 4), (7, 9), (11, 12)),
        )

    def test_public_artifact_semantics_accept_only_frozen_result(self) -> None:
        documents = AUDIT._load_public_reports()
        AUDIT._validate_public_cross_hashes(documents)
        AUDIT.validate_frozen_public_semantics_v1(documents)

    def test_private_oracle_has_no_caller_scientific_knobs(self) -> None:
        self.assertEqual(tuple(inspect.signature(AUDIT.run_private_oracle_v1).parameters), ())
        self.assertEqual(tuple(inspect.signature(AUDIT.run_public_audit_v1).parameters), ())

    def test_frozen_scope_contains_exact_37_unique_p1_features(self) -> None:
        self.assertEqual(len(AUDIT.P1_FEATURE_ORDER), 37)
        self.assertEqual(len(set(AUDIT.P1_FEATURE_ORDER)), 37)
        self.assertTrue(all(name.startswith("P1_") for name in AUDIT.P1_FEATURE_ORDER))


if __name__ == "__main__":
    unittest.main()
