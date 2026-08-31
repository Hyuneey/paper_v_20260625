from __future__ import annotations

import csv
import json
import unittest
from pathlib import Path


RCC = Path(__file__).resolve().parents[1]
ARCH = RCC / "architecture" / "11_outer_reproducibility"
BOOT = RCC / "bootstrap" / "ARCH_011"


class Arch011OuterReproducibilityTests(unittest.TestCase):
    def test_outer_custody_and_retry_boundary(self) -> None:
        evidence = json.loads((BOOT / "ARCH_011_EVIDENCE.json").read_text(encoding="utf-8"))
        old = evidence["old_outer"]
        self.assertEqual("UNAVAILABLE", old["result"])
        self.assertEqual("NOT_RETRYABLE_BY_PROTOCOL", old["retryability"])
        self.assertEqual(1, old["feature_custody_checks"])
        self.assertEqual(0, old["feature_byte_reads"])
        self.assertEqual(0, old["label_accesses"])
        self.assertEqual(0, old["predictions"])
        self.assertEqual(0, old["metrics"])

    def test_reproduction_levels_are_separated(self) -> None:
        payload = (ARCH / "ARCH_011_REPRODUCTION_LEVELS.md").read_text(encoding="utf-8")
        for marker in ("Traceability", "Same-machine", "Fresh-machine synthetic", "Fresh-machine scientific", "Independent external"):
            self.assertIn(marker, payload)
        self.assertIn("NOT YET DEMONSTRATED", payload)

    def test_environment_and_portability_contracts(self) -> None:
        with (ARCH / "ARCH_011_ENVIRONMENT_MATRIX.csv").open(encoding="utf-8", newline="") as handle:
            env = list(csv.DictReader(handle))
        with (ARCH / "ARCH_011_ARTIFACT_PORTABILITY.csv").open(encoding="utf-8", newline="") as handle:
            assets = list(csv.DictReader(handle))
        self.assertTrue(any(row["dependency"] == "NumPy" and row["risk"] == "HIGH" for row in env))
        self.assertTrue(any(row["release"] == "EXCLUDE" for row in assets))
        self.assertTrue(any("no persisted GDN model checkpoint" in row["notes"] for row in assets))

    def test_historical_authority_recommendation_and_current_resolution(self) -> None:
        with (ARCH / "ARCH_011_AUTHORITY_OPTIONS.csv").open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        self.assertEqual(3, len(rows))
        self.assertEqual("RECOMMENDED_PROSPECTIVE_TARGET_PENDING_DEC020", rows[2]["assessment"])
        state = json.loads((RCC / "registry" / "current_state.yaml").read_text(encoding="utf-8"))
        self.assertIn("DEC-020 RESOLVED", state["outer_reproducibility"]["authority_preference"])

    def test_registry_dashboard_safety_and_next_task(self) -> None:
        state = json.loads((RCC / "registry" / "current_state.yaml").read_text(encoding="utf-8"))
        self.assertTrue(state["last_completed_task"].startswith(("GAP-FIX-001", "GAP-FIX-002", "V2-PROTOCOL-001", "GAP-FIX-METRIC-001")))
        self.assertTrue(state["exact_next_task"].startswith(("GAP-FIX-002", "V2-PROTOCOL-001", "GAP-FIX-METRIC-001", "EXP-01")))
        self.assertEqual(8, len(state["user_todo_items"]))
        dashboard = (RCC / "dashboard" / "index.html").read_text(encoding="utf-8")
        for marker in ("OUTER·재현성", "new preregistered validation required", "Primary disposition", "Urgency"):
            self.assertIn(marker, dashboard)
        evidence = json.loads((BOOT / "ARCH_011_EVIDENCE.json").read_text(encoding="utf-8"))
        self.assertTrue(all(value == 0 for value in evidence["safety"].values()))


if __name__ == "__main__":
    unittest.main()
