from __future__ import annotations

import json
from pathlib import Path

from experiments.argos_reproduction.review_parent_registry import (
    build_parent_registry,
)


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs/argos_reproduction/task038c_review_inner_experiment.json"


def test_parent_registry_has_exact_structural_population(tmp_path: Path) -> None:
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    config["reports"]["parent_registry"] = str(tmp_path / "registry.json")
    local = tmp_path / "config.json"
    local.write_text(json.dumps(config), encoding="utf-8")
    report = build_parent_registry(local)
    assert report["all_branch_record_count"] == 192
    assert report["A2_executable_parent_count"] == 83
    assert report["A2_nonapplicable_count"] == 13
    assert report["A3_executable_parent_count"] == 96
    assert report["A3_repaired_parent_count"] == 13
    assert report["total_executable_review_branch_parents"] == 179


def test_repaired_a3_parents_use_task038b_hashes(tmp_path: Path) -> None:
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    config["reports"]["parent_registry"] = str(tmp_path / "registry.json")
    local = tmp_path / "config.json"
    local.write_text(json.dumps(config), encoding="utf-8")
    report = build_parent_registry(local)
    repaired = [
        row for row in report["records"] if row["parent_type"] == "repaired_executable"
    ]
    assert len(repaired) == 13
    assert all(row["branch_id"] == "A3" and row["repair_reuse_key"] for row in repaired)
