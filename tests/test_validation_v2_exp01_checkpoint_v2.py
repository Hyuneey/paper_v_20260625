from __future__ import annotations

import importlib.util
from pathlib import Path
import tempfile
import unittest

from paperworks.validation_v2.exp01_checkpoint_v2 import (
    Exp01CheckpointError,
    canonical_state_hash_v2,
    persist_private_checkpoint_v2,
    reopen_private_checkpoint_v2,
)


@unittest.skipUnless(importlib.util.find_spec("torch"), "torch is optional outside the approved EXP-01 environment")
class Exp01CheckpointV2Tests(unittest.TestCase):
    def test_atomic_checkpoint_reopens_and_detects_mutation(self) -> None:
        import torch

        state = {"weight": torch.tensor([[1.0, 2.0]], dtype=torch.float32)}
        with tempfile.TemporaryDirectory() as directory:
            path, receipt = persist_private_checkpoint_v2(
                private_root=Path(directory), run_id="run_01", arm_id="ARM", view_id="VIEW",
                seed=11, code_authority_hash="a" * 64, training_config_hash="b" * 64,
                state_dict=state,
            )
            payload = reopen_private_checkpoint_v2(path, expected_receipt=receipt)
            self.assertEqual(canonical_state_hash_v2(payload["state_dict"]), receipt.state_hash)
            with path.open("ab") as handle:
                handle.write(b"mutation")
            with self.assertRaises(Exp01CheckpointError):
                reopen_private_checkpoint_v2(path, expected_receipt=receipt)


if __name__ == "__main__":
    unittest.main()
