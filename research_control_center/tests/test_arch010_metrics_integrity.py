import csv
import json
import unittest
from pathlib import Path


RCC = Path(__file__).resolve().parents[1]
ARCH = RCC / "architecture" / "10_metrics_integrity"


class Arch010MetricsIntegrityTests(unittest.TestCase):
    def test_frozen_table_and_common_exposure(self) -> None:
        with (ARCH / "ARCH_010_FROZEN_PILOT_RESULTS.csv").open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        self.assertEqual(["D0", "D1", "D2_V1", "D2_V2"], [row["method"] for row in rows])
        self.assertEqual(["11", "13", "11", "11"], [row["detected_units"] for row in rows])
        self.assertEqual(["7", "574", "10", "98"], [row["normal_false_episodes"] for row in rows])
        self.assertTrue(all(row["normal_exposure_seconds"] == "51019" for row in rows))

    def test_metric_semantics_and_claim_boundary(self) -> None:
        event = (ARCH / "ARCH_010_EVENT_HIT_RULE.md").read_text(encoding="utf-8")
        method = (ARCH / "ARCH_010_METHOD_NORMALIZATION.md").read_text(encoding="utf-8")
        integrity = (ARCH / "ARCH_010_RESULT_INTEGRITY.md").read_text(encoding="utf-8")
        self.assertIn("PA-FREE", event)
        self.assertIn("SEMANTICALLY_EQUIVALENT", method)
        self.assertIn("FAIR_WITH_LIMITATIONS", method)
        self.assertIn("cannot establish", integrity)

    def test_state_progression_and_boundaries(self) -> None:
        state = json.loads((RCC / "registry" / "current_state.yaml").read_text(encoding="utf-8"))
        metrics = state["metric_integrity"]
        self.assertEqual(14, metrics["event_unit_count"])
        self.assertEqual("NOT_ESTABLISHED", metrics["event_independence"])
        self.assertEqual(51019, metrics["normal_exposure_seconds"])
        self.assertTrue(state["last_completed_task"] == "ARCH-011" or state["last_completed_task"].startswith(("GAP-FIX-001", "GAP-FIX-002")))
        self.assertTrue(state["exact_next_task"].startswith(("GAP-FIX-001", "GAP-FIX-002", "V2-PROTOCOL-001")))

    def test_generated_summary_is_plain_and_complete(self) -> None:
        summary = (RCC / "generated" / "ARCH_010_USER_SUMMARY.md").read_text(encoding="utf-8")
        for marker in ("alarm point", "51,019", "FAIR_WITH_LIMITATIONS", "integrity PASS", "ARCH-011"):
            self.assertIn(marker, summary)

    def test_mismatch_counts(self) -> None:
        payload = (ARCH / "ARCH_010_MISMATCHES.md").read_text(encoding="utf-8")
        self.assertIn("12 total", payload)
        self.assertIn("HIGH 5", payload)
        self.assertIn("MEDIUM 7", payload)


if __name__ == "__main__":
    unittest.main()
