"""Deterministic half-open detector-error segments for synthetic contract tests."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Iterable, Mapping, Sequence


CATEGORIES = ("TP", "FN", "FP", "TN")


class DetectorSegmentError(ValueError):
    pass


@dataclass(frozen=True, order=True)
class ErrorSegment:
    category: str
    start: int
    end_exclusive: int

    def to_dict(self) -> dict[str, object]:
        return {
            "category": self.category,
            "start": self.start,
            "end_exclusive": self.end_exclusive,
        }


def _binary(values: Sequence[int], name: str) -> tuple[int, ...]:
    result = tuple(values)
    if any(isinstance(value, bool) or value not in (0, 1) for value in result):
        raise DetectorSegmentError(f"DETECTOR_{name.upper()}_BINARY_INVALID")
    return result


def build_error_segments(
    labels: Sequence[int], predictions: Sequence[int]
) -> tuple[ErrorSegment, ...]:
    truth = _binary(labels, "labels")
    predicted = _binary(predictions, "predictions")
    if len(truth) != len(predicted):
        raise DetectorSegmentError("DETECTOR_SEGMENT_LENGTH_MISMATCH")
    point_categories = tuple(
        "TP" if y == 1 and p == 1 else
        "FN" if y == 1 else
        "FP" if p == 1 else
        "TN"
        for y, p in zip(truth, predicted)
    )
    segments: list[ErrorSegment] = []
    if not point_categories:
        return ()
    start = 0
    category = point_categories[0]
    for index, current in enumerate(point_categories[1:], 1):
        if current != category:
            segments.append(ErrorSegment(category, start, index))
            start, category = index, current
    segments.append(ErrorSegment(category, start, len(point_categories)))
    return tuple(segments)


def segments_by_category(
    segments: Iterable[ErrorSegment],
) -> dict[str, tuple[tuple[int, int], ...]]:
    grouped: dict[str, list[tuple[int, int]]] = {key: [] for key in CATEGORIES}
    for segment in segments:
        if segment.category not in grouped or segment.start >= segment.end_exclusive:
            raise DetectorSegmentError("DETECTOR_SEGMENT_INVALID")
        grouped[segment.category].append((segment.start, segment.end_exclusive))
    for ranges in grouped.values():
        for previous, current in zip(ranges, ranges[1:]):
            if previous[1] > current[0]:
                raise DetectorSegmentError("DETECTOR_SEGMENT_OVERLAP")
    return {key: tuple(grouped[key]) for key in CATEGORIES}


def argos_inclusive_intervals(
    grouped: Mapping[str, Sequence[tuple[int, int]]]
) -> dict[str, list[list[int]]]:
    """Convert internal half-open ranges to documented inclusive endpoints."""
    return {
        key: [[start, end_exclusive - 1] for start, end_exclusive in grouped.get(key, ())]
        for key in CATEGORIES
    }


def segment_manifest_hash(
    grouped: Mapping[str, Sequence[tuple[int, int]]], *, prediction_hash: str, threshold_hash: str
) -> str:
    subject = {
        "interval_semantics": "half_open",
        "prediction_hash": prediction_hash,
        "threshold_hash": threshold_hash,
        "segments": {key: [list(item) for item in grouped.get(key, ())] for key in CATEGORIES},
    }
    encoded = json.dumps(subject, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()
    return hashlib.sha256(encoded).hexdigest()
