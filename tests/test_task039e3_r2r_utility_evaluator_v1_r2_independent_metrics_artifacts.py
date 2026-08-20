"""Independent R2 metric, artifact, and D1/D2 boundary audit.

The expected event and metric answers below are derived locally from the
frozen half-open event policies.  The suite opens public committed authority
documents only to construct synthetic contract objects; it does not open HAI,
labels, attack intervals, locators, or either private numeric registry.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import fields, replace
import gc
import json
import math
from pathlib import Path
import unittest
import weakref

from paperworks.v6 import task039e3_r2r_utility_protocol_v4 as v4
from paperworks.v6 import task039e3_r2r_utility_source_census_supplement_v1 as supplement
import paperworks.v6.task039e3_r2r_utility_evaluator_metrics_v1 as metrics
from paperworks.v6.task039e3_r2r_utility_evaluator_authority_v1 import (
    CURRENT_EVALUATOR_IMPLEMENTATION_IDENTITY,
    SUPPLEMENT_PURPOSE,
    SyntheticNumericRecordV1,
    build_evaluator_authority_bundle_v1,
    build_evaluator_implementation_authority_v1,
    build_synthetic_numeric_resolver_v1,
)
from paperworks.v6.task039e3_r2r_utility_evaluator_census_v1 import (
    enumerate_full_census_v1,
)
from paperworks.v6.task039e3_r2r_utility_evaluator_input_v1 import (
    build_synthetic_feature_frame_v1,
)
from paperworks.v6.task039e3_r2r_utility_evaluator_rule_engine_v1 import (
    execute_rule_v1,
)
from paperworks.v6.task039e3_r2r_utility_evaluator_types_v1 import (
    SYNTHETIC_CONTRACT_ONLY,
    UtilityEvaluatorV1Error,
    dataclass_payload_v1,
    stable_hash_v1,
)


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_V4_AUTHORITY = "1a6200adce791ddd9be8d87b566d47b65e78c1735829d0f91f4ea22127ad1343"
EXPECTED_R2_IDENTITY = "e7a61070c0be96e305f6706b90308c9976bc8d521c8b97adea93836c3fd28cef"
ORIGINAL_IDENTITY = "332e367cdc0da21b281c5de43f6a735d7dc68bc87efafe90976d89d7f9dc3330"
R1_IDENTITY = "64a6e7f0d210dc074bc85b0f389e61b45aaa512091532cf8f4d275ccaa35746a"

# Each item names a materially distinct invariant, rather than a repeated
# parameter value.  Raw cases include independent positive oracle cases and
# every invalid parametrization exercised below.
METRIC_EVENT_CUSTODY_SEMANTIC_CLASSES = (
    "strict_binary_label_container",
    "strict_binary_label_scalar",
    "maximal_attack_runs",
    "attack_first_boundary",
    "attack_last_boundary",
    "raw_alarm_container",
    "raw_alarm_scalar",
    "raw_alarm_nonnegative",
    "raw_alarm_deduplication",
    "raw_alarm_sorting",
    "raw_alarm_adjacency_merge",
    "formed_episode_exact_type",
    "formed_episode_exact_integer_bounds",
    "formed_episode_nonnegative",
    "formed_episode_nonempty",
    "formed_episode_in_range",
    "formed_episode_strict_order",
    "formed_episode_no_overlap",
    "formed_episode_no_adjacency",
    "recall_zero_attack_undefined",
    "recall_each_attack_once",
    "recall_half_open_overlap",
    "far_zero_normal_undefined",
    "far_episode_not_point_count",
    "far_attack_overlap_exclusion",
    "far_normal_seconds_hours",
    "label_factory_custody",
    "label_attack_event_identity",
    "label_exposure_identity",
    "label_event_policy_identity",
    "label_stale_issuance",
    "metric_factory_custody",
    "metric_name_formula_authority",
    "metric_arithmetic_replay",
    "metric_custody_binding",
    "metric_episode_binding",
    "metric_policy_binding",
    "metric_stale_issuance",
)

ARTIFACT_D1_D2_SEMANTIC_CLASSES = (
    "rule_artifact_factory_custody",
    "rule_artifact_current_r2_identity",
    "rule_artifact_bundle_binding",
    "rule_artifact_v4_binding",
    "rule_artifact_common_binding",
    "rule_artifact_main_binding",
    "rule_artifact_supplement_binding",
    "rule_artifact_census_contract_binding",
    "rule_artifact_dataset_binding",
    "rule_artifact_split_binding",
    "rule_artifact_file_binding",
    "rule_artifact_opportunity_census_binding",
    "rule_artifact_denominator_binding",
    "rule_artifact_prediction_closure",
    "rule_artifact_prediction_order",
    "rule_artifact_trace_closure",
    "rule_artifact_count_replay",
    "rule_artifact_hash_replay",
    "rule_artifact_scientific_fail_closed",
    "detector_artifact_factory_custody",
    "detector_artifact_hash_replay",
    "detector_artifact_authority_binding",
    "detector_artifact_dataset_binding",
    "detector_artifact_split_binding",
    "detector_artifact_file_binding",
    "detector_artifact_prediction_binding",
    "comparison_same_rule_content",
    "comparison_dataset_match",
    "comparison_split_match",
    "comparison_file_match",
    "comparison_scientific_fail_closed",
    "synthetic_mode_not_promotable",
)

UNIQUE_METRIC_EVENT_CUSTODY_CLASSES = len(METRIC_EVENT_CUSTODY_SEMANTIC_CLASSES)
UNIQUE_ARTIFACT_D1_D2_CLASSES = len(ARTIFACT_D1_D2_SEMANTIC_CLASSES)
RAW_ADVERSARIAL_CASES = 140


def _load_public(relative: str) -> dict[str, object]:
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def _build_lower_v4_authority() -> v4.UtilityProtocolV4CanonicalAuthority:
    authority = v4.build_utility_protocol_v4_canonical_authority(
        executable_equivalence=_load_public(
            "docs/task_reports/TASK-039E3_R2R_UTILITY_PROTOCOL_EXECUTABLE_EQUIVALENCE.json"
        ),
        evidence_manifest=_load_public(
            "docs/task_reports/TASK-039E1_CONSTRUCTION_EVIDENCE_MANIFEST.json"
        ),
        dataset_manifest=_load_public("docs/task_reports/TASK-039A_DATASET_MANIFEST_V2.json"),
        csv_structure_report=_load_public(
            "docs/task_reports/TASK-039A_CSV_STRUCTURE_REPORT.json"
        ),
        c0_config=_load_public("configs/v6/task039c0_candidate_discovery_protocol.json"),
        br2_config=_load_public(
            "configs/v6/task039br2_hai_continuous_step_feasibility.json"
        ),
        materialized_audit_receipt=_load_public(
            "docs/task_reports/TASK-039E3_R2R_UTILITY_NORMAL_ONLY_AUTHORITY_V1_MATERIALIZED_RECEIPT.json"
        ),
    )
    if authority.authority_hash != EXPECTED_V4_AUTHORITY or len(authority.rule_descriptors) != 42:
        raise AssertionError("AUDIT_LOWER_V4_REPLAY_REJECTED")
    return authority


def _numeric_value(role: str) -> int | float:
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


def _oracle_attack_events(labels: tuple[int, ...]) -> tuple[tuple[int, int], ...]:
    """Audit-local maximal-run oracle; it does not call production helpers."""

    if type(labels) is not tuple or any(type(value) is not int or value not in (0, 1) for value in labels):
        raise ValueError("noncanonical labels")
    result: list[tuple[int, int]] = []
    start: int | None = None
    for index in range(len(labels) + 1):
        value = labels[index] if index < len(labels) else 0
        if value == 1 and start is None:
            start = index
        elif value == 0 and start is not None:
            result.append((start, index))
            start = None
    return tuple(result)


def _oracle_alarm_episodes(timestamps: tuple[int, ...]) -> tuple[tuple[int, int], ...]:
    """Audit-local dedupe/sort/maximal-adjacency oracle."""

    if type(timestamps) is not tuple or any(type(item) is not int or item < 0 for item in timestamps):
        raise ValueError("noncanonical timestamps")
    ordered = sorted(set(timestamps))
    if not ordered:
        return ()
    result: list[tuple[int, int]] = []
    start = previous = ordered[0]
    for item in ordered[1:]:
        if item == previous + 1:
            previous = item
        else:
            result.append((start, previous + 1))
            start = previous = item
    result.append((start, previous + 1))
    return tuple(result)


def _interval_pairs(items: tuple[metrics.IntervalV1, ...]) -> tuple[tuple[int, int], ...]:
    return tuple((item.start, item.end) for item in items)


def _reconstruct(value: object) -> object:
    return type(value)(**{field.name: getattr(value, field.name) for field in fields(value)})


def _rehash(value: object, hash_field: str) -> object:
    provisional = replace(value, **{hash_field: ""})
    return replace(
        provisional,
        **{
            hash_field: stable_hash_v1(
                dataclass_payload_v1(provisional, exclude=(hash_field,))
            )
        },
    )


def _raw_interval(start: object, end: object) -> metrics.IntervalV1:
    result = object.__new__(metrics.IntervalV1)
    object.__setattr__(result, "start", start)
    object.__setattr__(result, "end", end)
    return result


class _IntervalSubclass(metrics.IntervalV1):
    pass


class R2IndependentMetricEventCustodyAudit(unittest.TestCase):
    def _custody(self, labels: tuple[int, ...]) -> metrics.SyntheticLabelEventCustodyV1:
        return metrics.build_synthetic_label_event_custody_v1(
            labels=labels,
            dataset_manifest_identity="synthetic-dataset-r2-independent",
            split_identity="synthetic-split-r2-independent",
            source_file_identity="synthetic-file-r2-independent",
        )

    def test_attack_event_oracle_is_independently_reconstructed(self) -> None:
        cases = (
            (),
            (0, 0, 0),
            (1, 1, 1),
            (1, 0, 0),
            (0, 0, 1),
            (0, 1, 1, 0, 1, 0),
            (0, 1, 0, 1, 0, 1),
        )
        for labels in cases:
            expected = _oracle_attack_events(labels)
            observed = _interval_pairs(metrics.derive_attack_events_v1(labels))
            with self.subTest(labels=labels):
                self.assertEqual(observed, expected)

    def test_strict_binary_label_attacks_reject(self) -> None:
        invalid = (
            [0, 1],
            (True,),
            (False,),
            (1.0,),
            ("1",),
            (-1,),
            (2,),
            (None,),
            (float("nan"),),
        )
        for labels in invalid:
            with self.subTest(labels=repr(labels)), self.assertRaises(UtilityEvaluatorV1Error):
                metrics.derive_attack_events_v1(labels)  # type: ignore[arg-type]

    def test_alarm_episode_oracle_is_independently_reconstructed(self) -> None:
        cases = (
            (),
            (3,),
            (3, 3, 3),
            (3, 1, 2, 1),
            (1, 3),
            (1, 2, 3),
            (1, 2, 5, 8, 9),
            (9, 1, 2, 9, 8, 20),
        )
        for timestamps in cases:
            expected = _oracle_alarm_episodes(timestamps)
            observed = _interval_pairs(metrics.form_alarm_episodes_v1(timestamps))
            with self.subTest(timestamps=timestamps):
                self.assertEqual(observed, expected)

    def test_raw_alarm_timestamp_attacks_reject(self) -> None:
        invalid = ([1], (True,), (1.0,), ("1",), (-1,), (None,))
        for timestamps in invalid:
            with self.subTest(timestamps=repr(timestamps)), self.assertRaises(UtilityEvaluatorV1Error):
                metrics.form_alarm_episodes_v1(timestamps)  # type: ignore[arg-type]

    def test_recall_oracle_matches_frozen_half_open_semantics(self) -> None:
        cases = (
            ((0, 0, 0), (), (0, 0.0, None, False, "no_attack_events")),
            ((0, 1, 0), (), (0, 1.0, 0.0, True, None)),
            ((0, 1, 0), (metrics.IntervalV1(1, 2),), (1, 1.0, 1.0, True, None)),
            ((0, 1, 1, 1, 0), (metrics.IntervalV1(1, 2), metrics.IntervalV1(3, 4)), (1, 1.0, 1.0, True, None)),
            ((0, 1, 0, 0, 1, 0), (metrics.IntervalV1(1, 2),), (1, 2.0, 0.5, True, None)),
            ((0, 1, 0, 0, 1, 0), (metrics.IntervalV1(1, 2), metrics.IntervalV1(4, 5)), (2, 2.0, 1.0, True, None)),
            ((0, 1, 0), (metrics.IntervalV1(2, 3),), (0, 1.0, 0.0, True, None)),
            ((0, 1, 0, 1, 0), (metrics.IntervalV1(1, 4),), (2, 2.0, 1.0, True, None)),
        )
        for labels, alarms, expected in cases:
            metric = metrics.attack_event_recall_v1(self._custody(labels), alarms)
            observed = (metric.numerator, metric.denominator, metric.value, metric.defined, metric.undefined_reason)
            with self.subTest(labels=labels, alarms=alarms):
                self.assertEqual(observed, expected)
                self.assertEqual(metrics.validate_bound_metric_v1(metric), metric.metric_hash)

    def test_far_oracle_matches_episode_per_normal_hour_semantics(self) -> None:
        cases = (
            ((1, 1), (), (0, 0.0, None, False, "no_normal_exposure")),
            ((0, 0), (), (0, 2.0 / 3600.0, 0.0, True, None)),
            ((0, 0), (metrics.IntervalV1(0, 1),), (1, 2.0 / 3600.0, 1800.0, True, None)),
            ((0, 0, 0, 0), (metrics.IntervalV1(0, 1), metrics.IntervalV1(3, 4)), (2, 4.0 / 3600.0, 1800.0, True, None)),
            ((0, 1, 0), (metrics.IntervalV1(1, 2),), (0, 2.0 / 3600.0, 0.0, True, None)),
            ((0, 1, 0), (metrics.IntervalV1(0, 3),), (0, 2.0 / 3600.0, 0.0, True, None)),
            ((0,) * 3600, (metrics.IntervalV1(100, 101),), (1, 1.0, 1.0, True, None)),
        )
        for labels, alarms, expected in cases:
            metric = metrics.normal_far_episodes_per_hour_v1(self._custody(labels), alarms)
            observed = (metric.numerator, metric.denominator, metric.value, metric.defined, metric.undefined_reason)
            with self.subTest(row_count=len(labels), alarms=alarms):
                self.assertEqual(observed, expected)
                self.assertEqual(metrics.validate_bound_metric_v1(metric), metric.metric_hash)

    def test_duplicate_raw_timestamps_do_not_inflate_far(self) -> None:
        custody = self._custody((0,) * 10)
        episodes = metrics.form_alarm_episodes_v1((2, 2, 2, 3, 3))
        self.assertEqual(_interval_pairs(episodes), ((2, 4),))
        far = metrics.normal_far_episodes_per_hour_v1(custody, episodes)
        self.assertEqual(far.numerator, 1)

    def test_noncanonical_already_formed_episode_attacks_reject(self) -> None:
        custody = self._custody((0,) * 10)
        invalid = (
            [metrics.IntervalV1(1, 2)],
            (metrics.IntervalV1(1, 2), metrics.IntervalV1(1, 2)),
            (metrics.IntervalV1(1, 4), metrics.IntervalV1(3, 5)),
            (metrics.IntervalV1(1, 2), metrics.IntervalV1(2, 3)),
            (metrics.IntervalV1(5, 6), metrics.IntervalV1(1, 2)),
            (metrics.IntervalV1(9, 11),),
            (_raw_interval(-1, 1),),
            (_raw_interval(1, 1),),
            (_raw_interval(2, 1),),
            (_raw_interval(True, 2),),
            (_raw_interval(1.0, 2),),
            (_IntervalSubclass(1, 2),),
        )
        for episodes in invalid:
            for evaluator in (metrics.attack_event_recall_v1, metrics.normal_far_episodes_per_hour_v1):
                with self.subTest(episodes=repr(episodes), evaluator=evaluator.__name__), self.assertRaises(
                    UtilityEvaluatorV1Error
                ):
                    evaluator(custody, episodes)  # type: ignore[arg-type]

    def test_label_custody_reconstruction_and_semantic_self_rehash_reject(self) -> None:
        custody = self._custody((0, 1, 1, 0, 1, 0))
        relocated = replace(
            custody,
            attack_events=(metrics.IntervalV1(0, 2), metrics.IntervalV1(4, 5)),
        )
        attacks = (
            _reconstruct(custody),
            deepcopy(custody),
            replace(custody),
            _rehash(relocated, "custody_hash"),
            _rehash(replace(custody, attack_events=custody.attack_events + (metrics.IntervalV1(5, 6),)), "custody_hash"),
            _rehash(replace(custody, attack_events=custody.attack_events[:1]), "custody_hash"),
            _rehash(replace(custody, attack_events=tuple(reversed(custody.attack_events))), "custody_hash"),
            _rehash(replace(custody, dataset_manifest_identity="other-dataset"), "custody_hash"),
            _rehash(replace(custody, split_identity="other-split"), "custody_hash"),
            _rehash(replace(custody, source_file_identity="other-file"), "custody_hash"),
            _rehash(replace(custody, physical_row_count=7, normal_labeled_seconds=4), "custody_hash"),
            _rehash(replace(custody, strict_label_vector_hash="f" * 64), "custody_hash"),
            _rehash(replace(custody, attack_labeled_seconds=2, normal_labeled_seconds=4), "custody_hash"),
            _rehash(replace(custody, normal_labeled_seconds=2), "custody_hash"),
            _rehash(replace(custody, event_policy_hash="f" * 64), "custody_hash"),
        )
        for candidate in attacks:
            with self.subTest(candidate=repr(candidate)), self.assertRaises(UtilityEvaluatorV1Error):
                metrics.validate_synthetic_label_event_custody_v1(candidate)  # type: ignore[arg-type]

    def test_label_custody_stale_issuance_and_weakref_cleanup(self) -> None:
        custody = self._custody((0, 1, 0))
        key = id(custody)
        self.assertIn(key, metrics._ISSUED_LABEL_CUSTODIES)
        saved = metrics._ISSUED_LABEL_CUSTODIES.pop(key)
        with self.assertRaises(UtilityEvaluatorV1Error):
            metrics.validate_synthetic_label_event_custody_v1(custody)
        metrics._ISSUED_LABEL_CUSTODIES[key] = saved
        candidate_ref = weakref.ref(custody)
        del custody
        gc.collect()
        self.assertIsNone(candidate_ref())
        self.assertNotIn(key, metrics._ISSUED_LABEL_CUSTODIES)

    def test_bound_metric_reconstruction_and_semantic_self_rehash_reject(self) -> None:
        custody = self._custody((0, 1, 0, 0))
        metric = metrics.attack_event_recall_v1(custody, (metrics.IntervalV1(1, 2),))
        attacks = (
            _reconstruct(metric),
            deepcopy(metric),
            replace(metric),
            _rehash(replace(metric, metric_name="arbitrary_metric"), "metric_hash"),
            _rehash(replace(metric, formula_identity=metrics.NORMAL_FAR_FORMULA), "metric_hash"),
            _rehash(replace(metric, numerator=0, value=0.0), "metric_hash"),
            _rehash(replace(metric, denominator=2.0, value=0.5), "metric_hash"),
            _rehash(replace(metric, value=0.0), "metric_hash"),
            _rehash(replace(metric, defined=False, value=None, undefined_reason="no_attack_events", denominator=0.0), "metric_hash"),
            _rehash(replace(metric, undefined_reason="invented"), "metric_hash"),
            _rehash(replace(metric, label_custody_hash="f" * 64), "metric_hash"),
            _rehash(replace(metric, alarm_episode_set_hash="e" * 64), "metric_hash"),
            _rehash(replace(metric, metric_policy_hash="d" * 64), "metric_hash"),
            replace(metric, metric_hash="c" * 64),
        )
        for candidate in attacks:
            with self.subTest(candidate=repr(candidate)), self.assertRaises(UtilityEvaluatorV1Error):
                metrics.validate_bound_metric_v1(candidate)  # type: ignore[arg-type]

    def test_bound_metric_stale_issuance_rejects_and_cleans_up(self) -> None:
        custody = self._custody((0, 1, 0))
        metric = metrics.attack_event_recall_v1(custody, (metrics.IntervalV1(1, 2),))
        key = id(metric)
        saved = metrics._ISSUED_BOUND_METRICS.pop(key)
        with self.assertRaises(UtilityEvaluatorV1Error):
            metrics.validate_bound_metric_v1(metric)
        metrics._ISSUED_BOUND_METRICS[key] = saved
        metric_ref = weakref.ref(metric)
        del metric
        gc.collect()
        self.assertIsNone(metric_ref())
        self.assertNotIn(key, metrics._ISSUED_BOUND_METRICS)


class R2IndependentPredictionAndComparisonAudit(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.authority = _build_lower_v4_authority()
        cls.bundle = build_evaluator_authority_bundle_v1(cls.authority)
        cls.implementation = build_evaluator_implementation_authority_v1(cls.bundle)
        if CURRENT_EVALUATOR_IMPLEMENTATION_IDENTITY != EXPECTED_R2_IDENTITY:
            raise AssertionError("AUDIT_R2_IMPLEMENTATION_IDENTITY_REPLAY_REJECTED")

        main = tuple(
            SyntheticNumericRecordV1(
                "SYNTHETIC_MAIN_420",
                rule.source,
                rule.relation_binding_hash,
                role,
                reference,
                _numeric_value(role),
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
                _numeric_value(role),
            )
            for source in supplement.SUPPLEMENT_SOURCES
            for role in supplement.SUPPLEMENT_ROLES
        )
        cls.resolver = build_synthetic_numeric_resolver_v1(cls.bundle, main, extra)
        cls.rule = next(item for item in cls.authority.rule_descriptors if item.selected_horizon_seconds == 10)
        cls.frame, cls.census, cls.predictions, cls.artifact = cls._build_artifact(101)
        cls.other_frame, cls.other_census, cls.other_predictions, cls.other_artifact = cls._build_artifact(105)

    @classmethod
    def _build_artifact(cls, step_index: int):
        rows = tuple(
            tuple(
                (2.0 if cls.rule.source_direction == "step_up" else -2.0)
                if feature == cls.rule.source and physical >= step_index
                else 0.0
                for feature in cls.authority.feature_schema.union_features
            )
            for physical in range(80, 180)
        )
        frame = build_synthetic_feature_frame_v1(
            cls.bundle,
            source_file_identity="hai-test1.csv",
            start_physical_row_index=80,
            rows=rows,
        )
        census = enumerate_full_census_v1(frame, cls.bundle, cls.resolver)
        predictions = tuple(
            execute_rule_v1(envelope, census, frame, cls.bundle, cls.resolver)
            for envelope in census.relation_opportunities
        )
        artifact = metrics.build_rule_prediction_artifact_v1(
            evaluator_implementation_authority=cls.implementation,
            bundle=cls.bundle,
            frame=frame,
            census=census,
            resolver=cls.resolver,
            predictions=predictions,
        )
        return frame, census, predictions, artifact

    def _artifact_mutation(self, **changes: object) -> metrics.RulePredictionArtifactV1:
        return _rehash(replace(self.artifact, **changes), "artifact_hash")  # type: ignore[return-value]

    def _detector(self, **changes: object) -> metrics.DetectorPredictionArtifactV1:
        values = {
            "detector_authority_identity": "a" * 64,
            "dataset_manifest_identity": self.frame.dataset_manifest_identity,
            "split_identity": self.frame.split_identity,
            "source_file_identity": self.frame.source_file_identity,
            "point_predictions": tuple(False for _ in self.frame.rows),
        }
        values.update(changes)
        return metrics.build_synthetic_detector_prediction_artifact_v1(**values)  # type: ignore[arg-type]

    def test_rule_artifact_factory_result_binds_all_frozen_authorities(self) -> None:
        artifact = self.artifact
        self.assertEqual(metrics.validate_rule_prediction_artifact_v1(artifact), artifact.artifact_hash)
        self.assertEqual(artifact.evaluator_implementation_identity, EXPECTED_R2_IDENTITY)
        self.assertEqual(artifact.evaluator_authority_bundle_hash, self.bundle.bundle_hash)
        self.assertEqual(artifact.v4_authority_hash, EXPECTED_V4_AUTHORITY)
        self.assertEqual(artifact.common_portfolio, "COMMON-42")
        self.assertEqual(artifact.common_relation_count, 42)
        self.assertEqual(artifact.dataset_manifest_identity, self.frame.dataset_manifest_identity)
        self.assertEqual(artifact.split_identity, self.frame.split_identity)
        self.assertEqual(artifact.source_file_identity, self.frame.source_file_identity)
        self.assertEqual(artifact.opportunity_census_identity, self.census.census_hash)

    def test_rule_artifact_authority_content_and_count_mutations_reject(self) -> None:
        mutations = (
            {"artifact_type": "wrong"},
            {"execution_mode": "REAL"},
            {"synthetic_authority_identity": "f" * 64},
            {"scientific_eligible": True},
            {"evaluator_version": "V2"},
            {"evaluator_implementation_identity": ORIGINAL_IDENTITY},
            {"evaluator_implementation_identity": R1_IDENTITY},
            {"evaluator_implementation_identity": "f" * 64},
            {"evaluator_authority_bundle_hash": "f" * 64},
            {"v4_authority_hash": "f" * 64},
            {"common_portfolio": "T2-39"},
            {"common_relation_count": 39},
            {"main_descriptor_hash": "f" * 64},
            {"supplement_descriptor_hash": "f" * 64},
            {"combined_source_census_contract_hash": "f" * 64},
            {"dataset_manifest_identity": "other-dataset"},
            {"split_identity": "other-split"},
            {"source_file_identity": "other-file"},
            {"opportunity_census_identity": "f" * 64},
            {"denominator_policy": "caller-denominator"},
            {"trace_identities": tuple(reversed(self.artifact.trace_identities))},
            {"evaluated_count": self.artifact.evaluated_count + 1},
            {"alarm_count": self.artifact.alarm_count + 1},
            {"abstain_count": self.artifact.abstain_count + 1},
            {"error_count": 1},
        )
        for change in mutations:
            candidate = self._artifact_mutation(**change)
            with self.subTest(change=tuple(change)), self.assertRaises(UtilityEvaluatorV1Error):
                metrics.validate_rule_prediction_artifact_v1(candidate)

    def test_rule_artifact_prediction_insertion_deletion_reorder_and_trace_mutation_reject(self) -> None:
        altered_prediction = replace(
            self.predictions[0],
            final_state="evaluated_expected_response",
            alarm_emitted=False,
            trace_hash="f" * 64,
        )
        prediction_sets = (
            self.artifact.predictions + (self.artifact.predictions[0],),
            self.artifact.predictions[:-1],
            tuple(reversed(self.artifact.predictions)),
            (altered_prediction,) + self.artifact.predictions[1:],
        )
        for predictions in prediction_sets:
            traces = tuple(item.trace_hash for item in predictions)
            candidate = self._artifact_mutation(predictions=predictions, trace_identities=traces)
            with self.subTest(count=len(predictions)), self.assertRaises(UtilityEvaluatorV1Error):
                metrics.validate_rule_prediction_artifact_v1(candidate)

    def test_rule_artifact_factory_rejects_noncanonical_prediction_closure(self) -> None:
        prediction_sets = (
            self.predictions[:-1],
            self.predictions + (self.predictions[0],),
            tuple(reversed(self.predictions)),
            (replace(self.predictions[0], trace_hash="f" * 64),) + self.predictions[1:],
        )
        for predictions in prediction_sets:
            with self.subTest(count=len(predictions)), self.assertRaises(UtilityEvaluatorV1Error):
                metrics.build_rule_prediction_artifact_v1(
                    evaluator_implementation_authority=self.implementation,
                    bundle=self.bundle,
                    frame=self.frame,
                    census=self.census,
                    resolver=self.resolver,
                    predictions=predictions,
                )

    def test_rule_artifact_reconstruction_copy_replace_self_hash_and_stale_issuance_reject(self) -> None:
        candidates = (
            _reconstruct(self.artifact),
            deepcopy(self.artifact),
            replace(self.artifact),
            replace(self.artifact, artifact_hash="f" * 64),
        )
        for candidate in candidates:
            with self.subTest(kind=type(candidate).__name__), self.assertRaises(UtilityEvaluatorV1Error):
                metrics.validate_rule_prediction_artifact_v1(candidate)  # type: ignore[arg-type]

        fresh = metrics.build_rule_prediction_artifact_v1(
            evaluator_implementation_authority=self.implementation,
            bundle=self.bundle,
            frame=self.frame,
            census=self.census,
            resolver=self.resolver,
            predictions=self.predictions,
        )
        key = id(fresh)
        metrics._ISSUED_RULE_ARTIFACTS.pop(key)
        with self.assertRaises(UtilityEvaluatorV1Error):
            metrics.validate_rule_prediction_artifact_v1(fresh)

    def test_all_bare_implementation_identities_and_missing_authority_reject(self) -> None:
        kwargs = {
            "bundle": self.bundle,
            "frame": self.frame,
            "census": self.census,
            "resolver": self.resolver,
            "predictions": self.predictions,
        }
        for identity in (ORIGINAL_IDENTITY, R1_IDENTITY, EXPECTED_R2_IDENTITY, "f" * 64, "bad"):
            with self.subTest(identity=identity), self.assertRaises(UtilityEvaluatorV1Error):
                metrics.build_rule_prediction_artifact_v1(
                    evaluator_implementation_identity=identity,
                    **kwargs,
                )
        with self.assertRaises(UtilityEvaluatorV1Error):
            metrics.build_rule_prediction_artifact_v1(**kwargs)

    def test_detector_factory_artifact_reconstruction_and_self_rehash_must_reject(self) -> None:
        detector = self._detector()
        self.assertEqual(metrics.validate_detector_prediction_artifact_v1(detector), detector.artifact_hash)
        candidates = (
            _reconstruct(detector),
            deepcopy(detector),
            replace(detector),
            _rehash(replace(detector, detector_authority_identity="b" * 64), "artifact_hash"),
            _rehash(replace(detector, dataset_manifest_identity="other-dataset"), "artifact_hash"),
            _rehash(replace(detector, split_identity="other-split"), "artifact_hash"),
            _rehash(replace(detector, source_file_identity="other-file"), "artifact_hash"),
            _rehash(replace(detector, point_predictions=(True,) + detector.point_predictions[1:]), "artifact_hash"),
        )
        for candidate in candidates:
            with self.subTest(candidate=repr(candidate)), self.assertRaises(UtilityEvaluatorV1Error):
                metrics.validate_detector_prediction_artifact_v1(candidate)  # type: ignore[arg-type]

    def test_detector_authority_mode_and_point_type_attacks_reject(self) -> None:
        detector = self._detector()
        candidates = (
            _rehash(replace(detector, artifact_type="wrong"), "artifact_hash"),
            _rehash(replace(detector, execution_mode="REAL"), "artifact_hash"),
            _rehash(replace(detector, scientific_eligible=True), "artifact_hash"),
            _rehash(replace(detector, detector_authority_identity="not-a-sha"), "artifact_hash"),
            _rehash(replace(detector, point_predictions=(1,) + detector.point_predictions[1:]), "artifact_hash"),
            _rehash(replace(detector, point_predictions=list(detector.point_predictions)), "artifact_hash"),
        )
        for candidate in candidates:
            with self.subTest(candidate=repr(candidate)), self.assertRaises(UtilityEvaluatorV1Error):
                metrics.validate_detector_prediction_artifact_v1(candidate)  # type: ignore[arg-type]

    def test_d1_d2_same_rule_content_and_dataset_split_file_boundaries(self) -> None:
        detector = self._detector()
        comparison = metrics.build_synthetic_rule_detector_comparison_input_v1(
            detector=detector,
            d1_rule_artifact=self.artifact,
            d2_rule_artifact=self.artifact,
        )
        self.assertEqual(comparison.d1_rule_artifact_hash, comparison.d2_rule_artifact_hash)
        self.assertFalse(comparison.fusion_authorized)

        attacks = (
            (detector, self.artifact, self.other_artifact),
            (self._detector(dataset_manifest_identity="other-dataset"), self.artifact, self.artifact),
            (self._detector(split_identity="other-split"), self.artifact, self.artifact),
            (self._detector(source_file_identity="other-file"), self.artifact, self.artifact),
            (detector, self.artifact, self._artifact_mutation(common_portfolio="T2-39")),
            (detector, self.artifact, self._artifact_mutation(main_descriptor_hash="f" * 64)),
            (detector, self.artifact, self._artifact_mutation(evaluator_implementation_identity=R1_IDENTITY)),
            (detector, self.artifact, self._artifact_mutation(predictions=self.artifact.predictions[:-1])),
        )
        for detector_candidate, d1, d2 in attacks:
            with self.subTest(detector=repr(detector_candidate)), self.assertRaises(UtilityEvaluatorV1Error):
                metrics.build_synthetic_rule_detector_comparison_input_v1(
                    detector=detector_candidate,
                    d1_rule_artifact=d1,
                    d2_rule_artifact=d2,
                )

    def test_synthetic_artifacts_cannot_be_promoted_to_scientific(self) -> None:
        detector = self._detector()
        comparison = metrics.build_synthetic_rule_detector_comparison_input_v1(
            detector=detector,
            d1_rule_artifact=self.artifact,
            d2_rule_artifact=self.artifact,
        )
        with self.assertRaises(UtilityEvaluatorV1Error):
            metrics.validate_scientific_rule_prediction_artifact_v1(self.artifact)
        with self.assertRaises(UtilityEvaluatorV1Error):
            metrics.validate_scientific_rule_detector_comparison_input_v1(comparison)
        promoted_rule = self._artifact_mutation(execution_mode="REAL", scientific_eligible=True)
        with self.assertRaises(UtilityEvaluatorV1Error):
            metrics.validate_scientific_rule_prediction_artifact_v1(promoted_rule)
        promoted_detector = _rehash(
            replace(detector, execution_mode="REAL", scientific_eligible=True),
            "artifact_hash",
        )
        with self.assertRaises(UtilityEvaluatorV1Error):
            metrics.build_synthetic_rule_detector_comparison_input_v1(
                detector=promoted_detector,
                d1_rule_artifact=self.artifact,
                d2_rule_artifact=self.artifact,
            )


if __name__ == "__main__":
    unittest.main()
