import csv
import json
import unittest
from pathlib import Path


RCC = Path(__file__).resolve().parents[1]
ARCH = RCC / "architecture" / "09_d2_fusion"


class Arch009D2FusionTests(unittest.TestCase):
    def test_state_records_exact_frozen_results(self):
        state = json.loads((RCC / "registry" / "current_state.yaml").read_text(encoding="utf-8"))
        d2 = state["d2_fusion"]
        self.assertEqual(14, d2["event_unit_count"])
        self.assertIn("independence not established", d2["event_unit_definition"])
        self.assertEqual(("11/14", 0.7056194750975128, "0/3"), (
            d2["v1"]["attack_event_response"], d2["v1"]["normal_far_episodes_per_hour"],
            d2["v1"]["d0_miss_recovery"],
        ))
        self.assertEqual(("11/14", 6.915070855955625, "0/3"), (
            d2["v2"]["attack_event_response"], d2["v2"]["normal_far_episodes_per_hour"],
            d2["v2"]["d0_miss_recovery"],
        ))
        self.assertTrue(d2["v1"]["durable_pre_label_freeze"])
        self.assertTrue(d2["v2"]["durable_pre_label_freeze"])
        self.assertFalse(d2["v2"]["independent_confirmation"])

    def test_policy_semantics_are_explicit(self):
        v1 = (ARCH / "ARCH_009_V1_POLICY.md").read_text(encoding="utf-8")
        v2 = (ARCH / "ARCH_009_V2_POLICY.md").read_text(encoding="utf-8")
        self.assertIn("decision_physical_row_index", v1)
        self.assertIn("at least two distinct sources", v1)
        self.assertIn("i <= t <= i + h", v2)
        self.assertIn("TEST1_INFORMED_DEVELOPMENT", v2)

    def test_comparison_and_claim_boundaries(self):
        with (ARCH / "ARCH_009_POLICY_COMPARISON.csv").open("r", encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        by_dimension = {row["dimension"]: row for row in rows}
        self.assertEqual("YES; pointwise OR", by_dimension["D0 preserved"]["V1"])
        self.assertEqual("NO; V1/test1 diagnostic informed formulation", by_dimension["designed before test1 outcome"]["V2"])
        claims = (ARCH / "ARCH_009_CLAIM_MATRIX.csv").read_text(encoding="utf-8")
        self.assertIn("NOT_SUPPORTED_BY_CURRENT_PILOT_METRICS", claims)
        self.assertIn("UNVALIDATED_OVERGENERALIZATION", claims)

    def test_miss_recovery_and_generated_summary(self):
        miss = (ARCH / "ARCH_009_MISS_RECOVERY.md").read_text(encoding="utf-8")
        self.assertIn("RECOVERY_MISS_01", miss)
        self.assertIn("SINGLE_SOURCE_ONLY", miss)
        self.assertIn("D1 response does not imply D2 policy admission", miss)
        summary = (RCC / "generated" / "ARCH_009_USER_SUMMARY.md").read_text(encoding="utf-8")
        for marker in ("same-second", "native horizon", "0/3", "GAP-000"):
            self.assertIn(marker, summary)

    def test_progression(self):
        state = json.loads((RCC / "registry" / "current_state.yaml").read_text(encoding="utf-8"))
        self.assertEqual("ARCH-010", state["last_completed_task"])
        self.assertTrue(state["exact_next_task"].startswith("GAP-000"))


if __name__ == "__main__":
    unittest.main()
