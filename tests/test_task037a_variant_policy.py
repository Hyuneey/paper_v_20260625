import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_variant_policy_is_dual_arm_and_non_performance_selected():
    config = json.loads((ROOT / "configs/argos_reproduction/task037a_detector_audit.json").read_text())
    policy = config["variant_policy"]
    assert policy["retained_variants"] == ["LSTMADalpha", "LSTMADbeta"]
    assert policy["selection_between_variants"] == "prohibited"
    assert policy["detector_role"] == "paper_aligned_family_sensitivity"


def test_future_experiments_are_not_authorized():
    freeze = json.loads((ROOT / "configs/argos_reproduction/task037a_future_e4_e5_e6_freeze.json").read_text())
    assert freeze["authorization"] == "protocol_frozen_execution_not_authorized"
    assert freeze["e4"]["real_training"] == "not_run"
    assert freeze["e5"]["diagnostic_track"] == "frozen_not_run"
    assert freeze["e6"]["paper_faithful_track"] == "not_prepared"
