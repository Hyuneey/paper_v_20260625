from __future__ import annotations

import csv
import json
import unittest
from collections import Counter
from pathlib import Path


RCC = Path(__file__).resolve().parents[1]
GAP = RCC / "architecture" / "gap_000_pre_validation"
BOOT = RCC / "bootstrap" / "GAP_000"


def read_csv(name: str) -> list[dict[str, str]]:
    with (GAP / name).open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


class Gap000PreValidationTests(unittest.TestCase):
    def test_complete_raw_inventory(self) -> None:
        rows = read_csv("GAP_000_RAW_FINDINGS.csv")
        self.assertEqual(120, len(rows))
        self.assertEqual(Counter({"MEDIUM": 55, "HIGH": 54, "LOW": 11}), Counter(row["source_severity"] for row in rows))
        self.assertEqual(
            {"ARCH-000":15,"ARCH-001":8,"ARCH-002":7,"ARCH-003":9,"ARCH-004":10,"ARCH-005":11,"ARCH-006":13,"ARCH-007":10,"ARCH-008":13,"ARCH-009":12,"ARCH-010":12},
            Counter(row["source_arch"] for row in rows),
        )

    def test_root_merge_is_complete_and_dispositioned_once(self) -> None:
        raw = read_csv("GAP_000_RAW_FINDINGS.csv")
        roots = read_csv("GAP_000_ROOT_ISSUES.csv")
        matrix = read_csv("GAP_000_REMEDIATION_MATRIX.csv")
        root_ids = {row["gap_id"] for row in roots}
        self.assertEqual(19, len(root_ids))
        self.assertEqual(root_ids, {row["gap_id"] for row in matrix})
        self.assertTrue(all(row["duplicate_group"] in root_ids for row in raw))
        self.assertTrue(all(row["status"] == "TRIAGED_NOT_IMPLEMENTED" for row in matrix))
        self.assertEqual(2, sum(row["disposition"] == "P0_FIX_BEFORE_EXPANDED_VALIDATION" for row in matrix))
        self.assertEqual(3, sum(row["disposition"] == "P1_FIX_BEFORE_SPECIFIC_EXPERIMENT" for row in matrix))

    def test_experiment_gates_and_pilot_preservation(self) -> None:
        gates = {row["experiment_id"]: row["ready_now"] for row in read_csv("GAP_000_EXPERIMENT_GATES.csv")}
        self.assertEqual("READY_WITH_CONDITIONS", gates["EXP-02"])
        self.assertEqual("NOT_REQUIRED", gates["EXP-06"])
        self.assertEqual("BLOCKED", gates["NEW-HELD-OUT"])
        report = (GAP / "GAP_000_REPORT.md").read_text(encoding="utf-8")
        self.assertIn("No audited defect proves the frozen INNER pilot invalid", report)
        self.assertIn("PILOT V1", report)
        self.assertIn("VALIDATION V2", report)

    def test_registry_dashboard_and_user_summary(self) -> None:
        state = json.loads((RCC / "registry" / "current_state.yaml").read_text(encoding="utf-8"))
        self.assertTrue(state["last_completed_task"].startswith(("GAP-FIX-001", "GAP-FIX-002", "V2-PROTOCOL-001", "GAP-FIX-METRIC-001", "FRESH-MACHINE-SYNTHETIC", "VALIDATION-V2-RESUME-001", "V2-HAI", "V2-DUALTRACK-002", "V2-GDN-FRONT-EXP04-001", "V2-EVAL-EXPANSION-001", "EXP03-PROVIDER-EXEC-001", "EXP03B-PROVIDER-EXEC-001", "HAI-XVER-NORMAL-PREP-001", "XVER-T2-PROVIDER-EXEC-001", "MULTIPANEL-PRE-DG05-FREEZE-001", "DG05-EXEC-AUTHORITY-CLOSURE-001", "DG05-V2-METRIC-VERIFIER-CLOSURE-001", "DG05-PRODUCTION-CHAIN-CLOSURE-001")))
        self.assertTrue(state["exact_next_task"].startswith(("GAP-FIX-002", "V2-PROTOCOL-001", "GAP-FIX-METRIC-001", "EXP-01", "CUSTODY-RESTORE", "V2-HAI", "V2-EXEC-AUTH", "V2-SCI-EXP04", "DG-03", "DG-04", "HAI-XVER-NORMAL-PREP-001", "DG-XVER-PROVIDER", "MULTIPANEL-PRE-DG05-FREEZE-001", "DG-05")))
        self.assertEqual("BEFORE_REMEDIATION_READ_ONLY", state["pre_validation_readiness"]["arch011_position"])
        dashboard = (RCC / "dashboard" / "index.html").read_text(encoding="utf-8")
        for marker in ("준비도·위험", "Primary disposition", "Urgency", "조건부 진행 가능", "PILOT V1"):
            self.assertIn(marker, dashboard)
        summary = (RCC / "generated" / "GAP_000_USER_SUMMARY.md").read_text(encoding="utf-8")
        for marker in ("본격 실험 전에", "PILOT V1", "VALIDATION V2", "primary disposition", "Urgency priority"):
            self.assertIn(marker, summary)

    def test_bootstrap_evidence_and_agent_reviews(self) -> None:
        evidence = json.loads((BOOT / "GAP_000_EVIDENCE.json").read_text(encoding="utf-8"))
        self.assertEqual(0, evidence["invalidated_artifacts"])
        self.assertTrue(all(value == 0 for value in evidence["safety"].values()))
        for name in (
            "agent_a_scientific_validity.json", "agent_b_code_authority.json",
            "agent_c_governance_reproducibility.json", "agent_d_claim_scope.json", "agent_e_qa.json",
        ):
            payload = json.loads((BOOT / "agents" / name).read_text(encoding="utf-8"))
            self.assertIn("verdict", payload)


if __name__ == "__main__":
    unittest.main()
