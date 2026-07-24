"""Source-backed, mock-only RepairAgent request adapter for TASK-038A."""

from __future__ import annotations

import ast
from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
import re
from typing import Any, Sequence


ROOT = Path(__file__).resolve().parents[2]
REPAIR_PROMPT_SOURCE = ROOT / "external/argos/agent/prompts/repair.py"
REPAIR_PROMPT_SOURCE_SHA256 = (
    "f7dc354ee862bf4b6433eff247999be51596be1325743ef002b9c1ddd180eb3d"
)


class SafeRepairAdapterError(RuntimeError):
    """Raised when Repair request construction crosses a frozen boundary."""


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def load_pinned_string_constant(
    path: Path, *, expected_sha256: str, constant_name: str
) -> str:
    source = path.read_bytes()
    if sha256_bytes(source) != expected_sha256:
        raise SafeRepairAdapterError("TASK038A_PROMPT_SOURCE_HASH_MISMATCH")
    tree = ast.parse(source.decode("utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == constant_name
            for target in node.targets
        ):
            if isinstance(node.value, ast.Constant) and isinstance(
                node.value.value, str
            ):
                return node.value.value
    raise SafeRepairAdapterError("TASK038A_PROMPT_CONSTANT_MISSING")


def load_repair_system_prompt(chunk_size: int = 1000) -> str:
    if chunk_size != 1000:
        raise SafeRepairAdapterError("TASK038A_REPAIR_CHUNK_SIZE_NOT_FROZEN")
    template = load_pinned_string_constant(
        REPAIR_PROMPT_SOURCE,
        expected_sha256=REPAIR_PROMPT_SOURCE_SHA256,
        constant_name="REPAIR_AGENT_PROMPT_TEMPLATE",
    )
    return template.format(chunk_size=chunk_size).strip()


def sanitize_runtime_error(message: str) -> str:
    sanitized = re.sub(r"[A-Za-z]:\\[^\s]+", "<private-path>", str(message))
    sanitized = re.sub(r"/(?:home|Users)/[^\s]+", "<private-path>", sanitized)
    return sanitized[:1000]


@dataclass(frozen=True)
class RepairRequest:
    request_id: str
    initial_slot_id: str
    current_rule_hash: str
    failing_split: str
    failing_artifact_hash: str
    system_prompt: str
    user_prompt: str
    system_prompt_hash: str
    user_prompt_hash: str
    complete_request_hash: str
    labels_included: bool = False

    def private_dict(self) -> dict[str, Any]:
        return asdict(self)

    def tracked_receipt(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "initial_slot_id": self.initial_slot_id,
            "current_rule_hash": self.current_rule_hash,
            "failing_split": self.failing_split,
            "failing_artifact_hash": self.failing_artifact_hash,
            "system_prompt_hash": self.system_prompt_hash,
            "user_prompt_hash": self.user_prompt_hash,
            "complete_request_hash": self.complete_request_hash,
            "labels_included": False,
        }


def build_repair_request(
    *,
    initial_slot_id: str,
    current_rule_source: str,
    current_rule_hash: str,
    runtime_error: str,
    failing_values: Sequence[float],
    failing_artifact_hash: str,
    split: str = "generation",
) -> RepairRequest:
    if split != "generation":
        raise SafeRepairAdapterError("TASK038A_REPAIR_SPLIT_NOT_GENERATION")
    system_prompt = load_repair_system_prompt()
    value_list = [float(value) for value in failing_values]
    user_prompt = (
        "##### CODE\n"
        + current_rule_source
        + "\n##### ERROR FROM EXECUTING CODE, PLEASE FIX IT\n"
        + sanitize_runtime_error(runtime_error)
        + "\n##### FAILING VALUE-ONLY CHUNK\n"
        + json.dumps(value_list, separators=(",", ":"), allow_nan=False)
    )
    system_hash = sha256_bytes(system_prompt.encode("utf-8"))
    user_hash = sha256_bytes(user_prompt.encode("utf-8"))
    complete_hash = sha256_bytes(
        json.dumps(
            {"system": system_prompt, "user": user_prompt},
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("utf-8")
    )
    return RepairRequest(
        request_id=f"REPAIR-{initial_slot_id}",
        initial_slot_id=initial_slot_id,
        current_rule_hash=current_rule_hash,
        failing_split=split,
        failing_artifact_hash=failing_artifact_hash,
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        system_prompt_hash=system_hash,
        user_prompt_hash=user_hash,
        complete_request_hash=complete_hash,
    )


class MockRepairProvider:
    """Deterministic test-only provider; no external client is reachable."""

    provider_kind = "mock_repair"

    def __init__(self, response: str) -> None:
        self.response = response
        self.call_count = 0

    def call_once(self, request: RepairRequest) -> str:
        if self.call_count:
            raise SafeRepairAdapterError("TASK038A_REPAIR_RETRY_PROHIBITED")
        self.call_count += 1
        return self.response


def request_mock_repair(request: RepairRequest, provider: MockRepairProvider) -> str:
    if not isinstance(provider, MockRepairProvider):
        raise SafeRepairAdapterError("TASK038A_REAL_PROVIDER_PROHIBITED")
    return provider.call_once(request)
