"""Bounded, dataset-neutral provenance audit for the official HAI 23.05 source.

The module deliberately separates public structural metadata from private label
custody. It never computes feature-value statistics and never emits attack
intervals or targets into public artifacts.
"""

from __future__ import annotations

import ast
import csv
import json
import math
import re
import shutil
import subprocess
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from hashlib import sha256
from pathlib import Path, PurePosixPath
from typing import Any, Mapping, Sequence

from paperworks.data.contracts_v2 import (
    CompressionTypeV2,
    CreationMetadataV2,
    DatasetFileV2,
    DatasetManifestV2,
    LabelAvailabilityV2,
    LabelSpecificationV2,
    ProvenanceStatusV2,
    TimestampSpecificationV2,
)


HAI_PROVENANCE_SCHEMA_VERSION = "1.0.0"
LFS_POINTER_VERSION = "https://git-lfs.github.com/spec/v1"
_SHA256 = re.compile(r"^[a-f0-9]{64}$")
_COMMIT = re.compile(r"^[a-f0-9]{40}$")
_SAFE_RELATIVE_ROOT = "hai-23.05"
_TIMESTAMP_NAMES = frozenset({"timestamp", "time", "datetime", "date_time"})
_LABEL_NAMES = frozenset({"label", "attack", "anomaly", "is_attack"})
_NORMAL_LABEL_VALUES = frozenset({"", "0", "0.0", "false", "normal"})
_BINARY_LABEL_VALUES = frozenset({"0", "0.0", "1", "1.0", "false", "true"})


class HAIProvenanceError(ValueError):
    """Raised when a HAI provenance or custody contract fails closed."""


def _canonical_json(value: Mapping[str, Any]) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    )


def canonical_self_hash(value: Mapping[str, Any], field_name: str) -> str:
    """Hash a mapping after excluding its designated self-hash field."""

    payload = dict(value)
    payload.pop(field_name, None)
    return sha256(_canonical_json(payload).encode("utf-8")).hexdigest()


def _require_hash(value: str, field_name: str) -> str:
    if _SHA256.fullmatch(value) is None:
        raise HAIProvenanceError(f"{field_name} must be a lowercase SHA-256")
    return value


def _require_commit(value: str, field_name: str) -> str:
    if _COMMIT.fullmatch(value) is None:
        raise HAIProvenanceError(f"{field_name} must be a full lowercase Git commit")
    return value


def _require_relative_source_path(value: str) -> str:
    if not value or "\\" in value or re.match(r"^[A-Za-z]:", value):
        raise HAIProvenanceError("source path must be a POSIX relative path")
    parsed = PurePosixPath(value)
    if parsed.is_absolute() or ".." in parsed.parts or "." in parsed.parts:
        raise HAIProvenanceError("source path must remain relative")
    return value


def _require_hai2305_path(value: str) -> str:
    _require_relative_source_path(value)
    if not value.startswith(f"{_SAFE_RELATIVE_ROOT}/"):
        raise HAIProvenanceError("HAI 23.05 record cannot reference another dataset directory")
    if value.lower().startswith("haiend-"):
        raise HAIProvenanceError("HAIEnd is excluded from the HAI 23.05 audit")
    return value


def _artifact_dict(content: Mapping[str, Any]) -> dict[str, Any]:
    result = dict(content)
    result["artifact_hash"] = sha256(
        _canonical_json(content).encode("utf-8")
    ).hexdigest()
    return result


def _verify_serialized_hash(data: Mapping[str, Any], content: Mapping[str, Any]) -> None:
    supplied = data.get("artifact_hash")
    observed = sha256(_canonical_json(content).encode("utf-8")).hexdigest()
    if supplied is not None and supplied != observed:
        raise HAIProvenanceError("artifact_hash does not match artifact content")


def streaming_sha256(path: Path, *, chunk_size: int = 1024 * 1024) -> str:
    """Return a file SHA-256 without loading the file into memory."""

    if chunk_size <= 0:
        raise HAIProvenanceError("chunk_size must be positive")
    digest = sha256()
    with path.open("rb") as stream:
        while True:
            block = stream.read(chunk_size)
            if not block:
                break
            digest.update(block)
    return digest.hexdigest()


@dataclass(frozen=True)
class HAILfsPointerRecordV1:
    relative_path: str
    pointer_oid_sha256: str
    pointer_size_bytes: int
    expected_oid_sha256: str
    expected_size_bytes: int
    materialized_sha256: str
    materialized_size_bytes: int
    pointer_matches_expected: bool
    materialized_matches_pointer: bool
    materialized: bool
    schema_version: str = HAI_PROVENANCE_SCHEMA_VERSION
    artifact_type: str = "hai_lfs_pointer_record"

    def __post_init__(self) -> None:
        _require_hai2305_path(self.relative_path)
        for name in (
            "pointer_oid_sha256",
            "expected_oid_sha256",
            "materialized_sha256",
        ):
            _require_hash(getattr(self, name), name)
        if min(
            self.pointer_size_bytes,
            self.expected_size_bytes,
            self.materialized_size_bytes,
        ) < 0:
            raise HAIProvenanceError("LFS sizes must be non-negative")
        if self.schema_version != HAI_PROVENANCE_SCHEMA_VERSION:
            raise HAIProvenanceError("unsupported HAI provenance schema version")
        if self.artifact_type != "hai_lfs_pointer_record":
            raise HAIProvenanceError("invalid LFS pointer artifact type")
        if self.materialized and not self.materialized_matches_pointer:
            raise HAIProvenanceError("materialized status requires exact pointer binding")

    def _content_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "artifact_type": self.artifact_type,
            "relative_path": self.relative_path,
            "pointer_oid_sha256": self.pointer_oid_sha256,
            "pointer_size_bytes": self.pointer_size_bytes,
            "expected_oid_sha256": self.expected_oid_sha256,
            "expected_size_bytes": self.expected_size_bytes,
            "materialized_sha256": self.materialized_sha256,
            "materialized_size_bytes": self.materialized_size_bytes,
            "pointer_matches_expected": self.pointer_matches_expected,
            "materialized_matches_pointer": self.materialized_matches_pointer,
            "materialized": self.materialized,
        }

    @property
    def artifact_hash(self) -> str:
        return _artifact_dict(self._content_dict())["artifact_hash"]

    def to_dict(self) -> dict[str, Any]:
        return _artifact_dict(self._content_dict())

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "HAILfsPointerRecordV1":
        result = cls(
            relative_path=str(data["relative_path"]),
            pointer_oid_sha256=str(data["pointer_oid_sha256"]),
            pointer_size_bytes=int(data["pointer_size_bytes"]),
            expected_oid_sha256=str(data["expected_oid_sha256"]),
            expected_size_bytes=int(data["expected_size_bytes"]),
            materialized_sha256=str(data["materialized_sha256"]),
            materialized_size_bytes=int(data["materialized_size_bytes"]),
            pointer_matches_expected=data["pointer_matches_expected"] is True,
            materialized_matches_pointer=(
                data["materialized_matches_pointer"] is True
            ),
            materialized=data["materialized"] is True,
            schema_version=str(data.get("schema_version", HAI_PROVENANCE_SCHEMA_VERSION)),
            artifact_type=str(data.get("artifact_type", "hai_lfs_pointer_record")),
        )
        _verify_serialized_hash(data, result._content_dict())
        return result


@dataclass(frozen=True)
class HAIRepositorySnapshotV1:
    repository_url: str
    snapshot_commit: str
    introduction_commit: str
    observed_head: str
    tree_sha: str
    observed_origin_url: str
    detached_head: bool
    checkout_clean: bool
    git_fsck_passed: bool
    git_lfs_fsck_passed: bool
    lfs_available: bool
    readme_blob_sha: str
    technical_manual_blob_sha: str
    standalone_license_present: bool
    license_source: str
    license_statement: str
    warning_codes: tuple[str, ...]
    schema_version: str = HAI_PROVENANCE_SCHEMA_VERSION
    artifact_type: str = "hai_repository_snapshot"

    def __post_init__(self) -> None:
        if self.schema_version != HAI_PROVENANCE_SCHEMA_VERSION:
            raise HAIProvenanceError("unsupported repository snapshot schema version")
        if self.artifact_type != "hai_repository_snapshot":
            raise HAIProvenanceError("invalid repository snapshot artifact type")
        for name in ("snapshot_commit", "introduction_commit", "observed_head"):
            _require_commit(getattr(self, name), name)
        if not re.fullmatch(r"[a-f0-9]{40,64}", self.tree_sha):
            raise HAIProvenanceError("tree_sha must be a full Git object ID")
        for name in ("readme_blob_sha", "technical_manual_blob_sha"):
            if not re.fullmatch(r"[a-f0-9]{40,64}", getattr(self, name)):
                raise HAIProvenanceError(f"{name} must be a Git blob ID")
        if not self.repository_url or not self.observed_origin_url:
            raise HAIProvenanceError("repository URLs are required")
        if not self.license_source or not self.license_statement:
            raise HAIProvenanceError("license source and statement are required")
        if len(set(self.warning_codes)) != len(self.warning_codes):
            raise HAIProvenanceError("warning codes must be unique")

    def _content_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "artifact_type": self.artifact_type,
            "repository_url": self.repository_url,
            "snapshot_commit": self.snapshot_commit,
            "introduction_commit": self.introduction_commit,
            "observed_head": self.observed_head,
            "tree_sha": self.tree_sha,
            "observed_origin_url": self.observed_origin_url,
            "detached_head": self.detached_head,
            "checkout_clean": self.checkout_clean,
            "git_fsck_passed": self.git_fsck_passed,
            "git_lfs_fsck_passed": self.git_lfs_fsck_passed,
            "lfs_available": self.lfs_available,
            "readme_blob_sha": self.readme_blob_sha,
            "technical_manual_blob_sha": self.technical_manual_blob_sha,
            "standalone_license_present": self.standalone_license_present,
            "license_source": self.license_source,
            "license_statement": self.license_statement,
            "warning_codes": list(self.warning_codes),
        }

    @property
    def artifact_hash(self) -> str:
        return _artifact_dict(self._content_dict())["artifact_hash"]

    def to_dict(self) -> dict[str, Any]:
        return _artifact_dict(self._content_dict())


@dataclass(frozen=True)
class HAICsvStructureAuditV1:
    relative_path: str
    file_sha256: str
    byte_size: int
    utf_encoding_result: str
    delimiter: str
    header_field_count: int
    header_sha256: str
    timestamp_field: str
    row_count: int
    first_timestamp: str | None
    last_timestamp: str | None
    timestamps_strictly_increasing: bool
    duplicate_timestamp_count: int
    non_positive_timestamp_delta_count: int
    nominal_timestamp_delta_seconds: float | None
    distinct_timestamp_delta_seconds: tuple[float, ...]
    timestamp_delta_summary_truncated: bool
    malformed_row_count: int
    inconsistent_field_count_rows: int
    empty_field_count: int
    ordered_header_matches_canonical: bool
    expected_point_count_reconciled: bool
    normal_file_status: str | None
    test_file_structural_only: bool
    process_ids_observed: tuple[str, ...]
    schema_version: str = HAI_PROVENANCE_SCHEMA_VERSION
    artifact_type: str = "hai_csv_structure_audit"

    def __post_init__(self) -> None:
        if self.schema_version != HAI_PROVENANCE_SCHEMA_VERSION:
            raise HAIProvenanceError("unsupported CSV audit schema version")
        if self.artifact_type != "hai_csv_structure_audit":
            raise HAIProvenanceError("invalid CSV audit artifact type")
        _require_hai2305_path(self.relative_path)
        _require_hash(self.file_sha256, "file_sha256")
        _require_hash(self.header_sha256, "header_sha256")
        if not self.delimiter or len(self.delimiter) != 1:
            raise HAIProvenanceError("delimiter must be exactly one character")
        integer_fields = (
            self.byte_size,
            self.header_field_count,
            self.row_count,
            self.duplicate_timestamp_count,
            self.non_positive_timestamp_delta_count,
            self.malformed_row_count,
            self.inconsistent_field_count_rows,
            self.empty_field_count,
        )
        if min(integer_fields) < 0:
            raise HAIProvenanceError("CSV structural counts must be non-negative")
        if self.nominal_timestamp_delta_seconds is not None and (
            not math.isfinite(self.nominal_timestamp_delta_seconds)
            or self.nominal_timestamp_delta_seconds <= 0
        ):
            raise HAIProvenanceError("nominal timestamp delta must be positive")
        if any(not math.isfinite(item) for item in self.distinct_timestamp_delta_seconds):
            raise HAIProvenanceError("timestamp deltas must be finite")
        if self.normal_file_status not in {
            None,
            "normal_only_verified",
            "normal_status_unverifiable",
            "unexpected_attack_label_present",
        }:
            raise HAIProvenanceError("invalid normal file status")
        if self.test_file_structural_only and self.normal_file_status is not None:
            raise HAIProvenanceError("test structural audit cannot expose normal-file status")
        if len(set(self.process_ids_observed)) != len(self.process_ids_observed):
            raise HAIProvenanceError("observed process IDs must be unique")

    def _content_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "artifact_type": self.artifact_type,
            "relative_path": self.relative_path,
            "file_sha256": self.file_sha256,
            "byte_size": self.byte_size,
            "utf_encoding_result": self.utf_encoding_result,
            "delimiter": self.delimiter,
            "header_field_count": self.header_field_count,
            "header_sha256": self.header_sha256,
            "timestamp_field": self.timestamp_field,
            "row_count": self.row_count,
            "first_timestamp": self.first_timestamp,
            "last_timestamp": self.last_timestamp,
            "timestamps_strictly_increasing": self.timestamps_strictly_increasing,
            "duplicate_timestamp_count": self.duplicate_timestamp_count,
            "non_positive_timestamp_delta_count": (
                self.non_positive_timestamp_delta_count
            ),
            "nominal_timestamp_delta_seconds": self.nominal_timestamp_delta_seconds,
            "distinct_timestamp_delta_seconds": list(
                self.distinct_timestamp_delta_seconds
            ),
            "timestamp_delta_summary_truncated": (
                self.timestamp_delta_summary_truncated
            ),
            "malformed_row_count": self.malformed_row_count,
            "inconsistent_field_count_rows": self.inconsistent_field_count_rows,
            "empty_field_count": self.empty_field_count,
            "ordered_header_matches_canonical": self.ordered_header_matches_canonical,
            "expected_point_count_reconciled": self.expected_point_count_reconciled,
            "normal_file_status": self.normal_file_status,
            "test_file_structural_only": self.test_file_structural_only,
            "process_ids_observed": list(self.process_ids_observed),
        }

    @property
    def artifact_hash(self) -> str:
        return _artifact_dict(self._content_dict())["artifact_hash"]

    def to_dict(self) -> dict[str, Any]:
        return _artifact_dict(self._content_dict())

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "HAICsvStructureAuditV1":
        result = cls(
            relative_path=str(data["relative_path"]),
            file_sha256=str(data["file_sha256"]),
            byte_size=int(data["byte_size"]),
            utf_encoding_result=str(data["utf_encoding_result"]),
            delimiter=str(data["delimiter"]),
            header_field_count=int(data["header_field_count"]),
            header_sha256=str(data["header_sha256"]),
            timestamp_field=str(data["timestamp_field"]),
            row_count=int(data["row_count"]),
            first_timestamp=data.get("first_timestamp"),
            last_timestamp=data.get("last_timestamp"),
            timestamps_strictly_increasing=(
                data["timestamps_strictly_increasing"] is True
            ),
            duplicate_timestamp_count=int(data["duplicate_timestamp_count"]),
            non_positive_timestamp_delta_count=int(
                data["non_positive_timestamp_delta_count"]
            ),
            nominal_timestamp_delta_seconds=data.get(
                "nominal_timestamp_delta_seconds"
            ),
            distinct_timestamp_delta_seconds=tuple(
                float(item) for item in data["distinct_timestamp_delta_seconds"]
            ),
            timestamp_delta_summary_truncated=(
                data["timestamp_delta_summary_truncated"] is True
            ),
            malformed_row_count=int(data["malformed_row_count"]),
            inconsistent_field_count_rows=int(data["inconsistent_field_count_rows"]),
            empty_field_count=int(data["empty_field_count"]),
            ordered_header_matches_canonical=(
                data["ordered_header_matches_canonical"] is True
            ),
            expected_point_count_reconciled=(
                data["expected_point_count_reconciled"] is True
            ),
            normal_file_status=data.get("normal_file_status"),
            test_file_structural_only=data["test_file_structural_only"] is True,
            process_ids_observed=tuple(str(item) for item in data["process_ids_observed"]),
            schema_version=str(data.get("schema_version", HAI_PROVENANCE_SCHEMA_VERSION)),
            artifact_type=str(data.get("artifact_type", "hai_csv_structure_audit")),
        )
        _verify_serialized_hash(data, result._content_dict())
        return result


@dataclass(frozen=True)
class HAILabelCustodyPublicRecordV1:
    label_relative_path: str
    label_file_sha256: str
    label_byte_size: int
    label_header_sha256: str
    label_row_count: int
    timestamp_alignment_status: str
    label_domain_valid: bool
    summary_relative_path: str
    summary_file_sha256: str
    summary_byte_size: int
    summary_format_valid: bool
    event_record_count: int
    expected_event_record_count: int
    custody_status: str
    private_custody_artifact_hash: str
    label_content_accessed_for_provenance_only: bool
    label_content_used_for_scientific_selection: bool
    attack_event_details_publicly_exposed: bool
    schema_version: str = HAI_PROVENANCE_SCHEMA_VERSION
    artifact_type: str = "hai_label_custody_public"

    def __post_init__(self) -> None:
        if self.schema_version != HAI_PROVENANCE_SCHEMA_VERSION:
            raise HAIProvenanceError("unsupported label custody schema version")
        if self.artifact_type != "hai_label_custody_public":
            raise HAIProvenanceError("invalid label custody artifact type")
        for value in (self.label_relative_path, self.summary_relative_path):
            _require_hai2305_path(value)
        for name in (
            "label_file_sha256",
            "label_header_sha256",
            "summary_file_sha256",
            "private_custody_artifact_hash",
        ):
            _require_hash(getattr(self, name), name)
        if min(
            self.label_byte_size,
            self.label_row_count,
            self.summary_byte_size,
            self.event_record_count,
            self.expected_event_record_count,
        ) < 0:
            raise HAIProvenanceError("label custody counts must be non-negative")
        if self.label_content_accessed_for_provenance_only is not True:
            raise HAIProvenanceError("label access must be provenance-only")
        if self.label_content_used_for_scientific_selection is not False:
            raise HAIProvenanceError("label content cannot be used for selection")
        if self.attack_event_details_publicly_exposed is not False:
            raise HAIProvenanceError("public attack event details are prohibited")
        if self.custody_status == "verified" and not (
            self.timestamp_alignment_status == "aligned"
            and self.label_domain_valid
            and self.summary_format_valid
            and self.event_record_count == self.expected_event_record_count
        ):
            raise HAIProvenanceError("verified custody requires all public checks")

    def _content_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "artifact_type": self.artifact_type,
            "label_relative_path": self.label_relative_path,
            "label_file_sha256": self.label_file_sha256,
            "label_byte_size": self.label_byte_size,
            "label_header_sha256": self.label_header_sha256,
            "label_row_count": self.label_row_count,
            "timestamp_alignment_status": self.timestamp_alignment_status,
            "label_domain_valid": self.label_domain_valid,
            "summary_relative_path": self.summary_relative_path,
            "summary_file_sha256": self.summary_file_sha256,
            "summary_byte_size": self.summary_byte_size,
            "summary_format_valid": self.summary_format_valid,
            "event_record_count": self.event_record_count,
            "expected_event_record_count": self.expected_event_record_count,
            "custody_status": self.custody_status,
            "private_custody_artifact_hash": self.private_custody_artifact_hash,
            "label_content_accessed_for_provenance_only": (
                self.label_content_accessed_for_provenance_only
            ),
            "label_content_used_for_scientific_selection": (
                self.label_content_used_for_scientific_selection
            ),
            "attack_event_details_publicly_exposed": (
                self.attack_event_details_publicly_exposed
            ),
        }

    @property
    def artifact_hash(self) -> str:
        return _artifact_dict(self._content_dict())["artifact_hash"]

    def to_dict(self) -> dict[str, Any]:
        return _artifact_dict(self._content_dict())


@dataclass(frozen=True)
class HAIReferenceFileRecordV1:
    relative_path: str
    reference_kind: str
    git_blob_sha: str
    content_sha256: str
    byte_size: int
    file_type_valid: bool
    page_count: int | None
    title: str | None
    version_metadata: str | None
    hai_2305_coverage: str
    variable_descriptions_available: str
    process_information_available: str
    extraction_method: str
    extraction_tool_version: str | None
    extraction_status: str
    schema_version: str = HAI_PROVENANCE_SCHEMA_VERSION
    artifact_type: str = "hai_reference_file_record"

    def __post_init__(self) -> None:
        if self.schema_version != HAI_PROVENANCE_SCHEMA_VERSION:
            raise HAIProvenanceError("unsupported reference record schema version")
        if self.artifact_type != "hai_reference_file_record":
            raise HAIProvenanceError("invalid reference record artifact type")
        _require_relative_source_path(self.relative_path)
        if not re.fullmatch(r"[a-f0-9]{40,64}", self.git_blob_sha):
            raise HAIProvenanceError("git_blob_sha must be a Git object ID")
        _require_hash(self.content_sha256, "content_sha256")
        if self.byte_size < 0 or (self.page_count is not None and self.page_count < 0):
            raise HAIProvenanceError("reference sizes and page counts must be non-negative")

    def _content_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "artifact_type": self.artifact_type,
            "relative_path": self.relative_path,
            "reference_kind": self.reference_kind,
            "git_blob_sha": self.git_blob_sha,
            "content_sha256": self.content_sha256,
            "byte_size": self.byte_size,
            "file_type_valid": self.file_type_valid,
            "page_count": self.page_count,
            "title": self.title,
            "version_metadata": self.version_metadata,
            "hai_2305_coverage": self.hai_2305_coverage,
            "variable_descriptions_available": self.variable_descriptions_available,
            "process_information_available": self.process_information_available,
            "extraction_method": self.extraction_method,
            "extraction_tool_version": self.extraction_tool_version,
            "extraction_status": self.extraction_status,
        }

    @property
    def artifact_hash(self) -> str:
        return _artifact_dict(self._content_dict())["artifact_hash"]

    def to_dict(self) -> dict[str, Any]:
        return _artifact_dict(self._content_dict())


@dataclass(frozen=True)
class HAIGraphInventoryRecordV1:
    relative_path: str
    git_blob_sha: str
    content_sha256: str
    byte_size: int
    extension: str
    strict_json_parse_status: str
    python_literal_parse_status: str
    directed: bool | None
    multigraph: bool | None
    node_count: int | None
    edge_count: int | None
    apparent_process_coverage: tuple[str, ...]
    reference_kind: str
    scientific_claim_boundary: str
    schema_version: str = HAI_PROVENANCE_SCHEMA_VERSION
    artifact_type: str = "hai_graph_inventory_record"

    def __post_init__(self) -> None:
        if self.schema_version != HAI_PROVENANCE_SCHEMA_VERSION:
            raise HAIProvenanceError("unsupported graph inventory schema version")
        if self.artifact_type != "hai_graph_inventory_record":
            raise HAIProvenanceError("invalid graph inventory artifact type")
        _require_relative_source_path(self.relative_path)
        if not re.fullmatch(r"[a-f0-9]{40,64}", self.git_blob_sha):
            raise HAIProvenanceError("git_blob_sha must be a Git object ID")
        _require_hash(self.content_sha256, "content_sha256")
        if self.byte_size < 0:
            raise HAIProvenanceError("graph byte size must be non-negative")
        for count in (self.node_count, self.edge_count):
            if count is not None and count < 0:
                raise HAIProvenanceError("graph counts must be non-negative")
        if len(set(self.apparent_process_coverage)) != len(
            self.apparent_process_coverage
        ):
            raise HAIProvenanceError("process coverage must be unique")

    def _content_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "artifact_type": self.artifact_type,
            "relative_path": self.relative_path,
            "git_blob_sha": self.git_blob_sha,
            "content_sha256": self.content_sha256,
            "byte_size": self.byte_size,
            "extension": self.extension,
            "strict_json_parse_status": self.strict_json_parse_status,
            "python_literal_parse_status": self.python_literal_parse_status,
            "directed": self.directed,
            "multigraph": self.multigraph,
            "node_count": self.node_count,
            "edge_count": self.edge_count,
            "apparent_process_coverage": list(self.apparent_process_coverage),
            "reference_kind": self.reference_kind,
            "scientific_claim_boundary": self.scientific_claim_boundary,
        }

    @property
    def artifact_hash(self) -> str:
        return _artifact_dict(self._content_dict())["artifact_hash"]

    def to_dict(self) -> dict[str, Any]:
        return _artifact_dict(self._content_dict())


@dataclass(frozen=True)
class HAIProvenanceAuditResultV1:
    task_id: str
    status: str
    execution_code_commit: str
    repository_snapshot: HAIRepositorySnapshotV1
    lfs_records: tuple[HAILfsPointerRecordV1, ...]
    csv_records: tuple[HAICsvStructureAuditV1, ...]
    label_custody_records: tuple[HAILabelCustodyPublicRecordV1, ...]
    reference_records: tuple[HAIReferenceFileRecordV1, ...]
    graph_records: tuple[HAIGraphInventoryRecordV1, ...]
    dataset_manifest_id: str | None
    mandatory_gates: Mapping[str, bool]
    boundary: Mapping[str, Any]
    created_at: str
    schema_version: str = HAI_PROVENANCE_SCHEMA_VERSION
    artifact_type: str = "hai_provenance_audit_result"

    def __post_init__(self) -> None:
        if self.schema_version != HAI_PROVENANCE_SCHEMA_VERSION:
            raise HAIProvenanceError("unsupported provenance result schema version")
        if self.artifact_type != "hai_provenance_audit_result":
            raise HAIProvenanceError("invalid provenance result artifact type")
        _require_commit(self.execution_code_commit, "execution_code_commit")
        try:
            datetime.fromisoformat(self.created_at.replace("Z", "+00:00"))
        except ValueError as exc:
            raise HAIProvenanceError("created_at must be ISO 8601") from exc
        if self.dataset_manifest_id is not None:
            _require_hash(self.dataset_manifest_id, "dataset_manifest_id")
        if not self.mandatory_gates or any(
            type(value) is not bool for value in self.mandatory_gates.values()
        ):
            raise HAIProvenanceError("mandatory gates must be named booleans")
        if self.status == "passed_hai_2305_official_provenance_audit" and not all(
            self.mandatory_gates.values()
        ):
            raise HAIProvenanceError("passing status requires all mandatory gates")
        expected_boundary = {
            "label_content_accessed_for_provenance_only": True,
            "label_content_used_for_scientific_selection": False,
            "attack_event_details_publicly_exposed": False,
            "test_file_feature_statistics_computed": False,
            "process_selected": False,
            "scientific_split_created": False,
            "detector_executed": False,
            "rule_constructed_or_executed": False,
            "outer_or_sealed_scientific_access": False,
            "absolute_local_paths_public": False,
        }
        if dict(self.boundary) != expected_boundary:
            raise HAIProvenanceError("provenance result boundary is not fail-closed")

    def _content_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "artifact_type": self.artifact_type,
            "task_id": self.task_id,
            "status": self.status,
            "execution_code_commit": self.execution_code_commit,
            "repository_snapshot": self.repository_snapshot.to_dict(),
            "lfs_records": [item.to_dict() for item in self.lfs_records],
            "csv_records": [item.to_dict() for item in self.csv_records],
            "label_custody_records": [
                item.to_dict() for item in self.label_custody_records
            ],
            "reference_records": [item.to_dict() for item in self.reference_records],
            "graph_records": [item.to_dict() for item in self.graph_records],
            "dataset_manifest_id": self.dataset_manifest_id,
            "mandatory_gates": dict(sorted(self.mandatory_gates.items())),
            "boundary": dict(sorted(self.boundary.items())),
            "created_at": self.created_at,
        }

    @property
    def artifact_hash(self) -> str:
        return _artifact_dict(self._content_dict())["artifact_hash"]

    def to_dict(self) -> dict[str, Any]:
        return _artifact_dict(self._content_dict())


def parse_lfs_pointer_text(text: str) -> tuple[str, int]:
    """Parse a canonical three-line Git-LFS pointer."""

    lines = text.splitlines()
    if len(lines) != 3 or lines[0] != f"version {LFS_POINTER_VERSION}":
        raise HAIProvenanceError("invalid Git-LFS pointer version or line count")
    if not lines[1].startswith("oid sha256:") or not lines[2].startswith("size "):
        raise HAIProvenanceError("invalid Git-LFS pointer fields")
    oid = lines[1][len("oid sha256:") :]
    _require_hash(oid, "Git-LFS pointer OID")
    try:
        size = int(lines[2][len("size ") :])
    except ValueError as exc:
        raise HAIProvenanceError("Git-LFS pointer size is invalid") from exc
    if size < 0:
        raise HAIProvenanceError("Git-LFS pointer size is negative")
    return oid, size


def validate_lfs_materialization(
    *,
    relative_path: str,
    pointer_text: str,
    materialized_path: Path,
    expected_oid_sha256: str,
    expected_size_bytes: int,
) -> HAILfsPointerRecordV1:
    """Bind expected Git-LFS pointer metadata to one materialized file."""

    pointer_oid, pointer_size = parse_lfs_pointer_text(pointer_text)
    if not materialized_path.is_file():
        raise HAIProvenanceError(f"materialized file is missing: {relative_path}")
    materialized_size = materialized_path.stat().st_size
    materialized_hash = streaming_sha256(materialized_path)
    is_pointer_text = materialized_size < 1024 and materialized_hash != pointer_oid
    return HAILfsPointerRecordV1(
        relative_path=relative_path,
        pointer_oid_sha256=pointer_oid,
        pointer_size_bytes=pointer_size,
        expected_oid_sha256=expected_oid_sha256,
        expected_size_bytes=expected_size_bytes,
        materialized_sha256=materialized_hash,
        materialized_size_bytes=materialized_size,
        pointer_matches_expected=(
            pointer_oid == expected_oid_sha256
            and pointer_size == expected_size_bytes
        ),
        materialized_matches_pointer=(
            materialized_hash == pointer_oid and materialized_size == pointer_size
        ),
        materialized=not is_pointer_text and (
            materialized_hash == pointer_oid and materialized_size == pointer_size
        ),
    )


def _parse_timestamp(value: str) -> datetime:
    normalized = value.strip()
    if normalized.endswith("Z"):
        normalized = normalized[:-1] + "+00:00"
    candidates = (normalized, normalized.replace("/", "-"))
    for candidate in candidates:
        try:
            return datetime.fromisoformat(candidate)
        except ValueError:
            continue
    for fmt in (
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M:%S.%f",
        "%Y/%m/%d %H:%M:%S",
        "%Y/%m/%d %H:%M:%S.%f",
    ):
        try:
            return datetime.strptime(normalized, fmt)
        except ValueError:
            continue
    raise HAIProvenanceError("timestamp value does not match an approved format")


def _discover_timestamp_index(header: Sequence[str]) -> int:
    normalized = [item.strip().lower() for item in header]
    matches = [index for index, item in enumerate(normalized) if item in _TIMESTAMP_NAMES]
    if len(matches) != 1:
        raise HAIProvenanceError("exactly one timestamp field must be discoverable")
    return matches[0]


def _discover_label_indexes(header: Sequence[str]) -> tuple[int, ...]:
    return tuple(
        index
        for index, value in enumerate(header)
        if value.strip().lower() in _LABEL_NAMES
    )


def _discover_process_ids(feature_names: Sequence[str]) -> tuple[str, ...]:
    found: set[str] = set()
    for name in feature_names:
        match = re.match(r"^(P[1-4])(?:_|\b)", name.strip(), re.IGNORECASE)
        if match:
            found.add(match.group(1).upper())
    return tuple(sorted(found))


def _read_header(path: Path) -> tuple[bytes, list[str], str]:
    with path.open("rb") as binary:
        raw_header = binary.readline()
    if not raw_header:
        raise HAIProvenanceError("CSV is empty")
    try:
        decoded = raw_header.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise HAIProvenanceError("CSV header is not UTF-8") from exc
    sample = decoded.rstrip("\r\n")
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
        delimiter = dialect.delimiter
    except csv.Error as exc:
        raise HAIProvenanceError("CSV delimiter cannot be determined") from exc
    header = next(csv.reader([sample], delimiter=delimiter))
    if not header or any(not item for item in header):
        raise HAIProvenanceError("CSV header contains empty field names")
    return raw_header.rstrip(b"\r\n"), header, delimiter


def audit_csv_structure(
    path: Path,
    *,
    relative_path: str,
    expected_point_count: int,
    canonical_header: Sequence[str] | None = None,
    official_train_normal_description_verified: bool = False,
    test_file_structural_only: bool = False,
    maximum_distinct_deltas: int = 64,
) -> HAICsvStructureAuditV1:
    """Stream one time-series CSV and retain structural metadata only."""

    if maximum_distinct_deltas <= 0:
        raise HAIProvenanceError("maximum_distinct_deltas must be positive")
    raw_header, header, delimiter = _read_header(path)
    timestamp_index = _discover_timestamp_index(header)
    label_indexes = _discover_label_indexes(header)
    feature_indexes = tuple(
        index
        for index in range(len(header))
        if index != timestamp_index and index not in label_indexes
    )
    process_ids = _discover_process_ids([header[index] for index in feature_indexes])
    row_count = 0
    malformed = 0
    inconsistent = 0
    empty_fields = 0
    duplicate_timestamps = 0
    non_positive_deltas = 0
    first_timestamp: str | None = None
    last_timestamp: str | None = None
    previous: datetime | None = None
    delta_counts: Counter[float] = Counter()
    delta_summary_truncated = False
    unexpected_train_label = False
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as stream:
            reader = csv.reader(stream, delimiter=delimiter)
            next(reader)
            for row in reader:
                row_count += 1
                if len(row) != len(header):
                    inconsistent += 1
                    continue
                empty_fields += sum(value == "" for value in row)
                try:
                    current = _parse_timestamp(row[timestamp_index])
                except HAIProvenanceError:
                    malformed += 1
                    continue
                if first_timestamp is None:
                    first_timestamp = row[timestamp_index]
                last_timestamp = row[timestamp_index]
                if previous is not None:
                    delta = (current - previous).total_seconds()
                    if delta == 0:
                        duplicate_timestamps += 1
                    if delta <= 0:
                        non_positive_deltas += 1
                    if delta in delta_counts or len(delta_counts) < maximum_distinct_deltas:
                        delta_counts[delta] += 1
                    else:
                        delta_summary_truncated = True
                previous = current
                if not test_file_structural_only:
                    for index in label_indexes:
                        if row[index].strip().lower() not in _NORMAL_LABEL_VALUES:
                            unexpected_train_label = True
    except (UnicodeDecodeError, csv.Error) as exc:
        raise HAIProvenanceError("CSV streaming parse failed") from exc
    if row_count == 0:
        raise HAIProvenanceError("CSV contains no data rows")
    positive_deltas = {
        delta: count for delta, count in delta_counts.items() if delta > 0
    }
    nominal = (
        sorted(positive_deltas.items(), key=lambda item: (-item[1], item[0]))[0][0]
        if positive_deltas
        else None
    )
    normal_status: str | None = None
    if not test_file_structural_only:
        if unexpected_train_label:
            normal_status = "unexpected_attack_label_present"
        elif label_indexes or official_train_normal_description_verified:
            normal_status = "normal_only_verified"
        else:
            normal_status = "normal_status_unverifiable"
    return HAICsvStructureAuditV1(
        relative_path=relative_path,
        file_sha256=streaming_sha256(path),
        byte_size=path.stat().st_size,
        utf_encoding_result="utf-8-valid",
        delimiter=delimiter,
        header_field_count=len(header),
        header_sha256=sha256(raw_header).hexdigest(),
        timestamp_field=header[timestamp_index],
        row_count=row_count,
        first_timestamp=first_timestamp,
        last_timestamp=last_timestamp,
        timestamps_strictly_increasing=(
            malformed == 0 and non_positive_deltas == 0
        ),
        duplicate_timestamp_count=duplicate_timestamps,
        non_positive_timestamp_delta_count=non_positive_deltas,
        nominal_timestamp_delta_seconds=nominal,
        distinct_timestamp_delta_seconds=tuple(sorted(delta_counts)),
        timestamp_delta_summary_truncated=delta_summary_truncated,
        malformed_row_count=malformed,
        inconsistent_field_count_rows=inconsistent,
        empty_field_count=empty_fields,
        ordered_header_matches_canonical=(
            canonical_header is None or tuple(header) == tuple(canonical_header)
        ),
        expected_point_count_reconciled=(
            len(feature_indexes) == expected_point_count
        ),
        normal_file_status=normal_status,
        test_file_structural_only=test_file_structural_only,
        process_ids_observed=process_ids,
    )


def _label_is_positive(value: str) -> bool:
    normalized = value.strip().lower()
    if normalized not in _BINARY_LABEL_VALUES:
        raise HAIProvenanceError("label domain is not binary")
    return normalized in {"1", "1.0", "true"}


def _summary_event_records(text: str) -> tuple[str, ...]:
    """Return private summary records without exposing them through public output."""

    records: list[str] = []
    timestamp_pattern = re.compile(
        r"\d{4}[-/]\d{1,2}[-/]\d{1,2}[^\n]*\d{1,2}:\d{2}:\d{2}"
    )
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith(("#", "-", "=")):
            continue
        if timestamp_pattern.search(line):
            records.append(line)
    return tuple(records)


def audit_label_custody_pair(
    *,
    test_path: Path,
    test_relative_path: str,
    label_path: Path,
    label_relative_path: str,
    summary_path: Path,
    summary_relative_path: str,
    expected_event_count: int,
    private_output_path: Path,
) -> HAILabelCustodyPublicRecordV1:
    """Validate one label/test pair and write event-level custody outside Git."""

    test_raw_header, test_header, test_delimiter = _read_header(test_path)
    del test_raw_header
    label_raw_header, label_header, label_delimiter = _read_header(label_path)
    test_timestamp_index = _discover_timestamp_index(test_header)
    label_timestamp_index = _discover_timestamp_index(label_header)
    label_indexes = tuple(
        index for index in range(len(label_header)) if index != label_timestamp_index
    )
    named_label_indexes = _discover_label_indexes(label_header)
    if len(named_label_indexes) == 1:
        label_index = named_label_indexes[0]
    elif len(label_indexes) == 1:
        label_index = label_indexes[0]
    else:
        raise HAIProvenanceError("label file must expose exactly one label field")

    test_count = 0
    label_count = 0
    aligned = True
    domain_valid = True
    private_events: list[dict[str, str]] = []
    active_start: str | None = None
    active_end: str | None = None
    with test_path.open("r", encoding="utf-8-sig", newline="") as test_stream, (
        label_path.open("r", encoding="utf-8-sig", newline="")
    ) as label_stream:
        test_reader = csv.reader(test_stream, delimiter=test_delimiter)
        label_reader = csv.reader(label_stream, delimiter=label_delimiter)
        next(test_reader)
        next(label_reader)
        for test_row, label_row in zip(test_reader, label_reader):
            test_count += 1
            label_count += 1
            if len(test_row) != len(test_header) or len(label_row) != len(label_header):
                aligned = False
                continue
            test_timestamp = test_row[test_timestamp_index]
            label_timestamp = label_row[label_timestamp_index]
            if test_timestamp != label_timestamp:
                aligned = False
            try:
                positive = _label_is_positive(label_row[label_index])
            except HAIProvenanceError:
                domain_valid = False
                positive = False
            if positive:
                if active_start is None:
                    active_start = label_timestamp
                active_end = label_timestamp
            elif active_start is not None:
                private_events.append({"start": active_start, "end": active_end or active_start})
                active_start = None
                active_end = None
        for _ in test_reader:
            test_count += 1
            aligned = False
        for _ in label_reader:
            label_count += 1
            aligned = False
    if active_start is not None:
        private_events.append({"start": active_start, "end": active_end or active_start})

    try:
        summary_text = summary_path.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError as exc:
        raise HAIProvenanceError("summary label file is not UTF-8") from exc
    summary_records = _summary_event_records(summary_text)
    summary_count = len(summary_records)
    summary_valid = summary_count == expected_event_count
    private_payload = {
        "schema_version": HAI_PROVENANCE_SCHEMA_VERSION,
        "artifact_type": "hai_label_custody_private",
        "test_relative_path": test_relative_path,
        "label_relative_path": label_relative_path,
        "summary_relative_path": summary_relative_path,
        "label_events": private_events,
        "summary_records": list(summary_records),
        "summary_text": summary_text,
        "summary_text_sha256": sha256(summary_text.encode("utf-8")).hexdigest(),
        "label_content_used_for_scientific_selection": False,
    }
    private_payload["artifact_hash"] = canonical_self_hash(
        private_payload, "artifact_hash"
    )
    private_output_path.parent.mkdir(parents=True, exist_ok=True)
    private_output_path.write_text(
        json.dumps(private_payload, sort_keys=True, indent=2, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )
    private_hash = streaming_sha256(private_output_path)
    custody_ok = (
        aligned
        and test_count == label_count
        and domain_valid
        and summary_valid
        and len(private_events) == expected_event_count
    )
    return HAILabelCustodyPublicRecordV1(
        label_relative_path=label_relative_path,
        label_file_sha256=streaming_sha256(label_path),
        label_byte_size=label_path.stat().st_size,
        label_header_sha256=sha256(label_raw_header).hexdigest(),
        label_row_count=label_count,
        timestamp_alignment_status=("aligned" if aligned and test_count == label_count else "misaligned"),
        label_domain_valid=domain_valid,
        summary_relative_path=summary_relative_path,
        summary_file_sha256=streaming_sha256(summary_path),
        summary_byte_size=summary_path.stat().st_size,
        summary_format_valid=summary_valid,
        event_record_count=summary_count,
        expected_event_record_count=expected_event_count,
        custody_status=("verified" if custody_ok else "failed"),
        private_custody_artifact_hash=private_hash,
        label_content_accessed_for_provenance_only=True,
        label_content_used_for_scientific_selection=False,
        attack_event_details_publicly_exposed=False,
    )


def _graph_counts(document: Any) -> tuple[bool | None, bool | None, int | None, int | None]:
    if not isinstance(document, Mapping):
        return None, None, None, None
    directed = document.get("directed")
    multigraph = document.get("multigraph")
    nodes = document.get("nodes")
    edges = document.get("links", document.get("edges"))
    return (
        directed if isinstance(directed, bool) else None,
        multigraph if isinstance(multigraph, bool) else None,
        len(nodes) if isinstance(nodes, (list, tuple)) else None,
        len(edges) if isinstance(edges, (list, tuple)) else None,
    )


def inventory_graph_file(
    path: Path, *, relative_path: str, git_blob_sha: str
) -> HAIGraphInventoryRecordV1:
    """Inventory one official graph file without normalizing or copying it."""

    extension = path.suffix.lower()
    strict_status = "not_applicable"
    literal_status = "not_applicable"
    document: Any = None
    if extension in {".json", ".txt", ".graph"}:
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            strict_status = "decode_failed"
            literal_status = "decode_failed"
        else:
            try:
                document = json.loads(text)
                strict_status = "parsed"
            except json.JSONDecodeError:
                strict_status = "invalid"
                try:
                    document = ast.literal_eval(text)
                    literal_status = "parsed"
                except (SyntaxError, ValueError):
                    literal_status = "invalid"
    directed, multigraph, node_count, edge_count = _graph_counts(document)
    if document is None:
        names = relative_path
    else:
        try:
            names = json.dumps(document, ensure_ascii=True)
        except TypeError:
            names = repr(document)
    process_coverage = tuple(
        process for process in ("P1", "P2", "P3", "P4") if process in names
    )
    lower_name = relative_path.lower()
    if extension in {".png", ".jpg", ".jpeg", ".svg"}:
        kind = "image"
    elif extension == ".ipynb":
        kind = "notebook"
    elif "dcs" in lower_name:
        kind = "DCS_graph"
    else:
        kind = "official_reference_graph"
    return HAIGraphInventoryRecordV1(
        relative_path=relative_path,
        git_blob_sha=git_blob_sha,
        content_sha256=streaming_sha256(path),
        byte_size=path.stat().st_size,
        extension=extension or "none",
        strict_json_parse_status=strict_status,
        python_literal_parse_status=literal_status,
        directed=directed,
        multigraph=multigraph,
        node_count=node_count,
        edge_count=edge_count,
        apparent_process_coverage=process_coverage,
        reference_kind=kind,
        scientific_claim_boundary="weak_relation_reference_not_causal_truth",
    )


def inventory_pdf_reference(
    path: Path, *, relative_path: str, git_blob_sha: str
) -> HAIReferenceFileRecordV1:
    """Inventory the official PDF using optional metadata/text tools, never OCR."""

    with path.open("rb") as stream:
        header_valid = stream.read(5) == b"%PDF-"
    pdfinfo = shutil.which("pdfinfo")
    pdftotext = shutil.which("pdftotext")
    page_count: int | None = None
    title: str | None = None
    tool_version: str | None = None
    extraction_status = "tool_unavailable"
    coverage = "not_assessed"
    variables = "not_assessed"
    processes = "not_assessed"
    method = "file_signature_only"
    if pdfinfo:
        version_result = subprocess.run(
            [pdfinfo, "-v"], capture_output=True, text=True, check=False
        )
        tool_version = (version_result.stderr or version_result.stdout).splitlines()[0]
        info = subprocess.run(
            [pdfinfo, str(path)], capture_output=True, text=True, check=False
        )
        if info.returncode == 0:
            method = "pdfinfo"
            extraction_status = "metadata_extracted"
            for line in info.stdout.splitlines():
                key, _, value = line.partition(":")
                if key.strip() == "Pages" and value.strip().isdigit():
                    page_count = int(value.strip())
                elif key.strip() == "Title" and value.strip():
                    title = value.strip()
    if pdftotext:
        text_result = subprocess.run(
            [pdftotext, str(path), "-"], capture_output=True, text=True, check=False
        )
        if text_result.returncode == 0:
            text = text_result.stdout.lower()
            method = "pdfinfo+pdftotext" if pdfinfo else "pdftotext"
            extraction_status = "text_inspected_not_persisted"
            coverage = "explicit" if "23.05" in text else "not_found"
            variables = "available" if any(
                token in text for token in ("variable", "tag", "sensor", "actuator")
            ) else "not_found"
            processes = "available" if any(
                token in text for token in ("process", "boiler", "water treatment")
            ) else "not_found"
    return HAIReferenceFileRecordV1(
        relative_path=relative_path,
        reference_kind="technical_manual",
        git_blob_sha=git_blob_sha,
        content_sha256=streaming_sha256(path),
        byte_size=path.stat().st_size,
        file_type_valid=header_valid,
        page_count=page_count,
        title=title,
        version_metadata="23.05" if coverage == "explicit" else None,
        hai_2305_coverage=coverage,
        variable_descriptions_available=variables,
        process_information_available=processes,
        extraction_method=method,
        extraction_tool_version=tool_version,
        extraction_status=extraction_status,
    )


def build_hai_dataset_manifest_v2(
    *,
    csv_records: Sequence[HAICsvStructureAuditV1],
    label_records: Sequence[HAILabelCustodyPublicRecordV1],
    lfs_records: Sequence[HAILfsPointerRecordV1],
    metadata_artifact_references: Sequence[str],
    source_repository: str,
    snapshot_commit: str,
    feature_names_hash: str,
    label_field_name: str,
    license_reference: str,
    citation_reference: str,
    creation_metadata: CreationMetadataV2,
    expected_point_count: int = 86,
    expected_process_ids: tuple[str, ...] = ("P1", "P2", "P3", "P4"),
) -> DatasetManifestV2:
    """Build the P1A dataset-neutral manifest from verified public audit records."""

    if len(csv_records) != 6 or len(label_records) != 2 or len(lfs_records) != 10:
        raise HAIProvenanceError("HAI manifest requires the exact audited file population")
    _require_hash(feature_names_hash, "feature_names_hash")
    if not label_field_name:
        raise HAIProvenanceError("label_field_name must be discovered explicitly")
    if not all(item.materialized and item.pointer_matches_expected for item in lfs_records):
        raise HAIProvenanceError("all HAI Git-LFS records must be verified")
    if not all(item.expected_point_count_reconciled for item in csv_records):
        raise HAIProvenanceError("HAI point count is not reconciled")
    if any(item.process_ids_observed != expected_process_ids for item in csv_records):
        raise HAIProvenanceError("HAI process IDs are not source-supported across files")
    header_hashes = {item.header_sha256 for item in csv_records}
    if len(header_hashes) != 1:
        raise HAIProvenanceError("HAI time-series headers are not aligned")
    nominal_values = {
        item.nominal_timestamp_delta_seconds for item in csv_records
    }
    if len(nominal_values) != 1 or None in nominal_values:
        raise HAIProvenanceError("HAI nominal sampling interval is not aligned")
    csv_by_path = {item.relative_path: item for item in csv_records}
    label_by_path = {item.label_relative_path: item for item in label_records}
    file_records: list[DatasetFileV2] = []
    for lfs in sorted(lfs_records, key=lambda item: item.relative_path):
        path = lfs.relative_path
        if path in csv_by_path:
            audit = csv_by_path[path]
            is_test = "hai-test" in path
            role = "test_time_series" if is_test else "normal_train_time_series"
            label_availability = (
                LabelAvailabilityV2.AVAILABLE if is_test else LabelAvailabilityV2.UNAVAILABLE
            )
            row_count = audit.row_count
        elif path in label_by_path:
            role = "external_test_label"
            label_availability = LabelAvailabilityV2.AVAILABLE
            row_count = label_by_path[path].label_row_count
        elif "summary_label" in path:
            role = "private_attack_summary_reference"
            label_availability = LabelAvailabilityV2.AVAILABLE
            row_count = None
        else:
            raise HAIProvenanceError(f"unexpected HAI manifest file: {path}")
        file_records.append(
            DatasetFileV2(
                logical_file_role=role,
                relative_local_path=path,
                sha256=lfs.materialized_sha256,
                byte_size=lfs.materialized_size_bytes,
                row_count=row_count,
                compression=CompressionTypeV2.NONE,
                time_range=None,
                process_ids=expected_process_ids,
                label_availability=label_availability,
                provenance_status=ProvenanceStatusV2.VERIFIED,
            )
        )
    return DatasetManifestV2(
        dataset_name="HAI",
        dataset_version_or_edition="23.05",
        source_kind="official_github_git_lfs",
        source_reference=f"{source_repository}@{snapshot_commit}",
        license_or_terms_reference=license_reference,
        citation_reference=citation_reference,
        local_only_storage=True,
        files=tuple(file_records),
        feature_count=expected_point_count,
        feature_names_hash=feature_names_hash,
        timestamp_specification=TimestampSpecificationV2(
            field_name=csv_records[0].timestamp_field,
            format="ISO-8601-compatible source timestamp",
            timezone="source_unspecified",
            provenance_status=ProvenanceStatusV2.VERIFIED,
        ),
        nominal_sampling_interval_seconds=float(next(iter(nominal_values))),
        label_specification=LabelSpecificationV2(
            field_name=label_field_name,
            encoding={"normal": 0, "attack": 1},
            provenance_status=ProvenanceStatusV2.VERIFIED,
        ),
        available_process_ids=expected_process_ids,
        metadata_artifact_references=tuple(metadata_artifact_references),
        provenance_status=ProvenanceStatusV2.VERIFIED,
        creation_metadata=creation_metadata,
    )


def assert_public_artifact_has_no_sensitive_content(document: Any) -> None:
    """Fail closed on absolute paths or attack-detail fields in public output."""

    prohibited_keys = {
        "attack_start",
        "attack_end",
        "attack_duration",
        "attack_target",
        "target_controller",
        "target_point",
        "attack_description",
        "attack_sequence",
        "positive_attack_point_count",
        "event_sample_count",
    }

    def visit(value: Any) -> None:
        if isinstance(value, Mapping):
            for key, item in value.items():
                if str(key).lower() in prohibited_keys:
                    raise HAIProvenanceError("public artifact contains attack detail")
                visit(item)
        elif isinstance(value, (list, tuple)):
            for item in value:
                visit(item)
        elif isinstance(value, str):
            if re.search(r"^(?:[A-Za-z]:[\\/]|/home/|/Users/|/tmp/)", value):
                raise HAIProvenanceError("public artifact contains an absolute path")

    visit(document)


def run_git(repository: Path, *arguments: str) -> str:
    """Run a read-only Git query in the official checkout."""

    result = subprocess.run(
        ["git", "-C", str(repository), *arguments],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="strict",
        check=False,
    )
    if result.returncode != 0:
        raise HAIProvenanceError(
            f"Git query failed: {' '.join(arguments)}: {result.stderr.strip()}"
        )
    return result.stdout.strip()


def git_blob_sha(repository: Path, commit: str, relative_path: str) -> str:
    return run_git(repository, "rev-parse", f"{commit}:{relative_path}")


def git_blob_text(repository: Path, commit: str, relative_path: str) -> str:
    return run_git(repository, "show", f"{commit}:{relative_path}")


def assert_external_audit_roots(
    *, paper_repository_root: Path, official_root: Path, private_root: Path
) -> None:
    """Reject raw source or private custody roots inside the paper repository."""

    paper = paper_repository_root.resolve()
    official = official_root.resolve()
    private = private_root.resolve()
    for name, candidate in (("official", official), ("private", private)):
        try:
            candidate.relative_to(paper)
        except ValueError:
            continue
        raise HAIProvenanceError(f"{name} audit root must remain outside the paper repository")
    if official == private:
        raise HAIProvenanceError("official and private roots must be separate")


def write_public_json(path: Path, document: Mapping[str, Any]) -> None:
    """Write one sanitized deterministic public JSON artifact."""

    assert_public_artifact_has_no_sensitive_content(document)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(document, sort_keys=True, indent=2, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )


def build_sanitized_acquisition_failure_report(
    *,
    execution_code_commit: str,
    repository_url: str,
    snapshot_commit: str,
    observed_head: str,
    observed_origin_url: str,
    failure_status: str,
    failure_category: str,
    created_at: str,
) -> dict[str, Any]:
    """Build a public blocked-acquisition report without exception or path text."""

    _require_commit(execution_code_commit, "execution_code_commit")
    _require_commit(snapshot_commit, "snapshot_commit")
    _require_commit(observed_head, "observed_head")
    if failure_status not in {
        "blocked_official_source_unavailable",
        "blocked_git_lfs_unavailable",
        "blocked_lfs_object_unavailable",
    }:
        raise HAIProvenanceError("unsupported acquisition failure status")
    if failure_category not in {
        "official_git_remote_unavailable",
        "git_lfs_command_unavailable",
        "official_repository_lfs_budget_exhausted",
        "official_lfs_object_download_failed",
    }:
        raise HAIProvenanceError("unsupported acquisition failure category")
    try:
        parsed = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
    except ValueError as exc:
        raise HAIProvenanceError("created_at must be ISO 8601") from exc
    if parsed.tzinfo is None:
        raise HAIProvenanceError("created_at must include a timezone")
    report = {
        "schema_version": HAI_PROVENANCE_SCHEMA_VERSION,
        "artifact_type": "task039a_blocked_provenance_report",
        "task_id": "TASK-039A",
        "status": failure_status,
        "execution_code_commit": execution_code_commit,
        "official_repository": repository_url,
        "snapshot_commit": snapshot_commit,
        "observed_head": observed_head,
        "observed_origin_url": observed_origin_url,
        "failure_category": failure_category,
        "completed_audit_stages": [
            "official_git_clone",
            "official_remote_identity",
            "pinned_commit_availability",
            "detached_snapshot_checkout",
        ],
        "unexecuted_audit_stages": [
            "lfs_materialization_verification",
            "csv_structure_audit",
            "label_custody_audit",
            "technical_reference_inventory",
            "graph_inventory",
            "dataset_manifest_v2_construction",
        ],
        "dataset_manifest_created": False,
        "hai_ready": False,
        "raw_data_entered_paper_repository": False,
        "label_content_accessed": False,
        "attack_event_details_publicly_exposed": False,
        "scientific_analysis_performed": False,
        "fallback_source_used": False,
        "created_at": created_at,
    }
    report["report_hash"] = canonical_self_hash(report, "report_hash")
    assert_public_artifact_has_no_sensitive_content(report)
    return report
