"""Select five deterministic anomaly-anchored generation chunks per KPI."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import sys
from typing import Any

import numpy as np

REPO_ROOT_BOOTSTRAP = Path(__file__).resolve().parents[2]
if str(REPO_ROOT_BOOTSTRAP) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT_BOOTSTRAP))

from experiments.argos_reproduction.expanded_kpi_cohort import REPO_ROOT, anomaly_events, read_json, sha256_json, stable_json_bytes, write_json


class AnchorSelectionError(RuntimeError):
    pass


def chunk_hash(values: np.ndarray, labels: np.ndarray, indices: np.ndarray) -> str:
    payload = {"columns": ["value", "label", "index"], "rows": [[float(v), int(l), int(i)] for v, l, i in zip(values, labels, indices)]}
    return hashlib.sha256(stable_json_bytes(payload)).hexdigest()


def select_anchor_chunks(values: np.ndarray, labels: np.ndarray, generation_end: int, *, chunk_size: int, anchor_count: int) -> list[dict[str, Any]]:
    generation_labels = labels[:generation_end]
    events = anomaly_events(generation_labels)
    if len(events) < anchor_count or generation_end < chunk_size:
        raise AnchorSelectionError("TASK035A_INSUFFICIENT_ANCHOR_EVENTS")
    used_hashes: set[str] = set()
    used_events: set[int] = set()
    anchors: list[dict[str, Any]] = []
    for anchor_rank in range(anchor_count):
        target_rank = min(len(events) - 1, math.floor((anchor_rank + 0.5) * len(events) / anchor_count))
        candidates = list(range(target_rank, len(events)))
        chosen: dict[str, Any] | None = None
        for event_index in candidates:
            if event_index in used_events:
                continue
            event_start, event_end = events[event_index]
            event_length = event_end - event_start
            desired = event_start - math.floor((chunk_size - event_length) / 2)
            start = min(max(0, desired), generation_end - chunk_size)
            end = start + chunk_size
            digest = chunk_hash(values[start:end], labels[start:end], np.arange(start, end))
            if digest in used_hashes:
                continue
            chosen = {
                "anchor_rank": anchor_rank,
                "selected_event_rank": event_index,
                "chunk_start": start,
                "chunk_end_exclusive": end,
                "chunk_size": chunk_size,
                "chunk_sha256": digest,
                "normal_point_count": int(np.sum(labels[start:end] == 0)),
                "anomaly_point_count": int(np.sum(labels[start:end] == 1)),
                "anomaly_event_count_in_chunk": len(anomaly_events(labels[start:end])),
                "selected_event_length": event_length,
                "values": values[start:end],
                "labels": labels[start:end],
            }
            used_events.add(event_index)
            used_hashes.add(digest)
            break
        if chosen is None:
            raise AnchorSelectionError("TASK035A_INSUFFICIENT_DISTINCT_ANCHOR_CHUNKS")
        anchors.append(chosen)
    return anchors


def prepare_anchors(config_path: Path) -> dict[str, Any]:
    config = read_json(config_path)
    cohort = read_json(REPO_ROOT / config["reports"]["cohort"])
    if cohort["status"] != "prepared":
        raise AnchorSelectionError("TASK035A_COHORT_NOT_PREPARED")
    private_root = REPO_ROOT / config["private_root"]
    entries: list[dict[str, Any]] = []
    for item in cohort["per_kpi"]:
        kpi = item["kpi_id"]
        with np.load(private_root / "cohort" / f"{kpi}.npz", allow_pickle=False) as data:
            values = np.asarray(data["values"], dtype=np.float64)
            labels = np.asarray(data["labels"], dtype=np.int8)
        anchors = select_anchor_chunks(values, labels, item["generation_range"][1], chunk_size=int(config["design"]["chunk_size"]), anchor_count=int(config["design"]["anchors_per_kpi"]))
        for anchor in anchors:
            anchor_id = f"ANCHOR-{len(entries)+1:03d}"
            private = private_root / "anchors" / kpi / f"{anchor_id}.npz"
            private.parent.mkdir(parents=True, exist_ok=True)
            np.savez(private, values=anchor.pop("values"), labels=anchor.pop("labels"), indices=np.arange(anchor["chunk_start"], anchor["chunk_end_exclusive"], dtype=np.int64))
            entry = {
                "anchor_id": anchor_id,
                "kpi_id": kpi,
                **anchor,
                "generation_split_hash": item["split_manifest_hash"],
            }
            entries.append(entry)
    manifest = {
        "schema_version": "1.0", "task_id": "TASK-035A", "artifact_type": "anchor_manifest",
        "status": "prepared", "anchor_count": len(entries), "anchors": entries,
        "raw_chunks_tracked": False, "sealed_test_accessed": False,
    }
    manifest["report_hash"] = sha256_json(manifest)
    write_json(REPO_ROOT / config["reports"]["anchors"], manifest)
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="configs/argos_reproduction/task035a_expanded_rule_cohort.json")
    args = parser.parse_args()
    result = prepare_anchors((REPO_ROOT / args.config).resolve())
    print(json.dumps({"status": result["status"], "anchor_count": result["anchor_count"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
