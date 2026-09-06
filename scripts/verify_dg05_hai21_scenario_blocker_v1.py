"""Fail-closed verification of the unresolved HAI21 manual-to-label join."""

from __future__ import annotations

import argparse
import gzip
import csv
import hashlib
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

import pdfplumber


MANUAL_SHA256 = "0668345c4e80331b918fe17c81f8f363b13bd22886831d286e761bc62b71a556"
EXPECTED = {1: 5, 2: 20, 3: 8, 4: 5, 5: 12}


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()


def digest(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def manual(path: Path) -> list[dict[str, Any]]:
    if sha(path) != MANUAL_SHA256:
        raise ValueError("OFFICIAL_MANUAL_HASH_MISMATCH")
    result: list[dict[str, Any]] = []
    with pdfplumber.open(path) as document:
        for page_number in range(36, 39):
            for table in document.pages[page_number].extract_tables():
                for source_row in table:
                    row = [value.strip() if value else "" for value in source_row]
                    ids = [value for value in row if re.fullmatch(r"A[1-5][0-9]{2}", value)]
                    if not ids:
                        continue
                    times = [value for value in row if re.fullmatch(r"[0-9]{1,2}:[0-9]{2}", value)]
                    if len(ids) != 1 or len(times) != 1:
                        raise ValueError("HAI21_MANUAL_PARSE_FAILURE")
                    position = row.index(times[0])
                    durations = [int(value) for value in row[position + 1 :] if value.isdecimal()]
                    if len(durations) != 1:
                        raise ValueError("HAI21_MANUAL_DURATION_PARSE_FAILURE")
                    result.append({"id": ids[0], "start_minute": times[0].lstrip("0"), "duration": durations[0]})
    if len(result) != 50 or len({row["id"] for row in result}) != 50:
        raise ValueError("HAI21_MANUAL_CENSUS_MISMATCH")
    return result


def ranges(path: Path) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    with gzip.open(path, "rt", encoding="utf-8", newline="") as stream:
        reader = csv.reader(stream)
        header = next(reader)
        time_index, attack_index = header.index("time"), header.index("attack")
        start: str | None = None
        end: str | None = None
        for row in reader:
            time, attack = row[time_index], row[attack_index]
            if attack == "1" and start is None:
                start = time
            if attack == "1":
                end = time
            if attack == "0" and start is not None:
                output.append({"start": start, "end": end, "duration": int((datetime.fromisoformat(end or start) - datetime.fromisoformat(start)).total_seconds())})
                start = end = None
        if start is not None:
            output.append({"start": start, "end": end, "duration": int((datetime.fromisoformat(end or start) - datetime.fromisoformat(start)).total_seconds())})
    return output


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--official-root", type=Path, required=True)
    parser.add_argument("--public-output", type=Path, required=True)
    args = parser.parse_args()
    manual_rows = manual(args.official_root / "hai_dataset_technical_details.pdf")
    payloads: dict[str, dict[str, Any]] = {}
    failures: list[dict[str, str]] = []
    compatible = 0
    for number, expected in EXPECTED.items():
        file_name = f"test{number}.csv.gz"
        label_path = args.official_root / "hai-21.03" / file_name
        segments = ranges(label_path)
        occurrences = [row for row in manual_rows if row["id"][1] == str(number)]
        if len(segments) != expected or len(occurrences) != expected:
            raise ValueError("HAI21_MANUAL_LABEL_OCCURRENCE_COUNT_MISMATCH")
        payloads[file_name] = {"sha256": sha(label_path), "byte_size": label_path.stat().st_size, "label_range_count": len(segments)}
        for occurrence, segment in zip(occurrences, segments):
            label_minute = f"{datetime.fromisoformat(segment['start']).hour}:{datetime.fromisoformat(segment['start']).minute:02d}"
            if label_minute == occurrence["start_minute"] and segment["duration"] == occurrence["duration"] - 1:
                compatible += 1
            else:
                failures.append({"official_occurrence_id": occurrence["id"], "physical_file_id": f"HAI21_TEST{number}", "mismatch": "OFFICIAL_MANUAL_START_OR_INCLUSIVE_DURATION_INCOMPATIBLE_WITH_OFFICIAL_OVERALL_ATTACK_LABEL_RANGE"})
    body = {
        "schema": "hai21_official_scenario_authority_blocker_receipt_v1",
        "status": "BLOCKED",
        "verdict": "HAI21_MANUAL_LABEL_BOUNDARY_AUTHORITY_CONFLICT",
        "official_manual_sha256": MANUAL_SHA256,
        "label_payloads": payloads,
        "manual_occurrences": 50,
        "label_ranges": sum(item["label_range_count"] for item in payloads.values()),
        "manual_label_compatible_unique_joins": compatible,
        "manual_label_incompatible_occurrence_count": len(failures),
        "incompatible_occurrences": failures,
        "prohibited_resolution": "NO_MANUAL_DURATION_OR_TIMESTAMP_NORMALIZATION; NO_ROW_ORDER_ONLY_JOIN; NO_SCENARIO_AUTHORITY_FROZEN",
        "access_accounting": {"timestamp_and_overall_attack_label_only": True, "feature_values_read": 0, "heldout_predictions_observed": 0, "heldout_metrics_observed": 0},
    }
    body["self_hash"] = digest(body)
    args.public_output.parent.mkdir(parents=True, exist_ok=True)
    args.public_output.write_bytes(canonical_bytes(body) + b"\n")
    print(json.dumps({"status": body["status"], "compatible": compatible, "incompatible": len(failures), "receipt_hash": body["self_hash"]}, sort_keys=True))


if __name__ == "__main__":
    main()
