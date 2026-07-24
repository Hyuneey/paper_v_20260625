from __future__ import annotations

from pathlib import Path

import pytest

from experiments.argos_reproduction.agent_private_artifacts import (
    AgentArtifactBoundaryError,
    ContainerRuleValidationPlan,
    validate_container_plan,
    validate_tracked_payload,
)


ROOT = Path(__file__).resolve().parents[1]


def test_container_contract_requires_isolation_and_never_authorizes_host() -> None:
    plan = ContainerRuleValidationPlan(
        validation_id="VALIDATE-SYNTHETIC",
        rule_hash="a" * 64,
        value_artifact_hashes=("b" * 64,),
        split="generation",
        image_id="sha256:" + "c" * 64,
    )
    validate_container_plan(plan)
    assert plan.host_execution_authorized is False
    assert plan.labels_mounted is False
    with pytest.raises(AgentArtifactBoundaryError):
        validate_container_plan(
            ContainerRuleValidationPlan(
                validation_id="BAD",
                rule_hash="a" * 64,
                value_artifact_hashes=("b" * 64,),
                split="generation",
                image_id="sha256:" + "c" * 64,
                host_execution_authorized=True,
            )
        )


def test_tracked_payload_rejects_raw_fields_and_private_paths() -> None:
    validate_tracked_payload({"rule_hash": "a" * 64, "count": 1})
    with pytest.raises(AgentArtifactBoundaryError, match="RAW_FIELD_TRACKED"):
        validate_tracked_payload({"rule_source": "def inference(sample): pass"})
    with pytest.raises(AgentArtifactBoundaryError, match="PRIVATE_PATH_TRACKED"):
        validate_tracked_payload({"path": r"C:\Users\researcher\private.npy"})


def test_new_modules_have_no_host_dynamic_execution_or_real_provider_surface() -> None:
    modules = [
        "agent_factorial_registry.py",
        "agent_branch_state.py",
        "safe_repair_adapter.py",
        "safe_review_adapter.py",
        "review_regression_samples.py",
        "agent_private_artifacts.py",
        "agent_call_budget.py",
        "agent_validity_metrics.py",
    ]
    combined = "\n".join(
        (ROOT / "experiments/argos_reproduction" / name).read_text(encoding="utf-8")
        for name in modules
    ).lower()
    for prohibited in (
        "exec(",
        "eval(",
        "compile(",
        "importlib",
        "runpy",
        "subprocess",
        "openai.",
        "provider_client",
        "dataset_reader",
    ):
        assert prohibited not in combined
