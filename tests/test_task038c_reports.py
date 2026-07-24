from __future__ import annotations

import json
from pathlib import Path

from experiments.argos_reproduction.expanded_kpi_cohort import sha256_json


ROOT = Path(__file__).resolve().parents[1]


def test_present_task038c_reports_are_hashed_and_nonraw() -> None:
    for path in (ROOT / "docs/task_reports").glob("TASK-038C_*.json"):
        payload = json.loads(path.read_text(encoding="utf-8"))
        observed = payload.pop("report_hash")
        assert observed == sha256_json(payload)
        serialized = json.dumps(payload, sort_keys=True)
        for prohibited in (
            "source_values",
            "target_values",
            "artifacts/private_argos_reproduction",
            "C:\\\\Users",
        ):
            assert prohibited not in serialized


def test_outer_and_test_access_remain_prohibited() -> None:
    config = json.loads(
        (
            ROOT
            / "configs/argos_reproduction/task038c_review_inner_experiment.json"
        ).read_text(encoding="utf-8")
    )
    assert config["boundaries"]["outer_access"] is False
    assert config["boundaries"]["sealed_test_access"] is False


def test_effect_report_preserves_parent_and_call_denominators() -> None:
    path = ROOT / "docs/task_reports/TASK-038C_EFFECT_REPORT.json"
    if not path.is_file():
        return
    report = json.loads(path.read_text(encoding="utf-8"))
    assert report["A2"]["executable_branch_parent_count"] == 83
    assert report["A2"]["calls_attempted"] == 36
    assert report["A3"]["executable_branch_parent_count"] == 96
    assert report["A3"]["calls_attempted"] == 41
