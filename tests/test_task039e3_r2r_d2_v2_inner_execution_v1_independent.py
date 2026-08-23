from __future__ import annotations

import ast
from dataclasses import replace
from pathlib import Path
import subprocess
import unittest

from paperworks.v6 import task039e3_r2r_d2_v2_inner_execution_v1 as execution


class D2V2InnerExecutionV1IndependentTests(unittest.TestCase):
    def _rejects(self, action: object) -> bool:
        try:
            action()  # type: ignore[operator]
        except execution.D2V2InnerExecutionV1Error:
            return True
        return False

    def test_01_exactly_34_independent_mutations_are_rejected(self) -> None:
        grant = execution.issue_committed_d2_v2_inner_execution_grant_v1()
        token = execution.build_evidence_tokens_v1(
            ((2, True, "r"),), (("r", "s"),), (("r", 1),), 6
        )[0]
        caller_grant = execution.CommittedD2V2InnerExecutionGrantV1(**grant.__dict__)
        reconstructed_token = execution._D2V2ExecutionTokenV1(
            grant.grant_hash, execution.D2_V2_INNER_EXECUTION_VERSION, object()
        )
        invalid_interval = replace(token, start_physical_row_index=1)
        expired_before_start = replace(token, expiry_physical_row_index=1)
        record = execution.ScientificCombinedPredictionRecordV2(
            0, False, "NONE", execution._combined_identity_v1(0, False, "NONE")
        )
        attacks = [
            lambda: execution.validate_committed_d2_v2_inner_execution_grant_v1(caller_grant),
            lambda: execution.validate_committed_d2_v2_inner_execution_grant_v1(replace(grant, d2_v2_design_hash="0" * 64)),
            lambda: execution.validate_committed_d2_v2_inner_execution_grant_v1(replace(grant, d0_prediction_hash="1" * 64)),
            lambda: execution.validate_committed_d2_v2_inner_execution_grant_v1(replace(grant, d1_prediction_hash="2" * 64)),
            lambda: execution.validate_committed_d2_v2_inner_execution_grant_v1(replace(grant, source_map_hash="3" * 64)),
            lambda: execution.validate_committed_d2_v2_inner_execution_grant_v1(replace(grant, native_horizon_map_hash="4" * 64)),
            lambda: execution.reject_prohibited_operation_v1("horizon_override"),
            lambda: execution.reject_prohibited_operation_v1("horizon_multiplier"),
            lambda: execution.fuse_native_horizon_timeline_v1((False,) * 6, (invalid_interval,)),
            lambda: execution.fuse_native_horizon_timeline_v1((False,) * 6, (expired_before_start,)),
            lambda: execution.reject_prohibited_operation_v1("source_count_change"),
            lambda: execution.validate_committed_d2_v2_inner_execution_grant_v1(replace(grant, required_distinct_source_count=3)),
            lambda: execution.reject_prohibited_operation_v1("single_source_fallback"),
            lambda: execution.reject_prohibited_operation_v1("exact_same_second_exclusion"),
            lambda: execution.reject_prohibited_operation_v1("d0_suppression"),
            lambda: execution.reject_prohibited_operation_v1("raw_rule_or"),
            lambda: execution.reject_prohibited_operation_v1("d0_score"),
            lambda: execution.reject_prohibited_operation_v1("d0_rerun"),
            lambda: execution.reject_prohibited_operation_v1("d1_rerun"),
            lambda: execution.reject_prohibited_operation_v1("d2_v1_rerun"),
            lambda: execution.reject_prohibited_operation_v1("rule_reevaluation"),
            lambda: execution.D2V2ExecutionStateMachineV1().require_label_access(),
            lambda: execution.reject_prohibited_operation_v1("test1_feature"),
            lambda: execution.reject_prohibited_operation_v1("test2"),
            lambda: execution.reject_prohibited_operation_v1("outer"),
            lambda: execution.reject_prohibited_operation_v1("second_execution"),
            lambda: execution.reject_prohibited_operation_v1("retry"),
            lambda: execution.reject_prohibited_operation_v1("result_driven_change"),
            lambda: execution.reject_prohibited_operation_v1("private_source_set_exposure"),
            lambda: execution.reject_prohibited_operation_v1("private_path_exposure"),
            lambda: execution.reject_prohibited_operation_v1("alternate_policy"),
            lambda: execution._validate_execution_token_v1(reconstructed_token),
            lambda: execution.validate_combined_prediction_records_v1((), 1),
            lambda: execution.validate_combined_prediction_records_v1((replace(record, trigger_class="D0_ONLY"),), 1),
        ]
        self.assertEqual(len(attacks), execution.EXPECTED_INDEPENDENT_ATTACKS)
        rejected = sum(self._rejects(action) for action in attacks)
        self.assertEqual(rejected, 34)
        self.assertEqual(34 - rejected, 0)

    def test_02_static_controller_and_input_boundary(self) -> None:
        source = Path(execution.__file__).read_text(encoding="utf-8")
        tree = ast.parse(source)
        imported_modules = {
            alias.name
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        }
        imported_from = {
            node.module
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.module
        }
        all_imports = imported_modules | imported_from
        self.assertFalse(any(name.endswith("task039e3_r2r_d0_inner_execution_v1") for name in all_imports))
        self.assertFalse(any(name.endswith("task039e3_r2r_d1_inner_execution_v1") for name in all_imports))
        self.assertFalse(any(name.endswith("task039e3_r2r_d2_inner_execution_recovery_v1") for name in all_imports))
        function = next(
            node for node in tree.body
            if isinstance(node, ast.FunctionDef) and node.name == "execute_authorized_d2_v2_inner_v1"
        )
        self.assertEqual(len(function.args.args), 0)
        self.assertIsNone(function.args.vararg)
        self.assertIsNone(function.args.kwarg)

    def test_03_production_source_is_frozen_at_commit_a(self) -> None:
        root = Path(execution.__file__).resolve().parents[3]
        relative = "src/paperworks/v6/task039e3_r2r_d2_v2_inner_execution_v1.py"
        head_source = subprocess.run(
            ["git", "show", f"HEAD:{relative}"], cwd=root, check=True,
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
        ).stdout
        self.assertEqual(head_source, Path(execution.__file__).read_bytes())

    def test_04_no_old_v1_result_targets_or_fallback_writer(self) -> None:
        source = Path(execution.__file__).read_text(encoding="utf-8")
        self.assertNotIn("TASK-039E3_R2R_UTILITY_INNER_D2_COMBINED_PREDICTION_ARTIFACT_V1.json", source)
        self.assertNotIn("TASK-039E3_R2R_UTILITY_INNER_D2_METRICS_V1.json", source)
        self.assertNotIn("_write_private_json_atomic_v1", source)
        self.assertNotIn("_private_evidence_directory_v1", source)
        self.assertIn("_atomic_write_bytes_v1", source)

    def test_05_public_record_schema_excludes_private_and_label_fields(self) -> None:
        self.assertEqual(
            execution.COMBINED_RECORD_KEYS,
            frozenset({"physical_row_index", "d2_v2_alarm_emitted", "trigger_class", "combined_decision_identity"}),
        )
        forbidden = {"label", "attack", "d0_score", "active_sources", "native_horizon_seconds"}
        self.assertFalse(forbidden & execution.COMBINED_RECORD_KEYS)


if __name__ == "__main__":
    unittest.main()
