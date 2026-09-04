from __future__ import annotations

import csv
import json
import unittest
from pathlib import Path


RCC_ROOT = Path(__file__).resolve().parents[1]
ARCH = RCC_ROOT / "architecture" / "01_data_and_splits"
ALLOWED = {"READ_ALLOWED", "READ_NOT_USED", "FORBIDDEN", "UNKNOWN", "NOT_APPLICABLE"}


def rows(name: str) -> list[dict[str, str]]:
    with (ARCH / name).open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


class Arch001DataAndSplitTests(unittest.TestCase):
    def test_leakage_matrix_has_complete_valid_cells(self) -> None:
        matrix = rows("ARCH_001_LEAKAGE_MATRIX.csv")
        self.assertGreaterEqual(len(matrix), 20)
        self.assertEqual(len(matrix), len({row["stage"] for row in matrix}))
        for row in matrix:
            self.assertTrue(all(value in ALLOWED for key, value in row.items() if key != "stage"))

    def test_normal_only_and_label_boundaries_are_explicit(self) -> None:
        matrix = {row["stage"]: row for row in rows("ARCH_001_LEAKAGE_MATRIX.csv")}
        for stage in ("STAT discovery", "GDN training", "relation profiling", "numeric authority"):
            self.assertEqual("READ_ALLOWED", matrix[stage]["train1_features"])
            self.assertEqual("READ_ALLOWED", matrix[stage]["train2_features"])
            self.assertEqual("FORBIDDEN", matrix[stage]["test1_labels"])
        self.assertEqual("READ_ALLOWED", matrix["metric calculation"]["test1_labels"])
        self.assertEqual("FORBIDDEN", matrix["D0 test prediction"]["test1_labels"])
        self.assertEqual("FORBIDDEN", matrix["D1 runtime"]["test1_labels"])
        self.assertEqual("FORBIDDEN", matrix["D2 fusion"]["test1_labels"])

    def test_train3_dual_role_and_train4_sanity_are_visible(self) -> None:
        matrix = {row["stage"]: row for row in rows("ARCH_001_LEAKAGE_MATRIX.csv")}
        self.assertEqual("READ_ALLOWED", matrix["relation confirmation"]["train3_features"])
        self.assertEqual("READ_ALLOWED", matrix["D0 calibration"]["train3_features"])
        self.assertEqual("READ_ALLOWED", matrix["D0 normal sanity"]["train4_features"])

    def test_catalogs_are_populated_and_safe(self) -> None:
        contracts = rows("ARCH_001_INPUT_CONTRACTS.csv")
        functions = rows("ARCH_001_FUNCTION_CATALOG.csv")
        self.assertGreaterEqual(len(contracts), 15)
        self.assertGreaterEqual(len(functions), 20)
        self.assertEqual(len(contracts), len({row["contract_id"] for row in contracts}))
        self.assertTrue(all(row["path"].startswith("src/paperworks/") for row in functions))
        self.assertFalse(any(".." in row["path"] or "\\" in row["path"] for row in functions))

    def test_d1_durable_gap_and_d2v2_pilot_reuse_are_not_hidden(self) -> None:
        timeline = (ARCH / "ARCH_001_LABEL_ACCESS_TIMELINE.md").read_text(encoding="utf-8")
        mismatch = (ARCH / "ARCH_001_MISMATCHES.md").read_text(encoding="utf-8")
        self.assertIn("durable prediction-file-before-label ordering", timeline)
        self.assertIn("NOT VERIFIED / IMPLEMENTATION GAP", timeline)
        self.assertIn("label-informed policy", timeline)
        self.assertIn("ARCH001-M01", mismatch)
        self.assertIn("ARCH001-M04", mismatch)

    def test_outer_boundary_reports_attempt_but_zero_bytes(self) -> None:
        timeline = (ARCH / "ARCH_001_LABEL_ACCESS_TIMELINE.md").read_text(encoding="utf-8")
        self.assertIn("feature file custody access attempts: `1`", timeline)
        self.assertIn("feature bytes read: `0`", timeline)
        self.assertIn("scientific outcome: **unavailable**", timeline)

    def test_current_state_exposes_data_governance_without_claim_upgrade(self) -> None:
        state = json.loads((RCC_ROOT / "registry" / "current_state.yaml").read_text(encoding="utf-8"))
        governance = state["data_governance"]
        self.assertEqual("HAI 23.05", governance["dataset"])
        self.assertEqual(6, len(governance["splits"]))
        self.assertIn("NO VERIFIED LEAKAGE FOUND", governance["leakage_status"])
        self.assertEqual("pilot_only", state["scientific_result_status"])
        self.assertEqual("unconfirmed", state["held_out_generalization"])
        self.assertTrue(state["exact_next_task"].startswith(("ARCH-005", "ARCH-006", "ARCH-007", "ARCH-008", "ARCH-009", "ARCH-010", "GAP-000", "ARCH-011", "GAP-FIX-001", "GAP-FIX-002", "V2-PROTOCOL-001", "GAP-FIX-METRIC-001", "EXP-01", "CUSTODY-RESTORE", "V2-HAI", "V2-EXEC-AUTH", "V2-SCI-EXP04", "DG-03", "DG-04")))


if __name__ == "__main__":
    unittest.main()
