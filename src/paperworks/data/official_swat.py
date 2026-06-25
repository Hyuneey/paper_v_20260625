"""Official SWaT provenance manifest helpers for DEC-007 resolution."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path, PurePosixPath
from typing import Any, Mapping

from paperworks.data.contracts import SCHEMA_VERSION, stable_hash
from paperworks.data.files import sha256_file


class OfficialSwatManifestError(ValueError):
    """Raised when an official SWaT provenance manifest is incomplete or unsafe."""


def _validate_relative_path(path: str) -> None:
    parsed = PurePosixPath(path.replace("\\", "/"))
    if parsed.is_absolute() or ".." in parsed.parts:
        raise OfficialSwatManifestError(f"path must be relative and stay within SWAT_DATA_ROOT: {path}")


@dataclass(frozen=True)
class OfficialSwatFileRecord:
    logical_role: str
    relative_path: str
    sha256: str
    bytes: int
    rows_excluding_header: int | None = None
    file_version_note: str = "pending_manual_confirmation"

    def __post_init__(self) -> None:
        if not self.logical_role:
            raise OfficialSwatManifestError("logical_role is required")
        _validate_relative_path(self.relative_path)
        if len(self.sha256) != 64:
            raise OfficialSwatManifestError("sha256 must be a 64-character hash")
        if self.bytes < 0:
            raise OfficialSwatManifestError("bytes must be non-negative")
        if self.rows_excluding_header is not None and self.rows_excluding_header < 0:
            raise OfficialSwatManifestError("rows_excluding_header must be non-negative")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "OfficialSwatFileRecord":
        return cls(
            logical_role=str(data["logical_role"]),
            relative_path=str(data["relative_path"]),
            sha256=str(data["sha256"]),
            bytes=int(data["bytes"]),
            rows_excluding_header=data.get("rows_excluding_header"),
            file_version_note=str(data.get("file_version_note", "pending_manual_confirmation")),
        )


@dataclass(frozen=True)
class OfficialSwatProvenanceManifest:
    dataset_name: str = "SWaT"
    source_route: str = "official_iTrust_request"
    request_record_reference: str = "pending"
    approval_record_reference: str = "pending"
    terms_acknowledged: bool = False
    terms_acknowledged_by: str = "pending"
    terms_acknowledged_date: str = "pending"
    terms_source_url: str = "pending"
    required_credit_statement: str = "pending"
    no_sharing_acknowledged: bool = False
    publication_notification_acknowledged: bool = False
    dataset_edition: str = "pending"
    dataset_version: str = "pending"
    files: tuple[OfficialSwatFileRecord, ...] = field(default_factory=tuple)
    split_protocol_frozen: bool = False
    metric_protocol_frozen: bool = False
    sealed_test_access_policy_approved: bool = False
    git_artifact_policy_approved: bool = False
    final_test_opened: bool = False
    schema_version: str = SCHEMA_VERSION
    artifact_type: str = "official_swat_provenance_manifest"

    def __post_init__(self) -> None:
        if self.dataset_name != "SWaT":
            raise OfficialSwatManifestError("dataset_name must be SWaT")
        if self.source_route != "official_iTrust_request":
            raise OfficialSwatManifestError("DEC-007 final primary benchmark requires official_iTrust_request")
        if self.final_test_opened:
            raise OfficialSwatManifestError("TASK-015 does not approve final test access")
        if self.schema_version != SCHEMA_VERSION:
            raise OfficialSwatManifestError(f"unsupported schema_version: {self.schema_version}")

    @property
    def manifest_id(self) -> str:
        return stable_hash(self.to_dict())

    @property
    def dec007_resolution_ready(self) -> bool:
        return not self.resolution_blockers()

    def resolution_blockers(self) -> tuple[str, ...]:
        blockers: list[str] = []
        if self.source_route != "official_iTrust_request":
            blockers.append("official_source_not_selected")
        if self.request_record_reference == "pending":
            blockers.append("request_record_missing")
        if self.approval_record_reference == "pending":
            blockers.append("approval_record_missing")
        if not self.terms_acknowledged:
            blockers.append("terms_not_acknowledged")
        if self.terms_acknowledged_by == "pending" or self.terms_acknowledged_date == "pending":
            blockers.append("terms_acknowledgement_metadata_missing")
        if self.terms_source_url == "pending" or not self.terms_source_url:
            blockers.append("terms_source_url_missing")
        if self.required_credit_statement == "pending" or not self.required_credit_statement:
            blockers.append("required_credit_statement_missing")
        if not self.no_sharing_acknowledged:
            blockers.append("no_sharing_not_acknowledged")
        if not self.publication_notification_acknowledged:
            blockers.append("publication_notification_not_acknowledged")
        if self.dataset_edition == "pending" or self.dataset_version == "pending":
            blockers.append("dataset_edition_or_version_missing")
        if not self.files:
            blockers.append("approved_file_records_missing")
        if not self.split_protocol_frozen:
            blockers.append("split_protocol_not_frozen")
        if not self.metric_protocol_frozen:
            blockers.append("metric_protocol_not_frozen")
        if not self.sealed_test_access_policy_approved:
            blockers.append("sealed_test_access_policy_not_approved")
        if not self.git_artifact_policy_approved:
            blockers.append("git_artifact_policy_not_approved")
        return tuple(blockers)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "artifact_type": self.artifact_type,
            "dataset_name": self.dataset_name,
            "source_route": self.source_route,
            "request_record_reference": self.request_record_reference,
            "approval_record_reference": self.approval_record_reference,
            "terms_acknowledged": self.terms_acknowledged,
            "terms_acknowledged_by": self.terms_acknowledged_by,
            "terms_acknowledged_date": self.terms_acknowledged_date,
            "terms_source_url": self.terms_source_url,
            "required_credit_statement": self.required_credit_statement,
            "no_sharing_acknowledged": self.no_sharing_acknowledged,
            "publication_notification_acknowledged": self.publication_notification_acknowledged,
            "dataset_edition": self.dataset_edition,
            "dataset_version": self.dataset_version,
            "files": [file.to_dict() for file in self.files],
            "split_protocol_frozen": self.split_protocol_frozen,
            "metric_protocol_frozen": self.metric_protocol_frozen,
            "sealed_test_access_policy_approved": self.sealed_test_access_policy_approved,
            "git_artifact_policy_approved": self.git_artifact_policy_approved,
            "final_test_opened": self.final_test_opened,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, indent=2)

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "OfficialSwatProvenanceManifest":
        return cls(
            dataset_name=str(data.get("dataset_name", "SWaT")),
            source_route=str(data.get("source_route", "official_iTrust_request")),
            request_record_reference=str(data.get("request_record_reference", "pending")),
            approval_record_reference=str(data.get("approval_record_reference", "pending")),
            terms_acknowledged=bool(data.get("terms_acknowledged", False)),
            terms_acknowledged_by=str(data.get("terms_acknowledged_by", "pending")),
            terms_acknowledged_date=str(data.get("terms_acknowledged_date", "pending")),
            terms_source_url=str(data.get("terms_source_url", "pending")),
            required_credit_statement=str(data.get("required_credit_statement", "pending")),
            no_sharing_acknowledged=bool(data.get("no_sharing_acknowledged", False)),
            publication_notification_acknowledged=bool(data.get("publication_notification_acknowledged", False)),
            dataset_edition=str(data.get("dataset_edition", "pending")),
            dataset_version=str(data.get("dataset_version", "pending")),
            files=tuple(OfficialSwatFileRecord.from_dict(item) for item in data.get("files", ())),
            split_protocol_frozen=bool(data.get("split_protocol_frozen", False)),
            metric_protocol_frozen=bool(data.get("metric_protocol_frozen", False)),
            sealed_test_access_policy_approved=bool(data.get("sealed_test_access_policy_approved", False)),
            git_artifact_policy_approved=bool(data.get("git_artifact_policy_approved", False)),
            final_test_opened=bool(data.get("final_test_opened", False)),
            schema_version=str(data.get("schema_version", SCHEMA_VERSION)),
            artifact_type=str(data.get("artifact_type", "official_swat_provenance_manifest")),
        )

    @classmethod
    def from_json(cls, text: str) -> "OfficialSwatProvenanceManifest":
        return cls.from_dict(json.loads(text))


def hash_approved_swat_file(path: Path) -> str:
    if not path.exists() or not path.is_file():
        raise OfficialSwatManifestError(f"approved file does not exist: {path}")
    return sha256_file(path)


def build_official_swat_file_record(
    *,
    root: Path,
    relative_path: str,
    logical_role: str,
    rows_excluding_header: int | None = None,
    file_version_note: str = "pending_manual_confirmation",
) -> OfficialSwatFileRecord:
    _validate_relative_path(relative_path)
    path = root / relative_path
    if not path.exists() or not path.is_file():
        raise OfficialSwatManifestError(f"approved file does not exist: {relative_path}")
    return OfficialSwatFileRecord(
        logical_role=logical_role,
        relative_path=relative_path,
        sha256=hash_approved_swat_file(path),
        bytes=path.stat().st_size,
        rows_excluding_header=rows_excluding_header,
        file_version_note=file_version_note,
    )
