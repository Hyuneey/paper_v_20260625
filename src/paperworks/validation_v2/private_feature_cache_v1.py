"""Prospective private normal-feature cache for VALIDATION V2.

The cache is an engineering optimization, never a scientific authority.  It
can only persist already-authorized normal-only P1 matrices outside the Git
repository.  Raw-file identity, parser identity, feature order, sampling
contract, matrix bytes, and cache bytes are all bound in a path-free receipt.

No existing HAI reader is bypassed: a caller must first obtain and validate the
matrix through the normal custody path.  This module has no test1, test2,
held-out, timestamp, label, or attack-metadata interface.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from hashlib import sha256
import json
import os
from pathlib import Path
import re
from typing import Any, Mapping, Sequence

from paperworks.v6.task039e3_r2r_d0_detector_design_v1 import P1_FEATURE_ORDER

from .io_hash_v1 import sha256_file_v1


_HEX64 = re.compile(r"[0-9a-f]{64}\Z")
_TOKEN = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,95}\Z")
_NORMAL_SPLITS = frozenset({"train1", "train2", "train3", "train4"})
_FEATURE_ORDER = tuple(P1_FEATURE_ORDER)


class PrivateFeatureCacheError(RuntimeError):
    """Fail-closed private-cache contract error."""


def _fail(code: str) -> None:
    raise PrivateFeatureCacheError(code)


def _canonical(document: Mapping[str, Any]) -> bytes:
    return json.dumps(
        dict(document), sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("utf-8")


def _sha(value: object, code: str) -> str:
    if type(value) is not str or _HEX64.fullmatch(value) is None:
        _fail(code)
    return value


def _token(value: object, code: str) -> str:
    if type(value) is not str or _TOKEN.fullmatch(value) is None:
        _fail(code)
    return value


def _numpy() -> Any:
    try:
        import numpy as np
    except ImportError as exc:  # pragma: no cover - optional environment
        raise PrivateFeatureCacheError("FEATURE_CACHE_NUMPY_UNAVAILABLE") from exc
    return np


def _matrix_hash(matrix: Any, *, feature_order_hash: str) -> str:
    digest = sha256()
    digest.update(_canonical({
        "dtype": "float64",
        "feature_count": 37,
        "feature_order_hash": feature_order_hash,
        "shape": [int(matrix.shape[0]), int(matrix.shape[1])],
    }))
    try:
        digest.update(memoryview(matrix).cast("B"))
    except (TypeError, ValueError) as exc:
        raise PrivateFeatureCacheError("FEATURE_CACHE_MATRIX_BUFFER_REJECTED") from exc
    return digest.hexdigest()


@dataclass(frozen=True)
class PrivateFeatureCacheReceiptV1:
    split_id: str
    file_id: str
    file_content_sha256: str
    parser_source_sha256: str
    sampling_contract_sha256: str
    feature_order_sha256: str
    matrix_sha256: str
    cache_file_sha256: str
    row_count: int
    feature_count: int
    dtype: str
    cache_byte_size: int
    source_commit: str
    receipt_hash: str = ""

    def body_document(self) -> dict[str, Any]:
        return {
            "schema": "paperworks.validation_v2.private_feature_cache_receipt_v1",
            "schema_version": "1.0.0",
            "split_id": self.split_id,
            "file_id": self.file_id,
            "file_content_sha256": self.file_content_sha256,
            "parser_source_sha256": self.parser_source_sha256,
            "sampling_contract_sha256": self.sampling_contract_sha256,
            "feature_order_sha256": self.feature_order_sha256,
            "matrix_sha256": self.matrix_sha256,
            "cache_file_sha256": self.cache_file_sha256,
            "row_count": self.row_count,
            "feature_count": self.feature_count,
            "dtype": self.dtype,
            "cache_byte_size": self.cache_byte_size,
            "source_commit": self.source_commit,
            "state": "PRIVATE_NORMAL_ONLY_CACHE_REOPENED_AND_PARITY_VERIFIED",
            "scientific_authority": False,
            "persistent_cache_created": True,
            "labels_accessed": False,
            "test1_accesses": 0,
            "test2_accesses": 0,
            "heldout_accesses": 0,
            "private_paths_embedded": False,
            "numeric_values_embedded": False,
        }

    def to_document(self) -> dict[str, Any]:
        return {**self.body_document(), "receipt_hash": self.receipt_hash}


@dataclass(frozen=True)
class PrivateFeatureCacheBindingV1:
    """Process-private path paired with the public-safe receipt."""

    cache_path: Path
    receipt: PrivateFeatureCacheReceiptV1


class PrivateFeatureCacheViewV1:
    """Explicitly closable read-only memory-map view."""

    __slots__ = ("_matrix", "_closed")

    def __init__(self, matrix: Any) -> None:
        self._matrix = matrix
        self._closed = False

    def __enter__(self) -> "PrivateFeatureCacheViewV1":
        return self

    def __exit__(self, _exc_type: Any, _exc: Any, _traceback: Any) -> None:
        self.close()

    @property
    def matrix(self) -> Any:
        if self._closed:
            _fail("FEATURE_CACHE_VIEW_CLOSED")
        return self._matrix

    def close(self) -> None:
        if self._closed:
            return
        mmap = getattr(self._matrix, "_mmap", None)
        if mmap is not None:
            mmap.close()
        self._closed = True


def _validate_common_inputs(
    *, split_id: str, file_id: str, file_content_sha256: str,
    parser_source_sha256: str, sampling_contract_sha256: str,
    source_commit: str, feature_ids: Sequence[str],
) -> str:
    if split_id not in _NORMAL_SPLITS:
        _fail("FEATURE_CACHE_NON_NORMAL_SPLIT_REJECTED")
    _token(file_id, "FEATURE_CACHE_FILE_ID_REJECTED")
    _sha(file_content_sha256, "FEATURE_CACHE_FILE_HASH_REJECTED")
    _sha(parser_source_sha256, "FEATURE_CACHE_PARSER_HASH_REJECTED")
    _sha(sampling_contract_sha256, "FEATURE_CACHE_SAMPLING_HASH_REJECTED")
    if type(source_commit) is not str or len(source_commit) != 40 or set(source_commit) - set("0123456789abcdef"):
        _fail("FEATURE_CACHE_SOURCE_COMMIT_REJECTED")
    if tuple(feature_ids) != _FEATURE_ORDER:
        _fail("FEATURE_CACHE_FEATURE_ORDER_REJECTED")
    return sha256(_canonical({"feature_ids": list(_FEATURE_ORDER)})).hexdigest()


def persist_private_feature_cache_v1(
    *, repository_root: Path, private_root: Path, split_id: str, file_id: str,
    file_content_sha256: str, parser_source_sha256: str,
    sampling_contract_sha256: str, source_commit: str,
    feature_ids: Sequence[str], matrix: Any,
) -> PrivateFeatureCacheBindingV1:
    """Atomically persist and replay one authorized normal-only feature matrix."""

    feature_order_sha256 = _validate_common_inputs(
        split_id=split_id, file_id=file_id, file_content_sha256=file_content_sha256,
        parser_source_sha256=parser_source_sha256,
        sampling_contract_sha256=sampling_contract_sha256,
        source_commit=source_commit, feature_ids=feature_ids,
    )
    repository = repository_root.resolve(strict=True)
    root = private_root.resolve()
    replay = None
    try:
        root.relative_to(repository)
    except ValueError:
        pass
    else:
        _fail("FEATURE_CACHE_ROOT_INSIDE_REPOSITORY_REJECTED")
    root.mkdir(parents=True, exist_ok=True)
    destination = (root / f"{split_id}.features.v1.npy").resolve()
    if destination.parent != root:
        _fail("FEATURE_CACHE_PATH_ESCAPE_REJECTED")
    temporary = destination.with_suffix(destination.suffix + ".partial")
    if destination.exists() or temporary.exists():
        _fail("FEATURE_CACHE_EXISTING_OR_PARTIAL_REJECTED")

    np = _numpy()
    prepared = np.ascontiguousarray(matrix, dtype=np.float64)
    if prepared.ndim != 2 or prepared.shape[0] <= 0 or prepared.shape[1] != 37:
        _fail("FEATURE_CACHE_MATRIX_SHAPE_REJECTED")
    if not bool(np.isfinite(prepared).all()):
        _fail("FEATURE_CACHE_NONFINITE_REJECTED")
    matrix_sha256 = _matrix_hash(prepared, feature_order_hash=feature_order_sha256)
    try:
        with temporary.open("xb") as stream:
            np.save(stream, prepared, allow_pickle=False)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, destination)
        replay = np.load(destination, mmap_mode="r", allow_pickle=False)
        if replay.dtype != np.dtype("float64") or replay.shape != prepared.shape:
            _fail("FEATURE_CACHE_REPLAY_SCHEMA_MISMATCH")
        if _matrix_hash(replay, feature_order_hash=feature_order_sha256) != matrix_sha256:
            _fail("FEATURE_CACHE_MATRIX_PARITY_MISMATCH")
        replay.flags.writeable = False
        cache_file_sha256 = sha256_file_v1(destination)
        cache_byte_size = destination.stat().st_size
    finally:
        mmap = getattr(replay, "_mmap", None)
        if mmap is not None:
            mmap.close()
        if temporary.exists():
            temporary.unlink()

    provisional = PrivateFeatureCacheReceiptV1(
        split_id=split_id, file_id=file_id,
        file_content_sha256=file_content_sha256,
        parser_source_sha256=parser_source_sha256,
        sampling_contract_sha256=sampling_contract_sha256,
        feature_order_sha256=feature_order_sha256,
        matrix_sha256=matrix_sha256,
        cache_file_sha256=cache_file_sha256,
        row_count=int(prepared.shape[0]), feature_count=37, dtype="float64",
        cache_byte_size=cache_byte_size, source_commit=source_commit,
    )
    receipt = replace(
        provisional,
        receipt_hash=sha256(_canonical(provisional.body_document())).hexdigest(),
    )
    return PrivateFeatureCacheBindingV1(destination, receipt)


def reopen_private_feature_cache_v1(binding: PrivateFeatureCacheBindingV1) -> PrivateFeatureCacheViewV1:
    """Reopen a frozen cache only after byte and matrix parity replay."""

    if type(binding) is not PrivateFeatureCacheBindingV1:
        _fail("FEATURE_CACHE_BINDING_TYPE_REJECTED")
    receipt = binding.receipt
    if receipt.receipt_hash != sha256(_canonical(receipt.body_document())).hexdigest():
        _fail("FEATURE_CACHE_RECEIPT_REPLAY_REJECTED")
    if binding.cache_path.stat().st_size != receipt.cache_byte_size:
        _fail("FEATURE_CACHE_BYTE_SIZE_MISMATCH")
    if sha256_file_v1(binding.cache_path) != receipt.cache_file_sha256:
        _fail("FEATURE_CACHE_BYTES_MUTATED")
    np = _numpy()
    replay = np.load(binding.cache_path, mmap_mode="r", allow_pickle=False)
    if replay.shape != (receipt.row_count, receipt.feature_count) or str(replay.dtype) != receipt.dtype:
        _fail("FEATURE_CACHE_REPLAY_SCHEMA_MISMATCH")
    if _matrix_hash(replay, feature_order_hash=receipt.feature_order_sha256) != receipt.matrix_sha256:
        _fail("FEATURE_CACHE_MATRIX_PARITY_MISMATCH")
    replay.flags.writeable = False
    return PrivateFeatureCacheViewV1(replay)


__all__ = [
    "PrivateFeatureCacheBindingV1",
    "PrivateFeatureCacheError",
    "PrivateFeatureCacheReceiptV1",
    "PrivateFeatureCacheViewV1",
    "persist_private_feature_cache_v1",
    "reopen_private_feature_cache_v1",
]
