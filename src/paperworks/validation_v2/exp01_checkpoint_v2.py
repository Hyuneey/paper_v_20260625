"""Private, atomic EXP-01 checkpoint custody.

Checkpoint bytes remain outside Git.  Public callers receive only hashes and
sanitized identities.  The canonical state hash is independent of the
``torch.save`` container format and is replayed after close/reopen.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
import os
from pathlib import Path
from typing import Any, Mapping

from paperworks.v6.common import stable_hash_v1

from .io_hash_v1 import sha256_file_v1


class Exp01CheckpointError(RuntimeError):
    pass


def _safe_token(value: str, name: str) -> str:
    if not value or any(ch not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-" for ch in value):
        raise Exp01CheckpointError(f"unsafe {name}")
    return value


def canonical_state_hash_v2(state: Mapping[str, Any]) -> str:
    """Hash ordered tensor metadata and bytes without serializing values publicly."""

    digest = sha256()
    for name in sorted(state):
        tensor = state[name]
        if not hasattr(tensor, "detach"):
            raise Exp01CheckpointError("checkpoint state must contain tensors only")
        cpu = tensor.detach().cpu().contiguous()
        header = json.dumps(
            {"name": name, "dtype": str(cpu.dtype), "shape": list(cpu.shape)},
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        digest.update(len(header).to_bytes(8, "big"))
        digest.update(header)
        try:
            digest.update(memoryview(cpu.numpy()).cast("B"))
        except (TypeError, ValueError) as exc:
            raise Exp01CheckpointError("checkpoint tensor buffer cannot be hashed") from exc
    return digest.hexdigest()


@dataclass(frozen=True)
class Exp01CheckpointReceiptV2:
    run_id: str
    arm_id: str
    view_id: str
    seed: int
    code_authority_hash: str
    training_config_hash: str
    state_hash: str
    file_sha256: str
    byte_size: int
    reopened: bool
    schema: str = "paperworks.validation_v2.exp01_private_checkpoint_receipt_v2"
    schema_version: str = "2.0.0"
    receipt_hash: str = ""

    def to_dict(self, *, include_hash: bool = True) -> dict[str, object]:
        value = dict(self.__dict__)
        if not include_hash:
            value.pop("receipt_hash", None)
        return value


def persist_private_checkpoint_v2(
    *,
    private_root: Path,
    run_id: str,
    arm_id: str,
    view_id: str,
    seed: int,
    code_authority_hash: str,
    training_config_hash: str,
    state_dict: Mapping[str, Any],
) -> tuple[Path, Exp01CheckpointReceiptV2]:
    """Atomically write, fsync, close, reopen, and replay one best state."""

    import torch

    for value, name in ((run_id, "run_id"), (arm_id, "arm_id"), (view_id, "view_id")):
        _safe_token(value, name)
    root = private_root.resolve()
    root.mkdir(parents=True, exist_ok=True)
    destination = (root / f"{run_id}.pt").resolve()
    if destination.parent != root:
        raise Exp01CheckpointError("checkpoint path escaped private root")
    temporary = destination.with_suffix(".pt.partial")
    if destination.exists() or temporary.exists():
        raise Exp01CheckpointError("existing or partial checkpoint requires explicit verified resume")
    state_hash = canonical_state_hash_v2(state_dict)
    payload = {
        "schema": "paperworks.validation_v2.exp01_private_checkpoint_v2",
        "schema_version": "2.0.0",
        "run_id": run_id,
        "arm_id": arm_id,
        "view_id": view_id,
        "seed": seed,
        "code_authority_hash": code_authority_hash,
        "training_config_hash": training_config_hash,
        "state_hash": state_hash,
        "state_dict": {name: value.detach().cpu().contiguous() for name, value in state_dict.items()},
    }
    try:
        with temporary.open("wb") as handle:
            torch.save(payload, handle)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, destination)
        try:
            directory_fd = os.open(root, os.O_RDONLY)
        except OSError:
            directory_fd = None
        if directory_fd is not None:
            try:
                os.fsync(directory_fd)
            finally:
                os.close(directory_fd)
        file_sha256 = sha256_file_v1(destination)
        byte_size = destination.stat().st_size
        reopened = torch.load(destination, map_location="cpu", weights_only=False)
    finally:
        if temporary.exists():
            temporary.unlink()
    if (
        reopened.get("run_id") != run_id
        or reopened.get("arm_id") != arm_id
        or reopened.get("view_id") != view_id
        or reopened.get("seed") != seed
        or reopened.get("code_authority_hash") != code_authority_hash
        or reopened.get("training_config_hash") != training_config_hash
        or reopened.get("state_hash") != state_hash
        or canonical_state_hash_v2(reopened.get("state_dict", {})) != state_hash
    ):
        raise Exp01CheckpointError("checkpoint close/reopen replay failed")
    values = {
        "run_id": run_id,
        "arm_id": arm_id,
        "view_id": view_id,
        "seed": seed,
        "code_authority_hash": code_authority_hash,
        "training_config_hash": training_config_hash,
        "state_hash": state_hash,
        "file_sha256": file_sha256,
        "byte_size": byte_size,
        "reopened": True,
    }
    provisional = Exp01CheckpointReceiptV2(**values)
    receipt = Exp01CheckpointReceiptV2(
        **{**values, "receipt_hash": stable_hash_v1(provisional.to_dict(include_hash=False))}
    )
    return destination, receipt


def reopen_private_checkpoint_v2(
    path: Path, *, expected_receipt: Exp01CheckpointReceiptV2,
) -> Mapping[str, Any]:
    import torch

    if path.stat().st_size != expected_receipt.byte_size or sha256_file_v1(path) != expected_receipt.file_sha256:
        raise Exp01CheckpointError("checkpoint bytes changed after freeze")
    payload = torch.load(path, map_location="cpu", weights_only=False)
    if canonical_state_hash_v2(payload.get("state_dict", {})) != expected_receipt.state_hash:
        raise Exp01CheckpointError("checkpoint state changed after freeze")
    return payload


def recover_existing_private_checkpoint_v2(
    *,
    private_root: Path,
    run_id: str,
    arm_id: str,
    view_id: str,
    seed: int,
    expected_code_authority_hash: str,
    expected_training_config_hash: str,
) -> tuple[Path, Exp01CheckpointReceiptV2, Mapping[str, Any]]:
    """Bind a pre-existing interrupted-run checkpoint without rewriting it.

    Recovery is intentionally stricter than ordinary reopen: the exact file
    name, schedule identity, origin code authority, training configuration,
    payload schema, file bytes, and canonical tensor state are replayed before
    a new post-processing process may use the checkpoint.
    """

    for value, name in ((run_id, "run_id"), (arm_id, "arm_id"), (view_id, "view_id")):
        _safe_token(value, name)
    root = private_root.resolve(strict=True)
    destination = (root / f"{run_id}.pt").resolve(strict=True)
    if destination.parent != root:
        raise Exp01CheckpointError("checkpoint recovery path escaped private root")
    partial = destination.with_suffix(".pt.partial")
    if partial.exists():
        raise Exp01CheckpointError("partial checkpoint blocks recovery")
    file_sha256 = sha256_file_v1(destination)
    byte_size = destination.stat().st_size
    import torch

    payload = torch.load(destination, map_location="cpu", weights_only=True)
    expected = {
        "schema": "paperworks.validation_v2.exp01_private_checkpoint_v2",
        "schema_version": "2.0.0",
        "run_id": run_id,
        "arm_id": arm_id,
        "view_id": view_id,
        "seed": seed,
        "code_authority_hash": expected_code_authority_hash,
        "training_config_hash": expected_training_config_hash,
    }
    if any(payload.get(name) != value for name, value in expected.items()):
        raise Exp01CheckpointError("existing checkpoint authority or schedule mismatch")
    state_hash = canonical_state_hash_v2(payload.get("state_dict", {}))
    if payload.get("state_hash") != state_hash:
        raise Exp01CheckpointError("existing checkpoint state hash mismatch")
    values = {
        "run_id": run_id,
        "arm_id": arm_id,
        "view_id": view_id,
        "seed": seed,
        "code_authority_hash": expected_code_authority_hash,
        "training_config_hash": expected_training_config_hash,
        "state_hash": state_hash,
        "file_sha256": file_sha256,
        "byte_size": byte_size,
        "reopened": True,
    }
    provisional = Exp01CheckpointReceiptV2(**values)
    receipt = Exp01CheckpointReceiptV2(
        **{**values, "receipt_hash": stable_hash_v1(provisional.to_dict(include_hash=False))}
    )
    return destination, receipt, payload


__all__ = [
    "Exp01CheckpointError", "Exp01CheckpointReceiptV2", "canonical_state_hash_v2",
    "persist_private_checkpoint_v2", "recover_existing_private_checkpoint_v2",
    "reopen_private_checkpoint_v2",
]
