from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_receipt_is_written_before_provider_call_and_blocks_reuse() -> None:
    source = (
        ROOT / "experiments/argos_reproduction/review_provider_capture.py"
    ).read_text(encoding="utf-8")
    assert source.index("write_json(\n            receipt_path") < source.index(
        "result = call_once("
    )
    assert "TASK038C_SLOT_ALREADY_CONSUMED" in source
