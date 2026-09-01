from __future__ import annotations

import importlib.util
import unittest
from unittest.mock import patch

import numpy as np

from paperworks.gdn.exp01_upstream_backend_v2 import (
    _FileLocalLazyWindows,
    replay_exp01_checkpoint_graph_v2,
    train_exp01_seed_v2,
)
from paperworks.gdn.upstream_candidate_backend_v1 import UpstreamGDNTrainingConfigV1
from paperworks.validation_v2.exp01_scientific_v1 import PAIR_UNIVERSE, ArmId
from paperworks.v6.task039e3_r2r_d0_detector_design_v1 import P1_FEATURE_ORDER


class _FakeTensor:
    def __init__(self, value) -> None:
        self.value = np.asarray(value, dtype=np.float32)

    def contiguous(self):
        self.value = np.ascontiguousarray(self.value)
        return self

    def transpose(self, left: int, right: int):
        return _FakeTensor(np.swapaxes(self.value, left, right))

    def __len__(self) -> int:
        return len(self.value)

    def __getitem__(self, index):
        return _FakeTensor(self.value[index])

    @property
    def dtype(self):
        return self.value.dtype

    def tolist(self):
        return self.value.tolist()


class _FakeTorch:
    float32 = np.float32

    def __init__(self) -> None:
        self.as_tensor_calls = 0

    def as_tensor(self, value, *, dtype):
        self.as_tensor_calls += 1
        self.last_dtype = dtype
        return _FakeTensor(value)


class Exp01PreparedInputWithoutOptionalTorchTests(unittest.TestCase):
    def test_one_conversion_per_segment_and_exact_window_order(self) -> None:
        torch = _FakeTorch()
        segments = (
            np.arange(18, dtype=np.float64).reshape(6, 3),
            np.arange(15, dtype=np.float64).reshape(5, 3),
        )
        dataset = _FileLocalLazyWindows(segments, window=2, stride=1, torch_module=torch)
        observed = [(dataset[index][0].tolist(), dataset[index][1].tolist()) for index in range(len(dataset))]
        self.assertEqual(torch.as_tensor_calls, 2)
        self.assertEqual(len(observed), 7)
        self.assertEqual(observed[0], ([[0.0, 3.0], [1.0, 4.0], [2.0, 5.0]], [6.0, 7.0, 8.0]))
        self.assertEqual(observed[-1], ([[6.0, 9.0], [7.0, 10.0], [8.0, 11.0]], [12.0, 13.0, 14.0]))


@unittest.skipUnless(importlib.util.find_spec("torch"), "torch is optional outside the approved EXP-01 environment")
class Exp01BackendV2Tests(unittest.TestCase):
    def test_lazy_windows_match_file_local_eager_order(self) -> None:
        import torch

        segments = (
            ((1.0, 10.0), (2.0, 20.0), (3.0, 30.0), (4.0, 40.0)),
            ((5.0, 50.0), (6.0, 60.0), (7.0, 70.0)),
        )
        dataset = _FileLocalLazyWindows(segments, window=2, stride=1, torch_module=torch)
        self.assertEqual(len(dataset), 3)
        x0, y0 = dataset[0]
        x2, y2 = dataset[2]
        self.assertEqual(x0.tolist(), [[1.0, 2.0], [10.0, 20.0]])
        self.assertEqual(y0.tolist(), [3.0, 30.0])
        self.assertEqual(x2.tolist(), [[5.0, 6.0], [50.0, 60.0]])
        self.assertEqual(y2.tolist(), [7.0, 70.0])

    def test_input_tensor_conversion_occurs_once_per_segment(self) -> None:
        import torch

        segments = (
            np.arange(18, dtype=np.float64).reshape(6, 3),
            np.arange(15, dtype=np.float64).reshape(5, 3),
        )
        original = torch.as_tensor
        calls = 0

        def counted(*args, **kwargs):
            nonlocal calls
            calls += 1
            return original(*args, **kwargs)

        with patch.object(torch, "as_tensor", side_effect=counted):
            dataset = _FileLocalLazyWindows(segments, window=2, stride=1, torch_module=torch)
            for _ in range(3):
                for index in range(len(dataset)):
                    x, y = dataset[index]
                    self.assertEqual(x.dtype, torch.float32)
                    self.assertEqual(y.dtype, torch.float32)
        self.assertEqual(calls, len(segments))

    def test_checkpoint_graph_replay_matches_training_graph_without_retraining(self) -> None:
        values = np.arange(50 * 37, dtype=np.float32).reshape(50, 37) / 1000.0
        config = UpstreamGDNTrainingConfigV1()
        trained = train_exp01_seed_v2(
            arm_id=ArmId.CORRECTED_SELF_EXCLUDED,
            segments=(values,),
            feature_order=P1_FEATURE_ORDER,
            candidate_pairs=PAIR_UNIVERSE,
            seed=11,
            config=config,
        )
        replayed = replay_exp01_checkpoint_graph_v2(
            arm_id=ArmId.CORRECTED_SELF_EXCLUDED,
            state_dict=trained.best_state_dict,
            segments=(values,),
            feature_order=P1_FEATURE_ORDER,
            candidate_pairs=PAIR_UNIVERSE,
            seed=11,
            config=config,
        )
        self.assertEqual(replayed.graph_edges, trained.graph_edges)
        self.assertEqual(replayed.forward_graph_hash, trained.forward_graph_hash)
        self.assertEqual(replayed.extraction_graph_hash, trained.extraction_graph_hash)


if __name__ == "__main__":
    unittest.main()
