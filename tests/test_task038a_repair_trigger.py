from __future__ import annotations

import pytest

from experiments.argos_reproduction.agent_branch_state import repair_trigger
from experiments.argos_reproduction.safe_repair_adapter import (
    MockRepairProvider,
    SafeRepairAdapterError,
    build_repair_request,
    load_repair_system_prompt,
    request_mock_repair,
)


def test_repair_trigger_is_runtime_failure_only() -> None:
    assert repair_trigger("target_runtime_failed", static_valid=True)
    assert repair_trigger("contrast_runtime_failed", static_valid=True)
    assert repair_trigger("output_contract_failed", static_valid=True)
    assert not repair_trigger("executable_rule", static_valid=True)
    assert not repair_trigger("provider_error", static_valid=True)
    assert not repair_trigger("target_runtime_failed", static_valid=False)


def test_repair_prompt_is_source_backed_generation_only_and_label_free() -> None:
    request = build_repair_request(
        initial_slot_id="ERRRULE-SYNTHETIC",
        current_rule_source="def inference(sample):\n    return sample[:, 0]",
        current_rule_hash="a" * 64,
        runtime_error="ValueError: synthetic",
        failing_values=[1.0, 2.0],
        failing_artifact_hash="b" * 64,
    )
    assert "fixs syntax and runtime erros" in load_repair_system_prompt()
    assert request.failing_split == "generation"
    assert request.labels_included is False
    lowered = request.user_prompt.lower()
    assert "label" not in lowered
    assert "f1" not in lowered
    assert "outer" not in lowered
    assert "test" not in lowered


def test_repair_mock_is_one_shot_and_real_provider_is_unreachable() -> None:
    request = build_repair_request(
        initial_slot_id="ERRRULE-SYNTHETIC",
        current_rule_source="def inference(sample):\n    return sample",
        current_rule_hash="a" * 64,
        runtime_error="synthetic",
        failing_values=[1.0],
        failing_artifact_hash="b" * 64,
    )
    provider = MockRepairProvider("```python\ndef inference(sample):\n    return sample\n```")
    assert "inference" in request_mock_repair(request, provider)
    with pytest.raises(SafeRepairAdapterError, match="RETRY_PROHIBITED"):
        request_mock_repair(request, provider)
    with pytest.raises(SafeRepairAdapterError, match="REAL_PROVIDER_PROHIBITED"):
        request_mock_repair(request, object())  # type: ignore[arg-type]
