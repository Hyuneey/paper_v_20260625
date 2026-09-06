"""Build the private HAI23 resolution-aware scenario authority.

This audit-only builder is deliberately not a DG-05 adapter.  It reads only
the four official HAI23 ground-truth metadata payloads and the official manual,
preserves summary seconds as canonical endpoints, and uses label ranges only
for coarse native-resolution corroboration.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

import pdfplumber


EXPECTED: dict[str, tuple[str, int]] = {
    "summary_label1.txt": ("9d8fb32ee1e816c88f93c8d661f90a7736802582d3572a1e1ebd953783353da6", 1591),
    "label-test1.csv": ("eaf69edb9c5834bc393afd7bf658b5e408d34fd7bfc3261f80516765fb818fbc", 1242017),
    "summary_label2.txt": ("b564024a105981415a81dd1b338a48ad7ad5be511849884232540f1a6550e5c1", 2911),
    "label-test2.csv": ("8090c44981176e39b0f01a7126a80248ac0b93355c00f9db4d4e2f2106452b92", 4500018),
}
MANUAL_SHA256 = "0668345c4e80331b918fe17c81f8f363b13bd22886831d286e761bc62b71a556"
MANUAL_BLOB = "18cb88514176e1c641f584cf24ac8e9559432b38"
TIMESTAMP = re.compile(r"\d{4}-\d\d-\d\d \d\d:\d\d:\d\d")
SUMMARY_LINE = re.compile(r"^\[\s*(\d+)\]\s+")
MANUAL_ID = re.compile(r"^A2\d{2}$")


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


def self_hashed(value: dict[str, Any]) -> dict[str, Any]:
    body = dict(value)
    body.pop("self_hash", None)
    return {**body, "self_hash": hashlib.sha256(canonical_bytes(body)).hexdigest()}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def checked_payloads(root: Path) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for name, (expected_hash, expected_size) in EXPECTED.items():
        path = root / "hai-23.05" / name
        if not path.is_file() or path.stat().st_size != expected_size or sha256(path) != expected_hash:
            raise ValueError(f"HAI23_GROUND_TRUTH_PAYLOAD_IDENTITY_MISMATCH:{name}")
        result[name] = {"sha256": expected_hash, "byte_size": expected_size}
    return result


def summary_records(path: Path) -> tuple[int, list[dict[str, Any]]]:
    declared: int | None = None
    records: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip().startswith("Attacks"):
            match = re.search(r"(\d+)\s+times", line)
            if match is None:
                raise ValueError("INVALID_SUMMARY_DECLARED_COUNT")
            declared = int(match.group(1))
        match = SUMMARY_LINE.match(line)
        if match is None:
            continue
        points = TIMESTAMP.findall(line)
        if len(points) != 2:
            raise ValueError("INVALID_SUMMARY_INTERVAL")
        start, end = map(datetime.fromisoformat, points)
        if end < start:
            raise ValueError("INVALID_SUMMARY_INTERVAL_ORDER")
        records.append({"ordinal": int(match.group(1)), "start": points[0], "end": points[1], "duration_seconds": int((end - start).total_seconds())})
    if declared is None or not records or len({(r["start"], r["end"]) for r in records}) != len(records):
        raise ValueError("INVALID_SUMMARY_RECORD_SET")
    return declared, records


def label_ranges(path: Path) -> list[tuple[str, str]]:
    with path.open(encoding="utf-8", newline="") as stream:
        reader = csv.reader(stream)
        header = next(reader)
        if header != ["timestamp", "label"]:
            raise ValueError("UNEXPECTED_LABEL_SCHEMA")
        ranges: list[tuple[str, str]] = []
        active_start: str | None = None
        active_end: str | None = None
        for row in reader:
            if len(row) != 2 or row[1] not in {"0", "1"}:
                raise ValueError("INVALID_LABEL_ROW")
            timestamp, positive = row[0], row[1] == "1"
            if positive and active_start is None:
                active_start = timestamp
            if positive:
                active_end = timestamp
            if not positive and active_start is not None:
                ranges.append((active_start, active_end or active_start))
                active_start = active_end = None
        if active_start is not None:
            ranges.append((active_start, active_end or active_start))
    return ranges


def native_minute(timestamp: str) -> str:
    value = datetime.fromisoformat(timestamp)
    return f"{value:%Y-%m-%d} {value.hour}:{value.minute:02d}"


def table_with_manual_rows(page: Any) -> list[list[str | None]]:
    for table in page.extract_tables():
        if table and any(cell == "ID" for cell in table[0] if cell):
            return table[2:]
    raise ValueError("MANUAL_TABLE_NOT_FOUND")


def manual_records(manual: Path) -> list[dict[str, Any]]:
    if sha256(manual) != MANUAL_SHA256:
        raise ValueError("MANUAL_PAYLOAD_HASH_MISMATCH")
    records: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    with pdfplumber.open(manual) as document:
        for page_index in (31, 32):
            for row in table_with_manual_rows(document.pages[page_index]):
                cells = [cell.strip() if cell else "" for cell in row]
                candidate_ids = [cell for cell in cells if MANUAL_ID.fullmatch(cell)]
                if candidate_ids:
                    if len(candidate_ids) != 1:
                        raise ValueError("AMBIGUOUS_MANUAL_ID")
                    id_column = cells.index(candidate_ids[0])
                    target_column = id_column + 9
                    trailing = cells[target_column + 1 :]
                    time_column = next((index + target_column + 1 for index, cell in enumerate(trailing) if re.fullmatch(r"\d{1,2}:\d{2}", cell)), None)
                    if time_column is None:
                        raise ValueError("INVALID_MANUAL_START")
                    duration_column = next((index + time_column + 1 for index, cell in enumerate(cells[time_column + 1 :]) if re.fullmatch(r"\d+", cell)), None)
                    if duration_column is None:
                        raise ValueError("INVALID_MANUAL_DURATION")
                    current = {
                        "manual_id": candidate_ids[0],
                        "scenario_components": [cells[id_column + 3]],
                        "target_controller_components": [cells[id_column + 6]],
                        "target_point_components": [cells[target_column]],
                        "target_column": target_column,
                        "manual_start_minute": cells[time_column],
                        "manual_duration_seconds": int(cells[duration_column]),
                    }
                    if not re.fullmatch(r"\d{1,2}:\d{2}", current["manual_start_minute"]):
                        raise ValueError("INVALID_MANUAL_START")
                    records.append(current)
                elif current is not None:
                    compact = [cell for cell in cells if cell]
                    if len(compact) == 3:
                        current["scenario_components"].append(compact[0])
                        current["target_controller_components"].append(compact[1])
                        current["target_point_components"].append(compact[2])
    if len(records) != 38 or len({row["manual_id"] for row in records}) != 38:
        raise ValueError("HAI23_MANUAL_CENSUS_MISMATCH")
    for row in records:
        row.pop("target_column")
        targets = [part.strip() for component in row["target_point_components"] for part in component.split(",")]
        if not targets or any(not part for part in targets):
            raise ValueError("HAI23_TARGET_IDENTITY_FOLLOWUP_REQUIRED")
        row["attacked_identities"] = targets
    return records


def build(root: Path) -> dict[str, Any]:
    payloads = checked_payloads(root)
    manual = root / "hai_dataset_technical_details.pdf"
    test1_declared, test1_summary = summary_records(root / "hai-23.05" / "summary_label1.txt")
    test2_declared, test2_summary = summary_records(root / "hai-23.05" / "summary_label2.txt")
    test1_labels = label_ranges(root / "hai-23.05" / "label-test1.csv")
    test2_labels = label_ranges(root / "hai-23.05" / "label-test2.csv")
    if len(test1_summary) != len(test1_labels) != 14 or [(r["start"], r["end"]) for r in test1_summary] != test1_labels:
        raise ValueError("HAI23_TEST1_CONTROL_AUTHORITY_INCONSISTENT")
    if len(test2_summary) != 38 or len(test2_labels) != 38:
        raise ValueError("HAI23_TEST2_CENSUS_MISMATCH")
    coarse = [(native_minute(record["start"]), native_minute(record["end"])) for record in test2_summary]
    if coarse != test2_labels or len(set(coarse)) != 38 or len(set(test2_labels)) != 38:
        raise ValueError("HAI23_NATIVE_RESOLUTION_JOIN_AMBIGUOUS")
    manual_rows = manual_records(manual)
    candidates: defaultdict[tuple[str, int], list[dict[str, Any]]] = defaultdict(list)
    for summary in test2_summary:
        start = datetime.fromisoformat(summary["start"])
        candidates[(f"{start.hour}:{start.minute:02d}", summary["duration_seconds"])].append(summary)
    records: list[dict[str, Any]] = []
    used: set[int] = set()
    for row in manual_rows:
        matched = candidates[(row["manual_start_minute"], row["manual_duration_seconds"])]
        if len(matched) != 1 or matched[0]["ordinal"] in used:
            raise ValueError("HAI23_MANUAL_SUMMARY_JOIN_AMBIGUOUS")
        summary = matched[0]
        used.add(summary["ordinal"])
        records.append({
            "dataset_version": "23.05",
            "panel_id": "HAI23_TEST2_PRIMARY_HELDOUT_V1",
            "physical_file_id": "HAI23_TEST2",
            "scenario_id": f"HAI23_05:{row['manual_id']}",
            "official_occurrence_id": row["manual_id"],
            "closed_intervals": [{"start": summary["start"], "end": summary["end"]}],
            "attacked_identities": row["attacked_identities"],
            "explicit_affected_processes": [],
            "manual_start_minute": row["manual_start_minute"],
            "manual_duration_seconds": row["manual_duration_seconds"],
            "summary_ordinal": summary["ordinal"],
        })
    if len(records) != 38 or len(used) != 38:
        raise ValueError("HAI23_MANUAL_SUMMARY_JOIN_AMBIGUOUS")
    return self_hashed({
        "schema": "hai23_official_resolution_aware_scenario_authority_private_v1",
        "status": "PRIVATE_CANONICAL_AUTHORITY",
        "roles": {
            "technical_manual": "SCENARIO_IDENTITY_AUTHORITY",
            "enumerated_summary": "EXACT_PHYSICAL_INTERVAL_AUTHORITY",
            "binary_label": "COARSE_GROUND_TRUTH_CORROBORATION_AUTHORITY",
            "README": "PANEL_CENSUS_AUTHORITY",
        },
        "no_precision_upsampling_performed": True,
        "summary_declared_scalar_count": test2_declared,
        "declared_scalar_classification": "INTERNALLY_INCONSISTENT_NON_ENUMERATIVE_METADATA_FIELD",
        "official_source": {"repository_commit": "2a814cebc9a66b06c9e5cd545e2d72e65d383737", "manual_blob": MANUAL_BLOB, "manual_sha256": MANUAL_SHA256, "payloads": payloads},
        "test1_control": {"README": 14, "manual": 14, "summary": len(test1_summary), "label_ranges": len(test1_labels), "exact_matches": len(test1_summary), "declared": test1_declared},
        "test2_corroboration": {"README": 38, "manual": len(manual_rows), "summary": len(test2_summary), "label_ranges": len(test2_labels), "native_resolution_matches": len(coarse), "declared": test2_declared},
        "canonical_records": records,
    })


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--official-root", type=Path, required=True)
    parser.add_argument("--private-output", type=Path, required=True)
    args = parser.parse_args()
    authority = build(args.official_root)
    args.private_output.parent.mkdir(parents=True, exist_ok=True)
    args.private_output.write_bytes(canonical_bytes(authority) + b"\n")
    print(json.dumps({"canonical_records": len(authority["canonical_records"]), "private_authority_hash": authority["self_hash"], "status": "PASS"}, sort_keys=True))


if __name__ == "__main__":
    main()
