from __future__ import annotations

import unittest

from paperworks.v6.task039e0_rule_construction_prep_v1 import (
    canonical_proposal_hash_v1,
)
from paperworks.v6.task039e2_execution_freeze_prep_v1 import (
    TASK039E2PreparationError,
    accept_provider_structured_output_v1,
    structured_output_schema_hash_v1,
    validate_closed_structured_proposal_v1,
)
from tests.task039e2_support import (
    synthetic_provider_proposal,
    synthetic_t0_proposal,
    synthetic_view,
)


class StructuredOutputAndT0Tests(unittest.TestCase):
    def test_t0_uses_exact_candidate_dsl_and_reference_only_numbers(self) -> None:
        proposal = synthetic_t0_proposal()
        self.assertEqual(
            proposal["dsl_family"], "canonical_delayed_response_rule_v1_candidate"
        )
        self.assertEqual(proposal["construction_arm"], "T0")
        self.assertEqual(proposal["numeric_literals"], [])
        self.assertFalse(proposal["canonical_rule_materialized"])
        self.assertFalse(proposal["runtime_authority_granted"])

    def test_valid_provider_structured_proposal_is_closed(self) -> None:
        proposal = synthetic_provider_proposal()
        accepted = accept_provider_structured_output_v1(
            proposal, view=synthetic_view()
        )
        self.assertEqual(accepted, proposal)

    def test_arbitrary_numeric_literal_is_rejected(self) -> None:
        proposal = synthetic_provider_proposal()
        proposal["numeric_literals"] = [999.0]
        proposal["proposal_hash"] = canonical_proposal_hash_v1(proposal)
        with self.assertRaisesRegex(TASK039E2PreparationError, "numeric literal"):
            validate_closed_structured_proposal_v1(proposal, view=synthetic_view())

    def test_unsupported_variable_and_free_text_runtime_logic_are_rejected(self) -> None:
        cases = (
            ("variables", ["SYNTHETIC_SOURCE_01", "SYNTHETIC_UNSUPPORTED"], "variable"),
            ("free_text_runtime_logic", "execute arbitrary code", "free-form"),
        )
        for field, value, message in cases:
            with self.subTest(field=field):
                proposal = synthetic_provider_proposal()
                proposal[field] = value
                proposal["proposal_hash"] = canonical_proposal_hash_v1(proposal)
                with self.assertRaisesRegex(TASK039E2PreparationError, message):
                    validate_closed_structured_proposal_v1(
                        proposal, view=synthetic_view()
                    )

    def test_unknown_field_and_provider_controller_action_are_rejected(self) -> None:
        proposal = synthetic_provider_proposal()
        proposal["unsupported_field"] = "value"
        with self.assertRaisesRegex(TASK039E2PreparationError, "closure"):
            validate_closed_structured_proposal_v1(proposal, view=synthetic_view())
        proposal = synthetic_provider_proposal()
        proposal["controller_action"] = "retrieve"
        with self.assertRaisesRegex(TASK039E2PreparationError, "provider cannot"):
            accept_provider_structured_output_v1(proposal, view=synthetic_view())
        for action_field in ("revise", "retrieve", "no_rule"):
            with self.subTest(action_field=action_field):
                proposal = synthetic_provider_proposal()
                proposal[action_field] = True
                with self.assertRaisesRegex(
                    TASK039E2PreparationError, "provider cannot"
                ):
                    accept_provider_structured_output_v1(
                        proposal, view=synthetic_view()
                    )

    def test_prose_only_provider_answer_is_rejected(self) -> None:
        with self.assertRaisesRegex(TASK039E2PreparationError, "closure"):
            accept_provider_structured_output_v1(
                {"prose": "a rule-shaped answer"}, view=synthetic_view()
            )

    def test_provider_cannot_emit_t0_or_preclaim_runtime_authority(self) -> None:
        with self.assertRaisesRegex(TASK039E2PreparationError, "cannot emit the T0"):
            accept_provider_structured_output_v1(
                synthetic_t0_proposal(), view=synthetic_view()
            )
        proposal = synthetic_provider_proposal()
        proposal["runtime_authority_granted"] = True
        proposal["proposal_hash"] = canonical_proposal_hash_v1(proposal)
        with self.assertRaisesRegex(TASK039E2PreparationError, "runtime_authority"):
            validate_closed_structured_proposal_v1(proposal, view=synthetic_view())

    def test_schema_hash_requires_closed_schema(self) -> None:
        closed = {"type": "object", "additionalProperties": False, "properties": {}}
        self.assertEqual(len(structured_output_schema_hash_v1(closed)), 64)
        with self.assertRaisesRegex(TASK039E2PreparationError, "closed"):
            structured_output_schema_hash_v1(
                {"type": "object", "additionalProperties": True}
            )


if __name__ == "__main__":
    unittest.main()
