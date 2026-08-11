import unittest

from paperworks.v6.task039e3_execution_prep_v1 import (
    MockProviderEventV1,
    MockProviderTransportV1,
    ProviderCallLedgerV1,
    ProviderCallSlotV1,
    ScientificRunAbortV1,
    TASK039E3PreparationError,
    build_main_request_v1,
    execute_mock_provider_slot_v1,
)
from task039e3_support import make_evidence, valid_core_document


def _slot(evidence=None) -> ProviderCallSlotV1:
    evidence = evidence or make_evidence()
    return ProviderCallSlotV1(
        0, evidence.relation.binding_hash, "T1", 1, True
    )


class Task039E3TransportParserCustodyTests(unittest.TestCase):
    def test_valid_structured_response_is_parsed_and_custodied(self) -> None:
        evidence = make_evidence()
        transport = MockProviderTransportV1(
            (MockProviderEventV1("valid_proposal", valid_core_document(evidence)),)
        )
        ledger = ProviderCallLedgerV1()
        result = execute_mock_provider_slot_v1(
            slot=_slot(evidence),
            request=build_main_request_v1(evidence.render_view()),
            transport=transport,
            ledger=ledger,
            parse_kind="proposal",
        )
        self.assertEqual(result.parsed_proposal.parse_status, "valid_structured")
        self.assertEqual(result.record.terminal_slot_state, "completed_structured")
        self.assertEqual(len(ledger.records), 1)
        self.assertEqual(len(ledger.ledger_hash), 64)

    def test_refusal_invalid_and_incomplete_each_consume_one_scientific_call(self) -> None:
        evidence = make_evidence()
        cases = (
            ("provider_refusal", "provider_refusal", "completed_refusal"),
            (
                "schema_invalid_response",
                "schema_parse_failure",
                "completed_invalid_response",
            ),
            (
                "incomplete_response",
                "incomplete_response",
                "completed_invalid_response",
            ),
        )
        for scenario, parse_status, terminal in cases:
            with self.subTest(scenario=scenario):
                transport = MockProviderTransportV1(
                    (MockProviderEventV1(scenario, valid_core_document(evidence)),)
                )
                ledger = ProviderCallLedgerV1()
                result = execute_mock_provider_slot_v1(
                    slot=_slot(evidence),
                    request=build_main_request_v1(evidence.render_view()),
                    transport=transport,
                    ledger=ledger,
                    parse_kind="proposal",
                )
                self.assertEqual(result.parsed_proposal.parse_status, parse_status)
                self.assertEqual(result.record.terminal_slot_state, terminal)
                self.assertEqual(transport.calls, 1)
                self.assertEqual(len(result.record.transport_attempts), 1)

    def test_429_500_timeout_and_connection_retry_same_scientific_slot(self) -> None:
        evidence = make_evidence()
        cases = ("http_429", "http_500", "no_response_timeout", "connection_failure")
        for scenario in cases:
            with self.subTest(scenario=scenario):
                transport = MockProviderTransportV1(
                    (
                        MockProviderEventV1(scenario),
                        MockProviderEventV1(
                            "valid_proposal", valid_core_document(evidence)
                        ),
                    )
                )
                ledger = ProviderCallLedgerV1()
                result = execute_mock_provider_slot_v1(
                    slot=_slot(evidence),
                    request=build_main_request_v1(evidence.render_view()),
                    transport=transport,
                    ledger=ledger,
                    parse_kind="proposal",
                )
                self.assertEqual(transport.calls, 2)
                self.assertEqual(len(ledger.records), 1)
                self.assertEqual(len(result.record.transport_attempts), 2)
                self.assertEqual(
                    len({attempt.outcome for attempt in result.record.transport_attempts}),
                    2,
                )
                self.assertEqual(
                    [
                        attempt.planned_retry_delay_seconds
                        for attempt in result.record.transport_attempts
                    ],
                    [2, None],
                )

    def test_400_401_403_are_non_retryable_and_abort_without_relation_skip(
        self,
    ) -> None:
        evidence = make_evidence()
        for scenario in ("http_400", "http_401", "http_403"):
            with self.subTest(scenario=scenario):
                transport = MockProviderTransportV1(
                    (MockProviderEventV1(scenario),)
                )
                ledger = ProviderCallLedgerV1()
                with self.assertRaises(ScientificRunAbortV1) as captured:
                    execute_mock_provider_slot_v1(
                        slot=_slot(evidence),
                        request=build_main_request_v1(evidence.render_view()),
                        transport=transport,
                        ledger=ledger,
                        parse_kind="proposal",
                    )
                self.assertEqual(transport.calls, 1)
                self.assertEqual(
                    ledger.records[-1].terminal_slot_state,
                    "transport_exhausted",
                )
                self.assertTrue(captured.exception.receipt.full_run_aborted)
                self.assertFalse(
                    captured.exception.receipt.relation_skipping_allowed
                )

    def test_transport_exhaustion_is_full_run_failure_with_frozen_custody(self) -> None:
        evidence = make_evidence()
        transport = MockProviderTransportV1(
            tuple(MockProviderEventV1("http_500") for _ in range(3))
        )
        ledger = ProviderCallLedgerV1()
        with self.assertRaises(ScientificRunAbortV1) as captured:
            execute_mock_provider_slot_v1(
                slot=_slot(evidence),
                request=build_main_request_v1(evidence.render_view()),
                transport=transport,
                ledger=ledger,
                parse_kind="proposal",
            )
        receipt = captured.exception.receipt
        self.assertEqual(transport.calls, 3)
        self.assertEqual(len(ledger.records), 1)
        self.assertEqual(len(receipt.completed_slot_record_hashes), 1)
        self.assertEqual(
            [
                attempt.planned_retry_delay_seconds
                for attempt in ledger.records[0].transport_attempts
            ],
            [2, 4, None],
        )
        self.assertFalse(receipt.automatic_resume_authority)
        self.assertFalse(receipt.automatic_rerun_policy)

    def test_append_only_ledger_rejects_duplicate_slot(self) -> None:
        evidence = make_evidence()
        ledger = ProviderCallLedgerV1()
        slot = _slot(evidence)
        request = build_main_request_v1(evidence.render_view())
        first = execute_mock_provider_slot_v1(
            slot=slot,
            request=request,
            transport=MockProviderTransportV1(
                (MockProviderEventV1("valid_proposal", valid_core_document(evidence)),)
            ),
            ledger=ledger,
            parse_kind="proposal",
        )
        original_hash = ledger.ledger_hash
        with self.assertRaises(TASK039E3PreparationError):
            ledger.append(
                slot=slot,
                request_hash=request.request_hash,
                response_present=True,
                provider_response_metadata={},
                transport_attempts=first.record.transport_attempts,
                parse_status="valid_structured",
                proposal_core_hash=first.record.proposal_core_hash,
                terminal_slot_state="completed_structured",
            )
        self.assertEqual(ledger.ledger_hash, original_hash)


if __name__ == "__main__":
    unittest.main()
