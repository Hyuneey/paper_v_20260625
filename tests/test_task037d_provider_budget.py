from pathlib import Path

from experiments.argos_reproduction.error_conditioned_provider_capture import (
    approval_blockers,
)
from experiments.argos_reproduction.expanded_kpi_cohort import read_json


ROOT = Path(__file__).resolve().parents[1]


def test_exact_provider_budget_matches_frozen_manifest(monkeypatch) -> None:
    config = read_json(ROOT / "configs/argos_reproduction/task037d_error_conditioned_rules.json")
    approval = read_json(ROOT / "configs/argos_reproduction/task037d_provider_approval.json")
    manifest = read_json(ROOT / config["reports"]["requests"])
    monkeypatch.setenv(approval["credential_env_var"], "synthetic-test-key")
    assert manifest["registered_slot_count"] == 96
    assert config["design"]["exact_frozen_slot_count"] == 96
    assert approval["maximum_requests"] == 96
    assert approval_blockers(config, approval, True) == []


def test_no_retry_or_replacement_budget_exists() -> None:
    approval = read_json(ROOT / "configs/argos_reproduction/task037d_provider_approval.json")
    assert approval["automatic_retry"] is False
    assert approval["manual_retry"] is False
    assert approval["replacement_generation"] is False
