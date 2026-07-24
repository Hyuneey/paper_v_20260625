from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_a2_a3_variability_is_not_labeled_repair_effect() -> None:
    source = (
        ROOT / "experiments/argos_reproduction/review_stochastic_replicates.py"
    ).read_text(encoding="utf-8")
    assert "independent_Review_generation_variability_not_Repair_effect" in source
    assert "same_prompt_payload_hash" in source
    assert "different_branch_request_hash" in source
