from pathlib import Path


def test_final_claim_matrix_contains_all_required_claim_boundaries() -> None:
    text = Path(
        "docs/argos_reproduction/ARGOS_CLAIM_MATRIX_FINAL.md"
    ).read_text(encoding="utf-8")
    required = (
        "LLM rules can be generated",
        "Frozen rules can execute deterministically",
        "RepairAgent can recover runtime failures",
        "RepairAgent improves detection performance",
        "ReviewAgent improves inner performance",
        "Review improvements can transfer to outer",
        "Selected Review rules all transferred positively in this study",
        "Repair+Review is superior to one-shot",
        "Full Aggregator is superior to detector-only",
        "FP correction safely removes false positives",
        "ARGOS is exactly reproduced",
        "ARGOS methodology is partially supported",
        "Proposed multivariate method is validated",
        "Sealed-test superiority is established",
    )
    for claim in required:
        assert claim in text
    assert "Prohibited stronger wording" in text
    assert "A3 is the final winner" in text
    assert "Exact ARGOS reproduction" in text
