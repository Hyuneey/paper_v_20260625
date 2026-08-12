from __future__ import annotations

import json
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from paperworks.v6.common import stable_hash_v1
from paperworks.v6.task039e3_execution_prep_v1 import (
    EXACT_MODEL,
    FrozenProviderRequestV1,
    MockProviderResponseV1,
    MockProviderTransportV1,
    ProviderCallLedgerV1,
    ProviderCallSlotV1,
    build_capability_probe_request_v1,
    execute_mock_provider_slot_v1,
)
from paperworks.v6.task039e3_recovery_capability_v1 import (
    build_recovery_capability_request_v1,
    evaluate_recovery_capability_response_v1,
)
from paperworks.v6.task039e3_recovery_execution_v1 import (
    RecoveryScientificCompatibilityTransportV1,
    TASK039E3RecoveryExecutionError,
    execute_recovery_probe_v1,
    run_frozen_science_after_recovery_gate_v1,
)


def _present_response(
    *,
    token: str = "TASK039E3_STRICT_JSON_SCHEMA_V1",
    refusal: bool = False,
    response_id: str = "RECOVERY-PROVIDER-RESPONSE",
) -> MockProviderResponseV1:
    return MockProviderResponseV1(
        response_present=True,
        outcome="provider_refusal" if refusal else "successful_response",
        status_code=200,
        model=EXACT_MODEL,
        content=json.dumps(
            {
                "fixture_id": "SYNTHETIC_CAPABILITY_CHECK",
                "capability_token": token,
            },
            sort_keys=True,
            separators=(",", ":"),
        ),
        refusal=refusal,
        finish_reason="stop",
        response_id=response_id,
        token_usage={"prompt_tokens": 7, "completion_tokens": 3, "total_tokens": 10},
    )


def _timeout_response() -> MockProviderResponseV1:
    return MockProviderResponseV1(
        response_present=False,
        outcome="timeout_before_response",
        status_code=None,
        model=None,
        content=None,
    )


class _CountingTransport(MockProviderTransportV1):
    """Pure in-memory transport whose counters are independent audit evidence."""

    def __init__(self, responses: list[MockProviderResponseV1]) -> None:
        self._responses = list(responses)
        self._calls = 0
        self._request_objects: list[FrozenProviderRequestV1] = []
        self._attempt_custody: list[object] = []

    @property
    def calls(self) -> int:
        return self._calls

    @property
    def request_hashes(self) -> tuple[str, ...]:
        return tuple(request.request_hash for request in self._request_objects)

    @property
    def request_objects(self) -> tuple[FrozenProviderRequestV1, ...]:
        return tuple(self._request_objects)

    @property
    def attempt_custody(self) -> tuple[object, ...]:
        return tuple(self._attempt_custody)

    def send(self, request: FrozenProviderRequestV1) -> MockProviderResponseV1:
        if self._calls >= len(self._responses):
            raise AssertionError("synthetic transport exhausted")
        response = self._responses[self._calls]
        self._calls += 1
        self._request_objects.append(request)
        self._attempt_custody.append(object())
        return response


class IndependentCompatibilityCustodyAuditTests(unittest.TestCase):
    def test_integrated_science_entry_rejects_block_before_adapter_construction(self) -> None:
        blocked_execution = SimpleNamespace(
            gate=SimpleNamespace(gate_status="BLOCK")
        )
        with patch(
            "paperworks.v6.task039e3_recovery_execution_v1."
            "RecoveryScientificCompatibilityTransportV1"
        ) as adapter:
            with self.assertRaisesRegex(
                TASK039E3RecoveryExecutionError,
                "requires capability PASS",
            ):
                run_frozen_science_after_recovery_gate_v1(
                    repository_root=None,  # type: ignore[arg-type]
                    execution_commit="unused",
                    e1_private_root=None,  # type: ignore[arg-type]
                    recovery_private_root=None,  # type: ignore[arg-type]
                    live_transport=None,  # type: ignore[arg-type]
                    preflight={},
                    recovery_execution=blocked_execution,  # type: ignore[arg-type]
                    recovery_capability_receipt={},
                    recovery_capability_custody=None,  # type: ignore[arg-type]
                    source_manifest={},
                )
        adapter.assert_not_called()

    def test_adapter_itself_can_emit_local_ack_from_corrected_block_response(self) -> None:
        """Detect the mandatory reachability defect without repairing it."""

        refused = _present_response(refusal=True, response_id="REFUSED-RESPONSE")
        corrected_gate = evaluate_recovery_capability_response_v1(refused)
        self.assertEqual(corrected_gate.gate_status, "BLOCK")
        self.assertIn("provider_refusal", corrected_gate.failure_codes)

        delegate = _CountingTransport([_present_response()])
        adapter = RecoveryScientificCompatibilityTransportV1(
            delegate=delegate,  # type: ignore[arg-type]
            recovery_response=refused,
        )
        local = adapter.send(build_capability_probe_request_v1())

        self.assertEqual(delegate.calls, 0)
        self.assertEqual(
            local.outcome,
            "local_corrected_gate_compatibility_acknowledgement",
        )
        self.assertFalse(local.refusal)
        self.assertIn('"structured_output_supported":true', local.content or "")
        self.assertEqual(local.response_id, "REFUSED-RESPONSE")

    def test_local_ack_is_zero_provider_zero_science_then_delegates_unchanged(self) -> None:
        provider_scientific_response = _present_response(
            response_id="SYNTHETIC-SCIENTIFIC-RESPONSE"
        )
        delegate = _CountingTransport([provider_scientific_response])
        recovery_response = _present_response()
        adapter = RecoveryScientificCompatibilityTransportV1(
            delegate=delegate,  # type: ignore[arg-type]
            recovery_response=recovery_response,
        )
        historical_capability_request = build_capability_probe_request_v1()
        local = adapter.send(historical_capability_request)
        self.assertEqual(delegate.calls, 0)
        self.assertEqual(adapter.calls, 0)
        self.assertEqual(adapter.request_hashes, ())
        self.assertEqual(adapter.attempt_custody, ())
        self.assertEqual(local.outcome, "local_corrected_gate_compatibility_acknowledgement")

        model_visible_request = build_recovery_capability_request_v1()
        delegated = adapter.send(model_visible_request)
        self.assertIs(delegated, provider_scientific_response)
        self.assertEqual(delegate.calls, 1)
        self.assertIs(delegate.request_objects[0], model_visible_request)
        self.assertEqual(adapter.request_hashes, (model_visible_request.request_hash,))

    def test_one_two_three_attempt_probe_accounting_remains_logically_one(self) -> None:
        for attempts in (1, 2, 3):
            with self.subTest(attempts=attempts):
                delegate = _CountingTransport(
                    [_timeout_response()] * (attempts - 1) + [_present_response()]
                )
                execution = execute_recovery_probe_v1(delegate)
                self.assertEqual(delegate.calls, attempts)
                self.assertEqual(execution.transport_attempts, attempts)
                self.assertEqual(execution.transport_retries, attempts - 1)
                self.assertEqual(
                    execution.accounting.historical_probe_count,
                    1,
                )
                self.assertEqual(
                    execution.accounting.current_recovery_probe_count,
                    1,
                )
                self.assertEqual(execution.accounting.cumulative_probe_count, 2)
                self.assertEqual(
                    sum(bool(record.get("response_present")) for record in execution.attempt_records),
                    1,
                )

    def test_local_provider_ledger_record_is_marked_local_but_copies_metadata(self) -> None:
        recovery_response = _present_response(response_id="REAL-RECOVERY-ID")
        delegate = _CountingTransport([_present_response()])
        adapter = RecoveryScientificCompatibilityTransportV1(
            delegate=delegate,  # type: ignore[arg-type]
            recovery_response=recovery_response,
        )
        ledger = ProviderCallLedgerV1()
        slot = ProviderCallSlotV1(
            None,
            stable_hash_v1({"fixture": "SYNTHETIC_CAPABILITY_CHECK"}),
            "CAPABILITY",
            1,
            False,
        )
        result = execute_mock_provider_slot_v1(
            slot=slot,
            request=build_capability_probe_request_v1(),
            transport=adapter,
            ledger=ledger,
            parse_kind="capability",
        )
        record = result.record.to_dict()
        metadata = record["provider_response_metadata"]
        attempt = record["transport_attempts"][0]

        self.assertEqual(delegate.calls, 0)
        self.assertFalse(record["slot"]["scientific"])
        self.assertEqual(record["parse_status"], "pass")
        self.assertEqual(
            metadata["outcome"],
            "local_corrected_gate_compatibility_acknowledgement",
        )
        self.assertEqual(
            attempt["outcome"],
            "local_corrected_gate_compatibility_acknowledgement",
        )
        self.assertEqual(metadata["response_id"], "REAL-RECOVERY-ID")
        self.assertEqual(metadata["model"], EXACT_MODEL)
        self.assertEqual(
            metadata["token_usage"],
            {"prompt_tokens": 7, "completion_tokens": 3, "total_tokens": 10},
        )
        self.assertNotIn("response_origin", metadata)
        self.assertNotIn("provider_contacted", metadata)
        self.assertNotIn("provider_authored", metadata)

    def test_aggregate_retry_formula_uses_local_real_probe_substitution(self) -> None:
        """Expose the one-for-one counter substitution used by frozen science."""

        for recovery_attempts in (1, 2, 3):
            with self.subTest(recovery_attempts=recovery_attempts):
                # One real scientific request is added after the recovery probe.
                actual_provider_attempts = recovery_attempts + 1
                actual_provider_logical_calls = 1 + 1
                local_compatibility_slots = 1
                scientific_ledger_slots = 1
                frozen_provider_ledger_records = (
                    local_compatibility_slots + scientific_ledger_slots
                )
                independently_counted_retries = (
                    actual_provider_attempts - actual_provider_logical_calls
                )
                frozen_formula_retries = (
                    actual_provider_attempts - frozen_provider_ledger_records
                )
                self.assertEqual(frozen_formula_retries, independently_counted_retries)
                self.assertEqual(frozen_formula_retries, recovery_attempts - 1)
                self.assertNotEqual(
                    {"recovery_probe": 1, "scientific": 1},
                    {"local_compatibility": 1, "scientific": 1},
                )


if __name__ == "__main__":
    unittest.main()
