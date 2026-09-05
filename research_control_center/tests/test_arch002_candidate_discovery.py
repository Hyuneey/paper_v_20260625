from __future__ import annotations

import csv
import json
import unittest
from pathlib import Path


RCC_ROOT = Path(__file__).resolve().parents[1]
ARCH = RCC_ROOT / "architecture" / "02_candidate_discovery"


def rows(name: str) -> list[dict[str, str]]:
    with (ARCH / name).open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


class Arch002CandidateDiscoveryTests(unittest.TestCase):
    def test_candidate_provenance_closes_exact_arm_counts(self) -> None:
        candidates = rows("ARCH_002_CANDIDATE_PROVENANCE.csv")
        self.assertEqual(47, len(candidates))
        self.assertEqual(47, len({row["pair_id"] for row in candidates}))
        self.assertEqual(47, len({(row["source"], row["target"]) for row in candidates}))
        for arm in ("meta_selected", "stat_selected", "gdn_selected"):
            self.assertEqual(20, sum(row[arm] == "true" for row in candidates))

    def test_overlap_decomposition_is_exact(self) -> None:
        candidates = rows("ARCH_002_CANDIDATE_PROVENANCE.csv")
        arm_counts = [int(row["arm_count"]) for row in candidates]
        self.assertEqual(34, arm_counts.count(1))
        self.assertEqual(13, arm_counts.count(2))
        self.assertEqual(0, arm_counts.count(3))
        self.assertEqual(18, sum(row["gdn_selected"] == "true" and row["arm_count"] == "1" for row in candidates))

    def test_gdn_authority_is_not_attention_or_xai(self) -> None:
        report = (ARCH / "ARCH_002_REPORT.md").read_text(encoding="utf-8")
        answer = (ARCH / "ARCH_002_GDN_PROFESSOR_ANSWER.md").read_text(encoding="utf-8")
        self.assertIn("embedding cosine", report)
        self.assertIn("attention coefficient", report)
        self.assertIn("post-hoc XAI", report)
        self.assertIn("후보를 순위화하거나 최종 관계 근거로 사용하지 않는다", answer)
        self.assertIn("별도 post-hoc XAI, SHAP", answer)

    def test_discovery_and_confirmation_are_separate(self) -> None:
        report = (ARCH / "ARCH_002_REPORT.md").read_text(encoding="utf-8")
        self.assertIn("relation_confirmation=not_evaluated", report)
        self.assertIn("후속 normal delayed-response profiling", report)
        self.assertNotIn("GDN found causal", report)

    def test_union_is_unscored_and_topk_rationale_is_bounded(self) -> None:
        report = (ARCH / "ARCH_002_REPORT.md").read_text(encoding="utf-8")
        self.assertIn("global score와 global scientific rank는 만들지 않는다", report)
        self.assertIn("RATIONALE_UNDOCUMENTED", report)
        self.assertIn("diagonal/self를 먼저 mask하거나 제거하지 않고", report)
        self.assertIn("내부 neighbor budget에 미치는 기능적 영향은 시험되지 않았다", report)

    def test_catalogs_are_populated_and_safe(self) -> None:
        functions = rows("ARCH_002_FUNCTION_CATALOG.csv")
        contracts = rows("ARCH_002_IO_CONTRACTS.csv")
        self.assertGreaterEqual(len(functions), 30)
        self.assertGreaterEqual(len(contracts), 7)
        self.assertTrue(all(not row["path"].startswith(("/", "\\")) and ".." not in row["path"] for row in functions))

    def test_current_state_preserves_scientific_boundary(self) -> None:
        state = json.loads((RCC_ROOT / "registry" / "current_state.yaml").read_text(encoding="utf-8"))
        discovery = state["candidate_discovery"]
        self.assertFalse(discovery["attention_as_final_evidence"])
        self.assertFalse(discovery["posthoc_xai_used"])
        self.assertEqual("unscored provenance-preserving set union of 47 unique pairs", discovery["union"])
        self.assertIn("GDN general utility", state["not_established"][0])
        self.assertTrue(state["exact_next_task"].startswith(("ARCH-005", "ARCH-006", "ARCH-007", "ARCH-008", "ARCH-009", "ARCH-010", "GAP-000", "ARCH-011", "GAP-FIX-001", "GAP-FIX-002", "V2-PROTOCOL-001", "GAP-FIX-METRIC-001", "EXP-01", "CUSTODY-RESTORE", "V2-HAI", "V2-EXEC-AUTH", "V2-SCI-EXP04", "DG-03", "DG-04", "HAI-XVER-NORMAL-PREP-001", "DG-XVER-PROVIDER", "MULTIPANEL-PRE-DG05-FREEZE-001", "DG-05")))

    def test_generated_user_and_dashboard_views_are_explicit(self) -> None:
        summary = (RCC_ROOT / "generated" / "ARCH_002_USER_SUMMARY.md").read_text(encoding="utf-8")
        dashboard = (RCC_ROOT / "dashboard" / "index.html").read_text(encoding="utf-8")
        self.assertIn("learned graph", summary)
        self.assertIn("20+20+20인데 왜 47개인가", summary)
        self.assertIn("관계 후보 탐색", dashboard)
        self.assertIn("META / STAT / GDN", dashboard)
        self.assertIn("Candidate Union", dashboard)
        self.assertIn("candidate는 confirmed relation이 아님", dashboard)


if __name__ == "__main__":
    unittest.main()
