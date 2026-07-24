from experiments.argos_reproduction.task038e_generalization_gap import (
    generalization_record,
)


def test_generalization_gap_uses_inner_minus_outer() -> None:
    row = generalization_record(
        branch="A3",
        variant="LSTMADalpha",
        arm="full_aggregator",
        inner_f1=0.8,
        outer_f1=0.5,
        a0_inner_f1=0.6,
        a0_outer_f1=0.4,
    )
    assert abs(row["generalization_gap"] - 0.3) < 1e-12
    assert abs(row["transfer_gap"] - 0.1) < 1e-12
