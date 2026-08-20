from __future__ import annotations

import copy
from dataclasses import replace
import inspect
from pathlib import Path
import unittest

import numpy as np

from paperworks.v6.common import stable_hash_v1
from paperworks.v6 import task039e3_r2r_d0_inner_execution_v1 as subject
from paperworks.v6 import task039e3_r2r_utility_evaluator_metrics_v1 as metrics


def _rehash(document: dict[str, object]) -> None:
    document.pop("artifact_hash", None)
    document["artifact_hash"] = stable_hash_v1(document)


def _records(count: int, score_hash: str) -> tuple[subject.ScientificDetectorPredictionRecordV1, ...]:
    return tuple(
        subject.ScientificDetectorPredictionRecordV1(
            index,
            index % 3 == 0,
            subject._decision_identity_v1(index, index % 3 == 0, score_hash),
        )
        for index in range(count)
    )


class TestTask039E3R2RD0InnerExecutionV1(unittest.TestCase):
    def test_committed_grant_replay(self) -> None:
        grant = subject.issue_committed_d0_inner_execution_grant_v1()
        self.assertEqual(
            subject.validate_committed_d0_inner_execution_grant_v1(grant),
            grant.grant_hash,
        )
        self.assertEqual(grant.authorization_hash, subject.AUTHORIZATION_HASH)
        self.assertTrue(grant.d0_inner_execution_authorized)
        self.assertFalse(grant.d2_authorized)

    def test_reconstructed_grant_is_rejected(self) -> None:
        grant = subject.issue_committed_d0_inner_execution_grant_v1()
        with self.assertRaises(subject.InnerD0ExecutionV1Error):
            subject.validate_committed_d0_inner_execution_grant_v1(replace(grant))

    def test_wrong_authorization_is_rejected(self) -> None:
        documents = copy.deepcopy(subject._load_committed_artifact_set_v1())
        documents["authorization"]["d0_inner_execution_authorized"] = False
        _rehash(documents["authorization"])
        with self.assertRaises(subject.InnerD0ExecutionV1Error):
            subject._validate_committed_artifact_set_v1(documents)

    def test_wrong_preflight_is_rejected(self) -> None:
        documents = copy.deepcopy(subject._load_committed_artifact_set_v1())
        documents["preflight"]["test1_feature_observed_match"] = False
        _rehash(documents["preflight"])
        with self.assertRaises(subject.InnerD0ExecutionV1Error):
            subject._validate_committed_artifact_set_v1(documents)

    def test_wrong_receipt_is_rejected(self) -> None:
        documents = copy.deepcopy(subject._load_committed_artifact_set_v1())
        documents["receipt"]["bundle_hash"] = "0" * 64
        _rehash(documents["receipt"])
        with self.assertRaises(subject.InnerD0ExecutionV1Error):
            subject._validate_committed_artifact_set_v1(documents)

    def test_wrong_private_authority_hashes_are_rejected(self) -> None:
        grant = subject.issue_committed_d0_inner_execution_grant_v1()
        for field_name in ("preprocessing_hash", "model_hash", "threshold_hash"):
            with self.subTest(field_name=field_name):
                mutation = replace(grant, **{field_name: "0" * 64})
                with self.assertRaises(subject.InnerD0ExecutionV1Error):
                    subject.validate_committed_d0_inner_execution_grant_v1(mutation)

    def test_wrong_feature_order_is_rejected(self) -> None:
        grant = subject.issue_committed_d0_inner_execution_grant_v1()
        mutation = replace(grant, feature_order_hash="0" * 64)
        with self.assertRaises(subject.InnerD0ExecutionV1Error):
            subject.validate_committed_d0_inner_execution_grant_v1(mutation)

    def test_wrong_test1_hash_is_rejected(self) -> None:
        with self.assertRaises(subject.InnerD0ExecutionV1Error):
            subject.validate_test1_feature_raw_identity_v1(
                "0" * 64, subject.TEST1_FEATURE_BYTE_SIZE
            )
        with self.assertRaises(subject.InnerD0ExecutionV1Error):
            subject.validate_test1_feature_raw_identity_v1(
                subject.TEST1_FEATURE_SHA256, subject.TEST1_FEATURE_BYTE_SIZE + 1
            )

    def test_numeric_backend_identity(self) -> None:
        self.assertEqual(
            subject.validate_numeric_backend_v1(),
            (subject.PYTHON_VERSION, subject.NUMPY_VERSION),
        )

    def test_float32_is_rejected(self) -> None:
        values = np.zeros((2, subject.FEATURE_COUNT), dtype=np.float32)
        mean = np.zeros(subject.FEATURE_COUNT, dtype=np.float64)
        scale = np.ones(subject.FEATURE_COUNT, dtype=np.float64)
        loadings = np.eye(subject.FEATURE_COUNT, subject.SELECTED_K, dtype=np.float64)
        with self.assertRaises(subject.InnerD0ExecutionV1Error):
            subject.compute_spe_float64_v1(values, mean, scale, loadings)

    def test_nonfinite_data_is_rejected(self) -> None:
        values = np.zeros((2, subject.FEATURE_COUNT), dtype=np.float64)
        values[0, 0] = np.nan
        mean = np.zeros(subject.FEATURE_COUNT, dtype=np.float64)
        scale = np.ones(subject.FEATURE_COUNT, dtype=np.float64)
        loadings = np.eye(subject.FEATURE_COUNT, subject.SELECTED_K, dtype=np.float64)
        with self.assertRaises(subject.InnerD0ExecutionV1Error):
            subject.compute_spe_float64_v1(values, mean, scale, loadings)

    def test_54000_prediction_closure_contract(self) -> None:
        score_hash = "1" * 64
        records = _records(subject.EXPECTED_ROW_COUNT, score_hash)
        subject._validate_prediction_record_closure_v1(records, score_hash)
        self.assertEqual(records[0].physical_row_index, 0)
        self.assertEqual(records[-1].physical_row_index, 53_999)
        self.assertEqual(len({record.physical_row_index for record in records}), 54_000)

    def test_spe_arithmetic(self) -> None:
        mean = np.arange(subject.FEATURE_COUNT, dtype=np.float64)
        scale = np.arange(1, subject.FEATURE_COUNT + 1, dtype=np.float64)
        standardized = np.vstack(
            (
                np.linspace(-1.0, 1.0, subject.FEATURE_COUNT, dtype=np.float64),
                np.linspace(2.0, -2.0, subject.FEATURE_COUNT, dtype=np.float64),
            )
        )
        values = mean + standardized * scale
        loadings = np.eye(subject.FEATURE_COUNT, subject.SELECTED_K, dtype=np.float64)
        expected_projection = standardized @ loadings @ loadings.T
        expected_residual = standardized - expected_projection
        expected_spe = np.sum(expected_residual**2, axis=1, dtype=np.float64)
        observed = subject.compute_spe_float64_v1(values, mean, scale, loadings)
        np.testing.assert_allclose(observed, expected_spe, rtol=0.0, atol=1e-15)

    def test_numeric_differential_semantics(self) -> None:
        mean = np.arange(subject.FEATURE_COUNT, dtype=np.float64) / 10.0
        scale = np.arange(1, subject.FEATURE_COUNT + 1, dtype=np.float64) / 7.0
        z = np.vstack(
            (
                np.arange(subject.FEATURE_COUNT, dtype=np.float64) / 13.0,
                -np.arange(subject.FEATURE_COUNT, dtype=np.float64) / 17.0,
            )
        )
        values = mean + z * scale
        loadings = np.eye(subject.FEATURE_COUNT, subject.SELECTED_K, dtype=np.float64)
        manual_standardization = (values - mean) / scale
        manual_projection = (manual_standardization @ loadings) @ loadings.T
        manual_residual = manual_standardization - manual_projection
        manual_spe = np.sum(manual_residual * manual_residual, axis=1, dtype=np.float64)
        observed_spe = subject.compute_spe_float64_v1(values, mean, scale, loadings)
        np.testing.assert_allclose(manual_standardization, z, rtol=0.0, atol=1e-15)
        np.testing.assert_allclose(
            manual_projection[:, : subject.SELECTED_K],
            z[:, : subject.SELECTED_K],
            rtol=0.0,
            atol=1e-15,
        )
        np.testing.assert_allclose(
            manual_residual[:, : subject.SELECTED_K],
            np.zeros((2, subject.SELECTED_K)),
            rtol=0.0,
            atol=1e-15,
        )
        np.testing.assert_allclose(observed_spe, manual_spe, rtol=0.0, atol=1e-15)
        np.testing.assert_array_equal(
            subject.strict_alarm_mask_v1(observed_spe, float(observed_spe[0])),
            observed_spe > observed_spe[0],
        )
        self.assertEqual(subject.NUMERIC_DIFFERENTIAL_CASES, 5)

    def test_strict_comparator_and_equality(self) -> None:
        scores = np.asarray([0.9, 1.0, 1.1], dtype=np.float64)
        mask = subject.strict_alarm_mask_v1(scores, 1.0)
        np.testing.assert_array_equal(mask, np.asarray([False, False, True]))

    def test_prediction_record_is_label_blind(self) -> None:
        score_hash = "2" * 64
        record = _records(1, score_hash)[0]
        self.assertEqual(
            set(record.to_public_dict()),
            {
                "physical_row_index",
                "alarm_emitted",
                "detector_decision_identity",
            },
        )
        forbidden = {"label", "attack_state", "metric", "score", "threshold", "ground_truth"}
        self.assertTrue(forbidden.isdisjoint(record.to_public_dict()))

    def test_prediction_index_deletion_insertion_and_reorder_rejected(self) -> None:
        score_hash = "3" * 64
        records = _records(3, score_hash)
        for mutation in (records[:-1], (*records, records[-1]), tuple(reversed(records))):
            with self.subTest(length=len(mutation)):
                with self.assertRaises(subject.InnerD0ExecutionV1Error):
                    subject._validate_prediction_record_closure_v1(
                        mutation, score_hash, expected_count=3
                    )

    def test_prediction_persistence_order_is_enforced(self) -> None:
        state = subject.D0ExecutionStateMachineV1()
        with self.assertRaises(subject.InnerD0ExecutionV1Error):
            subject._persist_prediction_before_label_v1(state, None)  # type: ignore[arg-type]
        state.transition(
            subject.D0ExecutionStateV1.NOT_STARTED,
            subject.D0ExecutionStateV1.GRANT_REPLAYED,
        )
        with self.assertRaises(subject.InnerD0ExecutionV1Error):
            state.require_label_access()

    def test_label_access_before_prediction_freeze_rejected(self) -> None:
        state = subject.D0ExecutionStateMachineV1()
        for state_value in (
            subject.D0ExecutionStateV1.NOT_STARTED,
            subject.D0ExecutionStateV1.GRANT_REPLAYED,
            subject.D0ExecutionStateV1.PRIVATE_AUTHORITY_VALIDATED,
            subject.D0ExecutionStateV1.FEATURE_PARSED,
            subject.D0ExecutionStateV1.SCORES_COMPUTED,
        ):
            state.state = state_value
            with self.subTest(state=state_value):
                with self.assertRaises(subject.InnerD0ExecutionV1Error):
                    state.require_label_access()
        state.state = subject.D0ExecutionStateV1.PREDICTION_FROZEN
        state.require_label_access()

    def test_attack_event_formation(self) -> None:
        labels = (0, 1, 1, 0, 1, 0, 1, 1, 1)
        self.assertEqual(
            metrics.derive_attack_events_v1(labels),
            (metrics.IntervalV1(1, 3), metrics.IntervalV1(4, 5), metrics.IntervalV1(6, 9)),
        )

    def test_alarm_episode_formation(self) -> None:
        self.assertEqual(
            metrics.form_alarm_episodes_v1((6, 2, 3, 3, 10)),
            (
                metrics.IntervalV1(2, 4),
                metrics.IntervalV1(6, 7),
                metrics.IntervalV1(10, 11),
            ),
        )

    def test_recall_arithmetic(self) -> None:
        attack = (metrics.IntervalV1(1, 4), metrics.IntervalV1(8, 10))
        alarms = (metrics.IntervalV1(3, 5), metrics.IntervalV1(12, 13))
        recall_numerator, recall_denominator, _, _ = subject.metric_arithmetic_v1(
            attack, alarms, 100
        )
        self.assertEqual((recall_numerator, recall_denominator), (1, 2))

    def test_far_arithmetic_uses_episodes(self) -> None:
        attack = (metrics.IntervalV1(1, 4),)
        alarms = (
            metrics.IntervalV1(2, 3),
            metrics.IntervalV1(10, 12),
            metrics.IntervalV1(20, 21),
        )
        _, _, numerator, denominator = subject.metric_arithmetic_v1(attack, alarms, 3600)
        self.assertEqual(numerator, 2)
        self.assertEqual(denominator, 1.0)

    def test_test2_d1_d2_fusion_retry_and_result_change_rejected(self) -> None:
        for operation in (
            "test2",
            "d1_content_read",
            "d1_execution",
            "d2",
            "fusion",
            "outer",
            "retry",
            "retraining",
            "recalibration",
            "result_driven_change",
            "score_smoothing",
        ):
            with self.subTest(operation=operation):
                with self.assertRaises(subject.InnerD0ExecutionV1Error):
                    subject.reject_prohibited_operation_v1(operation)

    def test_d1_content_artifacts_are_not_committed_dependencies(self) -> None:
        joined = "\n".join(subject._COMMITTED_ARTIFACT_PATHS.values()).lower()
        self.assertNotIn("d1_rule_prediction", joined)
        self.assertNotIn("d1_metrics", joined)
        self.assertNotIn("hai-test2", joined)
        self.assertNotIn("label-test2", joined)

    def test_no_real_caller_scientific_knobs(self) -> None:
        signature = inspect.signature(subject.execute_authorized_d0_inner_v1)
        self.assertEqual(tuple(signature.parameters), ())
        with self.assertRaises(TypeError):
            subject.execute_authorized_d0_inner_v1(threshold=1.0)  # type: ignore[call-arg]
        with self.assertRaises(TypeError):
            subject.execute_authorized_d0_inner_v1(features=("P1_FT01",))  # type: ignore[call-arg]

    def test_public_prediction_schema_blocks_label_metric_score_and_threshold(self) -> None:
        self.assertTrue(
            {
                "label",
                "attack_state",
                "metric",
                "score",
                "raw_spe",
                "threshold_value",
                "ground_truth",
            }.isdisjoint(subject._PREDICTION_RECORD_KEYS)
        )
        self.assertNotIn("threshold_value", subject._PREDICTION_DOCUMENT_KEYS)
        self.assertNotIn("scores", subject._PREDICTION_DOCUMENT_KEYS)

    def test_execution_state_machine_has_exact_ordered_states(self) -> None:
        self.assertEqual(
            tuple(state.value for state in subject.D0ExecutionStateV1),
            (
                "NOT_STARTED",
                "GRANT_REPLAYED",
                "PRIVATE_AUTHORITY_VALIDATED",
                "FEATURE_PARSED",
                "SCORES_COMPUTED",
                "PREDICTION_FROZEN",
                "LABEL_PARSED",
                "METRICS_COMPUTED",
                "RESULT_FROZEN",
            ),
        )

    def test_source_contains_no_test2_or_d1_result_filename(self) -> None:
        source = Path(subject.__file__).read_text(encoding="utf-8").lower()
        self.assertNotIn("hai-test2", source)
        self.assertNotIn("label-test2", source)
        self.assertNotIn("d1_rule_prediction_artifact", source)
        self.assertNotIn("d1_metrics_v1.json", source)


if __name__ == "__main__":
    unittest.main()
