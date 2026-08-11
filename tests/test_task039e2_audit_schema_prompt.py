from dataclasses import replace
import unittest

from paperworks.v6.task039e2_audit_prep_v1 import (
    IndependentModelVisiblePromptV1,
    IndependentT1BPolicyV1,
    TASK039E2AuditPreparationError,
    audit_initial_prompt_fairness_v1,
    audit_provider_facing_schema_v1,
)
from task039e2_audit_support import (
    generic_provider_schema,
    make_configuration,
    make_initial_prompts,
    prompt_content,
)


class Task039E2AuditSchemaPromptTests(unittest.TestCase):
    def test_generic_schema_enforces_syntax_not_semantic_validity(self) -> None:
        result = audit_provider_facing_schema_v1(generic_provider_schema())
        self.assertTrue(result.syntactic_structured_output_enforced)
        self.assertTrue(result.relation_specific_answer_leakage_absent)
        self.assertTrue(result.semantic_validity_checked_separately)
        self.assertFalse(result.semantic_validity_result_used)

    def test_relation_specific_schema_answer_leakage_rejected(self) -> None:
        cases = (
            ("source", {"type": "string", "enum": ["SYNTHETIC_SOURCE_A"]}),
            ("target", {"type": "string", "const": "SYNTHETIC_TARGET_A"}),
            ("selected_delay_horizon", {"type": "integer", "const": 5}),
            ("evidence_reference", {"type": "string", "const": "a" * 64}),
            ("numeric_reference", {"type": "string", "const": "b" * 64}),
        )
        for field_name, leak in cases:
            with self.subTest(field_name=field_name):
                schema = generic_provider_schema()
                schema["properties"][field_name] = leak
                with self.assertRaises(TASK039E2AuditPreparationError):
                    audit_provider_facing_schema_v1(schema)

    def test_schema_must_be_closed(self) -> None:
        schema = generic_provider_schema()
        schema["additionalProperties"] = True
        with self.assertRaises(TASK039E2AuditPreparationError):
            audit_provider_facing_schema_v1(schema)

    def test_all_initial_scientific_prompts_are_identical(self) -> None:
        requests = make_initial_prompts()
        result = audit_initial_prompt_fairness_v1(requests)
        self.assertEqual(result.request_count, 5)
        self.assertEqual(
            len({request.scientific_content_hash for request in requests}), 1
        )
        IndependentT1BPolicyV1().audit_requests(requests[1:4])

    def test_model_visible_leaks_rejected(self) -> None:
        cases = (
            {"arm_label": "T2"},
            {"nested": {"call_index": 2}},
            {"other_arm_outcomes": ["accepted"]},
            {"candidate_method_provenance": "META"},
        )
        for leaking_content in cases:
            with self.subTest(leaking_content=leaking_content):
                with self.assertRaises(TASK039E2AuditPreparationError):
                    IndependentModelVisiblePromptV1(
                        relation_identity="SYNTHETIC_RELATION_001",
                        request_role="T1_INITIAL",
                        configuration_hash=make_configuration().artifact_hash,
                        model_visible_scientific_content=leaking_content,
                    )

    def test_prompt_drift_and_t1b_memory_are_rejected(self) -> None:
        requests = list(make_initial_prompts())
        changed = prompt_content()
        changed["allowed_horizons"] = [5, 10, 20]
        requests[-1] = replace(
            requests[-1], model_visible_scientific_content=changed
        )
        with self.assertRaises(TASK039E2AuditPreparationError):
            audit_initial_prompt_fairness_v1(requests)
        with self.assertRaises(TASK039E2AuditPreparationError):
            replace(make_initial_prompts()[1], previous_proposal_visible=True)

    def test_t1b_exact_three_lowest_admissible_and_no_fourth(self) -> None:
        policy = IndependentT1BPolicyV1()
        self.assertEqual(policy.select((False, True, True)), 2)
        self.assertIsNone(policy.select((False, False, False)))
        with self.assertRaises(TASK039E2AuditPreparationError):
            policy.audit_requests(make_initial_prompts()[1:])
        with self.assertRaises(TASK039E2AuditPreparationError):
            policy.select((False, False, False, True))


if __name__ == "__main__":
    unittest.main()
