import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def stable_hash(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode()).hexdigest()


def test_task037b_config_freezes_exact_dual_arm_and_no_test_or_fusion():
    config = json.loads((ROOT / "configs/argos_reproduction/task037b_dual_lstm_detector_validation.json").read_text())
    assert [item["detector_id"] for item in config["detector_arms"]] == ["LSTMADalpha", "LSTMADbeta"]
    assert config["execution"]["execution_unit_count"] == 20
    assert config["execution"]["variant_selection"] is False
    assert config["split_policy"]["training_label_policy"] == "contaminated_training"
    assert all(value is False for value in config["boundaries"].values())


def test_existing_task037b_json_reports_are_self_hashed_and_safe():
    paths = sorted((ROOT / "docs/task_reports").glob("TASK-037B_*.json"))
    for path in paths:
        report = json.loads(path.read_text())
        expected = report.pop("report_hash")
        assert expected == stable_hash(report)
        encoded = json.dumps(report).lower()
        assert "private_argos_reproduction" not in encoded
        assert "c:\\users\\" not in encoded
        assert "testlabels" not in encoded
