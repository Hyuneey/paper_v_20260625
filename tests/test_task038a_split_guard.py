from __future__ import annotations

import pytest

from experiments.argos_reproduction.agent_private_artifacts import (
    AgentArtifactBoundaryError,
    guard_agent_data_access,
)


def test_repair_and_review_split_roles_are_exact() -> None:
    guard_agent_data_access(role="repair", split="generation", labels=False)
    guard_agent_data_access(role="review", split="inner", labels=True)
    with pytest.raises(AgentArtifactBoundaryError):
        guard_agent_data_access(role="repair", split="generation", labels=True)
    with pytest.raises(AgentArtifactBoundaryError):
        guard_agent_data_access(role="review", split="generation", labels=False)


@pytest.mark.parametrize("split", ["outer", "outer_validation", "test", "sealed_test"])
def test_outer_and_test_access_fail_closed(split: str) -> None:
    with pytest.raises(AgentArtifactBoundaryError, match="SPLIT_ACCESS_PROHIBITED"):
        guard_agent_data_access(role="review", split=split, labels=False)
