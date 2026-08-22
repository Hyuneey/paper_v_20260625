from __future__ import annotations

import ast
from dataclasses import replace
import io
from pathlib import Path
import unittest
from contextlib import redirect_stderr, redirect_stdout

from paperworks.v6 import task039e3_r2r_d2_v2_execution_authorization_v1 as subject
from paperworks.v6 import task039e3_r2r_d2_v2_design_v1 as design


ROOT = Path(__file__).resolve().parents[1]


class D2V2ExecutionAuthorizationV1Tests(unittest.TestCase):
    def setUp(self) -> None:
        subject._ISSUED_PREFLIGHTS.clear()
        subject._ISSUED_AUTHORIZATIONS.clear()
        subject._ISSUED_HORIZON_RECEIPTS.clear()

    def _synthetic(self):
        preflight = subject.build_synthetic_d2_v2_execution_custody_preflight_receipt_v1()
        auth = subject.issue_d2_v2_inner_execution_authorization_v1(preflight)
        return preflight, auth

    def test_exact_public_authorities_and_provenance_replay(self) -> None:
        replay = subject.replay_required_d2_v2_public_authorities_v1()
        self.assertEqual(replay.d2_v2_design_hash, design.D2_V2_DESIGN_HASH)
        self.assertEqual(replay.d0_prediction_hash, design.FROZEN_D0_PREDICTION_HASH)
        self.assertEqual(replay.d1_prediction_hash, design.FROZEN_D1_PREDICTION_HASH)
        self.assertEqual(replay.source_map_hash, design.FROZEN_SOURCE_MAP_HASH)
        self.assertEqual(replay.native_horizon_map_hash, design.D2_V2_NATIVE_HORIZON_MAP_HASH)

    def test_native_horizon_receipt_is_exact_42_entry_factory_authority(self) -> None:
        receipt = subject.build_d2_v2_native_horizon_authority_receipt_v1()
        self.assertEqual(subject.validate_d2_v2_native_horizon_authority_receipt_v1(receipt), receipt.artifact_hash)
        self.assertEqual((receipt.relation_count, receipt.unique_relation_count), (42, 42))
        self.assertEqual((receipt.missing_horizon_count, receipt.ambiguous_horizon_count), (0, 0))
        self.assertEqual((receipt.label_derived_horizon_count, receipt.test1_derived_horizon_count), (0, 0))
        for mutation in (
            replace(receipt, native_horizon_map_hash="0" * 64),
            replace(receipt, relation_count=41),
            replace(receipt, missing_horizon_count=1),
            replace(receipt, ambiguous_horizon_count=1),
            replace(receipt, label_derived_horizon_count=1),
            replace(receipt, test1_derived_horizon_count=1),
        ):
            with self.assertRaises(subject.D2V2ExecutionAuthorizationError):
                subject.validate_d2_v2_native_horizon_authority_receipt_v1(mutation)

    def test_altered_noninteger_negative_and_test1_derived_horizons_rejected(self) -> None:
        original = design.native_horizon_map_document_v1()
        mutations = []
        for value in (original["entries"][0]["native_horizon_seconds"] + 1, 1.5, -1):
            candidate = __import__("copy").deepcopy(original)
            candidate["entries"][0]["native_horizon_seconds"] = value
            mutations.append(candidate)
        candidate = __import__("copy").deepcopy(original)
        candidate["test1_derived_count"] = 1
        mutations.append(candidate)
        for mutation in mutations:
            with self.assertRaises(design.D2V2DesignError):
                design.validate_native_horizon_map_document_v1(mutation)

    def test_synthetic_preflight_and_authorization_flags_are_fail_closed(self) -> None:
        preflight, auth = self._synthetic()
        self.assertEqual(subject.validate_d2_v2_execution_custody_preflight_receipt_v1(preflight), preflight.artifact_hash)
        self.assertEqual(subject.validate_d2_v2_inner_execution_authorization_v1(auth, preflight), auth.authorization_hash)
        self.assertFalse(auth.d2_v2_inner_execution_authorized)
        forbidden = (
            auth.label_before_combined_prediction_authorized,
            auth.test1_feature_access_authorized,
            auth.d0_rerun_authorized,
            auth.d1_rerun_authorized,
            auth.rule_reevaluation_authorized,
            auth.d0_score_access_authorized,
            auth.single_source_fallback_authorized,
            auth.fixed_temporal_window_override_authorized,
            auth.horizon_override_authorized,
            auth.fusion_change_authorized,
            auth.alternative_policy_search_authorized,
            auth.test2_authorized,
            auth.outer_authorized,
        )
        self.assertFalse(any(forbidden))

    def test_exact_token_source_and_fusion_contract(self) -> None:
        _, auth = self._synthetic()
        self.assertEqual(auth.token_start_policy, "D1_DECISION_PHYSICAL_ROW_INDEX")
        self.assertEqual(auth.token_expiry_policy, "DECISION_PHYSICAL_ROW_INDEX_PLUS_FROZEN_NATIVE_HORIZON_INCLUSIVE")
        self.assertFalse(auth.backdating_allowed)
        self.assertEqual(auth.required_distinct_source_count, 2)
        self.assertFalse(auth.single_source_fallback)
        self.assertIsNone(auth.fixed_global_temporal_window)
        self.assertFalse(auth.diagnostic_gap_used_as_parameter)
        self.assertEqual(auth.d0_preservation_policy, "EVERY_FROZEN_D0_ALARM_IS_A_D2_V2_ALARM")

    def test_synthetic_same_source_collapse_two_sources_and_d0_preservation(self) -> None:
        a, b, c = (design.FROZEN_NATIVE_HORIZON_BINDINGS[index][0] for index in range(3))
        horizons = ((a, 2), (b, 2), (c, 2))
        records = (
            design.D2V2SyntheticRuleAlarmV1(1, a, "SOURCE_A", True),
            design.D2V2SyntheticRuleAlarmV1(1, b, "SOURCE_A", True),
            design.D2V2SyntheticRuleAlarmV1(2, c, "SOURCE_B", True),
        )
        tokens = design.build_synthetic_causal_tokens_v1(records, horizons, 5)
        decisions = design.fuse_synthetic_native_horizon_timeline_v1((True, False, False, False, False), tokens)
        self.assertEqual(decisions[1].trigger_class, "NONE")
        self.assertEqual(decisions[2].trigger_class, "RULE_RECOVERY_NATIVE_HORIZON")
        self.assertTrue(decisions[0].d2_v2_alarm_emitted)

    def test_caller_reconstructed_or_mutated_values_are_rejected(self) -> None:
        preflight, auth = self._synthetic()
        reconstructed_preflight = replace(preflight)
        reconstructed_auth = replace(auth)
        with self.assertRaises(subject.D2V2ExecutionAuthorizationError):
            subject.validate_d2_v2_execution_custody_preflight_receipt_v1(reconstructed_preflight)
        with self.assertRaises(subject.D2V2ExecutionAuthorizationError):
            subject.validate_d2_v2_inner_execution_authorization_v1(reconstructed_auth, preflight)
        for mutation in (
            replace(auth, design_hash="0" * 64),
            replace(auth, d0_prediction_hash="0" * 64),
            replace(auth, d1_prediction_hash="0" * 64),
            replace(auth, source_map_hash="0" * 64),
            replace(auth, native_horizon_map_hash="0" * 64),
            replace(auth, required_distinct_source_count=1),
            replace(auth, single_source_fallback=True),
            replace(auth, backdating_allowed=True),
            replace(auth, fixed_global_temporal_window=2),
            replace(auth, d0_score_access_authorized=True),
            replace(auth, rule_reevaluation_authorized=True),
            replace(auth, label_before_combined_prediction_authorized=True),
            replace(auth, test1_feature_access_authorized=True),
            replace(auth, test2_authorized=True),
            replace(auth, outer_authorized=True),
        ):
            with self.assertRaises(subject.D2V2ExecutionAuthorizationError):
                subject.validate_d2_v2_inner_execution_authorization_v1(mutation, preflight)

    def test_path_bearing_errors_are_redacted_from_all_caller_channels(self) -> None:
        token = "PRIVATE_PATH_TOKEN_SHOULD_NEVER_ESCAPE"
        cases = (
            PermissionError(token),
            FileExistsError(token),
            IsADirectoryError(token),
            OSError(token),
        )
        for error in cases:
            stdout, stderr = io.StringIO(), io.StringIO()
            with redirect_stdout(stdout), redirect_stderr(stderr):
                try:
                    subject._raise_sanitized_custody_failure_v1(error)
                except subject.D2V2ExecutionAuthorizationError as observed:
                    visible = repr(observed) + str(observed) + stdout.getvalue() + stderr.getvalue()
                else:
                    self.fail("expected sanitized failure")
            self.assertNotIn(token, visible)

    def test_authorization_module_contains_no_scientific_execution(self) -> None:
        path = ROOT / "src/paperworks/v6/task039e3_r2r_d2_v2_execution_authorization_v1.py"
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source)
        forbidden = {
            "fuse_synthetic_native_horizon_timeline_v1",
            "build_synthetic_causal_tokens_v1",
            "execute_authorized_d2_inner_v1",
            "execute_authorized_d2_v2_inner_v1",
            "parse_label",
            "compute_metric_values_v1",
        }
        names = {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)}
        attrs = {node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute)}
        self.assertFalse((names | attrs) & forbidden)
        self.assertNotIn("prediction_records", source)
        self.assertNotIn("window_seconds", source)
        self.assertNotIn("lookahead_seconds", source)

    def test_v2_authorization_does_not_modify_v1_or_design_sources(self) -> None:
        expected_v1 = "eb559a91350fd046204d223d6820ef7f0590ad4beb7a2b17114a496859758e51"
        self.assertEqual(design.D2_V1_DESIGN_HASH, expected_v1)
        self.assertEqual(design.D2_V2_DESIGN_HASH, "ace631af367ee2abe1b0ee7658875eeb59a2a8d906d09ce8ea92e8f2d83e31e4")


if __name__ == "__main__":
    unittest.main()
