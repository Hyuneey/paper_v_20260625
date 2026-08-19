from __future__ import annotations

from copy import deepcopy
import importlib.util
from pathlib import Path
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = (
    REPO_ROOT
    / "scripts"
    / "audit_task039e3_r2r_utility_normal_only_authority_v1_materialized.py"
)
SPEC = importlib.util.spec_from_file_location("task039e3_materialized_audit", SCRIPT_PATH)
assert SPEC is not None and SPEC.loader is not None
audit = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(audit)


class MaterializedAuthorityPublicAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.common = audit.reconstruct_common42(REPO_ROOT)
        cls.synthetic_registry = audit.build_synthetic_registry(cls.common)

    def test_independent_canonical_hash_contract(self) -> None:
        self.assertEqual(
            audit.stable_hash({"b": 2, "a": 1}),
            "43258cff783fe7036d8a43033f830adfc60ec037382473548ac742b888292777",
        )

    def test_public_common_oracle_closes_42_relations_and_420_references(self) -> None:
        self.assertEqual(len(self.common["relations"]), 42)
        self.assertEqual(len(self.common["references"]), 420)
        self.assertEqual(len(set(self.common["references"])), 420)
        self.assertEqual(len(self.common["sources"]), 9)
        self.assertEqual(len(self.common["targets"]), 10)
        self.assertEqual(len(self.common["feature_union"]), 19)
        self.assertEqual(
            self.common["authority_definition_hash"], audit.AUTHORITY_DEFINITION_HASH
        )

    def test_synthetic_registry_passes_independent_oracle(self) -> None:
        result = audit.audit_registry_document(
            self.synthetic_registry,
            self.common,
            expected_artifact_hash=None,
        )
        self.assertEqual(result["records"], 420)
        self.assertEqual(result["logical_keys"], 420)
        self.assertEqual(result["references"], 420)
        self.assertEqual(result["record_hash_matches"], 420)
        self.assertEqual(result["provenance_identity_matches"], 420)

    def test_synthetic_mutation_matrix_is_fail_closed(self) -> None:
        result = audit.run_mutation_audit(self.synthetic_registry, self.common)
        self.assertGreaterEqual(result["cases"], 16)
        self.assertEqual(result["rejected"], result["cases"])
        self.assertEqual(result["accepted"], 0)

    def test_value_independent_reference_and_role_bound_provenance(self) -> None:
        relation = self.common["relations"][0]
        step_reference = audit.reference_identity(relation, "source_step_threshold")
        target_reference = audit.reference_identity(relation, "target_noise_scale")
        self.assertNotEqual(step_reference, target_reference)
        self.assertEqual(
            step_reference,
            audit.reference_identity(deepcopy(relation), "source_step_threshold"),
        )
        self.assertNotEqual(
            audit.provenance_identity(relation, "source_step_threshold"),
            audit.provenance_identity(relation, "target_noise_scale"),
        )

    def test_exact_numeric_types_reject_bool_and_int_for_float_roles(self) -> None:
        for invalid in (True, 1, "1", None, float("inf"), float("nan")):
            with self.subTest(type=type(invalid).__name__):
                with self.assertRaises(audit.AuditError):
                    audit.audit_numeric_value("source_step_threshold", invalid)
        audit.audit_numeric_value("source_step_threshold", 1.0)
        audit.audit_numeric_value("source_stability_tolerance", 0.0)
        audit.audit_numeric_value("target_noise_scale", 1.0)

    def test_frozen_constants_require_exact_type_and_value(self) -> None:
        for role, value in audit.FROZEN_CONSTANTS.items():
            audit.audit_numeric_value(role, value)
        with self.assertRaises(audit.AuditError):
            audit.audit_numeric_value("source_pre_window_seconds", 5.0)
        with self.assertRaises(audit.AuditError):
            audit.audit_numeric_value("minimum_source_stability_fraction", True)

    def test_public_authorization_receipt_and_leakage_oracles_pass(self) -> None:
        authorization = audit.audit_authorization(REPO_ROOT)["authorization"]
        receipt = audit.audit_public_receipt(REPO_ROOT, authorization)
        self.assertEqual(receipt["private_registry_content_hash"], audit.EXPECTED_PRIVATE_REGISTRY_HASH)
        leakage = audit.audit_public_artifact_leakage(REPO_ROOT)
        self.assertEqual(leakage["files_checked"], 6)
        self.assertEqual(leakage["findings"], 0)


if __name__ == "__main__":
    unittest.main()
