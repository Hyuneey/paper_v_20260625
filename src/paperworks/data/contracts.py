"""Typed data contracts for local-only datasets and leakage-safe splits."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from enum import Enum
from hashlib import sha256
from pathlib import PurePosixPath
from typing import Any, Mapping


SCHEMA_VERSION = "1.0"


class ContractError(ValueError):
    """Base class for data-contract validation errors."""


class SplitRole(str, Enum):
    TRAIN_NORMAL = "train_normal"
    CALIBRATION_NORMAL = "calibration_normal"
    VALIDATION = "validation"
    TEST = "test"


class DataViewName(str, Enum):
    CANONICAL_RULE = "canonical_rule"
    GDN = "gdn"


def _canonical_json(data: Mapping[str, Any]) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def stable_hash(data: Mapping[str, Any]) -> str:
    return sha256(_canonical_json(data).encode("utf-8")).hexdigest()


def _validate_relative_path(path: str) -> None:
    parsed = PurePosixPath(path.replace("\\", "/"))
    if parsed.is_absolute() or ".." in parsed.parts:
        raise ContractError(f"path must be relative and stay within the data root: {path}")


@dataclass(frozen=True)
class DatasetFile:
    logical_role: str
    relative_path: str
    sha256: str
    bytes: int | None = None
    rows_excluding_header: int | None = None
    label_counts: Mapping[str, int] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.logical_role:
            raise ContractError("logical_role is required")
        _validate_relative_path(self.relative_path)
        if len(self.sha256) != 64:
            raise ContractError("sha256 must be a 64-character hex digest")
        if self.bytes is not None and self.bytes < 0:
            raise ContractError("bytes must be non-negative")
        if self.rows_excluding_header is not None and self.rows_excluding_header < 0:
            raise ContractError("rows_excluding_header must be non-negative")

    def to_dict(self) -> dict[str, Any]:
        return dict(asdict(self))

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "DatasetFile":
        return cls(
            logical_role=str(data["logical_role"]),
            relative_path=str(data["relative_path"]),
            sha256=str(data["sha256"]),
            bytes=data.get("bytes"),
            rows_excluding_header=data.get("rows_excluding_header"),
            label_counts=dict(data.get("label_counts", {})),
        )


@dataclass(frozen=True)
class DatasetManifest:
    dataset_name: str
    source_kind: str
    source_reference: str
    dataset_edition: str
    normal_data_version: str
    file_fingerprints: Mapping[str, str]
    feature_count: int
    feature_names_hash: str
    timestamp_column: str
    sampling_period_seconds: float
    label_column: str
    label_encoding: Mapping[str, str | int]
    schema_version: str = SCHEMA_VERSION
    dataset_status: str = "local_unverified_smoke_test"
    terms_of_use_status: str = "unverified"
    files: tuple[DatasetFile, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if self.schema_version != SCHEMA_VERSION:
            raise ContractError(f"unsupported schema_version: {self.schema_version}")
        if not self.dataset_name:
            raise ContractError("dataset_name is required")
        if not self.dataset_edition:
            raise ContractError("dataset_edition is required; use 'unverified' if unknown")
        if self.feature_count <= 0:
            raise ContractError("feature_count must be positive")
        if len(self.feature_names_hash) != 64:
            raise ContractError("feature_names_hash must be a 64-character hex digest")
        if self.sampling_period_seconds <= 0:
            raise ContractError("sampling_period_seconds must be positive")
        if not self.timestamp_column or not self.label_column:
            raise ContractError("timestamp_column and label_column are required")
        if not self.label_encoding:
            raise ContractError("label_encoding is required")
        for relative_path, digest in self.file_fingerprints.items():
            _validate_relative_path(relative_path)
            if len(digest) != 64:
                raise ContractError(f"invalid sha256 for {relative_path}")

    @property
    def manifest_id(self) -> str:
        return stable_hash(self.to_dict())

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["files"] = [file.to_dict() for file in self.files]
        data["file_fingerprints"] = dict(self.file_fingerprints)
        data["label_encoding"] = dict(self.label_encoding)
        return data

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, indent=2)

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "DatasetManifest":
        files = tuple(DatasetFile.from_dict(item) for item in data.get("files", ()))
        return cls(
            dataset_name=str(data["dataset_name"]),
            source_kind=str(data["source_kind"]),
            source_reference=str(data["source_reference"]),
            dataset_edition=str(data["dataset_edition"]),
            normal_data_version=str(data["normal_data_version"]),
            file_fingerprints=dict(data["file_fingerprints"]),
            feature_count=int(data["feature_count"]),
            feature_names_hash=str(data["feature_names_hash"]),
            timestamp_column=str(data["timestamp_column"]),
            sampling_period_seconds=float(data["sampling_period_seconds"]),
            label_column=str(data["label_column"]),
            label_encoding=dict(data["label_encoding"]),
            schema_version=str(data.get("schema_version", SCHEMA_VERSION)),
            dataset_status=str(data.get("dataset_status", "local_unverified_smoke_test")),
            terms_of_use_status=str(data.get("terms_of_use_status", "unverified")),
            files=files,
        )

    @classmethod
    def from_json(cls, text: str) -> "DatasetManifest":
        return cls.from_dict(json.loads(text))


@dataclass(frozen=True)
class DataViewManifest:
    name: DataViewName
    sampling_period_seconds: float
    preprocessing_config: Mapping[str, Any]
    upstream_dataset_manifest_id: str
    fingerprint: str
    schema_version: str = SCHEMA_VERSION
    source_view: str | None = None

    def __post_init__(self) -> None:
        if self.sampling_period_seconds <= 0:
            raise ContractError("sampling_period_seconds must be positive")
        if len(self.upstream_dataset_manifest_id) != 64:
            raise ContractError("upstream_dataset_manifest_id must be a manifest hash")
        if len(self.fingerprint) != 64:
            raise ContractError("fingerprint must be a 64-character hex digest")

    @property
    def view_id(self) -> str:
        return stable_hash(self.to_dict())

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "name": self.name.value,
            "source_view": self.source_view or self.name.value,
            "sampling_period_seconds": self.sampling_period_seconds,
            "preprocessing_config": dict(self.preprocessing_config),
            "upstream_dataset_manifest_id": self.upstream_dataset_manifest_id,
            "fingerprint": self.fingerprint,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "DataViewManifest":
        return cls(
            name=DataViewName(str(data["name"])),
            sampling_period_seconds=float(data["sampling_period_seconds"]),
            preprocessing_config=dict(data["preprocessing_config"]),
            upstream_dataset_manifest_id=str(data["upstream_dataset_manifest_id"]),
            fingerprint=str(data["fingerprint"]),
            schema_version=str(data.get("schema_version", SCHEMA_VERSION)),
            source_view=data.get("source_view"),
        )


@dataclass(frozen=True)
class SplitManifest:
    dataset_manifest_id: str
    data_view_id: str
    role: SplitRole
    raw_index_ranges: tuple[tuple[int, int], ...]
    purge_gap_samples: int
    seed: int | None
    schema_version: str = SCHEMA_VERSION

    def __post_init__(self) -> None:
        if len(self.dataset_manifest_id) != 64:
            raise ContractError("dataset_manifest_id must be a manifest hash")
        if len(self.data_view_id) != 64:
            raise ContractError("data_view_id must be a view hash")
        if self.purge_gap_samples < 0:
            raise ContractError("purge_gap_samples must be non-negative")
        previous_end: int | None = None
        for start, end in self.raw_index_ranges:
            if start < 0 or end <= start:
                raise ContractError(f"invalid raw_index_range: {(start, end)}")
            if previous_end is not None and start < previous_end:
                raise ContractError("raw_index_ranges must not overlap")
            previous_end = end

    @property
    def split_id(self) -> str:
        return stable_hash(self.to_dict())

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "dataset_manifest_id": self.dataset_manifest_id,
            "data_view_id": self.data_view_id,
            "role": self.role.value,
            "raw_index_ranges": [list(item) for item in self.raw_index_ranges],
            "purge_gap_samples": self.purge_gap_samples,
            "seed": self.seed,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, indent=2)

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "SplitManifest":
        return cls(
            dataset_manifest_id=str(data["dataset_manifest_id"]),
            data_view_id=str(data["data_view_id"]),
            role=SplitRole(str(data["role"])),
            raw_index_ranges=tuple(tuple(int(v) for v in item) for item in data["raw_index_ranges"]),
            purge_gap_samples=int(data["purge_gap_samples"]),
            seed=data.get("seed"),
            schema_version=str(data.get("schema_version", SCHEMA_VERSION)),
        )

    @classmethod
    def from_json(cls, text: str) -> "SplitManifest":
        return cls.from_dict(json.loads(text))

