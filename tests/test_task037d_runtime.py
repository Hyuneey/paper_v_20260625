from pathlib import Path

import numpy as np

from experiments.argos_reproduction.error_conditioned_rule_runtime import _values_only


def test_runtime_materialization_strips_labels_and_predictions(tmp_path: Path) -> None:
    source = tmp_path / "chunk.npz"
    target = tmp_path / "values.npy"
    np.savez(
        source,
        values=np.array([1.0, 2.0]),
        labels=np.array([1, 0]),
        indices=np.array([10, 11]),
    )
    digest = _values_only(source, target)
    values = np.load(target, allow_pickle=False)
    assert values.shape == (2, 1)
    assert digest
    assert not (tmp_path / "labels.npy").exists()


def test_runtime_source_does_not_compute_detection_metrics() -> None:
    source = (
        Path(__file__).resolve().parents[1]
        / "experiments/argos_reproduction/error_conditioned_rule_runtime.py"
    ).read_text(encoding="utf-8")
    assert "direct_pa_free_metrics" not in source
    assert "fusion" not in source.lower().replace('"fusion_execution": false', "")
