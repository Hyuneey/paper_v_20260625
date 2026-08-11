from __future__ import annotations

import unittest
from dataclasses import replace

from paperworks.v6.task039e2_execution_freeze_prep_v1 import (
    EXPECTED_MAXIMUM_SCIENTIFIC_CALLS,
    ProviderResponseCustodyReceiptV1,
    T2ControllerIntegrationPolicyV1,
    TASK039E2PreparationError,
    TransportRetryPolicyV1,
)
from tests.task039e2_support import (
    synthetic_configuration_and_schedule,
    synthetic_hash,
)


class ScheduleAndTransportTests(unittest.TestCase):
    def test_schedule_is_deterministic_and_has_exact_call_budget(self) -> None:
        configuration, schedule = synthetic_configuration_and_schedule()
        configuration2, schedule2 = synthetic_configuration_and_schedule()
        self.assertEqual(schedule.artifact_hash, schedule2.artifact_hash)
        self.assertEqual(configuration.artifact_hash, configuration2.artifact_hash)
        slots = schedule.scientific_call_slots()
        self.assertEqual(len(slots), EXPECTED_MAXIMUM_SCIENTIFIC_CALLS)
        self.assertEqual(len([slot for slot in slots if slot[0] == "T1-B"]), 126)
        self.assertEqual(len([slot for slot in slots if slot[0] == "T2"]), 126)

    def test_result_dependent_ordering_and_hidden_calls_are_rejected(self) -> None:
        _, schedule = synthetic_configuration_and_schedule()
        with self.assertRaisesRegex(TASK039E2PreparationError, "result_dependent"):
            replace(schedule, result_dependent_ordering=True)
        with self.assertRaisesRegex(TASK039E2PreparationError, "call budget"):
            replace(schedule, t2_maximum_calls_per_relation=4)

    def test_t2_controller_adapter_rejects_hidden_fourth_call(self) -> None:
        integration = T2ControllerIntegrationPolicyV1(
            provider_proposal_adapter_hash=synthetic_hash("provider-adapter"),
            deterministic_validity_verifier_hash=synthetic_hash("verifier"),
            deterministic_t2_controller_hash=synthetic_hash("controller"),
            retrieval_renderer_policy_hash=synthetic_hash("retrieval-renderer"),
        )
        integration.assert_call_allowed(3)
        with self.assertRaisesRegex(TASK039E2PreparationError, "fourth"):
            integration.assert_call_allowed(4)
        self.assertFalse(integration.provider_selects_controller_action)

    def test_scientific_and_transport_retries_are_distinct(self) -> None:
        policy = TransportRetryPolicyV1()
        self.assertEqual(
            policy.classify_attempt(
                outcome="connection_failure", model_response_received=False
            ),
            (False, True),
        )
        self.assertEqual(
            policy.classify_attempt(
                outcome="malformed_response", model_response_received=True
            ),
            (True, False),
        )
        self.assertEqual(
            policy.classify_attempt(
                outcome="structured_response_received", model_response_received=True
            ),
            (True, False),
        )
        with self.assertRaisesRegex(TASK039E2PreparationError, "after a model response"):
            policy.classify_attempt(
                outcome="provider_5xx", model_response_received=True
            )

    def test_provider_response_custody_is_sanitized_and_cot_free(self) -> None:
        receipt = ProviderResponseCustodyReceiptV1(
            provider_identifier="SYNTHETIC_PROVIDER",
            model_identifier="SYNTHETIC_MODEL_VERSION_001",
            call_number=1,
            provider_request_identifier="SYNTHETIC_REQUEST_001",
            response_received=True,
            structured_parse_result="parsed",
            transport_retry_count=0,
            proposal_hash=synthetic_hash("proposal"),
        )
        self.assertEqual(
            receipt.raw_output_retention_policy,
            "sanitized_structured_output_first",
        )
        self.assertFalse(receipt.raw_model_output_stored)
        self.assertFalse(receipt.chain_of_thought_stored)
        self.assertFalse(receipt.runtime_authority_granted)


if __name__ == "__main__":
    unittest.main()
