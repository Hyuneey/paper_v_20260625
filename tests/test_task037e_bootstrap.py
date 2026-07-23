from __future__ import annotations

from experiments.argos_reproduction.paired_kpi_bootstrap import (
    paired_percentile_bootstrap,
)


def test_task037e_bootstrap_policy_is_deterministic() -> None:
    first = paired_percentile_bootstrap(
        [0.2, 0.4, 0.6],
        [0.1, 0.5, 0.3],
        seed=20260725,
        resamples=10000,
    )
    second = paired_percentile_bootstrap(
        [0.2, 0.4, 0.6],
        [0.1, 0.5, 0.3],
        seed=20260725,
        resamples=10000,
    )
    assert first == second
    assert first["bootstrap_seed"] == 20260725
