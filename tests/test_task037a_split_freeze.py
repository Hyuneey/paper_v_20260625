import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_detector_split_and_threshold_freeze():
    config = json.loads((ROOT / "configs/argos_reproduction/task037a_detector_audit.json").read_text())
    split = config["split_policy"]
    assert split["detector_fit_split"] == "generation"
    assert split["normalization_fit_split"] == "generation"
    assert split["training_label_policy"] == "contaminated_training"
    assert split["inner_variant_selection"] == "prohibited"
    assert split["test"] == "sealed_not_accessed"
    threshold = config["threshold_policy"]
    assert threshold["score_split"] == "inner"
    assert threshold["selection_metric"] == "PA_free_point_F1"
    assert threshold["point_adjustment"] is False


def test_existing_rule_panel_is_hash_bound_and_unchanged():
    config = json.loads((ROOT / "configs/argos_reproduction/task037a_detector_audit.json").read_text())
    panel = config["frozen_rule_panel"]
    assert panel["selected_kpi_count"] == 10
    assert panel["rules_per_kpi"] == 10
    assert panel["total_panel_rules"] == 100
    assert len(panel["panel_report_hash"]) == len(panel["selection_report_hash"]) == 64
