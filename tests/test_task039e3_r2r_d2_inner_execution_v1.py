from __future__ import annotations

import copy
from dataclasses import replace
import inspect
import unittest

from paperworks.v6 import task039e3_r2r_d2_inner_execution_v1 as subject
from paperworks.v6 import task039e3_r2r_utility_evaluator_metrics_v1 as metric_policy


def _record(index: int, alarm: bool, trigger: str) -> subject.ScientificCombinedPredictionRecordV1:
    identity = subject._combined_decision_identity_v1(index, alarm, trigger)
    return subject.ScientificCombinedPredictionRecordV1(index, alarm, trigger, identity)


class TestTask039E3R2RD2InnerExecutionV1(unittest.TestCase):
    def test_01_committed_authorization_replay_and_factory_custody(self) -> None:
        grant = subject.issue_committed_d2_inner_execution_grant_v1()
        self.assertEqual(subject.validate_committed_d2_inner_execution_grant_v1(grant), grant.grant_hash)
        with self.assertRaises(subject.D2InnerExecutionV1Error):
            copy.deepcopy(grant)
        forged = replace(grant)
        with self.assertRaises(subject.D2InnerExecutionV1Error):
            subject.validate_committed_d2_inner_execution_grant_v1(forged)
        reconstructed = subject.CommittedD2InnerExecutionGrantV1(**grant.__dict__)
        with self.assertRaises(subject.D2InnerExecutionV1Error):
            subject.validate_committed_d2_inner_execution_grant_v1(reconstructed)

    def test_02_exact_authorities_and_no_scientific_knobs(self) -> None:
        self.assertEqual(subject.D2_DESIGN_HASH, "eb559a91350fd046204d223d6820ef7f0590ad4beb7a2b17114a496859758e51")
        self.assertEqual(subject.D0_PREDICTION_HASH, "a4b58f1c78b9bb53125da1a009f3fd05b02e1c83a789772a341a7679fddca0f6")
        self.assertEqual(subject.D1_PREDICTION_HASH, "58c3c49f9657f68d35c830b12eeb493ce4bbf7669c90f04813fb80246c3c2682")
        self.assertEqual(subject.SOURCE_MAP_HASH, "f866176000c3d5a943053ac3125d2700b0b72f25b5a0539d8f4713435a959818")
        self.assertEqual(len(inspect.signature(subject.execute_authorized_d2_inner_v1).parameters), 0)

    def test_03_point_truth_table_and_d0_preservation(self) -> None:
        cases = (
            (False, frozenset(), (False, False, "NONE")),
            (True, frozenset(), (False, True, "D0_ONLY")),
            (False, frozenset({"A", "B"}), (True, True, "RULE_RECOVERY")),
            (True, frozenset({"A", "B"}), (True, True, "D0_AND_RULE_CORROBORATION")),
        )
        for d0, sources, expected in cases:
            self.assertEqual(subject.fuse_point_v1(d0, sources), expected)
            if d0:
                self.assertTrue(subject.fuse_point_v1(d0, sources)[1])

    def test_04_same_source_duplicates_count_once(self) -> None:
        result = subject.fuse_synthetic_timeline_v1(
            (False,), ((0, True, "r1"), (0, True, "r2")),
            {"r1": "SOURCE_A", "r2": "SOURCE_A"},
        )
        self.assertEqual(result, ((False, "NONE", ("SOURCE_A",)),))

    def test_05_two_distinct_sources_exact_same_second(self) -> None:
        result = subject.fuse_synthetic_timeline_v1(
            (False,), ((0, True, "r1"), (0, True, "r2")),
            {"r1": "SOURCE_A", "r2": "SOURCE_B"},
        )
        self.assertEqual(result, ((True, "RULE_RECOVERY", ("SOURCE_A", "SOURCE_B")),))

    def test_06_adjacent_seconds_do_not_corroborate(self) -> None:
        result = subject.fuse_synthetic_timeline_v1(
            (False, False), ((0, True, "r1"), (1, True, "r2")),
            {"r1": "SOURCE_A", "r2": "SOURCE_B"},
        )
        self.assertEqual(tuple(item[:2] for item in result), ((False, "NONE"), (False, "NONE")))

    def test_07_missing_source_mapping_fails_closed(self) -> None:
        with self.assertRaises(subject.D2InnerExecutionV1Error):
            subject.fuse_synthetic_timeline_v1((False,), ((0, True, "foreign"),), {})

    def test_08_combined_prediction_record_closure_and_label_blindness(self) -> None:
        records = tuple(_record(index, False, "NONE") for index in range(54_000))
        subject.validate_combined_prediction_records_v1(records, 54_000)
        self.assertEqual(set(records[0].to_public_dict()), subject.COMBINED_RECORD_KEYS)
        self.assertFalse(any("label" in key.lower() for key in records[0].to_public_dict()))
        with self.assertRaises(subject.D2InnerExecutionV1Error):
            subject.validate_combined_prediction_records_v1(records[:-1], 54_000)

    def test_09_combined_record_state_contradictions_rejected(self) -> None:
        invalid = (_record(0, True, "NONE"),)
        with self.assertRaises(subject.D2InnerExecutionV1Error):
            subject.validate_combined_prediction_records_v1(invalid, 1)
        invalid = (_record(1, False, "NONE"),)
        with self.assertRaises(subject.D2InnerExecutionV1Error):
            subject.validate_combined_prediction_records_v1(invalid, 1)

    def test_10_label_before_combined_prediction_freeze_rejected(self) -> None:
        state = subject.D2ExecutionStateMachineV1()
        with self.assertRaises(subject.D2InnerExecutionV1Error):
            state.require_label_access()
        state.state = subject.D2ExecutionStateV1.COMBINED_PREDICTION_FROZEN
        state.require_label_access()

    def test_11_episode_formation_for_d2_d0_and_recovery(self) -> None:
        expected = (
            metric_policy.IntervalV1(1, 3), metric_policy.IntervalV1(5, 6)
        )
        self.assertEqual(metric_policy.form_alarm_episodes_v1((1, 2, 5)), expected)
        self.assertEqual(metric_policy.form_alarm_episodes_v1((5, 2, 1)), expected)
        self.assertEqual(metric_policy.form_alarm_episodes_v1((1, 1, 2, 5)), expected)

    def test_12_attack_event_formation(self) -> None:
        self.assertEqual(
            metric_policy.derive_attack_events_v1((0, 1, 1, 0, 1)),
            (metric_policy.IntervalV1(1, 3), metric_policy.IntervalV1(4, 5)),
        )

    def test_13_primary_and_incremental_metric_arithmetic(self) -> None:
        attacks = (metric_policy.IntervalV1(2, 4), metric_policy.IntervalV1(8, 10))
        d0 = (metric_policy.IntervalV1(2, 3), metric_policy.IntervalV1(5, 6))
        recovery = (metric_policy.IntervalV1(8, 9), metric_policy.IntervalV1(12, 13))
        d2 = (metric_policy.IntervalV1(2, 3), metric_policy.IntervalV1(5, 6),
              metric_policy.IntervalV1(8, 9), metric_policy.IntervalV1(12, 13))
        values = subject.compute_metric_values_v1(attacks, d0, d2, recovery, 3600)
        self.assertEqual(values["d2_recall"], 1.0)
        self.assertEqual(values["d2_far"], 2.0)
        self.assertEqual(values["d0_missed_recovery"], 1.0)
        self.assertEqual(values["incremental_recall"], 0.5)
        self.assertEqual(values["added_recovery_far"], 1.0)
        self.assertEqual(values["incremental_far"], 1.0)

    def test_14_undefined_metrics(self) -> None:
        values = subject.compute_metric_values_v1((), (), (), (), 0)
        self.assertTrue(all(value is None for value in values.values()))

    def test_15_added_far_can_differ_from_incremental_far_due_to_merge(self) -> None:
        attacks: tuple[metric_policy.IntervalV1, ...] = ()
        d0 = (metric_policy.IntervalV1(1, 2),)
        recovery = (metric_policy.IntervalV1(2, 3),)
        d2 = (metric_policy.IntervalV1(1, 3),)
        values = subject.compute_metric_values_v1(attacks, d0, d2, recovery, 3600)
        self.assertEqual(values["added_recovery_far"], 1.0)
        self.assertEqual(values["incremental_far"], 0.0)

    def test_16_differential_six_case_oracle(self) -> None:
        cases = (
            ((False,), ((0, True, "a"),), {"a": "A"}, (False, "NONE")),
            ((False,), ((0, True, "a"), (0, True, "b")), {"a": "A", "b": "A"}, (False, "NONE")),
            ((False,), ((0, True, "a"), (0, True, "b")), {"a": "A", "b": "B"}, (True, "RULE_RECOVERY")),
            ((True,), (), {}, (True, "D0_ONLY")),
            ((True,), ((0, True, "a"), (0, True, "b")), {"a": "A", "b": "B"}, (True, "D0_AND_RULE_CORROBORATION")),
            ((False, False), ((0, True, "a"), (1, True, "b")), {"a": "A", "b": "B"}, (False, "NONE")),
        )
        divergences = 0
        for d0, d1, mapping, expected_first in cases:
            actual = subject.fuse_synthetic_timeline_v1(d0, d1, mapping)
            if actual[0][:2] != expected_first:
                divergences += 1
        self.assertEqual(len(cases), subject.DIFFERENTIAL_CASES)
        self.assertEqual(divergences, 0)

    def test_17_prohibited_dependencies_and_execution_paths(self) -> None:
        operations = (
            "d0_rerun", "d1_rerun", "d0_score_access", "d1_rule_reevaluation",
            "d1_metric_read", "test1_feature_access", "test2", "outer", "retry",
            "fusion_change", "fusion_candidate_search", "result_driven_change",
        )
        for operation in operations:
            with self.assertRaises(subject.D2InnerExecutionV1Error):
                subject.reject_prohibited_operation_v1(operation)


if __name__ == "__main__":
    unittest.main()
