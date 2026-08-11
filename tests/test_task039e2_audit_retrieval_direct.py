from dataclasses import replace
import unittest

from paperworks.v6.task039e2_audit_prep_v1 import (
    DIRECT_NUMBER_ALLOWED_SUPPLIED_ROLES,
    TASK039E2AuditPreparationError,
    audit_retrieval_sequence_v1,
)
from task039e2_audit_support import (
    make_direct_number_input,
    make_retrieval,
    synthetic_hash,
)


class Task039E2AuditRetrievalDirectTests(unittest.TestCase):
    def test_retrieval_is_one_action_and_subset_of_initial_e1_identities(self) -> None:
        retrieval = make_retrieval()
        self.assertIs(audit_retrieval_sequence_v1((retrieval,)), retrieval)
        self.assertNotEqual(
            retrieval.retrieved_identity_set_hash,
            retrieval.initial_identity_set_hash,
        )
        self.assertIsNone(audit_retrieval_sequence_v1(()))

    def test_retrieval_new_identity_and_second_action_rejected(self) -> None:
        with self.assertRaises(TASK039E2AuditPreparationError):
            make_retrieval(
                retrieved_evidence_identities=(synthetic_hash("new-evidence"),)
            )
        retrieval = make_retrieval()
        with self.assertRaises(TASK039E2AuditPreparationError):
            audit_retrieval_sequence_v1((retrieval, retrieval))
        with self.assertRaises(TASK039E2AuditPreparationError):
            replace(retrieval, retrieval_action_number=2)

    def test_prohibited_retrieval_content_rejected(self) -> None:
        for prohibited_key in (
            "raw_hai",
            "labels",
            "test_outcomes",
            "utility_results",
            "candidate_method_results",
        ):
            with self.subTest(prohibited_key=prohibited_key):
                with self.assertRaises(TASK039E2AuditPreparationError):
                    make_retrieval(
                        model_visible_retrieval_content={
                            "nested": {prohibited_key: "forbidden"}
                        }
                    )

    def test_direct_number_hides_exact_calibrated_roles_only(self) -> None:
        audit_input = make_direct_number_input()
        self.assertEqual(
            audit_input.hidden_calibrated_roles,
            (
                "source_step_threshold",
                "source_stability_tolerance",
                "target_noise_scale",
            ),
        )
        self.assertEqual(
            audit_input.supplied_nonhidden_numeric_roles,
            DIRECT_NUMBER_ALLOWED_SUPPLIED_ROLES,
        )
        self.assertEqual(len(audit_input.prompt_hash), 64)

    def test_direct_number_calibrated_value_and_reference_leaks_rejected(self) -> None:
        baseline = make_direct_number_input()
        leaked_value = baseline.calibrated_role_values[0][1]
        leaked_reference = baseline.calibrated_role_references[1][1]
        with self.assertRaises(TASK039E2AuditPreparationError):
            make_direct_number_input(
                model_visible_prompt={"proposed_hint": leaked_value}
            )
        with self.assertRaises(TASK039E2AuditPreparationError):
            make_direct_number_input(
                model_visible_prompt={"numeric_reference": leaked_reference}
            )

    def test_direct_number_wrong_hidden_or_supplied_role_sets_rejected(self) -> None:
        with self.assertRaises(TASK039E2AuditPreparationError):
            make_direct_number_input(
                hidden_calibrated_roles=("source_step_threshold",)
            )
        with self.assertRaises(TASK039E2AuditPreparationError):
            make_direct_number_input(
                supplied_nonhidden_numeric_roles=(
                    DIRECT_NUMBER_ALLOWED_SUPPLIED_ROLES[:-1]
                )
            )


if __name__ == "__main__":
    unittest.main()
