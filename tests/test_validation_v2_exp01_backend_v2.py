from __future__ import annotations

import importlib.util
import unittest

import numpy as np

from paperworks.gdn.exp01_upstream_backend_v2 import (
    _FileLocalLazyWindows,
    replay_exp01_checkpoint_graph_v2,
    train_exp01_seed_v2,
)
from paperworks.gdn.upstream_candidate_backend_v1 import UpstreamGDNTrainingConfigV1
from paperworks.validation_v2.exp01_scientific_v1 import PAIR_UNIVERSE, ArmId
from paperworks.v6.task039e3_r2r_d0_detector_design_v1 import P1_FEATURE_ORDER


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
