from experiments.argos_reproduction.task038e_repair_utility import (
    utility_classification,
)


def test_repair_utility_is_not_execution_recovery() -> None:
    assert utility_classification(0.6, 0.5) == "outer_useful"
    assert utility_classification(0.5, 0.5) == "outer_equal"
    assert utility_classification(0.4, 0.5) == "outer_regressive"
