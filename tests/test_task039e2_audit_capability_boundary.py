import ast
from pathlib import Path
import unittest

from paperworks.v6.task039e2_audit_prep_v1 import (
    API_KEY_ACCESSED,
    E3_AUTHORITY_GRANTED,
    EXPECTED_MODEL_SNAPSHOT,
    MODEL_CALLED,
    PROVIDER_CONTACTED,
    REAL_E1_PRIVATE_EVIDENCE_ACCESSED,
    REAL_E2_RESULT_ACCESSED,
    RUNTIME_AUTHORITY_GRANTED,
    IndependentCapabilityReceiptV1,
    IndependentE2AuditPreparationReceiptV1,
    TASK039E2AuditPreparationError,
    assert_preparation_boundary_v1,
    attempt_provider_interaction_v1,
)


class Task039E2AuditCapabilityBoundaryTests(unittest.TestCase):
    def test_provider_free_capability_receipt_makes_no_live_claims(self) -> None:
        receipt = IndependentCapabilityReceiptV1()
        self.assertEqual(receipt.exact_model_snapshot, EXPECTED_MODEL_SNAPSHOT)
        self.assertTrue(receipt.structured_output_required)
        self.assertEqual(receipt.seed_policy, "deprecated_not_relied_upon")
        self.assertFalse(receipt.provider_contacted)
        self.assertFalse(receipt.live_capability_checked)
        self.assertFalse(receipt.account_availability_checked)
        self.assertFalse(receipt.seed_determinism_claimed)
        self.assertEqual(len(receipt.to_dict()["artifact_hash"]), 64)

    def test_capability_overclaims_rejected(self) -> None:
        cases = (
            ("exact_model_snapshot", "gpt-5.4"),
            ("structured_output_required", False),
            ("seed_policy", "deterministic"),
            ("provider_contacted", True),
            ("live_capability_checked", True),
            ("account_availability_checked", True),
            ("seed_determinism_claimed", True),
        )
        for field_name, bad_value in cases:
            with self.subTest(field_name=field_name):
                with self.assertRaises(TASK039E2AuditPreparationError):
                    IndependentCapabilityReceiptV1(**{field_name: bad_value})

    def test_all_preparation_boundaries_remain_false(self) -> None:
        self.assertFalse(REAL_E2_RESULT_ACCESSED)
        self.assertFalse(REAL_E1_PRIVATE_EVIDENCE_ACCESSED)
        self.assertFalse(PROVIDER_CONTACTED)
        self.assertFalse(MODEL_CALLED)
        self.assertFalse(API_KEY_ACCESSED)
        self.assertFalse(RUNTIME_AUTHORITY_GRANTED)
        self.assertFalse(E3_AUTHORITY_GRANTED)
        receipt = IndependentE2AuditPreparationReceiptV1()
        self.assertFalse(receipt.real_t0_generated)
        self.assertFalse(receipt.rule_generated)
        self.assertFalse(receipt.e3_authority)
        assert_preparation_boundary_v1()

    def test_boundary_preclaims_fail_closed(self) -> None:
        for boundary in (
            "real_e2_result_accessed",
            "real_e1_private_evidence_accessed",
            "provider_contacted",
            "model_called",
            "api_key_accessed",
        ):
            with self.subTest(boundary=boundary):
                with self.assertRaises(TASK039E2AuditPreparationError):
                    assert_preparation_boundary_v1(**{boundary: True})

    def test_provider_interaction_is_impossible_before_client_or_key_use(self) -> None:
        sentinel = object()
        with self.assertRaises(TASK039E2AuditPreparationError):
            attempt_provider_interaction_v1(client=sentinel, credential=sentinel)

    def test_oracle_imports_standard_library_only_and_no_e2_freezer(self) -> None:
        module_path = (
            Path(__file__).parents[1]
            / "src"
            / "paperworks"
            / "v6"
            / "task039e2_audit_prep_v1.py"
        )
        source_text = module_path.read_text(encoding="utf-8")
        tree = ast.parse(source_text)
        imported_roots: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_roots.update(
                    alias.name.split(".")[0] for alias in node.names
                )
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported_roots.add(node.module.split(".")[0])
        self.assertLessEqual(
            imported_roots,
            {
                "__future__",
                "dataclasses",
                "hashlib",
                "json",
                "math",
                "re",
                "types",
                "typing",
            },
        )
        self.assertNotIn("task039e2_execution", source_text.lower())
        self.assertNotIn("requests", imported_roots)
        self.assertNotIn("openai", imported_roots)


if __name__ == "__main__":
    unittest.main()
