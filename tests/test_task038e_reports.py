import json
from pathlib import Path

from experiments.argos_reproduction.expanded_kpi_cohort import sha256_json


REPORTS = (
    "TASK-038E_OUTER_EXECUTION_REGISTRY.json",
    "TASK-038E_PHYSICAL_EXECUTION_MANIFEST.json",
)

RESULT_REPORTS = (
    "TASK-038E_OUTER_RUNTIME_REPORT.json",
    "TASK-038E_OUTER_PREDICTION_FREEZE.json",
    "TASK-038E_A0_REPRODUCTION_REPORT.json",
    "TASK-038E_BRANCH_OUTER_REPORT.json",
    "TASK-038E_CONTRIBUTION_REPORT.json",
    "TASK-038E_REVIEW_TRANSFER_REPORT.json",
    "TASK-038E_REPAIR_UTILITY_REPORT.json",
    "TASK-038E_FP_SAFETY_REPORT.json",
    "TASK-038E_GENERALIZATION_GAP_REPORT.json",
    "TASK-038E_VARIANT_CONSISTENCY_REPORT.json",
    "TASK-038E_BOOTSTRAP_REPORT.json",
    "TASK-038E_AGENT_COST_REPORT.json",
)


def test_task038e_reports_are_self_hashed_and_private_safe() -> None:
    names = list(REPORTS)
    if Path("docs/task_reports/TASK-038E_REPORT.md").exists():
        names.extend(RESULT_REPORTS)
    for name in names:
        payload = json.loads(Path("docs/task_reports", name).read_text())
        observed = payload.pop("report_hash")
        assert observed == sha256_json(payload)
        text = json.dumps(payload)
        for forbidden in (
            "private_argos_reproduction",
            "output_labels.npy",
            "outer_values.npy",
            "outer_labels.npy",
            "def inference(",
            "prompt_text",
            "response_text",
        ):
            assert forbidden not in text
