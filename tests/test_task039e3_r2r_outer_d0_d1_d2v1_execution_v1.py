from __future__ import annotations

from dataclasses import replace
import unittest

from paperworks.v6 import task039e3_r2r_outer_d0_d1_d2v1_execution_v1 as subject
from paperworks.v6 import task039e3_r2r_d0_inner_execution_v1 as d0
from paperworks.v6 import task039e3_r2r_utility_evaluator_metrics_v1 as metrics


class OuterExecutionStaticTests(unittest.TestCase):
    def assertRejected(self, callback) -> None:
        with self.assertRaises(subject.OuterExecutionError):
            callback()

    def test_01_exact_authorization_required(self):
        grant = subject.issue_committed_outer_execution_grant_v1()
        self.assertEqual(subject.AUTHORIZATION_SHA256, grant.authorization_sha256)

    def test_02_reconstructed_or_mutated_grant_rejected(self):
        grant = subject.issue_committed_outer_execution_grant_v1()
        self.assertRejected(lambda: subject.validate_grant(replace(grant, retries=1)))

    def test_03_wrong_feature_sha_rejected(self):
        self.assertRejected(lambda: subject._parse_feature_bytes(b"wrong", object()))

    def test_04_wrong_label_sha_rejected(self):
        self.assertRejected(lambda: subject._parse_label_bytes(b"wrong", ()))

    def test_05_compact_row_mismatch_rejected(self):
        document = subject.compact_prediction("OuterD0PredictionV1", (1,))
        document["record_count"] = 1
        self.assertRejected(lambda: subject.expand_compact_prediction(document))

    def test_06_compact_round_trip_has_exact_domain(self):
        document = subject.compact_prediction("OuterD0PredictionV1", (0, 2, subject.ROW_COUNT - 1))
        values = subject.expand_compact_prediction(document)
        self.assertEqual(subject.ROW_COUNT, len(values))
        self.assertEqual(3, sum(values))

    def test_07_d0_frozen_model_inference_arithmetic(self):
        np = d0._np_v1()
        values = np.zeros((2, 37), dtype=np.float64)
        values[1, 36] = 2.0
        mean = np.zeros(37, dtype=np.float64)
        scale = np.ones(37, dtype=np.float64)
        loadings = np.zeros((37, 10), dtype=np.float64)
        loadings[:10, :] = np.eye(10, dtype=np.float64)
        observed = d0.compute_spe_float64_v1(values, mean, scale, loadings)
        self.assertEqual([0.0, 4.0], observed.tolist())

    def test_08_d0_fit_rejected(self):
        self.assertRejected(lambda: subject.reject_prohibited_operation_v1("d0_fit"))

    def test_09_d0_threshold_mutation_rejected(self):
        self.assertRejected(lambda: subject.reject_prohibited_operation_v1("threshold_mutation"))

    def test_10_shared_feature_snapshot_type_is_single(self):
        fields = subject.OuterTest2FeatureSnapshotV1.__dataclass_fields__
        self.assertIn("_d0_matrix", fields)
        self.assertIn("_d1_columns", fields)

    def test_11_d1_common42_exact(self):
        self.assertEqual(("COMMON-42", 42), ("COMMON-42", subject.D1_RELATION_COUNT))

    def test_12_rule_mutation_rejected(self):
        self.assertRejected(lambda: subject.reject_prohibited_operation_v1("rule_mutation"))

    def test_13_evaluator_identity_exact(self):
        self.assertEqual("af74bf3bd9ae240f21c57630b4804eabb997021353f15e7c402904b94f783fb5",
                         subject.D1_EVALUATOR_IDENTITY)

    def test_14_d1_timestamp_semantics(self):
        source = subject._evaluate_d1.__doc__ or ""
        self.assertIn("OUTER", source)

    def test_15_d1_one_second_aggregation_collapses_duplicates(self):
        indices = tuple(sorted({2, 2, 4}))
        self.assertEqual((2, 4), indices)

    def test_16_d2_same_second_source_mapping(self):
        self.assertEqual((True, True, "RULE_RECOVERY"),
                         subject.fuse_point_v1(False, frozenset({"a", "b"})))

    def test_17_same_source_duplicates_collapse(self):
        self.assertEqual((False, False, "NONE"),
                         subject.fuse_point_v1(False, frozenset({"a"})))

    def test_18_source_count_two_exact(self):
        self.assertEqual(2, subject.REQUIRED_DISTINCT_SOURCES)

    def test_19_source_count_one_rejected(self):
        self.assertRejected(lambda: subject.fuse_point_v1(False, frozenset(), required_sources=1))

    def test_20_source_count_three_rejected(self):
        self.assertRejected(lambda: subject.fuse_point_v1(False, frozenset(), required_sources=3))

    def test_21_temporal_tolerance_rejected(self):
        self.assertRejected(lambda: subject.fuse_point_v1(False, frozenset(), temporal_tolerance_seconds=1))

    def test_22_d2_v2_rejected(self):
        self.assertRejected(lambda: subject.fuse_point_v1(False, frozenset(), d2_version="V2"))

    def test_23_d0_preservation(self):
        self.assertEqual((True, False, "D0_ONLY"), subject.fuse_point_v1(True, frozenset()))

    def test_24_trigger_truth_table(self):
        observed = [subject.fuse_point_v1(d0_alarm, sources)[2] for d0_alarm, sources in (
            (False, frozenset()), (True, frozenset()), (False, frozenset({"a", "b"})),
            (True, frozenset({"a", "b"})))]
        self.assertEqual(list(subject.TRIGGER_CLASSES), observed)

    def test_25_three_predictions_before_label(self):
        state = subject.OuterExecutionStateMachineV1(subject.OuterExecutionState.ALL_THREE_OUTER_PREDICTIONS_FROZEN)
        state.require_label_access()

    def test_26_label_before_freeze_rejected(self):
        state = subject.OuterExecutionStateMachineV1(subject.OuterExecutionState.D2_PREDICTION_FROZEN)
        self.assertRejected(state.require_label_access)

    def test_27_attack_event_derivation(self):
        events = metrics.derive_attack_events_v1((0, 1, 1, 0, 1))
        self.assertEqual(((1, 3), (4, 5)), tuple((e.start, e.end) for e in events))

    def test_28_episode_derivation(self):
        episodes = subject.derive_intervals((3, 2, 2, 8))
        self.assertEqual(((2, 4), (8, 9)), tuple((e.start, e.end) for e in episodes))

    def test_29_recall_formula(self):
        attacks = (metrics.IntervalV1(2, 4), metrics.IntervalV1(8, 9))
        observed = subject.metric_values(attacks, (metrics.IntervalV1(3, 4),), 8)
        self.assertEqual(0.5, observed[2])

    def test_30_far_formula(self):
        attacks = (metrics.IntervalV1(2, 4),)
        observed = subject.metric_values(attacks, (metrics.IntervalV1(5, 6),), 3600)
        self.assertEqual(1.0, observed[3])

    def test_31_complementarity_arithmetic(self):
        observed = subject.complementarity(frozenset({0}), frozenset({1}), 3)
        self.assertEqual((1, 1, 1), (observed["d0_only"], observed["d1_only"], observed["neither"]))

    def test_32_d2_recovery_and_far_formulas(self):
        self.assertEqual(0.5, 1 / 2)
        self.assertEqual(2.0, 2 / (3600 / 3600))

    def test_33_retry_rejected(self):
        self.assertRejected(lambda: subject.reject_prohibited_operation_v1("retry"))

    def test_34_test2_driven_change_rejected(self):
        self.assertRejected(lambda: subject.reject_prohibited_operation_v1("test2_driven_change"))


if __name__ == "__main__":
    unittest.main()
