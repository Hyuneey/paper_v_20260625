from __future__ import annotations

import ast
from dataclasses import replace
from pathlib import Path
import unittest

from paperworks.v6 import task039e3_r2r_d2_v2_inner_execution_v1 as execution
from paperworks.v6 import task039e3_r2r_utility_evaluator_metrics_v1 as metrics


class D2V2InnerExecutionV1Tests(unittest.TestCase):
    def _token(
        self,
        relation: str,
        source: str,
        decision: int,
        horizon: int,
        row_count: int = 8,
    ) -> execution.D2V2EvidenceTokenV1:
        return execution.build_evidence_tokens_v1(
            ((decision, True, relation),),
            ((relation, source),),
            ((relation, horizon),),
            row_count,
        )[0]

    def test_01_exact_authority_and_committed_grant(self) -> None:
        self.assertEqual(execution.D2_V2_DESIGN_HASH, "ace631af367ee2abe1b0ee7658875eeb59a2a8d906d09ce8ea92e8f2d83e31e4")
        self.assertEqual(execution.AUTHORIZATION_HASH, "0f909480cfe3db8afc4042909258fe041f36ad021a917907008ee7e5023f2f45")
        self.assertEqual(execution.D0_PREDICTION_HASH, "a4b58f1c78b9bb53125da1a009f3fd05b02e1c83a789772a341a7679fddca0f6")
        self.assertEqual(execution.D1_PREDICTION_HASH, "58c3c49f9657f68d35c830b12eeb493ce4bbf7669c90f04813fb80246c3c2682")
        grant = execution.issue_committed_d2_v2_inner_execution_grant_v1()
        self.assertEqual(execution.validate_committed_d2_v2_inner_execution_grant_v1(grant), grant.grant_hash)

    def test_02_causal_token_start_inclusive_expiry_and_clipping(self) -> None:
        zero = self._token("r0", "s0", 3, 0)
        clipped = self._token("r1", "s1", 6, 9)
        self.assertEqual((zero.start_physical_row_index, zero.expiry_physical_row_index), (3, 3))
        self.assertEqual((clipped.start_physical_row_index, clipped.expiry_physical_row_index), (6, 7))
        self.assertEqual(zero.start_physical_row_index, zero.decision_physical_row_index)

    def test_03_one_source_and_same_source_duplicates_do_not_corroborate(self) -> None:
        tokens = (
            self._token("r0", "same", 1, 2),
            self._token("r1", "same", 1, 2),
        )
        active, corroboration, alarms, triggers = execution.fuse_native_horizon_timeline_v1((False,) * 8, tokens)
        self.assertEqual(active[1], ("same",))
        self.assertFalse(any(corroboration))
        self.assertFalse(any(alarms))
        self.assertEqual(set(triggers), {"NONE"})

    def test_04_two_same_second_distinct_sources_corroborate(self) -> None:
        tokens = (self._token("r0", "s0", 2, 0), self._token("r1", "s1", 2, 0))
        _, corroboration, alarms, triggers = execution.fuse_native_horizon_timeline_v1((False,) * 8, tokens)
        self.assertTrue(corroboration[2])
        self.assertTrue(alarms[2])
        self.assertEqual(triggers[2], "RULE_RECOVERY_NATIVE_HORIZON")

    def test_05_native_horizon_asynchronous_overlap_corroborates(self) -> None:
        tokens = (self._token("r0", "s0", 1, 3), self._token("r1", "s1", 3, 1))
        active, corroboration, _, _ = execution.fuse_native_horizon_timeline_v1((False,) * 8, tokens)
        self.assertEqual(active[3], ("s0", "s1"))
        self.assertEqual(tuple(i for i, value in enumerate(corroboration) if value), (3, 4))

    def test_06_expired_evidence_cannot_corroborate(self) -> None:
        tokens = (self._token("r0", "s0", 1, 1), self._token("r1", "s1", 3, 0))
        _, corroboration, _, _ = execution.fuse_native_horizon_timeline_v1((False,) * 8, tokens)
        self.assertFalse(any(corroboration))

    def test_07_optimized_fusion_matches_bruteforce_oracle(self) -> None:
        cases = (
            (),
            (self._token("a0", "s0", 0, 0),),
            (self._token("a1", "s0", 1, 3), self._token("a2", "s1", 3, 0)),
            (self._token("a3", "s0", 1, 2), self._token("a4", "s0", 2, 2)),
            (self._token("a5", "s0", 6, 9), self._token("a6", "s1", 7, 0)),
            (self._token("a7", "s0", 2, 0), self._token("a8", "s1", 2, 0)),
            (self._token("a9", "s0", 0, 7), self._token("a10", "s1", 7, 0)),
            (self._token("a11", "s0", 2, 2), self._token("a12", "s1", 4, 0), self._token("a13", "s2", 4, 0)),
        )
        for index, tokens in enumerate(cases):
            d0 = tuple(i == index % 8 for i in range(8))
            self.assertEqual(
                execution.fuse_native_horizon_timeline_v1(d0, tokens),
                execution.brute_force_native_horizon_timeline_v1(d0, tokens),
            )

    def test_08_d0_preservation_and_trigger_truth_table(self) -> None:
        self.assertEqual(execution._fuse_point_v1(False, frozenset()), (False, False, "NONE"))
        self.assertEqual(execution._fuse_point_v1(True, frozenset()), (False, True, "D0_ONLY"))
        self.assertEqual(execution._fuse_point_v1(False, frozenset(("a", "b"))), (True, True, "RULE_RECOVERY_NATIVE_HORIZON"))
        self.assertEqual(execution._fuse_point_v1(True, frozenset(("a", "b"))), (True, True, "D0_AND_RULE_CORROBORATION_NATIVE_HORIZON"))

    def test_09_combined_record_contract_is_label_blind_and_fail_closed(self) -> None:
        record = execution.ScientificCombinedPredictionRecordV2(
            0, False, "NONE", execution._combined_identity_v1(0, False, "NONE")
        )
        execution.validate_combined_prediction_records_v1((record,), 1)
        self.assertEqual(set(record.to_public_dict()), execution.COMBINED_RECORD_KEYS)
        bad = replace(record, d2_v2_alarm_emitted=True)
        with self.assertRaisesRegex(execution.D2V2InnerExecutionV1Error, "COMBINED_PREDICTION_V2_TRIGGER_REJECTED"):
            execution.validate_combined_prediction_records_v1((bad,), 1)

    def test_10_state_machine_blocks_label_before_prediction_freeze(self) -> None:
        state = execution.D2V2ExecutionStateMachineV1()
        with self.assertRaisesRegex(execution.D2V2InnerExecutionV1Error, "LABEL_BEFORE_COMBINED_PREDICTION_V2_FREEZE_REJECTED"):
            state.require_label_access()
        state.state = execution.D2V2ExecutionStateV1.COMBINED_PREDICTION_V2_FROZEN
        state.require_label_access()

    def test_11_frozen_metric_arithmetic(self) -> None:
        attacks = (metrics.IntervalV1(1, 3), metrics.IntervalV1(8, 10))
        d0 = (metrics.IntervalV1(1, 2), metrics.IntervalV1(5, 6))
        v2 = (metrics.IntervalV1(1, 2), metrics.IntervalV1(5, 6), metrics.IntervalV1(8, 9))
        recovery = (metrics.IntervalV1(8, 9),)
        values = execution.compute_metric_values_v1(attacks, d0, v2, recovery, 3600)
        self.assertEqual(values, {
            "d2_v2_recall": 1.0,
            "d2_v2_far": 1.0,
            "d0_missed_recovery": 1.0,
            "incremental_recall": 0.5,
            "added_recovery_far": 0.0,
            "incremental_far": 0.0,
        })

    def test_12_static_one_shot_and_no_scientific_controller_dependency(self) -> None:
        path = Path(execution.__file__)
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source)
        calls = {
            node.func.id
            for node in ast.walk(tree)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
        }
        self.assertNotIn("execute_authorized_d0_inner_v1", calls)
        self.assertNotIn("execute_authorized_d1_inner_v1", calls)
        self.assertNotIn("execute_authorized_d2_inner_v1", calls)
        self.assertEqual(source.count("def execute_authorized_d2_v2_inner_v1("), 1)
        self.assertNotIn("window_seconds", source)
        for operation in ("retry", "horizon_override", "single_source_fallback", "d0_score", "test2", "outer"):
            with self.assertRaises(execution.D2V2InnerExecutionV1Error):
                execution.reject_prohibited_operation_v1(operation)


if __name__ == "__main__":
    unittest.main()
