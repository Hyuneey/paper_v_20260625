from __future__ import annotations

import importlib.util
import unittest

from paperworks.gdn.exp01_upstream_backend_v2 import _FileLocalLazyWindows


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


if __name__ == "__main__":
    unittest.main()
