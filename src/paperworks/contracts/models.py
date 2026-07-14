"""Immutable records for structural validation and migration assessment."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping


@dataclass(frozen=True)
class SchemaRegistration:
    registry_version: str
    contract_commit: str
    artifact_type: str
    schema_file: str
    schema_id: str
    schema_version: str
    schema_sha256: str
    format_validation: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class StructuralValidationIssue:
    issue_code: str
    instance_path: str
    schema_path: str
    validator_keyword: str
    message: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass(frozen=True)
class StructuralValidationReport:
    registry_version: str
    artifact_type: str
    schema_id: str
    schema_version: str
    schema_sha256: str
    instance_sha256: str
    status: str
    issues: tuple[StructuralValidationIssue, ...]

    def __post_init__(self) -> None:
        if self.status not in {"valid", "invalid", "registry_error"}:
            raise ValueError(f"unsupported structural validation status: {self.status}")

    def to_dict(self) -> dict[str, Any]:
        return {
            "registry_version": self.registry_version,
            "artifact_type": self.artifact_type,
            "schema_id": self.schema_id,
            "schema_version": self.schema_version,
            "schema_sha256": self.schema_sha256,
            "instance_sha256": self.instance_sha256,
            "status": self.status,
            "issues": [issue.to_dict() for issue in self.issues],
        }


@dataclass(frozen=True)
class LegacyFieldMapping:
    legacy_field: str
    target_field: str
    mapping: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass(frozen=True)
class LegacyMigrationAssessment:
    adapter_version: str
    source_schema_identifier: str
    source_artifact_type: str
    source_sha256: str
    target_schema_version: str
    target_artifact_type: str
    target_artifact_created: bool
    status: str
    detected_relation_family: str | None
    field_mappings: tuple[LegacyFieldMapping, ...]
    required_external_context: tuple[str, ...]
    information_loss: tuple[str, ...]
    warnings: tuple[str, ...]
    unsupported_reasons: tuple[str, ...]

    def __post_init__(self) -> None:
        allowed = {
            "convertible_delayed_response_pending_context",
            "unsupported_legacy_artifact",
            "invalid_legacy_artifact",
        }
        if self.status not in allowed:
            raise ValueError(f"unsupported migration assessment status: {self.status}")
        if self.target_artifact_created:
            raise ValueError("TASK-032A migration assessment cannot create a target artifact")

    @property
    def assessment_id(self) -> str:
        from hashlib import sha256
        import json

        payload = json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        return sha256(payload.encode("utf-8")).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        return {
            "adapter_version": self.adapter_version,
            "source_schema_identifier": self.source_schema_identifier,
            "source_artifact_type": self.source_artifact_type,
            "source_sha256": self.source_sha256,
            "target_schema_version": self.target_schema_version,
            "target_artifact_type": self.target_artifact_type,
            "target_artifact_created": self.target_artifact_created,
            "status": self.status,
            "detected_relation_family": self.detected_relation_family,
            "field_mappings": [item.to_dict() for item in self.field_mappings],
            "required_external_context": list(self.required_external_context),
            "information_loss": list(self.information_loss),
            "warnings": list(self.warnings),
            "unsupported_reasons": list(self.unsupported_reasons),
        }


JsonObject = Mapping[str, Any]
