from __future__ import annotations

import json
from pathlib import Path

from experiments.argos_reproduction.expanded_kpi_cohort import sha256_json


ROOT = Path(__file__).resolve().parents[1]
REPORT_NAMES = (
    "TASK-037C_INPUT_MANIFEST.json",
    "TASK-037C_INNER_DIAGNOSTIC_REPORT.json",
    "TASK-037C_OUTER_FUSION_REPORT.json",
    "TASK-037C_FN_CONTRIBUTION_REPORT.json",
    "TASK-037C_FP_CONTRIBUTION_REPORT.json",
    "TASK-037C_VARIANT_CONSISTENCY_REPORT.json",
    "TASK-037C_BOOTSTRAP_REPORT.json",
)


def test_required_protocol_and_task_files_exist() -> None:
    required = (
        "docs/argos_reproduction/GENERIC_RULE_DIAGNOSTIC_FUSION_PROTOCOL.md",
        "docs/argos_reproduction/FUSION_CONTRIBUTION_METRICS.md",
        "docs/argos_reproduction/E5_E6_CLAIM_BOUNDARY.md",
        "TASKS/TASK-037C_FROZEN_DIAGNOSTIC_FUSION.md",
    )
    assert all((ROOT / value).is_file() for value in required)


def test_completed_reports_are_self_hashed_and_boundary_safe_when_present() -> None:
    for name in REPORT_NAMES:
        path = ROOT / "docs/task_reports" / name
        if not path.exists():
            continue
        report = json.loads(path.read_text(encoding="utf-8"))
        expected = report.pop("report_hash")
        assert expected == sha256_json(report)
        encoded = json.dumps(report, sort_keys=True).lower()
        assert "private_argos_reproduction" not in encoded
        assert "c:\\users\\" not in encoded
        assert "source_values" not in encoded
        assert "target_values" not in encoded
        assert ".npy" not in encoded


def test_outer_report_never_fabricates_binary_fusion_auc() -> None:
    path = ROOT / "docs/task_reports/TASK-037C_OUTER_FUSION_REPORT.json"
    if not path.exists():
        return
    report = json.loads(path.read_text(encoding="utf-8"))
    assert report["AUROC_AUPRC_computed_for_binary_fusion"] is False
    for arm in report["fusion_arms"]:
        assert "AUROC" not in json.dumps(arm)
        assert "AUPRC" not in json.dumps(arm)
