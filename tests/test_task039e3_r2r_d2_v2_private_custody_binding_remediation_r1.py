from __future__ import annotations

from dataclasses import replace
import unittest

from scripts import remediate_task039e3_r2r_d2_v2_private_custody_binding_r1 as subject


class CustodyBindingRemediationR1Tests(unittest.TestCase):
    def test_exact_constants(self) -> None:
        self.assertEqual(subject.FUSION_HASH, "9fd5563b76cb4af0cf68383e1e2b9d10da9e6fd35a667d4a68d6eb5f8db2e8cb")
        self.assertEqual(subject.METRIC_HASH, "3e3f20b5b1a9387cd3bed4ad17e4232e714cc588d7df1c2a37dfd69bcd1a8513")
        self.assertEqual(subject.CUSTODY_MODULE_IDENTITY, "c0e3faafdab0cb84e2f8e62b9380c243b0faee9ab38cc014de36fed5464d62e6")

    def test_classification_closure(self) -> None:
        counts = subject.classification_counts()
        self.assertEqual(counts[subject.CLASS_STABLE_SCIENTIFIC], 9)
        self.assertEqual(counts[subject.CLASS_STABLE_SECURITY], 6)
        self.assertEqual(counts[subject.CLASS_STABLE_LOGICAL], 5)
        self.assertEqual(counts[subject.CLASS_ENVIRONMENT], 5)
        self.assertEqual(counts[subject.CLASS_EPHEMERAL], 4)
        self.assertEqual(counts["UNKNOWN_FAIL_CLOSED"], 0)

    def test_same_hash_different_environment_root_accepted(self) -> None:
        self.assertEqual(subject.validate_compatibility_candidate(subject.CompatibilityCandidateR1()),
                         "D2_V2_PRIVATE_CUSTODY_BINDING_COMPATIBILITY_PASS")

    def test_security_and_identity_mutations_rejected(self) -> None:
        mutations = (
            {"artifact_hashes_exact": False}, {"inside_git": True}, {"symlink": True},
            {"tracked_copy_count": 1}, {"logical_namespace_match": False},
            {"custody_module_match": False}, {"stable_scientific_bindings_exact": False},
            {"stable_logical_bindings_exact": False}, {"unexpected_residue_count": 1},
        )
        for mutation in mutations:
            with self.subTest(mutation=mutation), self.assertRaises(subject.CustodyRemediationError):
                subject.validate_compatibility_candidate(replace(subject.CompatibilityCandidateR1(), **mutation))

    def test_path_semantics_validator_defects_rejected(self) -> None:
        with self.assertRaises(subject.CustodyRemediationError):
            subject.validate_compatibility_candidate(replace(subject.CompatibilityCandidateR1(), validator_requires_absolute_path_equality=True))
        with self.assertRaises(subject.CustodyRemediationError):
            subject.validate_compatibility_candidate(replace(subject.CompatibilityCandidateR1(), producer_declares_path_environment_local=False, producer_declares_path_stable=True))

    def test_private_mutation_workarounds_rejected(self) -> None:
        for key in ("copied", "moved", "rewritten", "repersisted"):
            with self.subTest(key=key), self.assertRaises(subject.CustodyRemediationError):
                subject.validate_compatibility_candidate(replace(subject.CompatibilityCandidateR1(), **{key: True}))

    def test_path_exposure_rejected(self) -> None:
        with self.assertRaises(subject.CustodyRemediationError) as caught:
            subject.validate_compatibility_candidate(replace(subject.CompatibilityCandidateR1(), private_path_exposed=True))
        self.assertNotIn("\\", str(caught.exception))

    def test_forbidden_scientific_and_data_operations_rejected(self) -> None:
        forbidden = ("PARSE_D0", "PARSE_D1", "PARSE_SOURCE_MAP", "PARSE_HORIZON",
                     "PARSE_COMBINED", "PARSE_LABEL", "READ_TEST1_FEATURE", "READ_TEST2",
                     "RUN_FUSION", "COMPUTE_METRIC")
        for operation in forbidden:
            with self.subTest(operation=operation), self.assertRaises(subject.CustodyRemediationError):
                subject.validate_operation_request((operation,))

    def test_allowed_audit_operations(self) -> None:
        self.assertEqual(subject.validate_operation_request(tuple(sorted(subject.ALLOWED_OPERATIONS))),
                         "CUSTODY_REMEDIATION_OPERATION_SET_ACCEPTED")

    def test_adversarial_closure(self) -> None:
        attacks, accepted = subject.adversarial_audit()
        self.assertGreaterEqual(attacks, 20)
        self.assertEqual(accepted, 0)

    def test_report_contract_has_no_scientific_authority(self) -> None:
        source = (subject.ROOT / "scripts/remediate_task039e3_r2r_d2_v2_private_custody_binding_r1.py").read_text(encoding="utf-8")
        self.assertIn('"scientific_execution_authorized": False', source)
        self.assertIn('"merge-base", "--is-ancestor", BASE, head', source)
        self.assertIn("implementation_scope != allowed_scope", source)
        self.assertNotIn("execute_authorized_d2_v2_inner_v1(", source)
        self.assertNotIn("compute_metric_values_v1(", source)


if __name__ == "__main__":
    unittest.main()
