from __future__ import annotations

import ast
import json
import unittest
from pathlib import Path

from paperworks.v6.outcomes_v1 import ConstructionArmV1
from paperworks.v6.task039e0_rule_construction_prep_v1 import (
    AGENT_EXECUTION_AUTHORIZED,
    AGENT_RUN,
    D2_RESULT_CONSUMED,
    DETECTOR_RUNTIME_AUTHORIZED,
    HAI_ACCESSED,
    LLM_CALLED,
    REAL_CONFIRMED_RELATION_IDENTITY_CONSUMED,
    RULE_V2_CREATED,
    RULE_V2_EXECUTION_AUTHORIZED,
    CallAcceptedStateV1,
    FutureGenerationCallRecordV1,
)
from paperworks.v6.task039e0_validity_v1 import (
    ValidityIssueCodeV1,
    verify_prepared_rule_proposal_v1,
)
from tests.task039e0_support import (
    synthetic_digest,
    synthetic_proposal,
)


ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = {
    "confirmed_relation": (
        "schemas/v6/task039e0_confirmed_relation_primitive_v1_schema.json"
    ),
    "budget": (
        "schemas/v6/task039e0_fair_generation_budget_policy_v1_schema.json"
    ),
    "proposal": (
        "schemas/v6/task039e0_rule_proposal_envelope_v1_schema.json"
    ),
    "validity": (
        "schemas/v6/task039e0_prepared_validity_result_v1_schema.json"
    ),
    "call_record": (
        "schemas/v6/task039e0_future_generation_call_record_v1_schema.json"
    ),
}
IMPLEMENTATION_MODULES = (
    "src/paperworks/v6/task039e0_rule_construction_prep_v1.py",
    "src/paperworks/v6/task039e0_validity_v1.py",
)
CANONICAL_ADAPTERS = (
    "src/paperworks/contracts/task039e0_rule_construction_prep_v1.py",
    "src/paperworks/contracts/task039e0_validity_v1.py",
)


def _schema(name: str) -> dict[str, object]:
    return json.loads((ROOT / SCHEMAS[name]).read_text(encoding="utf-8"))


def _call_record() -> FutureGenerationCallRecordV1:
    return FutureGenerationCallRecordV1(
        construction_arm=ConstructionArmV1.T1_B,
        model_identifier="SYNTHETIC_MODEL_NOT_CALLED",
        provider_identifier="SYNTHETIC_PROVIDER_NOT_CALLED",
        prompt_template_version="SYNTHETIC_PROMPT_V1",
        temperature=0.0,
        decoding_settings={"synthetic_fixture": True},
        seed=7,
        seed_exposed=True,
        call_number=1,
        evidence_bundle_hash=synthetic_digest("fake-call-evidence"),
        verifier_feedback_hash=None,
        proposal_hash=synthetic_digest("fake-call-proposal"),
        accepted_state=CallAcceptedStateV1.CANDIDATE_PROPOSED,
        total_calls_consumed=1,
        independent_generation=True,
    )


class SchemaDraftTests(unittest.TestCase):
    def test_all_task_schemas_are_closed_draft_2020_12_json(self) -> None:
        for relative in SCHEMAS.values():
            schema = json.loads((ROOT / relative).read_text(encoding="utf-8"))
            self.assertEqual(
                schema["$schema"],
                "https://json-schema.org/draft/2020-12/schema",
            )
            self.assertEqual(schema["type"], "object")
            self.assertIs(schema["additionalProperties"], False)
            self.assertEqual(
                set(schema["required"]), set(schema["properties"])
            )

    def test_schema_keys_match_synthetic_contract_serialization(self) -> None:
        proposal, relation, evidence, budget, provenance = synthetic_proposal()
        result = verify_prepared_rule_proposal_v1(
            proposal,
            relation=relation,
            numeric_evidence=evidence,
            provenance=provenance,
            budget=budget,
            allowed_variables=frozenset({relation.source, relation.target}),
        )
        payloads = {
            "confirmed_relation": relation.to_dict(),
            "budget": budget.to_dict(),
            "proposal": proposal,
            "validity": result.to_dict(),
            "call_record": _call_record().to_dict(),
        }
        for name, payload in payloads.items():
            self.assertEqual(set(payload), set(_schema(name)["properties"]))

    def test_budget_and_proposal_schemas_freeze_fairness_and_authority(self) -> None:
        budget = _schema("budget")
        properties = budget["properties"]
        self.assertEqual(properties["t0_total_generation_calls"]["const"], 0)
        self.assertEqual(properties["t1_total_generation_calls"]["const"], 1)
        self.assertIn("equal", budget["description"].lower())
        self.assertIs(properties["result_dependent_extra_calls"]["const"], False)

        proposal = _schema("proposal")["properties"]
        self.assertEqual(proposal["numeric_origin"]["const"], "deterministic_calibrated_evidence")
        self.assertEqual(proposal["numeric_literals"]["maxItems"], 0)
        self.assertEqual(proposal["free_text_runtime_logic"]["type"], "null")
        for field in (
            "canonical_rule_materialized",
            "validity_authority_granted",
            "runtime_authority_granted",
        ):
            self.assertIs(proposal[field]["const"], False)

    def test_validity_schema_uses_exact_bounded_issue_vocabulary(self) -> None:
        issue_codes = _schema("validity")["$defs"]["issue"]["properties"]["code"]["enum"]
        self.assertEqual(
            set(issue_codes), {item.value for item in ValidityIssueCodeV1}
        )
        properties = _schema("validity")["properties"]
        self.assertIs(properties["project_owned_deterministic_code"]["const"], True)
        for field in (
            "label_input_used",
            "utility_input_used",
            "llm_chain_of_thought_used",
            "canonical_rule_materialized",
            "validity_authority_granted",
            "runtime_authority_granted",
        ):
            self.assertIs(properties[field]["const"], False)

    def test_future_call_schema_records_reproducibility_without_private_content(self) -> None:
        properties = _schema("call_record")["properties"]
        for field in (
            "model_identifier",
            "provider_identifier",
            "prompt_template_version",
            "temperature",
            "decoding_settings",
            "seed",
            "call_number",
            "evidence_bundle_hash",
            "verifier_feedback_hash",
            "proposal_hash",
            "accepted_state",
            "total_calls_consumed",
        ):
            self.assertIn(field, properties)
        for field in (
            "transport_retries_scientific_generation",
            "raw_prompt_stored",
            "chain_of_thought_stored",
            "raw_evidence_rows_stored",
            "runtime_authority_granted",
        ):
            self.assertIs(properties[field]["const"], False)

    def test_preparation_drafts_remain_unregistered_after_authoritative_e0(self) -> None:
        registry_sources = (
            ROOT / "src/paperworks/v6/schema_registry_v1.py",
            ROOT / "configs/contracts/task032a_schema_registry.json",
        )
        prep_draft_types = (
            "confirmed_relation_primitive_v1",
            "fair_generation_budget_policy_v1",
            "future_generation_call_record_v1",
            "task039e0_prepared_validity_result_v1",
            "task039e0_rule_proposal_envelope_v1",
        )
        for path in registry_sources:
            text = path.read_text(encoding="utf-8")
            for artifact_type in prep_draft_types:
                self.assertNotIn(f'"{artifact_type}"', text)


class HardBoundaryTests(unittest.TestCase):
    def test_all_preparation_authority_and_execution_flags_remain_false(self) -> None:
        self.assertEqual(
            (
                D2_RESULT_CONSUMED,
                REAL_CONFIRMED_RELATION_IDENTITY_CONSUMED,
                HAI_ACCESSED,
                LLM_CALLED,
                AGENT_RUN,
                RULE_V2_CREATED,
                RULE_V2_EXECUTION_AUTHORIZED,
                AGENT_EXECUTION_AUTHORIZED,
                DETECTOR_RUNTIME_AUTHORIZED,
            ),
            (False,) * 9,
        )

    def test_implementation_has_no_io_provider_agent_or_dynamic_execution_import(self) -> None:
        observed: set[str] = set()
        calls: set[str] = set()
        for relative in IMPLEMENTATION_MODULES:
            tree = ast.parse(
                (ROOT / relative).read_text(encoding="utf-8"),
                filename=relative,
            )
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    observed.update(alias.name for alias in node.names)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    observed.add(node.module)
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
        )
        self.assertFalse(
            any(
                name == prefix or name.startswith(prefix + ".")
                for name in observed
                for prefix in prohibited_imports
            )
        )
        self.assertTrue({"open", "exec", "eval", "compile", "__import__"}.isdisjoint(calls))

    def test_canonical_path_files_are_thin_nonexecuting_adapters(self) -> None:
        for relative in CANONICAL_ADAPTERS:
            tree = ast.parse(
                (ROOT / relative).read_text(encoding="utf-8"),
                filename=relative,
            )
            imports = [node for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)]
            calls = [node for node in ast.walk(tree) if isinstance(node, ast.Call)]
            self.assertTrue(imports)
            self.assertEqual(calls, [])
            self.assertTrue(
                all(
                    node.module is not None
                    and node.module.startswith("paperworks.v6.task039e0_")
                    for node in imports
                )
            )


if __name__ == "__main__":
    unittest.main()
