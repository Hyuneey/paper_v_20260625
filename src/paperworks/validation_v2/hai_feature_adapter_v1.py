"""Narrow, feature-only HAI 23.05 input boundary for VALIDATION V2.

The adapter deliberately has no label, test2, outer, or held-out mapping.  It
opens one explicitly authorized feature file once, hashes the bytes while
parsing them, validates the file-local one-second coordinate contract, and
returns an immutable private frame plus a path-free public receipt.
"""

from __future__ import annotations

import csv
from datetime import datetime
from hashlib import sha256
import io
import json
import math
import os
from pathlib import Path
import stat
from typing import Any, Mapping, Sequence

from paperworks.v6.task039e3_r2r_d0_detector_design_v1 import P1_FEATURE_ORDER

from .protocol_v1 import ProtocolExecutionGuardV1, ProtocolOperationV1


class HAIFeatureAdapterError(RuntimeError):
    """Path-free fail-closed adapter error."""


_CAPABILITY_ISSUER = object()
_FEATURE_ORDER = tuple(P1_FEATURE_ORDER)
_FEATURE_ORDER_HASH = "a612bdb9850ad0dd865dc62b23199bf2b696452c492e4aabe09fe554fa246d57"
_FEATURE_SET_HASH = "6dea06e82c0d99f35a0d11c5e97503e8bb3a0fc8c1d9963b997986021fd23515"
_RAW_HEADER_HASH = "95968d825d1c9caab778a857cec618b64674ec5a85d94e6952d99c2cab08d16a"


def _fail(code: str) -> None:
    raise HAIFeatureAdapterError(code)


class HAIFeatureFileSpecV1:
    __slots__ = (
        "split_id", "role", "relative_path", "sha256", "byte_size",
        "row_count", "raw_header_sha256", "header_field_count",
    )

    def __init__(
        self,
        *,
        split_id: str,
        role: str,
        relative_path: str,
        sha256_hex: str,
        byte_size: int,
        row_count: int,
        raw_header_sha256: str = _RAW_HEADER_HASH,
        header_field_count: int = 87,
    ) -> None:
        if (
            type(split_id) is not str
            or type(role) is not str
            or type(relative_path) is not str
            or not relative_path.startswith("hai-23.05/")
            or ".." in Path(relative_path).parts
            or Path(relative_path).is_absolute()
            or type(byte_size) is not int
            or byte_size <= 0
            or type(row_count) is not int
            or row_count <= 0
            or type(header_field_count) is not int
            or header_field_count < len(_FEATURE_ORDER) + 1
        ):
            _fail("INVALID_FEATURE_FILE_SPEC")
        for digest in (sha256_hex, raw_header_sha256):
            if type(digest) is not str or len(digest) != 64 or any(ch not in "0123456789abcdef" for ch in digest):
                _fail("INVALID_FEATURE_FILE_SPEC_HASH")
        self.split_id = split_id
        self.role = role
        self.relative_path = relative_path
        self.sha256 = sha256_hex
        self.byte_size = byte_size
        self.row_count = row_count
        self.raw_header_sha256 = raw_header_sha256
        self.header_field_count = header_field_count


_SPECS: dict[str, HAIFeatureFileSpecV1] = {
    "train1": HAIFeatureFileSpecV1(
        split_id="train1", role="NORMAL_FIT_PRIMARY",
        relative_path="hai-23.05/hai-train1.csv",
        sha256_hex="53007b0ba604fbf338e7ac2e08cd81d874b5d1388f3aecb213ddcba5bf2bec4a",
        byte_size=162_418_984, row_count=280_800,
    ),
    "train2": HAIFeatureFileSpecV1(
        split_id="train2", role="NORMAL_FIT_SECONDARY",
        relative_path="hai-23.05/hai-train2.csv",
        sha256_hex="0e520e82bf78a661ab19ce4967f3c766bd809820f457a9c90c365102d4534c56",
        byte_size=169_121_615, row_count=291_600,
    ),
    "train3": HAIFeatureFileSpecV1(
        split_id="train3", role="NORMAL_CONFIRMATION_CALIBRATION",
        relative_path="hai-23.05/hai-train3.csv",
        sha256_hex="bfcec2dc05adea103e7491546b0e28268faaa26d3cc717d10f4595c94b81e85d",
        byte_size=72_774_793, row_count=126_000,
    ),
    "train4": HAIFeatureFileSpecV1(
        split_id="train4", role="NORMAL_POLICY_SELECTION_SANITY",
        relative_path="hai-23.05/hai-train4.csv",
        sha256_hex="56658c83657d42a65db982b864362e0d0ffeb96d1f7b357d5e76e3a5c522d940",
        byte_size=114_494_940, row_count=198_000,
    ),
    "test1": HAIFeatureFileSpecV1(
        split_id="test1", role="DEVELOPMENT_ONLY",
        relative_path="hai-23.05/hai-test1.csv",
        sha256_hex="78c7f1d4de1f2ab9ccc2f8c719f80f831033543adb0c81d0d78f84f40838d4be",
        byte_size=31_255_559, row_count=54_000,
    ),
}

_ALLOWED_OPERATIONS: dict[str, tuple[ProtocolOperationV1, ...]] = {
    "train1": (
        ProtocolOperationV1.CANDIDATE_LEARNING, ProtocolOperationV1.RELATION_FIT,
        ProtocolOperationV1.NUMERIC_FIT, ProtocolOperationV1.DETECTOR_FIT,
    ),
    "train2": (
        ProtocolOperationV1.CANDIDATE_LEARNING, ProtocolOperationV1.RELATION_FIT,
        ProtocolOperationV1.NUMERIC_FIT, ProtocolOperationV1.DETECTOR_FIT,
    ),
    "train3": (
        ProtocolOperationV1.RELATION_CONFIRMATION, ProtocolOperationV1.THRESHOLD_CALIBRATION,
    ),
    "train4": (
        ProtocolOperationV1.NORMAL_POLICY_SELECTION, ProtocolOperationV1.NORMAL_SANITY,
    ),
    "test1": (ProtocolOperationV1.DEVELOPMENT_PREDICTION,),
}


def _is_reparse_point(path: Path) -> bool:
    try:
        attributes = getattr(path.lstat(), "st_file_attributes", 0)
    except OSError:
        _fail("FEATURE_ROOT_IDENTITY_REJECTED")
    return bool(attributes & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0))


def _validate_external_root(repository_root: Path, root: Path) -> tuple[Path, Path]:
    try:
        repository = repository_root.resolve(strict=True)
        resolved = root.resolve(strict=True)
        if not root.is_absolute() or not resolved.is_dir() or _is_reparse_point(root) or _is_reparse_point(resolved):
            _fail("FEATURE_ROOT_IDENTITY_REJECTED")
        try:
            resolved.relative_to(repository)
        except ValueError:
            pass
        else:
            _fail("FEATURE_ROOT_INSIDE_REPOSITORY_REJECTED")
        edition = resolved / "hai-23.05"
        if not edition.is_dir() or edition.is_symlink() or _is_reparse_point(edition):
            _fail("FEATURE_EDITION_IDENTITY_REJECTED")
        return repository, resolved
    except HAIFeatureAdapterError:
        raise
    except (OSError, RuntimeError, ValueError):
        _fail("FEATURE_ROOT_IDENTITY_REJECTED")


class HAIFeatureRootCapabilityV1:
    __slots__ = ("__repository", "__root")

    def __init__(self, token: object, *, repository: Path, root: Path) -> None:
        if token is not _CAPABILITY_ISSUER:
            _fail("FEATURE_ROOT_CAPABILITY_FORGERY_REJECTED")
        self.__repository = repository
        self.__root = root

    def __repr__(self) -> str:
        return "HAIFeatureRootCapabilityV1(<redacted>)"

    def __reduce__(self) -> Any:
        _fail("FEATURE_ROOT_CAPABILITY_SERIALIZATION_REJECTED")

    def _resolve(self, spec: HAIFeatureFileSpecV1) -> Path:
        candidate = self.__root.joinpath(*Path(spec.relative_path).parts)
        try:
            resolved = candidate.resolve(strict=True)
            resolved.relative_to(self.__root)
            if candidate.is_symlink() or _is_reparse_point(candidate) or not resolved.is_file():
                _fail("FEATURE_FILE_IDENTITY_REJECTED")
            return resolved
        except HAIFeatureAdapterError:
            raise
        except (OSError, RuntimeError, ValueError):
            _fail("FEATURE_FILE_IDENTITY_REJECTED")


def _binding_from_file(path: Path) -> str | None:
    if not path.is_file() or path.is_symlink() or _is_reparse_point(path):
        return None
    try:
        entries: dict[str, str] = {}
        for raw in path.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                _fail("CUSTODY_BINDING_FILE_REJECTED")
            key, value = line.split("=", 1)
            entries[key.strip()] = value.strip().strip('"').strip("'")
        return entries.get("HAI_DATA_ROOT")
    except HAIFeatureAdapterError:
        raise
    except (OSError, UnicodeError):
        _fail("CUSTODY_BINDING_FILE_REJECTED")


def resolve_hai_feature_root_capability_v1(repository_root: Path) -> HAIFeatureRootCapabilityV1:
    """Resolve only an explicit environment or ignored local binding."""

    if not isinstance(repository_root, Path):
        _fail("REPOSITORY_ROOT_TYPE_REJECTED")
    raw = os.environ.get("HAI_DATA_ROOT")
    if not raw:
        raw = _binding_from_file(repository_root / ".env.custody.local")
    if not raw:
        _fail("HAI_DATA_ROOT_BINDING_REQUIRED")
    repository, root = _validate_external_root(repository_root, Path(raw))
    return HAIFeatureRootCapabilityV1(_CAPABILITY_ISSUER, repository=repository, root=root)


class _HashingRawReader(io.RawIOBase):
    def __init__(self, path: Path) -> None:
        super().__init__()
        self._stream = path.open("rb", buffering=0)
        self._digest = sha256()
        self._header = bytearray()
        self._header_complete = False
        self.byte_count = 0

    def readable(self) -> bool:
        return True

    def readinto(self, buffer: Any) -> int:
        count = self._stream.readinto(buffer)
        if count:
            block = bytes(memoryview(buffer)[:count])
            self._digest.update(block)
            self.byte_count += count
            if not self._header_complete:
                marker = block.find(b"\n")
                if marker < 0:
                    self._header.extend(block)
                else:
                    self._header.extend(block[:marker])
                    self._header_complete = True
        return count

    @property
    def hexdigest(self) -> str:
        return self._digest.hexdigest()

    @property
    def raw_header(self) -> bytes:
        return bytes(self._header).rstrip(b"\r")

    def close(self) -> None:
        if not self.closed:
            self._stream.close()
        super().close()


class HAIFeatureReadReceiptV1:
    __slots__ = ("_document",)

    def __init__(self, document: Mapping[str, Any]) -> None:
        self._document = dict(document)

    def to_dict(self) -> dict[str, Any]:
        return dict(self._document)


class HAIFeatureFrameV1:
    __slots__ = ("__matrix", "__timestamps", "__receipt")

    def __init__(self, token: object, *, matrix: Any, timestamps: tuple[str, ...], receipt: HAIFeatureReadReceiptV1) -> None:
        if token is not _CAPABILITY_ISSUER:
            _fail("FEATURE_FRAME_FORGERY_REJECTED")
        self.__matrix = matrix
        self.__timestamps = timestamps
        self.__receipt = receipt

    def __repr__(self) -> str:
        return "HAIFeatureFrameV1(<private values redacted>)"

    def __reduce__(self) -> Any:
        _fail("FEATURE_FRAME_SERIALIZATION_REJECTED")

    @property
    def receipt(self) -> HAIFeatureReadReceiptV1:
        return self.__receipt

    def numeric_matrix(self, feature_ids: Sequence[str] = _FEATURE_ORDER) -> Any:
        np = _numpy()
        requested = tuple(feature_ids)
        if not requested or len(requested) != len(set(requested)) or any(item not in _FEATURE_ORDER for item in requested):
            _fail("FEATURE_PROJECTION_REJECTED")
        indices = tuple(_FEATURE_ORDER.index(item) for item in requested)
        if indices == tuple(range(len(_FEATURE_ORDER))):
            result = self.__matrix.view()
        else:
            result = self.__matrix[:, indices].copy()
        result.setflags(write=False)
        return result

    def file_local_timestamps(self) -> tuple[str, ...]:
        return self.__timestamps


class HAIFeatureAccessLedgerV1:
    __slots__ = ("_experiment_id", "_opened", "_labels_accessed")

    def __init__(self, *, experiment_id: str) -> None:
        if type(experiment_id) is not str or not experiment_id.strip():
            _fail("EXPERIMENT_ID_REJECTED")
        self._experiment_id = experiment_id
        self._opened: set[str] = set()
        self._labels_accessed = False

    def authorize_once(self, split_id: str) -> None:
        if self._labels_accessed:
            _fail("FEATURE_ACCESS_AFTER_LABELS_REJECTED")
        if split_id in self._opened:
            _fail("DUPLICATE_FEATURE_FILE_OPEN_REJECTED")
        self._opened.add(split_id)

    def mark_labels_accessed(self) -> None:
        self._labels_accessed = True

    def public_document(self) -> dict[str, Any]:
        return {
            "schema": "paperworks.validation_v2.hai_feature_access_ledger_v1",
            "experiment_id": self._experiment_id,
            "opened_split_ids": sorted(self._opened),
            "feature_file_open_count": len(self._opened),
            "labels_accessed": self._labels_accessed,
            "test2_accesses": 0,
            "heldout_accesses": 0,
        }


def _numpy() -> Any:
    try:
        import numpy as np
    except ImportError as exc:
        raise HAIFeatureAdapterError("NUMPY_DEPENDENCY_REQUIRED") from exc
    return np


def _parse_timestamp(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value)
    except (TypeError, ValueError):
        _fail("FEATURE_TIMESTAMP_REJECTED")
    return parsed


def _load_feature_file_from_spec_v1(
    capability: HAIFeatureRootCapabilityV1,
    spec: HAIFeatureFileSpecV1,
) -> HAIFeatureFrameV1:
    if type(capability) is not HAIFeatureRootCapabilityV1 or type(spec) is not HAIFeatureFileSpecV1:
        _fail("FEATURE_LOAD_TYPE_REJECTED")
    path = capability._resolve(spec)
    try:
        before = path.stat()
        if before.st_size != spec.byte_size:
            _fail("FEATURE_FILE_SIZE_REJECTED")
        np = _numpy()
        matrix = np.empty((spec.row_count, len(_FEATURE_ORDER)), dtype=np.float64)
        timestamps: list[str] = []
        raw = _HashingRawReader(path)
        buffered = io.BufferedReader(raw)
        text = io.TextIOWrapper(buffered, encoding="utf-8-sig", newline="")
        try:
            reader = csv.reader(text)
            header = next(reader)
            if len(header) != spec.header_field_count or len(header) != len(set(header)) or "timestamp" not in header:
                _fail("FEATURE_HEADER_REJECTED")
            observed_p1 = tuple(item for item in header if item.startswith("P1_"))
            if observed_p1 != _FEATURE_ORDER:
                _fail("FEATURE_ORDER_REJECTED")
            timestamp_index = header.index("timestamp")
            feature_indices = tuple(header.index(item) for item in _FEATURE_ORDER)
            previous: datetime | None = None
            for row_index, row in enumerate(reader):
                if row_index >= spec.row_count or len(row) != len(header):
                    _fail("FEATURE_ROW_CLOSURE_REJECTED")
                raw_timestamp = row[timestamp_index]
                current = _parse_timestamp(raw_timestamp)
                if previous is not None and (current - previous).total_seconds() != 1.0:
                    _fail("FEATURE_TIMESTAMP_CONTINUITY_REJECTED")
                previous = current
                timestamps.append(raw_timestamp)
                for column_index, source_index in enumerate(feature_indices):
                    value = float(row[source_index])
                    if not math.isfinite(value):
                        _fail("FEATURE_NONFINITE_REJECTED")
                    matrix[row_index, column_index] = value
            if len(timestamps) != spec.row_count:
                _fail("FEATURE_ROW_CLOSURE_REJECTED")
            text.close()
        finally:
            if not text.closed:
                text.close()
        after = path.stat()
        if (
            raw.byte_count != spec.byte_size
            or raw.hexdigest != spec.sha256
            or sha256(raw.raw_header).hexdigest() != spec.raw_header_sha256
            or before.st_size != after.st_size
            or before.st_mtime_ns != after.st_mtime_ns
        ):
            _fail("FEATURE_FILE_IDENTITY_REJECTED")
        if matrix.shape != (spec.row_count, len(_FEATURE_ORDER)) or not bool(np.isfinite(matrix).all()):
            _fail("FEATURE_MATRIX_REJECTED")
        matrix.setflags(write=False)
        body = {
            "schema": "paperworks.validation_v2.hai_feature_read_receipt_v1",
            "dataset_id": "HAI_23.05",
            "split_id": spec.split_id,
            "split_role": spec.role,
            "file_sha256": spec.sha256,
            "byte_size": spec.byte_size,
            "row_count": spec.row_count,
            "feature_count": len(_FEATURE_ORDER),
            "feature_order_hash": _FEATURE_ORDER_HASH,
            "feature_set_hash": _FEATURE_SET_HASH,
            "raw_header_sha256": spec.raw_header_sha256,
            "sampling_contract": "FILE_LOCAL_STRICT_ONE_SECOND_NO_GAP_NO_DUPLICATE",
            "timezone": "source_unspecified",
            "file_open_count": 1,
            "labels_accessed": False,
            "test2_accesses": 0,
            "heldout_accesses": 0,
        }
        body["receipt_hash"] = sha256(json.dumps(body, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
        return HAIFeatureFrameV1(
            _CAPABILITY_ISSUER,
            matrix=matrix,
            timestamps=tuple(timestamps),
            receipt=HAIFeatureReadReceiptV1(body),
        )
    except HAIFeatureAdapterError:
        raise
    except (OSError, UnicodeError, csv.Error, StopIteration, TypeError, ValueError, OverflowError):
        _fail("FEATURE_PARSE_REJECTED")


def load_authorized_hai_feature_frame_v1(
    *,
    capability: HAIFeatureRootCapabilityV1,
    split_id: str,
    operation: ProtocolOperationV1,
    protocol_guard: ProtocolExecutionGuardV1,
    ledger: HAIFeatureAccessLedgerV1,
) -> HAIFeatureFrameV1:
    """Authorize and open one exact feature split without any label capability."""

    if split_id in {"test2", "outer", "heldout", "sealed", "future_heldout"}:
        _fail("HELDOUT_OR_TEST2_ALIAS_REJECTED")
    spec = _SPECS.get(split_id)
    if spec is None or operation not in _ALLOWED_OPERATIONS[split_id]:
        _fail("SPLIT_OPERATION_REJECTED")
    if type(protocol_guard) is not ProtocolExecutionGuardV1 or type(ledger) is not HAIFeatureAccessLedgerV1:
        _fail("FEATURE_GOVERNANCE_TYPE_REJECTED")
    protocol_guard.authorize(split_id=split_id, operation=operation)
    ledger.authorize_once(split_id)
    return _load_feature_file_from_spec_v1(capability, spec)


def authorized_hai_feature_specs_v1() -> tuple[dict[str, Any], ...]:
    """Return public identities only; never return local paths or capabilities."""

    return tuple(
        {
            "split_id": spec.split_id,
            "role": spec.role,
            "relative_public_id": spec.relative_path,
            "sha256": spec.sha256,
            "byte_size": spec.byte_size,
            "row_count": spec.row_count,
        }
        for spec in _SPECS.values()
    )


__all__ = [
    "HAIFeatureAccessLedgerV1",
    "HAIFeatureAdapterError",
    "HAIFeatureFileSpecV1",
    "HAIFeatureFrameV1",
    "HAIFeatureReadReceiptV1",
    "HAIFeatureRootCapabilityV1",
    "authorized_hai_feature_specs_v1",
    "load_authorized_hai_feature_frame_v1",
    "resolve_hai_feature_root_capability_v1",
]
