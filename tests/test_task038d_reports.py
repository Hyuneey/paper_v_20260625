import json
from pathlib import Path

from experiments.argos_reproduction.expanded_kpi_cohort import sha256_json


REPORTS = (
    "TASK-038D_BRANCH_OUTPUT_REGISTRY.json",
    "TASK-038D_CANDIDATE_PREDICTION_MANIFEST.json",
    "TASK-038D_A0_REPRODUCTION_REPORT.json",
    "TASK-038D_SELECTION_FREEZE.json",
    "TASK-038D_SELECTION_ORIGIN_REPORT.json",
    "TASK-038D_SELECTION_CHANGE_REPORT.json",
    "TASK-038D_INNER_DIAGNOSTIC_REPORT.json",
)


def test_task038d_reports_are_self_hashed_and_private_safe() -> None:
    for name in REPORTS:
        payload = json.loads(Path("docs/task_reports", name).read_text())
        observed = payload.pop("report_hash")
        assert observed == sha256_json(payload)
        text = json.dumps(payload)
        assert "private_argos_reproduction" not in text
        assert "source_values" not in text
        assert "target_values" not in text
        assert "outer_label" not in text
