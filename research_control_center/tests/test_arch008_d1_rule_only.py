import csv
import json
import unittest
from pathlib import Path


RCC = Path(__file__).resolve().parents[1]
ARCH = RCC / "architecture" / "08_d1_rule_only"


class Arch008D1RuleOnlyTests(unittest.TestCase):
    def test_d1_counts_and_scientific_boundary(self):
        state = json.loads((RCC / "registry" / "current_state.yaml").read_text(encoding="utf-8"))
        d1 = state["d1_evaluation"]
        self.assertEqual("COMMON-42 Verified Relational Rule-only", d1["preferred_name"])
        self.assertEqual((6031, 788, 630, 626, 574), (
            d1["opportunities"], d1["anomalous_rule_records"], d1["unique_alarm_seconds"],
            d1["total_alarm_episodes"], d1["normal_false_episodes"],
        ))
        self.assertEqual((13, 14), (d1["attack_events_detected"], d1["pilot_events"]))
        self.assertIn("UNVALIDATED", d1["rule_only_utility"])
        self.assertFalse(d1["durable_freeze"])

    def test_overlap_is_exact_frozen_partition(self):
        with (ARCH / "ARCH_008_D0_D1_OVERLAP.csv").open("r", encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        self.assertEqual([("BOTH", "10"), ("D0_ONLY", "1"), ("D1_ONLY", "3"), ("NEITHER", "0")], [(row["category"], row["count"]) for row in rows])

    def test_count_levels_and_metric_semantics(self):
        text = (ARCH / "ARCH_008_OUTPUT_LEVELS.md").read_text(encoding="utf-8")
        for marker in ("6,031", "788", "630", "626", "574", "40.50255787059723"):
            self.assertIn(marker, text)
        self.assertIn("not point FPR", text)
        attack = (ARCH / "ARCH_008_ATTACK_EVENT_EVALUATION.md").read_text(encoding="utf-8")
        self.assertIn("half-open interval overlap", attack)
        self.assertIn("neither precision nor attack-point recall", attack)

    def test_claim_and_terminology_boundaries(self):
        utility = (ARCH / "ARCH_008_RULE_ONLY_UTILITY.md").read_text(encoding="utf-8")
        complementarity = (ARCH / "ARCH_008_COMPLEMENTARITY_BOUNDARY.md").read_text(encoding="utf-8")
        professor = (ARCH / "ARCH_008_PROFESSOR_RULE_ONLY_NOTE.md").read_text(encoding="utf-8")
        self.assertIn("UNVALIDATED", utility)
        self.assertIn("PILOT", complementarity)
        self.assertIn("T2 Agentic Rule-only", professor)

    def test_progression_and_generated_summary(self):
        state = json.loads((RCC / "registry" / "current_state.yaml").read_text(encoding="utf-8"))
        self.assertTrue(state["last_completed_task"] in {"ARCH-008", "ARCH-009", "ARCH-010", "GAP-000", "ARCH-011"} or state["last_completed_task"].startswith(("GAP-FIX-001", "GAP-FIX-002", "V2-PROTOCOL-001", "GAP-FIX-METRIC-001", "FRESH-MACHINE-SYNTHETIC", "VALIDATION-V2-RESUME-001", "V2-HAI")))
        self.assertTrue(state["exact_next_task"].startswith(("ARCH-009", "ARCH-010", "GAP-000", "ARCH-011", "GAP-FIX-001", "GAP-FIX-002", "V2-PROTOCOL-001", "GAP-FIX-METRIC-001", "EXP-01", "CUSTODY-RESTORE", "V2-HAI", "V2-EXEC-AUTH")))
        summary = (RCC / "generated" / "ARCH_008_USER_SUMMARY.md").read_text(encoding="utf-8")
        self.assertIn("13/14", summary)
        self.assertIn("Agentic Rule-only", summary)


if __name__ == "__main__":
    unittest.main()
