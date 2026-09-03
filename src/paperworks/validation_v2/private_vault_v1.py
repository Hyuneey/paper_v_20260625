"""Allowlisted private artifact preservation, without scientific producers."""
from __future__ import annotations

from hashlib import sha256
import json
import os
from pathlib import Path
import shutil
import stat
from typing import Any


def validate_private_path_v1(path: Path, *, allowed_root: Path) -> Path:
    """Reject lexical escape and every existing symlink/reparse ancestor before I/O."""
    path=Path(os.path.abspath(path)); root=Path(os.path.abspath(allowed_root))
    if not path.is_relative_to(root):
        raise ValueError("PRIVATE_PATH_OUTSIDE_AUTHORIZED_ROOT")
    for part in reversed((path,*path.parents)):
        try: info=part.lstat()
        except FileNotFoundError: continue
        if stat.S_ISLNK(info.st_mode) or getattr(info,"st_file_attributes",0)&getattr(stat,"FILE_ATTRIBUTE_REPARSE_POINT",1024):
            raise ValueError("PRIVATE_REPARSE_PATH_REJECTED")
    return path


def file_identity_v1(path: Path) -> tuple[str, int]:
    if path.is_symlink() or not path.is_file():
        raise ValueError("PRIVATE_ARTIFACT_NOT_REGULAR")
    digest, size = sha256(), 0
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
            size += len(block)
    return digest.hexdigest(), size


def publish_private_bytes_v1(path: Path, payload: bytes) -> None:
    """No overwrite, fsync, close and exact reopen. Existing identical is replay."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if file_identity_v1(path) != (sha256(payload).hexdigest(), len(payload)):
            raise ValueError("PRIVATE_EXISTING_BYTES_DIFFER")
        return
    temporary = path.with_name(path.name + ".publishing")
    fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "wb") as stream:
        stream.write(payload)
        stream.flush()
        os.fsync(stream.fileno())
    # Link publication is atomic and fails if destination already exists.
    os.link(temporary, path)
    temporary.unlink()
    if file_identity_v1(path) != (sha256(payload).hexdigest(), len(payload)):
        raise ValueError("PRIVATE_PUBLICATION_REPLAY_FAILED")


def preserve_private_artifact_v1(*, source: Path, vault: Path, artifact_id: str,
                                 expected_hash: str, restore_target: Path | None = None) -> dict[str, Any]:
    """Copy one explicitly approved file and replay; never claim independent backup."""
    if not artifact_id or any(c not in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_-" for c in artifact_id):
        raise ValueError("PRIVATE_ARTIFACT_ID_INVALID")
    before = file_identity_v1(source)
    if before[0] != expected_hash:
        raise ValueError("REQUIRED_ARTIFACT_HASH_MISMATCH")
    destination = vault / "objects" / artifact_id / expected_hash
    destination.parent.mkdir(parents=True, exist_ok=True)
    if not destination.exists():
        temporary = destination.with_name(destination.name + ".publishing")
        with source.open("rb") as src, temporary.open("xb") as dst:
            shutil.copyfileobj(src, dst, 1024 * 1024)
            dst.flush()
            os.fsync(dst.fileno())
        if file_identity_v1(temporary) != before:
            raise ValueError("PRIVATE_COPY_HASH_MISMATCH")
        os.link(temporary, destination)
        temporary.unlink()
    if file_identity_v1(destination) != before or file_identity_v1(source) != before:
        raise ValueError("PRIVATE_PRESERVATION_REPLAY_FAILED")
    if restore_target is not None:
        publish_private_bytes_v1(restore_target, destination.read_bytes())
        if file_identity_v1(restore_target) != before:
            raise ValueError("PRIVATE_RESTORE_HASH_MISMATCH")
    return {"artifact_id": artifact_id, "content_hash": before[0], "size": before[1],
            "exists": True, "backup_status": "SINGLE_COPY_LOCAL_ONLY",
            "restore_status": "EXACT_BYTE_REPLAY_PASS", "source_unchanged": True,
            "private_source": str(source), "private_vault_object": str(destination),
            "private_restore_target": str(restore_target) if restore_target else None}


def public_artifact_record_v1(record: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in record.items() if not key.startswith("private_")}
