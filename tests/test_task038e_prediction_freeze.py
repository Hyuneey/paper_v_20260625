import inspect

from experiments.argos_reproduction import task038e_outer_prediction_freeze as freeze


def test_prediction_freeze_precedes_label_access() -> None:
    source = inspect.getsource(freeze.freeze_outer_predictions)
    assert "outer_labels_path" not in source
    assert "logical_branch_arm_predictions" in source
    assert "all_outer_predictions_frozen_before_labels" in source
    assert "review_transfer_pairs" in source
    assert "repair_utility_rules" in source
