"""Deterministic bounded inner-regression sample extraction for TASK-038A."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Sequence


class RegressionSampleError(ValueError):
    """Raised when regression evidence violates the frozen inner-only policy."""


@dataclass(frozen=True)
class RegressionSample:
    start: int
    end: int
    values: tuple[float, ...]
    labels: tuple[int, ...]
    detector_predictions: tuple[int, ...]
    rule_predictions: tuple[int, ...]
    combined_predictions: tuple[int, ...]

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        for key in (
            "values",
            "labels",
            "detector_predictions",
            "rule_predictions",
            "combined_predictions",
        ):
            value[key] = list(value[key])
        return value


def _binary(values: Sequence[int], name: str) -> tuple[int, ...]:
    result = tuple(int(value) for value in values)
    if any(value not in (0, 1) for value in result):
        raise RegressionSampleError(f"TASK038A_{name}_NOT_BINARY")
    return result


def compose_direction(
    detector: Sequence[int], rule: Sequence[int], direction: str
) -> tuple[int, ...]:
    detector_values = _binary(detector, "DETECTOR")
    rule_values = _binary(rule, "RULE")
    if len(detector_values) != len(rule_values):
        raise RegressionSampleError("TASK038A_PREDICTION_LENGTH_MISMATCH")
    if direction == "FN":
        return tuple(max(left, right) for left, right in zip(detector_values, rule_values))
    if direction == "FP":
        return tuple(min(left, right) for left, right in zip(detector_values, rule_values))
    raise RegressionSampleError("TASK038A_DIRECTION_INVALID")


def extract_regression_samples(
    *,
    split: str,
    values: Sequence[float],
    labels: Sequence[int],
    detector_predictions: Sequence[int],
    rule_predictions: Sequence[int],
    direction: str,
    maximum_samples: int = 3,
    maximum_window_length: int = 20,
) -> tuple[RegressionSample, ...]:
    if split != "inner":
        raise RegressionSampleError("TASK038A_REVIEW_SPLIT_NOT_INNER")
    if maximum_samples != 3 or maximum_window_length != 20:
        raise RegressionSampleError("TASK038A_REGRESSION_POLICY_NOT_FROZEN")
    numeric_values = tuple(float(value) for value in values)
    truth = _binary(labels, "LABEL")
    detector = _binary(detector_predictions, "DETECTOR")
    rule = _binary(rule_predictions, "RULE")
    if len({len(numeric_values), len(truth), len(detector), len(rule)}) != 1:
        raise RegressionSampleError("TASK038A_REGRESSION_INPUT_LENGTH_MISMATCH")
    combined = compose_direction(detector, rule, direction)
    regression_indices = [
        index
        for index, (label, base, current) in enumerate(
            zip(truth, detector, combined)
        )
        if base == label and current != label
    ]
    samples: list[RegressionSample] = []
    previous_end = 0
    half = maximum_window_length // 2
    for index in regression_indices:
        start = max(0, index - half)
        end = min(len(truth), start + maximum_window_length)
        start = max(0, end - maximum_window_length)
        if samples and start < previous_end:
            continue
        sample = RegressionSample(
            start=start,
            end=end,
            values=numeric_values[start:end],
            labels=truth[start:end],
            detector_predictions=detector[start:end],
            rule_predictions=rule[start:end],
            combined_predictions=combined[start:end],
        )
        samples.append(sample)
        previous_end = end
        if len(samples) == maximum_samples:
            break
    return tuple(samples)
