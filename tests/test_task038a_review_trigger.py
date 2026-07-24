from __future__ import annotations

import pytest

from experiments.argos_reproduction.agent_branch_state import reviewed_output_rule
from experiments.argos_reproduction.safe_review_adapter import (
    MockReviewProvider,
    SafeReviewAdapterError,
    build_review_request,
    review_action,
    request_mock_review,
)


METRICS = {
    "precision": 0.5,
    "recall": 0.5,
    "point_f1": 0.5,
    "event_f1": 0.5,
    "fp_per_10000": 10.0,
}


def test_review_trigger_uses_inner_point_f1_and_executable_inputs_only() -> None:
    assert (
        review_action(
            executable=True,
            combined_metrics=METRICS,
            detector_metrics=METRICS,
        )
        == "no_review_needed"
    )
    worse = {**METRICS, "point_f1": 0.4}
    assert (
        review_action(
            executable=True, combined_metrics=worse, detector_metrics=METRICS
        )
        == "review_provider_call_required"
    )
    assert (
        review_action(
            executable=False, combined_metrics=worse, detector_metrics=METRICS
        )
        == "review_not_applicable_non_executable"
    )


def test_review_request_is_inner_only_and_one_shot() -> None:
    worse = {**METRICS, "point_f1": 0.4}
    request = build_review_request(
        branch_id="A2",
        initial_slot_id="ERRRULE-SYNTHETIC",
        current_rule_source="def inference(sample):\n    return sample",
        current_rule_hash="a" * 64,
        combined_metrics=worse,
        detector_metrics=METRICS,
        regression_samples=(),
    )
    assert request.split == "inner"
    assert request.outer_data_included is False
    assert request.sealed_test_data_included is False
    provider = MockReviewProvider("```python\ndef inference(sample):\n    return sample\n```")
    assert "inference" in request_mock_review(request, provider)
    with pytest.raises(SafeReviewAdapterError, match="RETRY_PROHIBITED"):
        request_mock_review(request, provider)
    with pytest.raises(SafeReviewAdapterError, match="REVIEW_SPLIT_NOT_INNER"):
        build_review_request(
            branch_id="A2",
            initial_slot_id="ERRRULE-SYNTHETIC",
            current_rule_source="def inference(sample):\n    return sample",
            current_rule_hash="a" * 64,
            combined_metrics=worse,
            detector_metrics=METRICS,
            regression_samples=(),
            split="outer",
        )


def test_harmful_or_invalid_review_is_never_silently_reverted() -> None:
    assert (
        reviewed_output_rule(
            pre_review_hash="a" * 64,
            reviewed_hash="b" * 64,
            reviewed_valid=True,
        )
        == "b" * 64
    )
    assert (
        reviewed_output_rule(
            pre_review_hash="a" * 64,
            reviewed_hash=None,
            reviewed_valid=False,
        )
        is None
    )
