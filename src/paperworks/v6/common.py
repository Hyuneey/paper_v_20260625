"""Shared deterministic primitives for lightweight v6 foundation artifacts."""

from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass
from datetime import datetime
from hashlib import sha256
from types import MappingProxyType
from typing import Any, Mapping


V6_FOUNDATION_SCHEMA_VERSION = "1.0.0"
_SHA256_PATTERN = re.compile(r"^[a-f0-9]{64}$")
_COMMIT_PATTERN = re.compile(r"^(?:[a-f0-9]{7,40}|unverified)$")
_IDENTIFIER_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]*$")


class V6FoundationError(ValueError):
    """Raised when a lightweight v6 foundation contract is invalid."""


def require_sha256(value: str, field_name: str) -> str:
    """Validate and return a lowercase SHA-256 reference."""

    if not isinstance(value, str) or _SHA256_PATTERN.fullmatch(value) is None:
        raise V6FoundationError(
            f"{field_name} must be a lowercase SHA-256 digest"
        )
    return value


def require_identifier(value: str, field_name: str) -> str:
    """Validate a non-path versioned or logical identifier."""

    if (
        not isinstance(value, str)
        or _IDENTIFIER_PATTERN.fullmatch(value) is None
        or value in {".", ".."}
    ):
        raise V6FoundationError(f"{field_name} must be a safe non-empty identifier")
    return value


def require_unique_strings(
    values: tuple[str, ...], field_name: str, *, allow_empty: bool = True
) -> tuple[str, ...]:
    """Normalize and validate an ordered set of non-empty strings."""

    normalized = tuple(str(item) for item in values)
    if not allow_empty and not normalized:
        raise V6FoundationError(f"{field_name} must not be empty")
    if any(not item for item in normalized):
        raise V6FoundationError(f"{field_name} must contain non-empty strings")
    if len(normalized) != len(set(normalized)):
        raise V6FoundationError(f"{field_name} must contain unique values")
    return normalized


def require_sha256_refs(
    values: tuple[str, ...], field_name: str, *, allow_empty: bool = True
) -> tuple[str, ...]:
    """Normalize an ordered set of SHA-256 artifact references."""

    normalized = require_unique_strings(values, field_name, allow_empty=allow_empty)
    for index, value in enumerate(normalized):
        require_sha256(value, f"{field_name}[{index}]")
    return normalized


def require_finite(value: int | float, field_name: str) -> float:
    """Validate and return a finite JSON number."""

    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise V6FoundationError(f"{field_name} must be a finite number")
    result = float(value)
    if not math.isfinite(result):
        raise V6FoundationError(f"{field_name} must be a finite number")
    return result


def parse_iso_datetime(value: str, field_name: str) -> datetime:
    """Parse a timezone-aware ISO 8601 timestamp."""

    if not isinstance(value, str) or not value:
        raise V6FoundationError(f"{field_name} must be an ISO 8601 date-time")
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        result = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise V6FoundationError(
            f"{field_name} must be an ISO 8601 date-time"
        ) from exc
    if result.tzinfo is None:
        raise V6FoundationError(f"{field_name} must include a timezone")
    return result


def freeze_json(value: Any) -> Any:
    """Copy JSON-compatible caller data into immutable containers."""

    if isinstance(value, Mapping):
        result: dict[str, Any] = {}
        for key, item in value.items():
            if not isinstance(key, str):
                raise V6FoundationError("mapping keys must be strings")
            result[key] = freeze_json(item)
        return MappingProxyType(result)
    if isinstance(value, (list, tuple)):
        return tuple(freeze_json(item) for item in value)
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise V6FoundationError("non-finite numbers are prohibited")
        return value
    raise V6FoundationError(
        f"value is not JSON-compatible: {type(value).__name__}"
    )


def thaw_json(value: Any) -> Any:
    """Return a mutable JSON-compatible copy of frozen caller data."""

    if isinstance(value, Mapping):
        return {key: thaw_json(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [thaw_json(item) for item in value]
    return value


def canonical_json_v1(value: Mapping[str, Any]) -> str:
    """Return compact canonical UTF-8 JSON for a v6 foundation payload."""

    return json.dumps(
        thaw_json(value),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    )


def stable_hash_v1(value: Mapping[str, Any]) -> str:
    """Return the SHA-256 of a canonical v6 foundation payload."""

    return sha256(canonical_json_v1(value).encode("utf-8")).hexdigest()


def deterministic_id(prefix: str, content: Mapping[str, Any]) -> str:
    """Build a deterministic, non-authorizing artifact identifier."""

    require_identifier(prefix, "identifier prefix")
    return f"{prefix}:{stable_hash_v1(content)}"


def verify_identity_fields(
    data: Mapping[str, Any],
    *,
    id_field: str,
    observed_id: str,
    observed_hash: str,
) -> None:
    """Verify optional serialized identity fields during round-trip parsing."""

    supplied_id = data.get(id_field)
    if supplied_id is not None and supplied_id != observed_id:
        raise V6FoundationError(f"{id_field} does not match the artifact content")
    supplied_hash = data.get("artifact_hash")
    if supplied_hash is not None and supplied_hash != observed_hash:
        raise V6FoundationError("artifact_hash does not match the artifact content")


def reject_unknown_fields(
    data: Mapping[str, Any], allowed_fields: frozenset[str], artifact_type: str
) -> None:
    """Fail closed when serialized artifacts contain undeclared fields."""

    unknown = sorted(set(data) - allowed_fields)
    if unknown:
        raise V6FoundationError(
            f"{artifact_type} contains undeclared fields: {', '.join(unknown)}"
        )


@dataclass(frozen=True)
class CreationMetadataV1:
    """Dataset-neutral creation metadata for v6 foundation artifacts."""

    created_at: str
    created_by: str
    code_commit: str
    config_hash: str | None = None

    def __post_init__(self) -> None:
        parse_iso_datetime(self.created_at, "creation_metadata.created_at")
        if not self.created_by:
            raise V6FoundationError("creation_metadata.created_by is required")
        if _COMMIT_PATTERN.fullmatch(self.code_commit) is None:
            raise V6FoundationError("creation_metadata.code_commit is invalid")
        if self.config_hash is not None:
            require_sha256(self.config_hash, "creation_metadata.config_hash")

    def to_dict(self) -> dict[str, Any]:
        return {
            "created_at": self.created_at,
            "created_by": self.created_by,
            "code_commit": self.code_commit,
            "config_hash": self.config_hash,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "CreationMetadataV1":
        reject_unknown_fields(
            data,
            frozenset({"created_at", "created_by", "code_commit", "config_hash"}),
            "creation_metadata",
        )
        return cls(
            created_at=str(data["created_at"]),
            created_by=str(data["created_by"]),
            code_commit=str(data["code_commit"]),
            config_hash=data.get("config_hash"),
        )
