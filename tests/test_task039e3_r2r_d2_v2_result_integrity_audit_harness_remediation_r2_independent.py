from __future__ import annotations

import ast
import importlib.util
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/audit_task039e3_r2r_d2_v2_result_integrity_harness_remediation_r2.py"
SPEC = importlib.util.spec_from_file_location("d2_v2_r2_independent", SCRIPT)
assert SPEC and SPEC.loader
subject = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = subject
SPEC.loader.exec_module(subject)


class IndependentD2V2R2HarnessAuditTests(unittest.TestCase):
    def test_no_authoritative_controller_or_scientific_helper_import(self) -> None:
        tree = ast.parse(SCRIPT.read_text(encoding="utf-8"))
        forbidden = (
            "task039e3_r2r_d2_v2_inner_execution_v1",
            "execute_authorized_d2_v2_inner_v1",
            "build_evidence_tokens_v1",
            "fuse_native_horizon_timeline_v1",
        )
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                rendered = ast.unparse(node)
                self.assertFalse(any(name in rendered for name in forbidden), rendered)

    def test_exactly_one_guard_rejects_alternate_helper_reentry(self) -> None:
        guard = subject.AuditSingleParseGuardR2.create()
        guard.claim_semantic_parse("D0_DETECTOR_PREDICTION")
        alternate_helper = lambda: guard.claim_semantic_parse("D0_DETECTOR_PREDICTION")
        with self.assertRaisesRegex(subject.AuditR2Error, "D2_V2_R2_AUDIT_DUPLICATE_REAL_INPUT_PARSE"):
            alternate_helper()

    def test_lazy_reopen_is_rejected_before_deserialization(self) -> None:
        guard = subject.AuditSingleParseGuardR2.create()
        class SyntheticReopen:
            reads = 0
            def read_bytes(self) -> bytes:
                self.reads += 1
                return json.dumps({"x": 1}).encode() if self.reads == 1 else b"not json"
        path = SyntheticReopen()
        self.assertEqual(subject.semantic_json_once(path, "SYNTHETIC", guard), {"x": 1})
        with self.assertRaisesRegex(subject.AuditR2Error, "D2_V2_R2_AUDIT_DUPLICATE_REAL_INPUT_PARSE"):
            subject.semantic_json_once(path, "SYNTHETIC", guard)
        self.assertEqual(path.reads, 1)

    def test_hidden_deserialization_is_not_hash_only(self) -> None:
        source = ast.parse(SCRIPT.read_text(encoding="utf-8"))
        function = next(node for node in source.body if isinstance(node, ast.FunctionDef) and node.name == "hash_only_bytes")
        rendered = ast.unparse(function)
        self.assertNotIn("json.loads", rendered)
        self.assertNotIn("csv.reader", rendered)

    def test_reports_are_pure_snapshot_consumers(self) -> None:
        source = ast.parse(SCRIPT.read_text(encoding="utf-8"))
        function = next(node for node in source.body if isinstance(node, ast.FunctionDef) and node.name == "build_reports")
        forbidden = ("semantic_json_once", "semantic_label_once", "build_prelabel_snapshot",
                     "metric_phase", "token_oracle", "fusion_oracle", "open")
        calls = {ast.unparse(node.func) for node in ast.walk(function) if isinstance(node, ast.Call)}
        self.assertFalse(any(any(name in call for name in forbidden) for call in calls), calls)

    def test_report_builders_cannot_reparse_public_authorization(self) -> None:
        source = ast.parse(SCRIPT.read_text(encoding="utf-8"))
        function = next(node for node in source.body if isinstance(node, ast.FunctionDef) and node.name == "build_reports")
        rendered = ast.unparse(function)
        self.assertNotIn("validate_public_authorities", rendered)
        self.assertNotIn("semantic_authorization_once", rendered)
        self.assertNotIn("AUTH_PATH", rendered)

    def test_old_redundant_field_requirement_is_absent(self) -> None:
        source = SCRIPT.read_text(encoding="utf-8")
        faulty = 'authorization.get("authorization_hash")'
        self.assertNotIn(faulty, source)
        self.assertIn('"authorization_hash" in document', source)

    def test_real_run_is_not_called_by_tests(self) -> None:
        for path in (
            ROOT / "tests/test_task039e3_r2r_d2_v2_result_integrity_audit_harness_remediation_r2.py",
            Path(__file__),
        ):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    self.assertNotIn("run_audit", ast.unparse(node.func))

    def test_real_scientific_paths_are_not_opened_by_tests(self) -> None:
        for path in (
            ROOT / "tests/test_task039e3_r2r_d2_v2_result_integrity_audit_harness_remediation_r2.py",
            Path(__file__),
        ):
            source = path.read_text(encoding="utf-8")
            for real_path in (subject.oracle.D0_PATH, subject.oracle.D1_PATH, subject.oracle.SOURCE_PATH,
                              subject.oracle.HORIZON_PATH, subject.oracle.COMBINED_PATH):
                self.assertNotIn(real_path, source)

    def test_metric_evidence_parse_occurs_after_metric_oracle(self) -> None:
        source = SCRIPT.read_text(encoding="utf-8")
        self.assertLess(source.index("metric, d0_episodes, v2_episodes, recovery_episodes = metric_phase"),
                        source.index('semantic_json_once(metric_path, "PRIVATE_METRIC_EVIDENCE_V2"'))

    def test_ordering_gate_occurs_before_label_semantic_parse(self) -> None:
        source = SCRIPT.read_text(encoding="utf-8")
        self.assertLess(source.index("ordering = validate_ordering()"),
                        source.index("extend_snapshot_after_ordering(snapshot, label_path"))

    def test_historical_blocker_is_never_a_write_target(self) -> None:
        tree = ast.parse(SCRIPT.read_text(encoding="utf-8"))
        writes = [ast.unparse(node) for node in ast.walk(tree) if isinstance(node, ast.Call)
                  and isinstance(node.func, ast.Attribute) and node.func.attr in {"write_text", "write_bytes"}]
        self.assertTrue(all("HIST" not in write for write in writes))

    def test_adversarial_attacks_all_rejected(self) -> None:
        attacks, accepted = subject.adversarial()
        self.assertGreaterEqual(attacks, 20)
        self.assertEqual(accepted, 0)

    def test_report_schema_closure(self) -> None:
        self.assertEqual(len(subject.REPORT_NAMES), 17)
        self.assertEqual(len(subject.LEAVES), 14)
        self.assertEqual(set(subject.REPORT_NAMES[-3:]), {"READINESS", "BUNDLE", "RECEIPT"})

    def test_fixed_duplicate_error_is_path_free(self) -> None:
        guard = subject.AuditSingleParseGuardR2.create()
        guard.claim_semantic_parse("X")
        try:
            guard.claim_semantic_parse("X")
        except subject.AuditR2Error as error:
            self.assertEqual(str(error), "D2_V2_R2_AUDIT_DUPLICATE_REAL_INPUT_PARSE")
            self.assertNotIn("\\", str(error))
            self.assertNotIn(":/", str(error))
        else:
            self.fail("duplicate parse accepted")

    def test_no_subprocess_real_replay(self) -> None:
        source = SCRIPT.read_text(encoding="utf-8")
        self.assertNotIn("sys.executable", source)
        self.assertNotIn("python.exe", source.lower())

    def test_no_feature_test2_or_outer_execution(self) -> None:
        source = SCRIPT.read_text(encoding="utf-8")
        self.assertNotIn("hai-test1.csv", source)
        self.assertNotIn("label-test2.csv", source)
        self.assertNotIn("execute_outer", source)


if __name__ == "__main__":
    unittest.main()

