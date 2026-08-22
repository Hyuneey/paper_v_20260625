from __future__ import annotations

import ast
import copy
from pathlib import Path
import unittest

from paperworks.v6 import task039e3_r2r_d2_v2_design_v1 as subject


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src/paperworks/v6/task039e3_r2r_d2_v2_design_v1.py"


def _mutated_designs() -> tuple[tuple[str, dict[str, object]], ...]:
    expected = subject.build_d2_v2_design_authority_v1().to_public_dict()
    attacks: list[tuple[str, dict[str, object]]] = []

    def add(name: str, path: tuple[str, ...], value: object) -> None:
        candidate = copy.deepcopy(expected)
        cursor: dict[str, object] = candidate
        for key in path[:-1]:
            cursor = cursor[key]  # type: ignore[assignment,index]
        cursor[path[-1]] = value
        attacks.append((name, candidate))

    add("v1_design_mutation", ("input_authority", "d2_v1_design_hash"), "0" * 64)
    add("v1_prediction_mutation", ("input_authority", "d2_v1_combined_prediction_hash"), "0" * 64)
    add("d0_substitution", ("input_authority", "d0_detector_prediction_hash"), "0" * 64)
    add("d1_substitution", ("input_authority", "d1_rule_prediction_hash"), "0" * 64)
    add("source_map_substitution", ("input_authority", "source_map_hash"), "0" * 64)
    add("horizon_map_substitution", ("native_horizon_authority", "native_horizon_map_hash"), "0" * 64)
    add("two_second_window", ("evidence_token_policy", "global_fixed_temporal_window_seconds"), 2)
    add("one_sixty_nine_second_window", ("evidence_token_policy", "global_fixed_temporal_window_seconds"), 169)
    add("generic_window", ("evidence_token_policy", "global_fixed_temporal_window_seconds"), 7)
    add("source_count_change", ("corroboration_policy", "required_distinct_source_count"), 3)
    add("single_source_fallback", ("corroboration_policy", "single_source_fallback"), True)
    add("same_second_exclusion", ("corroboration_policy", "exact_same_second_included"), False)
    add("d0_score_gating", ("fusion_policy", "d0_score_dependency"), True)
    add("backdated_evidence", ("evidence_token_policy", "backdated_rule_evidence"), True)
    add("future_information", ("evidence_token_policy", "future_information_used"), True)
    add("horizon_multiplier", ("evidence_token_policy", "horizon_multiplier_allowed"), True)
    add("diagnostic_gap_parameter", ("evidence_token_policy", "diagnostic_gap_values_used_as_parameters"), True)
    add("v2_prediction_observed", ("provenance", "d2_v2_predictions_observed_before_freeze"), True)
    add("v2_metric_observed", ("provenance", "d2_v2_metrics_observed_before_freeze"), True)
    add("alternative_policy_execution", ("provenance", "alternative_v2_policies_executed"), 1)
    add("hypothetical_performance", ("provenance", "hypothetical_performance_calculations"), 1)
    add("parameter_sweep", ("provenance", "parameter_sweeps"), 1)
    add("label_read", ("provenance", "label_file_read_during_this_design_task"), True)
    add("test2", ("provenance", "test2_read_during_design"), True)
    add("outer", ("outer_authorized",), True)

    for name, field, value in (
        ("rule_whitelist", "rule_whitelist", ["forbidden"]),
        ("label_selected_relation", "label_selected_relations", ["forbidden"]),
    ):
        candidate = copy.deepcopy(expected)
        candidate["corroboration_policy"][field] = value  # type: ignore[index]
        attacks.append((name, candidate))
    return tuple(attacks)


INDEPENDENT_ATTACK_COUNT = len(_mutated_designs())


class D2V2IndependentDesignAuditTests(unittest.TestCase):
    def test_all_independent_design_attacks_fail_closed(self) -> None:
        accepted_invalid = 0
        for name, candidate in _mutated_designs():
            with self.subTest(name=name):
                try:
                    subject.validate_d2_v2_design_document_v1(candidate)
                except subject.D2V2DesignError:
                    continue
                accepted_invalid += 1
        self.assertEqual(accepted_invalid, 0)
        self.assertGreaterEqual(INDEPENDENT_ATTACK_COUNT, 21)

    def test_horizon_map_value_multiplier_and_test1_origin_fail(self) -> None:
        expected = subject.native_horizon_map_document_v1()
        accepted_invalid = 0
        candidates = []
        multiplied = copy.deepcopy(expected)
        multiplied["entries"][0]["native_horizon_seconds"] *= 2
        candidates.append(multiplied)
        test1 = copy.deepcopy(expected)
        test1["test1_derived_count"] = 1
        candidates.append(test1)
        label = copy.deepcopy(expected)
        label["label_derived_count"] = 1
        candidates.append(label)
        for candidate in candidates:
            try:
                subject.validate_native_horizon_map_document_v1(candidate)
            except subject.D2V2DesignError:
                continue
            accepted_invalid += 1
        self.assertEqual(accepted_invalid, 0)

    def test_no_scientific_execution_or_data_io_in_design_source(self) -> None:
        text = SOURCE.read_text(encoding="utf-8")
        tree = ast.parse(text)
        imported = {
            alias.name
            for node in ast.walk(tree)
            if isinstance(node, (ast.Import, ast.ImportFrom))
            for alias in node.names
        }
        forbidden_import_fragments = (
            "d0_inner_execution",
            "d1_execution_v1",
            "d2_inner_execution",
            "label",
            "test2",
        )
        self.assertFalse(any(fragment in name for name in imported for fragment in forbidden_import_fragments))
        forbidden_calls = {
            "execute_authorized_d0_inner_v1",
            "execute_authorized_d1_inner_v1",
            "execute_authorized_d2_inner_v1",
            "open",
        }
        observed_calls = {
            node.func.id
            for node in ast.walk(tree)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
        }
        self.assertTrue(forbidden_calls.isdisjoint(observed_calls))

    def test_exact_same_second_is_subset_and_async_overlap_is_causal(self) -> None:
        a, b = (item[0] for item in subject.FROZEN_NATIVE_HORIZON_BINDINGS[:2])
        same_second_records = (
            subject.D2V2SyntheticRuleAlarmV1(1, a, "A", True),
            subject.D2V2SyntheticRuleAlarmV1(1, b, "B", True),
        )
        same_tokens = subject.build_synthetic_causal_tokens_v1(same_second_records, ((a, 1), (b, 1)), 5)
        same = subject.fuse_synthetic_native_horizon_timeline_v1((False,) * 5, same_tokens)
        self.assertTrue(same[1].d2_v2_alarm_emitted)

        async_records = (
            subject.D2V2SyntheticRuleAlarmV1(1, a, "A", True),
            subject.D2V2SyntheticRuleAlarmV1(2, b, "B", True),
        )
        async_tokens = subject.build_synthetic_causal_tokens_v1(async_records, ((a, 2), (b, 1)), 5)
        async_result = subject.fuse_synthetic_native_horizon_timeline_v1((False,) * 5, async_tokens)
        self.assertFalse(async_result[0].d2_v2_alarm_emitted)
        self.assertTrue(async_result[2].d2_v2_alarm_emitted)
        self.assertFalse(async_result[4].d2_v2_alarm_emitted)


if __name__ == "__main__":
    unittest.main()
