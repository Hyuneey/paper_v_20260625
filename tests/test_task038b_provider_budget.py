from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_dec073_provider_budget_is_exact_and_review_free() -> None:
    approval = json.loads(
        (
            ROOT
            / "configs/argos_reproduction/task038b_repair_provider_authorization.json"
        ).read_text(encoding="utf-8")
    )
    assert approval["decision_id"] == "DEC-073"
    assert approval["provider"] == "openai_responses"
    assert approval["model"] == "gpt-5.6-luna"
    assert approval["maximum_requests"] <= 13
    assert approval["maximum_output_tokens_per_call"] == 6000
    assert approval["temperature_parameter_sent"] is False
    assert approval["provider_seed_sent"] is False
    assert approval["review_agent_calls"] == 0
