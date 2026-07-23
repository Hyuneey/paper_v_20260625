from __future__ import annotations

from pathlib import Path

from experiments.argos_reproduction.error_rule_full_inner_runtime import (
    verify_hashed_report,
)


ROOT = Path(__file__).resolve().parents[1]


def test_exact_83_rule_candidate_registry_is_frozen() -> None:
    registry = verify_hashed_report(
        ROOT / "docs/task_reports/TASK-037E_CANDIDATE_REGISTRY.json"
    )
    assert registry["expected_rule_count"] == 83
    assert len(registry["records"]) == 83
    assert len({item["slot_id"] for item in registry["records"]}) == 83
    assert {item["direction"] for item in registry["records"]} == {"FN", "FP"}
    assert {item["detector_variant"] for item in registry["records"]} == {
        "LSTMADalpha",
        "LSTMADbeta",
    }


def test_inner_runtime_is_values_only_and_explicitly_replayed_twice() -> None:
    source = (
        ROOT
        / "experiments/argos_reproduction/error_rule_full_inner_runtime.py"
    ).read_text(encoding="utf-8")
    assert source.count("execute_full_window_rule(") == 2
    assert 'split_values_path(config, candidate["kpi_id"], "inner")' in source
    assert "per_kpi_labels" not in source
    assert "outer_prediction.npy" not in source
    assert "test_prediction" not in source
    assert '"labels_mounted": False' in source
