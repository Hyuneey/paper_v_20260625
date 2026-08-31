from __future__ import annotations

from dataclasses import replace
import unittest

import numpy as np

from paperworks.validation_v2.isolation_forest_v1 import (
    IsolationForestConfigV1,
    IsolationForestContractError,
    NormalMatrixInputV1,
    build_detector_environment_receipt_v1,
    calibrate_isolation_forest_threshold_v1,
    fit_isolation_forest_v1,
    predict_isolation_forest_v1,
)
from paperworks.v6.task039e3_r2r_d0_detector_design_v1 import P1_FEATURE_ORDER


H = "a" * 64
SOURCE = "a" * 40
FEATURES = tuple(P1_FEATURE_ORDER)
FILES = {
    "NORMAL_FIT_PRIMARY": ("hai-train1.csv", "53007b0ba604fbf338e7ac2e08cd81d874b5d1388f3aecb213ddcba5bf2bec4a"),
    "NORMAL_FIT_SECONDARY": ("hai-train2.csv", "0e520e82bf78a661ab19ce4967f3c766bd809820f457a9c90c365102d4534c56"),
    "NORMAL_CONFIRMATION_CALIBRATION": ("hai-train3.csv", "bfcec2dc05adea103e7491546b0e28268faaa26d3cc717d10f4595c94b81e85d"),
}


def matrix_input(role: str, rows: int, seed: int, *, file_id: str | None = None) -> NormalMatrixInputV1:
    rng = np.random.default_rng(seed)
    return NormalMatrixInputV1(
        file_id=file_id or FILES[role][0],
        file_content_sha256=FILES[role][1],
        split_role=role,
        feature_ids=FEATURES,
        values=rng.normal(size=(rows, 37)),
    )


class IsolationForestV2Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        try:
            cls.environment = build_detector_environment_receipt_v1()
        except (IsolationForestContractError, ModuleNotFoundError) as exc:
            raise unittest.SkipTest(f"optional exact V2 detector environment unavailable: {exc}") from exc
        cls.train1 = matrix_input("NORMAL_FIT_PRIMARY", 128, 1)
        cls.train2 = matrix_input("NORMAL_FIT_SECONDARY", 128, 2)
        cls.model = fit_isolation_forest_v1(
            cls.train1,
            cls.train2,
            source_commit=SOURCE,
            preregistration_hash=H,
            environment=cls.environment,
        )
        cls.train3 = matrix_input("NORMAL_CONFIRMATION_CALIBRATION", 1000, 3)
        cls.threshold = calibrate_isolation_forest_threshold_v1(
            cls.model,
            cls.train3,
            expected_fit_receipt_hash=cls.model.fit_receipt.self_hash,
        )

    def test_environment_closure_and_fixed_config(self) -> None:
        self.assertEqual({item[0]: item[1] for item in self.environment.package_records}["scikit-learn"], "1.9.0")
        self.assertEqual(self.model.fit_receipt.effective_max_samples, 256)
        with self.assertRaises(IsolationForestContractError):
            replace(IsolationForestConfigV1(), n_estimators=100).validate()
        for config in (
            replace(IsolationForestConfigV1(), max_samples=256.0),
            replace(IsolationForestConfigV1(), bootstrap=0),
            replace(IsolationForestConfigV1(), random_state=False),
            replace(IsolationForestConfigV1(), max_features=1),
        ):
            with self.assertRaises(IsolationForestContractError):
                config.validate()

    def test_fit_receipt_binds_stable_file_order_and_combined_rows(self) -> None:
        receipt = self.model.fit_receipt
        self.assertEqual(tuple(item.split_role for item in receipt.ordered_inputs), (
            "NORMAL_FIT_PRIMARY", "NORMAL_FIT_SECONDARY"
        ))
        self.assertEqual(receipt.combined_fit_rows, 256)
        self.assertEqual(receipt.feature_ids, FEATURES)

    def test_fit_fails_closed_below_256_rows(self) -> None:
        with self.assertRaisesRegex(IsolationForestContractError, "fewer than 256"):
            fit_isolation_forest_v1(
                matrix_input("NORMAL_FIT_PRIMARY", 100, 1),
                matrix_input("NORMAL_FIT_SECONDARY", 100, 2),
                source_commit=SOURCE,
                preregistration_hash=H,
                environment=self.environment,
            )

    def test_fit_rejects_wrong_role_and_prohibited_fields(self) -> None:
        with self.assertRaises(IsolationForestContractError):
            fit_isolation_forest_v1(
                replace(self.train1, split_role="DEVELOPMENT_ONLY"), self.train2,
                source_commit=SOURCE, preregistration_hash=H, environment=self.environment,
            )
        with self.assertRaises(IsolationForestContractError):
            fit_isolation_forest_v1(
                replace(self.train1, file_id="hai-test2.csv"), self.train2,
                source_commit=SOURCE, preregistration_hash=H, environment=self.environment,
            )
        with self.assertRaises(IsolationForestContractError):
            fit_isolation_forest_v1(
                replace(self.train1, labels_present=True), self.train2,
                source_commit=SOURCE, preregistration_hash=H, environment=self.environment,
            )

    def test_fit_rejects_wrong_feature_order_and_nonfinite(self) -> None:
        with self.assertRaises(IsolationForestContractError):
            fit_isolation_forest_v1(
                self.train1, replace(self.train2, feature_ids=tuple(reversed(FEATURES))),
                source_commit=SOURCE, preregistration_hash=H, environment=self.environment,
            )
        bad = np.asarray(self.train1.values).copy()
        bad[0, 0] = np.nan
        with self.assertRaises(IsolationForestContractError):
            fit_isolation_forest_v1(
                replace(self.train1, values=bad), self.train2,
                source_commit=SOURCE, preregistration_hash=H, environment=self.environment,
            )

    def test_repeated_fit_is_deterministic(self) -> None:
        repeat = fit_isolation_forest_v1(
            self.train1, self.train2, source_commit=SOURCE,
            preregistration_hash=H, environment=self.environment,
        )
        self.assertEqual(repeat.fit_receipt.model_state_sha256, self.model.fit_receipt.model_state_sha256)
        self.assertEqual(repeat.fit_receipt.self_hash, self.model.fit_receipt.self_hash)

    def test_calibration_is_nearest_rank_999(self) -> None:
        self.assertEqual(self.threshold.score_count, 1000)
        self.assertEqual(self.threshold.nearest_rank, 999)
        self.assertEqual(self.threshold.quantile, "0.999")

    def test_prediction_uses_strict_greater_than(self) -> None:
        scores, alarms, binding = predict_isolation_forest_v1(
            self.model, self.threshold, self.train3,
            expected_role="NORMAL_CONFIRMATION_CALIBRATION",
            expected_fit_receipt_hash=self.model.fit_receipt.self_hash,
            expected_threshold_receipt_hash=self.threshold.self_hash,
        )
        self.assertTrue(np.array_equal(alarms, scores > self.threshold.threshold))
        self.assertFalse(bool((scores == self.threshold.threshold)[alarms].any()))
        self.assertEqual(binding.row_count, 1000)

    def test_threshold_rejects_other_model_and_mutation(self) -> None:
        with self.assertRaises(IsolationForestContractError):
            predict_isolation_forest_v1(
                self.model,
                replace(self.threshold, fit_receipt_hash="b" * 64),
                self.train3,
                expected_role="NORMAL_CONFIRMATION_CALIBRATION",
                expected_fit_receipt_hash=self.model.fit_receipt.self_hash,
                expected_threshold_receipt_hash=self.threshold.self_hash,
            )
        forged = replace(self.threshold, comparator="score >= threshold", self_hash="")
        from paperworks.validation_v2.isolation_forest_v1 import _document_hash
        forged = replace(forged, self_hash=_document_hash(forged.body_document()))
        with self.assertRaises(IsolationForestContractError):
            predict_isolation_forest_v1(
                self.model, forged, self.train3,
                expected_role="NORMAL_CONFIRMATION_CALIBRATION",
                expected_fit_receipt_hash=self.model.fit_receipt.self_hash,
                expected_threshold_receipt_hash=self.threshold.self_hash,
            )

    def test_live_model_and_config_mutations_are_rejected(self) -> None:
        self.model.estimator.offset_ += 1.0
        try:
            with self.assertRaises(IsolationForestContractError):
                predict_isolation_forest_v1(
                    self.model, self.threshold, self.train3,
                    expected_role="NORMAL_CONFIRMATION_CALIBRATION",
                    expected_fit_receipt_hash=self.model.fit_receipt.self_hash,
                    expected_threshold_receipt_hash=self.threshold.self_hash,
                )
        finally:
            self.model.estimator.offset_ -= 1.0
        forged_model = replace(self.model, config=replace(self.model.config, n_estimators=1))
        with self.assertRaises(IsolationForestContractError):
            predict_isolation_forest_v1(
                forged_model, self.threshold, self.train3,
                expected_role="NORMAL_CONFIRMATION_CALIBRATION",
                expected_fit_receipt_hash=self.model.fit_receipt.self_hash,
                expected_threshold_receipt_hash=self.threshold.self_hash,
            )

    def test_all_serialized_scoring_state_is_bound(self) -> None:
        original_max_features = self.model.estimator._max_features
        original_features = [item.copy() for item in self.model.estimator.estimators_features_]
        self.model.estimator._max_features = 36
        self.model.estimator.estimators_features_ = [item[::-1].copy() for item in original_features]
        try:
            with self.assertRaises(IsolationForestContractError):
                predict_isolation_forest_v1(
                    self.model, self.threshold, self.train3,
                    expected_role="NORMAL_CONFIRMATION_CALIBRATION",
                    expected_fit_receipt_hash=self.model.fit_receipt.self_hash,
                    expected_threshold_receipt_hash=self.threshold.self_hash,
                )
        finally:
            self.model.estimator._max_features = original_max_features
            self.model.estimator.estimators_features_ = original_features

    def test_external_authority_rejects_coordinated_rehash(self) -> None:
        from paperworks.validation_v2.isolation_forest_v1 import _document_hash

        forged_fit = replace(self.model.fit_receipt, source_commit="b" * 40, self_hash="")
        forged_fit = replace(forged_fit, self_hash=_document_hash(forged_fit.body_document()))
        forged_model = replace(self.model, fit_receipt=forged_fit)
        forged_threshold = replace(self.threshold, fit_receipt_hash=forged_fit.self_hash, self_hash="")
        forged_threshold = replace(
            forged_threshold, self_hash=_document_hash(forged_threshold.body_document())
        )
        with self.assertRaises(IsolationForestContractError):
            predict_isolation_forest_v1(
                forged_model, forged_threshold, self.train3,
                expected_role="NORMAL_CONFIRMATION_CALIBRATION",
                expected_fit_receipt_hash=self.model.fit_receipt.self_hash,
                expected_threshold_receipt_hash=forged_threshold.self_hash,
            )

    def test_external_authority_rejects_rehashed_threshold_value(self) -> None:
        from paperworks.validation_v2.isolation_forest_v1 import _document_hash

        forged = replace(self.threshold, threshold=self.threshold.threshold + 100.0, self_hash="")
        forged = replace(forged, self_hash=_document_hash(forged.body_document()))
        with self.assertRaises(IsolationForestContractError):
            predict_isolation_forest_v1(
                self.model, forged, self.train3,
                expected_role="NORMAL_CONFIRMATION_CALIBRATION",
                expected_fit_receipt_hash=self.model.fit_receipt.self_hash,
                expected_threshold_receipt_hash=self.threshold.self_hash,
            )

    def test_environment_identity_mutation_is_rejected(self) -> None:
        forged = replace(self.environment, python_version="0.0.0", self_hash="")
        from paperworks.validation_v2.isolation_forest_v1 import _document_hash
        forged = replace(forged, self_hash=_document_hash(forged.body_document()))
        with self.assertRaises(IsolationForestContractError):
            fit_isolation_forest_v1(
                self.train1, self.train2, source_commit=SOURCE,
                preregistration_hash=H, environment=forged,
            )
        with self.assertRaises(IsolationForestContractError):
            predict_isolation_forest_v1(
                self.model,
                replace(self.threshold, threshold=self.threshold.threshold + 1.0),
                self.train3,
                expected_role="NORMAL_CONFIRMATION_CALIBRATION",
                expected_fit_receipt_hash=self.model.fit_receipt.self_hash,
                expected_threshold_receipt_hash=self.threshold.self_hash,
            )

    def test_scoring_rejects_wrong_feature_contract(self) -> None:
        with self.assertRaises(IsolationForestContractError):
            predict_isolation_forest_v1(
                self.model, self.threshold,
                replace(self.train3, feature_ids=tuple(reversed(FEATURES))),
                expected_role="NORMAL_CONFIRMATION_CALIBRATION",
                expected_fit_receipt_hash=self.model.fit_receipt.self_hash,
                expected_threshold_receipt_hash=self.threshold.self_hash,
            )

    def test_fit_rejects_unapproved_feature_names_even_when_unique(self) -> None:
        invented = tuple(f"P1_F{index:02d}" for index in range(37))
        with self.assertRaisesRegex(IsolationForestContractError, "approved ordered P1 authority"):
            fit_isolation_forest_v1(
                replace(self.train1, feature_ids=invented), self.train2,
                source_commit=SOURCE, preregistration_hash=H, environment=self.environment,
            )

    def test_fit_requires_git_commit_not_sha256(self) -> None:
        with self.assertRaisesRegex(IsolationForestContractError, "40-character Git commit"):
            fit_isolation_forest_v1(
                self.train1, self.train2, source_commit=H,
                preregistration_hash=H, environment=self.environment,
            )


if __name__ == "__main__":
    unittest.main()
