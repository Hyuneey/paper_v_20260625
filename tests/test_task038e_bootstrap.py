from experiments.argos_reproduction.task038e_bootstrap import branch_bootstrap


def _fixture() -> dict:
    return {
        f"k{i}": {
            branch: {
                "precision": i / 10 + offset,
                "recall": i / 10 + offset,
                "point_f1": i / 10 + offset,
                "event_f1": i / 10 + offset,
                "false_positive_points_per_10000_normal_points": i + offset,
            }
            for branch, offset in {"A0": 0.0, "A1": 0.1, "A2": 0.2, "A3": 0.3}.items()
        }
        for i in range(10)
    }


def test_bootstrap_is_deterministic_for_frozen_seed() -> None:
    assert branch_bootstrap(_fixture(), seed=20260726, resamples=100) == branch_bootstrap(
        _fixture(), seed=20260726, resamples=100
    )
