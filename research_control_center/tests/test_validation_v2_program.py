from __future__ import annotations

import csv
import json
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
V2 = ROOT / "research_control_center" / "validation_v2"


class ValidationV2ProgramTests(unittest.TestCase):
    def test_program_state_preserves_v1_and_held_out_boundary(self) -> None:
        state = json.loads((V2 / "PROGRAM_STATE.json").read_text(encoding="utf-8"))
        self.assertEqual(state["pilot_v1_status"], "IMMUTABLE")
        self.assertEqual(state["validation_v2_authority_policy"], "FORMAL_V4")
        self.assertEqual(state["test1_role"], "DEVELOPMENT_ONLY")
        self.assertFalse(state["held_out_authorized"])
        self.assertEqual(state["safety_counters"]["test2_accesses"], 0)

    def test_task_branches_do_not_conflict_with_integration_ref(self) -> None:
        with (V2 / "TASK_INDEX.csv").open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        branches = {row["branch"] for row in rows}
        self.assertIn("validation-v2", branches)
        self.assertTrue(all("validation-v2/" not in branch for branch in branches))

    def test_decision_gates_record_user_choices(self) -> None:
        text = (V2 / "DECISION_GATES.md").read_text(encoding="utf-8")
        self.assertIn("RESOLVED_FORMAL_V4", text)
        self.assertIn("RESOLVED_ISOLATION_FOREST", text)
        self.assertIn("DG-05", text)

    def test_pilot_v1_preservation_verifier_passes(self) -> None:
        python = Path(__import__("sys").executable)
        completed = subprocess.run(
            [
                str(python),
                str(
                    ROOT
                    / "research_control_center"
                    / "scripts"
                    / "verify_validation_v2_pilot_preservation.py"
                ),
                "--repo-root",
                str(ROOT),
            ],
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        self.assertIn("PILOT_V1_PRESERVATION_PASS", completed.stdout)


if __name__ == "__main__":
    unittest.main()
