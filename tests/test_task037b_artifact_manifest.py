import json
from pathlib import Path

from experiments.argos_reproduction.lstm_detector_artifacts import (
    build_final_manifest,
    ensure_report_safe,
)


ROOT = Path(__file__).resolve().parents[1]
HASH = "a" * 64


def test_complete_manifest_uses_both_co_primary_variants_without_selection():
    config = json.loads((ROOT / "configs/argos_reproduction/task037b_dual_lstm_detector_validation.json").read_text())
    hashes = {name: HASH for name in (
        "checkpoint_hash", "normalization_hash", "generation_score_hash", "inner_score_hash",
        "outer_score_hash", "generation_prediction_hash", "inner_prediction_hash",
        "outer_prediction_hash", "incorrect_indices_generation_hash",
    )}
    document = build_final_manifest(
        config, variant="LSTMADalpha", kpi_id="synthetic-kpi",
        split_manifest_hash=HASH, threshold=0.5, threshold_protocol_hash=HASH, hashes=hashes,
    )
    assert document["artifact_status"] == "complete"
    assert document["detector_role"] == "paper_aligned_family_sensitivity"
    ensure_report_safe({"records": [document]})
