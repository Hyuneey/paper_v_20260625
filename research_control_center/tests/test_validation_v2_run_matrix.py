from __future__ import annotations

import json
from pathlib import Path
import unittest

from paperworks.validation_v2.exp01_scientific_v1 import EXPECTED_SCHEDULE


ROOT = Path(__file__).resolve().parents[2]
MATRIX = (
    ROOT
    / "research_control_center"
    / "validation_v2"
    / "run_freeze"
    / "EXP01_EXP02_EXACT_RUN_MATRIX_V2.json"
)


class ValidationV2RunMatrixTest(unittest.TestCase):
    def setUp(self) -> None:
        self.document = json.loads(MATRIX.read_text(encoding="utf-8"))

    def test_exp01_schedule_exactly_replays_frozen_contract(self) -> None:
        observed = tuple(
            (row["arm"], row["view"], row["seed"])
            for row in self.document["exp01"]["runs"]
        )
        self.assertEqual(observed, EXPECTED_SCHEDULE)
        self.assertEqual(
            [row["order"] for row in self.document["exp01"]["runs"]],
            list(range(1, 13)),
        )
        self.assertEqual(self.document["exp01"]["run_count"], 12)

    def test_exp02_science_remains_fail_closed_on_three_bindings(self) -> None:
        gaps = self.document["exp02"]["pre_execution_contract_gaps"]
        self.assertEqual(len(gaps), 3)
        self.assertTrue(all(row["status"] == "UNRESOLVED" for row in gaps))
        self.assertTrue(all("EXP02_EXECUTION" in row["blocks"] for row in gaps))

    def test_forbidden_inputs_and_immutable_authorities(self) -> None:
        self.assertEqual(
            self.document["forbidden_inputs"],
            ["test1", "test2", "heldout", "labels", "provider"],
        )
        self.assertFalse(self.document["pilot_v1_mutation_allowed"])
        self.assertFalse(self.document["preregistration_mutation_allowed"])


if __name__ == "__main__":
    unittest.main()
