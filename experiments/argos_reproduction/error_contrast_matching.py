"""Build and deterministically match generation-only TN or TP contrast chunks."""

from __future__ import annotations

import hashlib
import math
from pathlib import Path
import sys
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from experiments.argos_reproduction.detector_error_support_audit import (
    GenerationErrorCell,
    aligned_contrast_starts,
)
from experiments.argos_reproduction.error_conditioned_target_selection import (
    canonical_chunk_hash,
)


class ErrorContrastMatchingError(RuntimeError):
    """Raised when a contrast pool or match violates the frozen policy."""


def contrast_pool(
    cell: GenerationErrorCell, direction: str, chunk_size: int
) -> tuple[dict[str, Any], ...]:
    rows: list[dict[str, Any]] = []
    for start in aligned_contrast_starts(cell, direction, chunk_size):
        end = start + chunk_size
        values = cell.values[start:end]
        labels = cell.labels[start:end]
        predictions = cell.predictions[start:end]
        indices = np.arange(start, end, dtype=np.int64)
        if direction == "FN":
            if not (np.all(labels == 0) and np.all(predictions == 0)):
                raise ErrorContrastMatchingError("TASK037D_FN_CONTRAST_NOT_PURE_TN")
        elif direction == "FP":
            if not np.any((labels == 1) & (predictions == 1)):
                raise ErrorContrastMatchingError("TASK037D_FP_CONTRAST_WITHOUT_TP")
        else:
            raise ErrorContrastMatchingError("TASK037D_DIRECTION_INVALID")
        rows.append(
            {
                "start": start,
                "end": end,
                "values": values.copy(),
                "labels": labels.copy(),
                "indices": indices,
                "hash": canonical_chunk_hash(values, labels, indices),
                "mean": float(np.mean(values)),
                "std": float(np.std(values, ddof=1)),
            }
        )
    return tuple(rows)


def match_contrast(
    target: dict[str, Any], pool: tuple[dict[str, Any], ...]
) -> dict[str, Any]:
    eligible = [
        item
        for item in pool
        if item["end"] <= target["start"] or item["start"] >= target["end"]
    ]
    if not eligible:
        raise ErrorContrastMatchingError("TASK037D_CONTRAST_SUPPORT_MISSING")
    summaries = np.asarray([[item["mean"], item["std"]] for item in eligible], dtype=float)
    center = np.mean(summaries, axis=0)
    scale = np.std(summaries, axis=0)
    scale = np.where(scale > 0, scale, 1.0)
    target_summary = np.asarray(
        [np.mean(target["values"]), np.std(target["values"], ddof=1)], dtype=float
    )
    target_z = (target_summary - center) / scale
    ranked: list[tuple[float, int, dict[str, Any]]] = []
    for item, summary in zip(eligible, summaries):
        distance = float(np.linalg.norm((summary - center) / scale - target_z))
        if not math.isfinite(distance):
            raise ErrorContrastMatchingError("TASK037D_CONTRAST_DISTANCE_NONFINITE")
        ranked.append((distance, int(item["start"]), item))
    return min(ranked, key=lambda row: (row[0], row[1]))[2]


def matching_policy_hash() -> str:
    text = (
        "aligned_generation_chunks|mean_std|pool_standardization|"
        "euclidean_distance|earliest_start_tie|target_nonoverlap"
    )
    return hashlib.sha256(text.encode("ascii")).hexdigest()
