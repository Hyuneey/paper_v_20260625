from __future__ import annotations

from experiments.argos_reproduction.paired_kpi_bootstrap import (
    paired_percentile_bootstrap,
)


def test_task037c_bootstrap_is_deterministic_for_frozen_seed() -> None:
    left = [0.1, 0.4, 0.2, 0.9, 0.3, 0.6, 0.5, 0.8, 0.7, 1.0]
    right = [0.0, 0.3, 0.3, 0.8, 0.2, 0.7, 0.4, 0.8, 0.6, 0.9]
    first = paired_percentile_bootstrap(
        left, right, seed=20260724, resamples=10000
    )
    second = paired_percentile_bootstrap(
        left, right, seed=20260724, resamples=10000
    )
    assert first == second
    assert first["bootstrap_seed"] == 20260724
    assert first["method"] == "percentile_paired_bootstrap"
