from __future__ import annotations

import ast
import importlib.util
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/audit_task039e3_r2r_d2_v2_result_integrity_harness_remediation_r5.py"
SPEC = importlib.util.spec_from_file_location("d2_v2_r5_independent", SCRIPT)
assert SPEC and SPEC.loader
subject = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = subject
SPEC.loader.exec_module(subject)


class R5IndependentHarnessTests(unittest.TestCase):
    def test_no_production_execution_controller_import(self) -> None:
        tree = ast.parse(SCRIPT.read_text(encoding="utf-8"))
        forbidden = ("task039e3_r2r_d2_v2_inner_execution_v1", "execute_authorized_d2_v2_inner_v1",
                     "build_evidence_tokens_v1", "fuse_native_horizon_timeline_v1")
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                rendered = ast.unparse(node)
                self.assertFalse(any(value in rendered for value in forbidden), rendered)

    def test_r5_implements_its_own_scientific_oracles(self) -> None:
        tree = ast.parse(SCRIPT.read_text(encoding="utf-8"))
        functions = {node.name for node in tree.body if isinstance(node, ast.FunctionDef)}
        self.assertTrue({"build_tokens", "fusion_oracle", "contiguous_runs", "attack_events", "metric_oracle"} <= functions)

    def test_reports_are_pure_completed_result_consumers(self) -> None:
        tree = ast.parse(SCRIPT.read_text(encoding="utf-8"))
        function = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "build_reports")
        calls = {ast.unparse(node.func) for node in ast.walk(function) if isinstance(node, ast.Call)}
        forbidden = {"semantic_json_once", "semantic_label_once", "build_tokens", "fusion_oracle",
                     "metric_oracle", "load_public", "open"}
        self.assertTrue(calls.isdisjoint(forbidden), calls)

    def test_report_generation_has_no_oracle_rerun(self) -> None:
        source = SCRIPT.read_text(encoding="utf-8")
        start = source.index("def build_reports")
        end = source.index("def strict_object")
        section = source[start:end]
        self.assertNotIn("fusion_oracle(", section)
        self.assertNotIn("metric_oracle(", section)

    def test_exact_once_real_sequence(self) -> None:
        source = SCRIPT.read_text(encoding="utf-8")
        sequence = [
            'semantic_json_once(ROOT / D0_PATH, "D0_PREDICTION"',
            'semantic_json_once(ROOT / D1_PATH, "D1_PREDICTION"',
            'semantic_json_once(ROOT / SOURCE_PATH, "SOURCE_MAP"',
            'semantic_json_once(ROOT / HORIZON_PATH, "NATIVE_HORIZON_MAP"',
            'semantic_json_once(ROOT / COMBINED_PATH, "COMBINED_PREDICTION_V2"',
            'semantic_json_once(fusion_path, "FUSION_EVIDENCE_V2"',
            "semantic_label_once(label_path, guard)",
            'semantic_json_once(metric_path, "METRIC_EVIDENCE_V2"',
        ]
        positions = [source.index(value) for value in sequence]
        self.assertEqual(positions, sorted(positions))
        self.assertTrue(all(source.count(value) == 1 for value in sequence))

    def test_ordering_precedes_label_parse(self) -> None:
        source = SCRIPT.read_text(encoding="utf-8")
        self.assertLess(source.index("ordering = validate_ordering()"), source.index("semantic_label_once(label_path, guard)"))

    def test_metric_evidence_is_after_oracle(self) -> None:
        source = SCRIPT.read_text(encoding="utf-8")
        self.assertLess(source.index("metric = metric_oracle"), source.index('semantic_json_once(metric_path, "METRIC_EVIDENCE_V2"'))

    def test_synthetic_tests_do_not_open_real_scientific_paths(self) -> None:
        for path in (ROOT / "tests/test_task039e3_r2r_d2_v2_result_integrity_audit_harness_remediation_r5.py", Path(__file__)):
            source = path.read_text(encoding="utf-8")
            for real_path in (subject.D0_PATH, subject.D1_PATH, subject.SOURCE_PATH, subject.HORIZON_PATH,
                              subject.COMBINED_PATH, subject.METRICS_PATH, subject.ACCOUNTING_PATH):
                self.assertNotIn(real_path, source)

    def test_tests_never_call_real_audit(self) -> None:
        for path in (ROOT / "tests/test_task039e3_r2r_d2_v2_result_integrity_audit_harness_remediation_r5.py", Path(__file__)):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    self.assertNotIn("run_audit", ast.unparse(node.func))

    def test_private_paths_never_rendered(self) -> None:
        source = SCRIPT.read_text(encoding="utf-8")
        main = source[source.index("def main"):]
        self.assertNotIn("private_root", main)
        self.assertNotIn("fusion_path", main)
        self.assertNotIn("metric_path", main)

    def test_report_schema_is_exact(self) -> None:
        self.assertEqual(len(subject.LEAVES), 14)
        self.assertEqual(len(subject.REPORT_NAMES), 17)
        self.assertEqual(subject.REPORT_NAMES[-3:], ("READINESS", "BUNDLE", "RECEIPT"))

    def test_role_specific_reference_hash_fields(self) -> None:
        source = SCRIPT.read_text(encoding="utf-8")
        self.assertIn("fusion_evidence_v2_sha256", source)
        self.assertIn("metric_evidence_v2_sha256", source)
        self.assertIn("combined_prediction_v2_sha256", source)

    def test_historical_blocker_count_is_five(self) -> None:
        self.assertEqual(len(subject.HISTORICAL_BLOCKERS), 5)

    def test_result_commit_is_exact(self) -> None:
        self.assertEqual(subject.RESULT_C, "55d41c543e110a9a6f0f5e2e2671857dba938aaa")

    def test_exact_next_task(self) -> None:
        self.assertEqual(subject.NEXT_TASK, "TASK-039E3-R2R-UTILITY-INNER-D2-V1-V2-SCIENTIFIC-DISPOSITION-V1")

    def test_no_push_or_outer_execution(self) -> None:
        source = SCRIPT.read_text(encoding="utf-8")
        self.assertNotIn("git push", source)
        self.assertNotIn("execute_outer", source)


if __name__ == "__main__":
    unittest.main()
