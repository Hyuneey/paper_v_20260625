from __future__ import annotations

import ast
from dataclasses import replace
import io
from pathlib import Path
import unittest
from contextlib import redirect_stderr, redirect_stdout

from paperworks.v6 import task039e3_r2r_d2_v2_execution_authorization_v1 as subject


ROOT = Path(__file__).resolve().parents[1]
INDEPENDENT_ATTACK_COUNT = 30


class D2V2ExecutionAuthorizationIndependentTests(unittest.TestCase):
    def setUp(self) -> None:
        subject._ISSUED_PREFLIGHTS.clear()
        subject._ISSUED_AUTHORIZATIONS.clear()
        subject._ISSUED_HORIZON_RECEIPTS.clear()

    def _authorization(self):
        preflight = subject.build_synthetic_d2_v2_execution_custody_preflight_receipt_v1()
        auth = subject.issue_d2_v2_inner_execution_authorization_v1(preflight)
        return preflight, auth

    def test_thirty_independent_authorization_attacks_are_rejected(self) -> None:
        preflight, auth = self._authorization()
        attacks = (
            ("alternate_v2_design", replace(auth, design_hash="0" * 64)),
            ("v1_design_substituted", replace(auth, design_hash=auth.d2_v1_design_hash)),
            ("d0_substitution", replace(auth, d0_prediction_hash="1" * 64)),
            ("d1_substitution", replace(auth, d1_prediction_hash="2" * 64)),
            ("source_map_substitution", replace(auth, source_map_hash="3" * 64)),
            ("horizon_map_substitution", replace(auth, native_horizon_map_hash="4" * 64)),
            ("diagnostic_gap_window_2", replace(auth, fixed_global_temporal_window=2)),
            ("diagnostic_gap_window_169", replace(auth, fixed_global_temporal_window=169)),
            ("generic_window", replace(auth, fixed_temporal_window_override_authorized=True)),
            ("token_backdating", replace(auth, backdating_allowed=True)),
            ("source_count_1", replace(auth, required_distinct_source_count=1)),
            ("source_count_3", replace(auth, required_distinct_source_count=3)),
            ("single_source_fallback", replace(auth, single_source_fallback=True)),
            ("single_source_fallback_authorized", replace(auth, single_source_fallback_authorized=True)),
            ("same_second_exclusion", replace(auth, trigger_classes=("NONE", "D0_ONLY", "RULE_RECOVERY_NATIVE_HORIZON"))),
            ("d0_suppression", replace(auth, d0_preservation_policy="D0_SUPPRESSION_ALLOWED")),
            ("d0_score_gating", replace(auth, d0_score_access_authorized=True)),
            ("rule_reevaluation", replace(auth, rule_reevaluation_authorized=True)),
            ("label_aware_fusion", replace(auth, label_before_combined_prediction_authorized=True)),
            ("test1_feature_access", replace(auth, test1_feature_access_authorized=True)),
            ("test2", replace(auth, test2_authorized=True)),
            ("outer", replace(auth, outer_authorized=True)),
            ("caller_policy", replace(auth, fusion_change_authorized=True)),
            ("policy_search", replace(auth, alternative_policy_search_authorized=True)),
            ("horizon_override", replace(auth, horizon_override_authorized=True)),
            ("d0_rerun", replace(auth, d0_rerun_authorized=True)),
            ("d1_rerun", replace(auth, d1_rerun_authorized=True)),
            ("wrong_record_count", replace(auth, future_record_count=53999)),
            ("wrong_execution_order", replace(auth, future_execution_order=tuple(reversed(auth.future_execution_order)))),
            ("result_driven_change", replace(auth, result_driven_changes=True)),
        )
        self.assertEqual(len(attacks), INDEPENDENT_ATTACK_COUNT)
        accepted: list[str] = []
        for name, attack in attacks:
            try:
                subject.validate_d2_v2_inner_execution_authorization_v1(attack, preflight)
            except subject.D2V2ExecutionAuthorizationError:
                continue
            accepted.append(name)
        self.assertEqual(accepted, [])

    def test_horizon_plus_one_multiplier_and_origin_mutations_are_rejected(self) -> None:
        receipt = subject.build_d2_v2_native_horizon_authority_receipt_v1()
        mutations = (
            replace(receipt, native_horizon_map_hash="a" * 64),
            replace(receipt, native_horizon_map_hash="b" * 64),
            replace(receipt, test1_derived_horizon_count=1),
            replace(receipt, label_derived_horizon_count=1),
        )
        accepted = 0
        for mutation in mutations:
            try:
                subject.validate_d2_v2_native_horizon_authority_receipt_v1(mutation)
            except subject.D2V2ExecutionAuthorizationError:
                continue
            accepted += 1
        self.assertEqual(accepted, 0)

    def test_raw_path_disclosure_attack_is_path_free(self) -> None:
        token = "UNIQUE_PRIVATE_PATH_TOKEN_FOR_INDEPENDENT_ATTACK"
        stdout, stderr = io.StringIO(), io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            try:
                subject._raise_sanitized_custody_failure_v1(PermissionError(token))
            except subject.D2V2ExecutionAuthorizationError as error:
                visible = repr(error) + str(error) + stdout.getvalue() + stderr.getvalue()
            else:
                self.fail("permission attack unexpectedly accepted")
        self.assertNotIn(token, visible)

    def test_static_boundary_has_no_controller_or_scientific_oracle(self) -> None:
        path = ROOT / "src/paperworks/v6/task039e3_r2r_d2_v2_execution_authorization_v1.py"
        tree = ast.parse(path.read_text(encoding="utf-8"))
        imports = {
            alias.name
            for node in ast.walk(tree)
            if isinstance(node, (ast.Import, ast.ImportFrom))
            for alias in node.names
        }
        calls = {
            node.func.id if isinstance(node.func, ast.Name) else node.func.attr
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, (ast.Name, ast.Attribute))
        }
        forbidden = {
            "task039e3_r2r_d2_inner_execution_v1",
            "task039e3_r2r_d2_inner_execution_recovery_v1",
            "fuse_synthetic_native_horizon_timeline_v1",
            "build_synthetic_causal_tokens_v1",
            "execute_authorized_d2_inner_v1",
            "compute_metric_values_v1",
        }
        self.assertFalse((imports | calls) & forbidden)


if __name__ == "__main__":
    unittest.main()
