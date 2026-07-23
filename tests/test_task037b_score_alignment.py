import numpy as np
import pytest

from experiments.argos_reproduction.easytsad_lstm_adapter import (
    EasyTsadAdapterError,
    align_scores,
)


def test_frozen_zero_left_prefix_alignment():
    aligned = align_scores(np.array([1.0, 2.0]), 5, 3)
    assert aligned.tolist() == [0.0, 0.0, 0.0, 1.0, 2.0]


def test_nonfinite_and_length_mismatch_fail_closed():
    with pytest.raises(EasyTsadAdapterError):
        align_scores(np.array([np.nan]), 4, 3)
    with pytest.raises(EasyTsadAdapterError):
        align_scores(np.array([1.0]), 5, 3)
