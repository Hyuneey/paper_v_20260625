"""Bounded-memory file hashing for VALIDATION V2 custody checks.

The helper deliberately returns only a digest.  It does not interpret payloads,
change custody read frequency, or expose paths.  Callers remain responsible for
their existing path, authority, and mutation checks.
"""

from __future__ import annotations

from hashlib import sha256
from pathlib import Path


DEFAULT_HASH_CHUNK_BYTES = 1024 * 1024


def sha256_file_v1(path: Path, *, chunk_bytes: int = DEFAULT_HASH_CHUNK_BYTES) -> str:
    """Return a SHA-256 digest while keeping memory bounded by ``chunk_bytes``."""

    if not isinstance(path, Path):
        raise TypeError("path must be a pathlib.Path")
    if type(chunk_bytes) is not int or chunk_bytes <= 0:
        raise ValueError("chunk_bytes must be a positive exact integer")
    digest = sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(chunk_bytes), b""):
            digest.update(block)
    return digest.hexdigest()


__all__ = ["DEFAULT_HASH_CHUNK_BYTES", "sha256_file_v1"]
