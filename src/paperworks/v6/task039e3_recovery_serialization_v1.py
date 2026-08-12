"""Recovery-safe public JSON serialization for TASK-039E3.

This module is deliberately additive.  It does not modify the historical E3
writer that failed on nested immutable mappings.  Recovery artifacts pass
through a recursive, closed JSON conversion before hashing or filesystem I/O.
"""

from __future__ import annotations

import json
import math
import os
import tempfile
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from paperworks.v6.common import stable_hash_v1


class RecoverySerializationError(ValueError):
    """Raised when a recovery public artifact cannot be serialized safely."""


def _location_v1(parent: str, child: str | int) -> str:
    if isinstance(child, int):
        return f"{parent}[{child}]"
    return f"{parent}.{child}"


def normalize_plain_json_v1(value: Any, *, _path: str = "$") -> Any:
    """Recursively convert supported immutable containers to plain JSON values.

    The accepted domain is intentionally closed.  In particular, unknown
    objects are never converted with ``str`` or ``repr`` because doing so can
    silently disclose private state or make artifact hashes unstable.
    """

    if isinstance(value, Mapping):
        normalized: dict[str, Any] = {}
        for key, item in value.items():
            if not isinstance(key, str):
                raise RecoverySerializationError(
                    f"unsupported mapping key at {_path}: {type(key).__name__}"
                )
            normalized[key] = normalize_plain_json_v1(
                item, _path=_location_v1(_path, key)
            )
        return normalized
    if isinstance(value, (tuple, list)):
        return [
            normalize_plain_json_v1(item, _path=_location_v1(_path, index))
            for index, item in enumerate(value)
        ]
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise RecoverySerializationError(f"non-finite number at {_path}")
        return value
    raise RecoverySerializationError(
        f"unsupported JSON value at {_path}: {type(value).__name__}"
    )


def canonical_json_v1(document: Mapping[str, Any]) -> str:
    """Return repository-compatible compact canonical JSON."""

    normalized = normalize_plain_json_v1(document)
    if not isinstance(normalized, dict):  # defensive; Mapping always normalizes so
        raise RecoverySerializationError("public artifact must be a JSON object")
    return json.dumps(
        normalized,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    )


def public_artifact_hash_v1(document: Mapping[str, Any]) -> str:
    """Hash normalized content, excluding its top-level ``artifact_hash``."""

    normalized = normalize_plain_json_v1(document)
    if not isinstance(normalized, dict):
        raise RecoverySerializationError("public artifact must be a JSON object")
    payload = {key: value for key, value in normalized.items() if key != "artifact_hash"}
    return stable_hash_v1(payload)


def finalize_public_artifact_v1(document: Mapping[str, Any]) -> dict[str, Any]:
    """Normalize, self-hash, and JSON-round-trip a public artifact in memory."""

    normalized = normalize_plain_json_v1(document)
    if not isinstance(normalized, dict):
        raise RecoverySerializationError("public artifact must be a JSON object")
    supplied = normalized.pop("artifact_hash", None)
    artifact_hash = stable_hash_v1(normalized)
    if supplied is not None and supplied != artifact_hash:
        raise RecoverySerializationError("artifact_hash does not match artifact content")
    finalized = {**normalized, "artifact_hash": artifact_hash}
    return verify_public_artifact_v1(finalized)


def verify_public_artifact_v1(document: Mapping[str, Any]) -> dict[str, Any]:
    """Verify self-hash and exact JSON round-trip equality; return a plain copy."""

    normalized = normalize_plain_json_v1(document)
    if not isinstance(normalized, dict):
        raise RecoverySerializationError("public artifact must be a JSON object")
    supplied = normalized.get("artifact_hash")
    if not isinstance(supplied, str):
        raise RecoverySerializationError("artifact_hash is required")
    expected = public_artifact_hash_v1(normalized)
    if supplied != expected:
        raise RecoverySerializationError("artifact_hash does not match artifact content")

    encoded = json.dumps(
        normalized,
        sort_keys=True,
        indent=2,
        ensure_ascii=True,
        allow_nan=False,
    ) + "\n"
    decoded = json.loads(encoded)
    if decoded != normalized:
        raise RecoverySerializationError("JSON round-trip changed artifact content")
    if public_artifact_hash_v1(decoded) != supplied:
        raise RecoverySerializationError("artifact_hash changed after JSON round-trip")
    return decoded


def serialize_public_artifact_v1(document: Mapping[str, Any]) -> bytes:
    """Return verified, canonical-content-equivalent pretty JSON bytes."""

    finalized = finalize_public_artifact_v1(document)
    text = json.dumps(
        finalized,
        sort_keys=True,
        indent=2,
        ensure_ascii=True,
        allow_nan=False,
    ) + "\n"
    decoded = json.loads(text)
    if decoded != finalized:
        raise RecoverySerializationError("serialized artifact failed round-trip equality")
    verify_public_artifact_v1(decoded)
    return text.encode("utf-8")


def _fsync_parent_directory_v1(parent: Path) -> None:
    """Durably sync a directory entry on platforms that support directory fsync."""

    if os.name == "nt":
        return
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
    directory_fd = os.open(parent, flags)
    try:
        os.fsync(directory_fd)
    finally:
        os.close(directory_fd)


def write_public_artifact_atomic_v1(
    path: str | os.PathLike[str], document: Mapping[str, Any]
) -> dict[str, Any]:
    """Atomically write and re-verify a recovery public artifact.

    Serialization and validation finish before a sibling temporary file is
    created.  A failed write or replace removes that temporary file and leaves
    any pre-existing destination untouched.
    """

    destination = Path(path)
    parent = destination.parent
    if not parent.is_dir():
        raise RecoverySerializationError("public artifact parent directory is absent")

    encoded = serialize_public_artifact_v1(document)
    expected = json.loads(encoded.decode("utf-8"))
    temporary_path: Path | None = None
    try:
        descriptor, temporary_name = tempfile.mkstemp(
            prefix=f".{destination.name}.", suffix=".tmp", dir=str(parent)
        )
        temporary_path = Path(temporary_name)
        try:
            with os.fdopen(descriptor, "wb") as handle:
                handle.write(encoded)
                handle.flush()
                os.fsync(handle.fileno())
        except BaseException:
            # fdopen owns the descriptor after construction.
            raise

        os.replace(temporary_path, destination)
        temporary_path = None
        _fsync_parent_directory_v1(parent)

        try:
            observed = json.loads(destination.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise RecoverySerializationError(
                "final public artifact could not be parsed"
            ) from exc
        if observed != expected:
            raise RecoverySerializationError(
                "final public artifact differs from verified in-memory content"
            )
        return verify_public_artifact_v1(observed)
    except RecoverySerializationError:
        raise
    except (OSError, TypeError, ValueError) as exc:
        raise RecoverySerializationError("atomic public artifact write failed") from exc
    finally:
        if temporary_path is not None:
            try:
                temporary_path.unlink(missing_ok=True)
            except OSError:
                # Preserve the original failure. A uniquely named sibling temp
                # is never treated as an authoritative public artifact.
                pass


__all__ = [
    "RecoverySerializationError",
    "canonical_json_v1",
    "finalize_public_artifact_v1",
    "normalize_plain_json_v1",
    "public_artifact_hash_v1",
    "serialize_public_artifact_v1",
    "verify_public_artifact_v1",
    "write_public_artifact_atomic_v1",
]
