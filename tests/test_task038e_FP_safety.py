from experiments.argos_reproduction.task038e_branch_metrics import (
    _fp_safety_classifications,
)


def test_fp_safety_never_hides_true_positive_removal() -> None:
    assert _fp_safety_classifications(2, 0, 0, 0.1) == [
        "safe_FP_correction"
    ]
    assert "costly_FP_correction" in _fp_safety_classifications(2, 1, 0, 0.1)
    assert "harmful_FP_correction" in _fp_safety_classifications(2, 0, 1, 0.1)
    assert _fp_safety_classifications(0, 0, 0, 0.0) == [
        "ineffective_FP_correction"
    ]
