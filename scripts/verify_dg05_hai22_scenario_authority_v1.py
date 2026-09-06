"""Independent HAI22 source replay; deliberately does not import the builder."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

import pdfplumber


MANUAL_SHA256 = "0668345c4e80331b918fe17c81f8f363b13bd22886831d286e761bc62b71a556"


def canon(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()


def hash_value(value: Any) -> str:
    return hashlib.sha256(canon(value)).hexdigest()


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def manual_rows(path: Path) -> list[dict[str, Any]]:
    if sha(path) != MANUAL_SHA256:
        raise ValueError("OFFICIAL_MANUAL_HASH_MISMATCH")
    id_re, time_re, ap_re = re.compile(r"A[1-4][0-9]{2}"), re.compile(r"[0-9]{1,2}:[0-9]{2}"), re.compile(r"AP[0-9]+")
    rows: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    with pdfplumber.open(path) as pdf:
        for page in range(33, 36):
            for table in pdf.pages[page].extract_tables():
                for raw in table:
                    cells = [item.strip() if item else "" for item in raw]
                    ids = [item for item in cells if id_re.fullmatch(item)]
                    aps = [item for item in cells if ap_re.fullmatch(item)]
                    controllers = [item for item in cells if re.fullmatch(r"P[1-4]-.*", item)]
                    targets = [item for item in cells if re.fullmatch(r"(?:P[1-4]_[A-Za-z0-9]|[0-9]{4}-).*", item)]
                    if ids:
                        times = [item for item in cells if time_re.fullmatch(item)]
                        if len(ids) != 1 or len(times) != 1:
                            raise ValueError("OFFICIAL_MANUAL_PARSE_FAILURE")
                        position = cells.index(times[0])
                        tail = [int(item) for item in cells[position + 1 :] if item.isdecimal()]
                        if len(tail) != 1:
                            raise ValueError("OFFICIAL_MANUAL_DURATION_FAILURE")
                        current = {"id": ids[0], "time": times[0], "duration": tail[0], "targets": targets, "controllers": controllers, "aps": aps}
                        rows.append(current)
                    elif current is not None and (aps or controllers or targets):
                        current["targets"].extend(targets)
                        current["controllers"].extend(controllers)
                        current["aps"].extend(aps)
    if len(rows) != 58 or len({row["id"] for row in rows}) != 58:
        raise ValueError("OFFICIAL_MANUAL_CENSUS_MISMATCH")
    return rows


def summary(path: Path) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    count: int | None = None
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip().startswith("Attacks"):
            count = int(re.search(r"([0-9]+)\s+times", line).group(1))
        points = re.findall(r"[0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2}", line)
        if len(points) == 2:
            output.append({"start": points[0], "end": points[1], "duration": int(line.split()[-1])})
    if count != len(output):
        raise ValueError("OFFICIAL_SUMMARY_CENSUS_MISMATCH")
    return output


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--official-root", type=Path, required=True)
    parser.add_argument("--private-authority", type=Path, required=True)
    parser.add_argument("--public-output", type=Path, required=True)
    args = parser.parse_args()
    authority = json.loads(args.private_authority.read_text(encoding="utf-8"))
    if authority.get("self_hash") != hash_value({key: value for key, value in authority.items() if key != "self_hash"}):
        raise ValueError("HAI22_PRIVATE_AUTHORITY_SELF_HASH_MISMATCH")
    manual = manual_rows(args.official_root / "hai_dataset_technical_details.pdf")
    expected = {1: 7, 2: 17, 3: 10, 4: 24}
    reconstructed: list[dict[str, Any]] = []
    for number, census in expected.items():
        occurrences = [row for row in manual if row["id"][1] == str(number)]
        intervals = summary(args.official_root / "hai-22.04" / "summary" / f"summary(test{number}.csv).txt")
        if len(occurrences) != census or len(intervals) != census:
            raise ValueError("HAI22_PER_FILE_CENSUS_MISMATCH")
        unused = set(range(len(intervals)))
        for row in occurrences:
            matches = [index for index in unused if f"{datetime.fromisoformat(intervals[index]['start']).hour}:{datetime.fromisoformat(intervals[index]['start']).minute:02d}" == row["time"].lstrip("0") and intervals[index]["duration"] == row["duration"]]
            if len(matches) != 1:
                raise ValueError("HAI22_INDEPENDENT_JOIN_NOT_UNIQUE")
            interval = intervals[matches[0]]
            unused.remove(matches[0])
            reconstructed.append({
                "dataset_version": "22.04", "panel_id": "HAI22_EXTERNAL_REPLICATION_V1", "physical_file_id": f"HAI22_TEST{number}",
                "scenario_id": f"HAI22_04:{row['id']}", "official_occurrence_id": row["id"],
                "closed_intervals": [{"start": interval["start"], "end": interval["end"]}], "attacked_identities": row["targets"],
                "explicit_affected_processes": [], "manual_start_minute": row["time"], "manual_duration_seconds": row["duration"],
                "summary_duration_seconds": interval["duration"], "scenario_components": row["aps"], "target_controller_components": row["controllers"],
            })
    if reconstructed != authority["canonical_records"]:
        raise ValueError("HAI22_INDEPENDENT_CANONICAL_REPLAY_MISMATCH")
    receipt = {"schema": "hai22_official_scenario_independent_replay_receipt_v1", "status": "PASS", "private_authority_sha256": authority["self_hash"], "canonical_records": 58, "per_file": expected, "independent_parser": "SEPARATE_IMPLEMENTATION_NO_BUILDER_IMPORT", "heldout_predictions_observed": 0, "heldout_metrics_observed": 0}
    receipt["self_hash"] = hash_value(receipt)
    args.public_output.parent.mkdir(parents=True, exist_ok=True)
    args.public_output.write_bytes(canon(receipt) + b"\n")
    print(json.dumps({"status": "PASS", "receipt_hash": receipt["self_hash"]}, sort_keys=True))


if __name__ == "__main__":
    main()
