"""Focused R1 custody/canonicalization tests for evaluator metrics.

All values in this module are synthetic contract fixtures.  No private
registry, locator, HAI file, label file, or attack-interval artifact is read.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import fields, replace
import gc
import unittest
from weakref import ref

from paperworks.v6 import task039e3_r2r_utility_evaluator_metrics_v1 as metrics_module
from paperworks.v6.task039e3_r2r_utility_evaluator_metrics_v1 import (
    ATTACK_EVENT_RECALL_FORMULA,
    NORMAL_FAR_FORMULA,
    BoundMetricV1,
    IntervalV1,
    attack_event_recall_v1,
    build_synthetic_label_event_custody_v1,
    form_alarm_episodes_v1,
    normal_far_episodes_per_hour_v1,
    validate_bound_metric_v1,
    validate_synthetic_label_event_custody_v1,
)
from paperworks.v6.task039e3_r2r_utility_evaluator_types_v1 import (
    SYNTHETIC_CONTRACT_ONLY,
    UtilityEvaluatorV1Error,
    dataclass_payload_v1,
    stable_hash_v1,
)
from paperworks.v6.task039e3_r2r_utility_protocol_v4 import (
    CORRECTED_METRIC_POLICY_HASH,
)


def _exact_reconstruction(value: object) -> object:
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


class UtilityEvaluatorV1R1MetricCustodyTests(unittest.TestCase):
    def _custody(self, labels: tuple[int, ...] = (1, 1, 0, 0, 1, 0, 0, 0)):
        return build_synthetic_label_event_custody_v1(
            labels=labels,
            dataset_manifest_identity="R1_SYNTHETIC_DATASET",
            split_identity="R1_SYNTHETIC_SPLIT",
            source_file_identity="R1_SYNTHETIC_FILE",
        )

    def test_factory_label_custody_passes_but_copies_and_reconstruction_reject(self) -> None:
        custody = self._custody()
        self.assertEqual(validate_synthetic_label_event_custody_v1(custody), custody.custody_hash)
        attacks = (
            _exact_reconstruction(custody),
            deepcopy(custody),
            replace(custody),
        )
        for candidate in attacks:
            self.assertIsNot(candidate, custody)
            with self.subTest(kind=type(candidate).__name__), self.assertRaises(UtilityEvaluatorV1Error):
                validate_synthetic_label_event_custody_v1(candidate)

    def test_label_and_metric_issuance_entries_cleanup_automatically(self) -> None:
        custody = self._custody()
        custody_id = id(custody)
        custody_ref = ref(custody)
        self.assertIn(custody_id, metrics_module._ISSUED_LABEL_CUSTODIES)

        metric = attack_event_recall_v1(custody, ())
        metric_id = id(metric)
        metric_ref = ref(metric)
        self.assertIn(metric_id, metrics_module._ISSUED_BOUND_METRICS)

        del metric
        gc.collect()
        self.assertIsNone(metric_ref())
        self.assertNotIn(metric_id, metrics_module._ISSUED_BOUND_METRICS)

        del custody
        gc.collect()
        self.assertIsNone(custody_ref())
        self.assertNotIn(custody_id, metrics_module._ISSUED_LABEL_CUSTODIES)

    def test_label_event_relocation_old_hash_and_self_rehash_reject(self) -> None:
        custody = self._custody((1, 1, 0, 0, 1, 0, 0))
        relocated = replace(
            custody,
            attack_events=(IntervalV1(1, 3), IntervalV1(5, 6)),
        )
        with self.assertRaises(UtilityEvaluatorV1Error):
            validate_synthetic_label_event_custody_v1(relocated)
        with self.assertRaises(UtilityEvaluatorV1Error):
            validate_synthetic_label_event_custody_v1(_rehash(relocated, "custody_hash"))

    def test_label_event_set_and_policy_mutations_reject(self) -> None:
        custody = self._custody()
        candidates = (
            replace(custody, attack_events=tuple(reversed(custody.attack_events))),
            replace(custody, attack_events=custody.attack_events + (IntervalV1(6, 7),)),
            replace(custody, attack_events=custody.attack_events[:-1]),
            replace(custody, event_policy_hash="f" * 64),
        )
        for candidate in candidates:
            with self.subTest(events=candidate.attack_events), self.assertRaises(UtilityEvaluatorV1Error):
                validate_synthetic_label_event_custody_v1(_rehash(candidate, "custody_hash"))

    def test_canonical_alarm_episode_inputs_pass(self) -> None:
        custody = self._custody((0,) * 8)
        one = normal_far_episodes_per_hour_v1(custody, (IntervalV1(0, 1),))
        separated = normal_far_episodes_per_hour_v1(
            custody,
            (IntervalV1(0, 1), IntervalV1(2, 4), IntervalV1(6, 7)),
        )
        self.assertEqual(one.numerator, 1)
        self.assertEqual(separated.numerator, 3)

    def test_noncanonical_alarm_episode_tuples_reject(self) -> None:
        custody = self._custody((0,) * 8)
        invalid = (
            (IntervalV1(0, 1), IntervalV1(0, 1)),
            (IntervalV1(0, 3), IntervalV1(2, 4)),
            (IntervalV1(0, 1), IntervalV1(1, 2)),
            (IntervalV1(4, 5), IntervalV1(1, 2)),
            (IntervalV1(7, 9),),
        )
        for episodes in invalid:
            with self.subTest(episodes=episodes), self.assertRaises(UtilityEvaluatorV1Error):
                normal_far_episodes_per_hour_v1(custody, episodes)
        with self.assertRaises(UtilityEvaluatorV1Error):
            normal_far_episodes_per_hour_v1(custody, [IntervalV1(0, 1)])
        with self.assertRaises(UtilityEvaluatorV1Error):
            IntervalV1(True, 1)
        with self.assertRaises(UtilityEvaluatorV1Error):
            IntervalV1(0.0, 1)

    def test_duplicate_episode_injection_rejects_in_recall_and_far(self) -> None:
        custody = self._custody((0, 0, 0, 0))
        episode = IntervalV1(0, 1)
        self.assertEqual(normal_far_episodes_per_hour_v1(custody, (episode,)).numerator, 1)
        for function in (attack_event_recall_v1, normal_far_episodes_per_hour_v1):
            with self.subTest(function=function.__name__), self.assertRaises(UtilityEvaluatorV1Error):
                function(custody, (episode, episode))

    def test_factory_metrics_pass_but_reconstruction_copy_and_replace_reject(self) -> None:
        custody = self._custody()
        episodes = form_alarm_episodes_v1((0, 1, 3, 6))
        metrics = (
            attack_event_recall_v1(custody, episodes),
            normal_far_episodes_per_hour_v1(custody, episodes),
        )
        for metric in metrics:
            self.assertEqual(validate_bound_metric_v1(metric), metric.metric_hash)
            for candidate in (_exact_reconstruction(metric), deepcopy(metric), replace(metric)):
                self.assertIsNot(candidate, metric)
                with self.subTest(metric=metric.metric_name), self.assertRaises(UtilityEvaluatorV1Error):
                    validate_bound_metric_v1(candidate)

    def test_direct_and_self_rehashed_forged_metric_reject(self) -> None:
        forged = BoundMetricV1(
            execution_mode=SYNTHETIC_CONTRACT_ONLY,
            metric_policy_hash=CORRECTED_METRIC_POLICY_HASH,
            metric_name="forged_metric",
            formula_identity="FORGED_FORMULA",
            value=3.5,
            numerator=7,
            denominator=2.0,
            defined=True,
            undefined_reason=None,
            label_custody_hash="a" * 64,
            alarm_episode_set_hash="b" * 64,
            metric_hash="",
        )
        for candidate in (forged, _rehash(forged, "metric_hash")):
            with self.assertRaises(UtilityEvaluatorV1Error):
                validate_bound_metric_v1(candidate)

    def test_metric_semantic_and_custody_mutations_reject(self) -> None:
        custody = self._custody()
        metric = attack_event_recall_v1(custody, form_alarm_episodes_v1((0, 1, 3, 6)))
        mutations = (
            {"formula_identity": NORMAL_FAR_FORMULA},
            {"metric_name": "normal_false_alarm_rate_per_hour"},
            {"numerator": 0, "value": 0.0},
            {"denominator": 4.0, "value": 0.25},
            {"label_custody_hash": "a" * 64},
            {"alarm_episode_set_hash": "b" * 64},
        )
        for changes in mutations:
            candidate = _rehash(replace(metric, **changes), "metric_hash")
            with self.subTest(changes=changes), self.assertRaises(UtilityEvaluatorV1Error):
                validate_bound_metric_v1(candidate)

    def test_canonical_metric_oracles_are_unchanged(self) -> None:
        custody = self._custody()
        episodes = form_alarm_episodes_v1((0, 1, 3, 6))
        recall = attack_event_recall_v1(custody, episodes)
        far = normal_far_episodes_per_hour_v1(custody, episodes)
        self.assertEqual(
            (recall.metric_name, recall.formula_identity, recall.numerator, recall.denominator, recall.value),
            ("attack_event_recall", ATTACK_EVENT_RECALL_FORMULA, 1, 2.0, 0.5),
        )
        self.assertEqual(
            (far.metric_name, far.formula_identity, far.numerator, far.denominator, far.value),
            (
                "normal_false_alarm_rate_per_hour",
                NORMAL_FAR_FORMULA,
                2,
                5.0 / 3600.0,
                2 / (5.0 / 3600.0),
            ),
        )


if __name__ == "__main__":
    unittest.main()
