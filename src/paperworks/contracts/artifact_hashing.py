"""Canonical self-hashing for TASK-030 external contract artifacts."""

from __future__ import annotations

import copy
import hashlib
import json
import re
from typing import Any, Mapping


_SHA256_PATTERN = r"^[a-f0-9]{64}$"


class ContractArtifactHashError(ValueError):
    """Fail-closed canonical artifact hash error."""

    def __init__(self, issue_code: str, message: str) -> None:
        super().__init__(f"{issue_code}: {message}")
        self.issue_code = issue_code
        self.message = message


def canonical_contract_artifact_bytes(document: Mapping[str, Any]) -> bytes:
    """Serialize a deep copy after excluding only the top-level self-hash."""

    payload = copy.deepcopy(dict(document))
    payload.pop("artifact_hash", None)
    try:
        text = json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        )
    except ValueError as exc:
        raise ContractArtifactHashError(
            "CONTRACT_ARTIFACT_NONFINITE_VALUE",
            "contract artifact contains a non-finite numeric value",
        ) from exc
    return text.encode("utf-8")


def canonical_contract_artifact_sha256(document: Mapping[str, Any]) -> str:
    """Return an integrity-only SHA-256 that excludes the top-level self-hash."""

    return hashlib.sha256(canonical_contract_artifact_bytes(document)).hexdigest()


def with_computed_artifact_hash(document: Mapping[str, Any]) -> dict[str, Any]:
    """Return a new document with its canonical top-level self-hash populated."""

    payload = copy.deepcopy(dict(document))
    payload["artifact_hash"] = canonical_contract_artifact_sha256(payload)
    return payload


def verify_contract_artifact_hash(document: Mapping[str, Any]) -> str:
    """Verify and return the integrity-only top-level artifact hash."""

    supplied = document.get("artifact_hash")
    if supplied is None:
        raise ContractArtifactHashError("CONTRACT_ARTIFACT_HASH_MISSING", "artifact_hash is required")
    if not isinstance(supplied, str) or re.fullmatch(_SHA256_PATTERN, supplied) is None:
        raise ContractArtifactHashError("CONTRACT_ARTIFACT_HASH_INVALID", "artifact_hash must be lowercase SHA-256")
    expected = canonical_contract_artifact_sha256(document)
    if supplied != expected:
        raise ContractArtifactHashError("CONTRACT_ARTIFACT_HASH_MISMATCH", "artifact_hash does not match content")
    return supplied
