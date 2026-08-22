from __future__ import annotations

import copy
from dataclasses import replace
from pathlib import Path
import tempfile
import unittest

from paperworks.v6 import task039e3_r2r_d2_execution_recovery_authorization_v1 as a
from paperworks.v6 import task039e3_r2r_d2_execution_recovery_custody_v1 as c


class D2RecoveryAuthorizationV1Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.temp = tempfile.TemporaryDirectory()
        base = Path(cls.temp.name)
        repo, private = base / "repo", base / "private"
        repo.mkdir(); private.mkdir()
        root = c._issue_synthetic_recovery_root_v1(private, repo)
        cls.preflight = c._build_synthetic_preflight_v1(root)
        cls.authorization = a._issue_synthetic_recovery_authorization_v1(cls.preflight)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.temp.cleanup()

    def test_public_authority_replay(self) -> None:
        replay = a.replay_d2_recovery_public_authorities_v1()
        self.assertTrue(replay.d2_design_hash_match)
        self.assertTrue(replay.original_implementation_unchanged)
        self.assertTrue(replay.d0_prediction_unchanged)
        self.assertTrue(replay.d1_prediction_unchanged)

    def test_exact_version_scope_and_hashes(self) -> None:
        value = self.authorization
        self.assertEqual(a.D2_EXECUTION_RECOVERY_AUTHORIZATION_VERSION, value.authorization_version)
        self.assertEqual(a.D2_EXECUTION_RECOVERY_AUTHORIZATION_SCOPE, value.authorization_scope)
        self.assertEqual(a.D2_DESIGN_HASH, value.original_d2_design_hash)
        self.assertEqual(a.D0_PREDICTION_HASH, value.d0_prediction_hash)
        self.assertEqual(a.D1_PREDICTION_HASH, value.d1_prediction_hash)
        self.assertEqual(a.SOURCE_MAP_HASH, value.source_map_hash)

    def test_transparent_attempt_accounting(self) -> None:
        value = self.authorization
        self.assertEqual(1, value.historical_total_execution_attempts)
        self.assertEqual(1, value.historical_aborted_infrastructure_attempts)
        self.assertEqual(0, value.historical_completed_scientific_executions)
        self.assertEqual(0, value.historical_result_driven_retries)
        self.assertEqual(1, value.authorized_additional_recovery_attempts)
        self.assertEqual(2, value.maximum_future_total_execution_attempts)
        self.assertEqual(1, value.maximum_future_completed_scientific_executions)
        self.assertEqual(0, value.result_driven_retries_authorized)

    def test_scientific_semantics_immutable(self) -> None:
        value = self.authorization
        self.assertEqual(2, value.required_distinct_source_count)
        self.assertEqual("EXACT_DECISION_PHYSICAL_ROW_INDEX_EQUALITY", value.same_second_policy)
        self.assertEqual("EVERY_FROZEN_D0_ALARM_IS_A_D2_ALARM", value.d0_preservation_policy)
        forbidden = [
            value.d2_design_change_authorized, value.fusion_change_authorized,
            value.source_map_change_authorized, value.corroboration_count_change_authorized,
            value.temporal_policy_change_authorized, value.d0_prediction_change_authorized,
            value.d1_prediction_change_authorized,
        ]
        self.assertTrue(value.d2_recovery_execution_authorized)
        self.assertTrue(all(item is False for item in forbidden))

    def test_prohibited_authorities_false(self) -> None:
        value = self.authorization
        forbidden = [
            value.d0_rerun_authorized, value.d1_rerun_authorized,
            value.d0_score_access_authorized, value.rule_reevaluation_authorized,
            value.label_before_combined_prediction_authorized,
            value.test1_feature_access_authorized, value.test2_authorized,
            value.outer_authorized, value.result_driven_retry_authorized,
        ]
        self.assertTrue(all(item is False for item in forbidden))

    def test_factory_custody_rejects_reconstruction_copy_replace(self) -> None:
        value = self.authorization
        forged = replace(value)
        with self.assertRaises(a.D2ExecutionRecoveryAuthorizationV1Error):
            a.validate_d2_execution_recovery_authorization_v1(forged, self.preflight)
        with self.assertRaises(a.D2ExecutionRecoveryAuthorizationV1Error):
            copy.deepcopy(value)

    def test_self_rehash_wrong_semantics_rejected(self) -> None:
        forged = replace(self.authorization, maximum_future_total_execution_attempts=3)
        forged = replace(forged, authorization_hash=c.stable_hash_v1(forged._payload()))
        with self.assertRaises(a.D2ExecutionRecoveryAuthorizationV1Error):
            a.validate_d2_execution_recovery_authorization_v1(forged, self.preflight)

    def test_exact_existing_authorization_validates(self) -> None:
        self.assertEqual(
            self.authorization.authorization_hash,
            a.validate_d2_execution_recovery_authorization_v1(
                self.authorization, self.preflight,
            ),
        )

    def test_future_order_freezes_combined_before_labels(self) -> None:
        order = self.authorization.future_execution_order
        self.assertLess(order.index("FREEZE_COMBINED_PREDICTION"),
                        order.index("PARSE_LABELS_AFTER_COMBINED_PREDICTION_FREEZE"))


if __name__ == "__main__":
    unittest.main()
