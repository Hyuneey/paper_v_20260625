from __future__ import annotations

import json
import math
from pathlib import Path
import unittest

from paperworks.v6.task039e3_r2r_utility_protocol_v1 import (
    IntervalV1,
    MetricValueV1,
    SyntheticCandidateDecisionV1,
    alarm_episode_precision_v1,
    attack_event_recall_v1,
    decision_index_v1,
    derive_synthetic_attack_events_v1,
    evaluate_synthetic_rule_window_v1,
    event_f1_v1,
    exact_mcnemar_two_sided_v1,
    form_alarm_episodes_v1,
    normal_false_alarm_rate_per_hour_v1,
)


ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "docs" / "task_reports"


def _base_window(**changes: object) -> dict[str, object]:
    value: dict[str, object] = {
        "event_index": 10,
        "horizon_seconds": 5,
        "source_pre_window": (0.0,) * 5,
        "source_post_window": (2.0,) * 5,
        "target_baseline_window": (10.0,) * 5,
        "target_response_window": (12.0,) * 3,
        "expected_source_direction": "step_up",
        "expected_target_direction": "increase",
        "source_step_threshold": 2.0,
        "source_stability_tolerance": 0.1,
        "target_noise_scale": 1.0,
    }
    value.update(changes)
    return value


class IndependentInterpreterAndMetricAuditTests(unittest.TestCase):
    def test_decision_indices_and_response_equality(self) -> None:
        self.assertEqual([decision_index_v1(10, h) for h in (1, 5, 10, 30, 60)], [13, 17, 22, 42, 72])
        equality = evaluate_synthetic_rule_window_v1(
            **_base_window(target_response_window=(11.0,) * 3)
        )
        self.assertEqual((equality.status, equality.anomaly), ("anomaly", True))

    def test_events_episodes_overlap_and_primary_metrics(self) -> None:
        events = derive_synthetic_attack_events_v1((0, 1, 1, 0, 1))
        alarms = form_alarm_episodes_v1((1, 1, 2, 4))
        self.assertEqual(events, (IntervalV1(1, 3), IntervalV1(4, 5)))
        self.assertEqual(alarms, (IntervalV1(1, 3), IntervalV1(4, 5)))
        self.assertEqual(attack_event_recall_v1(events, alarms).value, 1.0)
        self.assertEqual(alarm_episode_precision_v1(events, alarms).value, 1.0)

    def test_event_f1_custody_preimage_is_unfaithful(self) -> None:
        precision = MetricValueV1(0.5, 1, 2.0, True, None)
        recall = MetricValueV1(0.5, 1, 2.0, True, None)
        result = event_f1_v1(precision, recall)
        self.assertEqual(result.value, 0.5)
        self.assertEqual((result.numerator, result.denominator), (0, 1.0))
        self.assertNotEqual(result.value, result.numerator / result.denominator)
        inconsistent = MetricValueV1(0.9, 0, 1.0, True, None)
        self.assertEqual(inconsistent.value, 0.9)

    def test_nonbinary_synthetic_labels_are_silently_coerced(self) -> None:
        self.assertEqual(derive_synthetic_attack_events_v1((0.5,)), ())
        self.assertEqual(derive_synthetic_attack_events_v1((1.9,)), (IntervalV1(0, 1),))
        self.assertEqual(derive_synthetic_attack_events_v1((True,)), (IntervalV1(0, 1),))

    def test_normal_exposure_is_unbound_caller_input(self) -> None:
        events = (IntervalV1(10, 12),)
        false_alarm = (IntervalV1(1, 2),)
        first = normal_false_alarm_rate_per_hour_v1(events, false_alarm, normal_labeled_seconds=3_600)
        second = normal_false_alarm_rate_per_hour_v1(events, false_alarm, normal_labeled_seconds=7_200)
        self.assertEqual((first.value, second.value), (1.0, 0.5))

    def test_synthetic_state_and_numeric_guards_are_not_closed(self) -> None:
        invalid_state = SyntheticCandidateDecisionV1("anomaly", False, None)
        self.assertEqual((invalid_state.status, invalid_state.anomaly), ("anomaly", False))
        nan_threshold = evaluate_synthetic_rule_window_v1(
            **_base_window(source_step_threshold=math.nan)
        )
        self.assertIn(nan_threshold.status, {"no_trigger", "expected_response", "anomaly"})

    def test_exact_mcnemar_matches_small_enumeration(self) -> None:
        self.assertIsNone(exact_mcnemar_two_sided_v1(0, 0))
        for first in range(6):
            for second in range(6):
                if first + second == 0:
                    continue
                n = first + second
                k = min(first, second)
                expected = min(1.0, 2.0 * sum(math.comb(n, i) for i in range(k + 1)) / 2**n)
                self.assertEqual(exact_mcnemar_two_sided_v1(first, second), expected)

    def test_interpretation_margin_and_cost_baseline_are_open(self) -> None:
        authority = json.loads(
            (REPORTS / "TASK-039E3_R2R_UTILITY_PROTOCOL_AUTHORITY_POLICY.json").read_text(encoding="utf-8")
        )
        self.assertIn("material", authority["T2_interpretation_categories"]["A"])
        self.assertNotIn("material_coverage_loss_margin", authority)
        self.assertNotIn("construction_call_costs_by_arm", authority)


if __name__ == "__main__":
    unittest.main()
