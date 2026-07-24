import json
from pathlib import Path


def test_a0_reproduction_is_exact() -> None:
    report = json.loads(
        Path("docs/task_reports/TASK-038D_A0_REPRODUCTION_REPORT.json").read_text()
    )
    assert report["exact_match_count"] == 40
    assert (
        report["A0_FN_rule_selected_count"],
        report["A0_FN_no_op_count"],
        report["A0_FP_rule_selected_count"],
        report["A0_FP_no_op_count"],
    ) == (19, 1, 2, 18)
