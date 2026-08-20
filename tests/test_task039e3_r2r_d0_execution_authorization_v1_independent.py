from __future__ import annotations

from dataclasses import replace
import inspect
from pathlib import Path
import unittest
from unittest import mock

from paperworks.v6.common import stable_hash_v1
from paperworks.v6 import task039e3_r2r_d0_execution_authorization_v1 as auth


class IndependentD0ExecutionAuthorizationAudit(unittest.TestCase):
    """Independent semantic attacks against the frozen Commit-A contract."""

    def setUp(self) -> None:
        self.receipt = auth.build_synthetic_d0_inner_execution_custody_preflight_receipt_v1()
        self.authorization = auth.issue_d0_inner_execution_authorization_v1(self.receipt)

    def test_01_receipt_semantic_mutation_matrix_all_rejected(self) -> None:
        mutations = (
            {"authorization_version": "wrong"},
            {"authorization_scope": "wrong"},
            {"custody_mode": auth.REAL_CUSTODY_PREFLIGHT},
            {"public_authority_set_hash": "0" * 64},
            {"detector_id": "substituted"},
            {"design_hash": "0" * 64},
            {"feature_count": 36},
            {"feature_set_hash": "0" * 64},
            {"feature_order_hash": "0" * 64},
            {"preprocessing_expected_hash": "0" * 64},
            {"preprocessing_observed_match": False},
            {"model_expected_hash": "0" * 64},
            {"model_observed_match": False},
            {"threshold_expected_hash": "0" * 64},
            {"threshold_observed_match": False},
            {"training_receipt_hash": "0" * 64},
            {"integrity_receipt_hash": "0" * 64},
            {"dataset_manifest_id": "0" * 64},
            {"test1_feature_expected_hash": "0" * 64},
            {"test1_label_expected_hash": "0" * 64},
            {"numpy_version": "2.3.4"},
            {"python_runtime_identity": "alternate"},
            {"test2_touched": True},
            {"scientific_feature_parsing_performed": True},
            {"scientific_label_parsing_performed": True},
            {"detector_execution_count": 1},
            {"metric_computation_count": 1},
            {"private_paths_exposed": 1},
            {"private_model_values_exposed": 1},
            {"private_threshold_values_exposed": 1},
        )
        accepted = 0
        for values in mutations:
            candidate = replace(self.receipt, **values)
            try:
                auth.validate_d0_inner_execution_custody_preflight_receipt_v1(candidate)
            except auth.D0ExecutionAuthorizationV1Error:
                continue
            accepted += 1
        self.assertEqual(len(mutations), 30)
        self.assertEqual(accepted, 0)

    def test_02_authorization_escalation_and_substitution_matrix_all_rejected(self) -> None:
        mutations = (
            {"authorization_scope": "D0_D2_OUTER"},
            {"training_receipt_hash": "0" * 64},
            {"integrity_receipt_hash": "0" * 64},
            {"preprocessing_content_hash": "0" * 64},
            {"model_content_hash": "0" * 64},
            {"threshold_content_hash": "0" * 64},
            {"selected_k": 11},
            {"residual_dimensions": 26},
            {"threshold_alpha": 0.01},
            {"threshold_q_index": 125_874},
            {"threshold_comparison_operator": "score >= threshold"},
            {"numpy_version": "alternate"},
            {"test1_feature_sha256": "0" * 64},
            {"test1_label_sha256": "0" * 64},
            {"alarm_episode_policy": "point_adjusted"},
            {"attack_event_recall_formula": "alternate"},
            {"normal_far_formula": "alternate"},
            {"future_prediction_artifact_label_blind": False},
            {"future_prediction_label_fields_authorized": True},
            {"future_prediction_d1_fields_authorized": True},
            {"future_prediction_metric_fields_authorized": True},
            {"label_access_before_prediction_freeze_authorized": True},
            {"d1_execution_authorized": True},
            {"d1_rerun_authorized": True},
            {"d2_authorized": True},
            {"fusion_authorized": True},
            {"outer_authorized": True},
            {"test2_authorized": True},
            {"retraining_authorized": True},
            {"recalibration_authorized": True},
            {"threshold_change_authorized": True},
            {"feature_change_authorized": True},
            {"model_change_authorized": True},
            {"d0_executed": True},
        )
        accepted = 0
        for values in mutations:
            candidate = replace(self.authorization, **values)
            try:
                auth.validate_d0_inner_execution_authorization_v1(candidate, self.receipt)
            except auth.D0ExecutionAuthorizationV1Error:
                continue
            accepted += 1
        self.assertGreaterEqual(len(mutations), 34)
        self.assertEqual(accepted, 0)

    def test_03_rehash_reconstruction_and_receipt_swap_reject(self) -> None:
        wrong = replace(self.authorization, d2_authorized=True, authorization_hash="")
        wrong = replace(wrong, authorization_hash=stable_hash_v1(wrong._payload()))
        with self.assertRaises(auth.D0ExecutionAuthorizationV1Error):
            auth.validate_d0_inner_execution_authorization_v1(wrong, self.receipt)

        second_receipt = auth.build_synthetic_d0_inner_execution_custody_preflight_receipt_v1()
        with self.assertRaises(auth.D0ExecutionAuthorizationV1Error):
            auth.validate_d0_inner_execution_authorization_v1(self.authorization, second_receipt)

        with self.assertRaises(auth.D0ExecutionAuthorizationV1Error):
            auth.validate_d0_inner_execution_authorization_v1(
                type(self.authorization)(**self.authorization.__dict__), self.receipt
            )

    def test_04_require_real_rejects_synthetic_objects(self) -> None:
        with self.assertRaises(auth.D0ExecutionAuthorizationV1Error):
            auth.validate_d0_inner_execution_custody_preflight_receipt_v1(self.receipt, require_real=True)
        with self.assertRaises(auth.D0ExecutionAuthorizationV1Error):
            auth.validate_d0_inner_execution_authorization_v1(self.authorization, self.receipt, require_real=True)

    def test_05_caller_paths_and_scientific_knobs_fail_before_io(self) -> None:
        knobs = {
            "repo_root": ".", "preprocessing_path": ".", "model_path": ".",
            "threshold_path": ".", "test1_path": ".", "label_path": ".",
            "feature_order": (), "selected_k": 9, "alpha": 0.01,
            "threshold": 0.0, "comparator": ">=", "test2": True,
            "d1": True, "d2": True, "outer": True,
        }
        self.assertEqual(tuple(inspect.signature(auth.perform_d0_inner_execution_custody_preflight_v1).parameters), ())
        for name, value in knobs.items():
            with self.subTest(name=name), self.assertRaises(TypeError):
                auth.perform_d0_inner_execution_custody_preflight_v1(**{name: value})  # type: ignore[call-arg]

    def test_06_public_replay_rejects_fixed_authority_substitution(self) -> None:
        for name in ("D0_DESIGN_HASH", "MODEL_CONTENT_HASH", "THRESHOLD_CONTENT_HASH", "NUMPY_VERSION"):
            with self.subTest(name=name), mock.patch.object(auth, name, "0" * 64):
                with self.assertRaises(auth.D0ExecutionAuthorizationV1Error):
                    auth.replay_required_d0_public_authorities_v1()

    def test_07_no_private_or_scientific_content_in_public_serializations(self) -> None:
        text = repr((self.receipt.to_public_dict(), self.authorization.to_public_dict()))
        for forbidden in (
            "means_float_hex", "scales_float_hex", "eigenvalues_float_hex",
            "retained_loadings_float_hex", "threshold_float_hex", ":\\", "/Users/",
        ):
            self.assertNotIn(forbidden, text)

    def test_08_frozen_production_source_has_no_execution_entrypoint(self) -> None:
        source = Path(auth.__file__).read_text(encoding="utf-8")
        for forbidden in ("import pandas", "read_csv(", "np.linalg", "def calculate_spe", "def execute_d0"):
            self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
