"""Chronological KPI split reproduction with a fail-closed sealed-test reader."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import csv
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np


class KpiSplitGuardError(RuntimeError):
    """Raised when a read could cross the frozen validation/test boundary."""


@dataclass(frozen=True)
class KpiSplitBoundaries:
    series_row_count: int
    train_start: int
    train_end_exclusive: int
    validation_start: int
    validation_end_exclusive: int
    test_start: int
    test_end_exclusive: int

    @property
    def train_row_count(self) -> int:
        return self.train_end_exclusive - self.train_start

    @property
    def validation_row_count(self) -> int:
        return self.validation_end_exclusive - self.validation_start

    @property
    def test_row_count(self) -> int:
        return self.test_end_exclusive - self.test_start

    def to_dict(self) -> dict[str, int]:
        result = asdict(self)
        result.update(
            train_row_count=self.train_row_count,
            validation_row_count=self.validation_row_count,
            test_row_count=self.test_row_count,
        )
        return result


@dataclass(frozen=True)
class GuardedValidationData:
    values: np.ndarray
    labels: np.ndarray
    parsed_row_count: int
    maximum_parsed_row_exclusive: int
    test_rows_parsed: bool


def stable_json_bytes(value: object) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False
    ).encode("utf-8")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def compute_pinned_argos_split(
    row_count: int, *, train_test_split: float = 0.7, validation_split: float = 0.2
) -> KpiSplitBoundaries:
    """Reproduce pinned ARGOS nested ``int`` boundary calculations exactly."""
    if row_count <= 0:
        raise KpiSplitGuardError("TASK034_ROW_COUNT_INVALID")
    if not 0 < train_test_split < 1 or not 0 < validation_split < 1:
        raise KpiSplitGuardError("TASK034_SPLIT_PROPORTION_INVALID")
    train_pool_end = int(row_count * train_test_split)
    train_end = int(train_pool_end * (1 - validation_split))
    boundaries = KpiSplitBoundaries(
        series_row_count=row_count,
        train_start=0,
        train_end_exclusive=train_end,
        validation_start=train_end,
        validation_end_exclusive=train_pool_end,
        test_start=train_pool_end,
        test_end_exclusive=row_count,
    )
    if not (
        boundaries.train_start
        <= boundaries.train_end_exclusive
        == boundaries.validation_start
        <= boundaries.validation_end_exclusive
        == boundaries.test_start
        <= boundaries.test_end_exclusive
    ):
        raise KpiSplitGuardError("TASK034_SPLIT_BOUNDARY_INVALID")
    if boundaries.train_row_count + boundaries.validation_row_count + boundaries.test_row_count != row_count:
        raise KpiSplitGuardError("TASK034_SPLIT_NOT_EXHAUSTIVE")
    return boundaries


def assert_sealed_read_range(
    *, start: int, end_exclusive: int, boundaries: KpiSplitBoundaries
) -> None:
    if start < 0 or end_exclusive < start:
        raise KpiSplitGuardError("TASK034_READ_RANGE_INVALID")
    if start >= boundaries.test_start or end_exclusive > boundaries.test_start:
        raise KpiSplitGuardError("TASK034_TEST_RANGE_READ_PROHIBITED")


def read_validation_prefix(
    csv_path: Path, boundaries: KpiSplitBoundaries
) -> GuardedValidationData:
    """Read only the prefix ending at the validation boundary and retain validation rows."""
    assert_sealed_read_range(
        start=boundaries.validation_start,
        end_exclusive=boundaries.validation_end_exclusive,
        boundaries=boundaries,
    )
    values: list[float] = []
    labels: list[int] = []
    parsed = 0
    with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != ["value", "label", "index"]:
            raise KpiSplitGuardError("TASK034_CSV_SCHEMA_INVALID")
        for position, row in enumerate(reader):
            if position >= boundaries.validation_end_exclusive:
                break
            parsed = position + 1
            if position < boundaries.validation_start:
                continue
            try:
                value = float(row["value"])
                label_value = float(row["label"])
                index_value = int(row["index"])
            except (KeyError, TypeError, ValueError) as error:
                raise KpiSplitGuardError("TASK034_CSV_ROW_INVALID") from error
            if not np.isfinite(value) or label_value not in (0.0, 1.0):
                raise KpiSplitGuardError("TASK034_CSV_VALUE_INVALID")
            if index_value != position:
                raise KpiSplitGuardError("TASK034_CSV_INDEX_INVALID")
            values.append(value)
            labels.append(int(label_value))
    if parsed != boundaries.validation_end_exclusive:
        raise KpiSplitGuardError("TASK034_VALIDATION_PREFIX_TRUNCATED")
    if len(values) != boundaries.validation_row_count:
        raise KpiSplitGuardError("TASK034_VALIDATION_LENGTH_INVALID")
    return GuardedValidationData(
        values=np.asarray(values, dtype=np.float64).reshape(-1, 1),
        labels=np.asarray(labels, dtype=np.int8),
        parsed_row_count=parsed,
        maximum_parsed_row_exclusive=parsed,
        test_rows_parsed=False,
    )


def split_manifest_payload(
    boundaries: KpiSplitBoundaries, *, source_commit: str, source_blob_hash: str
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "schema_version": "1.0",
        "artifact_type": "task034_private_split_manifest",
        **boundaries.to_dict(),
        "boundary_algorithm": (
            "train_pool_end=int(N*0.7); "
            "train_end=int(train_pool_end*(1-0.2)); chronological half-open ranges"
        ),
        "source_commit": source_commit,
        "source_file": "datasets/dataset.py",
        "source_lineage_hash": source_blob_hash,
        "chronological": True,
        "shuffle": False,
        "purge_or_gap": False,
        "test_status": "sealed_not_accessed",
    }
    payload["split_manifest_hash"] = hashlib.sha256(stable_json_bytes(payload)).hexdigest()
    return payload
