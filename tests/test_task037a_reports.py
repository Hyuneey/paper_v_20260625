import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORTS = (
    "TASK-037A_DETECTOR_IDENTITY_REPORT.json",
    "TASK-037A_SOURCE_ALIGNMENT_REPORT.json",
    "TASK-037A_ENVIRONMENT_PREFLIGHT_REPORT.json",
    "TASK-037A_SYNTHETIC_SMOKE_REPORT.json",
    "TASK-037A_READINESS_REPORT.json",
)


def report_hash(document):
    subject = dict(document); subject.pop("report_hash")
    raw = json.dumps(subject, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode()
    return hashlib.sha256(raw).hexdigest()


def test_all_task037a_reports_are_self_hashed_and_boundary_safe():
    for name in REPORTS:
        report = json.loads((ROOT / "docs/task_reports" / name).read_text())
        assert report["report_hash"] == report_hash(report)
        text = json.dumps(report).lower()
        assert "source_values" not in text
        assert "target_values" not in text
        assert "private_argos_reproduction" not in text
        assert "openai_api_key" not in text


def test_readiness_preserves_ambiguity_and_no_execution_authority():
    report = json.loads((ROOT / "docs/task_reports/TASK-037A_READINESS_REPORT.json").read_text())
    assert report["status"] == "unresolved_variant_ambiguity_with_dual_arm_freeze"
    assert report["task037b_execution_authorized"] is False
    assert report["e4_e5_e6_execution_authorized"] is False
    assert report["test_values_parsed"] is False
    assert report["test_labels_parsed"] is False


def test_host_utilities_have_no_provider_or_real_dataset_surface():
    names = (
        "easytsad_detector_audit.py",
        "lstm_variant_resolver.py",
        "detector_artifact_contract.py",
        "detector_error_segments.py",
        "detector_environment_preflight.py",
        "detector_synthetic_smoke.py",
    )
    for name in names:
        source = (ROOT / "experiments/argos_reproduction" / name).read_text().lower()
        assert "openai" not in source
        assert "anthropic" not in source
        assert "swat_data_root" not in source
        assert "phase2_ground_truth" not in source
        assert "testlabels/" not in source
