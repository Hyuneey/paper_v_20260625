import json
from pathlib import Path


def test_origin_report_accounts_for_repair_and_review() -> None:
    report = json.loads(Path("docs/task_reports/TASK-038D_SELECTION_ORIGIN_REPORT.json").read_text())
    assert set(report["branch_summaries"]) == {"A0", "A1", "A2", "A3"}
    assert "repair_survival" in report
    assert "review_survival" in report
