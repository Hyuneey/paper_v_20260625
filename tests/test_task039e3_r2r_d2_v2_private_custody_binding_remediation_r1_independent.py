from __future__ import annotations

from dataclasses import replace
import ast
import unittest

from scripts import remediate_task039e3_r2r_d2_v2_private_custody_binding_r1 as subject


class IndependentCustodyBindingRemediationR1Tests(unittest.TestCase):
    def test_source_has_no_scientific_controller_import(self) -> None:
        path = subject.ROOT / "scripts/remediate_task039e3_r2r_d2_v2_private_custody_binding_r1.py"
        tree = ast.parse(path.read_text(encoding="utf-8"))
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                imports.append(node.module or "")
        self.assertFalse(any("task039e3_r2r_d2_v2_inner_execution_v1" in value for value in imports))

    def test_exact_hash_wrong_role_rejected(self) -> None:
        with self.assertRaises(subject.CustodyRemediationError):
            subject.validate_compatibility_candidate(replace(subject.CompatibilityCandidateR1(), stable_logical_bindings_exact=False))

    def test_forged_filename_size_or_path_cannot_replace_hash(self) -> None:
        for mutation in ({"artifact_hashes_exact": False}, {"stable_scientific_bindings_exact": False}):
            with self.subTest(mutation=mutation), self.assertRaises(subject.CustodyRemediationError):
                subject.validate_compatibility_candidate(replace(subject.CompatibilityCandidateR1(), **mutation))

    def test_alternate_spelling_allowed_only_as_environment_locator(self) -> None:
        self.assertEqual(subject.validate_compatibility_candidate(subject.CompatibilityCandidateR1(environment_local_differences_only=True)),
                         "D2_V2_PRIVATE_CUSTODY_BINDING_COMPATIBILITY_PASS")
        with self.assertRaises(subject.CustodyRemediationError):
            subject.validate_compatibility_candidate(subject.CompatibilityCandidateR1(environment_local_differences_only=False))

    def test_redaction_bypasses_rejected(self) -> None:
        for mutation in ({"private_path_exposed": True}, {"stable_security_properties_pass": False}):
            with self.subTest(mutation=mutation), self.assertRaises(subject.CustodyRemediationError):
                subject.validate_compatibility_candidate(replace(subject.CompatibilityCandidateR1(), **mutation))

    def test_all_copy_move_repersist_workarounds_rejected(self) -> None:
        for operation in ("COPY_PRIVATE", "MOVE_PRIVATE", "REWRITE_PRIVATE", "REPERSIST_PRIVATE"):
            with self.subTest(operation=operation), self.assertRaises(subject.CustodyRemediationError):
                subject.validate_operation_request((operation,))

    def test_label_test1_test2_are_never_allowed(self) -> None:
        for operation in ("PARSE_LABEL", "READ_TEST1_FEATURE", "READ_TEST2"):
            with self.subTest(operation=operation), self.assertRaises(subject.CustodyRemediationError):
                subject.validate_operation_request((operation,))

    def test_r4_disposition_is_exactly_explained(self) -> None:
        self.assertEqual(subject.ROOT_CAUSE_DISPOSITION, "OTHER_EXACTLY_EXPLAINED")
        self.assertEqual(subject.R4_FAILED_BINDING_CLASS, "ENVIRONMENT_LOCAL_LOCATOR_ACCESS_PERMISSION")

    def test_no_unknown_fields(self) -> None:
        self.assertEqual(subject.classification_counts()["UNKNOWN_FAIL_CLOSED"], 0)

    def test_receipt_authorizes_only_r5_audit(self) -> None:
        self.assertEqual(subject.NEXT_TASK, "TASK-039E3-R2R-UTILITY-INNER-D2-V2-RESULT-INTEGRITY-AUDIT-HARNESS-REMEDIATION-R5")


if __name__ == "__main__":
    unittest.main()
