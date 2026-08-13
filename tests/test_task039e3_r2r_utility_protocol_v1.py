from __future__ import annotations

import inspect
import json
from pathlib import Path
import unittest

from paperworks.data.contracts_v2 import (
    CreationMetadataV2,
    DataViewManifestV2,
    SplitRoleV2,
)
from paperworks.data.splits_v2 import (
    DataOperationV2,
    SplitPermissionV2Error,
    assert_operation_permitted_v2,
)
from paperworks.v6.task039e3_r2r_utility_protocol_v1 import (
    BASE_COMMIT,
    DATASET_MANIFEST_ID,
    ExecutableSignatureV1,
    IntervalV1,
    LOGICAL_EXTENT,
    PURGE_RANGE,
    SCIENTIFIC_P1_VIEW_ID,
    TEST1_RANGE,
    TEST2_RANGE,
    UtilityProtocolError,
    alarm_episode_precision_v1,
    attack_event_recall_v1,
    build_utility_data_view_v2,
    build_utility_split_manifests_v2,
    cluster_synthetic_source_candidates_v1,
    decision_index_v1,
    derive_synthetic_attack_events_v1,
    duplicate_firing_ratio_v1,
    evaluate_synthetic_rule_window_v1,
    event_f1_v1,
    exact_mcnemar_two_sided_v1,
    form_alarm_episodes_v1,
    is_synthetic_event_isolated_v1,
    no_rule_contribution_v1,
    normal_false_alarm_rate_per_hour_v1,
    protocol_policy_snapshot_v1,
)


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SOURCE_VIEW_PATH = REPOSITORY_ROOT / "docs/task_reports/TASK-039BR2_CANONICAL_RULE_VIEW_V2.json"


def _creation() -> CreationMetadataV2:
    return CreationMetadataV2(
        created_at="2026-08-14T00:00:00+09:00",
        created_by="TASK-039E3-R2R-UTILITY-PROTOCOL-FREEZE",
        code_commit=BASE_COMMIT,
        config_hash="110a0070f309db6680a508a6f10e65025f1c87b15585f8c019a3dbe277a48f02",
    )


def _signature_mapping() -> dict[str, object]:
    windows = {
        role: f"ref-{index}"
        for index, role in enumerate(
            (
                "source_pre_window_seconds",
                "source_post_window_seconds",
                "minimum_source_stability_fraction",
                "source_refractory_seconds",
                "cross_source_isolation_radius_seconds",
                "target_baseline_window_seconds",
                "target_response_window_seconds",
            ),
            start=4,
        )
    }
    return {
        "source": "P1-source",
        "source_step_direction": "step_up",
        "target": "P1-target",
        "target_response_direction": "increase",
        "selected_delay_horizon_seconds": 5,
        "source_threshold_reference": "ref-1",
        "source_stability_reference": "ref-2",
        "target_scale_reference": "ref-3",
        "window_constant_references": windows,
        "runtime_logic_family": "missing_expected_delayed_response",
        "construction_arm": "T0",
        "call_number": 0,
        "provider_response_id": None,
    }


def _base_window(**changes: object) -> dict[str, object]:
    value: dict[str, object] = {
        "event_index": 10,
        "horizon_seconds": 5,
        "source_pre_window": (0.0, 0.0, 0.0, 0.0, 0.0),
        "source_post_window": (2.0, 2.0, 2.0, 2.0, 2.0),
        "target_baseline_window": (10.0, 10.0, 10.0, 10.0, 10.0),
        "target_response_window": (12.0, 12.0, 12.0),
        "expected_source_direction": "step_up",
        "expected_target_direction": "increase",
        "source_step_threshold": 2.0,
        "source_stability_tolerance": 0.1,
        "target_noise_scale": 1.0,
    }
    value.update(changes)
    return value


class UtilityProtocolMetadataTests(unittest.TestCase):
    def test_dataset_authority_and_file_coordinate_split(self) -> None:
        source = DataViewManifestV2.from_dict(json.loads(SOURCE_VIEW_PATH.read_text(encoding="utf-8")))
        self.assertEqual(source.view_id, SCIENTIFIC_P1_VIEW_ID)
        utility = build_utility_data_view_v2(source, creation_metadata=_creation())
        self.assertEqual(utility.source_dataset_manifest_id, DATASET_MANIFEST_ID)
        self.assertFalse(utility.second_level_rule_calibration_allowed)
        self.assertEqual(dict(utility.preprocessing_config), dict(source.preprocessing_config))
        inner, outer = build_utility_split_manifests_v2(utility, creation_metadata=_creation())
        self.assertEqual((inner.role, outer.role), (SplitRoleV2.INNER_UTILITY, SplitRoleV2.OUTER_VALIDATION))
        self.assertEqual((inner.raw_ranges[0].start, inner.raw_ranges[0].end), TEST1_RANGE)
        self.assertEqual((outer.raw_ranges[0].start, outer.raw_ranges[0].end), TEST2_RANGE)
        self.assertEqual(PURGE_RANGE, (54_000, 54_120))
        self.assertEqual(LOGICAL_EXTENT, 284_520)
        self.assertIsNone(inner.event_ids)
        self.assertIsNone(outer.seed)
        self.assertTrue(inner.split_before_windowing)

    def test_protocol_narrows_inner_and_outer_operations(self) -> None:
        source = DataViewManifestV2.from_dict(json.loads(SOURCE_VIEW_PATH.read_text(encoding="utf-8")))
        utility = build_utility_data_view_v2(source, creation_metadata=_creation())
        inner, outer = build_utility_split_manifests_v2(utility, creation_metadata=_creation())
        assert_operation_permitted_v2(inner, DataOperationV2.ASSESS_RULE_UTILITY)
        assert_operation_permitted_v2(outer, DataOperationV2.REPLAY_OUTER)
        with self.assertRaises(SplitPermissionV2Error):
            assert_operation_permitted_v2(outer, DataOperationV2.ASSESS_RULE_UTILITY)
        self.assertNotEqual(inner.role, SplitRoleV2.SEALED_EVALUATION)
        self.assertNotEqual(outer.role, SplitRoleV2.SEALED_EVALUATION)

    def test_executable_signature_excludes_arm_and_provenance(self) -> None:
        first = _signature_mapping()
        second = dict(first)
        second.update(construction_arm="T1-B", call_number=3, provider_response_id="provider-id")
        left = ExecutableSignatureV1.from_mapping(first)
        right = ExecutableSignatureV1.from_mapping(second)
        self.assertEqual(left.semantic_execution_hash, right.semantic_execution_hash)
        mutated = dict(first)
        mutated["selected_delay_horizon_seconds"] = 10
        self.assertNotEqual(
            left.semantic_execution_hash,
            ExecutableSignatureV1.from_mapping(mutated).semantic_execution_hash,
        )

    def test_signature_fails_closed_on_missing_reference(self) -> None:
        value = _signature_mapping()
        del value["window_constant_references"]["target_response_window_seconds"]  # type: ignore[index]
        with self.assertRaises((KeyError, UtilityProtocolError)):
            ExecutableSignatureV1.from_mapping(value)


class UtilityProtocolSyntheticInterpreterTests(unittest.TestCase):
    def test_expected_response_and_decision_timestamp(self) -> None:
        result = evaluate_synthetic_rule_window_v1(**_base_window())
        self.assertEqual((result.status, result.anomaly), ("expected_response", False))
        self.assertEqual(result.decision_index, 17)
        self.assertEqual(decision_index_v1(10, 5), 17)

    def test_missing_response_and_equality_are_anomalies(self) -> None:
        missing = evaluate_synthetic_rule_window_v1(
            **_base_window(target_response_window=(10.5, 10.5, 10.5))
        )
        equality = evaluate_synthetic_rule_window_v1(
            **_base_window(target_response_window=(11.0, 11.0, 11.0))
        )
        self.assertEqual((missing.status, equality.status), ("anomaly", "anomaly"))
        self.assertTrue(missing.anomaly)

    def test_threshold_equality_and_stability_equality_qualify(self) -> None:
        result = evaluate_synthetic_rule_window_v1(
            **_base_window(source_pre_window=(0.0, 0.0, 0.0, 0.0, 0.2))
        )
        self.assertEqual(result.status, "expected_response")

    def test_wrong_direction_is_no_trigger(self) -> None:
        result = evaluate_synthetic_rule_window_v1(
            **_base_window(expected_source_direction="step_down")
        )
        self.assertEqual((result.status, result.anomaly), ("no_trigger", False))

    def test_incomplete_and_window_local_nonfinite_abstain(self) -> None:
        incomplete = evaluate_synthetic_rule_window_v1(
            **_base_window(target_response_window=(12.0, 12.0))
        )
        nonfinite = evaluate_synthetic_rule_window_v1(
            **_base_window(source_post_window=(2.0, 2.0, float("nan"), 2.0, 2.0))
        )
        self.assertEqual(incomplete.abstention_reason, "incomplete_target_response_window")
        self.assertEqual(nonfinite.abstention_reason, "nonfinite_source_window")
        self.assertIsNone(incomplete.anomaly)

    def test_refractory_single_link_and_tie_policy(self) -> None:
        self.assertEqual(
            cluster_synthetic_source_candidates_v1(((5, 2.0), (14, -3.0), (23, 3.0))),
            ((14, -3.0),),
        )

    def test_cross_source_isolation_is_inclusive_and_complete(self) -> None:
        sources = ("s1", "s2", "s3")
        self.assertFalse(
            is_synthetic_event_isolated_v1(
                source="s1",
                event_index=10,
                retained_events_by_source={"s1": (10,), "s2": (12,), "s3": ()},
                required_sources=sources,
            )
        )
        self.assertTrue(
            is_synthetic_event_isolated_v1(
                source="s1",
                event_index=10,
                retained_events_by_source={"s1": (10,), "s2": (13,), "s3": ()},
                required_sources=sources,
            )
        )
        with self.assertRaises(UtilityProtocolError):
            is_synthetic_event_isolated_v1(
                source="s1",
                event_index=10,
                retained_events_by_source={"s1": (10,), "s2": (13,)},
                required_sources=sources,
            )

    def test_no_rule_has_no_interpreter_and_remains_in_denominator(self) -> None:
        value = no_rule_contribution_v1()
        self.assertEqual(value["interpreter_instances"], 0)
        self.assertEqual(value["alarms"], 0)
        self.assertEqual(value["relation_denominator_contribution"], 1)
        self.assertIsNone(value["alarm_precision"])


class UtilityProtocolMetricTests(unittest.TestCase):
    def test_contiguous_attack_event_derivation_has_no_point_adjustment(self) -> None:
        events = derive_synthetic_attack_events_v1((0, 1, 1, 0, 1, 0))
        self.assertEqual(events, (IntervalV1(1, 3), IntervalV1(4, 5)))

    def test_alarm_deduplication_and_episode_formation(self) -> None:
        episodes = form_alarm_episodes_v1((2, 2, 3, 5))
        self.assertEqual(episodes, (IntervalV1(2, 4), IntervalV1(5, 6)))

    def test_primary_and_secondary_metric_formulas(self) -> None:
        attacks = (IntervalV1(2, 4), IntervalV1(8, 10))
        alarms = (IntervalV1(3, 4), IntervalV1(6, 7))
        recall = attack_event_recall_v1(attacks, alarms)
        precision = alarm_episode_precision_v1(attacks, alarms)
        far = normal_false_alarm_rate_per_hour_v1(attacks, alarms, normal_labeled_seconds=3600)
        f1 = event_f1_v1(precision, recall)
        self.assertEqual((recall.value, precision.value, far.value), (0.5, 0.5, 1.0))
        self.assertEqual(f1.value, 0.5)
        self.assertEqual(duplicate_firing_ratio_v1(4, 3).value, 0.25)

    def test_zero_denominator_is_na_not_zero(self) -> None:
        precision = alarm_episode_precision_v1((), ())
        far = normal_false_alarm_rate_per_hour_v1((), (), normal_labeled_seconds=0)
        self.assertFalse(precision.defined)
        self.assertIsNone(precision.value)
        self.assertFalse(far.defined)

    def test_exact_paired_mcnemar(self) -> None:
        self.assertIsNone(exact_mcnemar_two_sided_v1(0, 0))
        self.assertEqual(exact_mcnemar_two_sided_v1(3, 0), 0.25)

    def test_authority_and_metric_policy_is_closed(self) -> None:
        policy = protocol_policy_snapshot_v1()
        self.assertEqual(policy["protocol_classification"], "POST_RESULT_PROTOCOL_FREEZE")
        self.assertEqual(policy["primary_metrics"], ["attack_event_recall", "normal_false_alarm_rate_per_hour"])
        self.assertEqual(policy["point_adjustment"], "PROHIBITED")
        self.assertIn("NOT_APPLICABLE", policy["auroc"])
        self.assertFalse(policy["rule_v2_authority"])
        self.assertFalse(policy["utility_execution_authority"])
        self.assertFalse(policy["direct_number_threshold_substitution"])
        self.assertEqual(policy["no_op_selection"], "DEFERRED")
        self.assertEqual(policy["detector_integration"], "DEFERRED_UNTIL_DETECTOR_PROTOCOL")

    def test_module_has_no_real_data_loader_surface(self) -> None:
        import paperworks.v6.task039e3_r2r_utility_protocol_v1 as protocol

        public_parameters = {
            parameter
            for public_name in protocol.__all__
            if inspect.isfunction(getattr(protocol, public_name))
            for parameter in inspect.signature(getattr(protocol, public_name)).parameters
        }
        self.assertFalse({"path", "file", "dataset_root", "label_path"} & public_parameters)


if __name__ == "__main__":
    unittest.main()
