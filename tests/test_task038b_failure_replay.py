from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from experiments.argos_reproduction.repair_failure_replay import (
    RepairFailureReplayError,
    _write_values_only,
    load_repair_population,
    sanitize_error_evidence,
)
from experiments.argos_reproduction.error_conditioned_target_selection import (
    canonical_chunk_hash,
)


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs/argos_reproduction/task038b_repair_execution.json"


def test_exact_thirteen_static_valid_failed_rules_are_frozen() -> None:
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    records = load_repair_population(config)
    assert len(records) == 13
    assert all(item["initial_static_valid"] for item in records)
    assert all(not item["initial_executable"] for item in records)
    assert {item["initial_runtime_status"] for item in records} <= {
        "target_runtime_failed",
        "contrast_runtime_failed",
        "output_contract_failed",
    }


def test_error_sanitization_removes_host_paths_and_keeps_rule_line() -> None:
    evidence = sanitize_error_evidence(
        'File "/rule/generated_rule.py", line 12\n'
        "File C:\\Users\\private\\temp.py\n"
        "ValueError: operands could not be broadcast",
        failure_stage="target",
        timed_out=False,
    )
    serialized = json.dumps(evidence)
    assert "C:\\Users" not in serialized
    assert evidence["rule_line_number_if_available"] == 12
    assert evidence["failure_stage"] == "target"


def test_values_only_extraction_verifies_semantic_chunk_hash(tmp_path: Path) -> None:
    values = np.array([1.0, 2.0], dtype=np.float64)
    labels = np.array([0, 1], dtype=np.int8)
    indices = np.array([10, 11], dtype=np.int64)
    source = tmp_path / "source.npz"
    target = tmp_path / "values.npy"
    np.savez(source, values=values, labels=labels, indices=indices)

    digest = canonical_chunk_hash(values, labels, indices)
    _write_values_only(source, target, digest)
    extracted = np.load(target, allow_pickle=False)
    assert extracted.shape == (2, 1)

    with pytest.raises(
        RepairFailureReplayError,
        match="TASK038B_FROZEN_CHUNK_HASH_MISMATCH",
    ):
        _write_values_only(source, target, "0" * 64)


def test_failure_replay_report_is_aggregate_only_when_present() -> None:
    path = ROOT / "docs/task_reports/TASK-038B_FAILURE_REPLAY_REPORT.json"
    if not path.exists():
        return
    report = json.loads(path.read_text(encoding="utf-8"))
    assert report["frozen_repair_population"] == 13
    assert report["fresh_container_runs"] == 26
    assert report["labels_mounted"] is False
    assert report["inner_access"] is False
    assert report["outer_access"] is False
    assert report["sealed_test_access"] is False
