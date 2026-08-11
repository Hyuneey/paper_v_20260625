#!/usr/bin/env python3
"""Validate TASK-039E3-R0 public JSON hashes and sanitized boundaries."""

from __future__ import annotations

import json
from pathlib import Path

from paperworks.v6.task039e3_r0_capability_forensics_v1 import verify_self_hash_v1


def _strings(value: object) -> list[str]:
    if isinstance(value, dict):
        result: list[str] = []
        for item in value.values():
            result.extend(_strings(item))
        return result
    if isinstance(value, list):
        result = []
        for item in value:
            result.extend(_strings(item))
        return result
    return [value] if isinstance(value, str) else []


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    reports = root / "docs/task_reports"
    json_paths = sorted(reports.glob("TASK-039E3_R0_*.json"))
    if len(json_paths) != 6:
        raise RuntimeError("R0 JSON artifact count differs")
    all_strings: list[str] = []
    for path in json_paths:
        document = json.loads(path.read_text(encoding="utf-8"))
        verify_self_hash_v1(document)
        all_strings.extend(_strings(document))
    report_path = reports / "TASK-039E3_R0_REPORT.md"
    all_strings.append(report_path.read_text(encoding="utf-8"))
    forbidden_value_markers = (
        "authorization: bearer",
        "bearer sk-",
        "chat.completions.message.content",
        "private_relation_payload",
        "calibrated_numeric_value",
    )
    lowered = "\n".join(all_strings).lower()
    hits = tuple(marker for marker in forbidden_value_markers if marker in lowered)
    if hits:
        raise RuntimeError(f"public sensitive-value scan failed: {hits}")
    print("6 JSON artifacts parsed; 6 self-hashes verified; 7 public artifacts leak-scanned")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
