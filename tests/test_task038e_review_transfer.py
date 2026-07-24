from experiments.argos_reproduction.task038e_review_transfer import (
    review_summary,
    transfer_classification,
)


def test_review_transfer_classification_is_exact() -> None:
    assert transfer_classification(0.1, 0.2) == "positive_transfer"
    assert transfer_classification(0.1, 0.0) == "no_transfer"
    assert transfer_classification(0.1, -0.2) == "negative_transfer"
    assert transfer_classification(-0.1, 0.2) == "inner_regression_outer_recovery"
    assert transfer_classification(0.0, 0.0) == "same"


def test_review_summary_keeps_all_pairs() -> None:
    rows = [
        {
            "inner_F1_delta": 0.1,
            "outer_F1_delta": -0.1,
            "transfer_classification": "negative_transfer",
        }
    ]
    assert review_summary(rows)["reviewed_executable_count"] == 1
