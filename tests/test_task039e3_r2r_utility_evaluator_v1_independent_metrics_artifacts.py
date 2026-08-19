"""Independent metric/custody audit for Utility Evaluator V1.

The expected results below are derived directly from the frozen half-open,
file-local event definitions in the lower metric authority.  This module does
not import or reuse the evaluator implementation tests.  The two rejection
tests intentionally expose the fail-open behavior found by the independent
audit; they are frozen evidence and must not be weakened to make production
pass.
"""

from __future__ import annotations

from dataclasses import replace
import unittest

from paperworks.v6.task039e3_r2r_utility_evaluator_metrics_v1 import (
    ATTACK_EVENT_RECALL_FORMULA,
    NORMAL_FAR_FORMULA,
    BoundMetricV1,
    IntervalV1,
    attack_event_recall_v1,
    build_synthetic_label_event_custody_v1,
    derive_attack_events_v1,
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


INDEPENDENT_SEMANTIC_ATTACK_CLASSES = 3
EXPECTED_ACCEPTED_INVALID_CASES = 0


def independent_attack_events(labels: tuple[int, ...]) -> tuple[tuple[int, int], ...]:
    """Maximal half-open runs of exact integer one values."""

    result: list[tuple[int, int]] = []
    start: int | None = None
    for index, label in enumerate(labels + (0,)):
        if type(label) is not int or label not in (0, 1):
            raise ValueError("AUDIT_LABEL_DOMAIN")
        if label == 1 and start is None:
            start = index
        elif label == 0 and start is not None:
            result.append((start, index))
            start = None
    return tuple(result)


def independent_alarm_episodes(timestamps: tuple[int, ...]) -> tuple[tuple[int, int], ...]:
    """Maximal half-open runs after integer validation, sorting, and dedupe."""

    if any(type(value) is not int or value < 0 for value in timestamps):
        raise ValueError("AUDIT_ALARM_DOMAIN")
    ordered = sorted(set(timestamps))
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


def rehash_dataclass(value: object, *, hash_field: str) -> object:
    provisional = replace(value, **{hash_field: ""})
    payload = dataclass_payload_v1(provisional, exclude=(hash_field,))
    return replace(provisional, **{hash_field: stable_hash_v1(payload)})


class IndependentMetricArtifactAudit(unittest.TestCase):
    def test_lower_event_oracles_match_canonical_unmutated_examples(self) -> None:
        labels = (1, 1, 0, 1, 0, 0, 1, 1)
        expected_attacks = independent_attack_events(labels)
        observed_attacks = tuple(
            (event.start, event.end) for event in derive_attack_events_v1(labels)
        )
        self.assertEqual(expected_attacks, ((0, 2), (3, 4), (6, 8)))
        self.assertEqual(observed_attacks, expected_attacks)

        timestamps = (9, 1, 2, 2, 4, 8)
        expected_alarms = independent_alarm_episodes(timestamps)
        observed_alarms = tuple(
            (event.start, event.end) for event in form_alarm_episodes_v1(timestamps)
        )
        self.assertEqual(expected_alarms, ((1, 3), (4, 5), (8, 10)))
        self.assertEqual(observed_alarms, expected_alarms)

    def test_lower_metric_oracles_match_canonical_unmutated_examples(self) -> None:
        labels = (1, 1, 0, 0, 1, 0, 0, 0)
        custody = build_synthetic_label_event_custody_v1(
            labels=labels,
            dataset_manifest_identity="AUDIT_SYNTHETIC_DATASET",
            split_identity="AUDIT_SYNTHETIC_SPLIT",
            source_file_identity="AUDIT_SYNTHETIC_FILE",
        )
        alarms = form_alarm_episodes_v1((0, 1, 3, 6))
        recall = attack_event_recall_v1(custody, alarms)
        far = normal_far_episodes_per_hour_v1(custody, alarms)

        # Independent half-open overlap: [0,2) covers only the first of two
        # attacks; [3,4) and [6,7) are two false-alarm episodes.
        self.assertEqual((recall.numerator, recall.denominator, recall.value), (1, 2.0, 0.5))
        self.assertEqual(recall.formula_identity, ATTACK_EVENT_RECALL_FORMULA)
        self.assertEqual(far.numerator, 2)
        self.assertEqual(far.denominator, 5.0 / 3600.0)
        self.assertEqual(far.value, 2 / (5.0 / 3600.0))
        self.assertEqual(far.formula_identity, NORMAL_FAR_FORMULA)

    def test_self_rehashed_label_custody_semantic_mutation_must_reject(self) -> None:
        labels = (1, 1, 0, 0, 1, 0, 0)
        custody = build_synthetic_label_event_custody_v1(
            labels=labels,
            dataset_manifest_identity="AUDIT_SYNTHETIC_DATASET",
            split_identity="AUDIT_SYNTHETIC_SPLIT",
            source_file_identity="AUDIT_SYNTHETIC_FILE",
        )
        self.assertEqual(
            tuple((event.start, event.end) for event in custody.attack_events),
            ((0, 2), (4, 5)),
        )

        # Preserve total attack seconds and interval separation, but move every
        # interval away from the frozen label-vector derivation.
        forged = replace(custody, attack_events=(IntervalV1(1, 3), IntervalV1(5, 6)))
        forged = rehash_dataclass(forged, hash_field="custody_hash")
        with self.assertRaises(UtilityEvaluatorV1Error):
            validate_synthetic_label_event_custody_v1(forged)

    def test_self_rehashed_metric_semantic_substitution_must_reject(self) -> None:
        # This artifact claims the current metric policy but substitutes every
        # scientific binding.  Arithmetic self-consistency is not authority.
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
        forged = rehash_dataclass(forged, hash_field="metric_hash")
        with self.assertRaises(UtilityEvaluatorV1Error):
            validate_bound_metric_v1(forged)

    def test_duplicate_alarm_episode_injection_must_not_inflate_far(self) -> None:
        labels = (0, 0, 0, 0)
        custody = build_synthetic_label_event_custody_v1(
            labels=labels,
            dataset_manifest_identity="AUDIT_SYNTHETIC_DATASET",
            split_identity="AUDIT_SYNTHETIC_SPLIT",
            source_file_identity="AUDIT_SYNTHETIC_FILE",
        )
        canonical_episode = IntervalV1(0, 1)
        canonical = normal_far_episodes_per_hour_v1(custody, (canonical_episode,))
        self.assertEqual(canonical.numerator, 1)

        # An authoritative episode set is maximal and duplicate-free.  Passing
        # the identical interval twice must reject rather than double count.
        with self.assertRaises(UtilityEvaluatorV1Error):
            normal_far_episodes_per_hour_v1(
                custody,
                (canonical_episode, canonical_episode),
            )


if __name__ == "__main__":
    unittest.main()
