"""Dataset-neutral v2 data, view, and split contracts."""

from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from hashlib import sha256
from pathlib import PurePosixPath
from types import MappingProxyType
from typing import Any, Mapping


V2_SCHEMA_VERSION = "2.0.0"
_SHA256_PATTERN = re.compile(r"^[a-f0-9]{64}$")
_COMMIT_PATTERN = re.compile(r"^(?:[a-f0-9]{7,40}|unverified)$")


class DataContractV2Error(ValueError):
    """Raised when a dataset-neutral v2 contract is invalid."""


class ProvenanceStatusV2(str, Enum):
    VERIFIED = "verified"
    UNVERIFIED = "unverified"
    UNKNOWN = "unknown"


class CompressionTypeV2(str, Enum):
    NONE = "none"
    GZIP = "gzip"
    ZIP = "zip"
    BZIP2 = "bzip2"
    XZ = "xz"
    OTHER = "other"
    UNKNOWN = "unknown"


class LabelAvailabilityV2(str, Enum):
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    PARTIAL = "partial"
    UNKNOWN = "unknown"


class DataViewKindV2(str, Enum):
    CANONICAL_RULE = "canonical_rule"
    CANDIDATE_LEARNING = "candidate_learning"
    GDN = "gdn"


class SplitRoleV2(str, Enum):
    NORMAL_CANDIDATE_FIT = "normal_candidate_fit"
    NORMAL_RELATION_CALIBRATION = "normal_relation_calibration"
    NORMAL_GUARD = "normal_guard"
    DEVELOPMENT = "development"
    INNER_UTILITY = "inner_utility"
    OUTER_VALIDATION = "outer_validation"
    SEALED_EVALUATION = "sealed_evaluation"


class SealedAccessStatusV2(str, Enum):
    NOT_APPLICABLE = "not_applicable"
    APPROVAL_REQUIRED = "approval_required"
    APPROVED = "approved"


def _validate_sha256(value: str, field_name: str) -> None:
    if _SHA256_PATTERN.fullmatch(value) is None:
        raise DataContractV2Error(f"{field_name} must be a lowercase SHA-256 digest")


def _validate_relative_path(value: str) -> None:
    if not value or "\\" in value or re.match(r"^[A-Za-z]:", value):
        raise DataContractV2Error("relative_local_path must be a non-empty POSIX relative path")
    parsed = PurePosixPath(value)
    if parsed.is_absolute() or ".." in parsed.parts or "." in parsed.parts:
        raise DataContractV2Error("relative_local_path must remain below the dataset root")


def _parse_datetime(value: str, field_name: str) -> datetime:
    if not isinstance(value, str) or not value:
        raise DataContractV2Error(f"{field_name} must be an ISO 8601 date-time")
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        result = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise DataContractV2Error(f"{field_name} must be an ISO 8601 date-time") from exc
    if result.tzinfo is None:
        raise DataContractV2Error(f"{field_name} must include a timezone")
    return result


def _freeze_json(value: Any) -> Any:
    if isinstance(value, Mapping):
        result: dict[str, Any] = {}
        for key, item in value.items():
            if not isinstance(key, str):
                raise DataContractV2Error("mapping keys must be strings")
            result[key] = _freeze_json(item)
        return MappingProxyType(result)
    if isinstance(value, (list, tuple)):
        return tuple(_freeze_json(item) for item in value)
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise DataContractV2Error("non-finite numbers are prohibited")
        return value
    raise DataContractV2Error(f"value is not JSON-compatible: {type(value).__name__}")


def _thaw_json(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {key: _thaw_json(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_thaw_json(item) for item in value]
    return value


def canonical_json_v2(value: Mapping[str, Any]) -> str:
    """Return deterministic JSON used for v2 artifact identity."""

    return json.dumps(
        _thaw_json(value),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    )


def stable_hash_v2(value: Mapping[str, Any]) -> str:
    """Return a deterministic SHA-256 for a public v2 artifact payload."""

    return sha256(canonical_json_v2(value).encode("utf-8")).hexdigest()


def _verify_optional_artifact_hash(data: Mapping[str, Any], observed: str) -> None:
    supplied = data.get("artifact_hash")
    if supplied is not None and supplied != observed:
        raise DataContractV2Error("artifact_hash does not match the contract content")


@dataclass(frozen=True)
class TimeRangeV2:
    start: str
    end: str

    def __post_init__(self) -> None:
        start = _parse_datetime(self.start, "time_range.start")
        end = _parse_datetime(self.end, "time_range.end")
        if end < start:
            raise DataContractV2Error("time_range.end must not precede time_range.start")

    def to_dict(self) -> dict[str, str]:
        return {"start": self.start, "end": self.end}

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "TimeRangeV2":
        return cls(start=str(data["start"]), end=str(data["end"]))


@dataclass(frozen=True)
class TimestampSpecificationV2:
    field_name: str | None
    format: str | None
    timezone: str | None
    provenance_status: ProvenanceStatusV2

    def __post_init__(self) -> None:
        if self.provenance_status is ProvenanceStatusV2.VERIFIED and not self.field_name:
            raise DataContractV2Error("verified timestamp specification requires field_name")

    def to_dict(self) -> dict[str, Any]:
        return {
            "field_name": self.field_name,
            "format": self.format,
            "timezone": self.timezone,
            "provenance_status": self.provenance_status.value,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "TimestampSpecificationV2":
        return cls(
            field_name=data.get("field_name"),
            format=data.get("format"),
            timezone=data.get("timezone"),
            provenance_status=ProvenanceStatusV2(str(data["provenance_status"])),
        )


@dataclass(frozen=True)
class LabelSpecificationV2:
    field_name: str | None
    encoding: Mapping[str, Any]
    provenance_status: ProvenanceStatusV2

    def __post_init__(self) -> None:
        object.__setattr__(self, "encoding", _freeze_json(self.encoding))
        if any(
            isinstance(item, (Mapping, tuple)) for item in self.encoding.values()
        ):
            raise DataContractV2Error(
                "label encoding values must be JSON primitives"
            )
        if self.provenance_status is ProvenanceStatusV2.VERIFIED and not self.field_name:
            raise DataContractV2Error("verified label specification requires field_name")

    def to_dict(self) -> dict[str, Any]:
        return {
            "field_name": self.field_name,
            "encoding": _thaw_json(self.encoding),
            "provenance_status": self.provenance_status.value,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "LabelSpecificationV2":
        return cls(
            field_name=data.get("field_name"),
            encoding=dict(data.get("encoding", {})),
            provenance_status=ProvenanceStatusV2(str(data["provenance_status"])),
        )


@dataclass(frozen=True)
class CreationMetadataV2:
    created_at: str
    created_by: str
    code_commit: str
    config_hash: str | None = None

    def __post_init__(self) -> None:
        _parse_datetime(self.created_at, "creation_metadata.created_at")
        if not self.created_by:
            raise DataContractV2Error("creation_metadata.created_by is required")
        if _COMMIT_PATTERN.fullmatch(self.code_commit) is None:
            raise DataContractV2Error("creation_metadata.code_commit is invalid")
        if self.config_hash is not None:
            _validate_sha256(self.config_hash, "creation_metadata.config_hash")

    def to_dict(self) -> dict[str, Any]:
        return {
            "created_at": self.created_at,
            "created_by": self.created_by,
            "code_commit": self.code_commit,
            "config_hash": self.config_hash,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "CreationMetadataV2":
        return cls(
            created_at=str(data["created_at"]),
            created_by=str(data["created_by"]),
            code_commit=str(data["code_commit"]),
            config_hash=data.get("config_hash"),
        )


@dataclass(frozen=True)
class DatasetFileV2:
    logical_file_role: str
    relative_local_path: str
    sha256: str
    byte_size: int | None
    row_count: int | None
    compression: CompressionTypeV2
    time_range: TimeRangeV2 | None
    process_ids: tuple[str, ...] | None
    label_availability: LabelAvailabilityV2 | None
    provenance_status: ProvenanceStatusV2

    def __post_init__(self) -> None:
        if not self.logical_file_role:
            raise DataContractV2Error("logical_file_role is required")
        _validate_relative_path(self.relative_local_path)
        _validate_sha256(self.sha256, "sha256")
        if self.byte_size is not None and self.byte_size < 0:
            raise DataContractV2Error("byte_size must be non-negative or null")
        if self.row_count is not None and self.row_count < 0:
            raise DataContractV2Error("row_count must be non-negative or null")
        if self.process_ids is not None:
            normalized = tuple(str(item) for item in self.process_ids)
            if any(not item for item in normalized) or len(set(normalized)) != len(normalized):
                raise DataContractV2Error("process_ids must contain unique non-empty values")
            object.__setattr__(self, "process_ids", normalized)

    def to_dict(self) -> dict[str, Any]:
        return {
            "logical_file_role": self.logical_file_role,
            "relative_local_path": self.relative_local_path,
            "sha256": self.sha256,
            "byte_size": self.byte_size,
            "row_count": self.row_count,
            "compression": self.compression.value,
            "time_range": self.time_range.to_dict() if self.time_range else None,
            "process_ids": list(self.process_ids) if self.process_ids is not None else None,
            "label_availability": (
                self.label_availability.value if self.label_availability else None
            ),
            "provenance_status": self.provenance_status.value,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "DatasetFileV2":
        time_range = data.get("time_range")
        process_ids = data.get("process_ids")
        label_availability = data.get("label_availability")
        return cls(
            logical_file_role=str(data["logical_file_role"]),
            relative_local_path=str(data["relative_local_path"]),
            sha256=str(data["sha256"]),
            byte_size=data.get("byte_size"),
            row_count=data.get("row_count"),
            compression=CompressionTypeV2(str(data["compression"])),
            time_range=TimeRangeV2.from_dict(time_range) if time_range else None,
            process_ids=tuple(str(item) for item in process_ids) if process_ids is not None else None,
            label_availability=(
                LabelAvailabilityV2(str(label_availability))
                if label_availability is not None
                else None
            ),
            provenance_status=ProvenanceStatusV2(str(data["provenance_status"])),
        )


@dataclass(frozen=True)
class DatasetManifestV2:
    dataset_name: str
    dataset_version_or_edition: str
    source_kind: str
    source_reference: str
    license_or_terms_reference: str
    citation_reference: str
    local_only_storage: bool
    files: tuple[DatasetFileV2, ...]
    feature_count: int | None
    feature_names_hash: str | None
    timestamp_specification: TimestampSpecificationV2
    nominal_sampling_interval_seconds: float | None
    label_specification: LabelSpecificationV2 | None
    available_process_ids: tuple[str, ...] | None
    metadata_artifact_references: tuple[str, ...]
    provenance_status: ProvenanceStatusV2
    creation_metadata: CreationMetadataV2
    schema_version: str = V2_SCHEMA_VERSION
    artifact_type: str = "dataset_manifest_v2"

    def __post_init__(self) -> None:
        if self.schema_version != V2_SCHEMA_VERSION:
            raise DataContractV2Error("unsupported dataset manifest schema_version")
        if self.artifact_type != "dataset_manifest_v2":
            raise DataContractV2Error("invalid dataset manifest artifact_type")
        for name, value in (
            ("dataset_name", self.dataset_name),
            ("dataset_version_or_edition", self.dataset_version_or_edition),
            ("source_kind", self.source_kind),
            ("source_reference", self.source_reference),
            ("license_or_terms_reference", self.license_or_terms_reference),
            ("citation_reference", self.citation_reference),
        ):
            if not value:
                raise DataContractV2Error(f"{name} is required; use 'unknown' if unavailable")
        if self.local_only_storage is not True:
            raise DataContractV2Error("local_only_storage must be true")
        if not self.files:
            raise DataContractV2Error("files must contain at least one file record")
        paths = [item.relative_local_path for item in self.files]
        if len(paths) != len(set(paths)):
            raise DataContractV2Error("file relative paths must be unique")
        if self.feature_count is not None and self.feature_count <= 0:
            raise DataContractV2Error("feature_count must be positive or null")
        if self.feature_names_hash is not None:
            _validate_sha256(self.feature_names_hash, "feature_names_hash")
        if (
            self.nominal_sampling_interval_seconds is not None
            and self.nominal_sampling_interval_seconds <= 0
        ):
            raise DataContractV2Error(
                "nominal_sampling_interval_seconds must be positive or null"
            )
        if self.available_process_ids is not None:
            values = tuple(str(item) for item in self.available_process_ids)
            if any(not item for item in values) or len(values) != len(set(values)):
                raise DataContractV2Error(
                    "available_process_ids must contain unique non-empty values"
                )
            object.__setattr__(self, "available_process_ids", values)
        references = tuple(str(item) for item in self.metadata_artifact_references)
        if any(not item for item in references) or len(references) != len(set(references)):
            raise DataContractV2Error(
                "metadata_artifact_references must contain unique non-empty values"
            )
        object.__setattr__(self, "metadata_artifact_references", references)

    def _content_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "artifact_type": self.artifact_type,
            "dataset_name": self.dataset_name,
            "dataset_version_or_edition": self.dataset_version_or_edition,
            "source_kind": self.source_kind,
            "source_reference": self.source_reference,
            "license_or_terms_reference": self.license_or_terms_reference,
            "citation_reference": self.citation_reference,
            "local_only_storage": self.local_only_storage,
            "files": [item.to_dict() for item in self.files],
            "feature_count": self.feature_count,
            "feature_names_hash": self.feature_names_hash,
            "timestamp_specification": self.timestamp_specification.to_dict(),
            "nominal_sampling_interval_seconds": self.nominal_sampling_interval_seconds,
            "label_specification": (
                self.label_specification.to_dict() if self.label_specification else None
            ),
            "available_process_ids": (
                list(self.available_process_ids)
                if self.available_process_ids is not None
                else None
            ),
            "metadata_artifact_references": list(self.metadata_artifact_references),
            "provenance_status": self.provenance_status.value,
            "creation_metadata": self.creation_metadata.to_dict(),
        }

    @property
    def manifest_id(self) -> str:
        return stable_hash_v2(self._content_dict())

    def to_dict(self) -> dict[str, Any]:
        payload = self._content_dict()
        payload["artifact_hash"] = self.manifest_id
        return payload

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, indent=2, ensure_ascii=True)

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "DatasetManifestV2":
        process_ids = data.get("available_process_ids")
        label_specification = data.get("label_specification")
        result = cls(
            dataset_name=str(data["dataset_name"]),
            dataset_version_or_edition=str(data["dataset_version_or_edition"]),
            source_kind=str(data["source_kind"]),
            source_reference=str(data["source_reference"]),
            license_or_terms_reference=str(data["license_or_terms_reference"]),
            citation_reference=str(data["citation_reference"]),
            local_only_storage=data["local_only_storage"] is True,
            files=tuple(DatasetFileV2.from_dict(item) for item in data["files"]),
            feature_count=data.get("feature_count"),
            feature_names_hash=data.get("feature_names_hash"),
            timestamp_specification=TimestampSpecificationV2.from_dict(
                data["timestamp_specification"]
            ),
            nominal_sampling_interval_seconds=data.get(
                "nominal_sampling_interval_seconds"
            ),
            label_specification=(
                LabelSpecificationV2.from_dict(label_specification)
                if label_specification
                else None
            ),
            available_process_ids=(
                tuple(str(item) for item in process_ids)
                if process_ids is not None
                else None
            ),
            metadata_artifact_references=tuple(
                str(item) for item in data.get("metadata_artifact_references", ())
            ),
            provenance_status=ProvenanceStatusV2(str(data["provenance_status"])),
            creation_metadata=CreationMetadataV2.from_dict(data["creation_metadata"]),
            schema_version=str(data.get("schema_version", V2_SCHEMA_VERSION)),
            artifact_type=str(data.get("artifact_type", "dataset_manifest_v2")),
        )
        _verify_optional_artifact_hash(data, result.manifest_id)
        return result

    @classmethod
    def from_json(cls, text: str) -> "DatasetManifestV2":
        return cls.from_dict(json.loads(text))


@dataclass(frozen=True)
class AggregationDescriptionV2:
    method: str
    source_sampling_interval_seconds: float | None
    output_sampling_interval_seconds: float
    explicit: bool
    description: str

    def __post_init__(self) -> None:
        if not self.method or not self.description:
            raise DataContractV2Error("aggregation method and description are required")
        if (
            self.source_sampling_interval_seconds is not None
            and self.source_sampling_interval_seconds <= 0
        ):
            raise DataContractV2Error(
                "source_sampling_interval_seconds must be positive or null"
            )
        if self.output_sampling_interval_seconds <= 0:
            raise DataContractV2Error("output_sampling_interval_seconds must be positive")
        if self.is_downsampled and not self.explicit:
            raise DataContractV2Error("downsampling must be explicit")

    @property
    def is_downsampled(self) -> bool:
        return (
            self.source_sampling_interval_seconds is not None
            and self.output_sampling_interval_seconds
            > self.source_sampling_interval_seconds
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "method": self.method,
            "source_sampling_interval_seconds": self.source_sampling_interval_seconds,
            "output_sampling_interval_seconds": self.output_sampling_interval_seconds,
            "explicit": self.explicit,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "AggregationDescriptionV2":
        return cls(
            method=str(data["method"]),
            source_sampling_interval_seconds=data.get(
                "source_sampling_interval_seconds"
            ),
            output_sampling_interval_seconds=float(
                data["output_sampling_interval_seconds"]
            ),
            explicit=data["explicit"] is True,
            description=str(data["description"]),
        )


@dataclass(frozen=True)
class DataViewManifestV2:
    view_kind: DataViewKindV2
    source_dataset_manifest_id: str
    process_scope: tuple[str, ...] | None
    sampling_interval_seconds: float
    preprocessing_config: Mapping[str, Any]
    aggregation: AggregationDescriptionV2
    feature_order_hash: str
    second_level_rule_calibration_allowed: bool
    provenance_status: ProvenanceStatusV2
    creation_metadata: CreationMetadataV2
    schema_version: str = V2_SCHEMA_VERSION
    artifact_type: str = "data_view_manifest_v2"

    def __post_init__(self) -> None:
        if self.schema_version != V2_SCHEMA_VERSION:
            raise DataContractV2Error("unsupported data view schema_version")
        if self.artifact_type != "data_view_manifest_v2":
            raise DataContractV2Error("invalid data view artifact_type")
        _validate_sha256(
            self.source_dataset_manifest_id, "source_dataset_manifest_id"
        )
        _validate_sha256(self.feature_order_hash, "feature_order_hash")
        if self.sampling_interval_seconds <= 0:
            raise DataContractV2Error("sampling_interval_seconds must be positive")
        if (
            self.sampling_interval_seconds
            != self.aggregation.output_sampling_interval_seconds
        ):
            raise DataContractV2Error(
                "view sampling interval must match aggregation output interval"
            )
        object.__setattr__(
            self, "preprocessing_config", _freeze_json(self.preprocessing_config)
        )
        if self.process_scope is not None:
            values = tuple(str(item) for item in self.process_scope)
            if not values or any(not item for item in values) or len(values) != len(set(values)):
                raise DataContractV2Error(
                    "process_scope must be null or unique non-empty values"
                )
            object.__setattr__(self, "process_scope", values)
        if self.second_level_rule_calibration_allowed and (
            self.aggregation.source_sampling_interval_seconds is None
            or self.aggregation.is_downsampled
        ):
            raise DataContractV2Error(
                "second-level calibration requires a known non-downsampled view"
            )

    def _content_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "artifact_type": self.artifact_type,
            "view_kind": self.view_kind.value,
            "source_dataset_manifest_id": self.source_dataset_manifest_id,
            "process_scope": (
                list(self.process_scope) if self.process_scope is not None else None
            ),
            "sampling_interval_seconds": self.sampling_interval_seconds,
            "preprocessing_config": _thaw_json(self.preprocessing_config),
            "aggregation": self.aggregation.to_dict(),
            "feature_order_hash": self.feature_order_hash,
            "second_level_rule_calibration_allowed": (
                self.second_level_rule_calibration_allowed
            ),
            "provenance_status": self.provenance_status.value,
            "creation_metadata": self.creation_metadata.to_dict(),
        }

    @property
    def view_id(self) -> str:
        return stable_hash_v2(self._content_dict())

    def to_dict(self) -> dict[str, Any]:
        payload = self._content_dict()
        payload["artifact_hash"] = self.view_id
        return payload

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, indent=2, ensure_ascii=True)

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "DataViewManifestV2":
        process_scope = data.get("process_scope")
        result = cls(
            view_kind=DataViewKindV2(str(data["view_kind"])),
            source_dataset_manifest_id=str(data["source_dataset_manifest_id"]),
            process_scope=(
                tuple(str(item) for item in process_scope)
                if process_scope is not None
                else None
            ),
            sampling_interval_seconds=float(data["sampling_interval_seconds"]),
            preprocessing_config=dict(data.get("preprocessing_config", {})),
            aggregation=AggregationDescriptionV2.from_dict(data["aggregation"]),
            feature_order_hash=str(data["feature_order_hash"]),
            second_level_rule_calibration_allowed=(
                data["second_level_rule_calibration_allowed"] is True
            ),
            provenance_status=ProvenanceStatusV2(str(data["provenance_status"])),
            creation_metadata=CreationMetadataV2.from_dict(data["creation_metadata"]),
            schema_version=str(data.get("schema_version", V2_SCHEMA_VERSION)),
            artifact_type=str(data.get("artifact_type", "data_view_manifest_v2")),
        )
        _verify_optional_artifact_hash(data, result.view_id)
        return result

    @classmethod
    def from_json(cls, text: str) -> "DataViewManifestV2":
        return cls.from_dict(json.loads(text))


@dataclass(frozen=True)
class RawRangeV2:
    start: int
    end: int

    def __post_init__(self) -> None:
        if self.start < 0 or self.end <= self.start:
            raise DataContractV2Error("raw range must satisfy 0 <= start < end")

    def to_dict(self) -> dict[str, int]:
        return {"start": self.start, "end": self.end}

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "RawRangeV2":
        return cls(start=int(data["start"]), end=int(data["end"]))


@dataclass(frozen=True)
class SplitManifestV2:
    dataset_manifest_id: str
    data_view_id: str
    role: SplitRoleV2
    raw_ranges: tuple[RawRangeV2, ...]
    event_ids: tuple[str, ...] | None
    purge_gap_samples: int
    process_scope: tuple[str, ...] | None
    seed: int | None
    creation_policy: str
    provenance_status: ProvenanceStatusV2
    sealed_access_status: SealedAccessStatusV2
    split_before_windowing: bool
    creation_metadata: CreationMetadataV2
    schema_version: str = V2_SCHEMA_VERSION
    artifact_type: str = "split_manifest_v2"

    def __post_init__(self) -> None:
        if self.schema_version != V2_SCHEMA_VERSION:
            raise DataContractV2Error("unsupported split manifest schema_version")
        if self.artifact_type != "split_manifest_v2":
            raise DataContractV2Error("invalid split manifest artifact_type")
        _validate_sha256(self.dataset_manifest_id, "dataset_manifest_id")
        _validate_sha256(self.data_view_id, "data_view_id")
        if not self.raw_ranges:
            raise DataContractV2Error("raw_ranges must not be empty")
        previous_end: int | None = None
        for item in self.raw_ranges:
            if previous_end is not None and item.start < previous_end:
                raise DataContractV2Error(
                    "raw_ranges must be ordered and non-overlapping"
                )
            previous_end = item.end
        if self.purge_gap_samples < 0:
            raise DataContractV2Error("purge_gap_samples must be non-negative")
        if not self.creation_policy:
            raise DataContractV2Error("creation_policy is required")
        if self.split_before_windowing is not True:
            raise DataContractV2Error("split_before_windowing must be true")
        if self.event_ids is not None:
            values = tuple(str(item) for item in self.event_ids)
            if any(not item for item in values) or len(values) != len(set(values)):
                raise DataContractV2Error(
                    "event_ids must contain unique non-empty values"
                )
            object.__setattr__(self, "event_ids", values)
        if self.process_scope is not None:
            values = tuple(str(item) for item in self.process_scope)
            if not values or any(not item for item in values) or len(values) != len(set(values)):
                raise DataContractV2Error(
                    "process_scope must be null or unique non-empty values"
                )
            object.__setattr__(self, "process_scope", values)
        if self.role is SplitRoleV2.SEALED_EVALUATION:
            if self.sealed_access_status is SealedAccessStatusV2.NOT_APPLICABLE:
                raise DataContractV2Error(
                    "sealed_evaluation requires an explicit sealed access status"
                )
        elif self.sealed_access_status is not SealedAccessStatusV2.NOT_APPLICABLE:
            raise DataContractV2Error(
                "non-sealed split must use sealed_access_status=not_applicable"
            )

    def _content_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "artifact_type": self.artifact_type,
            "dataset_manifest_id": self.dataset_manifest_id,
            "data_view_id": self.data_view_id,
            "role": self.role.value,
            "raw_ranges": [item.to_dict() for item in self.raw_ranges],
            "event_ids": list(self.event_ids) if self.event_ids is not None else None,
            "purge_gap_samples": self.purge_gap_samples,
            "process_scope": (
                list(self.process_scope) if self.process_scope is not None else None
            ),
            "seed": self.seed,
            "creation_policy": self.creation_policy,
            "provenance_status": self.provenance_status.value,
            "sealed_access_status": self.sealed_access_status.value,
            "split_before_windowing": self.split_before_windowing,
            "creation_metadata": self.creation_metadata.to_dict(),
        }

    @property
    def split_id(self) -> str:
        return stable_hash_v2(self._content_dict())

    def to_dict(self) -> dict[str, Any]:
        payload = self._content_dict()
        payload["artifact_hash"] = self.split_id
        return payload

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, indent=2, ensure_ascii=True)

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "SplitManifestV2":
        event_ids = data.get("event_ids")
        process_scope = data.get("process_scope")
        result = cls(
            dataset_manifest_id=str(data["dataset_manifest_id"]),
            data_view_id=str(data["data_view_id"]),
            role=SplitRoleV2(str(data["role"])),
            raw_ranges=tuple(RawRangeV2.from_dict(item) for item in data["raw_ranges"]),
            event_ids=(
                tuple(str(item) for item in event_ids)
                if event_ids is not None
                else None
            ),
            purge_gap_samples=int(data["purge_gap_samples"]),
            process_scope=(
                tuple(str(item) for item in process_scope)
                if process_scope is not None
                else None
            ),
            seed=data.get("seed"),
            creation_policy=str(data["creation_policy"]),
            provenance_status=ProvenanceStatusV2(str(data["provenance_status"])),
            sealed_access_status=SealedAccessStatusV2(
                str(data["sealed_access_status"])
            ),
            split_before_windowing=data["split_before_windowing"] is True,
            creation_metadata=CreationMetadataV2.from_dict(data["creation_metadata"]),
            schema_version=str(data.get("schema_version", V2_SCHEMA_VERSION)),
            artifact_type=str(data.get("artifact_type", "split_manifest_v2")),
        )
        _verify_optional_artifact_hash(data, result.split_id)
        return result

    @classmethod
    def from_json(cls, text: str) -> "SplitManifestV2":
        return cls.from_dict(json.loads(text))


def assert_second_level_rule_calibration_compatible(
    view: DataViewManifestV2,
) -> None:
    """Fail when a view cannot support second-level rule calibration."""

    if not view.second_level_rule_calibration_allowed:
        raise DataContractV2Error(
            "view is not authorized for second-level rule calibration"
        )
    if view.aggregation.is_downsampled:
        raise DataContractV2Error(
            "downsampled views cannot calibrate second-level rule parameters"
        )
