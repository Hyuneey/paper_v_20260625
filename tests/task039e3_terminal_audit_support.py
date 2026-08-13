from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from paperworks.v6.common import stable_hash_v1


PUBLIC_ROOT_ENV = "TASK039E3_R2R_TERMINAL_PUBLIC_ROOT"
PRIVATE_ROOT_ENV = "TASK039E3_R2R_TERMINAL_PRIVATE_ROOT"


def required_root(name: str) -> Path:
    value = os.environ.get(name)
    if not value:
        raise AssertionError(f"required terminal-audit root is absent: {name}")
    root = Path(value).resolve(strict=True)
    if not root.is_dir() or root.is_symlink():
        raise AssertionError(f"terminal-audit root is not a regular directory: {name}")
    return root


def public_root() -> Path:
    return required_root(PUBLIC_ROOT_ENV)


def private_root() -> Path:
    return required_root(PRIVATE_ROOT_ENV)


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise AssertionError(f"JSON object required: {path.name}")
    return value


def verified_artifact(path: Path, *, hash_field: str = "artifact_hash") -> dict[str, Any]:
    value = read_json(path)
    observed = value.get(hash_field)
    if not isinstance(observed, str):
        raise AssertionError(f"artifact hash is absent: {path.name}")
    payload = {key: item for key, item in value.items() if key != hash_field}
    if stable_hash_v1(payload) != observed:
        raise AssertionError(f"artifact self-hash differs: {path.name}")
    return value


def final_private_root() -> Path:
    return private_root() / "final_authoritative_r2r_v1"


def relation_binding_to_identity(
    proposals: list[dict[str, Any]], binding_hash: str
) -> str:
    identities = {
        str(record["relation_identity"])
        for record in proposals
        if record["project_proposal"]["relation_binding_hash"] == binding_hash
    }
    if len(identities) != 1:
        raise AssertionError("relation binding does not resolve uniquely")
    return identities.pop()
