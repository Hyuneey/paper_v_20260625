from __future__ import annotations

import ast
from dataclasses import replace
import inspect
from pathlib import Path
import unittest
from unittest.mock import Mock, patch

from paperworks.v6 import task039e3_r2r_d2_inner_execution_recovery_v1 as recovery
from paperworks.v6 import task039e3_r2r_d2_inner_execution_v1 as original


class TestD2InnerExecutionRecoveryV1(unittest.TestCase):
    def test_exact_static_authorities(self) -> None:
        self.assertEqual(
            recovery.validate_static_recovery_boundary_v1(),
            recovery.D2_RECOVERY_EXECUTION_IMPLEMENTATION_IDENTITY,
        )
        self.assertEqual(recovery.HISTORICAL_TOTAL_ATTEMPTS, 1)
        self.assertEqual(recovery.MAXIMUM_TOTAL_ATTEMPTS, 2)
        self.assertEqual(recovery.MAXIMUM_COMPLETED_SCIENTIFIC_EXECUTIONS, 1)
        self.assertEqual(recovery.EXECUTION_MODE, "AUTHORIZED_INFRASTRUCTURE_RECOVERY_ATTEMPT")

    def test_bridge_ast_has_no_scientific_algorithm(self) -> None:
        tree = ast.parse(inspect.getsource(recovery))
        defined = {node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)}
        prohibited = {
            "fuse_point_v1", "fuse_synthetic_timeline_v1", "metric_counts_v1",
            "compute_metric_values_v1", "form_alarm_episodes_v1",
            "_build_fusion_evidence_v1", "_build_private_metric_evidence_v1",
        }
        self.assertFalse(defined & prohibited)

    def test_bridge_does_not_call_original_real_entry_or_writer(self) -> None:
        tree = ast.parse(inspect.getsource(recovery))
        attributes = {
            node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute)
        }
        self.assertNotIn("execute_authorized_d2_inner_v1", attributes)
        self.assertNotIn("_write_private_json_atomic_v1", attributes)
        self.assertNotIn("_public_result_reports_v1", attributes)
        self.assertIn("write_recovery_private_json_atomic_v1", attributes)

    def test_exact_original_scientific_calls_declared(self) -> None:
        self.assertIn("_build_fusion_evidence_v1", recovery.BRIDGE_SCIENTIFIC_CALLS)
        self.assertIn("_build_combined_prediction_v1", recovery.BRIDGE_SCIENTIFIC_CALLS)
        self.assertIn("_build_private_metric_evidence_v1", recovery.BRIDGE_SCIENTIFIC_CALLS)

    def test_semantic_differential_truth_table(self) -> None:
        cases = (
            (False, frozenset(), False, False, "NONE"),
            (True, frozenset(), False, True, "D0_ONLY"),
            (False, frozenset({"a"}), False, False, "NONE"),
            (True, frozenset({"a"}), False, True, "D0_ONLY"),
            (False, frozenset({"a", "b"}), True, True, "RULE_RECOVERY"),
            (True, frozenset({"a", "b"}), True, True, "D0_AND_RULE_CORROBORATION"),
            (False, frozenset({"a", "b", "c"}), True, True, "RULE_RECOVERY"),
            (True, frozenset({"a", "b", "c"}), True, True, "D0_AND_RULE_CORROBORATION"),
        )
        self.assertEqual(len(cases), recovery.SEMANTIC_DIFFERENTIAL_CASES)
        for d0_alarm, sources, corroborated, alarm, trigger in cases:
            self.assertEqual(
                original.fuse_point_v1(d0_alarm, sources),
                (corroborated, alarm, trigger),
            )

    def test_same_source_collapses(self) -> None:
        self.assertEqual(
            original.fuse_point_v1(False, frozenset({"same"})),
            (False, False, "NONE"),
        )

    def test_adjacent_seconds_do_not_corroborate(self) -> None:
        rows = original.fuse_synthetic_timeline_v1(
            (False, False),
            ((0, True, "relation_a"), (1, True, "relation_b")),
            {"relation_a": "source_a", "relation_b": "source_b"},
        )
        self.assertEqual(
            rows,
            ((False, "NONE", ("source_a",)), (False, "NONE", ("source_b",))),
        )

    def test_d0_preservation(self) -> None:
        for sources in (frozenset(), frozenset({"a"}), frozenset({"a", "b"})):
            self.assertTrue(original.fuse_point_v1(True, sources)[1])

    def test_private_document_self_hash_required(self) -> None:
        payload = {"artifact_type": "synthetic", "value": 1}
        valid = {**payload, "artifact_hash": original.stable_hash_v1(payload)}
        self.assertEqual(recovery._validate_private_document_v1(valid), valid["artifact_hash"])
        with self.assertRaises(recovery.D2RecoveryExecutionV1Error):
            recovery._validate_private_document_v1({**valid, "value": 2})

    def test_recovery_writer_is_used_and_hash_checked(self) -> None:
        payload = {"artifact_type": "synthetic", "value": 1}
        document = {**payload, "artifact_hash": original.stable_hash_v1(payload)}
        expected = document["artifact_hash"]
        with patch.object(
            recovery.recovery_custody, "write_recovery_private_json_atomic_v1",
            return_value=expected,
        ) as writer:
            self.assertEqual(
                recovery._persist_private_v1(Mock(), "task039e3_inner_d2_fusion_evidence_v1.json", document),
                expected,
            )
        writer.assert_called_once()

    def test_recovery_writer_hash_mismatch_fails(self) -> None:
        payload = {"artifact_type": "synthetic", "value": 1}
        document = {**payload, "artifact_hash": original.stable_hash_v1(payload)}
        with patch.object(
            recovery.recovery_custody, "write_recovery_private_json_atomic_v1",
            return_value="0" * 64,
        ), self.assertRaises(recovery.D2RecoveryExecutionV1Error):
            recovery._persist_private_v1(
                Mock(), "task039e3_inner_d2_fusion_evidence_v1.json", document
            )

    def test_label_state_gate(self) -> None:
        state = original.D2ExecutionStateMachineV1()
        with self.assertRaises(original.D2InnerExecutionV1Error):
            state.require_label_access()
        state.state = original.D2ExecutionStateV1.COMBINED_PREDICTION_FROZEN
        state.require_label_access()

    def test_persistence_failure_prevents_combined_and_label(self) -> None:
        old = (
            recovery._REAL_RECOVERY_ENTRY_ATTEMPTED,
            recovery._SCIENTIFIC_RECOVERY_ATTEMPT_STARTED,
            recovery._SCIENTIFIC_RECOVERY_COMPLETED,
        )
        recovery._REAL_RECOVERY_ENTRY_ATTEMPTED = False
        recovery._SCIENTIFIC_RECOVERY_ATTEMPT_STARTED = False
        recovery._SCIENTIFIC_RECOVERY_COMPLETED = False
        preflight = Mock(artifact_hash=recovery.RECOVERY_PREFLIGHT_HASH, _root=Mock())
        authorization = Mock(authorization_hash=recovery.RECOVERY_AUTHORIZATION_HASH)
        grant = Mock(authorization_hash=recovery.ORIGINAL_AUTHORIZATION_HASH)
        evidence_document = {"artifact_type": "x", "artifact_hash": "0" * 64}
        try:
            with patch.object(recovery, "validate_static_recovery_boundary_v1"), \
                 patch.object(recovery.recovery_custody, "perform_d2_recovery_custody_preflight_v1", return_value=preflight), \
                 patch.object(recovery.recovery_auth, "issue_d2_execution_recovery_authorization_v1", return_value=authorization), \
                 patch.object(recovery, "_validate_real_authorities_v1"), \
                 patch.object(recovery.original, "issue_committed_d2_inner_execution_grant_v1", return_value=grant), \
                 patch.object(recovery.original, "_issue_execution_token_v1", return_value=Mock()), \
                 patch.object(recovery.original, "_parse_frozen_d0_prediction_v1", return_value=Mock()), \
                 patch.object(recovery.original, "_parse_frozen_d1_prediction_v1", return_value=Mock()), \
                 patch.object(recovery.original, "_parse_frozen_source_map_v1", return_value=Mock()), \
                 patch.object(recovery.original, "_build_fusion_evidence_v1", return_value=(Mock(), evidence_document)), \
                 patch.object(recovery, "_persist_private_v1", side_effect=recovery.D2RecoveryExecutionV1Error("WRITE_DENIED")), \
                 patch.object(recovery.original, "_build_combined_prediction_v1") as combined, \
                 patch.object(recovery.original, "_load_label_custody_once_v1") as labels:
                with self.assertRaises(recovery.D2RecoveryExecutionV1Error):
                    recovery.execute_authorized_d2_inner_recovery_v1()
                combined.assert_not_called()
                labels.assert_not_called()
        finally:
            (
                recovery._REAL_RECOVERY_ENTRY_ATTEMPTED,
                recovery._SCIENTIFIC_RECOVERY_ATTEMPT_STARTED,
                recovery._SCIENTIFIC_RECOVERY_COMPLETED,
            ) = old

    def test_third_attempt_guard(self) -> None:
        old = recovery._REAL_RECOVERY_ENTRY_ATTEMPTED
        recovery._REAL_RECOVERY_ENTRY_ATTEMPTED = True
        try:
            with self.assertRaisesRegex(
                recovery.D2RecoveryExecutionV1Error, "D2_RECOVERY_THIRD_ATTEMPT_REJECTED"
            ):
                recovery.execute_authorized_d2_inner_recovery_v1()
        finally:
            recovery._REAL_RECOVERY_ENTRY_ATTEMPTED = old

    def test_metric_formula_reuses_original(self) -> None:
        interval = original.metric_policy_v1.IntervalV1
        values = original.compute_metric_values_v1(
            (interval(2, 4),),
            (),
            (interval(3, 4),),
            (interval(3, 4),),
            3600,
        )
        self.assertEqual(values["d2_recall"], 1.0)
        self.assertEqual(values["incremental_recall"], 1.0)

    def test_prohibited_operations(self) -> None:
        for operation in (
            "third_attempt", "retry", "fusion_change", "source_map_change",
            "d0_score", "d0_rerun", "d1_rerun", "rule_reevaluation",
            "label_before_prediction", "test1_feature", "test2", "outer",
        ):
            with self.assertRaises(recovery.D2RecoveryExecutionV1Error):
                recovery.reject_prohibited_recovery_operation_v1(operation)

    def test_report_accounting_language_is_transparent(self) -> None:
        source = inspect.getsource(recovery._write_recovery_reports_v1)
        for token in (
            '"historical_d2_execution_attempts": 1',
            '"recovery_d2_execution_attempts": 1',
            '"total_d2_execution_attempts": 2',
            '"aborted_infrastructure_attempts": 1',
            '"completed_scientific_executions": 1',
            '"result_driven_retries": 0',
            '"third_attempt_authorized": False',
        ):
            self.assertIn(token, source)


if __name__ == "__main__":
    unittest.main()
