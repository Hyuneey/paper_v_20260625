from __future__ import annotations

from experiments.argos_reproduction.repair_provider_capture import (
    approval_blockers,
)


def _approval(count: int) -> dict[str, object]:
    return {
        "approved": True,
        "approved_by": "researcher",
        "approval_date": "2026-07-24",
        "provider": "openai_responses",
        "model": "gpt-5.6-luna",
        "credential_env_var": "TASK038B_TEST_KEY",
        "maximum_requests": count,
        "maximum_requests_upper_bound": 13,
        "maximum_requests_per_initial_rule": 1,
        "maximum_input_tokens_per_call": 20000,
        "maximum_output_tokens_per_call": 6000,
        "maximum_total_declared_input_tokens": count * 20000,
        "maximum_total_declared_output_tokens": count * 6000,
        "temperature_parameter_sent": False,
        "provider_seed_sent": False,
        "automatic_retry": False,
        "manual_retry": False,
        "replacement_generation": False,
        "review_agent_calls": 0,
    }


def test_real_call_requires_explicit_flag_and_credential(monkeypatch) -> None:
    config = {"provider": {"provider": "openai_responses", "model": "gpt-5.6-luna"}}
    manifest = {"authorized_call_count": 3}
    approval = _approval(3)
    blockers = approval_blockers(
        config, approval, manifest, allow_real_provider_call=False
    )
    assert "cli_allow_flag_missing" in blockers
    assert "credential_missing" in blockers
    monkeypatch.setenv("TASK038B_TEST_KEY", "synthetic")
    assert (
        approval_blockers(
            config, approval, manifest, allow_real_provider_call=True
        )
        == []
    )


def test_consumed_receipt_has_no_retry_budget() -> None:
    approval = _approval(13)
    assert approval["maximum_requests_per_initial_rule"] == 1
    assert approval["automatic_retry"] is False
    assert approval["manual_retry"] is False
    assert approval["replacement_generation"] is False
