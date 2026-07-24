from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _verify(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    expected = payload["report_hash"]
    material = {key: value for key, value in payload.items() if key != "report_hash"}
    encoded = json.dumps(
        material,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode()
    assert hashlib.sha256(encoded).hexdigest() == expected
    serialized = path.read_text(encoding="utf-8").lower()
    for token in (
        "c:\\users",
        "private_argos_reproduction",
        "raw_response.md",
        "output_labels.npy",
        "source_values",
        "target_values",
    ):
        assert token not in serialized
    return payload


def test_all_present_task038b_json_reports_are_self_hashed_and_sanitized() -> None:
    reports = sorted(
        (ROOT / "docs/task_reports").glob("TASK-038B_*.json")
    )
    for path in reports:
        _verify(path)


def test_final_report_preserves_claim_boundary_when_present() -> None:
    path = ROOT / "docs/task_reports/TASK-038B_REPORT.md"
    if not path.exists():
        return
    text = path.read_text(encoding="utf-8")
    assert "does not evaluate ReviewAgent" in text
    assert "detection performance" in text
    assert "sealed-test" in text
