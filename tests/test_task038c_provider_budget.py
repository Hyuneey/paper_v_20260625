import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_provider_budget_is_bounded_and_retry_free_before_exact_freeze() -> None:
    approval = json.loads(
        (
            ROOT
            / "configs/argos_reproduction/task038c_review_provider_authorization.json"
        ).read_text(encoding="utf-8")
    )
    assert approval["maximum_requests_upper_bound"] == 179
    assert approval["maximum_requests_per_review_branch"] == 1
    assert approval["maximum_output_tokens_per_call"] == 6000
    assert approval["automatic_retry"] is False
    assert approval["manual_retry"] is False
    assert approval["replacement_generation"] is False
    assert approval["repair_agent_calls"] == 0
    assert approval["detection_agent_calls"] == 0
