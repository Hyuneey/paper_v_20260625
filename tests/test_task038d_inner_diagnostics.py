import json
from pathlib import Path


def test_inner_diagnostics_are_non_selecting() -> None:
    report = json.loads(Path("docs/task_reports/TASK-038D_INNER_DIAGNOSTIC_REPORT.json").read_text())
    assert report["status"] == "selection_split_diagnostics_only"
    assert report["diagnostics_used_for_selection"] is False
    assert report["joint_pair_search"] is False
