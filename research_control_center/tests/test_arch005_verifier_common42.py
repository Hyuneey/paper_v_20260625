import csv
import json
import unittest
from pathlib import Path


RCC = Path(__file__).resolve().parents[1]
ARCH = RCC / "architecture" / "05_verifier_common42"


def rows(name: str):
    with (ARCH / name).open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


class Arch005VerifierCommon42Tests(unittest.TestCase):
    def test_twenty_ordered_verifier_stages(self):
        stages = rows("ARCH_005_VERIFIER_STAGES.csv")
        self.assertEqual(20, len(stages))
        self.assertEqual(list(range(1, 21)), [int(row["stage_order"]) for row in stages])
        self.assertTrue(all(row["no_rule_possible"] == "no" for row in stages))

    def test_task_and_canonical_are_not_conflated(self):
        text = (ARCH / "ARCH_005_RULE_LIFECYCLE.md").read_text(encoding="utf-8")
        self.assertIn("PARTIALLY_OVERLAPPING", text)
        self.assertIn("NON_EQUIVALENT_BY_DESIGN", text)
        self.assertIn("No tracked bridge", text)

    def test_common42_and_t2_boundary(self):
        mapping = {row["arm"]: row for row in rows("ARCH_005_ARM_PORTFOLIO_MAPPING.csv")}
        self.assertEqual("42", mapping["T0"]["task_specific_accepted"])
        self.assertEqual("shared_projection_only", mapping["T0"]["D1_used"])
        self.assertEqual("39", mapping["T2"]["task_specific_accepted"])
        self.assertEqual("no", mapping["T2"]["D1_used"])
        common = (ARCH / "ARCH_005_COMMON42.md").read_text(encoding="utf-8")
        self.assertIn("CanonicalRuleDescriptorV4", common)
        self.assertIn("T0, T1 and T1-B", common)
        disposition = (ARCH / "ARCH_005_HIGH_RISK_DISPOSITION.md").read_text(encoding="utf-8")
        self.assertIn("DEFER_TO_ARCH_006", disposition)
        self.assertIn("REQUIRES_CODE_FIX", disposition)

    def test_runtime_authority_and_no_rule_are_separate(self):
        runtime = (ARCH / "ARCH_005_RUNTIME_AUTHORIZATION.md").read_text(encoding="utf-8")
        taxonomy = (ARCH / "ARCH_005_NO_RULE_TAXONOMY.md").read_text(encoding="utf-8")
        self.assertIn("Frozen D1 does not use that bundle", runtime)
        self.assertIn("`VerifierV1` never emits `no_rule`", taxonomy)
        self.assertIn("VALIDITY_UNSUPPORTED_VARIABLE", taxonomy)

    def test_state_and_generated_summary(self):
        state = json.loads((RCC / "registry" / "current_state.yaml").read_text(encoding="utf-8"))
        self.assertTrue(state["last_completed_task"] in {"ARCH-005", "ARCH-006", "ARCH-007", "ARCH-008", "ARCH-009", "ARCH-010", "GAP-000", "ARCH-011"} or state["last_completed_task"].startswith(("GAP-FIX-001", "GAP-FIX-002", "V2-PROTOCOL-001", "GAP-FIX-METRIC-001", "FRESH-MACHINE-SYNTHETIC", "VALIDATION-V2-RESUME-001", "V2-HAI", "V2-DUALTRACK-002", "V2-GDN-FRONT-EXP04-001", "V2-EVAL-EXPANSION-001", "EXP03-PROVIDER-EXEC-001", "EXP03B-PROVIDER-EXEC-001")))
        self.assertTrue(state["exact_next_task"].startswith(("ARCH-006", "ARCH-007", "ARCH-008", "ARCH-009", "ARCH-010", "GAP-000", "ARCH-011", "GAP-FIX-001", "GAP-FIX-002", "V2-PROTOCOL-001", "GAP-FIX-METRIC-001", "EXP-01", "CUSTODY-RESTORE", "V2-HAI", "V2-EXEC-AUTH", "V2-SCI-EXP04", "DG-03", "DG-04", "HAI-XVER-NORMAL-PREP-001")))
        self.assertEqual("COMMON-42 Verified Relational Rule-only", state["verifier_common42_authority"]["preferred_d1_term"])
        summary = (RCC / "generated" / "ARCH_005_USER_SUMMARY.md").read_text(encoding="utf-8")
        self.assertIn("COMMON-42", summary)
        self.assertIn("runtime authorization", summary)


if __name__ == "__main__":
    unittest.main()
