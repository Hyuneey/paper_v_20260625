from __future__ import annotations

from dataclasses import replace
import json
import math
from pathlib import Path
import unittest

from paperworks.v6 import task039e3_r2r_utility_protocol_v4 as v4
from paperworks.v6 import task039e3_r2r_utility_source_census_supplement_v1 as supplement
from paperworks.v6.task039e3_r2r_utility_evaluator_authority_v1 import (
    SUPPLEMENT_PURPOSE,
    SyntheticNumericRecordV1,
    build_evaluator_authority_bundle_v1,
    build_evaluator_implementation_authority_v1,
    build_synthetic_numeric_resolver_v1,
)
from paperworks.v6.task039e3_r2r_utility_evaluator_census_v1 import enumerate_full_census_v1
from paperworks.v6.task039e3_r2r_utility_evaluator_input_v1 import build_synthetic_feature_frame_v1
from paperworks.v6.task039e3_r2r_utility_evaluator_rule_engine_v1 import execute_rule_v1
from paperworks.v6.task039e3_r2r_utility_evaluator_metrics_v1 import (
    IntervalV1,
    alarm_episodes_from_rule_artifact_v1,
    attack_event_recall_v1,
    build_rule_prediction_artifact_v1,
    build_synthetic_detector_prediction_artifact_v1,
    build_synthetic_label_event_custody_v1,
    build_synthetic_point_diagnostics_v1,
    build_synthetic_rule_detector_comparison_input_v1,
    derive_attack_events_v1,
    form_alarm_episodes_v1,
    normal_far_episodes_per_hour_v1,
    validate_bound_metric_v1,
    validate_detector_prediction_artifact_v1,
    validate_rule_prediction_artifact_v1,
    validate_scientific_rule_detector_comparison_input_v1,
    validate_scientific_rule_prediction_artifact_v1,
    validate_synthetic_label_event_custody_v1,
)
from paperworks.v6.task039e3_r2r_utility_evaluator_types_v1 import (
    SYNTHETIC_CONTRACT_ONLY,
    UtilityEvaluatorV1Error,
    dataclass_payload_v1,
    stable_hash_v1,
)


ROOT = Path(__file__).resolve().parents[1]
NEGATIVE_SYNTHETIC_CASES = 30


def load(relative_path: str) -> dict[str, object]:
    return json.loads((ROOT / relative_path).read_text(encoding="utf-8"))


def numeric_value(role: str) -> int | float:
    return {
        "source_step_threshold": 1.0,
        "source_stability_tolerance": 0.0,
        "target_noise_scale": 0.5,
        "source_pre_window_seconds": 5,
        "source_post_window_seconds": 5,
        "minimum_source_stability_fraction": 0.8,
        "source_refractory_seconds": 10,
        "cross_source_isolation_radius_seconds": 2,
        "target_baseline_window_seconds": 5,
        "target_response_window_seconds": 3,
    }[role]


class UtilityEvaluatorV1MetricsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.authority = v4.build_utility_protocol_v4_canonical_authority(
            executable_equivalence=load(
                "docs/task_reports/TASK-039E3_R2R_UTILITY_PROTOCOL_EXECUTABLE_EQUIVALENCE.json"
            ),
            evidence_manifest=load("docs/task_reports/TASK-039E1_CONSTRUCTION_EVIDENCE_MANIFEST.json"),
            dataset_manifest=load("docs/task_reports/TASK-039A_DATASET_MANIFEST_V2.json"),
            csv_structure_report=load("docs/task_reports/TASK-039A_CSV_STRUCTURE_REPORT.json"),
            c0_config=load("configs/v6/task039c0_candidate_discovery_protocol.json"),
            br2_config=load("configs/v6/task039br2_hai_continuous_step_feasibility.json"),
            materialized_audit_receipt=load(
                "docs/task_reports/TASK-039E3_R2R_UTILITY_NORMAL_ONLY_AUTHORITY_V1_MATERIALIZED_RECEIPT.json"
            ),
        )
        cls.bundle = build_evaluator_authority_bundle_v1(cls.authority)
        main = tuple(
            SyntheticNumericRecordV1(
                "SYNTHETIC_MAIN_420",
                rule.source,
                rule.relation_binding_hash,
                role,
                reference,
                numeric_value(role),
            )
            for rule in cls.authority.rule_descriptors
            for role, reference in rule.numeric_reference_bindings
        )
        extra = tuple(
            SyntheticNumericRecordV1(
                SUPPLEMENT_PURPOSE,
                source,
                None,
                role,
                supplement.supplement_reference_identity_v1(source, role),
                1.0 if role == "source_step_threshold" else 0.0,
            )
            for source in supplement.SUPPLEMENT_SOURCES
            for role in supplement.SUPPLEMENT_ROLES
        )
        cls.resolver = build_synthetic_numeric_resolver_v1(cls.bundle, main, extra)
        cls.rule = next(rule for rule in cls.authority.rule_descriptors if rule.selected_horizon_seconds == 10)
        ordered_features = cls.authority.feature_schema.union_features
        frame_rows = []
        for physical_index in range(80, 180):
            frame_rows.append(
                tuple(
                    (
                        2.0 if cls.rule.source_direction == "step_up" else -2.0
                    )
                    if feature == cls.rule.source and physical_index >= 101
                    else 0.0
                    for feature in ordered_features
                )
            )
        cls.frame = build_synthetic_feature_frame_v1(
            cls.bundle,
            source_file_identity="hai-test1.csv",
            start_physical_row_index=80,
            rows=tuple(frame_rows),
        )
        cls.census = enumerate_full_census_v1(cls.frame, cls.bundle, cls.resolver)
        cls.predictions = tuple(
            execute_rule_v1(envelope, cls.census, cls.frame, cls.bundle, cls.resolver)
            for envelope in cls.census.relation_opportunities
        )
        cls.implementation_authority = build_evaluator_implementation_authority_v1(
            cls.bundle
        )
        cls.rule_artifact = build_rule_prediction_artifact_v1(
            evaluator_implementation_authority=cls.implementation_authority,
            bundle=cls.bundle,
            frame=cls.frame,
            census=cls.census,
            resolver=cls.resolver,
            predictions=cls.predictions,
        )

    def test_file_local_attack_and_alarm_episode_semantics(self) -> None:
        self.assertEqual(
            derive_attack_events_v1((0, 1, 1, 0, 1, 0)),
            (IntervalV1(1, 3), IntervalV1(4, 5)),
        )
        self.assertEqual(
            form_alarm_episodes_v1((4, 1, 2, 1, 8, 9, 10)),
            (IntervalV1(1, 3), IntervalV1(4, 5), IntervalV1(8, 11)),
        )

    def test_exact_attack_recall_and_normal_far_toy_case(self) -> None:
        labels = [0] * 3600
        labels[10:12] = [1, 1]
        labels[20] = 1
        custody = build_synthetic_label_event_custody_v1(
            labels=tuple(labels),
            dataset_manifest_identity="synthetic-dataset",
            split_identity="synthetic-split",
            source_file_identity="synthetic-file",
        )
        alarms = form_alarm_episodes_v1((10, 11, 10, 100, 101, 100))
        recall = attack_event_recall_v1(custody, alarms)
        far = normal_far_episodes_per_hour_v1(custody, alarms)
        self.assertEqual((recall.numerator, recall.denominator, recall.value), (1, 2.0, 0.5))
        self.assertEqual(far.numerator, 1)
        self.assertAlmostEqual(far.denominator, 3597 / 3600)
        self.assertAlmostEqual(far.value or -1.0, 1 / (3597 / 3600))
        self.assertEqual(validate_bound_metric_v1(recall), recall.metric_hash)
        self.assertEqual(validate_bound_metric_v1(far), far.metric_hash)

    def test_zero_denominators_are_undefined_not_zero(self) -> None:
        no_attack = build_synthetic_label_event_custody_v1(
            labels=(0, 0, 0), dataset_manifest_identity="d", split_identity="s", source_file_identity="f"
        )
        recall = attack_event_recall_v1(no_attack, ())
        self.assertFalse(recall.defined)
        self.assertIsNone(recall.value)
        self.assertEqual(recall.undefined_reason, "no_attack_events")

        no_normal = build_synthetic_label_event_custody_v1(
            labels=(1, 1, 1), dataset_manifest_identity="d", split_identity="s", source_file_identity="f"
        )
        far = normal_far_episodes_per_hour_v1(no_normal, (IntervalV1(0, 1),))
        self.assertFalse(far.defined)
        self.assertIsNone(far.value)
        self.assertEqual(far.undefined_reason, "no_normal_exposure")

    def test_duplicate_alarms_and_attack_matches_are_counted_once(self) -> None:
        custody = build_synthetic_label_event_custody_v1(
            labels=(0, 1, 1, 1, 0), dataset_manifest_identity="d", split_identity="s", source_file_identity="f"
        )
        episodes = form_alarm_episodes_v1((1, 1, 3, 3))
        self.assertEqual(len(episodes), 2)
        metric = attack_event_recall_v1(custody, episodes)
        self.assertEqual(metric.numerator, 1)
        self.assertEqual(metric.denominator, 1.0)

    def test_synthetic_point_diagnostics_are_explicit_and_exact(self) -> None:
        result = build_synthetic_point_diagnostics_v1(
            labels=(1, 1, 0, 0),
            detector_alarm_points=(False, True, False, True),
            rule_alarm_points=(True, True, True, True),
        )
        self.assertEqual(result.execution_mode, SYNTHETIC_CONTRACT_ONLY)
        self.assertEqual(result.detector_false_negative_points, 1)
        self.assertEqual(result.recovered_false_negative_points, 1)
        self.assertEqual(result.added_false_positive_points, 1)
        self.assertIn("INTERFACE_ONLY_POINT_LEVEL", result.formula_scope)

    def test_rule_prediction_artifact_is_deterministic_and_synthetic_only(self) -> None:
        second = build_rule_prediction_artifact_v1(
            evaluator_implementation_authority=self.implementation_authority,
            bundle=self.bundle,
            frame=self.frame,
            census=self.census,
            resolver=self.resolver,
            predictions=self.predictions,
        )
        self.assertEqual(self.rule_artifact, second)
        self.assertEqual(validate_rule_prediction_artifact_v1(second), second.artifact_hash)
        self.assertFalse(second.scientific_eligible)
        self.assertGreater(len(alarm_episodes_from_rule_artifact_v1(second)), 0)
        with self.assertRaises(UtilityEvaluatorV1Error):
            validate_scientific_rule_prediction_artifact_v1(second)

    def test_self_rehashed_authority_and_count_mutations_rejected(self) -> None:
        cases = (
            {"artifact_type": "wrong"},
            {"execution_mode": "REAL_AUTHORIZED_UTILITY_EXECUTION"},
            {"scientific_eligible": True},
            {"evaluator_authority_bundle_hash": "f" * 64},
            {"v4_authority_hash": "2864c99017dcea576437efe9f9c5d531cc0d7810504cb2bd8e8585643d2fa0a1"},
            {"common_portfolio": "T2"},
            {"main_descriptor_hash": "f" * 64},
            {"supplement_descriptor_hash": "f" * 64},
            {"combined_source_census_contract_hash": "f" * 64},
            {"denominator_policy": "caller denominator"},
            {"evaluated_count": True},
            {"error_count": 1},
            {"artifact_hash": "f" * 64},
        )
        self.assertEqual(len(cases), 13)
        for changes in cases:
            candidate = replace(self.rule_artifact, **changes)
            if "artifact_hash" not in changes:
                candidate = replace(
                    candidate,
                    artifact_hash=stable_hash_v1(
                        dataclass_payload_v1(candidate, exclude=("artifact_hash",))
                    ),
                )
            with self.subTest(changes=tuple(changes)), self.assertRaises(UtilityEvaluatorV1Error):
                validate_rule_prediction_artifact_v1(candidate)

    def test_detector_and_d1_d2_same_rule_artifact_contract(self) -> None:
        detector = build_synthetic_detector_prediction_artifact_v1(
            detector_authority_identity="a" * 64,
            dataset_manifest_identity=self.frame.dataset_manifest_identity,
            split_identity=self.frame.split_identity,
            source_file_identity=self.frame.source_file_identity,
            point_predictions=tuple(False for _ in self.frame.rows),
        )
        self.assertEqual(validate_detector_prediction_artifact_v1(detector), detector.artifact_hash)
        comparison = build_synthetic_rule_detector_comparison_input_v1(
            detector=detector,
            d1_rule_artifact=self.rule_artifact,
            d2_rule_artifact=self.rule_artifact,
        )
        self.assertEqual(comparison.d1_rule_artifact_hash, comparison.d2_rule_artifact_hash)
        self.assertFalse(comparison.fusion_authorized)
        with self.assertRaises(UtilityEvaluatorV1Error):
            validate_scientific_rule_detector_comparison_input_v1(comparison)

        changed = replace(self.rule_artifact, evaluator_implementation_identity="f" * 64)
        changed = replace(
            changed,
            artifact_hash=stable_hash_v1(
                dataclass_payload_v1(changed, exclude=("artifact_hash",))
            ),
        )
        with self.assertRaises(UtilityEvaluatorV1Error):
            build_synthetic_rule_detector_comparison_input_v1(
                detector=detector,
                d1_rule_artifact=self.rule_artifact,
                d2_rule_artifact=changed,
            )

    def test_forged_canonical_result_and_direct_artifact_copy_rejected(self) -> None:
        forged_prediction = replace(
            self.predictions[0],
            final_state="evaluated_expected_response",
            alarm_emitted=False,
            trace_hash="f" * 64,
        )
        with self.assertRaises(UtilityEvaluatorV1Error):
            build_rule_prediction_artifact_v1(
                evaluator_implementation_authority=self.implementation_authority,
                bundle=self.bundle,
                frame=self.frame,
                census=self.census,
                resolver=self.resolver,
                predictions=(forged_prediction,) + self.predictions[1:],
            )
        with self.assertRaises(UtilityEvaluatorV1Error):
            validate_rule_prediction_artifact_v1(replace(self.rule_artifact))

    def test_strict_label_alarm_detector_and_diagnostic_boundaries(self) -> None:
        invalid_calls = (
            lambda: derive_attack_events_v1((True,)),
            lambda: derive_attack_events_v1((1.0,)),
            lambda: derive_attack_events_v1(("1",)),
            lambda: derive_attack_events_v1([1]),
            lambda: form_alarm_episodes_v1((True,)),
            lambda: form_alarm_episodes_v1((1.0,)),
            lambda: form_alarm_episodes_v1(("1",)),
            lambda: form_alarm_episodes_v1((-1,)),
            lambda: form_alarm_episodes_v1([1]),
            lambda: build_synthetic_point_diagnostics_v1(
                labels=(1,), detector_alarm_points=(False, False), rule_alarm_points=(True,)
            ),
            lambda: build_synthetic_point_diagnostics_v1(
                labels=(1,), detector_alarm_points=(0,), rule_alarm_points=(True,)
            ),
            lambda: build_synthetic_detector_prediction_artifact_v1(
                detector_authority_identity="a" * 64,
                dataset_manifest_identity="d",
                split_identity="s",
                source_file_identity="f",
                point_predictions=(1,),
            ),
        )
        self.assertEqual(len(invalid_calls), 12)
        for call in invalid_calls:
            with self.subTest(call=repr(call)), self.assertRaises(UtilityEvaluatorV1Error):
                call()

    def test_custody_and_metric_self_hash_mutations_rejected(self) -> None:
        custody = build_synthetic_label_event_custody_v1(
            labels=(0, 1, 0), dataset_manifest_identity="d", split_identity="s", source_file_identity="f"
        )
        mutations = (
            replace(custody, custody_hash="f" * 64),
            replace(custody, attack_labeled_seconds=True, normal_labeled_seconds=2),
            replace(custody, event_policy_hash="f" * 64),
        )
        for item in mutations:
            with self.assertRaises(UtilityEvaluatorV1Error):
                validate_synthetic_label_event_custody_v1(item)
        metric = attack_event_recall_v1(custody, (IntervalV1(1, 2),))
        with self.assertRaises(UtilityEvaluatorV1Error):
            validate_bound_metric_v1(replace(metric, numerator=True))
        with self.assertRaises(UtilityEvaluatorV1Error):
            validate_bound_metric_v1(replace(metric, metric_hash="f" * 64))


if __name__ == "__main__":
    unittest.main()
