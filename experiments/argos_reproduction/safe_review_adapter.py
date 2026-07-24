"""Source-backed, inner-only, mock ReviewAgent request adapter for TASK-038A."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from experiments.argos_reproduction.agent_branch_state import review_trigger
from experiments.argos_reproduction.review_regression_samples import RegressionSample
from experiments.argos_reproduction.safe_repair_adapter import (
    load_pinned_string_constant,
)


ROOT = Path(__file__).resolve().parents[2]
REVIEW_PROMPT_SOURCE = ROOT / "external/argos/agent/prompts/review.py"
REVIEW_PROMPT_SOURCE_SHA256 = (
    "155015f2d34f6c940a48cd9357ec2e68f9d08e3d888ccaf0acb388204547746f"
)
METRIC_FIELDS = ("precision", "recall", "point_f1", "event_f1", "fp_per_10000")


class SafeReviewAdapterError(RuntimeError):
    """Raised when Review request construction crosses a frozen boundary."""


def load_review_system_prompt() -> str:
    return load_pinned_string_constant(
        REVIEW_PROMPT_SOURCE,
        expected_sha256=REVIEW_PROMPT_SOURCE_SHA256,
        constant_name="REVIEW_AGENT_COMBINED_PROMPT",
    ).strip()


def review_action(
    *, executable: bool, combined_metrics: Mapping[str, float], detector_metrics: Mapping[str, float]
) -> str:
    for field in METRIC_FIELDS:
        if field not in combined_metrics or field not in detector_metrics:
            raise SafeReviewAdapterError("TASK038A_REVIEW_METRIC_MISSING")
    return review_trigger(
        executable=executable,
        combined_point_f1=float(combined_metrics["point_f1"]),
        detector_point_f1=float(detector_metrics["point_f1"]),
    )


@dataclass(frozen=True)
class ReviewRequest:
    request_id: str
    branch_id: str
    initial_slot_id: str
    current_rule_hash: str
    split: str
    system_prompt: str
    user_prompt: str
    system_prompt_hash: str
    user_prompt_hash: str
    complete_request_hash: str
    regression_sample_count: int
    outer_data_included: bool = False
    sealed_test_data_included: bool = False

    def private_dict(self) -> dict[str, Any]:
        return asdict(self)

    def tracked_receipt(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "branch_id": self.branch_id,
            "initial_slot_id": self.initial_slot_id,
            "current_rule_hash": self.current_rule_hash,
            "split": self.split,
            "system_prompt_hash": self.system_prompt_hash,
            "user_prompt_hash": self.user_prompt_hash,
            "complete_request_hash": self.complete_request_hash,
            "regression_sample_count": self.regression_sample_count,
            "outer_data_included": False,
            "sealed_test_data_included": False,
        }


def build_review_request(
    *,
    branch_id: str,
    initial_slot_id: str,
    current_rule_source: str,
    current_rule_hash: str,
    combined_metrics: Mapping[str, float],
    detector_metrics: Mapping[str, float],
    regression_samples: Sequence[RegressionSample],
    split: str = "inner",
) -> ReviewRequest:
    if split != "inner":
        raise SafeReviewAdapterError("TASK038A_REVIEW_SPLIT_NOT_INNER")
    if branch_id not in ("A2", "A3"):
        raise SafeReviewAdapterError("TASK038A_REVIEW_BRANCH_INVALID")
    if len(regression_samples) > 3:
        raise SafeReviewAdapterError("TASK038A_TOO_MANY_REGRESSION_SAMPLES")
    action = review_action(
        executable=True,
        combined_metrics=combined_metrics,
        detector_metrics=detector_metrics,
    )
    if action != "review_provider_call_required":
        raise SafeReviewAdapterError("TASK038A_REVIEW_CALL_NOT_TRIGGERED")
    system_prompt = load_review_system_prompt()
    metric_payload = {
        field: {
            "current": float(combined_metrics[field]),
            "baseline": float(detector_metrics[field]),
            "difference": float(combined_metrics[field])
            - float(detector_metrics[field]),
        }
        for field in METRIC_FIELDS
    }
    samples = [sample.to_dict() for sample in regression_samples]
    user_prompt = (
        "##### CODE\n"
        + current_rule_source
        + "\n##### PERFORMANCE METRICS\n"
        + json.dumps(metric_payload, sort_keys=True, separators=(",", ":"))
        + "\n##### INNER REGRESSION SAMPLES\n"
        + json.dumps(samples, sort_keys=True, separators=(",", ":"), allow_nan=False)
    )
    system_hash = hashlib.sha256(system_prompt.encode("utf-8")).hexdigest()
    user_hash = hashlib.sha256(user_prompt.encode("utf-8")).hexdigest()
    complete_hash = hashlib.sha256(
        json.dumps(
            {"system": system_prompt, "user": user_prompt},
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()
    return ReviewRequest(
        request_id=f"REVIEW-{branch_id}-{initial_slot_id}",
        branch_id=branch_id,
        initial_slot_id=initial_slot_id,
        current_rule_hash=current_rule_hash,
        split=split,
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        system_prompt_hash=system_hash,
        user_prompt_hash=user_hash,
        complete_request_hash=complete_hash,
        regression_sample_count=len(samples),
    )


class MockReviewProvider:
    """Deterministic test-only provider; no external client is reachable."""

    provider_kind = "mock_review"

    def __init__(self, response: str) -> None:
        self.response = response
        self.call_count = 0

    def call_once(self, request: ReviewRequest) -> str:
        if self.call_count:
            raise SafeReviewAdapterError("TASK038A_REVIEW_RETRY_PROHIBITED")
        self.call_count += 1
        return self.response


def request_mock_review(request: ReviewRequest, provider: MockReviewProvider) -> str:
    if not isinstance(provider, MockReviewProvider):
        raise SafeReviewAdapterError("TASK038A_REAL_PROVIDER_PROHIBITED")
    return provider.call_once(request)
