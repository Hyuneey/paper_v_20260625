from __future__ import annotations

import csv
import json
import unittest
from pathlib import Path


RCC_ROOT = Path(__file__).resolve().parents[1]
ARCH = RCC_ROOT / "architecture" / "03_relation_and_numeric"


def rows(name: str) -> list[dict[str, str]]:
    with (ARCH / name).open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


class Arch003RelationNumericTests(unittest.TestCase):
    def test_lineage_preserves_fit_and_confirmation_stages(self) -> None:
        state = json.loads((RCC_ROOT / "registry" / "current_state.yaml").read_text(encoding="utf-8"))
        relation = state["relation_numeric_authority"]
        self.assertEqual(47, relation["candidate_pairs"])
        self.assertEqual(94, relation["directional_opportunities"])
        self.assertEqual((25, 45), (relation["fit_supported_pair_contexts"], relation["fit_supported_directions"]))
        self.assertEqual((23, 42), (relation["confirmed_pair_contexts"], relation["confirmed_directions"]))

    def test_numeric_roles_separate_construction_and_runtime(self) -> None:
        numeric = rows("ARCH_003_NUMERIC_AUTHORITY.csv")
        construction = [row for row in numeric if row["construction_or_runtime"] == "construction"]
        runtime = [row for row in numeric if row["construction_or_runtime"] == "runtime"]
        self.assertEqual(11, len(construction))
        self.assertEqual(10, len(runtime))
        self.assertIn("selected_delay_horizon_seconds", {row["field_name"] for row in construction})
        self.assertNotIn("selected_delay_horizon_seconds", {row["field_name"] for row in runtime})

    def test_authority_report_distinguishes_value_and_identity(self) -> None:
        report = (ARCH / "ARCH_003_CONSTRUCTION_RUNTIME_AUTHORITY.md").read_text(encoding="utf-8")
        self.assertIn("420 exact E1 numeric matches", report)
        self.assertIn("authority versions and reference identities remain different", report)
        self.assertIn("no runtime authority", report)

    def test_confirmation_is_one_way_and_noncausal(self) -> None:
        report = (ARCH / "ARCH_003_REPORT.md").read_text(encoding="utf-8")
        self.assertIn("retuning, alternate horizon, opposite-direction search, fallback", report)
        self.assertIn("causal", report)
        self.assertIn("single-link", report)

    def test_catalogs_and_mermaid_are_safe_and_complete(self) -> None:
        functions = rows("ARCH_003_FUNCTION_CATALOG.csv")
        contracts = rows("ARCH_003_IO_CONTRACTS.csv")
        self.assertGreaterEqual(len(functions), 20)
        self.assertGreaterEqual(len(contracts), 9)
        self.assertTrue(all(not row["path"].startswith(("/", "\\")) and ".." not in row["path"] for row in functions))
        mermaid = (ARCH / "ARCH_003_RELATION_FLOW.mmd").read_text(encoding="utf-8")
        self.assertIn("25 fit-supported contexts", mermaid)
        self.assertIn("42 directional relations", mermaid)

    def test_generated_views_show_relation_numeric_boundary(self) -> None:
        dashboard = (RCC_ROOT / "dashboard" / "index.html").read_text(encoding="utf-8")
        summary = (RCC_ROOT / "generated" / "ARCH_003_USER_SUMMARY.md").read_text(encoding="utf-8")
        self.assertIn("RELATION &amp; NUMERIC AUTHORITY", dashboard)
        self.assertIn("Runtime-bound", dashboard)
        self.assertIn("value equality", summary)
        self.assertIn("causal relation", summary)


if __name__ == "__main__":
    unittest.main()
