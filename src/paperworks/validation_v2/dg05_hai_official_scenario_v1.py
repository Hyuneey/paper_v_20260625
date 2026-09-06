"""Deterministic, source-only HAI22/21 scenario reconstruction helpers.

This module is deliberately outside the detector route.  It consumes official
manual, summary, and (for HAI21 only) timestamp/overall-attack metadata to
construct pre-result scenario authorities.  It never opens feature values or
invokes a detector.
"""

from __future__ import annotations

import csv
import gzip
import hashlib
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

import pdfplumber


MANUAL_SHA256 = "0668345c4e80331b918fe17c81f8f363b13bd22886831d286e761bc62b71a556"
MANUAL_BLOB = "18cb88514176e1c641f584cf24ac8e9559432b38"
OFFICIAL_REPOSITORY_COMMIT = "2a814cebc9a66b06c9e5cd545e2d72e65d383737"
_ID = re.compile(r"A[1-5][0-9]{2}")
_AP = re.compile(r"AP[0-9]+")
_TIME = re.compile(r"[0-9]{1,2}:[0-9]{2}")
_NUMBER = re.compile(r"[0-9]+")
_CONTROLLER = re.compile(r"P[1-4]-.*")
_TARGET = re.compile(r"(?:P[1-4]_[A-Za-z0-9]|[0-9]{4}-).*")
_TIMESTAMP = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2}")


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


def digest(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def self_hashed(value: dict[str, Any]) -> dict[str, Any]:
    body = dict(value)
    body.pop("self_hash", None)
    return {**body, "self_hash": digest(body)}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _cells(row: Iterable[str | None]) -> list[str]:
    return [item.strip() if item else "" for item in row]


def _components(cells: list[str]) -> tuple[list[str], list[str], list[str]]:
    return (
        [item for item in cells if _AP.fullmatch(item)],
        [item for item in cells if _CONTROLLER.fullmatch(item)],
        [item for item in cells if _TARGET.fullmatch(item)],
    )


def manual_records(manual: Path, version: str) -> list[dict[str, Any]]:
    """Extract rows and retain target cells exactly as printed by the manual.

    The target-cell grammar is intentionally not an alias or normalization
    grammar.  A comma or full stop in an official target cell is retained in
    that component for any later, separately authorized namespace decision.
    """
    if sha256(manual) != MANUAL_SHA256:
        raise ValueError("OFFICIAL_MANUAL_HASH_MISMATCH")
    pages = range(33, 36) if version == "22.04" else range(36, 39)
    expected = 58 if version == "22.04" else 50
    output: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    with pdfplumber.open(manual) as document:
        for page_index in pages:
            for table in document.pages[page_index].extract_tables():
                for row in table:
                    cells = _cells(row)
                    ids = [item for item in cells if _ID.fullmatch(item)]
                    ap, controller, target = _components(cells)
                    if ids:
                        if len(ids) != 1:
                            raise ValueError("AMBIGUOUS_OFFICIAL_MANUAL_ID")
                        times = [item for item in cells if _TIME.fullmatch(item)]
                        if len(times) != 1:
                            raise ValueError("OFFICIAL_MANUAL_TIME_MISSING")
                        time_index = cells.index(times[0])
                        durations = [int(item) for item in cells[time_index + 1 :] if _NUMBER.fullmatch(item)]
                        if len(durations) != 1:
                            raise ValueError("OFFICIAL_MANUAL_DURATION_MISSING")
                        current = {
                            "official_occurrence_id": ids[0],
                            "manual_start_minute": times[0],
                            "manual_duration_seconds": durations[0],
                            "scenario_components": ap,
                            "target_controller_components": controller,
                            "attacked_identities": target,
                        }
                        output.append(current)
                    elif current is not None and (ap or controller or target):
                        current["scenario_components"].extend(ap)
                        current["target_controller_components"].extend(controller)
                        current["attacked_identities"].extend(target)
    if len(output) != expected or len({item["official_occurrence_id"] for item in output}) != expected:
        raise ValueError("OFFICIAL_MANUAL_OCCURRENCE_CENSUS_MISMATCH")
    if any(not item["attacked_identities"] for item in output):
        raise ValueError("OFFICIAL_MANUAL_TARGET_MISSING")
    return output


def summary_records(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    declared: int | None = None
    file_name: str | None = None
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip().startswith("File Name"):
            file_name = line.split(":", 1)[1].strip()
        if line.strip().startswith("Attacks"):
            match = re.search(r"([0-9]+)\s+times", line)
            if match is None:
                raise ValueError("OFFICIAL_SUMMARY_DECLARED_CENSUS_INVALID")
            declared = int(match.group(1))
        points = _TIMESTAMP.findall(line)
        if len(points) == 2:
            fields = line.split()
            duration = int(fields[-1])
            start, end = map(datetime.fromisoformat, points)
            if end < start or duration != int((end - start).total_seconds()):
                raise ValueError("OFFICIAL_SUMMARY_INTERVAL_INVALID")
            records.append({"start": points[0], "end": points[1], "duration_seconds": duration})
    if file_name is None or declared is None or declared != len(records):
        raise ValueError("OFFICIAL_SUMMARY_CENSUS_MISMATCH")
    if len({(item["start"], item["end"]) for item in records}) != len(records):
        raise ValueError("OFFICIAL_SUMMARY_DUPLICATE_INTERVAL")
    return records


def label_ranges(path: Path) -> list[dict[str, Any]]:
    """Read only HAI21 ``time`` and overall ``attack`` columns from gzip CSV."""
    records: list[dict[str, Any]] = []
    with gzip.open(path, "rt", encoding="utf-8", newline="") as stream:
        reader = csv.reader(stream)
        header = next(reader)
        if "time" not in header or "attack" not in header:
            raise ValueError("HAI21_OFFICIAL_LABEL_SCHEMA_MISMATCH")
        time_index, attack_index = header.index("time"), header.index("attack")
        start: str | None = None
        end: str | None = None
        previous: datetime | None = None
        for row in reader:
            if len(row) != len(header):
                raise ValueError("HAI21_OFFICIAL_LABEL_ROW_SHAPE_MISMATCH")
            timestamp = row[time_index]
            attack = row[attack_index]
            point = datetime.fromisoformat(timestamp)
            if previous is not None and point <= previous:
                raise ValueError("HAI21_LABEL_TIMELINE_NOT_STRICTLY_INCREASING")
            previous = point
            if attack not in {"0", "1"}:
                raise ValueError("HAI21_OFFICIAL_ATTACK_LABEL_NOT_BINARY")
            if attack == "1" and start is None:
                start = timestamp
            if attack == "1":
                end = timestamp
            elif start is not None:
                records.append({"start": start, "end": end, "duration_seconds": int((datetime.fromisoformat(end or start) - datetime.fromisoformat(start)).total_seconds())})
                start = end = None
        if start is not None:
            records.append({"start": start, "end": end, "duration_seconds": int((datetime.fromisoformat(end or start) - datetime.fromisoformat(start)).total_seconds())})
    return records


def _manual_group(records: list[dict[str, Any]], file_number: int, expected: int) -> list[dict[str, Any]]:
    group = [item for item in records if item["official_occurrence_id"][1] == str(file_number)]
    if len(group) != expected:
        raise ValueError("OFFICIAL_MANUAL_FILE_GROUP_CENSUS_MISMATCH")
    return group


def _unique_join(manual: list[dict[str, Any]], intervals: list[dict[str, Any]], *, inclusive_duration: bool) -> list[tuple[dict[str, Any], dict[str, Any]]]:
    used: set[int] = set()
    joined: list[tuple[dict[str, Any], dict[str, Any]]] = []
    for occurrence in manual:
        expected_duration = occurrence["manual_duration_seconds"] - (1 if inclusive_duration else 0)
        candidates = [
            (index, interval)
            for index, interval in enumerate(intervals)
            if index not in used
            and f"{datetime.fromisoformat(interval['start']).hour}:{datetime.fromisoformat(interval['start']).minute:02d}" == occurrence["manual_start_minute"].lstrip("0")
            and interval["duration_seconds"] == expected_duration
        ]
        if len(candidates) != 1:
            raise ValueError("OFFICIAL_MANUAL_INTERVAL_JOIN_NOT_UNIQUE")
        index, interval = candidates[0]
        used.add(index)
        joined.append((occurrence, interval))
    if len(used) != len(intervals):
        raise ValueError("OFFICIAL_INTERVAL_UNBOUND")
    return joined


def build_hai22_authority(official_root: Path) -> dict[str, Any]:
    manual = manual_records(official_root / "hai_dataset_technical_details.pdf", "22.04")
    expected = {1: 7, 2: 17, 3: 10, 4: 24}
    records: list[dict[str, Any]] = []
    summary_hashes: dict[str, str] = {}
    for number, count in expected.items():
        summary_path = official_root / "hai-22.04" / "summary" / f"summary(test{number}.csv).txt"
        intervals = summary_records(summary_path)
        if len(intervals) != count:
            raise ValueError("HAI22_OFFICIAL_SUMMARY_CENSUS_MISMATCH")
        summary_hashes[f"test{number}.csv"] = sha256(summary_path)
        for occurrence, interval in _unique_join(_manual_group(manual, number, count), intervals, inclusive_duration=False):
            records.append({
                "dataset_version": "22.04",
                "panel_id": "HAI22_EXTERNAL_REPLICATION_V1",
                "physical_file_id": f"HAI22_TEST{number}",
                "scenario_id": f"HAI22_04:{occurrence['official_occurrence_id']}",
                "official_occurrence_id": occurrence["official_occurrence_id"],
                "closed_intervals": [{"start": interval["start"], "end": interval["end"]}],
                "attacked_identities": occurrence["attacked_identities"],
                "explicit_affected_processes": [],
                "manual_start_minute": occurrence["manual_start_minute"],
                "manual_duration_seconds": occurrence["manual_duration_seconds"],
                "summary_duration_seconds": interval["duration_seconds"],
                "scenario_components": occurrence["scenario_components"],
                "target_controller_components": occurrence["target_controller_components"],
            })
    if len(records) != 58 or len({item["scenario_id"] for item in records}) != 58:
        raise ValueError("HAI22_OFFICIAL_SCENARIO_CENSUS_MISMATCH")
    return self_hashed({
        "schema": "hai22_official_scenario_authority_private_v1",
        "status": "PRIVATE_CANONICAL_AUTHORITY",
        "official_source": {"repository_commit": OFFICIAL_REPOSITORY_COMMIT, "manual_blob": MANUAL_BLOB, "manual_sha256": MANUAL_SHA256, "summary_sha256": summary_hashes},
        "source_roles": {"technical_manual": "SCENARIO_IDENTITY_AND_DIRECT_TARGET_METADATA", "enumerated_summary": "EXACT_PHYSICAL_INTERVAL_AUTHORITY", "README": "PANEL_CENSUS_AUTHORITY"},
        "file_census": {"test1.csv": 7, "test2.csv": 17, "test3.csv": 10, "test4.csv": 24},
        "manual_file_binding_rule": "MANUAL_OCCURRENCE_BLOCK_CARDINALITY_PLUS_UNIQUE_START_TIME_DURATION_JOIN_TO_OFFICIAL_SUMMARY",
        "canonical_records": records,
    })


def _minute(value: str) -> str:
    point = datetime.fromisoformat(value)
    return f"{point.hour}:{point.minute:02d}"


def _hai21_compatible_pairs(
    manual: list[dict[str, Any]], intervals: list[dict[str, Any]]
) -> list[tuple[int, int]]:
    """Return only exact, non-residual HAI21 corroborative pairings.

    Manual timing is deliberately used here only as corroboration.  The
    canonical physical interval is always carried by the official overall
    attack-label range; DEC-035 supplies the explicitly fail-closed residual
    rule for the two rows whose manual timing is not compatible.
    """
    pairs: list[tuple[int, int]] = []
    used_intervals: set[int] = set()
    for manual_index, occurrence in enumerate(manual):
        candidates = [
            interval_index
            for interval_index, interval in enumerate(intervals)
            if interval_index not in used_intervals
            and _minute(interval["start"]) == occurrence["manual_start_minute"].lstrip("0")
            and interval["duration_seconds"] == occurrence["manual_duration_seconds"] - 1
        ]
        if len(candidates) == 1:
            used_intervals.add(candidates[0])
            pairs.append((manual_index, candidates[0]))
        elif len(candidates) > 1:
            raise ValueError("HAI21_COMPATIBLE_OCCURRENCE_MAPPING_AMBIGUOUS")
    return pairs


def _residual_pair(
    *,
    manual: list[dict[str, Any]],
    intervals: list[dict[str, Any]],
    compatible: list[tuple[int, int]],
    expected_id: str,
) -> tuple[int, int, dict[str, Any]]:
    matched_manual = {item[0] for item in compatible}
    matched_intervals = {item[1] for item in compatible}
    remaining_manual = [index for index in range(len(manual)) if index not in matched_manual]
    remaining_intervals = [index for index in range(len(intervals)) if index not in matched_intervals]
    if len(remaining_manual) != 1 or len(remaining_intervals) != 1:
        raise ValueError("HAI21_RESIDUAL_OCCURRENCE_MAPPING_AMBIGUOUS")
    manual_index, interval_index = remaining_manual[0], remaining_intervals[0]
    if manual[manual_index]["official_occurrence_id"] != expected_id:
        raise ValueError("HAI21_RESIDUAL_OCCURRENCE_MAPPING_AMBIGUOUS")
    starts = [datetime.fromisoformat(item["start"]) for item in intervals]
    interval_point = starts[interval_index]
    # Chronological neighborhood is an independent guard: every accepted
    # matched occurrence before/after the residual remains before/after it.
    for left_manual, left_interval in compatible:
        manual_order = left_manual < manual_index
        interval_order = starts[left_interval] < interval_point
        if manual_order != interval_order:
            raise ValueError("HAI21_RESIDUAL_OCCURRENCE_MAPPING_AMBIGUOUS")
    return manual_index, interval_index, {
        "join_kind": "UNIQUE_RESIDUAL_OFFICIAL_SOURCE_BIJECTION",
        "same_physical_file": True,
        "manual_file_census": len(manual),
        "label_range_census": len(intervals),
        "compatible_pairs_preassigned": len(compatible),
        "unmatched_manual_count": 1,
        "unmatched_label_range_count": 1,
        "chronological_neighborhood_noncontradictory": True,
        "alternative_complete_bijections": 0,
    }


def build_hai21_authority(official_root: Path) -> dict[str, Any]:
    """Freeze HAI21 source roles exactly as prospectively approved by DEC-035."""
    manual = manual_records(official_root / "hai_dataset_technical_details.pdf", "21.03")
    expected = {1: 5, 2: 20, 3: 8, 4: 5, 5: 12}
    residual_ids = {2: "A209", 5: "A512"}
    label_hashes: dict[str, str] = {}
    canonical_records: list[dict[str, Any]] = []
    residual_proofs: dict[str, dict[str, Any]] = {}
    for number, count in expected.items():
        label_path = official_root / "hai-21.03" / f"test{number}.csv.gz"
        intervals = label_ranges(label_path)
        file_manual = _manual_group(manual, number, count)
        if len(intervals) != count:
            raise ValueError("HAI21_OFFICIAL_LABEL_CENSUS_MISMATCH")
        label_hashes[f"test{number}.csv.gz"] = sha256(label_path)
        compatible = _hai21_compatible_pairs(file_manual, intervals)
        matched: dict[int, tuple[int, dict[str, Any]]] = {
            manual_index: (interval_index, {"join_kind": "UNIQUE_COMPATIBLE_MANUAL_LABEL_CORROBORATION"})
            for manual_index, interval_index in compatible
        }
        if number in residual_ids:
            manual_index, interval_index, proof = _residual_pair(
                manual=file_manual,
                intervals=intervals,
                compatible=compatible,
                expected_id=residual_ids[number],
            )
            matched[manual_index] = (interval_index, proof)
            residual_proofs[residual_ids[number]] = proof
        if len(matched) != count or len({item[0] for item in matched.values()}) != count:
            raise ValueError("HAI21_RESIDUAL_OCCURRENCE_MAPPING_AMBIGUOUS")
        for manual_index, occurrence in enumerate(file_manual):
            interval_index, join_proof = matched[manual_index]
            interval = intervals[interval_index]
            canonical_records.append({
                "dataset_version": "21.03",
                "panel_id": "HAI21_EXTERNAL_REPLICATION_V1",
                "physical_file_id": f"HAI21_TEST{number}",
                "scenario_id": f"HAI21_03:{occurrence['official_occurrence_id']}",
                "official_occurrence_id": occurrence["official_occurrence_id"],
                "closed_intervals": [{"start": interval["start"], "end": interval["end"]}],
                "attacked_identities": occurrence["attacked_identities"],
                "explicit_affected_processes": [],
                "manual_start_minute": occurrence["manual_start_minute"],
                "manual_duration_seconds": occurrence["manual_duration_seconds"],
                "label_duration_seconds": interval["duration_seconds"],
                "scenario_components": occurrence["scenario_components"],
                "target_controller_components": occurrence["target_controller_components"],
                "join_proof": join_proof,
            })
    if len(canonical_records) != 50 or len({item["scenario_id"] for item in canonical_records}) != 50:
        raise ValueError("HAI21_OFFICIAL_SCENARIO_CENSUS_MISMATCH")
    return self_hashed({
        "schema": "hai21_official_scenario_authority_private_v1",
        "status": "PRIVATE_CANONICAL_AUTHORITY",
        "decision": {"decision_id": "DEC-035", "role_amendment": "HAI21_OFFICIAL_SCENARIO_BOUNDARY_SOURCE_ROLE_AMENDMENT"},
        "official_source": {"repository_commit": OFFICIAL_REPOSITORY_COMMIT, "manual_blob": MANUAL_BLOB, "manual_sha256": MANUAL_SHA256, "overall_attack_label_sha256": label_hashes},
        "source_roles": {
            "technical_manual": "SCENARIO_IDENTITY_AND_DIRECT_TARGET_AUTHORITY",
            "overall_attack_label": "EXACT_PHYSICAL_INTERVAL_AUTHORITY",
            "README": "PANEL_CENSUS_AUTHORITY",
            "manual_start_and_duration": "CORROBORATIVE_OCCURRENCE_METADATA_NOT_INTERVAL_OVERRIDE",
        },
        "file_census": {f"test{number}.csv.gz": count for number, count in expected.items()},
        "residual_bijection_proofs": residual_proofs,
        "canonical_records": canonical_records,
    })
