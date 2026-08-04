from __future__ import annotations

import math
import unittest

from paperworks.feasibility.hai_continuous_step_v1 import (
    DirectionCandidateV1,
    HAIContinuousStepError,
    calibration_confirmation_values_v1,
    classify_multisource_isolation_v1,
    deduplicate_directional_relations_v1,
    derive_multifile_robust_scale_v1,
    derive_multifile_source_screening_parameters_v1,
    direction_agrees_strict_v1,
    evaluate_direction_candidate_v1,
    extract_multifile_events_v1,
    fit_candidate_passes_v1,
    select_direction_candidate_v1,
    transfer_rate_v1,
)
from paperworks.v6.continuous_step_protocol_v1 import (
    SustainedStepEventV1,
    cluster_step_events_v1,
    evaluate_step_candidate_v1,
    extract_sustained_step_events_v1,
    robust_one_step_scale_v1,
)


FIT1 = "hai-23.05/hai-train1.csv"
FIT2 = "hai-23.05/hai-train2.csv"
CAL = "hai-23.05/hai-train3.csv"


def event(index: int, direction: str = "step_up") -> SustainedStepEventV1:
    amplitude = 10.0 if direction == "step_up" else -10.0
    return SustainedStepEventV1(index, direction, 0.0, amplitude, amplitude, 1.0, 1.0)


class MultiFileScaleTests(unittest.TestCase):
    def test_no_cross_file_difference(self) -> None:
        scale = derive_multifile_robust_scale_v1({FIT1: [0.0] * 20, FIT2: [1000.0] * 20})
        self.assertEqual(scale, 1e-12)

    def test_single_file_parity_with_br1_scale(self) -> None:
        values = [0.0, 0.0, 1.0, 1.0, 3.0, 3.0, 4.0]
        self.assertEqual(
            derive_multifile_robust_scale_v1({FIT1: values}),
            robust_one_step_scale_v1(values),
        )

    def test_insufficient_nontrivial_amplitudes(self) -> None:
        self.assertIsNone(
            derive_multifile_source_screening_parameters_v1(
                {FIT1: [0.0] * 30, FIT2: [0.0] * 30}
            )
        )

    def test_fit_only_threshold_is_deterministic(self) -> None:
        values = [0.0] * 6
        for index in range(30):
            values.extend([float(index % 2) * 10.0] * 6)
        first = derive_multifile_source_screening_parameters_v1({FIT1: values, FIT2: values})
        second = derive_multifile_source_screening_parameters_v1({FIT1: values, FIT2: values})
        self.assertEqual(first, second)
        self.assertIsNotNone(first)

    def test_source_input_nonfinite_fails(self) -> None:
        with self.assertRaises(HAIContinuousStepError):
            derive_multifile_robust_scale_v1({FIT1: [0.0, math.nan]})


class EventTests(unittest.TestCase):
    def test_step_up_extraction(self) -> None:
        values = [0.0] * 10 + [10.0] * 10
        events = extract_multifile_events_v1(
            {FIT1: values}, source_step_threshold=5.0, source_stability_tolerance=0.1
        )[FIT1]
        self.assertEqual(events[0].direction, "step_up")

    def test_step_down_extraction(self) -> None:
        values = [10.0] * 10 + [0.0] * 10
        events = extract_multifile_events_v1(
            {FIT1: values}, source_step_threshold=5.0, source_stability_tolerance=0.1
        )[FIT1]
        self.assertEqual(events[0].direction, "step_down")

    def test_file_boundary_does_not_form_event(self) -> None:
        result = extract_multifile_events_v1(
            {FIT1: [0.0] * 20, FIT2: [10.0] * 20},
            source_step_threshold=5.0,
            source_stability_tolerance=0.1,
        )
        self.assertEqual(result, {FIT1: (), FIT2: ()})

    def test_single_file_event_parity_with_br1(self) -> None:
        values = [0.0] * 10 + [10.0] * 10
        expected = extract_sustained_step_events_v1(
            values, source_step_threshold=5.0, source_stability_tolerance=0.1
        )
        observed = extract_multifile_events_v1(
            {FIT1: values}, source_step_threshold=5.0, source_stability_tolerance=0.1
        )[FIT1]
        self.assertEqual(observed, expected)

    def test_unstable_pre_and_post_levels(self) -> None:
        unstable_pre = [0.0, 10.0, 0.0, 10.0, 0.0] + [20.0] * 5
        pre = evaluate_step_candidate_v1(
            unstable_pre, 5, source_step_threshold=5.0, source_stability_tolerance=0.1
        )
        self.assertEqual(pre.status, "unstable_pre_level")
        unstable_post = [0.0] * 5 + [20.0, 10.0, 20.0, 10.0, 20.0]
        post = evaluate_step_candidate_v1(
            unstable_post, 5, source_step_threshold=5.0, source_stability_tolerance=0.1
        )
        self.assertEqual(post.status, "unstable_post_level")

    def test_refractory_clustering_uses_largest_then_earliest(self) -> None:
        clustered = cluster_step_events_v1(
            (
                event(10),
                SustainedStepEventV1(12, "step_up", 0.0, 12.0, 12.0, 1.0, 1.0),
                SustainedStepEventV1(14, "step_up", 0.0, 12.0, 12.0, 1.0, 1.0),
            )
        )
        self.assertEqual(clustered[0].event_index, 12)

    def test_cross_source_isolation(self) -> None:
        result = classify_multisource_isolation_v1(
            {
                "P1_A": {FIT1: (event(10),), FIT2: ()},
                "P1_B": {FIT1: (event(12),), FIT2: ()},
            }
        )
        self.assertFalse(result["P1_A"][FIT1][0][1])
        self.assertFalse(result["P1_B"][FIT1][0][1])


class DirectionTests(unittest.TestCase):
    def test_strict_direction_agreement(self) -> None:
        self.assertTrue(
            direction_agrees_strict_v1(
                selected_train1=0.8,
                opposite_train1=0.1,
                selected_train2=0.7,
                opposite_train2=0.2,
            )
        )

    def test_directional_tie_is_rejected(self) -> None:
        self.assertFalse(
            direction_agrees_strict_v1(
                selected_train1=0.5,
                opposite_train1=0.5,
                selected_train2=0.7,
                opposite_train2=0.2,
            )
        )

    def test_ranking_order(self) -> None:
        candidates = [
            DirectionCandidateV1("increase", 10, (), (), 0, 0, 0.8, 0.8, 0.8, 2.0, 2.0, True),
            DirectionCandidateV1("increase", 5, (), (), 0, 0, 0.8, 0.8, 0.8, 2.0, 2.0, True),
            DirectionCandidateV1("decrease", 1, (), (), 0, 0, 0.7, 0.7, 0.7, -5.0, 5.0, True),
        ]
        selected = select_direction_candidate_v1(candidates)
        self.assertIsNotNone(selected)
        self.assertEqual(selected.horizon_seconds, 5)

    def test_no_agreeing_candidate(self) -> None:
        candidate = DirectionCandidateV1("increase", 1, (), (), 0, 0, 0.5, 0.5, 0.5, 0.0, 0.0, False)
        self.assertIsNone(select_direction_candidate_v1([candidate]))

    def test_fit_gate(self) -> None:
        candidate = DirectionCandidateV1(
            "increase", 5, tuple([2.0] * 10), tuple([2.0] * 10), 0, 0,
            1.0, 1.0, 1.0, 2.0, 2.0, True,
        )
        self.assertTrue(fit_candidate_passes_v1(candidate))

    def test_target_increase_and_decrease(self) -> None:
        events = {FIT1: (event(10),), FIT2: (event(10),)}
        increase = [0.0] * 11 + [5.0] * 20
        decrease = [5.0] * 11 + [0.0] * 20
        inc = evaluate_direction_candidate_v1(
            target_by_file={FIT1: increase, FIT2: increase},
            isolated_events_by_file=events,
            source_step_direction="step_up",
            target_direction="increase",
            horizon_seconds=1,
            target_noise_scale=1.0,
        )
        dec = evaluate_direction_candidate_v1(
            target_by_file={FIT1: decrease, FIT2: decrease},
            isolated_events_by_file=events,
            source_step_direction="step_up",
            target_direction="decrease",
            horizon_seconds=1,
            target_noise_scale=1.0,
        )
        self.assertEqual(inc.pooled_consistency, 1.0)
        self.assertEqual(dec.pooled_consistency, 1.0)

    def test_train3_confirmation_and_right_censoring(self) -> None:
        values = [0.0] * 11 + [5.0] * 20
        usable, censored, consistency, opposite, _, unchanged, confirmed = calibration_confirmation_values_v1(
            target_values=values,
            isolated_events=(event(10), event(29)),
            source_step_direction="step_up",
            target_direction="increase",
            horizon_seconds=1,
            target_noise_scale=1.0,
        )
        self.assertEqual((usable, censored), (1, 1))
        self.assertGreater(consistency, opposite)
        self.assertTrue(unchanged)
        self.assertFalse(confirmed)  # fewer than five calibration events

    def test_transfer_zero_denominator(self) -> None:
        self.assertEqual(transfer_rate_v1(0, 0), 0.0)


if __name__ == "__main__":
    unittest.main()
