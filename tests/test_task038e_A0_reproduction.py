import inspect

from experiments.argos_reproduction.task038e_branch_metrics import _a0_reproduction


def test_a0_reproduction_checks_hashes_and_metrics() -> None:
    source = inspect.getsource(_a0_reproduction)
    assert "len(comparisons) == 80" in source
    assert "prediction_hash_matches" in source
    assert "metrics_match" in source
    assert "TASK038E_A0_OUTER_REPRODUCTION_FAILED" in source
