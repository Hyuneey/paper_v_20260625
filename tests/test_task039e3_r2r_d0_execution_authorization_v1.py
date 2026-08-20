from __future__ import annotations

import copy
from dataclasses import replace
import inspect
from pathlib import Path
import unittest

from paperworks.v6.common import stable_hash_v1
from paperworks.v6 import task039e3_r2r_d0_execution_authorization_v1 as auth


class D0ExecutionAuthorizationContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.receipt = auth.build_synthetic_d0_inner_execution_custody_preflight_receipt_v1()
        self.authorization = auth.issue_d0_inner_execution_authorization_v1(self.receipt)

    def assertReceiptRejected(self, value: object, *, require_real: bool = False) -> None:
        with self.assertRaises(auth.D0ExecutionAuthorizationV1Error):
            auth.validate_d0_inner_execution_custody_preflight_receipt_v1(value, require_real=require_real)  # type: ignore[arg-type]

    def assertAuthorizationRejected(self, value: object) -> None:
        with self.assertRaises(auth.D0ExecutionAuthorizationV1Error):
            auth.validate_d0_inner_execution_authorization_v1(value, self.receipt)  # type: ignore[arg-type]

    def test_public_authority_replay_closes_exact_dag(self) -> None:
        replay = auth.replay_required_d0_public_authorities_v1()
        self.assertEqual(replay.public_artifact_count, 26)
        self.assertEqual(replay.public_cross_binding_count, 50)
        self.assertEqual(replay.d0_design_hash, auth.D0_DESIGN_HASH)
        self.assertTrue(replay.integrity_audited)
        self.assertTrue(replay.d0_execution_ready_for_separate_authorization)
        self.assertFalse(replay.d0_currently_authorized)

    def test_exact_scope_detector_and_scientific_identities(self) -> None:
        value = self.authorization
        self.assertEqual(value.authorization_version, "TASK039E3_R2R_D0_INNER_EXECUTION_AUTHORIZATION_V1")
        self.assertEqual(value.authorization_scope, "HAI_23_05_P1_TEST1_D0_PCA_SPE_INNER_V1")
        self.assertEqual(value.detector_id, "D0_PCA_SPE_V1")
        self.assertEqual(value.design_hash, auth.D0_DESIGN_HASH)
        self.assertEqual(value.preprocessing_content_hash, auth.PREPROCESSING_CONTENT_HASH)
        self.assertEqual(value.model_content_hash, auth.MODEL_CONTENT_HASH)
        self.assertEqual(value.threshold_content_hash, auth.THRESHOLD_CONTENT_HASH)
        self.assertEqual(value.test1_feature_sha256, auth.TEST1_FEATURE_SHA256)
        self.assertEqual(value.test1_label_sha256, auth.TEST1_LABEL_SHA256)
        self.assertEqual(value.selected_k, 10)
        self.assertEqual(value.residual_dimensions, 27)
        self.assertEqual(value.threshold_comparison_operator, "score > threshold")

    def test_numeric_backend_is_exact(self) -> None:
        self.assertEqual(self.authorization.python_version, "3.12.13")
        self.assertEqual(self.authorization.python_runtime_identity, "CPython-3.12")
        self.assertEqual(self.authorization.numpy_version, "2.3.5")
        self.assertEqual(self.authorization.numeric_backend, "NUMPY_LINEAR_ALGEBRA")

    def test_synthetic_contract_validates_but_never_authorizes(self) -> None:
        self.assertEqual(auth.validate_d0_inner_execution_custody_preflight_receipt_v1(self.receipt), self.receipt.custody_preflight_hash)
        self.assertEqual(auth.validate_d0_inner_execution_authorization_v1(self.authorization, self.receipt), self.authorization.authorization_hash)
        self.assertFalse(self.authorization.d0_inner_execution_authorized)
        self.assertFalse(self.authorization.d0_detector_prediction_authorized)
        self.assertReceiptRejected(self.receipt, require_real=True)
        with self.assertRaises(auth.D0ExecutionAuthorizationV1Error):
            auth.validate_d0_inner_execution_authorization_v1(self.authorization, self.receipt, require_real=True)

    def test_receipt_reconstruction_copy_deepcopy_replace_reject(self) -> None:
        reconstructed = type(self.receipt)(**self.receipt.__dict__)
        for value in (reconstructed, copy.copy(self.receipt), copy.deepcopy(self.receipt), replace(self.receipt)):
            if value is self.receipt:
                continue
            self.assertReceiptRejected(value)

    def test_receipt_self_rehash_rejects(self) -> None:
        mutated = replace(self.receipt, design_hash="0" * 64, custody_preflight_hash="")
        mutated = replace(mutated, custody_preflight_hash=stable_hash_v1(mutated._payload()))
        self.assertReceiptRejected(mutated)

    def test_authorization_reconstruction_copy_deepcopy_replace_reject(self) -> None:
        reconstructed = type(self.authorization)(**self.authorization.__dict__)
        for value in (reconstructed, copy.copy(self.authorization), copy.deepcopy(self.authorization), replace(self.authorization)):
            if value is self.authorization:
                continue
            self.assertAuthorizationRejected(value)

    def test_authorization_self_rehash_rejects(self) -> None:
        mutated = replace(self.authorization, model_content_hash="0" * 64, authorization_hash="")
        mutated = replace(mutated, authorization_hash=stable_hash_v1(mutated._payload()))
        self.assertAuthorizationRejected(mutated)

    def test_wrong_receipt_authorities_reject(self) -> None:
        mutations = (
            {"design_hash": "0" * 64},
            {"model_expected_hash": "0" * 64},
            {"threshold_expected_hash": "0" * 64},
            {"feature_count": 36},
            {"feature_order_hash": "0" * 64},
            {"test1_feature_expected_hash": "0" * 64},
            {"test1_label_expected_hash": "0" * 64},
            {"numpy_version": "0.0.0"},
        )
        for values in mutations:
            with self.subTest(values=values):
                self.assertReceiptRejected(replace(self.receipt, **values))

    def test_authorization_semantic_substitutions_reject(self) -> None:
        mutations = (
            {"design_hash": "0" * 64},
            {"preprocessing_content_hash": "0" * 64},
            {"model_content_hash": "0" * 64},
            {"threshold_content_hash": "0" * 64},
            {"feature_set_hash": "0" * 64},
            {"selected_k": 9},
            {"threshold_comparison_operator": "score >= threshold"},
            {"test1_feature_sha256": "0" * 64},
            {"test1_label_sha256": "0" * 64},
        )
        for values in mutations:
            with self.subTest(values=values):
                self.assertAuthorizationRejected(replace(self.authorization, **values))

    def test_all_escalations_remain_false(self) -> None:
        fields = (
            "label_access_before_prediction_freeze_authorized",
            "d1_execution_authorized", "d1_rerun_authorized", "d2_authorized",
            "fusion_authorized", "outer_authorized", "test2_authorized",
            "retraining_authorized", "recalibration_authorized",
            "threshold_change_authorized", "feature_change_authorized", "model_change_authorized",
        )
        for name in fields:
            self.assertIs(getattr(self.authorization, name), False)
            self.assertAuthorizationRejected(replace(self.authorization, **{name: True}))

    def test_future_prediction_contract_is_label_blind(self) -> None:
        value = self.authorization
        self.assertEqual(value.future_prediction_artifact_family, "ScientificDetectorPredictionArtifactV1")
        self.assertTrue(value.future_prediction_artifact_label_blind)
        self.assertFalse(value.future_prediction_label_fields_authorized)
        self.assertFalse(value.future_prediction_d1_fields_authorized)
        self.assertFalse(value.future_prediction_metric_fields_authorized)
        freeze = value.future_execution_order.index("freeze_detector_prediction_artifact")
        label = value.future_execution_order.index("validate_label_raw_hash_after_prediction_freeze")
        self.assertLess(freeze, label)

    def test_public_objects_contain_no_paths_or_private_values(self) -> None:
        for value in (self.receipt.to_public_dict(), self.authorization.to_public_dict()):
            text = repr(value)
            self.assertNotIn("means_float_hex", text)
            self.assertNotIn("retained_loadings_float_hex", text)
            self.assertNotIn("threshold_float_hex", text)
            self.assertNotIn(":\\", text)
            self.assertNotIn("/Users/", text)

    def test_public_apis_accept_no_caller_paths_or_scientific_knobs(self) -> None:
        preflight = inspect.signature(auth.perform_d0_inner_execution_custody_preflight_v1)
        self.assertEqual(tuple(preflight.parameters), ())
        issue = inspect.signature(auth.issue_d0_inner_execution_authorization_v1)
        self.assertEqual(tuple(issue.parameters), ("receipt",))
        for signature in (preflight, issue):
            self.assertFalse(any(item.kind is inspect.Parameter.VAR_KEYWORD for item in signature.parameters.values()))

    def test_module_has_no_scientific_execution_plane(self) -> None:
        source = Path(auth.__file__).read_text(encoding="utf-8")
        prohibited = ("import pandas", "read_csv(", "np.linalg", "def calculate_spe", "hai-test2.csv", "label-test2.csv")
        for token in prohibited:
            self.assertNotIn(token, source)


if __name__ == "__main__":
    unittest.main()
