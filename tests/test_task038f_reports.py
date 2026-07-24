import json
from pathlib import Path

from experiments.argos_reproduction.expanded_kpi_cohort import sha256_json


JSON_REPORTS = (
    "docs/task_reports/TASK-038F_EVIDENCE_SOURCE_MAP.json",
    "docs/task_reports/TASK-038F_COMPONENT_JUDGMENTS.json",
    "docs/task_reports/TASK-038F_OVERALL_VALIDITY.json",
    "docs/task_reports/TASK-038F_REFERENCE_FREEZE_RECOMMENDATION.json",
    "docs/argos_reproduction/ARGOS_VALIDITY_DECISION_MATRIX.json",
)

REQUIRED_OUTPUTS = (
    "docs/argos_reproduction/ARGOS_COMPONENT_EVIDENCE_LEDGER.md",
    "docs/argos_reproduction/ARGOS_METHODOLOGICAL_VALIDITY_REPORT.md",
    "docs/argos_reproduction/ARGOS_VALIDITY_DECISION_MATRIX.json",
    "docs/argos_reproduction/ARGOS_CLAIM_MATRIX_FINAL.md",
    "docs/argos_reproduction/ARGOS_REFERENCE_TRACK_FREEZE.md",
    "docs/argos_reproduction/ARGOS_TO_PROPOSED_METHOD_BRIDGE.md",
    "docs/professor_feedback/ARGOS_METHOD_VALIDITY_UPDATE.md",
    "docs/task_reports/TASK-038F_REPORT.md",
    "TASKS/TASK-038F_ARGOS_METHOD_VALIDITY_SYNTHESIS.md",
)


def test_task038f_json_reports_are_self_hashed() -> None:
    for name in JSON_REPORTS:
        payload = json.loads(Path(name).read_text(encoding="utf-8"))
        observed = payload.pop("report_hash")
        assert observed == sha256_json(payload)


def test_required_outputs_exist_and_preserve_claim_boundary() -> None:
    for name in REQUIRED_OUTPUTS:
        assert Path(name).is_file()
    report = Path("docs/task_reports/TASK-038F_REPORT.md").read_text(
        encoding="utf-8"
    )
    assert "passed_argos_methodological_validity_synthesis" in report
    assert "partial_methodological_support" in report
    assert "not exact reproduction" in report
    assert "sealed-test access: false" in report
