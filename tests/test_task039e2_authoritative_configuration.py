from __future__ import annotations

import unittest
from pathlib import Path

from paperworks.v6.task039e2_execution_configuration_v1 import (
    API_ENDPOINT,
    EXACT_MODEL,
    MAXIMUM_SCIENTIFIC_CALLS,
    PROVIDER,
    SCIENTIFIC_CONCURRENCY,
    TASK039E2ConfigurationError,
    build_chat_completions_request_body_v1,
    build_task039e2_artifacts_v1,
    classify_transport_outcome_v1,
    validate_sampling_configuration_v1,
)


ROOT = Path(__file__).resolve().parents[1]


class AuthoritativeConfigurationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.artifacts = build_task039e2_artifacts_v1(ROOT)

    def test_exact_provider_model_and_no_fallback(self) -> None:
        freeze = self.artifacts["provider_model_freeze"].to_dict()
        self.assertEqual(PROVIDER, freeze["provider"])
        self.assertEqual(API_ENDPOINT, freeze["api_endpoint"])
        self.assertEqual(EXACT_MODEL, freeze["exact_model_snapshot"])
        self.assertTrue(freeze["snapshot_locked"])
        self.assertFalse(freeze["model_alias_fallback_allowed"])
        self.assertFalse(freeze["automatic_upgrade_allowed"])
        self.assertFalse(freeze["alternative_model_fallback_allowed"])
        self.assertEqual("block_task039e3", freeze["unavailable_snapshot_outcome"])

    def test_static_capability_receipt_does_not_claim_account_availability(self) -> None:
        receipt = self.artifacts["model_capability_receipt"].to_dict()
        self.assertEqual("deprecated_beta_not_relied_upon", receipt["seed_capability"])
        self.assertEqual("not_probed", receipt["account_specific_model_availability"])
        self.assertEqual("not_probed", receipt["credential_availability"])
        self.assertFalse(receipt["provider_contacted"])
        self.assertEqual("2026-08-11", receipt["review_date"])
        self.assertEqual(3, len(receipt["source_documents"]))

    def test_sampling_configuration_is_exact_and_seedless(self) -> None:
        config = self.artifacts["execution_configuration"].to_dict()
        sampling = config["sampling_configuration"]
        validate_sampling_configuration_v1(sampling)
        self.assertEqual("none", sampling["reasoning_effort"])
        self.assertEqual(0.7, sampling["temperature"])
        self.assertEqual(1.0, sampling["top_p"])
        self.assertEqual(1024, sampling["max_completion_tokens"])
        self.assertIsNone(sampling["seed"])
        self.assertFalse(sampling["seed_used"])
        self.assertFalse(sampling["seed_determinism_claimed"])
        self.assertEqual([], sampling["tools"])
        self.assertIsNone(sampling["tool_choice"])

    def test_sampling_mutations_fail_closed(self) -> None:
        sampling = dict(self.artifacts["execution_configuration"].to_dict()["sampling_configuration"])
        for field, value in (
            ("model", "gpt-5.4"),
            ("reasoning_effort", "low"),
            ("temperature", 0.8),
            ("seed", 11),
        ):
            with self.subTest(field=field):
                changed = dict(sampling)
                changed[field] = value
                with self.assertRaisesRegex(TASK039E2ConfigurationError, "sampling"):
                    validate_sampling_configuration_v1(changed)

    def test_future_request_builder_is_stateless_strict_and_seedless(self) -> None:
        from paperworks.v6.task039e2_execution_configuration_v1 import MAIN_PROVIDER_SCHEMA_V1

        body = build_chat_completions_request_body_v1(
            model_visible_content="synthetic content",
            provider_schema=MAIN_PROVIDER_SCHEMA_V1,
            schema_name="provider_proposal_core_v1",
        )
        self.assertEqual(EXACT_MODEL, body["model"])
        self.assertEqual("none", body["reasoning_effort"])
        self.assertTrue(body["response_format"]["json_schema"]["strict"])
        self.assertNotIn("seed", body)
        self.assertNotIn("tools", body)
        self.assertNotIn("tool_choice", body)
        self.assertNotIn("previous_response_id", body)
        self.assertNotIn("authorization", str(body).lower())

    def test_schedule_freezes_relation_major_336_call_maximum(self) -> None:
        schedule = self.artifacts["execution_schedule"].to_dict()
        self.assertEqual(42, schedule["relation_count"])
        self.assertEqual(42, len(schedule["relation_identities"]))
        self.assertEqual(MAXIMUM_SCIENTIFIC_CALLS, schedule["maximum_scientific_calls"])
        self.assertEqual(SCIENTIFIC_CONCURRENCY, schedule["scientific_concurrency"])
        self.assertEqual(126, schedule["t1b_fixed_scientific_calls"])
        self.assertEqual(126, schedule["t2_maximum_scientific_calls"])
        self.assertFalse(schedule["result_dependent_ordering"])
        self.assertFalse(schedule["serialization_order_is_scientific_rank"])

    def test_transport_and_scientific_attempts_are_distinct(self) -> None:
        self.assertEqual(
            (False, True),
            classify_transport_outcome_v1("http_429", model_response_received=False),
        )
        self.assertEqual(
            (True, False),
            classify_transport_outcome_v1("provider_refusal", model_response_received=True),
        )
        policy = self.artifacts["transport_retry_policy"].to_dict()
        self.assertEqual(2, policy["maximum_transport_retries_per_request"])
        self.assertEqual(0, policy["scientific_generation_retries"])
        self.assertEqual([2, 4], policy["fixed_retry_delays_seconds"])
        self.assertIn("overrides", policy["retry_after_429_policy"])
        self.assertEqual("abort_full_scientific_run", policy["retry_exhaustion_outcome"])

    def test_all_execution_and_authority_flags_remain_false(self) -> None:
        bundle = self.artifacts["protocol_bundle"].to_dict()
        for field in (
            "provider_contacted",
            "credential_checked",
            "capability_probe_executed",
            "llm_called",
            "real_t0_generated",
            "t1_generated",
            "t1b_generated",
            "t2_generated",
            "direct_number_executed",
            "e3_authorization_created",
            "rule_v2_authorized",
            "runtime_authority",
            "e1_private_evidence_accessed",
            "hai_accessed",
        ):
            self.assertFalse(bundle[field], field)


if __name__ == "__main__":
    unittest.main()
