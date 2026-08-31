import csv
import json
import unittest
from pathlib import Path


RCC = Path(__file__).resolve().parents[1]
ARCH = RCC / "architecture" / "06_runtime_trace_explanation"


def rows(name: str):
    with (ARCH / name).open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


class Arch006RuntimeTraceExplanationTests(unittest.TestCase):
    def test_runtime_outcomes_are_not_conflated(self):
        state_machine = (ARCH / "ARCH_006_RUNTIME_STATE_MACHINE.md").read_text(encoding="utf-8")
        taxonomy = (ARCH / "ARCH_006_OUTCOME_TAXONOMY.md").read_text(encoding="utf-8")
        self.assertIn("Non-trigger timestamps never become opportunities", state_machine)
        self.assertIn("evaluated_expected_response", taxonomy)
        self.assertIn("evaluated_anomaly", taxonomy)
        self.assertIn("system error", taxonomy)

    def test_alarm_counts_keep_three_levels_separate(self):
        prediction = (ARCH / "ARCH_006_D1_PREDICTION_SCHEMA.md").read_text(encoding="utf-8")
        self.assertIn("6,031", prediction)
        self.assertIn("788", prediction)
        self.assertIn("630", prediction)
        self.assertIn("626", prediction)
        self.assertIn("must not be described as 788 unique point alarms", prediction)

    def test_trace_is_not_renamed_canonical(self):
        trace = rows("ARCH_006_TRACE_SCHEMA.csv")
        self.assertGreaterEqual(len(trace), 14)
        self.assertTrue(any(row["semantic_equivalent"] == "NO" for row in trace))
        hashes = (ARCH / "ARCH_006_TRACE_HASH_CHAIN.md").read_text(encoding="utf-8")
        self.assertIn("NON_EQUIVALENT", hashes)
        self.assertIn("RuntimeTraceV1", hashes)

    def test_freeze_and_explanation_boundaries(self):
        freeze = (ARCH / "ARCH_006_D1_FREEZE_BOUNDARY.md").read_text(encoding="utf-8")
        explanation = (ARCH / "ARCH_006_EXPLANATION_RENDERER.md").read_text(encoding="utf-8")
        self.assertIn("SAFE_BUT_WEAKER_THAN_D0_D2", freeze)
        self.assertIn("Unsupported wording", freeze)
        self.assertIn("does not import or call the renderer", explanation)
        self.assertIn("UNVALIDATED", explanation)

    def test_state_dashboard_and_summary(self):
        state = json.loads((RCC / "registry" / "current_state.yaml").read_text(encoding="utf-8"))
        self.assertTrue(state["last_completed_task"] in {"ARCH-006", "ARCH-007", "ARCH-008", "ARCH-009", "ARCH-010", "GAP-000", "ARCH-011"} or state["last_completed_task"].startswith(("GAP-FIX-001", "GAP-FIX-002", "V2-PROTOCOL-001", "GAP-FIX-METRIC-001", "FRESH-MACHINE-SYNTHETIC", "VALIDATION-V2-RESUME-001")))
        self.assertTrue(state["exact_next_task"].startswith(("ARCH-007", "ARCH-008", "ARCH-009", "ARCH-010", "GAP-000", "ARCH-011", "GAP-FIX-001", "GAP-FIX-002", "V2-PROTOCOL-001", "GAP-FIX-METRIC-001", "EXP-01", "CUSTODY-RESTORE", "V2-HAI")))
        self.assertEqual(0, state["runtime_trace_explanation"]["llm_calls"])
        self.assertFalse(state["runtime_trace_explanation"]["durable_persistence"])
        dashboard = (RCC / "dashboard" / "index.html").read_text(encoding="utf-8")
        self.assertIn("D1 관계 규칙", dashboard)
        self.assertIn("LLM-free fixed-rule", dashboard)
        self.assertIn("D1은 T2 Agentic Rule-only가 아닙니다", dashboard)
        summary = (RCC / "generated" / "ARCH_006_USER_SUMMARY.md").read_text(encoding="utf-8")
        self.assertIn("630 unique alarm seconds", summary)
        self.assertTrue("ARCH-007" in summary or "ARCH-008" in summary or "ARCH-009" in summary or "ARCH-010" in summary or "GAP-000" in summary or "ARCH-011" in summary or "GAP-FIX-001" in summary or "GAP-FIX-002" in summary or "V2-PROTOCOL-001" in summary or "GAP-FIX-METRIC-001" in summary or "EXP-01-EXEC" in summary or "CUSTODY-RESTORE" in summary or "V2-HAI" in summary)


if __name__ == "__main__":
    unittest.main()
