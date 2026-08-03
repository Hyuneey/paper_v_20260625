from __future__ import annotations

import ast
import hashlib
import json
import unittest
from pathlib import Path

from paperworks.v6.common import stable_hash_v1
from paperworks.v6.continuous_step_protocol_v1 import (
    ContinuousStepProtocolBundleV1,
    ContinuousStepProtocolError,
    SourceEventStatusV1,
    SustainedStepEventV1,
    build_default_protocol_bundle_v1,
    calibration_confirmation_gate_v1,
    classify_event_isolation_v1,
    cluster_step_events_v1,
    default_protocol_config_content_v1,
    derive_source_screening_parameters_v1,
    evaluate_step_candidate_v1,
    evaluate_target_response_v1,
    extract_sustained_step_events_v1,
    fit_support_gate_v1,
    process_feasibility_gate_v1,
    robust_one_step_scale_v1,
    select_process_v1,
)


ROOT = Path(__file__).resolve().parents[1]


def bundle() -> ContinuousStepProtocolBundleV1:
    content = default_protocol_config_content_v1()
    return build_default_protocol_bundle_v1(config_hash=stable_hash_v1(content))


def event(index: int, amplitude: float) -> SustainedStepEventV1:
    return SustainedStepEventV1(
        index,
        "step_up" if amplitude > 0 else "step_down",
        0.0,
        amplitude,
        amplitude,
        1.0,
        1.0,
    )


def feasible_metrics(**updates: object) -> dict[str, object]:
    result: dict[str, object] = {
        "documented_sources_with_valid_fit_thresholds": 2,
        "eligible_continuous_targets": 3,
        "calibration_confirmed_directional_pairs": 3,
        "distinct_confirmed_sources": 2,
        "distinct_confirmed_targets": 2,
        "fit_to_calibration_transfer_rate": 0.5,
        "normal_candidate_fit_files": ("hai-train1.csv", "hai-train2.csv"),
        "normal_relation_calibration_file": "hai-train3.csv",
        "normal_guard_feature_values_accessed": False,
        "prohibited_data_access_count": 0,
        "median_calibration_isolated_event_support": 10.0,
        "manual_metadata_coverage": 1.0,
        "metadata_unresolved_ratio": 0.0,
        "non_isolated_source_event_ratio": 0.1,
        "missing_or_nonfinite_rate": 0.0,
    }
    result.update(updates)
    return result


class TriggerSemanticsTests(unittest.TestCase):
    def test_valid_step_up_and_step_down(self) -> None:
        up = evaluate_step_candidate_v1(
            [0.0] * 5 + [10.0] * 5,
            5,
            source_step_threshold=5.0,
            source_stability_tolerance=0.1,
        )
        down = evaluate_step_candidate_v1(
            [10.0] * 5 + [0.0] * 5,
            5,
            source_step_threshold=5.0,
            source_stability_tolerance=0.1,
        )
        self.assertEqual(up.event.direction, "step_up")
        self.assertEqual(down.event.direction, "step_down")

    def test_insufficient_amplitude(self) -> None:
        result = evaluate_step_candidate_v1(
            [0.0] * 5 + [1.0] * 5,
            5,
            source_step_threshold=2.0,
            source_stability_tolerance=0.1,
        )
        self.assertEqual(result.status, "insufficient_fit_events")
        self.assertIsNone(result.event)

    def test_unstable_pre_level(self) -> None:
        result = evaluate_step_candidate_v1(
            [0.0, 0.0, 0.0, 10.0, 10.0] + [20.0] * 5,
            5,
            source_step_threshold=5.0,
            source_stability_tolerance=0.1,
        )
        self.assertEqual(result.status, "unstable_pre_level")

    def test_unstable_post_level(self) -> None:
        result = evaluate_step_candidate_v1(
            [0.0] * 5 + [10.0, 10.0, 10.0, 20.0, 20.0],
            5,
            source_step_threshold=5.0,
            source_stability_tolerance=0.1,
        )
        self.assertEqual(result.status, "unstable_post_level")

    def test_file_boundary_censoring(self) -> None:
        for index in (4, 6):
            with self.subTest(index=index):
                result = evaluate_step_candidate_v1(
                    [0.0] * 10,
                    index,
                    source_step_threshold=1.0,
                    source_stability_tolerance=0.1,
                )
                self.assertEqual(result.status, "cross_file_unavailable")

    def test_refractory_clustering_largest_and_earliest_tie(self) -> None:
        clustered = cluster_step_events_v1(
            (event(10, 5.0), event(15, 8.0), event(20, -8.0), event(40, 3.0))
        )
        self.assertEqual([item.event_index for item in clustered], [15, 40])

    def test_isolation_classification(self) -> None:
        classified = classify_event_isolation_v1(
            {"A": (event(10, 4.0), event(30, 4.0)), "B": (event(12, 3.0),)}
        )
        self.assertFalse(classified["A"][0][1])
        self.assertTrue(classified["A"][1][1])
        self.assertFalse(classified["B"][0][1])

    def test_source_scale_and_threshold(self) -> None:
        values = ([0.0] * 5 + [10.0] * 5) * 24
        self.assertEqual(robust_one_step_scale_v1(values), 1e-12)
        result = derive_source_screening_parameters_v1(values)
        self.assertEqual(result.status, "supported")
        self.assertGreaterEqual(result.nontrivial_amplitude_count, 20)
        self.assertIsNotNone(result.source_step_threshold)
        self.assertIsNotNone(result.source_stability_tolerance)

    def test_insufficient_nontrivial_amplitudes(self) -> None:
        result = derive_source_screening_parameters_v1([0.0] * 30)
        self.assertEqual(
            result.status,
            SourceEventStatusV1.INSUFFICIENT_NONTRIVIAL_AMPLITUDES.value,
        )
        self.assertIsNone(result.source_step_threshold)

    def test_extraction_is_deterministic(self) -> None:
        values = [0.0] * 12 + [10.0] * 12
        first = extract_sustained_step_events_v1(
            values,
            source_step_threshold=5.0,
            source_stability_tolerance=0.1,
        )
        second = extract_sustained_step_events_v1(
            values,
            source_step_threshold=5.0,
            source_stability_tolerance=0.1,
        )
        self.assertEqual(first, second)
        self.assertEqual(len(first), 1)


class ResponseAndGateTests(unittest.TestCase):
    def test_target_increase_and_decrease(self) -> None:
        increase = evaluate_target_response_v1(
            [0.0] * 10 + [5.0] * 10,
            event_index=9,
            horizon_seconds=1,
            target_noise_scale=1.0,
            target_direction="increase",
        )
        decrease = evaluate_target_response_v1(
            [10.0] * 10 + [0.0] * 10,
            event_index=9,
            horizon_seconds=1,
            target_noise_scale=1.0,
            target_direction="decrease",
        )
        self.assertTrue(increase.direction_matches)
        self.assertTrue(decrease.direction_matches)
        self.assertGreater(increase.target_response, 0.0)
        self.assertLess(decrease.target_response, 0.0)

    def test_target_right_censoring(self) -> None:
        result = evaluate_target_response_v1(
            [0.0] * 12,
            event_index=8,
            horizon_seconds=5,
            target_noise_scale=1.0,
            target_direction="increase",
        )
        self.assertTrue(result.right_censored)

    def test_fit_support_gate(self) -> None:
        self.assertTrue(
            fit_support_gate_v1(
                total_isolated_events=20,
                train1_isolated_events=10,
                train2_isolated_events=10,
                fit_directional_consistency=0.70,
                train1_directional_consistency=0.60,
                train2_directional_consistency=0.60,
                fit_robust_effect_ratio=2.0,
                direction_agrees_across_files=True,
            )
        )
        self.assertFalse(
            fit_support_gate_v1(
                total_isolated_events=19,
                train1_isolated_events=10,
                train2_isolated_events=9,
                fit_directional_consistency=0.90,
                train1_directional_consistency=0.90,
                train2_directional_consistency=0.90,
                fit_robust_effect_ratio=3.0,
                direction_agrees_across_files=True,
            )
        )

    def test_calibration_confirmation_requires_no_retuning(self) -> None:
        common = dict(
            train3_isolated_events=5,
            source_direction_unchanged=True,
            target_direction_unchanged=True,
            train3_directional_consistency=0.60,
            train3_robust_effect_ratio=1.0,
        )
        self.assertTrue(
            calibration_confirmation_gate_v1(
                **common, fit_parameters_reused_without_retuning=True
            )
        )
        self.assertFalse(
            calibration_confirmation_gate_v1(
                **common, fit_parameters_reused_without_retuning=False
            )
        )


class ProcessPolicyTests(unittest.TestCase):
    def test_process_feasibility_gate(self) -> None:
        self.assertTrue(process_feasibility_gate_v1(feasible_metrics()))
        self.assertFalse(
            process_feasibility_gate_v1(
                feasible_metrics(normal_guard_feature_values_accessed=True)
            )
        )

    def test_exactly_one_feasible_process_is_selected(self) -> None:
        decision = select_process_v1(
            feasible_metrics(),
            feasible_metrics(eligible_continuous_targets=2),
        )
        self.assertEqual(decision.selected_process, "P1")

    def test_pareto_dominance(self) -> None:
        p1 = feasible_metrics(
            distinct_confirmed_sources=3,
            calibration_confirmed_directional_pairs=5,
        )
        decision = select_process_v1(p1, feasible_metrics())
        self.assertEqual(decision.selected_process, "P1")
        self.assertEqual(decision.reason, "pareto_dominance")

    def test_indeterminate_selection(self) -> None:
        p1 = feasible_metrics(distinct_confirmed_sources=3)
        p3 = feasible_metrics(distinct_confirmed_targets=3)
        decision = select_process_v1(p1, p3)
        self.assertEqual(decision.status, "selection_indeterminate")
        self.assertIsNone(decision.selected_process)

    def test_neither_process_feasible(self) -> None:
        decision = select_process_v1(
            feasible_metrics(eligible_continuous_targets=2),
            feasible_metrics(eligible_continuous_targets=2),
        )
        self.assertEqual(decision.reason, "blocked_no_feasible_continuous_step_process")


class ContractBoundaryTests(unittest.TestCase):
    def test_data_behavior_and_graph_cannot_invent_source_semantics(self) -> None:
        policy = bundle().trigger_policy
        self.assertTrue(policy.manual_review_required)
        self.assertEqual(
            policy.metadata_confidence_policy,
            "sufficient_under_frozen_metadata_policy",
        )
        self.assertTrue(
            policy.finite_nonconstant_repeated_changes_all_fit_and_calibration_required
        )
        self.assertTrue(policy.setpoints_excluded)
        self.assertFalse(policy.data_behavior_grants_control_semantics)
        self.assertFalse(policy.official_graph_grants_source_eligibility)
        self.assertFalse(policy.discrete_sources_routed_to_family)

    def test_unsupported_no_rule_and_abstention_remain_distinct(self) -> None:
        policy = bundle().unsupported_policy
        self.assertNotIn("no_rule", policy.source_event_statuses)
        self.assertNotIn("no_rule", policy.source_target_statuses)
        self.assertFalse(policy.no_rule_created_in_br1)
        self.assertFalse(policy.invalid_rule_is_abstention)
        self.assertFalse(policy.parameter_binding_failure_is_abstention)
        self.assertFalse(policy.isolation_is_runtime_abstention_rule)
        self.assertIn("file_or_split_boundary", policy.future_runtime_abstention_reasons)

    def test_parameter_provenance_and_agent_number_prohibition(self) -> None:
        policy = bundle().parameter_provenance_policy
        self.assertEqual(
            policy.parameter_classes,
            ("feasibility_screening", "final_calibration", "runtime"),
        )
        self.assertTrue(policy.screening_implicit_promotion_prohibited)
        self.assertFalse(policy.agent_number_authority)
        self.assertIn("invent_lag", policy.agent_prohibited_actions)

    def test_rule_v1_isolated_and_rule_v2_is_plan_only(self) -> None:
        plan = bundle().rule_migration_plan
        self.assertFalse(plan.rule_v1_modified)
        self.assertFalse(plan.rule_v2_created)
        self.assertFalse(plan.route_continuous_rules_through_rule_v1)
        self.assertTrue(plan.independent_schema_and_parser_required)

    def test_no_authority_grants_or_real_data(self) -> None:
        frozen = bundle()
        self.assertFalse(frozen.validity_authority_granted)
        self.assertFalse(frozen.runtime_authority_granted)
        self.assertFalse(frozen.process_selection_granted)
        self.assertFalse(frozen.process_selected)
        self.assertFalse(frozen.task039c_authorized)
        self.assertFalse(frozen.real_data_accessed)
        self.assertEqual(frozen.next_task, "TASK-039BR2")

    def test_deterministic_hash_and_round_trip(self) -> None:
        frozen = bundle()
        serialized = frozen.to_dict()
        self.assertEqual(serialized, bundle().to_dict())
        self.assertEqual(
            ContinuousStepProtocolBundleV1.from_dict(serialized), frozen
        )

    def test_unknown_field_rejected_for_every_artifact(self) -> None:
        frozen = bundle()
        artifacts = (
            frozen.relation_family,
            frozen.trigger_policy,
            frozen.response_policy,
            frozen.feasibility_policy,
            frozen.process_selection_policy,
            frozen.unsupported_policy,
            frozen.parameter_provenance_policy,
            frozen.rule_migration_plan,
            frozen.verifier_migration_plan,
            frozen.runtime_migration_plan,
            frozen,
        )
        for artifact in artifacts:
            with self.subTest(artifact=artifact.artifact_type):
                payload = artifact.to_dict()
                payload["undeclared"] = True
                with self.assertRaises(ContinuousStepProtocolError):
                    type(artifact).from_dict(payload)

    def test_rule_v1_verifier_runtime_hashes_match_br0_receipt(self) -> None:
        receipt = json.loads(
            (ROOT / "docs/task_reports/TASK-039BR0_RULE_V1_COMPATIBILITY.json").read_text(
                encoding="utf-8"
            )
        )
        paths = {
            "rule_parser_sha256": ROOT / "src/paperworks/contracts/rule_v1.py",
            "verifier_sha256": ROOT / "src/paperworks/contracts/verifier_v1.py",
            "runtime_sha256": ROOT / "src/paperworks/contracts/runtime_v1.py",
        }
        for field, path in paths.items():
            with self.subTest(field=field):
                self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), receipt[field])

    def test_module_has_no_canonical_authority_or_data_import(self) -> None:
        path = ROOT / "src/paperworks/v6/continuous_step_protocol_v1.py"
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module)
            elif isinstance(node, ast.Import):
                imports.update(alias.name for alias in node.names)
        prohibited = {
            "paperworks.contracts",
            "paperworks.data.hai_provenance_v1",
            "paperworks.feasibility.hai_process_v1",
            "paperworks.runtime",
            "paperworks.verification",
        }
        self.assertTrue(
            all(
                not any(item == root or item.startswith(root + ".") for root in prohibited)
                for item in imports
            )
        )


if __name__ == "__main__":
    unittest.main()
