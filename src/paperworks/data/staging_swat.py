"""Kaggle/local SWaT staging mirror manifest helpers."""

from __future__ import annotations

import csv
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path, PurePosixPath
from typing import Any, Mapping, Sequence

from paperworks.data.contracts import SCHEMA_VERSION, stable_hash
from paperworks.data.files import (
    DataFileError,
    IrregularSamplingError,
    infer_regular_sampling_period,
    parse_timestamp,
    resolve_data_root,
    sha256_file,
)
from paperworks.metadata import MetadataRegistry


TASK016_REQUIRED_REPORT_STATEMENT = (
    "This is a Kaggle/local staging run for implementation debugging only. "
    "It is not an official SWaT benchmark result and must not be used as a final thesis performance claim."
)
KAGGLE_SWAT_SOURCE = "https://www.kaggle.com/datasets/vishala28/swat-dataset-secure-water-treatment-system"
DEFAULT_STAGING_FILES = ("normal.csv", "attack.csv", "merged.csv")
DEFAULT_TIMESTAMP_FORMATS = ("%d/%m/%Y %I:%M:%S %p", "%Y-%m-%d %H:%M:%S")


class StagingSwatMirrorError(ValueError):
    """Raised when a staging SWaT mirror manifest is incomplete or unsafe."""


def _validate_relative_path(path: str) -> None:
    parsed = PurePosixPath(path.replace("\\", "/"))
    if parsed.is_absolute() or ".." in parsed.parts:
        raise StagingSwatMirrorError(f"path must be relative and stay within SWAT_DATA_ROOT: {path}")


@dataclass(frozen=True)
class StagingSwatFileRecord:
    logical_role: str
    relative_path: str
    sha256: str
    bytes: int
    rows_excluding_header: int
    column_names: tuple[str, ...]
    label_counts: Mapping[str, int]
    timestamp_column: str
    label_column: str
    inferred_sampling_period_seconds: float | None
    limitations: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.logical_role:
            raise StagingSwatMirrorError("logical_role is required")
        _validate_relative_path(self.relative_path)
        if len(self.sha256) != 64:
            raise StagingSwatMirrorError("sha256 must be a 64-character hash")
        if self.bytes < 0 or self.rows_excluding_header < 0:
            raise StagingSwatMirrorError("bytes and row counts must be non-negative")
        if not self.column_names:
            raise StagingSwatMirrorError("column_names are required")
        if self.timestamp_column not in self.column_names:
            raise StagingSwatMirrorError("timestamp_column must be present in column_names")
        if self.label_column not in self.column_names:
            raise StagingSwatMirrorError("label_column must be present in column_names")

    @property
    def feature_columns(self) -> tuple[str, ...]:
        return tuple(
            name for name in self.column_names if name not in {self.timestamp_column, self.label_column}
        )

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["column_names"] = list(self.column_names)
        data["label_counts"] = dict(sorted(self.label_counts.items()))
        data["limitations"] = list(self.limitations)
        return data

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "StagingSwatFileRecord":
        return cls(
            logical_role=str(data["logical_role"]),
            relative_path=str(data["relative_path"]),
            sha256=str(data["sha256"]),
            bytes=int(data["bytes"]),
            rows_excluding_header=int(data["rows_excluding_header"]),
            column_names=tuple(str(item) for item in data["column_names"]),
            label_counts={str(key): int(value) for key, value in dict(data["label_counts"]).items()},
            timestamp_column=str(data["timestamp_column"]),
            label_column=str(data["label_column"]),
            inferred_sampling_period_seconds=(
                None
                if data.get("inferred_sampling_period_seconds") is None
                else float(data["inferred_sampling_period_seconds"])
            ),
            limitations=tuple(str(item) for item in data.get("limitations", ())),
        )


@dataclass(frozen=True)
class StagingSwatMirrorManifest:
    files: tuple[StagingSwatFileRecord, ...]
    staging_source_label: str = "kaggle_mirror_staging"
    source_kind: str = "kaggle_mirror"
    dataset_status: str = "staging_only"
    source_reference: str = KAGGLE_SWAT_SOURCE
    local_root_env: str = "SWAT_DATA_ROOT"
    timestamp_column: str = "Timestamp"
    index_columns: tuple[str, ...] = ()
    label_column: str = "Normal/Attack"
    label_schema: Mapping[str, str] = field(default_factory=lambda: {"normal": "Normal", "attack": "Attack"})
    known_limitations: tuple[str, ...] = (
        "Current local/Kaggle CSV files are staging-only implementation inputs.",
        "This manifest does not resolve DEC-007.",
        "This manifest is not an official SWaT provenance record.",
        "Aggregate row and label counts sum all listed files and may double-count merged plus label-filtered files.",
        "Staging outputs must not be used as final thesis performance claims.",
    )
    required_report_statement: str = TASK016_REQUIRED_REPORT_STATEMENT
    final_claims_allowed: bool = False
    schema_version: str = SCHEMA_VERSION
    artifact_type: str = "staging_swat_mirror_manifest"

    def __post_init__(self) -> None:
        if self.staging_source_label != "kaggle_mirror_staging":
            raise StagingSwatMirrorError("staging_source_label must be kaggle_mirror_staging")
        if self.source_kind != "kaggle_mirror":
            raise StagingSwatMirrorError("source_kind must be kaggle_mirror")
        if self.dataset_status != "staging_only":
            raise StagingSwatMirrorError("dataset_status must be staging_only")
        if self.final_claims_allowed:
            raise StagingSwatMirrorError("staging mirror cannot allow final claims")
        if not self.files:
            raise StagingSwatMirrorError("files are required")
        for file_record in self.files:
            if file_record.timestamp_column != self.timestamp_column:
                raise StagingSwatMirrorError("file timestamp column mismatch")
            if file_record.label_column != self.label_column:
                raise StagingSwatMirrorError("file label column mismatch")
            for index_column in self.index_columns:
                if index_column not in file_record.column_names:
                    raise StagingSwatMirrorError("index_columns must be present in each file")

    @property
    def manifest_id(self) -> str:
        return stable_hash(self.to_dict())

    @property
    def feature_columns(self) -> tuple[str, ...]:
        return self.files[0].feature_columns

    @property
    def feature_count(self) -> int:
        return len(self.feature_columns)

    @property
    def total_rows(self) -> int:
        return sum(file.rows_excluding_header for file in self.files)

    @property
    def file_fingerprints(self) -> Mapping[str, str]:
        return {file.relative_path: file.sha256 for file in self.files}

    @property
    def columns_consistent(self) -> bool:
        first = self.files[0].column_names
        return all(file.column_names == first for file in self.files)

    @property
    def aggregate_label_counts(self) -> Mapping[str, int]:
        counts: dict[str, int] = {}
        for file in self.files:
            for label, count in file.label_counts.items():
                counts[label] = counts.get(label, 0) + count
        return dict(sorted(counts.items()))

    def normalized_feature_columns(self) -> tuple[str, ...]:
        return tuple(name.strip() for name in self.feature_columns)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "artifact_type": self.artifact_type,
            "staging_source_label": self.staging_source_label,
            "source_kind": self.source_kind,
            "dataset_status": self.dataset_status,
            "source_reference": self.source_reference,
            "local_root_env": self.local_root_env,
            "timestamp_column": self.timestamp_column,
            "index_columns": list(self.index_columns),
            "label_column": self.label_column,
            "label_schema": dict(sorted(self.label_schema.items())),
            "feature_count": self.feature_count,
            "feature_columns": list(self.feature_columns),
            "total_rows": self.total_rows,
            "columns_consistent": self.columns_consistent,
            "aggregate_label_counts": dict(self.aggregate_label_counts),
            "file_fingerprints": dict(sorted(self.file_fingerprints.items())),
            "files": [file.to_dict() for file in self.files],
            "known_limitations": list(self.known_limitations),
            "required_report_statement": self.required_report_statement,
            "final_claims_allowed": self.final_claims_allowed,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, indent=2)

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "StagingSwatMirrorManifest":
        return cls(
            files=tuple(StagingSwatFileRecord.from_dict(item) for item in data["files"]),
            staging_source_label=str(data.get("staging_source_label", "kaggle_mirror_staging")),
            source_kind=str(data.get("source_kind", "kaggle_mirror")),
            dataset_status=str(data.get("dataset_status", "staging_only")),
            source_reference=str(data.get("source_reference", KAGGLE_SWAT_SOURCE)),
            local_root_env=str(data.get("local_root_env", "SWAT_DATA_ROOT")),
            timestamp_column=str(data.get("timestamp_column", "Timestamp")),
            index_columns=tuple(str(item) for item in data.get("index_columns", ())),
            label_column=str(data.get("label_column", "Normal/Attack")),
            label_schema={str(key): str(value) for key, value in dict(data.get("label_schema", {})).items()},
            known_limitations=tuple(str(item) for item in data.get("known_limitations", ())),
            required_report_statement=str(data.get("required_report_statement", TASK016_REQUIRED_REPORT_STATEMENT)),
            final_claims_allowed=bool(data.get("final_claims_allowed", False)),
            schema_version=str(data.get("schema_version", SCHEMA_VERSION)),
            artifact_type=str(data.get("artifact_type", "staging_swat_mirror_manifest")),
        )

    @classmethod
    def from_json(cls, text: str) -> "StagingSwatMirrorManifest":
        return cls.from_dict(json.loads(text))


@dataclass(frozen=True)
class StagingSwatDevelopmentReport:
    manifest_id: str
    report_statement: str
    staging_source_label: str
    dataset_status: str
    source_kind: str
    file_count: int
    feature_count: int
    total_rows: int
    columns_consistent: bool
    aggregate_label_counts: Mapping[str, int]
    metadata_expected_count: int | None
    metadata_missing_features: tuple[str, ...]
    metadata_extra_features: tuple[str, ...]
    pipeline_stage: str = "staging_schema_metadata_smoke"
    final_claims_allowed: bool = False
    dec007_resolved: bool = False
    official_manifest_used: bool = False
    known_limitations: tuple[str, ...] = ()
    schema_version: str = SCHEMA_VERSION
    artifact_type: str = "task016_staging_development_report"

    def __post_init__(self) -> None:
        if self.report_statement != TASK016_REQUIRED_REPORT_STATEMENT:
            raise StagingSwatMirrorError("TASK-016 report statement is required")
        if self.final_claims_allowed or self.dec007_resolved or self.official_manifest_used:
            raise StagingSwatMirrorError("staging development report cannot authorize final evaluation")
        if len(self.manifest_id) != 64:
            raise StagingSwatMirrorError("manifest_id must be a 64-character hash")

    @property
    def report_id(self) -> str:
        return stable_hash(self.to_dict())

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "artifact_type": self.artifact_type,
            "manifest_id": self.manifest_id,
            "report_statement": self.report_statement,
            "staging_source_label": self.staging_source_label,
            "dataset_status": self.dataset_status,
            "source_kind": self.source_kind,
            "file_count": self.file_count,
            "feature_count": self.feature_count,
            "total_rows": self.total_rows,
            "columns_consistent": self.columns_consistent,
            "aggregate_label_counts": dict(sorted(self.aggregate_label_counts.items())),
            "metadata_expected_count": self.metadata_expected_count,
            "metadata_missing_features": list(self.metadata_missing_features),
            "metadata_extra_features": list(self.metadata_extra_features),
            "pipeline_stage": self.pipeline_stage,
            "final_claims_allowed": self.final_claims_allowed,
            "dec007_resolved": self.dec007_resolved,
            "official_manifest_used": self.official_manifest_used,
            "known_limitations": list(self.known_limitations),
        }


def inspect_staging_swat_mirror(
    *,
    root: Path,
    relative_paths: Sequence[str] = DEFAULT_STAGING_FILES,
    timestamp_column: str = "Timestamp",
    label_column: str = "Normal/Attack",
    timestamp_formats: Sequence[str] = DEFAULT_TIMESTAMP_FORMATS,
    sampling_sample_limit: int = 100,
) -> StagingSwatMirrorManifest:
    records = tuple(
        _inspect_staging_file(
            root=root,
            relative_path=relative_path,
            timestamp_column=timestamp_column,
            label_column=label_column,
            timestamp_formats=timestamp_formats,
            sampling_sample_limit=sampling_sample_limit,
        )
        for relative_path in relative_paths
    )
    return StagingSwatMirrorManifest(files=records, timestamp_column=timestamp_column, label_column=label_column)


def inspect_staging_swat_mirror_from_env(
    *,
    env_var: str = "SWAT_DATA_ROOT",
    relative_paths: Sequence[str] = DEFAULT_STAGING_FILES,
    sampling_sample_limit: int = 100,
) -> StagingSwatMirrorManifest:
    return inspect_staging_swat_mirror(
        root=resolve_data_root(env_var),
        relative_paths=relative_paths,
        sampling_sample_limit=sampling_sample_limit,
    )


def build_task016_staging_development_report(
    *,
    manifest: StagingSwatMirrorManifest,
    metadata: MetadataRegistry | None = None,
) -> StagingSwatDevelopmentReport:
    missing_features: tuple[str, ...] = ()
    extra_features: tuple[str, ...] = ()
    expected_count: int | None = None
    if metadata is not None:
        coverage = metadata.coverage_report(manifest.feature_columns)
        expected_count = coverage.expected_count
        missing_features = coverage.missing_features
        extra_features = coverage.extra_metadata
    return StagingSwatDevelopmentReport(
        manifest_id=manifest.manifest_id,
        report_statement=TASK016_REQUIRED_REPORT_STATEMENT,
        staging_source_label=manifest.staging_source_label,
        dataset_status=manifest.dataset_status,
        source_kind=manifest.source_kind,
        file_count=len(manifest.files),
        feature_count=manifest.feature_count,
        total_rows=manifest.total_rows,
        columns_consistent=manifest.columns_consistent,
        aggregate_label_counts=manifest.aggregate_label_counts,
        metadata_expected_count=expected_count,
        metadata_missing_features=missing_features,
        metadata_extra_features=extra_features,
        known_limitations=manifest.known_limitations,
    )


def _inspect_staging_file(
    *,
    root: Path,
    relative_path: str,
    timestamp_column: str,
    label_column: str,
    timestamp_formats: Sequence[str],
    sampling_sample_limit: int,
) -> StagingSwatFileRecord:
    _validate_relative_path(relative_path)
    path = root / relative_path
    if not path.exists() or not path.is_file():
        raise StagingSwatMirrorError(f"missing staging file: {relative_path}")
    rows = 0
    labels: dict[str, int] = {}
    timestamps = []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise StagingSwatMirrorError(f"CSV has no header: {relative_path}")
        columns = tuple(name.strip() for name in reader.fieldnames)
        reader.fieldnames = list(columns)
        if timestamp_column not in columns:
            raise StagingSwatMirrorError(f"missing timestamp column {timestamp_column!r}")
        if label_column not in columns:
            raise StagingSwatMirrorError(f"missing label column {label_column!r}")
        for row in reader:
            rows += 1
            label = row[label_column].strip()
            labels[label] = labels.get(label, 0) + 1
            if len(timestamps) < sampling_sample_limit:
                timestamps.append(parse_timestamp(row[timestamp_column], timestamp_formats))
    sampling_period: float | None
    limitations: list[str] = []
    try:
        sampling_period = infer_regular_sampling_period(timestamps)
    except (DataFileError, IrregularSamplingError):
        sampling_period = None
        limitations.append("sampled timestamps were not regular enough to infer one sampling period")
    return StagingSwatFileRecord(
        logical_role=_logical_role(relative_path),
        relative_path=relative_path,
        sha256=sha256_file(path),
        bytes=path.stat().st_size,
        rows_excluding_header=rows,
        column_names=columns,
        label_counts=labels,
        timestamp_column=timestamp_column,
        label_column=label_column,
        inferred_sampling_period_seconds=sampling_period,
        limitations=tuple(limitations),
    )


def _logical_role(relative_path: str) -> str:
    lowered = Path(relative_path).name.lower()
    if lowered == "normal.csv":
        return "kaggle_staging_normal_label_subset"
    if lowered == "attack.csv":
        return "kaggle_staging_attack_label_subset"
    if lowered == "merged.csv":
        return "kaggle_staging_merged_label_subset"
    return "kaggle_staging_auxiliary_file"
