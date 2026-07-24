from experiments.argos_reproduction.review_regression_samples import compose_direction
from experiments.argos_reproduction.safe_review_adapter import review_action


def _metrics(point_f1: float) -> dict[str, float]:
    return {
        "precision": 0.5,
        "recall": 0.5,
        "point_f1": point_f1,
        "event_f1": 0.5,
        "fp_per_10000": 1.0,
    }


def test_direction_composition_is_exact_max_or_min() -> None:
    detector = [0, 0, 1, 1]
    rule = [0, 1, 0, 1]
    assert compose_direction(detector, rule, "FN") == (0, 1, 1, 1)
    assert compose_direction(detector, rule, "FP") == (0, 0, 0, 1)


def test_review_trigger_uses_only_point_f1_below_baseline() -> None:
    assert (
        review_action(
            executable=True,
            combined_metrics=_metrics(0.4),
            detector_metrics=_metrics(0.5),
        )
        == "review_provider_call_required"
    )
    assert (
        review_action(
            executable=True,
            combined_metrics=_metrics(0.5),
            detector_metrics=_metrics(0.5),
        )
        == "no_review_needed"
    )
