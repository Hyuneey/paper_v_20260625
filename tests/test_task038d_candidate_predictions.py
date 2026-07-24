from experiments.argos_reproduction.branch_output_registry import ROOT
from experiments.argos_reproduction.branch_prediction_freeze import (
    freeze_candidate_predictions,
)


def test_all_357_candidate_predictions_verify_before_labels() -> None:
    report = freeze_candidate_predictions(
        ROOT / "configs/argos_reproduction/task038d_branch_selection.json"
    )
    assert report["candidate_prediction_record_count"] == 357
    assert report["detector_prediction_record_count"] == 20
    assert report["labels_loaded_during_freeze"] is False
    assert all(row["hash_verified"] for row in report["records"])
