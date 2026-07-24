"""Non-executing private-artifact and container-interface contracts for TASK-038A."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import re
from typing import Any, Mapping


class AgentArtifactBoundaryError(ValueError):
    """Raised when a split or artifact would cross the TASK-038A boundary."""


RAW_TRACKED_KEYS = frozenset(
    {
        "rule_source",
        "prompt_text",
        "response_text",
        "values",
        "labels",
        "prediction_array",
        "regression_windows",
        "container_log",
        "local_path",
    }
)


@dataclass(frozen=True)
class ArtifactReference:
    artifact_id: str
    artifact_type: str
    sha256: str
    split: str
    private: bool = True


@dataclass(frozen=True)
class ContainerRuleValidationPlan:
    validation_id: str
    rule_hash: str
    value_artifact_hashes: tuple[str, ...]
    split: str
    image_id: str
    network: str = "none"
    non_root: bool = True
    read_only_root: bool = True
    cap_drop_all: bool = True
    no_new_privileges: bool = True
    bounded_cpu: bool = True
    bounded_memory: bool = True
    bounded_pids: bool = True
    bounded_timeout: bool = True
    labels_mounted: bool = False
    host_execution_authorized: bool = False

    def tracked_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["value_artifact_hashes"] = list(self.value_artifact_hashes)
        return value


def guard_agent_data_access(*, role: str, split: str, labels: bool) -> None:
    if split in ("outer", "outer_validation", "test", "sealed_test"):
        raise AgentArtifactBoundaryError("TASK038A_SPLIT_ACCESS_PROHIBITED")
    if role == "repair":
        if split != "generation" or labels:
            raise AgentArtifactBoundaryError("TASK038A_REPAIR_DATA_SCOPE_INVALID")
        return
    if role == "review":
        if split != "inner":
            raise AgentArtifactBoundaryError("TASK038A_REVIEW_DATA_SCOPE_INVALID")
        return
    raise AgentArtifactBoundaryError("TASK038A_AGENT_ROLE_UNKNOWN")


def validate_container_plan(plan: ContainerRuleValidationPlan) -> None:
    if plan.split not in ("generation", "inner"):
        raise AgentArtifactBoundaryError("TASK038A_CONTAINER_SPLIT_INVALID")
    required_true = (
        plan.non_root,
        plan.read_only_root,
        plan.cap_drop_all,
        plan.no_new_privileges,
        plan.bounded_cpu,
        plan.bounded_memory,
        plan.bounded_pids,
        plan.bounded_timeout,
    )
    if plan.network != "none" or not all(required_true):
        raise AgentArtifactBoundaryError("TASK038A_CONTAINER_ISOLATION_INCOMPLETE")
    if plan.labels_mounted or plan.host_execution_authorized:
        raise AgentArtifactBoundaryError("TASK038A_CONTAINER_AUTHORITY_INVALID")


def validate_tracked_payload(payload: Mapping[str, Any]) -> None:
    def visit(value: Any, key: str = "") -> None:
        if key in RAW_TRACKED_KEYS:
            raise AgentArtifactBoundaryError("TASK038A_RAW_FIELD_TRACKED")
        if isinstance(value, Mapping):
            for child_key, child in value.items():
                visit(child, str(child_key))
        elif isinstance(value, (list, tuple)):
            for child in value:
                visit(child, key)
        elif isinstance(value, str):
            if re.match(r"^[A-Za-z]:\\", value) or value.startswith("/home/"):
                raise AgentArtifactBoundaryError("TASK038A_PRIVATE_PATH_TRACKED")

    visit(payload)
