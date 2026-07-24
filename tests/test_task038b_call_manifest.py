from __future__ import annotations

import json
from pathlib import Path

from experiments.argos_reproduction.repair_call_manifest import (
    build_provider_request,
)


ROOT = Path(__file__).resolve().parents[1]


def test_provider_request_has_exact_two_message_contract() -> None:
    request = build_provider_request("system", "user")
    assert request == {
        "messages": [
            {"role": "system", "content": "system"},
            {"role": "user", "content": "user"},
        ]
    }


def test_frozen_manifest_is_unique_ordered_and_bounded_when_present() -> None:
    path = ROOT / "docs/task_reports/TASK-038B_REPAIR_CALL_MANIFEST.json"
    if not path.exists():
        return
    report = json.loads(path.read_text(encoding="utf-8"))
    slots = report["slots"]
    assert report["authorized_call_count"] <= 13
    assert [item["request_order"] for item in slots] == list(
        range(1, len(slots) + 1)
    )
    assert [item["initial_slot_id"] for item in slots] == sorted(
        item["initial_slot_id"] for item in slots
    )
    assert len({item["initial_slot_id"] for item in slots}) == len(slots)
    assert len({item["complete_request_hash"] for item in slots}) == len(slots)
    assert report["retry_slots"] == report["replacement_slots"] == 0
    assert report["review_slots"] == 0
