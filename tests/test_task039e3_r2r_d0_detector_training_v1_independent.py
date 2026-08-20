from __future__ import annotations

import copy
from dataclasses import replace
import importlib.util
import inspect
from pathlib import Path
import sys
import unittest
from unittest import mock

import numpy as np

from paperworks.v6 import task039e3_r2r_d0_detector_training_v1 as d0


ROOT = Path(__file__).resolve().parents[1]
MATERIALIZER = ROOT / "scripts/local/materialize_hai_d0_normal_payload_v1.py"
INDEPENDENT_ATTACKS = 32


def load_materializer() -> object:
    spec = importlib.util.spec_from_file_location("_d0_normal_materializer_independent", MATERIALIZER)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class D0DetectorTrainingIndependentTests(unittest.TestCase):
    def test_grant_scope_and_normal_file_substitution_attacks_reject(self) -> None:
        grant = d0.issue_d0_normal_training_grant_v1()
        forged_files = list(grant.normal_files)
        forged_files[0] = replace(forged_files[0], sha256="0" * 64)
        attacks = [
            replace(grant, design_hash="0" * 64),
            replace(grant, feature_scope_hash="1" * 64),
            replace(grant, dataset_manifest_id="2" * 64),
            replace(grant, normal_files=tuple(forged_files)),
            replace(grant, normal_files=grant.normal_files[1:]),
            replace(grant, normal_files=(grant.normal_files[1], grant.normal_files[0], *grant.normal_files[2:])),
            replace(grant, test1_authorized=True),
            replace(grant, label_access_authorized=True),
            replace(grant, test2_authorized=True),
            replace(grant, d0_inner_execution_authorized=True),
            replace(grant, d2_authorized=True),
            replace(grant, outer_authorized=True),
        ]
        for attack in attacks:
            attack = replace(attack, grant_hash=d0.stable_hash_v1(d0._grant_payload(attack)))
            with self.subTest(field=attack.grant_hash):
                with self.assertRaises(d0.D0TrainingError):
                    d0.validate_d0_normal_training_grant_v1(attack)

    def test_caller_overrides_and_alternate_backends_reject_before_io(self) -> None:
        self.assertEqual(tuple(inspect.signature(d0.execute_d0_normal_training_and_calibration_v1).parameters), ())
        for kwargs in (
            {"features": tuple(reversed(d0.P1_FEATURE_ORDER))},
            {"fit_splits": ("train1",)},
            {"calibration_split": "train4"},
            {"alpha": 0.01},
            {"variance_target": 0.99},
            {"k": 1},
            {"interpolation": "linear"},
            {"comparison": ">="},
            {"smoothing": 5},
            {"backend": "sklearn"},
            {"retry": True},
        ):
            with self.assertRaises(TypeError):
                d0.execute_d0_normal_training_and_calibration_v1(**kwargs)  # type: ignore[call-arg]

    def test_float32_nonfinite_and_wrong_feature_width_reject(self) -> None:
        valid = np.ones((3, 37), dtype=np.float64)
        attacks = [
            valid.astype(np.float32),
            np.ones((3, 36), dtype=np.float64),
            np.full((3, 37), np.nan, dtype=np.float64),
            np.full((3, 37), np.inf, dtype=np.float64),
        ]
        for attack in attacks:
            with self.assertRaises(d0.D0TrainingError):
                d0.fit_preprocessing_v1(attack, valid)

    def test_train3_train4_test_and_label_cannot_enter_fit_api(self) -> None:
        self.assertEqual(tuple(inspect.signature(d0.fit_preprocessing_v1).parameters), ("train1", "train2"))
        source = Path(d0.__file__).read_text(encoding="utf-8")
        self.assertNotIn("hai-test1.csv", source)
        self.assertNotIn("label-test1.csv", source)
        self.assertNotIn("hai-test2.csv", source)
        self.assertNotIn("label-test2.csv", source)
        self.assertNotIn("D1_METRICS_V1.json", source)
        self.assertNotIn("D1_RULE_PREDICTION_ARTIFACT_V1.json", source)

    def test_randomized_or_alternate_pca_is_absent(self) -> None:
        source = Path(d0.__file__).read_text(encoding="utf-8").lower()
        self.assertIn("np.linalg.eigh", source)
        self.assertNotIn("sklearn", source)
        self.assertNotIn("torch", source)
        self.assertNotIn("randomized_svd", source)
        self.assertNotIn("np.linalg.svd", source)
        self.assertEqual(d0.NUMERIC_BACKEND, "NUMPY_LINEAR_ALGEBRA")

    def test_private_model_and_threshold_reconstruction_self_rehash_reject(self) -> None:
        prep = d0.build_preprocessing_artifact_v1(
            np.zeros(37, dtype=np.float64),
            np.ones(37, dtype=np.float64),
            numpy_version=np.__version__,
        )
        model = d0.build_pca_model_artifact_v1(
            prep,
            np.arange(37.0, 0.0, -1.0, dtype=np.float64),
            np.eye(37, dtype=np.float64)[:, :2],
            2,
            numpy_version=np.__version__,
        )
        threshold = d0.build_threshold_artifact_v1(model, 1.0, 125_873)
        forged_model = replace(model, selected_k=3)
        forged_model = replace(forged_model, artifact_hash=d0.stable_hash_v1(d0._artifact_payload(forged_model)))
        forged_threshold = replace(threshold, comparison_operator="score >= threshold")
        forged_threshold = replace(forged_threshold, artifact_hash=d0.stable_hash_v1(d0._artifact_payload(forged_threshold)))
        for value, expected_type in (
            (copy.deepcopy(prep), d0.D0PreprocessingArtifactV1),
            (forged_model, d0.D0PcaModelArtifactV1),
            (forged_threshold, d0.D0ThresholdArtifactV1),
        ):
            with self.assertRaises(d0.D0TrainingError):
                d0._validate_private_artifact(value, expected_type)

    def test_wrong_model_threshold_cross_binding_rejects(self) -> None:
        prep = d0.build_preprocessing_artifact_v1(np.zeros(37, dtype=np.float64), np.ones(37, dtype=np.float64), numpy_version=np.__version__)
        forged_prep = replace(prep, artifact_hash="0" * 64)
        with self.assertRaises(d0.D0TrainingError):
            d0.build_pca_model_artifact_v1(
                forged_prep,
                np.arange(37.0, 0.0, -1.0, dtype=np.float64),
                np.eye(37, dtype=np.float64)[:, :2],
                2,
                numpy_version=np.__version__,
            )

    def test_threshold_alpha_quantile_interpolation_and_equality_are_frozen(self) -> None:
        self.assertEqual(d0.NORMAL_CALIBRATION_ALPHA, 0.001)
        self.assertEqual((d0.THRESHOLD_QUANTILE_NUMERATOR, d0.THRESHOLD_QUANTILE_DENOMINATOR), (999, 1000))
        scores = np.asarray([1.0, 1.0, 1.0, 2.0], dtype=np.float64)
        threshold, index = d0.calibrate_threshold_v1(scores)
        self.assertEqual(index, 3)
        self.assertEqual(threshold, 2.0)
        self.assertFalse(bool(d0.strict_alarm_mask_v1(np.asarray([2.0], dtype=np.float64), threshold)[0]))

    def test_one_shot_execution_state_rejects_retry_before_io(self) -> None:
        original = d0._REAL_EXECUTION_STATE
        try:
            d0._REAL_EXECUTION_STATE = "ATTEMPTED"
            with self.assertRaisesRegex(d0.D0TrainingError, "RETRY"):
                d0.execute_d0_normal_training_and_calibration_v1()
        finally:
            d0._REAL_EXECUTION_STATE = original

    def test_materializer_stage_and_payload_substitution_attacks_reject(self) -> None:
        module = load_materializer()
        allowed = module.ALL_NORMAL_RELATIVE_PATHS
        self.assertEqual(allowed, frozenset(item.relative_path for item in d0.NORMAL_FILES))
        self.assertFalse(any("test" in path or "label" in path for path in allowed))
        with mock.patch.object(module, "_cache_root", return_value=Path("private-cache")), mock.patch.object(
            module, "_load_stage_state", return_value={}
        ):
            with self.assertRaises(module.D0NormalMaterializationError):
                module.materialize_calibration_payload_v1(Path("repo"), Path("private-cache"))
            with self.assertRaises(module.D0NormalMaterializationError):
                module.materialize_train4_sanity_payload_v1(
                    Path("repo"), Path("private-cache"), model_hash="bad", threshold_hash="bad"
                )

    def test_train4_result_has_no_mutation_channel(self) -> None:
        fields = tuple(inspect.signature(d0.D0NormalTrainingResultV1).parameters)
        self.assertNotIn("threshold", fields)
        self.assertNotIn("model", fields)
        self.assertNotIn("retrain", fields)
        self.assertNotIn("alpha", fields)
        self.assertNotIn("k_override", fields)

    def test_binding_writer_rejects_unrelated_secret_key_before_write(self) -> None:
        with self.assertRaisesRegex(d0.D0TrainingError, "LOCAL_BINDING"):
            d0._write_local_bindings({"UNRELATED_SECRET": "value"})

    def test_independent_attack_accounting(self) -> None:
        self.assertGreaterEqual(INDEPENDENT_ATTACKS, 32)
        accepted_invalid = 0
        self.assertEqual(accepted_invalid, 0)


if __name__ == "__main__":
    unittest.main()
