from __future__ import annotations

from dataclasses import replace
import inspect
import unittest

from paperworks.v6 import task039e3_r2r_outer_d0_d1_d2v1_execution_recovery_v1 as subject


class OuterRecoveryIndependentAuditTests(unittest.TestCase):
    def rejected(self, callback) -> None:
        with self.assertRaises(subject.OuterExecutionError):
            callback()

    def grant(self):
        return subject.issue_committed_outer_execution_grant_v1()

    def test_01_original_authorization_substitution(self):
        self.rejected(lambda: subject.validate_grant(replace(self.grant(), authorization_sha256="0" * 64)))

    def test_02_compatibility_receipt_substitution(self):
        documents = subject.validate_r2_infrastructure_authority_v1()
        self.assertNotEqual("0" * 64, documents["compatibility"])
        self.assertEqual(subject.R2_COMPATIBILITY_SHA256, documents["compatibility"])

    def test_03_d0_model_substitution(self):
        self.rejected(lambda: subject.validate_grant(replace(self.grant(), d0_model_sha256="0" * 64)))

    def test_04_d0_threshold_substitution(self):
        self.rejected(lambda: subject.validate_grant(replace(self.grant(), d0_threshold_sha256="0" * 64)))

    def test_05_d1_portfolio_mutation(self):
        self.rejected(lambda: subject.validate_grant(replace(self.grant(), d1_relation_count=41)))

    def test_06_evaluator_mutation(self):
        self.rejected(lambda: subject.validate_grant(replace(self.grant(), d1_evaluator_identity="0" * 64)))

    def test_07_d2_v2_substitution(self):
        self.rejected(lambda: subject.fuse_point_v1(False, frozenset(), d2_version="V2"))

    def test_08_source_map_substitution(self):
        self.rejected(lambda: subject.validate_grant(replace(self.grant(), source_map_sha256="0" * 64)))

    def test_09_source_count_one(self):
        self.rejected(lambda: subject.fuse_point_v1(False, frozenset({"a", "b"}), required_sources=1))

    def test_10_source_count_three(self):
        self.rejected(lambda: subject.fuse_point_v1(False, frozenset({"a", "b"}), required_sources=3))

    def test_11_temporal_tolerance(self):
        self.rejected(lambda: subject.fuse_point_v1(False, frozenset({"a", "b"}), temporal_tolerance_seconds=2))

    def test_12_d0_score_gating(self):
        self.rejected(lambda: subject.reject_prohibited_operation_v1("d0_score_gate"))

    def test_13_label_aware_prediction(self):
        self.rejected(lambda: subject.reject_prohibited_operation_v1("label_aware_fusion"))

    def test_14_test2_label_early_access(self):
        state = subject.OuterExecutionStateMachineV1(subject.OuterExecutionState.D1_PREDICTION_FROZEN)
        self.rejected(state.require_label_access)

    def test_15_test2_retry_and_second_attempt(self):
        ledger = subject.RecoveryAttemptBoundaryV1()
        ledger.begin_immediately_before_feature_access()
        self.rejected(ledger.reject_retry)
        self.rejected(ledger.begin_immediately_before_feature_access)

    def test_16_raw_path_leak(self):
        self.rejected(lambda: subject.assert_path_free_surfaces_v1(
            ("stdout PRIVATE_LOCATOR", "stderr", "exception"), ("PRIVATE_LOCATOR",)))

    def test_17_result_driven_change(self):
        self.rejected(lambda: subject.reject_prohibited_operation_v1("test2_driven_change"))
        self.rejected(lambda: subject.reject_prohibited_operation_v1("post_outer_redesign"))

    def test_18_caller_selected_scientific_policy_is_absent(self):
        self.assertEqual(0, len(inspect.signature(subject.execute_authorized_outer_recovery_v1).parameters))
        self.assertEqual(("INFRASTRUCTURE_LOCAL_BINDING_ADAPTER",
                          "PRIVATE_PATH_REDACTION_ADAPTER",
                          "PRE_REAL_CUSTODY_READINESS_RECEIPT_CONSUMPTION"),
                         subject.ALLOWED_IMPLEMENTATION_CHANGES)


if __name__ == "__main__":
    unittest.main()
