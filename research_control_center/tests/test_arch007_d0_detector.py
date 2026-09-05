import csv
import json
import unittest
from pathlib import Path


RCC = Path(__file__).resolve().parents[1]
ARCH = RCC / "architecture" / "07_d0_detector"


class Arch007D0DetectorTests(unittest.TestCase):
    def test_d0_contract_and_scientific_boundary(self):
        state = json.loads((RCC / "registry" / "current_state.yaml").read_text(encoding="utf-8"))
        d0 = state["d0_detector"]
        self.assertEqual("D0_PCA_SPE_V1", d0["detector_id"])
        self.assertEqual(37, d0["features"])
        self.assertEqual(0.95, d0["variance_target"])
        self.assertEqual(10, d0["selected_components"])
        self.assertFalse(d0["labels_used_in_fit_or_calibration"])
        self.assertEqual("PILOT_ONLY", d0["validation"])
        self.assertEqual("INCOMPLETE", d0["fresh_machine_reproducibility"])

    def test_threshold_and_freeze_are_explicit(self):
        state_machine = (ARCH / "ARCH_007_D0_STATE_MACHINE.md").read_text(encoding="utf-8")
        freeze = (ARCH / "ARCH_007_FREEZE_BOUNDARY.md").read_text(encoding="utf-8")
        self.assertIn("score == threshold", state_machine)
        self.assertIn("DURABLE_PREDICTION_FILE_BEFORE_LABEL", freeze)
        self.assertIn("byte", freeze.lower())

    def test_output_levels_remain_distinct(self):
        output = (ARCH / "ARCH_007_OUTPUT_LEVELS.md").read_text(encoding="utf-8")
        for value in ("876", "46", "7", "11 of 14", "0.4939336325682589"):
            self.assertIn(value, output)
        self.assertIn("not a point-level false-positive rate", output)

    def test_catalogs_are_safe_and_complete(self):
        def rows(name):
            with (ARCH / name).open("r", encoding="utf-8", newline="") as handle:
                return list(csv.DictReader(handle))
        functions = rows("ARCH_007_FUNCTION_CATALOG.csv")
        artifacts = rows("ARCH_007_ARTIFACT_LINEAGE.csv")
        contracts = rows("ARCH_007_IO_CONTRACTS.csv")
        self.assertGreaterEqual(len(functions), 14)
        self.assertGreaterEqual(len(artifacts), 8)
        self.assertGreaterEqual(len(contracts), 12)
        self.assertTrue(all(not Path(row["path"]).is_absolute() for row in functions))

    def test_generated_view_and_progression(self):
        state = json.loads((RCC / "registry" / "current_state.yaml").read_text(encoding="utf-8"))
        self.assertTrue(state["last_completed_task"] in {"ARCH-007", "ARCH-008", "ARCH-009", "ARCH-010", "GAP-000", "ARCH-011"} or state["last_completed_task"].startswith(("GAP-FIX-001", "GAP-FIX-002", "V2-PROTOCOL-001", "GAP-FIX-METRIC-001", "FRESH-MACHINE-SYNTHETIC", "VALIDATION-V2-RESUME-001", "V2-HAI", "V2-DUALTRACK-002", "V2-GDN-FRONT-EXP04-001", "V2-EVAL-EXPANSION-001", "EXP03-PROVIDER-EXEC-001", "EXP03B-PROVIDER-EXEC-001", "HAI-XVER-NORMAL-PREP-001", "XVER-T2-PROVIDER-EXEC-001", "MULTIPANEL-PRE-DG05-FREEZE-001", "DG05-EXEC-AUTHORITY-CLOSURE-001", "DG05-V2-METRIC-VERIFIER-CLOSURE-001")))
        self.assertTrue(state["exact_next_task"].startswith(("ARCH-008", "ARCH-009", "ARCH-010", "GAP-000", "ARCH-011", "GAP-FIX-001", "GAP-FIX-002", "V2-PROTOCOL-001", "GAP-FIX-METRIC-001", "EXP-01", "CUSTODY-RESTORE", "V2-HAI", "V2-EXEC-AUTH", "V2-SCI-EXP04", "DG-03", "DG-04", "HAI-XVER-NORMAL-PREP-001", "DG-XVER-PROVIDER", "MULTIPANEL-PRE-DG05-FREEZE-001", "DG-05")))
        summary = (RCC / "generated" / "ARCH_007_USER_SUMMARY.md").read_text(encoding="utf-8")
        self.assertIn("D0 PCA-SPE", summary)
        self.assertIn("stronger detector", summary)


if __name__ == "__main__":
    unittest.main()
