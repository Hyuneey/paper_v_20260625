from __future__ import annotations

from dataclasses import replace
from hashlib import sha256
import json
import unittest
from unittest.mock import patch

import numpy as np

from paperworks.validation_v2.isolation_forest_v1 import (
    DetectorEnvironmentReceiptV1, NormalMatrixInputV1,
)
from paperworks.validation_v2.pca_spe_v2 import (
    PcaSpeConfigV2, PcaSpeV2ContractError, calibrate_pca_spe_threshold_v2,
    fit_pca_spe_v2, predict_pca_spe_v2, score_pca_spe_v2,
    strict_alarm_mask_pca_spe_v2,
)
from paperworks.v6.task039e3_r2r_d0_detector_design_v1 import P1_FEATURE_ORDER


FILES = {
    "NORMAL_FIT_PRIMARY": ("hai-train1.csv", "53007b0ba604fbf338e7ac2e08cd81d874b5d1388f3aecb213ddcba5bf2bec4a"),
    "NORMAL_FIT_SECONDARY": ("hai-train2.csv", "0e520e82bf78a661ab19ce4967f3c766bd809820f457a9c90c365102d4534c56"),
    "NORMAL_CONFIRMATION_CALIBRATION": ("hai-train3.csv", "bfcec2dc05adea103e7491546b0e28268faaa26d3cc717d10f4595c94b81e85d"),
}
FEATURES = tuple(P1_FEATURE_ORDER)
COMMIT = "a" * 40
PREREG = sha256(b"v2-d0-prereg").hexdigest()


def matrix(role: str, rows: int, seed: int) -> NormalMatrixInputV1:
    rng = np.random.default_rng(seed)
    values = rng.normal(size=(rows, 37))
    values[:, 0] = 2.0  # explicit constant-dimension scale-floor coverage
    return NormalMatrixInputV1(
        file_id=FILES[role][0], file_content_sha256=FILES[role][1], split_role=role,
        feature_ids=FEATURES, values=values,
    )


class PcaSpeV2Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        provisional = DetectorEnvironmentReceiptV1(
            python_version="3.11.9",
            package_records=(("numpy", np.__version__, sha256(b"numpy-record").hexdigest()),),
            self_hash="",
        )
        cls.environment = replace(
            provisional,
            self_hash=sha256(json.dumps(
                provisional.body_document(), sort_keys=True, separators=(",", ":"),
                ensure_ascii=True,
            ).encode("utf-8")).hexdigest(),
        )
        cls.environment_patcher = patch(
            "paperworks.validation_v2.pca_spe_v2.build_detector_environment_receipt_v1",
            return_value=cls.environment,
        )
        cls.environment_patcher.start()
        cls.train1 = matrix("NORMAL_FIT_PRIMARY", 160, 1)
        cls.train2 = matrix("NORMAL_FIT_SECONDARY", 160, 2)
        cls.model = fit_pca_spe_v2(
            cls.train1, cls.train2, source_commit=COMMIT, preregistration_hash=PREREG,
            environment=cls.environment,
        )
        cls.train3 = matrix("NORMAL_CONFIRMATION_CALIBRATION", 1000, 3)
        cls.threshold = calibrate_pca_spe_threshold_v2(
            cls.model, cls.train3,
            expected_fit_receipt_hash=cls.model.fit_receipt.receipt_hash,
        )

    @classmethod
    def tearDownClass(cls) -> None:
        cls.environment_patcher.stop()

    def test_fit_is_normal_only_population_standardization_with_residual_space(self) -> None:
        receipt = self.model.fit_receipt
        self.assertEqual(tuple(item.split_role for item in receipt.ordered_inputs), (
            "NORMAL_FIT_PRIMARY", "NORMAL_FIT_SECONDARY",
        ))
        self.assertEqual(receipt.combined_fit_rows, 320)
        self.assertEqual(receipt.feature_count, 37)
        self.assertGreater(receipt.component_count, 0)
        self.assertGreater(receipt.residual_dimension_count, 0)
        self.assertEqual(self.model.scale[0], 1e-12)
        self.assertFalse(self.model.mean.flags.writeable)
        self.assertEqual(receipt.environment_hash, self.environment.self_hash)

    def test_fit_and_score_are_deterministic_for_same_environment(self) -> None:
        repeated = fit_pca_spe_v2(
            self.train1, self.train2, source_commit=COMMIT, preregistration_hash=PREREG,
            environment=self.environment,
        )
        self.assertEqual(repeated.fit_receipt.receipt_hash, self.model.fit_receipt.receipt_hash)
        first, _ = score_pca_spe_v2(
            self.model, self.train3, expected_role="NORMAL_CONFIRMATION_CALIBRATION",
            expected_fit_receipt_hash=self.model.fit_receipt.receipt_hash,
        )
        second, _ = score_pca_spe_v2(
            repeated, self.train3, expected_role="NORMAL_CONFIRMATION_CALIBRATION",
            expected_fit_receipt_hash=repeated.fit_receipt.receipt_hash,
        )
        self.assertTrue(np.array_equal(first, second))

    def test_threshold_is_nearest_rank_999_and_comparator_is_strict(self) -> None:
        self.assertEqual(self.threshold.score_count, 1000)
        self.assertEqual(self.threshold.nearest_rank, 999)
        value = float.fromhex(self.threshold.threshold_hex)
        mask = strict_alarm_mask_pca_spe_v2(np.asarray([value - 1.0, value, value + 1.0]), value)
        self.assertEqual(mask.tolist(), [False, False, True])

    def test_prediction_replays_fit_and_threshold_authorities(self) -> None:
        scores, alarms, binding = predict_pca_spe_v2(
            self.model, self.threshold, self.train3,
            expected_role="NORMAL_CONFIRMATION_CALIBRATION",
            expected_fit_receipt_hash=self.model.fit_receipt.receipt_hash,
            expected_threshold_receipt_hash=self.threshold.receipt_hash,
        )
        self.assertEqual(len(scores), 1000)
        self.assertTrue(np.array_equal(alarms, scores > float.fromhex(self.threshold.threshold_hex)))
        self.assertEqual(binding.split_role, "NORMAL_CONFIRMATION_CALIBRATION")

    def test_model_or_threshold_mutation_is_rejected(self) -> None:
        mean = self.model.mean.copy()
        mean[0] += 1.0
        forged_model = replace(self.model, mean=mean)
        with self.assertRaisesRegex(PcaSpeV2ContractError, "model authority replay mismatch"):
            score_pca_spe_v2(
                forged_model, self.train3, expected_role="NORMAL_CONFIRMATION_CALIBRATION",
                expected_fit_receipt_hash=self.model.fit_receipt.receipt_hash,
            )
        with self.assertRaisesRegex(PcaSpeV2ContractError, "threshold authority replay mismatch"):
            predict_pca_spe_v2(
                self.model, replace(self.threshold, threshold_hex=float(999.0).hex()), self.train3,
                expected_role="NORMAL_CONFIRMATION_CALIBRATION",
                expected_fit_receipt_hash=self.model.fit_receipt.receipt_hash,
                expected_threshold_receipt_hash=self.threshold.receipt_hash,
            )

    def test_config_and_split_boundaries_fail_closed(self) -> None:
        with self.assertRaises(PcaSpeV2ContractError):
            replace(PcaSpeConfigV2(), comparator="score >= threshold").validate()
        with self.assertRaises(ValueError):
            fit_pca_spe_v2(
                replace(self.train1, labels_present=True), self.train2,
                source_commit=COMMIT, preregistration_hash=PREREG, environment=self.environment,
            )
        with self.assertRaises(ValueError):
            fit_pca_spe_v2(
                replace(self.train1, split_role="DEVELOPMENT_ONLY"), self.train2,
                source_commit=COMMIT, preregistration_hash=PREREG, environment=self.environment,
            )

    def test_stale_environment_receipt_is_rejected_at_fit_and_score(self) -> None:
        stale = replace(self.environment, self_hash="0" * 64)
        with self.assertRaisesRegex(PcaSpeV2ContractError, "environment receipt is stale"):
            fit_pca_spe_v2(
                self.train1, self.train2, source_commit=COMMIT,
                preregistration_hash=PREREG, environment=stale,
            )
        forged_receipt = replace(
            self.model.fit_receipt, environment_hash="0" * 64, receipt_hash="",
        )
        forged_receipt = replace(
            forged_receipt,
            receipt_hash=sha256(
                json.dumps(
                    forged_receipt.payload(), sort_keys=True, separators=(",", ":"),
                    ensure_ascii=True,
                ).encode("utf-8")
            ).hexdigest(),
        )
        with self.assertRaisesRegex(PcaSpeV2ContractError, "model authority replay mismatch"):
            score_pca_spe_v2(
                replace(self.model, fit_receipt=forged_receipt), self.train3,
                expected_role="NORMAL_CONFIRMATION_CALIBRATION",
                expected_fit_receipt_hash=forged_receipt.receipt_hash,
            )

    def test_pilot_v1_identifiers_are_not_reused(self) -> None:
        self.assertEqual(self.model.config.detector_id, "V2_D0_PCA_SPE_NORMAL_ONLY_V1")
        self.assertNotIn("PILOT", self.model.config.detector_id)


if __name__ == "__main__":
    unittest.main()
