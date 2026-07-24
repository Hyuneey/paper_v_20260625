from experiments.argos_reproduction.direct_event_metrics import direct_pa_free_metrics
from experiments.argos_reproduction.task038e_branch_metrics import _summary


def test_branch_summary_keeps_macro_micro_and_distribution() -> None:
    rows = [
        direct_pa_free_metrics([0, 1, 1, 0], [0, 1, 0, 1]),
        direct_pa_free_metrics([0, 1, 1, 0], [0, 1, 1, 0]),
    ]
    report = _summary(rows)
    assert set(report) == {"macro", "micro", "distribution"}
    assert report["micro"]["true_positive"] == 3
    assert report["distribution"]["point_f1"]["minimum"] <= report["macro"]["point_f1"]
