from experiments.argos_reproduction.task038e_variant_consistency import (
    direction_label,
)


def test_variant_consistency_does_not_rank_variants() -> None:
    assert direction_label(1.0, 2.0) == "same_positive"
    assert direction_label(-1.0, -2.0) == "same_negative"
    assert direction_label(0.0, 0.0) == "both_zero"
    assert direction_label(1.0, -1.0) == "mixed"
