import numpy as np

from experiments.argos_reproduction.easytsad_lstm_adapter import normalize_values


def test_generation_fitted_min_max_and_clip():
    values = normalize_values(np.array([-30.0, 0.0, 5.0, 30.0]), 0.0, 5.0)
    assert values.tolist() == [-2.0, 0.0, 1.0, 3.0]


def test_constant_normalization_is_finite():
    result = normalize_values(np.array([4.0, 4.0]), 4.0, 4.0)
    assert np.all(np.isfinite(result))
    assert result.tolist() == [0.0, 0.0]
