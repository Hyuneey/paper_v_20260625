from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_invalid_review_never_falls_back_to_parent() -> None:
    source = (
        ROOT / "experiments/argos_reproduction/review_branch_update.py"
    ).read_text(encoding="utf-8")
    assert '"output_rule_hash_or_null": reviewed_hash' in source
    assert '"harmful_revision_reverted": False' in source
    assert '"A0_unchanged": True' in source
    assert '"A1_unchanged": True' in source
