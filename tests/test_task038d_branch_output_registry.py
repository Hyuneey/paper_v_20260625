from pathlib import Path

from experiments.argos_reproduction.branch_output_registry import (
    ROOT,
    build_branch_output_registry,
)


CONFIG = ROOT / "configs/argos_reproduction/task038d_branch_selection.json"


def test_branch_output_registry_has_exact_counts() -> None:
    report = build_branch_output_registry(CONFIG)
    assert report["branch_output_counts"] == {"A0": 83, "A1": 96, "A2": 82, "A3": 96}
    assert report["total_branch_executable_output_records"] == 357
    assert not report["invalid_review_fallback_performed"]
