from __future__ import annotations

import inspect
import tempfile
import unittest
from pathlib import Path

import paperworks.profiling.task039d2_confirmation_v1 as synthetic
import paperworks.profiling.task039d2_real_execution_v1 as real


ROOT = Path(__file__).resolve().parents[1]


class TASK039D2RealBoundaryTests(unittest.TestCase):
    def test_synthetic_preparation_authority_remains_false(self) -> None:
        self.assertIs(synthetic.D2_REAL_EXECUTION_AUTHORIZED, False)

    def test_real_module_names_only_train3_data_file(self) -> None:
        source = inspect.getsource(real)
        self.assertIn('TRAIN3_RELATIVE_PATH = "hai-23.05/hai-train3.csv"', source)
        for forbidden in ("hai-train1.csv", "hai-train2.csv", "hai-train4.csv"):
            self.assertNotIn(forbidden, source)

    def test_external_roots_inside_repository_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as outside:
            with self.assertRaises(real.TASK039D2ExecutionError):
                real.validate_external_roots_v1(
                    repository_root=ROOT,
                    data_root_value=str(ROOT),
                    d1_private_value=outside,
                    d2_private_value=str(Path(outside) / "d2"),
                )

    def test_wrong_file_identity_fails_before_open(self) -> None:
        state = real.D2DataAccessStateV1()
        with self.assertRaisesRegex(real.TASK039D2ExecutionError, "data_boundary"):
            real.load_authorized_train3_values_v1(
                data_root=ROOT, expected={"relative_path": "hai-23.05/hai-train2.csv"}, state=state,
            )
        self.assertEqual(state.prohibited_access_count, 1)
        self.assertEqual(state.file_open_count, 0)


if __name__ == "__main__":
    unittest.main()
