from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from paperworks.profiling.task039d2_real_execution_v1 import (
    TASK039D2ExecutionError,
    load_d1_private_inputs_v1,
)


class TASK039D2PrivateInputTests(unittest.TestCase):
    def test_private_root_requires_exact_three_task_owned_ledgers(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "unrelated.json").write_text("{}", encoding="utf-8")
            with self.assertRaisesRegex(TASK039D2ExecutionError, "private_input_binding"):
                load_d1_private_inputs_v1(root)


if __name__ == "__main__":
    unittest.main()
