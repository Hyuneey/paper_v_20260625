from __future__ import annotations

import csv
import json
import unittest
from pathlib import Path


RCC = Path(__file__).resolve().parents[1]
ARCH = RCC / "architecture" / "04_rule_construction"


def rows(name: str) -> list[dict[str, str]]:
    with (ARCH / name).open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


class ARCH004RuleConstructionTests(unittest.TestCase):
    def test_arm_outcomes_are_explicit_relation_level_states(self) -> None:
        outcomes = rows("ARCH_004_ARM_OUTCOMES.csv")
        self.assertEqual(["T0", "T1", "T1-B", "T2"], [row["arm"] for row in outcomes])
        self.assertEqual([42, 42, 42, 39], [int(row["task_specific_admissible"]) for row in outcomes])
        self.assertEqual([0, 42, 126, 42], [int(row["LLM_calls"]) for row in outcomes])
        self.assertEqual("0", outcomes[3]["feedback_actions"])
        self.assertEqual("0", outcomes[3]["retrieval_actions"])
        self.assertTrue(all(row["runtime_authorized"] == "false" for row in outcomes))

    def test_evidence_and_dsl_boundaries_are_visible(self) -> None:
        evidence = (ARCH / "ARCH_004_EVIDENCE_PACK_SCHEMA.md").read_text(encoding="utf-8")
        dsl = (ARCH / "ARCH_004_RULE_DSL.md").read_text(encoding="utf-8")
        for phrase in ("raw HAI", "labels", "test1 outcomes", "numeric_bindings[10]"):
            self.assertIn(phrase, evidence)
        for phrase in ("arbitrary Python", "canonical_rule_materialized=false", "runtime authorization", "no_rule"):
            self.assertIn(phrase, dsl)

    def test_t2_and_agentic_claim_are_conservative(self) -> None:
        loop = (ARCH / "ARCH_004_T2_FEEDBACK_LOOP.md").read_text(encoding="utf-8")
        claim = (ARCH / "ARCH_004_AGENTIC_CLAIM_BOUNDARY.md").read_text(encoding="utf-8")
        self.assertIn("maximum three", loop)
        self.assertIn("zero revise actions", loop)
        self.assertIn("feedback improved rule quality", claim)
        self.assertIn("Forbidden", claim)
        self.assertIn("HIGH contract mismatch", loop)
        mismatch = (ARCH / "ARCH_004_MISMATCHES.md").read_text(encoding="utf-8")
        self.assertIn("response/schema failure", mismatch)

    def test_catalogs_and_flow_are_closed(self) -> None:
        self.assertGreaterEqual(len(rows("ARCH_004_FUNCTION_CATALOG.csv")), 20)
        self.assertGreaterEqual(len(rows("ARCH_004_IO_CONTRACTS.csv")), 10)
        self.assertEqual(4, len(rows("ARCH_004_EVIDENCE_LINEAGE.csv")))
        flow = (ARCH / "ARCH_004_RULE_CONSTRUCTION_FLOW.mmd").read_text(encoding="utf-8")
        self.assertTrue(flow.startswith("flowchart "))
        self.assertIn("revise 0 / retrieve 0", flow)

    def test_current_state_and_generated_view(self) -> None:
        state = json.loads((RCC / "registry" / "current_state.yaml").read_text(encoding="utf-8"))
        self.assertIn(state["last_completed_task"], {"ARCH-004", "ARCH-005", "ARCH-006", "ARCH-007", "ARCH-008"})
        self.assertTrue(state["exact_next_task"].startswith(("ARCH-005", "ARCH-006", "ARCH-007", "ARCH-008", "ARCH-009")))
        self.assertEqual(0, state["rule_construction_authority"]["observed_feedback_actions"])
        summary = (RCC / "generated" / "ARCH_004_USER_SUMMARY.md").read_text(encoding="utf-8")
        self.assertIn("39/42", summary)
        self.assertIn("runtime authorization", summary)


if __name__ == "__main__":
    unittest.main()
