"""Local file validation and CSV metadata helpers."""

from __future__ import annotations

import csv
import os
from dataclasses import dataclass
from datetime import datetime
from hashlib import sha256
from pathlib import Path
from typing import Iterable, Mapping, Sequence

from paperworks.data.contracts import DatasetManifest


class DataFileError(ValueError):
    """Raised when local dataset files are missing or inconsistent."""


class IrregularSamplingError(DataFileError):
    """Raised when timestamps do not have a regular sampling period."""


@dataclass(frozen=True)
class CsvMetadata:
    relative_path: str
    rows_excluding_header: int
    column_names: tuple[str, ...]
    label_counts: Mapping[str, int]
    timestamp_column: str
    label_column: str
    sampling_period_seconds: float | None


def resolve_data_root(env_var: str = "SWAT_DATA_ROOT") -> Path:
    value = os.environ.get(env_var)
    if not value:
        raise DataFileError(f"{env_var} is not set")
    root = Path(value).expanduser()
    if not root.exists() or not root.is_dir():
        raise DataFileError(f"{env_var} does not point to an existing directory: {root}")
    return root


def sha256_file(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_local_files(manifest: DatasetManifest, root: Path) -> None:
    for relative_path, expected_digest in manifest.file_fingerprints.items():
        path = root / relative_path
        if not path.exists() or not path.is_file():
            raise DataFileError(f"missing dataset file: {relative_path}")
        observed_digest = sha256_file(path)
        if observed_digest != expected_digest:
            raise DataFileError(
                f"fingerprint mismatch for {relative_path}: "
                f"expected {expected_digest}, observed {observed_digest}"
            )


def parse_timestamp(value: str, formats: Sequence[str]) -> datetime:
    stripped = value.strip()
    for fmt in formats:
        try:
            return datetime.strptime(stripped, fmt)
        except ValueError:
            continue
    raise DataFileError(f"timestamp does not match configured formats: {stripped!r}")


def infer_regular_sampling_period(timestamps: Sequence[datetime]) -> float | None:
    if len(timestamps) < 2:
        return None
    deltas = [
        (timestamps[index] - timestamps[index - 1]).total_seconds()
        for index in range(1, len(timestamps))
    ]
    first = deltas[0]
    if any(delta != first for delta in deltas):
        raise IrregularSamplingError("timestamp intervals are not regular")
    if first <= 0:
        raise IrregularSamplingError("timestamp intervals must be positive")
    return first


def inspect_csv_metadata(
    path: Path,
    *,
    relative_path: str,
    timestamp_column: str,
    label_column: str,
    timestamp_formats: Iterable[str],
    sample_limit: int | None = None,
) -> CsvMetadata:
    rows = 0
    labels: dict[str, int] = {}
    sampled_timestamps: list[datetime] = []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise DataFileError(f"CSV has no header: {relative_path}")
        columns = tuple(name.strip() for name in reader.fieldnames)
        if timestamp_column not in columns:
            raise DataFileError(f"missing timestamp column {timestamp_column!r}")
        if label_column not in columns:
            raise DataFileError(f"missing label column {label_column!r}")
        formats = tuple(timestamp_formats)
        for row in reader:
            rows += 1
            label = row[label_column].strip()
            labels[label] = labels.get(label, 0) + 1
            if sample_limit is None or len(sampled_timestamps) < sample_limit:
                sampled_timestamps.append(parse_timestamp(row[timestamp_column], formats))
    return CsvMetadata(
        relative_path=relative_path,
        rows_excluding_header=rows,
        column_names=columns,
        label_counts=labels,
        timestamp_column=timestamp_column,
        label_column=label_column,
        sampling_period_seconds=infer_regular_sampling_period(sampled_timestamps),
    )

