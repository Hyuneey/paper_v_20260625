from __future__ import annotations

import inspect
import unittest

from paperworks.profiling import task039d2_audit_reference_v1 as audit
from paperworks.v6.continuous_step_protocol_v1 import (
    calibration_confirmation_gate_v1,
    classify_event_isolation_v1,
    evaluate_target_response_v1,
    extract_sustained_step_events_v1,
)
from paperworks.v6.relation_profiling_protocol_v1 import (
    FROZEN_SOURCES,
    FROZEN_TARGETS,
)
from tests.task039d2_audit_support import (
    make_input_set,
    one_relation,
    response_target,
    stepped_source,
    synthetic_value_map,
)


class IndependentReferenceParityTests(unittest.TestCase):
    def test_source_event_reconstruction_matches_frozen_reference(self) -> None:
        for direction in ("step_up", "step_down"):
            values = stepped_source(direction=direction)
            actual = audit.reconstruct_source_events_reference_v1(
                values,
                source_step_threshold=0.5,
                source_stability_tolerance=0.1,
            )
            frozen = extract_sustained_step_events_v1(
                values,
                source_step_threshold=0.5,
                source_stability_tolerance=0.1,
            )
            self.assertEqual([tuple(item) for item in actual], [tuple(item) for item in frozen])
            self.assertEqual({item.direction for item in actual}, {direction})

    def test_all_12_isolation_matches_reference_and_plus_minus_2_is_inclusive(self) -> None:
        event = audit.AuditStepEventV1(10, "step_up", 0.0, 2.0, 2.0, 1.0, 1.0)
        at_boundary = audit.AuditStepEventV1(12, "step_up", 0.0, 2.0, 2.0, 1.0, 1.0)
        outside = audit.AuditStepEventV1(13, "step_up", 0.0, 2.0, 2.0, 1.0, 1.0)
        source_events = {source: () for source in FROZEN_SOURCES}
        source_events[FROZEN_SOURCES[0]] = (event,)
        source_events[FROZEN_SOURCES[1]] = (at_boundary,)
        actual = audit.reconstruct_all_source_isolation_reference_v1(source_events)
        frozen = classify_event_isolation_v1(source_events, isolation_radius_seconds=2)
        self.assertEqual(actual, frozen)
        self.assertFalse(actual[FROZEN_SOURCES[0]][0][1])
        source_events[FROZEN_SOURCES[1]] = (outside,)
        actual = audit.reconstruct_all_source_isolation_reference_v1(source_events)
        self.assertTrue(actual[FROZEN_SOURCES[0]][0][1])

    def test_target_response_and_right_censoring_match_frozen_reference(self) -> None:
        values = response_target(horizon=5, direction="decrease")
        actual = audit.reconstruct_target_response_reference_v1(
            values, event_index=9, selected_horizon_seconds=5
        )
        frozen = evaluate_target_response_v1(
            values,
            event_index=9,
            horizon_seconds=5,
            target_noise_scale=1.0,
            target_direction="decrease",
        )
        self.assertEqual(actual, (frozen.right_censored, frozen.target_response))
        censored = audit.reconstruct_target_response_reference_v1(
            values, event_index=155, selected_horizon_seconds=5
        )
        self.assertEqual(censored, (True, None))

    def test_confirmation_gate_boundaries_match_d0_br1(self) -> None:
        cases = (
            (5, 0.60, 0.40, 1.0, True),
            (4, 0.75, 0.25, 2.0, False),
            (5, 0.60, 0.60, 2.0, False),
            (5, 0.59, 0.41, 2.0, False),
            (5, 0.80, 0.20, 0.999, False),
            (5, 0.80, 0.20, 1.0, True),
            (5, 0.20, 0.80, 2.0, False),
        )
        for usable, selected, opposite, effect, expected in cases:
            with self.subTest(
                usable=usable, selected=selected, opposite=opposite, effect=effect
            ):
                actual = audit.reconstruct_confirmation_gate_reference_v1(
                    usable_response_count=usable,
                    source_direction_unchanged=True,
                    selected_consistency=selected,
                    opposite_consistency=opposite,
                    robust_effect_ratio=effect,
                    fit_parameters_reused_without_retuning=True,
                )
                frozen = calibration_confirmation_gate_v1(
                    train3_isolated_events=usable,
                    source_direction_unchanged=True,
                    target_direction_unchanged=selected > opposite,
                    train3_directional_consistency=selected,
                    train3_robust_effect_ratio=effect,
                    fit_parameters_reused_without_retuning=True,
                )
                self.assertEqual(actual, frozen)
                self.assertEqual(actual, expected)

    def test_both_source_and_target_directions_replay_as_confirmed(self) -> None:
        input_set = make_input_set()
        source = FROZEN_SOURCES[0]
        target = FROZEN_TARGETS[0]
        for source_direction in ("step_up", "step_down"):
            for target_direction in ("increase", "decrease"):
                with self.subTest(source=source_direction, target=target_direction):
                    relation = one_relation(
                        input_set,
                        source_direction=source_direction,
                        target_direction=target_direction,
                        horizon=1,
                    )
                    value_map = synthetic_value_map(
                        source_values={
                            source: stepped_source(direction=source_direction)
                        },
                        target_values={
                            target: response_target(direction=target_direction)
                        },
                    )
                    replay = audit.replay_synthetic_directions_reference_v1(
                        directional_inputs=(relation,),
                        source_parameters=input_set.source_parameters,
                        target_parameters=input_set.target_parameters,
                        value_map=value_map,
                    )[0]
                    self.assertEqual(replay.usable_response_count, 6)
                    self.assertEqual(replay.selected_consistency, 1.0)
                    self.assertEqual(replay.opposite_consistency, 0.0)
                    self.assertEqual(replay.robust_effect_ratio, 2.0)
                    self.assertEqual(replay.status, "calibration_confirmed")

    def test_another_source_within_two_seconds_blocks_all_six_events(self) -> None:
        input_set = make_input_set()
        source = FROZEN_SOURCES[0]
        blocker = FROZEN_SOURCES[1]
        target = FROZEN_TARGETS[0]
        relation = one_relation(input_set)
        shifted_indices = (12, 32, 52, 72, 92, 112)
        value_map = synthetic_value_map(
            source_values={
                source: stepped_source(direction="step_up"),
                blocker: stepped_source(
                    direction="step_up", event_indices=shifted_indices
                ),
            },
            target_values={target: response_target(direction="increase")},
        )
        replay = audit.replay_synthetic_directions_reference_v1(
            directional_inputs=(relation,),
            source_parameters=input_set.source_parameters,
            target_parameters=input_set.target_parameters,
            value_map=value_map,
        )[0]
        self.assertEqual(replay.usable_response_count, 0)
        self.assertEqual(replay.status, "calibration_conflict")

    def test_reference_source_is_independent_of_confirmation_engine(self) -> None:
        source = inspect.getsource(audit)
        self.assertNotIn("task039d2_confirmation_v1", source)
        self.assertNotIn("confirm_directional_relations_v1", source)
        self.assertNotIn("origin_arms", source)
        self.assertNotIn("meta_rank", source)
        self.assertNotIn("stat_score", source)
        self.assertNotIn("gdn_similarity", source)


if __name__ == "__main__":
    unittest.main()
