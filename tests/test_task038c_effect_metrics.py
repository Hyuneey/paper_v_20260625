from experiments.argos_reproduction.review_effect_metrics import (
    _distribution,
    _provider_usage,
    _wilson,
)


def test_effect_intervals_keep_invalid_calls_in_denominator() -> None:
    result = _wilson(2, 4)
    assert result["successes"] == 2
    assert result["denominator"] == 4
    assert result["rate"] == 0.5
    assert result["formal_population_inference"] is False


def test_conditional_delta_distribution_is_deterministic() -> None:
    result = _distribution([1.0, 2.0, 3.0])
    assert result["mean"] == 2.0
    assert result["median"] == 2.0
    assert result["minimum"] == 1.0
    assert result["maximum"] == 3.0


def test_provider_usage_is_branch_local_and_provider_reported() -> None:
    result = _provider_usage(
        [
            {
                "usage": {
                    "input_tokens": 10,
                    "input_tokens_details": {"cached_tokens": 2},
                    "output_tokens": 5,
                    "output_tokens_details": {"reasoning_tokens": 3},
                    "total_tokens": 15,
                }
            },
            {
                "usage": {
                    "input_tokens": 20,
                    "output_tokens": 7,
                    "total_tokens": 27,
                }
            },
        ]
    )
    assert result["calls"] == 2
    assert result["input_tokens_total"] == 30
    assert result["cached_input_tokens_total"] == 2
    assert result["reasoning_tokens_total"] == 3
    assert result["estimated_provider_cost"] == "not_computed_unfrozen_pricing"
