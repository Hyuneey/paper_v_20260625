from __future__ import annotations

import pytest

from experiments.argos_reproduction.review_regression_samples import (
    RegressionSampleError,
    extract_regression_samples,
)


def test_regression_samples_are_chronological_bounded_and_non_overlapping() -> None:
    size = 100
    labels = [0] * size
    detector = [0] * size
    rule = [0] * size
    for index in (10, 40, 80):
        rule[index] = 1
    samples = extract_regression_samples(
        split="inner",
        values=list(range(size)),
        labels=labels,
        detector_predictions=detector,
        rule_predictions=rule,
        direction="FN",
    )
    assert len(samples) == 3
    assert [sample.start for sample in samples] == sorted(sample.start for sample in samples)
    assert all(sample.end - sample.start <= 20 for sample in samples)
    assert all(left.end <= right.start for left, right in zip(samples, samples[1:]))


def test_regression_sample_extraction_rejects_non_inner_and_policy_changes() -> None:
    kwargs = {
        "values": [0.0, 1.0],
        "labels": [0, 0],
        "detector_predictions": [0, 0],
        "rule_predictions": [0, 1],
        "direction": "FN",
    }
    with pytest.raises(RegressionSampleError, match="SPLIT_NOT_INNER"):
        extract_regression_samples(split="outer", **kwargs)
    with pytest.raises(RegressionSampleError, match="POLICY_NOT_FROZEN"):
        extract_regression_samples(split="inner", maximum_samples=4, **kwargs)
