"""Fail-closed access to the frozen TASK-035B KPI prefix splits."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

import numpy as np

from experiments.argos_reproduction.expanded_kpi_cohort import (
    REPO_ROOT,
    read_json,
    sha256_file,
    sha256_json,
)


ALLOWED_SPLITS = ("generation", "inner", "outer")
RANGE_FIELDS = {
    "generation": "generation_range",
    "inner": "inner_selection_range",
    "outer": "outer_validation_range",
}


class KpiDetectorSplitGuardError(RuntimeError):
    pass


@dataclass(frozen=True)
class FrozenKpiSplit:
    kpi_id: str
    split_manifest_hash: str
    prefix_hash: str
    generation_range: tuple[int, int]
    inner_range: tuple[int, int]
    outer_range: tuple[int, int]
    sealed_test_range: tuple[int, int]


def _verified_report(path: Path) -> dict[str, Any]:
    report = read_json(path)
    subject = dict(report)
    expected = subject.pop("report_hash", None)
    if expected != sha256_json(subject):
        raise KpiDetectorSplitGuardError("TASK037B_SOURCE_REPORT_HASH_MISMATCH")
    return report


def load_frozen_splits(config: Mapping[str, Any]) -> tuple[FrozenKpiSplit, ...]:
    report = _verified_report(REPO_ROOT / str(config["sources"]["kpi_manifest"]))
    expected = config["frozen_kpi_splits"]
    if report.get("selected_kpi_ids") != [item["kpi_id"] for item in expected]:
        raise KpiDetectorSplitGuardError("TASK037B_KPI_ORDER_MISMATCH")
    by_kpi = {item["kpi_id"]: item for item in report["per_kpi"]}
    result: list[FrozenKpiSplit] = []
    for frozen in expected:
        source = by_kpi.get(frozen["kpi_id"])
        if source is None or source["split_manifest_hash"] != frozen["split_manifest_hash"]:
            raise KpiDetectorSplitGuardError("TASK037B_SPLIT_HASH_MISMATCH")
        if source["test_values_parsed"] or source["test_labels_parsed"]:
            raise KpiDetectorSplitGuardError("TASK037B_PRIOR_TEST_ACCESS_INVALID")
        result.append(
            FrozenKpiSplit(
                kpi_id=str(source["kpi_id"]),
                split_manifest_hash=str(source["split_manifest_hash"]),
                prefix_hash=str(source["converted_private_prefix_hash"]),
                generation_range=tuple(source["generation_range"]),
                inner_range=tuple(source["inner_selection_range"]),
                outer_range=tuple(source["outer_validation_range"]),
                sealed_test_range=tuple(source["sealed_test_range"]),
            )
        )
    if len(result) != 10:
        raise KpiDetectorSplitGuardError("TASK037B_REQUIRES_TEN_KPIS")
    return tuple(result)


def assert_split_allowed(split: str) -> None:
    if split not in ALLOWED_SPLITS:
        raise KpiDetectorSplitGuardError("TASK037B_SEALED_TEST_ACCESS_PROHIBITED")


def _range(frozen: FrozenKpiSplit, split: str) -> tuple[int, int]:
    assert_split_allowed(split)
    return {
        "generation": frozen.generation_range,
        "inner": frozen.inner_range,
        "outer": frozen.outer_range,
    }[split]


def private_prefix_path(config: Mapping[str, Any], frozen: FrozenKpiSplit) -> Path:
    path = REPO_ROOT / str(config["sources"]["cohort_private_root"]) / f"{frozen.kpi_id}.npz"
    if not path.is_file() or sha256_file(path) != frozen.prefix_hash:
        raise KpiDetectorSplitGuardError("TASK037B_PRIVATE_PREFIX_HASH_MISMATCH")
    return path


def materialize_split_values(
    config: Mapping[str, Any], frozen: FrozenKpiSplit, split: str, target: Path
) -> dict[str, Any]:
    start, end = _range(frozen, split)
    with np.load(private_prefix_path(config, frozen), allow_pickle=False) as source:
        values = np.asarray(source["values"][start:end], dtype=np.float64)
    if values.ndim != 1 or len(values) != end - start or not np.all(np.isfinite(values)):
        raise KpiDetectorSplitGuardError("TASK037B_SPLIT_VALUES_INVALID")
    target.parent.mkdir(parents=True, exist_ok=True)
    np.save(target, values, allow_pickle=False)
    return {
        "kpi_id": frozen.kpi_id,
        "split": split,
        "range": [start, end],
        "input_count": len(values),
        "input_hash": sha256_file(target),
        "labels_loaded": False,
        "test_accessed": False,
    }


def load_split_labels_after_freeze(
    config: Mapping[str, Any],
    frozen: FrozenKpiSplit,
    split: str,
    *,
    prediction_freeze: Mapping[str, Any],
) -> np.ndarray:
    start, end = _range(frozen, split)
    if prediction_freeze.get("split") != split:
        raise KpiDetectorSplitGuardError("TASK037B_PREDICTION_FREEZE_SPLIT_MISMATCH")
    if prediction_freeze.get("kpi_id") != frozen.kpi_id:
        raise KpiDetectorSplitGuardError("TASK037B_PREDICTION_FREEZE_KPI_MISMATCH")
    if prediction_freeze.get("prediction_frozen_before_labels") is not True:
        raise KpiDetectorSplitGuardError("TASK037B_LABEL_ACCESS_BEFORE_FREEZE")
    with np.load(private_prefix_path(config, frozen), allow_pickle=False) as source:
        labels = np.asarray(source["labels"][start:end], dtype=np.int8)
    if labels.ndim != 1 or len(labels) != end - start or not np.all(np.isin(labels, (0, 1))):
        raise KpiDetectorSplitGuardError("TASK037B_SPLIT_LABELS_INVALID")
    return labels


def frozen_split_ledger(config: Mapping[str, Any]) -> list[dict[str, str]]:
    return [
        {"kpi_id": item.kpi_id, "split_manifest_hash": item.split_manifest_hash}
        for item in load_frozen_splits(config)
    ]
