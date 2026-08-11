from __future__ import annotations

import ast
from dataclasses import replace
import json
from pathlib import Path
import unittest

from paperworks.v6.task039e1_evidence_materialization_prep_v1 import (
    D1_PRIVATE_LEDGER_ACCESSED,
    D2_PRIVATE_LEDGER_ACCESSED,
    E1_AUTHORIZATION_CREATED,
    HAI_ACCESSED,
    LLM_CALLED,
    NUMERIC_ROLE_ORDER,
    REAL_CONFIRMED_RELATION_IDENTITY_CONSUMED,
    REAL_D2_RESULT_CONSUMED,
    RULE_GENERATED,
    RUNTIME_AUTHORITY_GRANTED,
    ConstructionNumericRoleV1,
    TASK039E1PreparationError,
    assert_preparation_boundary_v1,
    resolve_private_numeric_reference_v1,
)
from tests.task039e1_support import (
    materialize_input,
    synthetic_materialization_input,
)


ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = {
    "source": "schemas/v6/task039e1_synthetic_d1_source_parameter_record_v1_schema.json",
    "target": "schemas/v6/task039e1_synthetic_d1_target_parameter_record_v1_schema.json",
    "d1": "schemas/v6/task039e1_synthetic_d1_directional_fit_supported_record_v1_schema.json",
    "d2": "schemas/v6/task039e1_synthetic_d2_confirmation_record_v1_schema.json",
    "windows": "schemas/v6/task039e1_preregistered_window_constant_bundle_v1_schema.json",
    "private": "schemas/v6/task039e1_private_construction_evidence_v1_schema.json",
    "public": "schemas/v6/task039e1_public_construction_evidence_manifest_entry_v1_schema.json",
    "resolved": "schemas/v6/task039e1_resolved_private_numeric_value_v1_schema.json",
}
IMPLEMENTATION = "src/paperworks/v6/task039e1_evidence_materialization_prep_v1.py"
ADAPTER = "src/paperworks/contracts/task039e1_evidence_materialization_prep_v1.py"


def _schema(name: str) -> dict[str, object]:
    return json.loads((ROOT / SCHEMAS[name]).read_text(encoding="utf-8"))


class SchemaDraftTests(unittest.TestCase):
    def test_all_eight_schemas_are_closed_draft_2020_12_json(self) -> None:
        for relative in SCHEMAS.values():
            schema = json.loads((ROOT / relative).read_text(encoding="utf-8"))
            self.assertEqual(
                schema["$schema"],
                "https://json-schema.org/draft/2020-12/schema",
            )
            self.assertEqual(schema["type"], "object")
            self.assertIs(schema["additionalProperties"], False)
            self.assertEqual(set(schema["required"]), set(schema["properties"]))

    def test_schema_keys_match_synthetic_serialization(self) -> None:
        item = synthetic_materialization_input()
        result = materialize_input(item)
        threshold = result.private_evidence.numeric_bindings[0]
        resolved = resolve_private_numeric_reference_v1(
            proposal_numeric_reference=threshold.numeric_reference,
            relation_binding_hash=item.relation.binding_hash,
            numeric_role=threshold.numeric_role,
            private_evidence_record_hash=result.private_evidence.artifact_hash,
            private_evidence=result.private_evidence,
        )
        payloads = {
            "source": item.source_parameter.to_dict(),
            "target": item.target_parameter.to_dict(),
            "d1": item.d1_fit_record.to_dict(),
            "d2": item.d2_confirmation_record.to_dict(),
            "windows": item.window_constants.to_dict(),
            "private": result.private_evidence.to_dict(),
            "public": result.public_manifest.to_dict(),
            "resolved": resolved.to_dict(),
        }
        for name, payload in payloads.items():
            self.assertEqual(set(payload), set(_schema(name)["properties"]))

    def test_private_schema_binds_every_role_and_public_schema_has_no_values(self) -> None:
        private_defs = _schema("private")["$defs"]
        self.assertEqual(
            set(private_defs["numericRole"]["enum"]), set(NUMERIC_ROLE_ORDER)
        )
        binding_properties = private_defs["numericBinding"]["properties"]
        for field in (
            "numeric_role",
            "numeric_value",
            "source_parameter_record_hash",
            "target_parameter_record_hash",
            "d1_fit_evidence_hash",
            "d2_confirmation_evidence_hash",
            "numeric_reference",
        ):
            self.assertIn(field, binding_properties)
        public_properties = _schema("public")["properties"]
        for field in (
            "numeric_value",
            "numeric_bindings",
            "source_step_threshold",
            "source_stability_tolerance",
            "target_noise_scale",
        ):
            self.assertNotIn(field, public_properties)
        self.assertIs(
            public_properties["private_numeric_values_included"]["const"],
            False,
        )
        self.assertIs(public_properties["runtime_authority_granted"]["const"], False)

    def test_preparation_schemas_are_not_registered_as_execution_contracts(self) -> None:
        from paperworks.v6.schema_registry_v1 import V6_SCHEMA_FILES

        preparation_artifact_types = {
            json.loads((ROOT / relative).read_text(encoding="utf-8"))["properties"][
                "artifact_type"
            ]["const"]
            for relative in SCHEMAS.values()
        }
        for artifact_type in preparation_artifact_types:
            self.assertNotIn(artifact_type, V6_SCHEMA_FILES)


class PreparationBoundaryTests(unittest.TestCase):
    def test_all_execution_data_and_authority_flags_remain_false(self) -> None:
        self.assertEqual(
            (
                REAL_D2_RESULT_CONSUMED,
                REAL_CONFIRMED_RELATION_IDENTITY_CONSUMED,
                D1_PRIVATE_LEDGER_ACCESSED,
                D2_PRIVATE_LEDGER_ACCESSED,
                HAI_ACCESSED,
                LLM_CALLED,
                RULE_GENERATED,
                RUNTIME_AUTHORITY_GRANTED,
                E1_AUTHORIZATION_CREATED,
            ),
            (False,) * 9,
        )

    def test_real_private_or_executable_inputs_fail_before_work(self) -> None:
        assert_preparation_boundary_v1()
        for field in (
            "real_d2_result",
            "real_confirmed_identity",
            "d1_private_ledger",
            "d2_private_ledger",
            "hai_input",
            "provider",
        ):
            with self.subTest(field=field), self.assertRaisesRegex(
                TASK039E1PreparationError, "synthetic fixtures only"
            ):
                assert_preparation_boundary_v1(**{field: object()})

    def test_non_synthetic_relation_identity_fails_closed(self) -> None:
        item = synthetic_materialization_input()
        with self.assertRaisesRegex(
            TASK039E1PreparationError, "SYNTHETIC_ prefix"
        ):
            materialize_input(
                replace(
                    item,
                    relation=replace(
                        item.relation, relation_identity="REAL_RELATION_001"
                    ),
                )
            )

    def test_parameter_origins_and_window_policy_hashes_are_immutable(self) -> None:
        item = synthetic_materialization_input()
        with self.assertRaises(ValueError):
            replace(
                item.source_parameter,
                source_threshold_origin="llm_generated",
            )
        with self.assertRaises(ValueError):
            replace(
                item.source_parameter,
                stability_tolerance_origin="llm_generated",
            )
        with self.assertRaises(ValueError):
            replace(item.target_parameter, target_scale_origin="unapproved")
        with self.assertRaises(TASK039E1PreparationError):
            materialize_input(
                replace(
                    item,
                    window_constants=replace(
                        item.window_constants,
                        d0_protocol_bundle_hash="a" * 64,
                    ),
                )
            )

    def test_runtime_authority_cannot_be_added(self) -> None:
        result = materialize_input(synthetic_materialization_input())
        with self.assertRaises(TASK039E1PreparationError):
            replace(result.private_evidence, runtime_authority_granted=True)
        with self.assertRaises(TASK039E1PreparationError):
            replace(result.public_manifest, runtime_authority_granted=True)

    def test_implementation_has_no_io_provider_agent_or_dynamic_execution(self) -> None:
        tree = ast.parse(
            (ROOT / IMPLEMENTATION).read_text(encoding="utf-8"),
            filename=IMPLEMENTATION,
        )
        imports: set[str] = set()
        calls: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module)
            elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                calls.add(node.func.id)
        prohibited_imports = (
            "openai",
            "anthropic",
            "pathlib",
            "subprocess",
            "paperworks.runtime",
            "paperworks.planning",
            "paperworks.e2e",
            "paperworks.data",
            "paperworks.profiling",
        )
        self.assertFalse(
            any(
                name == prefix or name.startswith(prefix + ".")
                for name in imports
                for prefix in prohibited_imports
            )
        )
        self.assertTrue(
            {"open", "exec", "eval", "compile", "__import__"}.isdisjoint(calls)
        )

    def test_canonical_path_file_is_a_thin_nonexecuting_adapter(self) -> None:
        tree = ast.parse((ROOT / ADAPTER).read_text(encoding="utf-8"), filename=ADAPTER)
        imports = [node for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)]
        calls = [node for node in ast.walk(tree) if isinstance(node, ast.Call)]
        self.assertTrue(imports)
        self.assertEqual(calls, [])
        self.assertTrue(
            all(
                node.module
                == "paperworks.v6.task039e1_evidence_materialization_prep_v1"
                for node in imports
            )
        )

    def test_all_fixture_identities_are_visibly_synthetic(self) -> None:
        item = synthetic_materialization_input()
        identities = (
            item.relation.relation_identity,
            item.relation.source,
            item.relation.target,
            item.source_parameter.source,
            item.target_parameter.target,
            item.d1_fit_record.source,
            item.d1_fit_record.target,
            item.d2_confirmation_record.source,
            item.d2_confirmation_record.target,
            item.window_constants.bundle_identity,
            item.disclosure_policy.policy_identity,
        )
        self.assertTrue(all(value.startswith("SYNTHETIC_") for value in identities))
        self.assertEqual(
            set(NUMERIC_ROLE_ORDER), {item.value for item in ConstructionNumericRoleV1}
        )


if __name__ == "__main__":
    unittest.main()
