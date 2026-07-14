"""Frozen lineage and values-only split helpers shared by TASK-035B stages."""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Any, Mapping

import numpy as np

from experiments.argos_reproduction.expanded_kpi_cohort import REPO_ROOT, read_json, sha256_file, sha256_json


def verified_report(path: Path) -> dict[str, Any]:
    report = read_json(path)
    expected = report.get("report_hash")
    subject = dict(report)
    subject.pop("report_hash", None)
    if expected != sha256_json(subject):
        raise ValueError("TASK035B_SOURCE_REPORT_HASH_MISMATCH")
    return report


def frozen_executable_cohort(config: Mapping[str, Any]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    seen: set[str] = set()
    for cohort, report_key, private_key in (
        ("TASK-035A", "task035a_runtime", "task035a_private_root"),
        ("TASK-035AR", "task035ar_runtime", "task035ar_private_root"),
    ):
        report = verified_report(REPO_ROOT / config["sources"][report_key])
        for item in report["slots"]:
            if item.get("terminal_status") != "executable_rule":
                continue
            rule_hash = str(item["rule_sha256"])
            if rule_hash in seen:
                raise ValueError("TASK035B_COHORT_RULE_HASH_DUPLICATE")
            seen.add(rule_hash)
            rule_path = REPO_ROOT / config["sources"][private_key] / "quarantine" / f"{rule_hash}.py"
            if sha256_file(rule_path) != rule_hash:
                raise ValueError("TASK035B_PRIVATE_RULE_HASH_MISMATCH")
            result.append({
                "rule_sha256": rule_hash,
                "kpi_id": item["kpi_id"],
                "anchor_id": item["anchor_id"],
                "replicate_id": int(item["replicate_id"]),
                "original_slot_id": item["slot_id"],
                "generation_cohort": cohort,
                "_rule_path": rule_path,
            })
    if len(result) != int(config["design"]["executable_rule_count"]):
        raise ValueError("TASK035B_FROZEN_COHORT_COUNT_MISMATCH")
    return sorted(result, key=lambda item: (item["kpi_id"], item["anchor_id"], item["rule_sha256"]))


def save_values_only_split(config: Mapping[str, Any], split: str) -> tuple[dict[str, Path], dict[str, dict[str, Any]]]:
    manifest = verified_report(REPO_ROOT / config["sources"]["kpi_manifest"])
    private = REPO_ROOT / config["private_root"] / split
    private.mkdir(parents=True, exist_ok=True)
    paths: dict[str, Path] = {}
    metadata: dict[str, dict[str, Any]] = {}
    field = "inner_selection_range" if split == "inner" else "outer_validation_range"
    for entry in manifest["per_kpi"]:
        kpi_id = entry["kpi_id"]
        source = REPO_ROOT / config["sources"]["cohort_private_root"] / f"{kpi_id}.npz"
        if sha256_file(source) != entry["converted_private_prefix_hash"]:
            raise ValueError("TASK035B_PRIVATE_PREFIX_HASH_MISMATCH")
        start, end = map(int, entry[field])
        with np.load(source, allow_pickle=False) as data:
            values = np.asarray(data["values"][start:end], dtype=np.float64).reshape(-1, 1)
        target = private / "per_kpi_values" / f"{kpi_id}.npy"
        target.parent.mkdir(parents=True, exist_ok=True)
        np.save(target, values, allow_pickle=False)
        paths[kpi_id] = target
        metadata[kpi_id] = {"input_sha256": sha256_file(target), "input_count": len(values), "split_range": [start, end]}
    return paths, metadata
