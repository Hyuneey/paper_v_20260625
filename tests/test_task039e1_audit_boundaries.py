from __future__ import annotations

import ast
import unittest
from pathlib import Path

import paperworks.v6.task039e1_audit_prep_v1 as audit_prep
from paperworks.v6.task039e1_audit_prep_v1 import (
    FUTURE_REPLAY_DESIGN,
    TASK039E1AuditPreparationError,
    assert_audit_preparation_boundary_v1,
    attempt_future_private_ledger_replay_v1,
)


class PreparationBoundaryTests(unittest.TestCase):
    def test_all_real_access_and_authority_flags_are_false(self) -> None:
        flag_names = (
            "REAL_E1_RESULT_ACCESSED",
            "REAL_D2_RESULT_ACCESSED",
            "D1_PRIVATE_LEDGERS_ACCESSED",
            "D2_PRIVATE_LEDGERS_ACCESSED",
            "E1_PRIVATE_LEDGER_ACCESSED",
            "REAL_CONFIRMED_IDENTITIES_CONSUMED",
            "HAI_ACCESSED",
            "LLM_AVAILABLE",
            "LLM_CALLED",
            "RULE_GENERATION_AVAILABLE",
            "RULE_GENERATED",
            "RUNTIME_AUTHORITY_GRANTED",
            "E1_AUTHORIZED",
            "E2_AUTHORIZATION_CREATED",
        )
        for name in flag_names:
            with self.subTest(flag=name):
                self.assertIs(getattr(audit_prep, name), False)

    def test_real_boundary_inputs_are_rejected(self) -> None:
        arguments = (
            "real_e1_result",
            "real_d2_result",
            "d1_private_ledger",
            "d2_private_ledger",
            "e1_private_ledger",
            "real_confirmed_identity",
            "hai_input",
            "llm",
        )
        for argument in arguments:
            with self.subTest(argument=argument):
                with self.assertRaisesRegex(
                    TASK039E1AuditPreparationError, "synthetic inputs only"
                ):
                    assert_audit_preparation_boundary_v1(**{argument: object()})

    def test_future_replay_design_is_exact_and_disabled(self) -> None:
        self.assertEqual(
            FUTURE_REPLAY_DESIGN.logical_inputs,
            (
                "d1_source_ledger",
                "d1_target_ledger",
                "d1_directional_ledger",
                "d2_confirmation_ledger",
                "e1_private_construction_evidence_ledger",
            ),
        )
        self.assertEqual(FUTURE_REPLAY_DESIGN.expected_relation_count, 42)
        self.assertEqual(FUTURE_REPLAY_DESIGN.expected_numeric_binding_count, 462)
        self.assertFalse(FUTURE_REPLAY_DESIGN.real_reads_enabled)
        self.assertTrue(FUTURE_REPLAY_DESIGN.separate_authorization_required)
        self.assertFalse(FUTURE_REPLAY_DESIGN.raw_hai_allowed)
        self.assertFalse(FUTURE_REPLAY_DESIGN.runtime_authority_granted)

    def test_hai_and_private_ledger_paths_fail_before_io(self) -> None:
        common = {
            "d1_source_ledger": "SYNTHETIC_D1_SOURCE",
            "d1_target_ledger": "SYNTHETIC_D1_TARGET",
            "d1_directional_ledger": "SYNTHETIC_D1_DIRECTIONAL",
            "d2_confirmation_ledger": "SYNTHETIC_D2_CONFIRMATION",
            "e1_private_evidence_ledger": "SYNTHETIC_E1_PRIVATE",
        }
        with self.assertRaisesRegex(TASK039E1AuditPreparationError, "HAI path"):
            attempt_future_private_ledger_replay_v1(
                **{**common, "d2_confirmation_ledger": "hai-23.05/train3.csv"}
            )
        with self.assertRaisesRegex(
            TASK039E1AuditPreparationError, "absolute private"
        ):
            attempt_future_private_ledger_replay_v1(
                **{**common, "d1_source_ledger": "C:\\private\\d1.json"}
            )
        with self.assertRaisesRegex(TASK039E1AuditPreparationError, "disabled"):
            attempt_future_private_ledger_replay_v1(**common, authorization=object())

    def test_oracle_has_no_materializer_or_io_import(self) -> None:
        module_path = Path(audit_prep.__file__)
        source = module_path.read_text(encoding="utf-8")
        tree = ast.parse(source)
        imports = tuple(
            node
            for node in ast.walk(tree)
            if isinstance(node, (ast.Import, ast.ImportFrom))
        )
        imported_modules = {
            node.module.split(".")[0]
            for node in imports
            if isinstance(node, ast.ImportFrom) and node.module
        }
        imported_modules.update(
            alias.name.split(".")[0]
            for node in imports
            if isinstance(node, ast.Import)
            for alias in node.names
        )
        self.assertNotIn("materialize_construction_evidence_v1", source)
        self.assertNotIn("stable_hash_v1", source)
        self.assertTrue(
            imported_modules.isdisjoint(
                {"pathlib", "requests", "openai", "subprocess", "paperworks"}
            )
        )
        self.assertNotIn("open(", source)
        self.assertNotIn("exec(", source)
        self.assertNotIn("eval(", source)


if __name__ == "__main__":
    unittest.main()
