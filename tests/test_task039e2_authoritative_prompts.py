from __future__ import annotations

import unittest
from pathlib import Path
from hashlib import sha256

from paperworks.v6.task039e2_execution_configuration_v1 import (
    CALIBRATED_NUMERIC_ROLES,
    MAIN_PROVIDER_SCHEMA_V1,
    TASK039E2ConfigurationError,
    WINDOW_NUMERIC_ROLES,
    assert_generic_main_schema_v1,
    build_task039e2_artifacts_v1,
    generate_synthetic_t0_core_v1,
    initial_model_visible_content_hash_v1,
    render_direct_number_model_content_v1,
    render_main_initial_model_content_v1,
    render_t2_followup_model_content_v1,
    validate_retrieval_request_v1,
)


ROOT = Path(__file__).resolve().parents[1]


def digest(label: str) -> str:
    from hashlib import sha256

    return sha256(label.encode()).hexdigest()


def synthetic_view() -> dict:
    roles = (*CALIBRATED_NUMERIC_ROLES, *WINDOW_NUMERIC_ROLES)
    return {
        "relation_identity": "SYNTHETIC_RELATION_001",
        "source": "SYNTHETIC_SOURCE_01",
        "source_step_direction": "step_up",
        "target": "SYNTHETIC_TARGET_01",
        "target_response_direction": "increase",
        "selected_delay_horizon_seconds": 5,
        "numeric_bindings": [
            {"numeric_role": role, "numeric_value": index + 0.5, "numeric_reference": digest(role)}
            for index, role in enumerate(roles)
        ],
        "numeric_references": {role: digest(role) for role in roles},
        "semantic_process_metadata": {"process": "P1", "relation_family": "continuous_step_delayed_response_v1"},
    }


class AuthoritativePromptTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.artifacts = build_task039e2_artifacts_v1(ROOT)

    def test_initial_model_visible_content_is_identical_across_five_requests(self) -> None:
        view = synthetic_view()
        contents = [render_main_initial_model_content_v1(view) for _ in range(5)]
        hashes = [initial_model_visible_content_hash_v1(view) for _ in range(5)]
        self.assertEqual(1, len(set(contents)))
        self.assertEqual(1, len(set(hashes)))

    def test_committed_prompt_bytes_match_frozen_hashes(self) -> None:
        bundle = self.artifacts["prompt_template_bundle"].to_dict()
        mappings = (
            ("main_initial_template_path", "main_initial_prompt_hash"),
            ("t2_followup_template_path", "t2_followup_prompt_hash"),
            ("direct_number_template_path", "direct_number_prompt_hash"),
        )
        for path_field, hash_field in mappings:
            with self.subTest(path=path_field):
                raw = (ROOT / bundle[path_field]).read_bytes()
                self.assertEqual(bundle[hash_field], sha256(raw).hexdigest())

    def test_arm_and_call_provenance_are_rejected_from_model_input(self) -> None:
        for key in ("construction_arm", "call_index", "META", "utility_result"):
            with self.subTest(key=key):
                view = synthetic_view()
                view[key] = "prohibited"
                with self.assertRaisesRegex(TASK039E2ConfigurationError, "prohibited"):
                    render_main_initial_model_content_v1(view)

    def test_generic_strict_schema_contains_no_relation_answer_const(self) -> None:
        assert_generic_main_schema_v1(MAIN_PROVIDER_SCHEMA_V1)
        self.assertFalse(MAIN_PROVIDER_SCHEMA_V1["additionalProperties"])
        text = str(MAIN_PROVIDER_SCHEMA_V1)
        self.assertNotIn("SYNTHETIC_SOURCE", text)
        self.assertNotIn("P1_", text)

    def test_direct_number_withholds_exact_three_values_and_references(self) -> None:
        rendered = render_direct_number_model_content_v1(synthetic_view())
        scientific_view = rendered.split("DIRECT_NUMBER_INPUT_JSON\n", 1)[1]
        for role in CALIBRATED_NUMERIC_ROLES:
            self.assertNotIn(role, scientific_view)
            self.assertNotIn(digest(role), scientific_view)
        for role in WINDOW_NUMERIC_ROLES:
            self.assertIn(role, scientific_view)
        policy = self.artifacts["direct_number_role_policy"].to_dict()
        self.assertEqual(list(CALIBRATED_NUMERIC_ROLES), policy["numeric_roles"])
        self.assertEqual(1, policy["calls_per_relation"])
        self.assertFalse(policy["retrieval_allowed"])

    def test_retrieval_re_presents_only_existing_corpus_once(self) -> None:
        initial = (digest("a"), digest("b"), digest("c"))
        self.assertEqual(
            (initial[1],),
            validate_retrieval_request_v1(
                initial_evidence_identities=initial,
                requested_evidence_identities=(initial[1],),
                retrieval_actions_already_used=0,
            ),
        )
        with self.assertRaisesRegex(TASK039E2ConfigurationError, "new evidence"):
            validate_retrieval_request_v1(
                initial_evidence_identities=initial,
                requested_evidence_identities=(digest("new"),),
                retrieval_actions_already_used=0,
            )
        with self.assertRaisesRegex(TASK039E2ConfigurationError, "one retrieval"):
            validate_retrieval_request_v1(
                initial_evidence_identities=initial,
                requested_evidence_identities=(initial[0],),
                retrieval_actions_already_used=1,
            )

    def test_t2_followup_is_bounded_and_contains_no_hidden_feedback(self) -> None:
        view = synthetic_view()
        rendered = render_t2_followup_model_content_v1(
            original_view=view,
            verifier_issue_codes=("numeric_reference_mismatch",),
            affected_fields=("source_threshold_reference",),
            previous_proposal_hash=digest("proposal"),
            retrieved_evidence={"evidence_identities": [digest("source-threshold")]},
        )
        self.assertIn("numeric_reference_mismatch", rendered)
        self.assertNotIn("chain_of_thought", rendered)
        self.assertNotIn("candidate_method", rendered)

    def test_t0_template_is_synthetic_only_and_uses_same_core(self) -> None:
        view = synthetic_view()
        core = generate_synthetic_t0_core_v1(view)
        self.assertEqual("canonical_delayed_response_rule_v1_candidate", core.dsl_family)
        self.assertEqual("missing_expected_delayed_response", core.runtime_logic_family)
        self.assertEqual([view["source"], view["target"]], core.to_dict()["variables"])
        real = dict(view)
        real["relation_identity"] = "directional_relation:real"
        with self.assertRaisesRegex(TASK039E2ConfigurationError, "real T0"):
            generate_synthetic_t0_core_v1(real)


if __name__ == "__main__":
    unittest.main()
