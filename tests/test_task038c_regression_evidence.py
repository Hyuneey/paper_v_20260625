from experiments.argos_reproduction.review_regression_samples import (
    extract_regression_samples,
)


def test_regression_windows_are_bounded_chronological_and_nonoverlapping() -> None:
    length = 100
    values = list(range(length))
    labels = [0] * length
    detector = [0] * length
    rule = [0] * length
    for index in (10, 40, 80):
        rule[index] = 1
    samples = extract_regression_samples(
        split="inner",
        values=values,
        labels=labels,
        detector_predictions=detector,
        rule_predictions=rule,
        direction="FN",
    )
    assert len(samples) == 3
    assert all(sample.end - sample.start <= 20 for sample in samples)
    assert all(left.end <= right.start for left, right in zip(samples, samples[1:]))
