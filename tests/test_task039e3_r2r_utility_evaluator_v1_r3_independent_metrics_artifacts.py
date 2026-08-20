"""Independent R3 metric, artifact, and D1/D2 interface audit.

Expected event and metric answers come from the small audit-local oracles below,
not from evaluator helpers or earlier tests.  All constructed data is explicit
``SYNTHETIC_CONTRACT_ONLY`` content.  No real labels, HAI rows, detector,
private registry, provider, credential, or network are accessed.
"""

from __future__ import annotations

import copy
from dataclasses import fields, replace
import gc
import hashlib
import json
import pickle
from pathlib import Path
import unittest
import weakref

import paperworks.v6.task039e3_r2r_utility_evaluator_authority_v1 as authority_v1
import paperworks.v6.task039e3_r2r_utility_evaluator_metrics_v1 as metrics_v1
from paperworks.v6 import task039e3_r2r_utility_protocol_v4 as protocol_v4
from paperworks.v6 import task039e3_r2r_utility_source_census_supplement_v1 as supplement_v1
from paperworks.v6.task039e3_r2r_utility_evaluator_census_v1 import enumerate_full_census_v1
from paperworks.v6.task039e3_r2r_utility_evaluator_input_v1 import build_synthetic_feature_frame_v1
from paperworks.v6.task039e3_r2r_utility_evaluator_rule_engine_v1 import execute_rule_v1
from paperworks.v6.task039e3_r2r_utility_evaluator_types_v1 import UtilityEvaluatorV1Error


EXPECTED_R3_IDENTITY = "af74bf3bd9ae240f21c57630b4804eabb997021353f15e7c402904b94f783fb5"
EXPECTED_DETECTOR_AUTHORITY = "99399ef47589871f5ffb37a83d63bc4fa414d79b41435b4bb61c679a243dbd7b"
EXPECTED_EVENT_POLICY = "6e4a4467953c5c9bf973a0a8a18950669dc902310407b7b354128ad91febb2f4"
EXPECTED_METRIC_POLICY = "4c7b6cfdb6b3889e56e7151be60b92a7e6f46ce0135de0ed65ebf3207a7b0d6a"
EXPECTED_RECALL_FORMULA = (
    "ATTACK_EVENTS_OVERLAPPED_BY_AT_LEAST_ONE_ALARM_EPISODE_DIVIDED_BY_ALL_ATTACK_EVENTS"
)
EXPECTED_FAR_FORMULA = (
    "ALARM_EPISODES_WITH_NO_ATTACK_TIMESTAMP_DIVIDED_BY_NORMAL_LABELED_SECONDS_OVER_3600"
)

INDEPENDENT_ORACLE_CASES = 36
UNIQUE_SEMANTIC_ATTACK_CLASSES = 72
RAW_ADVERSARIAL_CASES = 126
DETECTOR_SPECIFIC_CLASSES = 24
ACCEPTED_INVALID_CASES = 0
REAL_LABEL_READS = 0
DETECTOR_EXECUTIONS = 0

_PUBLIC_LOWER_INPUTS = {
    "executable_equivalence": "docs/task_reports/TASK-039E3_R2R_UTILITY_PROTOCOL_EXECUTABLE_EQUIVALENCE.json",
    "evidence_manifest": "docs/task_reports/TASK-039E1_CONSTRUCTION_EVIDENCE_MANIFEST.json",
    "dataset_manifest": "docs/task_reports/TASK-039A_DATASET_MANIFEST_V2.json",
    "csv_structure_report": "docs/task_reports/TASK-039A_CSV_STRUCTURE_REPORT.json",
    "c0_config": "configs/v6/task039c0_candidate_discovery_protocol.json",
    "br2_config": "configs/v6/task039br2_hai_continuous_step_feasibility.json",
    "materialized_audit_receipt": "docs/task_reports/TASK-039E3_R2R_UTILITY_NORMAL_ONLY_AUTHORITY_V1_MATERIALIZED_RECEIPT.json",
}


def _strict_int(value: object) -> int:
    if type(value) is not int or value < 0:
        raise ValueError("audit oracle requires an exact nonnegative integer")
    return value


def _oracle_alarm_episodes(raw: tuple[int, ...]) -> tuple[tuple[int, int], ...]:
    if type(raw) is not tuple:
        raise ValueError("audit oracle requires exact tuple")
    ordered = sorted({_strict_int(value) for value in raw})
    if not ordered:
        return ()
    result: list[tuple[int, int]] = []
    start = previous = ordered[0]
    for value in ordered[1:]:
        if value == previous + 1:
            previous = value
        else:
            result.append((start, previous + 1))
            start = previous = value
    result.append((start, previous + 1))
    return tuple(result)


def _oracle_attack_events(labels: tuple[int, ...]) -> tuple[tuple[int, int], ...]:
    if type(labels) is not tuple or any(type(value) is not int or value not in {0, 1} for value in labels):
        raise ValueError("audit oracle requires exact binary integer tuple")
    events: list[tuple[int, int]] = []
    start: int | None = None
    for index, value in enumerate((*labels, 0)):
        if value == 1 and start is None:
            start = index
        elif value == 0 and start is not None:
            events.append((start, index))
            start = None
    return tuple(events)


def _overlap(left: tuple[int, int], right: tuple[int, int]) -> bool:
    return left[0] < right[1] and right[0] < left[1]


def _oracle_recall(
    labels: tuple[int, ...], episodes: tuple[tuple[int, int], ...]
) -> tuple[int, float, float | None]:
    attacks = _oracle_attack_events(labels)
    numerator = sum(any(_overlap(attack, alarm) for alarm in episodes) for attack in attacks)
    denominator = float(len(attacks))
    return numerator, denominator, None if denominator == 0.0 else numerator / denominator


def _oracle_far(
    labels: tuple[int, ...], episodes: tuple[tuple[int, int], ...]
) -> tuple[int, float, float | None]:
    attacks = _oracle_attack_events(labels)
    numerator = sum(not any(_overlap(attack, alarm) for attack in attacks) for alarm in episodes)
    denominator = labels.count(0) / 3600.0
    return numerator, denominator, None if denominator == 0.0 else numerator / denominator


def _independent_hash(payload: object) -> str:
    return hashlib.sha256(
        json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()


def _json_value(value: object) -> object:
    if hasattr(value, "__dataclass_fields__") and not isinstance(value, type):
        return {field.name: _json_value(getattr(value, field.name)) for field in fields(value)}
    if type(value) is tuple:
        return [_json_value(item) for item in value]
    if type(value) is dict:
        return {str(key): _json_value(item) for key, item in value.items()}
    return value


def _self_hash(value: object, hash_field: str) -> str:
    return _independent_hash(
        {
            field.name: _json_value(getattr(value, field.name))
            for field in fields(value)
            if field.name != hash_field
        }
    )


def _reconstruct(value: object) -> object:
    return type(value)(**{field.name: getattr(value, field.name) for field in fields(value)})


def _intervals(values: tuple[tuple[int, int], ...]) -> tuple[metrics_v1.IntervalV1, ...]:
    return tuple(metrics_v1.IntervalV1(start, end) for start, end in values)


def _load_lower_v4_authority() -> protocol_v4.UtilityProtocolV4CanonicalAuthority:
    root = Path(__file__).resolve().parents[1]
    documents = {
        name: json.loads((root / relative).read_text(encoding="utf-8"))
        for name, relative in _PUBLIC_LOWER_INPUTS.items()
    }
    authority = protocol_v4.build_utility_protocol_v4_canonical_authority(**documents)
    if authority.authority_hash != "1a6200adce791ddd9be8d87b566d47b65e78c1735829d0f91f4ea22127ad1343":
        raise AssertionError("lower V4 authority replay changed")
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


class UtilityEvaluatorV1R3IndependentMetricArtifactAudit(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.v4_authority = _load_lower_v4_authority()
        cls.bundle = authority_v1.build_evaluator_authority_bundle_v1(cls.v4_authority)
        cls.implementation = authority_v1.build_evaluator_implementation_authority_v1(cls.bundle)
        main_records = tuple(
            authority_v1.SyntheticNumericRecordV1(
                "SYNTHETIC_MAIN_420",
                rule.source,
                rule.relation_binding_hash,
                role,
                reference,
                _numeric_value(role),
            )
            for rule in cls.v4_authority.rule_descriptors
            for role, reference in rule.numeric_reference_bindings
        )
        supplement_records = tuple(
            authority_v1.SyntheticNumericRecordV1(
                "CROSS_SOURCE_ISOLATION_EVENT_CENSUS_ONLY",
                source,
                None,
                role,
                supplement_v1.supplement_reference_identity_v1(source, role),
                _numeric_value(role),
            )
            for source in supplement_v1.SUPPLEMENT_SOURCES
            for role in supplement_v1.SUPPLEMENT_ROLES
        )
        cls.resolver = authority_v1.build_synthetic_numeric_resolver_v1(
            cls.bundle, main_records, supplement_records
        )
        relation = next(
            item for item in cls.v4_authority.rule_descriptors if item.selected_horizon_seconds == 10
        )
        rows = tuple(
            tuple(
                (2.0 if relation.source_direction == "step_up" else -2.0)
                if feature == relation.source and physical_index >= 101
                else 0.0
                for feature in cls.v4_authority.feature_schema.union_features
            )
            for physical_index in range(80, 180)
        )
        cls.frame = build_synthetic_feature_frame_v1(
            cls.bundle,
            source_file_identity="hai-test1.csv",
            start_physical_row_index=80,
            rows=rows,
        )
        cls.census = enumerate_full_census_v1(cls.frame, cls.bundle, cls.resolver)
        cls.predictions = tuple(
            execute_rule_v1(envelope, cls.census, cls.frame, cls.bundle, cls.resolver)
            for envelope in cls.census.relation_opportunities
        )
        cls.rule_artifact = cls._new_rule_artifact()
        cls.labels = (0, 1, 1, 0, 0, 1, 0, 0, 0, 0)
        cls.custody = cls._new_custody(cls.labels)
        cls.episodes = _intervals(((0, 1), (3, 4), (7, 8)))
        cls.recall = metrics_v1.attack_event_recall_v1(cls.custody, cls.episodes)
        cls.far = metrics_v1.normal_far_episodes_per_hour_v1(cls.custody, cls.episodes)

    @classmethod
    def _new_rule_artifact(cls) -> metrics_v1.RulePredictionArtifactV1:
        return metrics_v1.build_rule_prediction_artifact_v1(
            evaluator_implementation_authority=cls.implementation,
            bundle=cls.bundle,
            frame=cls.frame,
            census=cls.census,
            resolver=cls.resolver,
            predictions=cls.predictions,
        )

    @classmethod
    def _new_custody(cls, labels: tuple[int, ...]) -> metrics_v1.SyntheticLabelEventCustodyV1:
        return metrics_v1.build_synthetic_label_event_custody_v1(
            labels=labels,
            dataset_manifest_identity="synthetic-dataset",
            split_identity="synthetic-split",
            source_file_identity="synthetic-file",
        )

    def _new_detector(self, **changes: object) -> metrics_v1.DetectorPredictionArtifactV1:
        values: dict[str, object] = {
            "dataset_manifest_identity": self.rule_artifact.dataset_manifest_identity,
            "split_identity": self.rule_artifact.split_identity,
            "source_file_identity": self.rule_artifact.source_file_identity,
            "point_predictions": tuple(False for _ in self.frame.rows),
        }
        values.update(changes)
        return metrics_v1.build_synthetic_detector_prediction_artifact_v1(**values)  # type: ignore[arg-type]

    def assertCustodyRejected(self, candidate: object) -> None:  # noqa: N802
        with self.assertRaises(UtilityEvaluatorV1Error):
            metrics_v1.validate_synthetic_label_event_custody_v1(candidate)  # type: ignore[arg-type]

    def assertMetricRejected(self, candidate: object) -> None:  # noqa: N802
        with self.assertRaises(UtilityEvaluatorV1Error):
            metrics_v1.validate_bound_metric_v1(candidate)  # type: ignore[arg-type]

    def assertRuleRejected(self, candidate: object) -> None:  # noqa: N802
        with self.assertRaises(UtilityEvaluatorV1Error):
            metrics_v1.validate_rule_prediction_artifact_v1(candidate)  # type: ignore[arg-type]

    def assertDetectorRejected(self, candidate: object) -> None:  # noqa: N802
        with self.assertRaises(UtilityEvaluatorV1Error):
            metrics_v1.validate_detector_prediction_artifact_v1(candidate)  # type: ignore[arg-type]

    def test_01_attack_event_oracle_matches_independent_cases(self) -> None:
        cases = (
            ((), ()),
            ((0, 0, 0), ()),
            ((1, 1, 1), ((0, 3),)),
            ((0, 1, 0), ((1, 2),)),
            ((1, 0, 0), ((0, 1),)),
            ((0, 0, 1), ((2, 3),)),
            ((0, 1, 1, 0, 1, 0), ((1, 3), (4, 5))),
            ((1, 0, 1, 0, 1), ((0, 1), (2, 3), (4, 5))),
        )
        for labels, expected in cases:
            self.assertEqual(_oracle_attack_events(labels), expected)
            observed = metrics_v1.derive_attack_events_v1(labels)
            self.assertEqual(tuple((item.start, item.end) for item in observed), expected)

    def test_02_malformed_attack_labels_reject(self) -> None:
        invalid: tuple[object, ...] = (
            [0, 1],
            (False,),
            (True,),
            (0.0,),
            (1.0,),
            (-1,),
            (2,),
            ("1",),
            (None,),
            ({"label": 1},),
        )
        for labels in invalid:
            with self.assertRaises(UtilityEvaluatorV1Error):
                metrics_v1.derive_attack_events_v1(labels)  # type: ignore[arg-type]

    def test_03_alarm_episode_oracle_matches_independent_cases(self) -> None:
        cases = (
            ((), ()),
            ((4,), ((4, 5),)),
            ((1, 2, 3), ((1, 4),)),
            ((1, 3), ((1, 2), (3, 4))),
            ((7, 1, 2), ((1, 3), (7, 8))),
            ((2, 2, 2), ((2, 3),)),
            ((10, 1, 9, 2, 2), ((1, 3), (9, 11))),
        )
        for raw, expected in cases:
            self.assertEqual(_oracle_alarm_episodes(raw), expected)
            observed = metrics_v1.form_alarm_episodes_v1(raw)
            self.assertEqual(tuple((item.start, item.end) for item in observed), expected)

    def test_04_malformed_raw_alarm_timestamps_reject(self) -> None:
        invalid: tuple[object, ...] = (
            [1],
            (True,),
            (False,),
            (1.0,),
            (-1,),
            ("1",),
            (None,),
            ({"time": 1},),
        )
        for raw in invalid:
            with self.assertRaises(UtilityEvaluatorV1Error):
                metrics_v1.form_alarm_episodes_v1(raw)  # type: ignore[arg-type]

    def test_05_interval_constructor_rejects_noncanonical_boundaries(self) -> None:
        for start, end in ((-1, 1), (1, 1), (2, 1), (True, 2), (0, False), (0.0, 1), (0, 1.0)):
            with self.assertRaises(UtilityEvaluatorV1Error):
                metrics_v1.IntervalV1(start, end)  # type: ignore[arg-type]

    def test_06_label_custody_factory_output_matches_oracle(self) -> None:
        self.assertEqual(
            metrics_v1.validate_synthetic_label_event_custody_v1(self.custody),
            self.custody.custody_hash,
        )
        self.assertEqual(
            tuple((event.start, event.end) for event in self.custody.attack_events),
            _oracle_attack_events(self.labels),
        )
        self.assertEqual(self.custody.attack_labeled_seconds, 3)
        self.assertEqual(self.custody.normal_labeled_seconds, 7)

    def test_07_label_custody_reconstruction_copy_replace_pickle_reject(self) -> None:
        for candidate in (
            _reconstruct(self.custody),
            copy.copy(self.custody),
            copy.deepcopy(self.custody),
            replace(self.custody),
            pickle.loads(pickle.dumps(self.custody)),
        ):
            self.assertCustodyRejected(candidate)

    def test_08_label_custody_self_rehash_semantic_substitutions_reject(self) -> None:
        mutations = (
            {"attack_events": _intervals(((0, 2), (7, 8)))},
            {"attack_events": _intervals(((1, 3),))},
            {"attack_events": self.custody.attack_events + (metrics_v1.IntervalV1(8, 9),)},
            {"dataset_manifest_identity": "other-dataset"},
            {"split_identity": "other-split"},
            {"source_file_identity": "other-file"},
            {"physical_row_count": 11},
            {"strict_label_vector_hash": "e" * 64},
            {"attack_labeled_seconds": 4},
            {"normal_labeled_seconds": 8},
            {"event_policy_hash": "d" * 64},
            {"execution_mode": "REAL_AUTHORIZED_UTILITY_EXECUTION"},
            {"synthetic_authority_identity": "c" * 64},
        )
        for change in mutations:
            provisional = replace(self.custody, **change, custody_hash="")
            candidate = replace(provisional, custody_hash=_self_hash(provisional, "custody_hash"))
            self.assertCustodyRejected(candidate)

    def test_09_label_custody_issuance_metadata_missing_stale_and_gc_reject(self) -> None:
        key = id(self.custody)
        saved = metrics_v1._ISSUED_LABEL_CUSTODIES[key]
        other = self._new_custody(self.labels)
        variants = (
            (weakref.ref(other), *saved[1:]),
            (saved[0], "f" * 64, *saved[2:]),
            (*saved[:2], "e" * 64, *saved[3:]),
            (*saved[:3], "d" * 64, *saved[4:]),
            (*saved[:4], 11, *saved[5:]),
            (*saved[:5], 4, saved[6]),
            (*saved[:6], 8),
        )
        try:
            for variant in variants:
                metrics_v1._ISSUED_LABEL_CUSTODIES[key] = variant
                self.assertCustodyRejected(self.custody)
            metrics_v1._ISSUED_LABEL_CUSTODIES.pop(key, None)
            self.assertCustodyRejected(self.custody)
        finally:
            metrics_v1._ISSUED_LABEL_CUSTODIES[key] = saved
        temporary = self._new_custody(self.labels)
        temporary_key = id(temporary)
        temporary_ref = weakref.ref(temporary)
        del temporary
        gc.collect()
        self.assertIsNone(temporary_ref())
        self.assertNotIn(temporary_key, metrics_v1._ISSUED_LABEL_CUSTODIES)

    def test_10_canonical_formed_alarm_episode_validation(self) -> None:
        valid_sets = ((), _intervals(((0, 1),)), _intervals(((0, 1), (2, 4), (7, 8))))
        for episodes in valid_sets:
            metric = metrics_v1.attack_event_recall_v1(self.custody, episodes)
            self.assertEqual(metrics_v1.validate_bound_metric_v1(metric), metric.metric_hash)

    def test_11_noncanonical_formed_alarm_episodes_reject(self) -> None:
        invalid: tuple[object, ...] = (
            [metrics_v1.IntervalV1(0, 1)],
            _intervals(((0, 1), (0, 1))),
            _intervals(((0, 3), (2, 4))),
            _intervals(((0, 1), (1, 2))),
            _intervals(((3, 4), (0, 1))),
            _intervals(((0, 11),)),
            (object(),),
        )
        for episodes in invalid:
            with self.assertRaises(UtilityEvaluatorV1Error):
                metrics_v1.attack_event_recall_v1(self.custody, episodes)  # type: ignore[arg-type]
            with self.assertRaises(UtilityEvaluatorV1Error):
                metrics_v1.normal_far_episodes_per_hour_v1(self.custody, episodes)  # type: ignore[arg-type]

    def test_12_attack_event_recall_matches_independent_oracle(self) -> None:
        cases = (
            ((0, 0, 0), ()),
            ((0, 1, 1, 0), ()),
            ((0, 1, 1, 0), ((1, 2),)),
            ((0, 1, 1, 1, 1, 0), ((1, 2), (3, 4))),
            ((0, 1, 0, 1, 0), ((1, 2),)),
            ((0, 1, 0, 1, 0), ((1, 2), (3, 4))),
            ((0, 1, 1, 0), ((3, 4),)),
            ((0, 1, 0, 1, 0), ((0, 5),)),
        )
        for labels, interval_values in cases:
            custody = self._new_custody(labels)
            episodes = _intervals(interval_values)
            expected = _oracle_recall(labels, interval_values)
            metric = metrics_v1.attack_event_recall_v1(custody, episodes)
            self.assertEqual((metric.numerator, metric.denominator, metric.value), expected)
            self.assertEqual(metric.metric_name, "attack_event_recall")
            self.assertEqual(metric.formula_identity, EXPECTED_RECALL_FORMULA)

    def test_13_normal_far_matches_independent_oracle(self) -> None:
        cases = (
            ((1, 1, 1), ()),
            ((0, 0, 0), ()),
            ((0, 1, 1, 0), ((0, 1),)),
            ((0, 1, 1, 0, 0, 0), ((0, 1), (4, 5))),
            ((0, 1, 1, 0), ((1, 2),)),
            ((0, 1, 1, 0), ((0, 3),)),
            ((0,) * 3600, ((0, 1),)),
        )
        for labels, interval_values in cases:
            custody = self._new_custody(labels)
            episodes = _intervals(interval_values)
            expected = _oracle_far(labels, interval_values)
            metric = metrics_v1.normal_far_episodes_per_hour_v1(custody, episodes)
            self.assertEqual(metric.numerator, expected[0])
            self.assertAlmostEqual(metric.denominator, expected[1], places=15)
            self.assertEqual(metric.value, expected[2])
            self.assertEqual(metric.formula_identity, EXPECTED_FAR_FORMULA)

    def test_14_duplicate_raw_alarm_timestamp_dedupes_but_formed_duplicate_rejects(self) -> None:
        formed = metrics_v1.form_alarm_episodes_v1((0, 0, 0))
        self.assertEqual(tuple((item.start, item.end) for item in formed), ((0, 1),))
        metric = metrics_v1.normal_far_episodes_per_hour_v1(self.custody, formed)
        self.assertEqual(metric.numerator, 1)
        with self.assertRaises(UtilityEvaluatorV1Error):
            metrics_v1.normal_far_episodes_per_hour_v1(self.custody, formed + formed)

    def test_15_bound_metric_factory_outputs_and_policy_bindings(self) -> None:
        for metric in (self.recall, self.far):
            self.assertEqual(metrics_v1.validate_bound_metric_v1(metric), metric.metric_hash)
            self.assertEqual(metric.execution_mode, "SYNTHETIC_CONTRACT_ONLY")
            self.assertEqual(metric.metric_policy_hash, EXPECTED_METRIC_POLICY)
        self.assertEqual(
            (self.recall.numerator, self.recall.denominator, self.recall.value),
            _oracle_recall(self.labels, ((0, 1), (3, 4), (7, 8))),
        )
        expected_far = _oracle_far(self.labels, ((0, 1), (3, 4), (7, 8)))
        self.assertEqual(self.far.numerator, expected_far[0])
        self.assertAlmostEqual(self.far.denominator, expected_far[1], places=15)
        self.assertEqual(self.far.value, expected_far[2])

    def test_16_bound_metric_reconstruction_copy_replace_pickle_reject(self) -> None:
        for metric in (self.recall, self.far):
            for candidate in (
                _reconstruct(metric),
                copy.copy(metric),
                copy.deepcopy(metric),
                replace(metric),
                pickle.loads(pickle.dumps(metric)),
            ):
                self.assertMetricRejected(candidate)

    def test_17_bound_metric_self_rehash_semantic_substitutions_reject(self) -> None:
        mutations = (
            {"execution_mode": "REAL_AUTHORIZED_UTILITY_EXECUTION"},
            {"metric_policy_hash": "f" * 64},
            {"metric_name": "arbitrary_metric"},
            {"formula_identity": "arbitrary_formula"},
            {"numerator": self.recall.numerator + 1},
            {"denominator": self.recall.denominator + 1.0},
            {"value": 0.125},
            {"defined": False},
            {"undefined_reason": "no_attack_events"},
            {"label_custody_hash": "e" * 64},
            {"alarm_episode_set_hash": "d" * 64},
        )
        for change in mutations:
            provisional = replace(self.recall, **change, metric_hash="")
            candidate = replace(provisional, metric_hash=_self_hash(provisional, "metric_hash"))
            self.assertMetricRejected(candidate)

    def test_18_direct_self_hashed_arbitrary_metric_rejects(self) -> None:
        provisional = metrics_v1.BoundMetricV1(
            "SYNTHETIC_CONTRACT_ONLY",
            EXPECTED_METRIC_POLICY,
            "arbitrary_metric",
            "arbitrary_formula",
            123.0,
            123,
            1.0,
            True,
            None,
            "a" * 64,
            "b" * 64,
            "",
        )
        candidate = replace(provisional, metric_hash=_self_hash(provisional, "metric_hash"))
        self.assertMetricRejected(candidate)

    def test_19_bound_metric_issuance_metadata_missing_stale_and_gc_reject(self) -> None:
        key = id(self.recall)
        saved = metrics_v1._ISSUED_BOUND_METRICS[key]
        other = metrics_v1.attack_event_recall_v1(self.custody, self.episodes)
        variants = (
            (weakref.ref(other), *saved[1:]),
            (saved[0], "f" * 64, *saved[2:]),
            (*saved[:2], "other-name", *saved[3:]),
            (*saved[:3], "other-formula", *saved[4:]),
            (*saved[:4], "e" * 64, saved[5]),
            (*saved[:5], "d" * 64),
        )
        try:
            for variant in variants:
                metrics_v1._ISSUED_BOUND_METRICS[key] = variant
                self.assertMetricRejected(self.recall)
            metrics_v1._ISSUED_BOUND_METRICS.pop(key, None)
            self.assertMetricRejected(self.recall)
        finally:
            metrics_v1._ISSUED_BOUND_METRICS[key] = saved
        temporary = metrics_v1.attack_event_recall_v1(self.custody, self.episodes)
        temporary_key = id(temporary)
        temporary_ref = weakref.ref(temporary)
        del temporary
        gc.collect()
        self.assertIsNone(temporary_ref())
        self.assertNotIn(temporary_key, metrics_v1._ISSUED_BOUND_METRICS)

    def test_20_rule_prediction_factory_output_and_full_authority_binding(self) -> None:
        artifact = self.rule_artifact
        self.assertEqual(metrics_v1.validate_rule_prediction_artifact_v1(artifact), artifact.artifact_hash)
        self.assertEqual(artifact.evaluator_implementation_identity, EXPECTED_R3_IDENTITY)
        self.assertEqual(artifact.common_portfolio, "COMMON-42")
        self.assertEqual(artifact.common_relation_count, 42)
        self.assertFalse(artifact.scientific_eligible)
        self.assertEqual(artifact.error_count, 0)

    def test_21_rule_prediction_reconstruction_copy_replace_pickle_reject(self) -> None:
        for candidate in (
            _reconstruct(self.rule_artifact),
            copy.copy(self.rule_artifact),
            copy.deepcopy(self.rule_artifact),
            replace(self.rule_artifact),
            pickle.loads(pickle.dumps(self.rule_artifact)),
        ):
            self.assertRuleRejected(candidate)

    def test_22_rule_prediction_full_content_self_rehash_mutations_reject(self) -> None:
        artifact = self.rule_artifact
        mutations = (
            {"execution_mode": "REAL_AUTHORIZED_UTILITY_EXECUTION"},
            {"synthetic_authority_identity": "f" * 64},
            {"scientific_eligible": True},
            {"evaluator_version": "V2"},
            {"evaluator_implementation_identity": authority_v1.R2_EVALUATOR_IMPLEMENTATION_IDENTITY},
            {"evaluator_authority_bundle_hash": "e" * 64},
            {"v4_authority_hash": "d" * 64},
            {"common_portfolio": "T2-39"},
            {"common_relation_count": 41},
            {"main_descriptor_hash": "c" * 64},
            {"supplement_descriptor_hash": "b" * 64},
            {"combined_source_census_contract_hash": "a" * 64},
            {"dataset_manifest_identity": "other-dataset"},
            {"split_identity": "other-split"},
            {"source_file_identity": "other-file"},
            {"opportunity_census_identity": "9" * 64},
            {"denominator_policy": "CALLER_SELECTED"},
            {"predictions": artifact.predictions[:-1]},
            {"predictions": artifact.predictions + artifact.predictions[:1]},
            {"predictions": tuple(reversed(artifact.predictions))},
            {"trace_identities": artifact.trace_identities[:-1]},
            {"evaluated_count": artifact.evaluated_count + 1},
            {"alarm_count": artifact.alarm_count + 1},
            {"abstain_count": artifact.abstain_count + 1},
            {"error_count": 1},
        )
        for change in mutations:
            provisional = replace(artifact, **change, artifact_hash="")
            candidate = replace(provisional, artifact_hash=_self_hash(provisional, "artifact_hash"))
            self.assertRuleRejected(candidate)

    def test_23_rule_prediction_issuance_missing_stale_and_gc_reject(self) -> None:
        artifact = self.rule_artifact
        key = id(artifact)
        saved = metrics_v1._ISSUED_RULE_ARTIFACTS[key]
        other = self._new_rule_artifact()
        variants = (
            (weakref.ref(other), *saved[1:]),
            (saved[0], "f" * 64, *saved[2:]),
            (saved[0], saved[1], authority_v1.R2_EVALUATOR_IMPLEMENTATION_IDENTITY, saved[3]),
            (saved[0], saved[1], saved[2], "e" * 64),
        )
        try:
            for variant in variants:
                metrics_v1._ISSUED_RULE_ARTIFACTS[key] = variant
                self.assertRuleRejected(artifact)
            metrics_v1._ISSUED_RULE_ARTIFACTS.pop(key, None)
            self.assertRuleRejected(artifact)
        finally:
            metrics_v1._ISSUED_RULE_ARTIFACTS[key] = saved
        temporary = self._new_rule_artifact()
        temporary_key = id(temporary)
        temporary_ref = weakref.ref(temporary)
        del temporary
        gc.collect()
        self.assertIsNone(temporary_ref())
        self.assertNotIn(temporary_key, metrics_v1._ISSUED_RULE_ARTIFACTS)

    def test_24_detector_factory_and_independent_authority_replay(self) -> None:
        expected = _independent_hash(
            {
                "artifact_type": "task039e3_r2r_utility_evaluator_v1_synthetic_detector_authority",
                "evaluator_version": "TASK039E3_R2R_UTILITY_EVALUATOR_V1",
                "execution_mode": "SYNTHETIC_CONTRACT_ONLY",
                "scientific_eligibility": False,
                "real_detector_authority": False,
                "detector_science_executed": False,
            }
        )
        self.assertEqual(expected, EXPECTED_DETECTOR_AUTHORITY)
        detector = self._new_detector()
        self.assertEqual(metrics_v1.validate_detector_prediction_artifact_v1(detector), detector.artifact_hash)
        self.assertEqual(detector.detector_authority_identity, expected)
        self.assertFalse(detector.scientific_eligible)

    def test_25_detector_nine_historical_and_serialization_attacks_reject(self) -> None:
        detector = self._new_detector()
        candidates = [
            _reconstruct(detector),
            copy.deepcopy(detector),
            replace(detector),
            pickle.loads(pickle.dumps(detector)),
        ]
        changes = (
            {"detector_authority_identity": "b" * 64},
            {"detector_authority_identity": "not-a-sha"},
            {"dataset_manifest_identity": "other-dataset"},
            {"split_identity": "other-split"},
            {"source_file_identity": "other-file"},
            {"point_predictions": (True,) + detector.point_predictions[1:]},
        )
        for change in changes:
            provisional = replace(detector, **change, artifact_hash="")
            candidates.append(replace(provisional, artifact_hash=_self_hash(provisional, "artifact_hash")))
        for candidate in candidates:
            self.assertDetectorRejected(candidate)

    def test_26_detector_extended_prediction_and_authority_attacks_reject(self) -> None:
        detector = self._new_detector()
        original = detector.point_predictions
        mutations: tuple[dict[str, object], ...] = (
            {"point_predictions": original + (False,)},
            {"point_predictions": original[:-1]},
            {"point_predictions": tuple(reversed((True,) + original[1:]))},
            {"point_predictions": list(original)},
            {"point_predictions": (1,) + original[1:]},
            {"point_predictions": (1.0,) + original[1:]},
            {"point_predictions": ("false",) + original[1:]},
            {"point_predictions": ()},
            {"artifact_type": "wrong"},
            {"execution_mode": "REAL_AUTHORIZED_UTILITY_EXECUTION"},
            {"scientific_eligible": True},
        )
        for change in mutations:
            provisional = replace(detector, **change, artifact_hash="")
            candidate = replace(provisional, artifact_hash=_self_hash(provisional, "artifact_hash"))
            self.assertDetectorRejected(candidate)
        for identity in (EXPECTED_DETECTOR_AUTHORITY, "a" * 64, "malformed", "", None):
            with self.assertRaises(UtilityEvaluatorV1Error):
                self._new_detector(detector_authority_identity=identity)

    def test_27_detector_factory_input_types_issuance_and_gc_reject(self) -> None:
        for change in (
            {"dataset_manifest_identity": ""},
            {"split_identity": ""},
            {"source_file_identity": ""},
            {"point_predictions": [False]},
            {"point_predictions": (0,)},
            {"point_predictions": (1.0,)},
        ):
            with self.assertRaises(UtilityEvaluatorV1Error):
                self._new_detector(**change)
        detector = self._new_detector()
        other = self._new_detector()
        key = id(detector)
        saved = metrics_v1._ISSUED_DETECTOR_ARTIFACTS[key]
        variants = (
            (weakref.ref(other), *saved[1:]),
            (saved[0], "f" * 64, *saved[2:]),
            (saved[0], saved[1], "e" * 64, *saved[3:]),
            (*saved[:3], "other-dataset", *saved[4:]),
            (*saved[:4], "other-split", *saved[5:]),
            (*saved[:5], "other-file", saved[6]),
            (*saved[:6], "d" * 64),
        )
        try:
            for variant in variants:
                metrics_v1._ISSUED_DETECTOR_ARTIFACTS[key] = variant
                self.assertDetectorRejected(detector)
            metrics_v1._ISSUED_DETECTOR_ARTIFACTS.pop(key, None)
            self.assertDetectorRejected(detector)
        finally:
            metrics_v1._ISSUED_DETECTOR_ARTIFACTS[key] = saved
        temporary = self._new_detector()
        temporary_key = id(temporary)
        temporary_ref = weakref.ref(temporary)
        del temporary
        gc.collect()
        self.assertIsNone(temporary_ref())
        self.assertNotIn(temporary_key, metrics_v1._ISSUED_DETECTOR_ARTIFACTS)

    def test_28_comparison_accepts_same_content_and_rejects_forged_detector(self) -> None:
        detector = self._new_detector()
        other_rule = self._new_rule_artifact()
        self.assertEqual(other_rule.artifact_hash, self.rule_artifact.artifact_hash)
        comparison = metrics_v1.build_synthetic_rule_detector_comparison_input_v1(
            detector=detector,
            d1_rule_artifact=self.rule_artifact,
            d2_rule_artifact=other_rule,
        )
        self.assertFalse(comparison.scientific_eligible)
        self.assertFalse(comparison.fusion_authorized)
        self.assertTrue(comparison.same_rule_artifact_required)
        provisional = replace(
            detector,
            point_predictions=(True,) + detector.point_predictions[1:],
            artifact_hash="",
        )
        forged = replace(provisional, artifact_hash=_self_hash(provisional, "artifact_hash"))
        for candidate in (_reconstruct(detector), copy.deepcopy(detector), forged):
            with self.assertRaises(UtilityEvaluatorV1Error):
                metrics_v1.build_synthetic_rule_detector_comparison_input_v1(
                    detector=candidate,  # type: ignore[arg-type]
                    d1_rule_artifact=self.rule_artifact,
                    d2_rule_artifact=self.rule_artifact,
                )

    def test_29_comparison_dataset_split_file_and_rule_content_mismatch_reject(self) -> None:
        for change in (
            {"dataset_manifest_identity": "other-dataset"},
            {"split_identity": "other-split"},
            {"source_file_identity": "other-file"},
        ):
            with self.assertRaises(UtilityEvaluatorV1Error):
                metrics_v1.build_synthetic_rule_detector_comparison_input_v1(
                    detector=self._new_detector(**change),
                    d1_rule_artifact=self.rule_artifact,
                    d2_rule_artifact=self.rule_artifact,
                )
        provisional = replace(
            self.rule_artifact,
            alarm_count=self.rule_artifact.alarm_count + 1,
            artifact_hash="",
        )
        forged_rule = replace(provisional, artifact_hash=_self_hash(provisional, "artifact_hash"))
        with self.assertRaises(UtilityEvaluatorV1Error):
            metrics_v1.build_synthetic_rule_detector_comparison_input_v1(
                detector=self._new_detector(),
                d1_rule_artifact=self.rule_artifact,
                d2_rule_artifact=forged_rule,
            )

    def test_30_synthetic_artifacts_never_promote_to_scientific(self) -> None:
        with self.assertRaises(UtilityEvaluatorV1Error):
            metrics_v1.validate_scientific_rule_prediction_artifact_v1(self.rule_artifact)
        detector = self._new_detector()
        comparison = metrics_v1.build_synthetic_rule_detector_comparison_input_v1(
            detector=detector,
            d1_rule_artifact=self.rule_artifact,
            d2_rule_artifact=self.rule_artifact,
        )
        with self.assertRaises(UtilityEvaluatorV1Error):
            metrics_v1.validate_scientific_rule_detector_comparison_input_v1(comparison)
        promoted_rule = replace(self.rule_artifact, scientific_eligible=True)
        promoted_detector = replace(detector, scientific_eligible=True)
        self.assertRuleRejected(promoted_rule)
        self.assertDetectorRejected(promoted_detector)
        promoted_comparison = replace(comparison, scientific_eligible=True, artifact_hash="")
        promoted_comparison = replace(
            promoted_comparison,
            artifact_hash=_self_hash(promoted_comparison, "artifact_hash"),
        )
        with self.assertRaises(UtilityEvaluatorV1Error):
            metrics_v1.validate_scientific_rule_detector_comparison_input_v1(
                promoted_comparison
            )


if __name__ == "__main__":
    unittest.main()
