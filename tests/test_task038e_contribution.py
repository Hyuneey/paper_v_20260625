from experiments.argos_reproduction.task038e_contribution_accounting import (
    fn_direction_contribution,
    fp_direction_contribution,
    full_aggregator_contribution,
)


def test_directional_contribution_reports_benefit_and_cost() -> None:
    truth = [0, 1, 0, 1]
    detector = [1, 0, 1, 1]
    fn = [1, 1, 1, 1]
    fp = [0, 0, 1, 1]
    assert fn_direction_contribution(truth, detector, fn)["FN_points_recovered"] == 1
    fp_row = fp_direction_contribution(truth, detector, fp)
    assert fp_row["FP_points_removed"] == 1
    assert fp_row["true_positive_points_removed"] == 0
    full = full_aggregator_contribution(truth, detector, fp, [1, 1, 1, 1])
    assert "FP_correction_changes_overridden_by_FN" in full
