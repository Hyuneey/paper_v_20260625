from __future__ import annotations

import inspect
import json
from pathlib import Path

import pytest

from experiments.argos_reproduction.expanded_kpi_cohort import sha256_json
from experiments.argos_reproduction.frozen_prediction_loader import (
    FrozenPredictionError,
    validate_frozen_matrix,
    verified_report,
)


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs/argos_reproduction/task037c_diagnostic_fusion.json"


def test_config_registers_exact_matrix_and_prohibits_selection() -> None:
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    validate_frozen_matrix(config)
    assert config["matrix"]["fusion_arm_count"] == 16
    assert set(config["selection_policy"].values()) == {False}
    assert config["boundaries"]["test_value_access"] is False
    assert config["boundaries"]["test_label_access"] is False


def test_report_hash_mismatch_fails_closed(tmp_path: Path) -> None:
    report = {"schema_version": "1.0", "value": 1}
    report["report_hash"] = sha256_json(report)
    path = tmp_path / "report.json"
    path.write_text(json.dumps(report), encoding="utf-8")
    assert verified_report(path)["value"] == 1
    report["value"] = 2
    path.write_text(json.dumps(report), encoding="utf-8")
    with pytest.raises(FrozenPredictionError, match="SELF_HASH_MISMATCH"):
        verified_report(path)


def test_prediction_loader_has_no_label_or_test_reader_surface() -> None:
    import experiments.argos_reproduction.frozen_prediction_loader as module

    source = inspect.getsource(module.load_frozen_predictions)
    signature = inspect.signature(module.load_frozen_predictions)
    assert "label" not in signature.parameters
    assert "np.load" not in source
    assert "test_prediction" not in source
