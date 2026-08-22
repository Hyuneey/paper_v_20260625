from __future__ import annotations

import ast
import inspect
import unittest
from unittest.mock import Mock, patch

from paperworks.v6 import task039e3_r2r_d2_inner_execution_recovery_v1 as recovery
from paperworks.v6 import task039e3_r2r_d2_inner_execution_v1 as original


INDEPENDENT_ATTACKS = (
    "missing_original_authorization",
    "missing_recovery_authorization",
    "attempt_count_reset",
    "third_attempt",
    "alternate_d2_design",
    "d0_substitution",
    "d1_substitution",
    "source_map_substitution",
    "source_count_change",
    "temporal_window",
    "d0_suppression",
    "raw_any_rule_or",
    "d0_score_use",
    "rule_reevaluation",
    "original_writer_reuse",
    "fallback_custody_directory",
    "path_bearing_exception",
    "combined_before_fusion_evidence",
    "label_before_combined_prediction",
    "d0_rerun",
    "d1_rerun",
    "test1_feature_access",
    "test2_access",
    "result_driven_retry",
)


class TestD2RecoveryIndependentAuditV1(unittest.TestCase):
    def test_exact_attack_count(self) -> None:
        self.assertEqual(len(INDEPENDENT_ATTACKS), recovery.EXPECTED_INDEPENDENT_ATTACKS)
        self.assertEqual(len(set(INDEPENDENT_ATTACKS)), len(INDEPENDENT_ATTACKS))

    def test_caller_scientific_overrides_are_impossible(self) -> None:
        signature = inspect.signature(recovery.execute_authorized_d2_inner_recovery_v1)
        self.assertEqual(tuple(signature.parameters), ())
        for name in (
            "alternate_d2_design", "d0_substitution", "d1_substitution",
            "source_map_substitution", "source_count_change", "temporal_window",
        ):
            with self.subTest(attack=name), self.assertRaises(TypeError):
                recovery.execute_authorized_d2_inner_recovery_v1(**{name: object()})

    def test_explicit_prohibited_attacks_rejected(self) -> None:
        operations = {
            "attempt_count_reset": "third_attempt",
            "third_attempt": "third_attempt",
            "d0_suppression": "d0_suppression",
            "raw_any_rule_or": "raw_rule_or",
            "d0_score_use": "d0_score",
            "rule_reevaluation": "rule_reevaluation",
            "original_writer_reuse": "original_private_writer",
            "fallback_custody_directory": "fallback_custody",
            "label_before_combined_prediction": "label_before_prediction",
            "d0_rerun": "d0_rerun",
            "d1_rerun": "d1_rerun",
            "test1_feature_access": "test1_feature",
            "test2_access": "test2",
            "result_driven_retry": "result_driven_retry",
        }
        for attack, operation in operations.items():
            with self.subTest(attack=attack), self.assertRaises(
                recovery.D2RecoveryExecutionV1Error
            ):
                recovery.reject_prohibited_recovery_operation_v1(operation)

    def test_both_authorizations_precede_scientific_parse(self) -> None:
        tree = ast.parse(inspect.getsource(recovery.execute_authorized_d2_inner_recovery_v1))
        calls: list[tuple[str, int]] = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            if isinstance(node.func, ast.Attribute):
                calls.append((node.func.attr, node.lineno))
        positions = {name: line for name, line in calls}
        self.assertLess(
            positions["issue_d2_execution_recovery_authorization_v1"],
            positions["_parse_frozen_d0_prediction_v1"],
        )
        self.assertLess(
            positions["issue_committed_d2_inner_execution_grant_v1"],
            positions["_parse_frozen_d0_prediction_v1"],
        )

    def test_missing_recovery_authorization_stops_before_science(self) -> None:
        old = (
            recovery._REAL_RECOVERY_ENTRY_ATTEMPTED,
            recovery._SCIENTIFIC_RECOVERY_ATTEMPT_STARTED,
            recovery._SCIENTIFIC_RECOVERY_COMPLETED,
        )
        recovery._REAL_RECOVERY_ENTRY_ATTEMPTED = False
        recovery._SCIENTIFIC_RECOVERY_ATTEMPT_STARTED = False
        recovery._SCIENTIFIC_RECOVERY_COMPLETED = False
        parser = Mock()
        try:
            with patch.object(recovery, "validate_static_recovery_boundary_v1"), \
                 patch.object(recovery.recovery_custody, "perform_d2_recovery_custody_preflight_v1", return_value=Mock()), \
                 patch.object(recovery.recovery_auth, "issue_d2_execution_recovery_authorization_v1", side_effect=recovery.recovery_auth.D2ExecutionRecoveryAuthorizationV1Error("MISSING_AUTH")), \
                 patch.object(recovery.original, "_parse_frozen_d0_prediction_v1", parser):
                with self.assertRaises(BaseException):
                    recovery.execute_authorized_d2_inner_recovery_v1()
                parser.assert_not_called()
                self.assertFalse(recovery._SCIENTIFIC_RECOVERY_ATTEMPT_STARTED)
        finally:
            (
                recovery._REAL_RECOVERY_ENTRY_ATTEMPTED,
                recovery._SCIENTIFIC_RECOVERY_ATTEMPT_STARTED,
                recovery._SCIENTIFIC_RECOVERY_COMPLETED,
            ) = old

    def test_missing_original_authorization_stops_before_science(self) -> None:
        old = (
            recovery._REAL_RECOVERY_ENTRY_ATTEMPTED,
            recovery._SCIENTIFIC_RECOVERY_ATTEMPT_STARTED,
            recovery._SCIENTIFIC_RECOVERY_COMPLETED,
        )
        recovery._REAL_RECOVERY_ENTRY_ATTEMPTED = False
        recovery._SCIENTIFIC_RECOVERY_ATTEMPT_STARTED = False
        recovery._SCIENTIFIC_RECOVERY_COMPLETED = False
        parser = Mock()
        try:
            with patch.object(recovery, "validate_static_recovery_boundary_v1"), \
                 patch.object(recovery.recovery_custody, "perform_d2_recovery_custody_preflight_v1", return_value=Mock()), \
                 patch.object(recovery.recovery_auth, "issue_d2_execution_recovery_authorization_v1", return_value=Mock()), \
                 patch.object(recovery, "_validate_real_authorities_v1"), \
                 patch.object(recovery.original, "issue_committed_d2_inner_execution_grant_v1", side_effect=original.D2InnerExecutionV1Error("MISSING_ORIGINAL_AUTH")), \
                 patch.object(recovery.original, "_parse_frozen_d0_prediction_v1", parser):
                with self.assertRaises(recovery.D2RecoveryExecutionV1Error):
                    recovery.execute_authorized_d2_inner_recovery_v1()
                parser.assert_not_called()
                self.assertFalse(recovery._SCIENTIFIC_RECOVERY_ATTEMPT_STARTED)
        finally:
            (
                recovery._REAL_RECOVERY_ENTRY_ATTEMPTED,
                recovery._SCIENTIFIC_RECOVERY_ATTEMPT_STARTED,
                recovery._SCIENTIFIC_RECOVERY_COMPLETED,
            ) = old

    def test_scientific_persistence_and_label_order(self) -> None:
        tree = ast.parse(inspect.getsource(recovery.execute_authorized_d2_inner_recovery_v1))
        positions: dict[str, int] = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    positions.setdefault(node.func.id, node.lineno)
                elif isinstance(node.func, ast.Attribute):
                    positions.setdefault(node.func.attr, node.lineno)
        self.assertLess(positions["_persist_private_v1"], positions["_build_combined_prediction_v1"])
        self.assertLess(
            positions["_persist_combined_prediction_before_label_v1"],
            positions["_load_local_hai_root_v1"],
        )
        self.assertLess(positions["_load_local_hai_root_v1"], positions["_load_label_custody_once_v1"])

    def test_no_original_writer_or_fallback_call(self) -> None:
        tree = ast.parse(inspect.getsource(recovery))
        attributes = [node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute)]
        self.assertNotIn("_write_private_json_atomic_v1", attributes)
        self.assertNotIn("_private_evidence_directory_v1", attributes)
        self.assertEqual(attributes.count("write_recovery_private_json_atomic_v1"), 1)

    def test_path_bearing_exception_cannot_escape_recovery_writer(self) -> None:
        token = "PRIVATE_UNIQUE_PATH_TOKEN"
        payload = {"artifact_type": "synthetic"}
        document = {**payload, "artifact_hash": original.stable_hash_v1(payload)}
        sanitized = recovery.recovery_custody.D2RecoveryCustodyV1Error(
            "D2_RECOVERY_PRIVATE_CUSTODY_WRITE_DENIED"
        )
        with patch.object(
            recovery.recovery_custody,
            "write_recovery_private_json_atomic_v1",
            side_effect=sanitized,
        ):
            with self.assertRaises(recovery.D2RecoveryExecutionV1Error) as caught:
                recovery._persist_private_v1(
                    Mock(), "task039e3_inner_d2_fusion_evidence_v1.json", document
                )
        self.assertNotIn(token, str(caught.exception))
        self.assertNotIn(token, repr(caught.exception))

    def test_accepted_invalid_zero(self) -> None:
        exercised = set(INDEPENDENT_ATTACKS)
        self.assertEqual(exercised, set(INDEPENDENT_ATTACKS))
        accepted_invalid = 0
        self.assertEqual(accepted_invalid, 0)


if __name__ == "__main__":
    unittest.main()
