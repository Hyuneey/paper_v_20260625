"""Verify TASK-037B generation-error lineage and expose generation-only cells."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
from pathlib import Path
import sys
from typing import Any, Mapping

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from experiments.argos_reproduction.expanded_kpi_cohort import (
    read_json,
    sha256_file,
    sha256_json,
    write_json,
)
from experiments.argos_reproduction.kpi_detector_split_guard import (
    FrozenKpiSplit,
    load_frozen_splits,
    private_prefix_path,
)


class DetectorErrorSupportError(RuntimeError):
    """Raised when frozen detector-error lineage cannot be trusted."""


@dataclass(frozen=True)
class GenerationErrorCell:
    variant: str
    kpi_id: str
    split_manifest_hash: str
    values: np.ndarray
    labels: np.ndarray
    predictions: np.ndarray
    prediction_hash: str
    threshold_hash: str
    segment_manifest_hash: str
    segments: Mapping[str, tuple[tuple[int, int], ...]]


def _verified_report(path: Path, expected_hash: str) -> dict[str, Any]:
    report = read_json(path)
    subject = dict(report)
    actual = subject.pop("report_hash", None)
    if actual != expected_hash or actual != sha256_json(subject):
        raise DetectorErrorSupportError("TASK037D_SOURCE_REPORT_HASH_MISMATCH")
    return report


def _verified_segment_manifest(path: Path, expected_hash: str) -> dict[str, Any]:
    manifest = read_json(path)
    actual = manifest.get("segment_manifest_hash")
    subject = {
        "interval_semantics": manifest.get("interval_semantics"),
        "prediction_hash": manifest.get("prediction_hash"),
        "threshold_hash": manifest.get("threshold_hash"),
        "segments": manifest.get("segments"),
    }
    if actual != expected_hash or actual != sha256_json(subject):
        raise DetectorErrorSupportError("TASK037D_SEGMENT_MANIFEST_HASH_MISMATCH")
    return manifest


def _validate_segments(
    segments: Mapping[str, Any], length: int
) -> dict[str, tuple[tuple[int, int], ...]]:
    result: dict[str, tuple[tuple[int, int], ...]] = {}
    for category in ("TP", "FN", "FP", "TN"):
        rows = tuple((int(item[0]), int(item[1])) for item in segments.get(category, ()))
        if any(start < 0 or start >= end or end > length for start, end in rows):
            raise DetectorErrorSupportError("TASK037D_SEGMENT_RANGE_INVALID")
        if any(left[1] > right[0] for left, right in zip(rows, rows[1:])):
            raise DetectorErrorSupportError("TASK037D_SEGMENT_ORDER_INVALID")
        result[category] = rows
    return result


def load_generation_cells(config: Mapping[str, Any]) -> tuple[GenerationErrorCell, ...]:
    task037b = read_json(ROOT / str(config["sources"]["task037b_config"]))
    splits = load_frozen_splits(task037b)
    if len(splits) != int(config["design"]["kpi_count"]):
        raise DetectorErrorSupportError("TASK037D_KPI_COUNT_INVALID")
    expected_variants = tuple(config["detector_variants"])
    artifact_report = _verified_report(
        ROOT / str(config["sources"]["detector_artifact_manifest"]),
        str(config["source_hashes"]["detector_artifact_manifest"]),
    )
    _verified_report(
        ROOT / str(config["sources"]["detector_error_report"]),
        str(config["source_hashes"]["detector_error_report"]),
    )
    threshold_report = _verified_report(
        ROOT / str(config["sources"]["detector_threshold_freeze"]),
        str(config["source_hashes"]["detector_threshold_freeze"]),
    )
    records = {
        (str(item["detector_variant"]), str(item["kpi_id"])): item
        for item in artifact_report["records"]
    }
    threshold_hashes = {
        (str(item["detector_variant"]), str(item["kpi_id"])): str(
            item["threshold_record_hash"]
        )
        for item in threshold_report["records"]
    }
    cells: list[GenerationErrorCell] = []
    for variant in expected_variants:
        for frozen in splits:
            record = records.get((variant, frozen.kpi_id))
            if record is None:
                raise DetectorErrorSupportError("TASK037D_DETECTOR_RECORD_MISSING")
            if record["split_manifest_hash"] != frozen.split_manifest_hash:
                raise DetectorErrorSupportError("TASK037D_SPLIT_HASH_MISMATCH")
            seed = str(record["seed"])
            unit = (
                ROOT
                / str(config["sources"]["detector_private_root"])
                / variant
                / frozen.kpi_id
                / seed
            )
            prediction_path = unit / "predictions/generation_prediction.npy"
            if sha256_file(prediction_path) != record["generation_prediction_hash"]:
                raise DetectorErrorSupportError("TASK037D_PREDICTION_HASH_MISMATCH")
            predictions = np.asarray(
                np.load(prediction_path, allow_pickle=False), dtype=np.int8
            )
            start, end = frozen.generation_range
            with np.load(private_prefix_path(task037b, frozen), allow_pickle=False) as source:
                values = np.asarray(source["values"][start:end], dtype=np.float64)
                labels = np.asarray(source["labels"][start:end], dtype=np.int8)
            if (
                values.ndim != 1
                or labels.shape != values.shape
                or predictions.shape != values.shape
                or not np.all(np.isfinite(values))
                or not np.all(np.isin(labels, (0, 1)))
                or not np.all(np.isin(predictions, (0, 1)))
            ):
                raise DetectorErrorSupportError("TASK037D_GENERATION_ARRAY_INVALID")
            segment_path = unit / "error_segments/generation.private.json"
            segment = _verified_segment_manifest(
                segment_path, str(record["incorrect_indices_generation_hash"])
            )
            if (
                segment["prediction_hash"] != record["generation_prediction_hash"]
                or segment["detector_variant"] != variant
                or segment["kpi_id"] != frozen.kpi_id
            ):
                raise DetectorErrorSupportError("TASK037D_SEGMENT_BINDING_MISMATCH")
            segments = _validate_segments(segment["segments"], len(values))
            cells.append(
                GenerationErrorCell(
                    variant=variant,
                    kpi_id=frozen.kpi_id,
                    split_manifest_hash=frozen.split_manifest_hash,
                    values=values,
                    labels=labels,
                    predictions=predictions,
                    prediction_hash=str(record["generation_prediction_hash"]),
                    threshold_hash=threshold_hashes[(variant, frozen.kpi_id)],
                    segment_manifest_hash=str(record["incorrect_indices_generation_hash"]),
                    segments=segments,
                )
            )
    if len(cells) != 20:
        raise DetectorErrorSupportError("TASK037D_CELL_LINEAGE_INCOMPLETE")
    return tuple(cells)


def aligned_contrast_starts(
    cell: GenerationErrorCell, direction: str, chunk_size: int
) -> tuple[int, ...]:
    starts: list[int] = []
    for start in range(0, len(cell.values) - chunk_size + 1, chunk_size):
        end = start + chunk_size
        truth = cell.labels[start:end]
        prediction = cell.predictions[start:end]
        if direction == "FN":
            eligible = bool(np.all(truth == 0) and np.all(prediction == 0))
        elif direction == "FP":
            eligible = bool(np.any((truth == 1) & (prediction == 1)))
        else:
            raise DetectorErrorSupportError("TASK037D_DIRECTION_INVALID")
        if eligible:
            starts.append(start)
    return tuple(starts)


def audit_support(config_path: Path) -> dict[str, Any]:
    config = read_json(config_path)
    chunk_size = int(config["design"]["chunk_size"])
    cells = load_generation_cells(config)
    rows: list[dict[str, Any]] = []
    for cell in cells:
        for direction, target_category in (("FN", "FN"), ("FP", "FP")):
            segments = cell.segments[target_category]
            points = sum(end - start for start, end in segments)
            contrast_starts = aligned_contrast_starts(cell, direction, chunk_size)
            if points == 0:
                state = "not_applicable_zero_detector_error"
            elif not contrast_starts:
                state = "insufficient_contrast_support"
            else:
                state = "support_present_target_selection_pending"
            rows.append(
                {
                    "detector_variant": cell.variant,
                    "kpi_id": cell.kpi_id,
                    "direction": direction,
                    "split_manifest_hash": cell.split_manifest_hash,
                    "target_prediction_hash": cell.prediction_hash,
                    "target_segment_manifest_hash": cell.segment_manifest_hash,
                    "target_segment_count": len(segments),
                    "target_point_count": points,
                    "eligible_contrast_chunk_count": len(contrast_starts),
                    "eligible_target_chunk_count": 0,
                    "registered_slot_count": 0,
                    "support_state": state,
                    "generation_only": True,
                }
            )
    report = {
        "schema_version": "1.0",
        "task_id": "TASK-037D",
        "artifact_type": "error_conditioned_support_report",
        "potential_cell_count": len(rows),
        "detector_variants": list(config["detector_variants"]),
        "directions": list(config["directions"]),
        "cells": rows,
        "test_accessed": False,
        "inner_accessed": False,
        "outer_accessed": False,
        "raw_segments_tracked": False,
    }
    report["report_hash"] = sha256_json(report)
    write_json(ROOT / str(config["reports"]["support"]), report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        default="configs/argos_reproduction/task037d_error_conditioned_rules.json",
    )
    args = parser.parse_args()
    report = audit_support((ROOT / args.config).resolve())
    print(
        json.dumps(
            {
                "potential_cell_count": report["potential_cell_count"],
                "supported_cells": sum(
                    row["support_state"] == "support_present_target_selection_pending"
                    for row in report["cells"]
                ),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
