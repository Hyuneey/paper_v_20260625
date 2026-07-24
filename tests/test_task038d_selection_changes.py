import json
from pathlib import Path


def test_change_report_keeps_stochasticity_separate_from_repair() -> None:
    report = json.loads(Path("docs/task_reports/TASK-038D_SELECTION_CHANGE_REPORT.json").read_text())
    stability = report["stochastic_selection_stability"]
    assert stability["paired_review_slots"] == 36
    assert stability["interpreted_as_repair_effect"] is False
