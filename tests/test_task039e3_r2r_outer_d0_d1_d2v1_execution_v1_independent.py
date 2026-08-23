from __future__ import annotations

from dataclasses import replace
import inspect
import unittest

from paperworks.v6 import task039e3_r2r_outer_d0_d1_d2v1_execution_v1 as subject


class OuterExecutionIndependentAuditTests(unittest.TestCase):
    def rejected(self, callback) -> None:
        with self.assertRaises(subject.OuterExecutionError):
            callback()

    def test_01_authorization_substitution(self):
        grant = subject.issue_committed_outer_execution_grant_v1()
        self.rejected(lambda: subject.validate_grant(replace(grant, authorization_sha256="0" * 64)))

    def test_02_test2_feature_substitution(self):
        grant = subject.issue_committed_outer_execution_grant_v1()
        self.rejected(lambda: subject.validate_grant(replace(grant, test2_feature_sha256="0" * 64)))

    def test_03_test2_label_substitution(self):
        grant = subject.issue_committed_outer_execution_grant_v1()
        self.rejected(lambda: subject.validate_grant(replace(grant, test2_label_sha256="0" * 64)))

    def test_04_d0_model_substitution(self):
        grant = subject.issue_committed_outer_execution_grant_v1()
        self.rejected(lambda: subject.validate_grant(replace(grant, d0_model_sha256="0" * 64)))

    def test_05_d0_threshold_substitution(self):
        grant = subject.issue_committed_outer_execution_grant_v1()
        self.rejected(lambda: subject.validate_grant(replace(grant, d0_threshold_sha256="0" * 64)))

    def test_06_d0_refit(self):
        self.rejected(lambda: subject.reject_prohibited_operation_v1("d0_fit"))

    def test_07_d1_portfolio_substitution(self):
        grant = subject.issue_committed_outer_execution_grant_v1()
        self.rejected(lambda: subject.validate_grant(replace(grant, d1_relation_count=41)))

    def test_08_rule_addition(self):
        self.rejected(lambda: subject.reject_prohibited_operation_v1("rule_add"))

    def test_09_rule_deletion(self):
        self.rejected(lambda: subject.reject_prohibited_operation_v1("rule_delete"))

    def test_10_numeric_mutation(self):
        self.rejected(lambda: subject.reject_prohibited_operation_v1("threshold_mutation"))

    def test_11_evaluator_mutation(self):
        grant = subject.issue_committed_outer_execution_grant_v1()
        self.rejected(lambda: subject.validate_grant(replace(grant, d1_evaluator_identity="0" * 64)))

    def test_12_d2_v2_substitution(self):
        self.rejected(lambda: subject.fuse_point_v1(False, frozenset(), d2_version="V2"))

    def test_13_source_map_substitution(self):
        grant = subject.issue_committed_outer_execution_grant_v1()
        self.rejected(lambda: subject.validate_grant(replace(grant, source_map_sha256="0" * 64)))

    def test_14_source_count_change(self):
        self.rejected(lambda: subject.fuse_point_v1(False, frozenset({"a", "b"}), required_sources=3))

    def test_15_time_tolerance_insertion(self):
        self.rejected(lambda: subject.fuse_point_v1(False, frozenset({"a", "b"}), temporal_tolerance_seconds=2))

    def test_16_d0_score_gating(self):
        self.rejected(lambda: subject.reject_prohibited_operation_v1("d0_score_gate"))

    def test_17_label_aware_d1(self):
        self.rejected(lambda: subject.reject_prohibited_operation_v1("label_aware_fusion"))

    def test_18_label_aware_d2(self):
        self.rejected(lambda: subject.reject_prohibited_operation_v1("label_aware_fusion"))

    def test_19_d0_suppression_impossible(self):
        self.assertTrue(subject.fuse_point_v1(True, frozenset())[0])

    def test_20_prediction_mutation_after_freeze(self):
        document = subject.compact_prediction("OuterD0PredictionV1", (1,))
        document["alarm_true_indices"] = [2]
        self.rejected(lambda: subject.expand_compact_prediction(document))

    def test_21_label_before_one_prediction_freeze(self):
        state = subject.OuterExecutionStateMachineV1(subject.OuterExecutionState.D1_PREDICTION_FROZEN)
        self.rejected(state.require_label_access)

    def test_22_label_before_durable_reopen(self):
        state = subject.OuterExecutionStateMachineV1(subject.OuterExecutionState.D2_PREDICTION_FROZEN)
        self.rejected(state.require_label_access)

    def test_23_metric_policy_mutation(self):
        self.assertEqual(("ATTACK_EVENT_RECALL", "NORMAL_FAR_EPISODES_PER_HOUR"),
                         subject.outer_auth.PRIMARY_METRICS)

    def test_24_second_attempt_and_result_retry(self):
        self.rejected(lambda: subject.reject_prohibited_operation_v1("retry"))

    def test_25_result_driven_retry_and_post_redesign(self):
        self.rejected(lambda: subject.reject_prohibited_operation_v1("test2_driven_change"))
        self.rejected(lambda: subject.reject_prohibited_operation_v1("post_outer_redesign"))

    def test_26_private_path_leak_surface_is_redacted(self):
        source = inspect.getsource(subject.OuterExecutionError)
        self.assertNotIn("resolve(", source)
        error = subject.OuterExecutionError("not-safe")
        self.assertEqual("OUTER_EXECUTION_UNEXPECTED", str(error))


if __name__ == "__main__":
    unittest.main()
