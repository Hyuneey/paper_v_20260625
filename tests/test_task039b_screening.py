from __future__ import annotations

import unittest

from paperworks.feasibility.hai_process_v1 import (
    FIXED_HORIZONS,
    HAIFeasibilityError,
    ResponseDirectionV1,
    choose_fit_horizon,
    isolated_transition_indices,
    screen_delayed_response_pair,
    screen_horizon,
)


def synthetic_file(trigger_count: int, *, increase: bool = True) -> tuple[dict[str, list[float]], list[float]]:
    length = trigger_count * 10 + 10
    source = [0.0] * length
    other = [0.0] * length
    target = [0.0] * length
    for index in range(5, 5 + trigger_count * 10, 10):
        source[index] = 1.0
        source[index + 1] = 0.0
        target[index + 1] = 5.0 if increase else -5.0
    return {"P1_CMD01D": source, "P1_CMD02D": other}, target


class Task039BScreeningTests(unittest.TestCase):
    def test_isolation_rejects_nearby_other_source_transition(self) -> None:
        sources, _ = synthetic_file(3)
        sources["P1_CMD02D"][4] = 1.0
        isolated = isolated_transition_indices(
            source_variable="P1_CMD01D", source_values=sources, destination_state=1.0
        )
        self.assertNotIn(5, isolated)

    def test_horizon_rejects_cross_boundary(self) -> None:
        summary = screen_horizon(
            trigger_indices=(9,), target_values=[0.0] * 10, horizon_seconds=1, noise_scale=1.0
        )
        self.assertEqual(summary.usable_trigger_count, 0)
        self.assertEqual(summary.right_censored_count, 1)

    def test_fixed_horizon_enforcement(self) -> None:
        with self.assertRaises(HAIFeasibilityError):
            screen_horizon(
                trigger_indices=(1,), target_values=[0.0, 1.0, 2.0], horizon_seconds=2, noise_scale=1.0
            )

    def test_fit_and_calibration_increase_confirmation(self) -> None:
        files = {"f1": synthetic_file(12), "f2": synthetic_file(12), "f3": synthetic_file(6)}
        sources = {name: item[0] for name, item in files.items()}
        targets = {name: item[1] for name, item in files.items()}
        record, private = screen_delayed_response_pair(
            process_id="P1",
            source_variable="P1_CMD01D",
            target_variable="P1_SENSOR01",
            destination_state=1.0,
            source_values_by_file=sources,
            target_values_by_file=targets,
            noise_scale=1.0,
            fit_files=("f1", "f2"),
            calibration_file="f3",
        )
        self.assertTrue(record.fit_supported)
        self.assertTrue(record.calibration_confirmed)
        self.assertEqual(record.selected_direction, ResponseDirectionV1.INCREASE)
        self.assertEqual(record.readiness, "canonical_increase_ready")
        self.assertEqual(record.selected_horizon_seconds, 1)
        self.assertEqual(len(private["fixed_horizon_summaries"]), len(FIXED_HORIZONS))

    def test_decrease_remains_future_family(self) -> None:
        files = {
            "f1": synthetic_file(12, increase=False),
            "f2": synthetic_file(12, increase=False),
            "f3": synthetic_file(6, increase=False),
        }
        record, _ = screen_delayed_response_pair(
            process_id="P1",
            source_variable="P1_CMD01D",
            target_variable="P1_SENSOR01",
            destination_state=1.0,
            source_values_by_file={name: item[0] for name, item in files.items()},
            target_values_by_file={name: item[1] for name, item in files.items()},
            noise_scale=1.0,
            fit_files=("f1", "f2"),
            calibration_file="f3",
        )
        self.assertEqual(record.selected_direction, ResponseDirectionV1.DECREASE)
        self.assertEqual(record.readiness, "future_decrease_family_candidate")

    def test_choose_horizon_requires_frozen_grid(self) -> None:
        summary = screen_horizon(
            trigger_indices=(1,), target_values=[0.0] * 70, horizon_seconds=1, noise_scale=1.0
        )
        with self.assertRaises(HAIFeasibilityError):
            choose_fit_horizon((summary,))


if __name__ == "__main__":
    unittest.main()
