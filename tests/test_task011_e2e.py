from __future__ import annotations

import ast
from pathlib import Path
import unittest

from paperworks.e2e import run_task011_template_feasibility


class Task011EndToEndTests(unittest.TestCase):
    def test_template_feasibility_smoke_passes(self) -> None:
        report = run_task011_template_feasibility()

        self.assertTrue(report.passed)
        self.assertEqual(report.phase_gate_recommendation, "proceed_to_phase_gate_b_review")
        self.assertTrue(report.checks["candidate_edges_obey_C_i"])
        self.assertTrue(report.checks["runtime_alarm_generated"])
        self.assertTrue(report.checks["final_test_sealed"])
        self.assertTrue(report.detailed_case_study)

    def test_artifact_provenance_graph_is_complete(self) -> None:
        report = run_task011_template_feasibility()
        graph = report.artifact_graph

        for key in (
            "dataset_manifest",
            "data_view",
            "train_split",
            "calibration_split",
            "candidate_universe",
            "gdn_checkpoint",
            "gdn_candidate_edges",
        ):
            self.assertIn(key, graph)
            self.assertEqual(len(graph[key]), 64)

    def test_attempted_pairs_include_supported_and_unsupported(self) -> None:
        report = run_task011_template_feasibility()
        statuses = {attempt.status for attempt in report.attempted_pairs}

        self.assertIn("verified", statuses)
        self.assertIn("unsupported", statuses)

    def test_no_test_access_audit(self) -> None:
        report = run_task011_template_feasibility()

        self.assertFalse(report.restricted_data_audit["final_test_accessed"])
        self.assertFalse(report.restricted_data_audit["raw_swat_rows_loaded"])
        self.assertFalse(report.restricted_data_audit["llm_called"])

    def test_deterministic_rerun_comparison(self) -> None:
        first = run_task011_template_feasibility()
        second = run_task011_template_feasibility()

        self.assertEqual(first.to_dict(), second.to_dict())
        self.assertEqual(first.report_id, second.report_id)

    def test_runtime_import_boundary_check(self) -> None:
        runtime_root = Path("src/paperworks/runtime")
        imported_modules: set[str] = set()
        for path in runtime_root.rglob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imported_modules.update(alias.name for alias in node.names)
                elif isinstance(node, ast.ImportFrom) and node.module is not None:
                    imported_modules.add(node.module)

        self.assertFalse(any(name.startswith("paperworks.planning") for name in imported_modules))
        self.assertFalse(any("openai" in name.lower() or "anthropic" in name.lower() for name in imported_modules))

    def test_report_contains_no_raw_sequences(self) -> None:
        report = run_task011_template_feasibility().to_dict()
        rendered = str(report)

        self.assertNotIn("normal.csv", rendered)
        self.assertNotIn("attack.csv", rendered)
        self.assertNotIn("merged.csv", rendered)
        self.assertNotIn("[10, 10, 10", rendered)


if __name__ == "__main__":
    unittest.main()
