from pathlib import Path

from experiments.argos_reproduction.expanded_kpi_cohort import read_json, sha256_json


ROOT = Path(__file__).resolve().parents[1]


def _verify(name: str) -> dict:
    report = read_json(ROOT / "docs/task_reports" / name)
    expected = report.pop("report_hash")
    assert expected == sha256_json(report)
    return report


def test_pre_provider_manifests_are_hash_valid_and_sanitized() -> None:
    support = _verify("TASK-037D_SUPPORT_REPORT.json")
    targets = _verify("TASK-037D_TARGET_CONTRAST_MANIFEST.json")
    requests = _verify("TASK-037D_REQUEST_MANIFEST.json")
    assert support["potential_cell_count"] == 40
    assert targets["record_count"] == requests["registered_slot_count"] == 96
    text = " ".join(
        (ROOT / "docs/task_reports" / name).read_text(encoding="utf-8")
        for name in (
            "TASK-037D_SUPPORT_REPORT.json",
            "TASK-037D_TARGET_CONTRAST_MANIFEST.json",
            "TASK-037D_REQUEST_MANIFEST.json",
        )
    )
    for forbidden in ("source_values", "target_values", "raw_response", "C:\\Users\\"):
        assert forbidden not in text


def test_zero_error_cells_register_no_requests() -> None:
    support = _verify("TASK-037D_SUPPORT_REPORT.json")
    assert all(
        row["registered_slot_count"] == 0
        for row in support["cells"]
        if row["support_state"] == "not_applicable_zero_detector_error"
    )
