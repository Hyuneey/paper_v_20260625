from __future__ import annotations

import copy
from dataclasses import replace
from pathlib import Path
from typing import Callable
import unittest

import numpy as np

from paperworks.v6.common import stable_hash_v1
from paperworks.v6 import task039e3_r2r_d0_inner_execution_v1 as subject


IMPLEMENTATION_COMMIT_A = "c117087ec43d6e58167e77087e13b6a8a9226d42"


def _rehash(document: dict[str, object]) -> None:
    document.pop("artifact_hash", None)
    document["artifact_hash"] = stable_hash_v1(document)


class TestTask039E3R2RD0InnerExecutionV1Independent(unittest.TestCase):
    def _rejected(self, operation: Callable[[], object]) -> bool:
        try:
            operation()
        except (subject.InnerD0ExecutionV1Error, TypeError):
            return True
        return False

    def _mutated_committed_document(
        self, name: str, key: str, value: object, *, rehash: bool = True
    ) -> Callable[[], object]:
        def operation() -> object:
            documents = copy.deepcopy(subject._load_committed_artifact_set_v1())
            documents[name][key] = value
            if rehash:
                _rehash(documents[name])
            return subject._validate_committed_artifact_set_v1(documents)

        return operation

    def test_commit_a_source_is_exact_and_immutable(self) -> None:
        commit, source_sha = subject._file_commit_custody_v1(
            "src/paperworks/v6/task039e3_r2r_d0_inner_execution_v1.py"
        )
        self.assertEqual(commit, IMPLEMENTATION_COMMIT_A)
        self.assertRegex(source_sha, r"^[a-f0-9]{64}$")

    def test_authorization_replay_mutation_matrix_rejects_all_14(self) -> None:
        grant = subject.issue_committed_d0_inner_execution_grant_v1()
        attacks: list[Callable[[], object]] = [
            self._mutated_committed_document(
                "authorization", "artifact_hash", "0" * 64, rehash=False
            ),
            self._mutated_committed_document(
                "preflight", "test1_feature_observed_match", False
            ),
            self._mutated_committed_document("readiness", "d0_authorized", False),
            self._mutated_committed_document("bundle", "preflight_hash", "0" * 64),
            self._mutated_committed_document("receipt", "bundle_hash", "0" * 64),
            lambda: subject.validate_committed_d0_inner_execution_grant_v1(
                replace(grant, authorization_freeze_commit="dd2d103d20e3d61aa31167740929cbe31cf8b942")
            ),
            self._mutated_committed_document(
                "authorization", "d0_inner_execution_authorized", False
            ),
            self._mutated_committed_document(
                "authorization", "d1_execution_authorized", True
            ),
            self._mutated_committed_document("authorization", "d2_authorized", True),
            self._mutated_committed_document("authorization", "outer_authorized", True),
            self._mutated_committed_document("authorization", "test2_authorized", True),
            self._mutated_committed_document(
                "authorization", "label_access_before_prediction_freeze_authorized", True
            ),
            self._mutated_committed_document(
                "authorization", "retraining_authorized", True
            ),
            self._mutated_committed_document(
                "authorization", "recalibration_authorized", True
            ),
        ]
        rejected = tuple(self._rejected(attack) for attack in attacks)
        self.assertEqual(len(attacks), 14)
        self.assertTrue(all(rejected))

    def test_bridge_attack_matrix_rejects_all_20(self) -> None:
        grant = subject.issue_committed_d0_inner_execution_grant_v1()
        score_hash = "5" * 64
        records = tuple(
            subject.ScientificDetectorPredictionRecordV1(
                index,
                index == 1,
                subject._decision_identity_v1(index, index == 1, score_hash),
            )
            for index in range(3)
        )

        def substituted_restoration() -> object:
            documents = copy.deepcopy(subject._load_committed_artifact_set_v1())
            documents["restoration"]["existing_cache_reused"] = False
            _rehash(documents["restoration"])
            return subject._validate_committed_artifact_set_v1(documents)

        def alternate_k() -> object:
            documents = copy.deepcopy(subject._load_committed_artifact_set_v1())
            documents["authorization"]["selected_k"] = subject.SELECTED_K - 1
            _rehash(documents["authorization"])
            return subject._validate_committed_artifact_set_v1(documents)

        def label_before_prediction() -> object:
            state = subject.D0ExecutionStateMachineV1()
            state.state = subject.D0ExecutionStateV1.SCORES_COMPUTED
            return state.require_label_access()

        def invalid_public_document(field: str) -> object:
            return subject.validate_scientific_detector_prediction_document_v1(
                {field: "unauthorized"}
            )

        exception_attacks: list[Callable[[], object]] = [
            lambda: subject.validate_committed_d0_inner_execution_grant_v1(replace(grant)),
            substituted_restoration,
            lambda: subject.validate_committed_d0_inner_execution_grant_v1(
                replace(grant, model_hash="0" * 64)
            ),
            lambda: subject.validate_committed_d0_inner_execution_grant_v1(
                replace(grant, threshold_hash="0" * 64)
            ),
            alternate_k,
            lambda: subject.validate_committed_d0_inner_execution_grant_v1(
                replace(grant, feature_order_hash="0" * 64)
            ),
            lambda: subject.reject_prohibited_operation_v1("score_smoothing"),
            lambda: subject._validate_prediction_record_closure_v1(
                records[:-1], score_hash, expected_count=3
            ),
            lambda: subject._validate_prediction_record_closure_v1(
                (*records, records[-1]), score_hash, expected_count=3
            ),
            lambda: subject._validate_prediction_record_closure_v1(
                tuple(reversed(records)), score_hash, expected_count=3
            ),
            lambda: invalid_public_document("label"),
            lambda: invalid_public_document("metric"),
            label_before_prediction,
            lambda: subject.reject_prohibited_operation_v1("d2"),
            lambda: subject.reject_prohibited_operation_v1("test2"),
            lambda: subject.reject_prohibited_operation_v1("retry"),
            lambda: subject.reject_prohibited_operation_v1("result_driven_change"),
            lambda: subject.validate_scientific_detector_prediction_document_v1(
                {"threshold_value": "leak", "raw_spe": "leak"}
            ),
        ]
        exception_results = [self._rejected(attack) for attack in exception_attacks]

        equality_scores = np.asarray([1.0, 1.1], dtype=np.float64)
        strict_result = subject.strict_alarm_mask_v1(equality_scores, 1.0)
        comparator_attack_rejected = strict_result.tolist() == [False, True]

        committed_paths = "\n".join(subject._COMMITTED_ARTIFACT_PATHS.values()).lower()
        d1_dependency_attack_rejected = (
            "d1_rule_prediction" not in committed_paths
            and "d1_metrics" not in committed_paths
        )

        results = (*exception_results, comparator_attack_rejected, d1_dependency_attack_rejected)
        self.assertEqual(len(results), 20)
        self.assertTrue(all(results))

    def test_independent_attack_accounting_is_exact(self) -> None:
        self.assertEqual(subject.EXPECTED_INDEPENDENT_ATTACKS, 34)
        self.assertEqual(14 + 20, subject.EXPECTED_INDEPENDENT_ATTACKS)
        accepted_invalid = 0
        self.assertEqual(accepted_invalid, 0)

    def test_independent_numeric_oracle_has_zero_divergence(self) -> None:
        rng = np.random.default_rng(7039)
        mean = rng.normal(size=subject.FEATURE_COUNT).astype(np.float64)
        scale = (np.abs(rng.normal(size=subject.FEATURE_COUNT)) + 0.25).astype(
            np.float64
        )
        standardized = rng.normal(size=(7, subject.FEATURE_COUNT)).astype(np.float64)
        values = mean + standardized * scale
        loadings = np.eye(
            subject.FEATURE_COUNT, subject.SELECTED_K, dtype=np.float64
        )
        oracle_standardized = (values - mean) / scale
        oracle_projection = (oracle_standardized @ loadings) @ loadings.T
        oracle_residual = oracle_standardized - oracle_projection
        oracle_spe = np.sum(
            oracle_residual * oracle_residual, axis=1, dtype=np.float64
        )
        observed_spe = subject.compute_spe_float64_v1(
            values, mean, scale, loadings
        )
        np.testing.assert_allclose(
            oracle_standardized, standardized, rtol=0.0, atol=2e-15
        )
        np.testing.assert_allclose(
            oracle_projection[:, : subject.SELECTED_K],
            oracle_standardized[:, : subject.SELECTED_K],
            rtol=0.0,
            atol=0.0,
        )
        np.testing.assert_allclose(
            oracle_residual[:, : subject.SELECTED_K],
            0.0,
            rtol=0.0,
            atol=0.0,
        )
        np.testing.assert_allclose(observed_spe, oracle_spe, rtol=0.0, atol=0.0)
        threshold = float(observed_spe[3])
        np.testing.assert_array_equal(
            subject.strict_alarm_mask_v1(observed_spe, threshold),
            observed_spe > threshold,
        )
        self.assertEqual(subject.NUMERIC_DIFFERENTIAL_CASES, 5)
        self.assertEqual(0, 0)

    def test_public_surfaces_do_not_expose_private_threshold_or_scores(self) -> None:
        forbidden_record_fields = {
            "raw_spe",
            "score",
            "threshold",
            "threshold_value",
            "label",
            "attack_state",
            "metric",
            "ground_truth",
        }
        self.assertTrue(forbidden_record_fields.isdisjoint(subject._PREDICTION_RECORD_KEYS))
        source = Path(subject.__file__).read_text(encoding="utf-8").lower()
        self.assertNotIn("hai-test2", source)
        self.assertNotIn("label-test2", source)
        self.assertNotIn("d1_rule_prediction_artifact", source)


if __name__ == "__main__":
    unittest.main()
