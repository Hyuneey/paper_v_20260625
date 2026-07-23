import pytest

from experiments.argos_reproduction.detector_artifact_contract import (
    DetectorArtifactContractError,
    argos_compatibility_layout,
    validate_detector_manifest,
)


H = "a" * 64


def manifest():
    return {
        "detector_id": "DET-SYNTHETIC",
        "detector_family": "LSTMAD",
        "detector_variant": "LSTMADalpha",
        "detector_role": "paper_aligned_family_sensitivity",
        "source_commit": "55eff2c6d62f9c792bf6253c046dcc04636efe5a",
        "source_file_hashes": [("method.py", H)],
        "config_hash": H,
        "environment_hash": H,
        "seed": 7,
        "kpi_id": "synthetic-kpi-id",
        "split_manifest_hash": H,
        "checkpoint_hash": H,
        "normalization_hash": H,
        "generation_score_hash": H,
        "inner_score_hash": H,
        "outer_score_hash": H,
        "generation_prediction_hash": H,
        "inner_prediction_hash": H,
        "outer_prediction_hash": H,
        "threshold": 0.25,
        "threshold_protocol_hash": H,
        "incorrect_indices_generation_hash": H,
        "artifact_status": "complete",
    }


def test_complete_future_manifest_validates_without_test_artifact():
    result = validate_detector_manifest(manifest())
    assert result.detector_variant == "LSTMADalpha"
    layout = argos_compatibility_layout("curve-id")
    assert layout["train_labels"] == "TrainLabels/curve-id.npy"
    assert layout["test_labels"] == "prohibited_until_joint_sealed_test_approval"


def test_unknown_field_and_bad_hash_fail_closed():
    value = manifest(); value["unexpected"] = True
    with pytest.raises(DetectorArtifactContractError):
        validate_detector_manifest(value)
    value = manifest(); value["checkpoint_hash"] = "bad"
    with pytest.raises(DetectorArtifactContractError):
        validate_detector_manifest(value)
