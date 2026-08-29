from __future__ import annotations

import csv
import unittest
from pathlib import Path


RCC_ROOT = Path(__file__).resolve().parents[1]
OVERVIEW = RCC_ROOT / "architecture" / "00_overview"


def rows(name: str) -> list[dict[str, str]]:
    with (OVERVIEW / name).open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


class Arch000ArchitectureTests(unittest.TestCase):
    def test_source_map_covers_all_components_once(self) -> None:
        source = rows("ARCH_000_SOURCE_MAP.csv")
        components = rows("../../registry/components.csv")
        self.assertEqual(32, len(source))
        self.assertEqual(32, len({row["component_id"] for row in source}))
        self.assertEqual({row["component_id"] for row in components}, {row["component_id"] for row in source})

    def test_verified_and_unknown_edges_are_explicit(self) -> None:
        dataflow = rows("ARCH_000_DATAFLOW.csv")
        self.assertEqual(35, sum(row["verified"] == "TRUE" for row in dataflow))
        self.assertEqual(10, sum(row["verified"] == "UNKNOWN" for row in dataflow))
        self.assertFalse(any(row["verified"] not in {"TRUE", "UNKNOWN"} for row in dataflow))

    def test_executed_representatives_are_not_conceptual_substitutes(self) -> None:
        source = {row["component_id"]: row for row in rows("ARCH_000_SOURCE_MAP.csv")}
        self.assertEqual("src/paperworks/v6/candidate_discovery_protocol_v1.py", source["VARIABLE_ROLE_UNIVERSE"]["path"])
        self.assertEqual("src/paperworks/v6/task039e0_validity_v2.py", source["DETERMINISTIC_VERIFIER"]["path"])
        self.assertEqual("execute_real_rule_v1:1509", source["RULE_RUNTIME"]["symbol"])
        self.assertEqual("RealRuleExecutionResultV1:665", source["SATISFACTION_TRACE"]["symbol"])
        self.assertIn("recovery", source["D2_V1"]["path"])
        self.assertEqual("RecoveryAttemptBoundaryV1:218", source["OUTER_EVALUATION"]["symbol"])

    def test_result_lineage_preserves_required_qualifications(self) -> None:
        lineage = (OVERVIEW / "ARCH_000_RESULT_LINEAGE.md").read_text(encoding="utf-8")
        self.assertIn("PERSISTED_PREDICTION_BEFORE_LABEL", lineage)
        self.assertIn("LABEL_BLIND_PREDICTION_OBJECT_BUILT_AND_VALIDATED_BEFORE_LABEL", lineage)
        self.assertIn("execute_authorized_d2_inner_recovery_v1", lineage)
        self.assertIn("composite completion", lineage.lower())
        self.assertIn("No scientific result was recomputed", lineage)

    def test_mermaid_keeps_unverified_links_visible(self) -> None:
        mermaid = (OVERVIEW / "ARCH_000_ARCHITECTURE.mmd").read_text(encoding="utf-8")
        self.assertTrue(mermaid.startswith("flowchart LR"))
        self.assertIn("not selected for utility", mermaid)
        self.assertIn("typed RuntimeTraceV1 link not found", mermaid)
        self.assertIn("BLOCKED · NO RESULT", mermaid)
        self.assertIn("custody and policy mediated", mermaid)
        self.assertIn("artifact/equivalence mediated", mermaid)

    def test_no_overall_completion_or_scientific_promotion(self) -> None:
        report = (OVERVIEW / "ARCH_000_REPORT.md").read_text(encoding="utf-8")
        user = (RCC_ROOT / "generated" / "ARCH_000_USER_SUMMARY.md").read_text(encoding="utf-8")
        self.assertIn("Critical은 0", report)
        self.assertIn("pilot", user)
        self.assertIn("아직 검증되지 않았다", user)


if __name__ == "__main__":
    unittest.main()
