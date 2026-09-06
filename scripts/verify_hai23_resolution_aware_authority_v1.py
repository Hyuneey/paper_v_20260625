"""Independent replay for the private HAI23 resolution-aware authority."""

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


SUMMARY_RECORD = re.compile(r"^\[\s*\d+\]")
DATETIME = re.compile(r"\d{4}-\d\d-\d\d \d\d:\d\d:\d\d")
ID = re.compile(r"A2\d{2}")


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


def digest(value: Any) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def read_authority(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    claimed = value.pop("self_hash")
    if digest(value) != claimed:
        raise ValueError("PRIVATE_AUTHORITY_SELF_HASH_MISMATCH")
    return {**value, "self_hash": claimed}


def summary(path: Path) -> list[tuple[str, str, int]]:
    output: list[tuple[str, str, int]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not SUMMARY_RECORD.match(line):
            continue
        values = DATETIME.findall(line)
        if len(values) != 2:
            raise ValueError("INDEPENDENT_SUMMARY_PARSE_FAILURE")
        start, end = map(datetime.fromisoformat, values)
        output.append((values[0], values[1], int((end - start).total_seconds())))
    return output


def labels(path: Path) -> list[tuple[str, str]]:
    output: list[tuple[str, str]] = []
    with path.open(encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames != ["timestamp", "label"]:
            raise ValueError("INDEPENDENT_LABEL_SCHEMA_FAILURE")
        selected = ((row["timestamp"], row["label"] == "1") for row in reader)
        started: str | None = None
        ended: str | None = None
        for timestamp, positive in selected:
            if positive:
                started = timestamp if started is None else started
                ended = timestamp
            elif started is not None:
                output.append((started, ended or started))
                started = ended = None
        if started is not None:
            output.append((started, ended or started))
    return output


def minute(value: str) -> str:
    instant = datetime.fromisoformat(value)
    return f"{instant:%Y-%m-%d} {instant.hour}:{instant.minute:02d}"


def table_rows(page: Any) -> list[list[str | None]]:
    return next(table[2:] for table in page.extract_tables() if table and "ID" in table[0])


def manual(manual_path: Path) -> dict[str, tuple[str, int, tuple[str, ...]]]:
    output: dict[str, tuple[str, int, tuple[str, ...]]] = {}
    active_id: str | None = None
    active_targets: list[str] = []

    def close() -> None:
        nonlocal active_id, active_targets
        if active_id is not None:
            start, duration, _ = output[active_id]
            output[active_id] = (start, duration, tuple(active_targets))
        active_id = None
        active_targets = []

    with pdfplumber.open(manual_path) as document:
        for page_number in (31, 32):
            for row in table_rows(document.pages[page_number]):
                compact = [cell.strip() for cell in row if cell and cell.strip()]
                identifiers = [cell for cell in compact if ID.fullmatch(cell)]
                if identifiers:
                    close()
                    if len(identifiers) != 1 or len(compact) < 7:
                        raise ValueError("INDEPENDENT_MANUAL_PARSE_FAILURE")
                    active_id = identifiers[0]
                    time = compact[-2]
                    duration = compact[-1]
                    if not re.fullmatch(r"\d{1,2}:\d{2}", time) or not duration.isdigit():
                        raise ValueError("INDEPENDENT_MANUAL_PARSE_FAILURE")
                    output[active_id] = (time, int(duration), ())
                    active_targets.extend(part.strip() for part in compact[4].split(","))
                elif active_id is not None and len(compact) == 3:
                    active_targets.extend(part.strip() for part in compact[2].split(","))
        close()
    if len(output) != 38 or any(not targets for _, _, targets in output.values()):
        raise ValueError("INDEPENDENT_MANUAL_CENSUS_FAILURE")
    return output


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--official-root", type=Path, required=True)
    parser.add_argument("--private-authority", type=Path, required=True)
    args = parser.parse_args()
    authority = read_authority(args.private_authority)
    root = args.official_root / "hai-23.05"
    test1_summary, test1_labels = summary(root / "summary_label1.txt"), labels(root / "label-test1.csv")
    test2_summary, test2_labels = summary(root / "summary_label2.txt"), labels(root / "label-test2.csv")
    if [(a, b) for a, b, _ in test1_summary] != test1_labels or len(test1_summary) != 14:
        raise ValueError("INDEPENDENT_TEST1_CONTROL_FAILURE")
    coarse = [(minute(start), minute(end)) for start, end, _ in test2_summary]
    if len(test2_summary) != 38 or coarse != test2_labels or len(set(coarse)) != 38:
        raise ValueError("INDEPENDENT_NATIVE_RESOLUTION_FAILURE")
    manual_rows = manual(args.official_root / "hai_dataset_technical_details.pdf")
    by_key: defaultdict[tuple[str, int], list[tuple[str, str, int]]] = defaultdict(list)
    for record in test2_summary:
        start = datetime.fromisoformat(record[0])
        by_key[(f"{start.hour}:{start.minute:02d}", record[2])].append(record)
    reconstructed: list[dict[str, Any]] = []
    for identifier in sorted(manual_rows):
        start, duration, targets = manual_rows[identifier]
        matches = by_key[(start, duration)]
        if len(matches) != 1:
            raise ValueError("INDEPENDENT_MANUAL_SUMMARY_JOIN_FAILURE")
        interval = matches[0]
        reconstructed.append({"scenario_id": f"HAI23_05:{identifier}", "closed_intervals": [{"start": interval[0], "end": interval[1]}], "attacked_identities": list(targets)})
    observed = [{key: record[key] for key in ("scenario_id", "closed_intervals", "attacked_identities")} for record in authority["canonical_records"]]
    if reconstructed != observed:
        raise ValueError("INDEPENDENT_CANONICAL_RECORD_MISMATCH")
    receipt = {"schema": "hai23_resolution_aware_independent_replay_receipt_v1", "test1_exact": 14, "test2_native_resolution": 38, "manual_summary_unique": 38, "canonical_records": 38, "private_authority_hash": authority["self_hash"], "verdict": "PASS"}
    receipt["self_hash"] = digest(receipt)
    print(json.dumps(receipt, sort_keys=True))


if __name__ == "__main__":
    main()
