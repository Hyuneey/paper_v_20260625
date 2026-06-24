"""Provenance-aware variable metadata schema."""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


METADATA_SCHEMA_VERSION = "1.0"


class MetadataValidationError(ValueError):
    """Raised when variable metadata is invalid or incomplete."""


class VariableRole(str, Enum):
    SENSOR = "sensor"
    ACTUATOR = "actuator"
    UNKNOWN = "unknown"


class ValueType(str, Enum):
    CONTINUOUS = "continuous"
    BINARY = "binary"
    CATEGORICAL = "categorical"
    UNKNOWN = "unknown"


class PhysicalType(str, Enum):
    VALVE = "valve"
    PUMP = "pump"
    FLOW = "flow"
    LEVEL = "level"
    PRESSURE = "pressure"
    QUALITY = "quality"
    OTHER = "other"
    UNKNOWN = "unknown"


class MetadataSourceMethod(str, Enum):
    DATASET_DOCUMENTATION = "dataset_documentation"
    NAME_PATTERN = "name_pattern"
    MANUAL_REVIEW = "manual_review"
    INFERRED = "inferred"
    UNKNOWN = "unknown"


class ReviewStatus(str, Enum):
    UNREVIEWED = "unreviewed"
    REVIEWED = "reviewed"
    REJECTED = "rejected"


@dataclass(frozen=True)
class VariableMetadata:
    name: str
    role: VariableRole
    value_type: ValueType
    physical_type: PhysicalType
    subsystem: str | None = None
    stage: str | None = None
    unit: str | None = None
    allowed_states: tuple[str, ...] | None = None
    source_method: MetadataSourceMethod = MetadataSourceMethod.UNKNOWN
    source_reference: str | None = None
    confidence: float | None = None
    review_status: ReviewStatus = ReviewStatus.UNREVIEWED
    schema_version: str = METADATA_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.schema_version != METADATA_SCHEMA_VERSION:
            raise MetadataValidationError(f"unsupported metadata schema_version: {self.schema_version}")
        if not self.name or not self.name.strip():
            raise MetadataValidationError("metadata name is required")
        if self.confidence is not None and not (0.0 <= self.confidence <= 1.0):
            raise MetadataValidationError("confidence must be between 0 and 1")
        if self.role == VariableRole.ACTUATOR and self.value_type == ValueType.CONTINUOUS:
            raise MetadataValidationError(f"actuator {self.name} cannot have continuous value_type")
        if self.physical_type in {PhysicalType.VALVE, PhysicalType.PUMP} and self.role == VariableRole.SENSOR:
            raise MetadataValidationError(
                f"sensor {self.name} cannot have physical_type {self.physical_type.value}"
            )
        if self.physical_type in {PhysicalType.FLOW, PhysicalType.LEVEL, PhysicalType.PRESSURE, PhysicalType.QUALITY}:
            if self.role == VariableRole.ACTUATOR:
                raise MetadataValidationError(
                    f"actuator {self.name} cannot have physical_type {self.physical_type.value}"
                )
        if self.allowed_states is not None and len(self.allowed_states) == 0:
            raise MetadataValidationError("allowed_states must be omitted or non-empty")
        if self.source_method == MetadataSourceMethod.MANUAL_REVIEW and self.review_status != ReviewStatus.REVIEWED:
            raise MetadataValidationError("manual_review metadata must have review_status=reviewed")

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["role"] = self.role.value
        data["value_type"] = self.value_type.value
        data["physical_type"] = self.physical_type.value
        data["source_method"] = self.source_method.value
        data["review_status"] = self.review_status.value
        data["allowed_states"] = list(self.allowed_states) if self.allowed_states is not None else None
        return data

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "VariableMetadata":
        allowed_states = data.get("allowed_states")
        return cls(
            name=str(data["name"]),
            role=VariableRole(str(data["role"])),
            value_type=ValueType(str(data["value_type"])),
            physical_type=PhysicalType(str(data["physical_type"])),
            subsystem=data.get("subsystem"),
            stage=data.get("stage"),
            unit=data.get("unit"),
            allowed_states=tuple(str(item) for item in allowed_states) if allowed_states is not None else None,
            source_method=MetadataSourceMethod(str(data.get("source_method", MetadataSourceMethod.UNKNOWN.value))),
            source_reference=data.get("source_reference"),
            confidence=float(data["confidence"]) if data.get("confidence") is not None else None,
            review_status=ReviewStatus(str(data.get("review_status", ReviewStatus.UNREVIEWED.value))),
            schema_version=str(data.get("schema_version", METADATA_SCHEMA_VERSION)),
        )


@dataclass(frozen=True)
class MetadataCoverageReport:
    expected_count: int
    metadata_count: int
    missing_features: tuple[str, ...]
    extra_metadata: tuple[str, ...]
    unknown_field_counts: Mapping[str, int]
    source_method_counts: Mapping[str, int]
    review_status_counts: Mapping[str, int]

    @property
    def is_complete(self) -> bool:
        return not self.missing_features and not self.extra_metadata

    def to_dict(self) -> dict[str, Any]:
        return {
            "expected_count": self.expected_count,
            "metadata_count": self.metadata_count,
            "missing_features": list(self.missing_features),
            "extra_metadata": list(self.extra_metadata),
            "unknown_field_counts": dict(self.unknown_field_counts),
            "source_method_counts": dict(self.source_method_counts),
            "review_status_counts": dict(self.review_status_counts),
            "is_complete": self.is_complete,
        }


class MetadataRegistry:
    """Validated metadata lookup by variable name."""

    def __init__(self, variables: Iterable[VariableMetadata]) -> None:
        by_name: dict[str, VariableMetadata] = {}
        duplicates: list[str] = []
        for variable in variables:
            if variable.name in by_name:
                duplicates.append(variable.name)
            by_name[variable.name] = variable
        if duplicates:
            duplicate_list = ", ".join(sorted(set(duplicates)))
            raise MetadataValidationError(f"duplicate metadata names: {duplicate_list}")
        self._by_name = dict(sorted(by_name.items()))

    def __len__(self) -> int:
        return len(self._by_name)

    def __contains__(self, name: str) -> bool:
        return name in self._by_name

    @property
    def names(self) -> tuple[str, ...]:
        return tuple(self._by_name)

    def get(self, name: str) -> VariableMetadata:
        try:
            return self._by_name[name]
        except KeyError as exc:
            raise MetadataValidationError(f"metadata not found for variable: {name}") from exc

    def to_list(self) -> list[dict[str, Any]]:
        return [self._by_name[name].to_dict() for name in self._by_name]

    def to_json(self) -> str:
        return json.dumps(self.to_list(), sort_keys=True, indent=2)

    @classmethod
    def from_list(cls, data: Sequence[Mapping[str, Any]]) -> "MetadataRegistry":
        return cls(VariableMetadata.from_dict(item) for item in data)

    @classmethod
    def from_json(cls, text: str) -> "MetadataRegistry":
        return cls.from_list(json.loads(text))

    def coverage_report(self, expected_features: Sequence[str]) -> MetadataCoverageReport:
        expected = tuple(expected_features)
        expected_set = set(expected)
        observed_set = set(self._by_name)
        missing = tuple(name for name in expected if name not in observed_set)
        extra = tuple(name for name in self.names if name not in expected_set)

        unknown_counts = {
            "role": sum(1 for item in self._by_name.values() if item.role == VariableRole.UNKNOWN),
            "value_type": sum(1 for item in self._by_name.values() if item.value_type == ValueType.UNKNOWN),
            "physical_type": sum(1 for item in self._by_name.values() if item.physical_type == PhysicalType.UNKNOWN),
            "stage": sum(1 for item in self._by_name.values() if item.stage is None),
            "unit": sum(1 for item in self._by_name.values() if item.unit is None),
        }

        source_counts: dict[str, int] = {}
        review_counts: dict[str, int] = {}
        for item in self._by_name.values():
            source_counts[item.source_method.value] = source_counts.get(item.source_method.value, 0) + 1
            review_counts[item.review_status.value] = review_counts.get(item.review_status.value, 0) + 1

        return MetadataCoverageReport(
            expected_count=len(expected),
            metadata_count=len(self._by_name),
            missing_features=missing,
            extra_metadata=extra,
            unknown_field_counts=unknown_counts,
            source_method_counts=source_counts,
            review_status_counts=review_counts,
        )


def validate_feature_coverage(registry: MetadataRegistry, expected_features: Sequence[str]) -> MetadataCoverageReport:
    report = registry.coverage_report(expected_features)
    if not report.is_complete:
        raise MetadataValidationError(
            "metadata coverage mismatch: "
            f"missing={list(report.missing_features)}, extra={list(report.extra_metadata)}"
        )
    return report


def load_metadata_json(path: Path) -> MetadataRegistry:
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if isinstance(payload, dict):
        variables = payload.get("variables")
    else:
        variables = payload
    if not isinstance(variables, list):
        raise MetadataValidationError("metadata JSON must contain a list or a 'variables' list")
    return MetadataRegistry.from_list(variables)


def suggest_metadata_from_name(
    name: str,
    *,
    source_reference: str | None = None,
) -> VariableMetadata:
    prefix_match = re.match(r"([A-Z]+)", name)
    prefix = prefix_match.group(1) if prefix_match else ""
    stage_match = re.search(r"(\d)", name)
    stage = stage_match.group(1) if stage_match else None

    role = VariableRole.UNKNOWN
    value_type = ValueType.UNKNOWN
    physical_type = PhysicalType.UNKNOWN

    if prefix in {"FIT"}:
        role = VariableRole.SENSOR
        value_type = ValueType.CONTINUOUS
        physical_type = PhysicalType.FLOW
    elif prefix in {"LIT"}:
        role = VariableRole.SENSOR
        value_type = ValueType.CONTINUOUS
        physical_type = PhysicalType.LEVEL
    elif prefix in {"PIT", "DPIT"}:
        role = VariableRole.SENSOR
        value_type = ValueType.CONTINUOUS
        physical_type = PhysicalType.PRESSURE
    elif prefix in {"AIT"}:
        role = VariableRole.SENSOR
        value_type = ValueType.CONTINUOUS
        physical_type = PhysicalType.QUALITY
    elif prefix in {"MV"}:
        role = VariableRole.ACTUATOR
        value_type = ValueType.BINARY
        physical_type = PhysicalType.VALVE
    elif prefix in {"P"}:
        role = VariableRole.ACTUATOR
        value_type = ValueType.BINARY
        physical_type = PhysicalType.PUMP
    elif prefix in {"UV"}:
        role = VariableRole.ACTUATOR
        value_type = ValueType.BINARY
        physical_type = PhysicalType.OTHER

    return VariableMetadata(
        name=name,
        role=role,
        value_type=value_type,
        physical_type=physical_type,
        subsystem=f"stage_{stage}" if stage is not None else None,
        stage=stage,
        source_method=MetadataSourceMethod.NAME_PATTERN,
        source_reference=source_reference,
        confidence=0.6 if role != VariableRole.UNKNOWN else 0.2,
        review_status=ReviewStatus.UNREVIEWED,
    )

