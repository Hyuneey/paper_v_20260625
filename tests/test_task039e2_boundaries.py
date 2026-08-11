from __future__ import annotations

import ast
import unittest
from pathlib import Path

import paperworks.v6.task039e2_execution_freeze_prep_v1 as prep
from paperworks.v6.task039e2_execution_freeze_prep_v1 import (
    TASK039E2PreparationError,
    assert_preparation_boundary_v1,
)


class PreparationBoundaryTests(unittest.TestCase):
    def test_all_real_execution_and_authority_flags_are_false(self) -> None:
        names = (
            "REAL_E1_RESULT_CONSUMED",
            "REAL_E1_PRIVATE_EVIDENCE_ACCESSED",
            "REAL_CONFIRMED_IDENTITIES_CONSUMED",
            "PROVIDER_SELECTED",
            "MODEL_SELECTED",
            "PROVIDER_CONTACTED",
            "LLM_CALLED",
            "REAL_T0_GENERATED",
            "RULE_V2_AUTHORIZED",
            "RUNTIME_AUTHORITY_GRANTED",
            "E2_AUTHORIZATION_CREATED",
        )
        for name in names:
            with self.subTest(name=name):
                self.assertIs(getattr(prep, name), False)

    def test_real_inputs_provider_and_llm_are_rejected(self) -> None:
        arguments = (
            "real_e1_result",
            "real_e1_private_evidence",
            "real_confirmed_identity",
            "real_provider_identifier",
            "real_model_identifier",
            "provider_client",
            "llm",
        )
        for argument in arguments:
            with self.subTest(argument=argument):
                with self.assertRaisesRegex(
                    TASK039E2PreparationError, "provider-neutral inputs only"
                ):
                    assert_preparation_boundary_v1(**{argument: object()})

    def test_module_has_no_provider_sdk_network_or_e1_result_io(self) -> None:
        module_path = Path(prep.__file__)
        source = module_path.read_text(encoding="utf-8")
        tree = ast.parse(source)
        imported_modules = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_modules.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported_modules.add(node.module.split(".")[0])
        self.assertTrue(
            imported_modules.isdisjoint(
                {"openai", "anthropic", "requests", "httpx", "urllib", "socket", "subprocess"}
            )
        )
        self.assertNotIn("materialize_construction_evidence_v1", source)
        self.assertNotIn("open(", source)
        self.assertNotIn("read_text", source)
        self.assertNotIn("read_bytes", source)
        self.assertNotIn("exec(", source)
        self.assertNotIn("eval(", source)


if __name__ == "__main__":
    unittest.main()
