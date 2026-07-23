"""Deterministically select distinct generation-only FN and FP target chunks."""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import sys
from typing import Any, Iterable

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from experiments.argos_reproduction.detector_error_support_audit import (
    GenerationErrorCell,
)
from experiments.argos_reproduction.expanded_kpi_cohort import stable_json_bytes


class ErrorTargetSelectionError(RuntimeError):
    """Raised when an error target violates the frozen generation policy."""


def canonical_chunk_hash(
    values: np.ndarray, labels: np.ndarray, indices: np.ndarray
) -> str:
    payload = {
        "columns": ["value", "label", "index"],
        "rows": [
            [float(value), int(label), int(index)]
            for value, label, index in zip(values, labels, indices)
        ],
    }
    return hashlib.sha256(stable_json_bytes(payload)).hexdigest()


def centered_chunk_bounds(
    segment: tuple[int, int], length: int, chunk_size: int
) -> tuple[int, int]:
    if length < chunk_size:
        raise ErrorTargetSelectionError("TASK037D_GENERATION_SHORTER_THAN_CHUNK")
    center = (segment[0] + segment[1] - 1) // 2
    start = max(0, min(center - chunk_size // 2, length - chunk_size))
    return start, start + chunk_size


def enumerate_distinct_targets(
    cell: GenerationErrorCell, direction: str, chunk_size: int
) -> tuple[dict[str, Any], ...]:
    category = {"FN": "FN", "FP": "FP"}.get(direction)
    if category is None:
        raise ErrorTargetSelectionError("TASK037D_DIRECTION_INVALID")
    candidates: list[dict[str, Any]] = []
    seen: set[str] = set()
    for segment_rank, segment in enumerate(cell.segments[category]):
        start, end = centered_chunk_bounds(segment, len(cell.values), chunk_size)
        values = cell.values[start:end]
        labels = cell.labels[start:end]
        predictions = cell.predictions[start:end]
        intersects = start < segment[1] and end > segment[0]
        if not intersects:
            raise ErrorTargetSelectionError("TASK037D_TARGET_SEGMENT_NOT_INTERSECTED")
        if direction == "FN":
            eligible = bool(np.any(labels == 1) and np.any((labels == 1) & (predictions == 0)))
        else:
            eligible = bool(
                np.all(labels == 0) and np.any((labels == 0) & (predictions == 1))
            )
        if not eligible:
            continue
        indices = np.arange(start, end, dtype=np.int64)
        digest = canonical_chunk_hash(values, labels, indices)
        if digest in seen:
            continue
        seen.add(digest)
        candidates.append(
            {
                "segment_rank": segment_rank,
                "segment": segment,
                "start": start,
                "end": end,
                "hash": digest,
                "values": values.copy(),
                "labels": labels.copy(),
                "indices": indices,
            }
        )
    return tuple(candidates)


def evenly_distributed_targets(
    candidates: Iterable[dict[str, Any]], maximum: int
) -> tuple[dict[str, Any], ...]:
    rows = tuple(candidates)
    count = min(maximum, len(rows))
    if count == 0:
        return ()
    selected: list[dict[str, Any]] = []
    used: set[int] = set()
    for index in range(count):
        rank = math.floor((index + 0.5) * len(rows) / count)
        rank = min(rank, len(rows) - 1)
        while rank in used and rank + 1 < len(rows):
            rank += 1
        if rank in used:
            rank = next(candidate for candidate in range(len(rows)) if candidate not in used)
        used.add(rank)
        selected.append(rows[rank])
    return tuple(selected)


def save_private_chunk(path: Path, target: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savez(
        path,
        values=np.asarray(target["values"], dtype=np.float64),
        labels=np.asarray(target["labels"], dtype=np.int8),
        indices=np.asarray(target["indices"], dtype=np.int64),
    )


def sanitized_target(target: dict[str, Any], target_rank: int) -> dict[str, Any]:
    return {
        "target_rank": target_rank,
        "target_segment_rank": int(target["segment_rank"]),
        "target_start": int(target["start"]),
        "target_end": int(target["end"]),
        "target_chunk_hash": str(target["hash"]),
        "row_count": int(target["end"] - target["start"]),
    }


def _main_demo() -> int:
    print(json.dumps({"module": "error_conditioned_target_selection", "status": "ready"}))
    return 0


if __name__ == "__main__":
    raise SystemExit(_main_demo())
