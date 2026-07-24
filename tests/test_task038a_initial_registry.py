from __future__ import annotations

import json
from pathlib import Path

from experiments.argos_reproduction.agent_factorial_registry import (
    build_initial_rule_registry,
)


ROOT = Path(__file__).resolve().parents[1]


def _config() -> dict[str, object]:
    return json.loads(
        (
            ROOT
            / "configs/argos_reproduction/task038a_agent_factorial_protocol.json"
        ).read_text(encoding="utf-8")
    )


def test_complete_task037d_initial_population_is_frozen() -> None:
    registry = build_initial_rule_registry(_config())
    assert registry["initial_rule_slots"] == 96
    assert registry["initial_static_valid"] == 96
    assert registry["initial_executable"] == 83
    assert registry["initial_runtime_failed"] == 13
    assert registry["repair_population"] == 13
    assert len({row["initial_slot_id"] for row in registry["records"]}) == 96
    assert all(row["initial_rule_hash"] for row in registry["records"])


def test_initial_registry_preserves_frozen_identity_and_contains_no_raw_data() -> None:
    registry = build_initial_rule_registry(_config())
    assert {row["detector_variant"] for row in registry["records"]} == {
        "LSTMADalpha",
        "LSTMADbeta",
    }
    assert {row["direction"] for row in registry["records"]} == {"FN", "FP"}
    serialized = json.dumps(registry)
    assert registry["raw_rule_source_included"] is False
    assert "source_values" not in serialized
    assert "target_values" not in serialized
    assert "C:\\\\Users" not in serialized


def test_task037d_frozen_reports_remain_at_declared_hashes() -> None:
    config = _config()
    for key, expected in config["source_report_hashes"].items():
        report = json.loads(
            (ROOT / config["sources"][key]).read_text(encoding="utf-8")
        )
        assert report["report_hash"] == expected
