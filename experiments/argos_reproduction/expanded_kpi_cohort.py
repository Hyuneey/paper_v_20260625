"""Prepare the TASK-035A KPI cohort without parsing sealed-test values or labels."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
import hashlib
import json
from pathlib import Path
import subprocess
from typing import Any, Iterable, Mapping

import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[2]


class ExpandedKpiCohortError(RuntimeError):
    """Fail-closed cohort preparation error."""


def stable_json_bytes(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("utf-8")


def sha256_json(value: object) -> str:
    return hashlib.sha256(stable_json_bytes(value)).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8-sig") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ExpandedKpiCohortError("TASK035A_JSON_OBJECT_REQUIRED")
    return value


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(stable_json_bytes(value) + b"\n")


def git_clean_commit() -> str:
    status = subprocess.run(["git", "status", "--porcelain"], cwd=REPO_ROOT, capture_output=True, text=True, check=True)
    if status.stdout.strip():
        raise ExpandedKpiCohortError("TASK035A_EXECUTION_WORKTREE_NOT_CLEAN")
    return subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, capture_output=True, text=True, check=True).stdout.strip()


def split_ranges(row_count: int) -> dict[str, list[int]]:
    if row_count <= 0:
        raise ExpandedKpiCohortError("TASK035A_ROW_COUNT_INVALID")
    train_pool_end = int(row_count * 0.7)
    outer_train_end = int(train_pool_end * 0.8)
    generation_end = int(outer_train_end * 5 / 7)
    ranges = {
        "generation": [0, generation_end],
        "inner_selection": [generation_end, outer_train_end],
        "outer_validation": [outer_train_end, train_pool_end],
        "sealed_test": [train_pool_end, row_count],
    }
    ordered = list(ranges.values())
    if ordered[0][0] != 0 or ordered[-1][1] != row_count or any(left[1] != right[0] for left, right in zip(ordered, ordered[1:])):
        raise ExpandedKpiCohortError("TASK035A_SPLIT_NOT_EXHAUSTIVE")
    return ranges


def anomaly_events(labels: np.ndarray) -> list[tuple[int, int]]:
    events: list[tuple[int, int]] = []
    start: int | None = None
    for index, label in enumerate(labels.tolist()):
        if label == 1 and start is None:
            start = index
        elif label == 0 and start is not None:
            events.append((start, index))
            start = None
    if start is not None:
        events.append((start, len(labels)))
    return events


def count_series_rows(csv_path: Path) -> dict[str, int]:
    """First pass: access only the KPI identifier field."""
    counts: Counter[str] = Counter()
    with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames or "KPI ID" not in reader.fieldnames:
            raise ExpandedKpiCohortError("TASK035A_SOURCE_SCHEMA_INVALID")
        for row in reader:
            counts[str(row["KPI ID"])] += 1
    return dict(counts)


def parse_prefix_records(records: Iterable[Mapping[str, object]], counts: Mapping[str, int]) -> dict[str, dict[str, list[object]]]:
    """Second pass: value/label access is guarded by each series test boundary."""
    positions: defaultdict[str, int] = defaultdict(int)
    prefixes: dict[str, dict[str, list[object]]] = {
        kpi: {"value": [], "label": []} for kpi in counts
    }
    for row in records:
        kpi = str(row["KPI ID"])
        position = positions[kpi]
        positions[kpi] += 1
        if kpi not in counts:
            raise ExpandedKpiCohortError("TASK035A_UNKNOWN_KPI")
        test_start = split_ranges(int(counts[kpi]))["sealed_test"][0]
        if position >= test_start:
            continue
        try:
            value = float(row["value"])
            label_value = float(row["label"])
        except (KeyError, TypeError, ValueError) as error:
            raise ExpandedKpiCohortError("TASK035A_PREFIX_ROW_INVALID") from error
        if not np.isfinite(value) or label_value not in (0.0, 1.0):
            raise ExpandedKpiCohortError("TASK035A_PREFIX_VALUE_INVALID")
        prefixes[kpi]["value"].append(value)
        prefixes[kpi]["label"].append(int(label_value))
    if dict(positions) != dict(counts):
        raise ExpandedKpiCohortError("TASK035A_SERIES_COUNT_CHANGED")
    return prefixes


def read_prefixes(csv_path: Path, counts: Mapping[str, int]) -> dict[str, dict[str, list[object]]]:
    with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
        return parse_prefix_records(csv.DictReader(handle), counts)


def _split_summary(labels: np.ndarray) -> dict[str, int]:
    return {
        "normal_count": int(np.sum(labels == 0)),
        "anomaly_count": int(np.sum(labels == 1)),
        "event_count": len(anomaly_events(labels)),
    }


def prepare_cohort(config_path: Path, *, require_clean: bool = True) -> dict[str, Any]:
    config = read_json(config_path)
    execution_commit = git_clean_commit() if require_clean else subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, capture_output=True, text=True, check=True
    ).stdout.strip()
    source = REPO_ROOT / config["source"]["private_train_csv"]
    if not source.is_file():
        raise ExpandedKpiCohortError("TASK035A_PRIVATE_TRAIN_SOURCE_MISSING")
    counts = count_series_rows(source)
    prefixes = read_prefixes(source, counts)
    policy = config["eligibility"]
    private_root = REPO_ROOT / config["private_root"]
    per_kpi_private = private_root / "cohort"
    per_kpi: list[dict[str, Any]] = []
    eligible: list[str] = []
    for kpi in sorted(counts):
        ranges = split_ranges(counts[kpi])
        values = np.asarray(prefixes[kpi]["value"], dtype=np.float64)
        labels = np.asarray(prefixes[kpi]["label"], dtype=np.int8)
        if len(values) != ranges["sealed_test"][0]:
            raise ExpandedKpiCohortError("TASK035A_PREFIX_LENGTH_INVALID")
        summaries: dict[str, dict[str, int]] = {}
        for name in ("generation", "inner_selection", "outer_validation"):
            start, end = ranges[name]
            summaries[name] = _split_summary(labels[start:end])
        is_eligible = (
            counts[kpi] >= int(policy["minimum_total_rows"])
            and summaries["generation"]["normal_count"] > 0
            and summaries["generation"]["anomaly_count"] > 0
            and summaries["generation"]["event_count"] >= int(policy["generation_minimum_events"])
            and summaries["inner_selection"]["normal_count"] > 0
            and summaries["inner_selection"]["anomaly_count"] > 0
            and summaries["inner_selection"]["event_count"] >= int(policy["inner_minimum_events"])
            and summaries["outer_validation"]["normal_count"] > 0
            and summaries["outer_validation"]["anomaly_count"] > 0
            and summaries["outer_validation"]["event_count"] >= int(policy["outer_minimum_events"])
        )
        if is_eligible:
            eligible.append(kpi)
        private_path = per_kpi_private / f"{kpi}.npz"
        private_path.parent.mkdir(parents=True, exist_ok=True)
        np.savez(private_path, values=values, labels=labels)
        split_payload = {"kpi_id": kpi, "ranges": ranges, "row_count": counts[kpi]}
        per_kpi.append({
            "kpi_id": kpi,
            "total_row_count": counts[kpi],
            "generation_range": ranges["generation"],
            "inner_selection_range": ranges["inner_selection"],
            "outer_validation_range": ranges["outer_validation"],
            "sealed_test_range": ranges["sealed_test"],
            "generation_normal_count": summaries["generation"]["normal_count"],
            "generation_anomaly_count": summaries["generation"]["anomaly_count"],
            "generation_event_count": summaries["generation"]["event_count"],
            "inner_normal_count": summaries["inner_selection"]["normal_count"],
            "inner_anomaly_count": summaries["inner_selection"]["anomaly_count"],
            "inner_event_count": summaries["inner_selection"]["event_count"],
            "outer_normal_count": summaries["outer_validation"]["normal_count"],
            "outer_anomaly_count": summaries["outer_validation"]["anomaly_count"],
            "outer_event_count": summaries["outer_validation"]["event_count"],
            "converted_private_prefix_hash": sha256_file(private_path),
            "split_manifest_hash": sha256_json(split_payload),
            "maximum_value_label_position_parsed": ranges["sealed_test"][0] - 1,
            "test_values_parsed": False,
            "test_labels_parsed": False,
            "eligible": is_eligible,
        })
    selected = eligible[: int(config["design"]["kpi_count"])]
    status = "prepared" if len(selected) == int(config["design"]["kpi_count"]) else "failed_kpi_cohort_eligibility"
    manifest = {
        "schema_version": "1.0",
        "task_id": "TASK-035A",
        "artifact_type": "kpi_cohort_manifest",
        "status": status,
        "execution_code_commit": execution_commit,
        "source_package_sha256": sha256_file(source),
        "selected_kpi_ids": selected,
        "selection_order": "lexicographic_first_ten_eligible",
        "selection_policy_hash": sha256_json(policy),
        "per_kpi": [item for item in per_kpi if item["kpi_id"] in selected],
        "eligible_kpi_count": len(eligible),
        "test_value_field_accessed": False,
        "test_label_field_accessed": False,
        "phase2_ground_truth_accessed": False,
    }
    manifest["report_hash"] = sha256_json(manifest)
    write_json(REPO_ROOT / config["reports"]["cohort"], manifest)
    write_json(private_root / "execution_receipt.json", {"execution_code_commit": execution_commit, "source_hash": manifest["source_package_sha256"]})
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="configs/argos_reproduction/task035a_expanded_rule_cohort.json")
    parser.add_argument("--allow-dirty-for-tests", action="store_true")
    args = parser.parse_args()
    result = prepare_cohort((REPO_ROOT / args.config).resolve(), require_clean=not args.allow_dirty_for_tests)
    print(json.dumps({"status": result["status"], "selected_kpi_count": len(result["selected_kpi_ids"])}))
    return 0 if result["status"] == "prepared" else 2


if __name__ == "__main__":
    raise SystemExit(main())
