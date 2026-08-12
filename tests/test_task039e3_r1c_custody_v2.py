from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from paperworks.v6.common import stable_hash_v1
from paperworks.v6.task039e3_execution_prep_v1 import (
    FrozenProviderRequestV1,
    MockProviderResponseV1,
    MockProviderTransportV1,
    ProviderCallSlotV1,
    execute_mock_provider_slot_v1,
)
from paperworks.v6.task039e3_recovery_capability_v1 import (
    build_recovery_capability_request_v1,
)
from paperworks.v6.task039e3_recovery_custody_v2 import (
    LOCAL_COMPATIBILITY_SLOTS,
    ProviderTransportAttemptCustodyV2,
    RecoveryCapabilityProviderLedgerV2,
    ScientificModelIdentityMismatchAbortV2,
    ScientificProviderLedgerV2,
    TASK039E3RecoveryCustodyV2Error,
    build_typed_provider_accounting_v2,
)


REQUEST_HASH = stable_hash_v1({"request": "synthetic"})
RELATION_HASH = stable_hash_v1({"relation": "synthetic"})


def _slot(*, scientific: bool, index: int = 1) -> ProviderCallSlotV1:
    return ProviderCallSlotV1(
        relation_schedule_index=(index - 1 if scientific else None),
        relation_binding_hash=(
            stable_hash_v1({"relation": f"synthetic-{index}"})
            if scientific
            else RELATION_HASH
        ),
        arm=("T1" if scientific else "CAPABILITY"),
        arm_local_call_number=1,
        scientific=scientific,
    )


def _attempt(
    number: int,
    *,
    outcome: str,
    present: bool,
    model: str | None = None,
    response_id: str | None = None,
    retry: bool = False,
) -> dict[str, object]:
    return {
        "attempt_number": number,
        "request_hash": REQUEST_HASH,
        "response_origin": "provider",
        "provider_contacted": True,
        "provider_authored_response": present,
        "status_code": 200 if present else None,
        "outcome": outcome,
        "response_present": present,
        "returned_model": model,
        "response_id": response_id,
        "finish_reason": "stop" if present else None,
        "usage": {"total_tokens": 5} if present else None,
        "system_fingerprint": "fp-test" if present else None,
        "retry_eligible": retry,
        "actual_retry_delay_seconds": (float(number - 1) if number > 1 else None),
        "retry_after_observed": None,
    }


def _append(
    ledger: object,
    *,
    scientific: bool,
    attempts: list[dict[str, object]],
    metadata: dict[str, object] | None = None,
    index: int = 1,
) -> object:
    metadata = metadata or {
        "outcome": "successful_response",
        "status_code": 200,
        "model": "gpt-5.4-2026-03-05",
        "response_id": f"chatcmpl-{index}",
        "finish_reason": "stop",
        "token_usage": {"total_tokens": 5},
    }
    return ledger.append(  # type: ignore[attr-defined]
        slot=_slot(scientific=scientific, index=index),
        request_hash=REQUEST_HASH,
        response_present=True,
        provider_response_metadata=metadata,
        transport_attempts=attempts,
        parse_status="valid_structured" if scientific else "pass",
        proposal_core_hash=None,
        terminal_slot_state="completed_structured",
    )


class RecoveryCustodyV2Tests(unittest.TestCase):
    def test_capability_ledger_accepts_exactly_one_provider_logical_call(self) -> None:
        ledger = RecoveryCapabilityProviderLedgerV2()
        record = _append(
            ledger,
            scientific=False,
            attempts=[
                _attempt(
                    1,
                    outcome="successful_response",
                    present=True,
                    model="gpt-5.4-2026-03-05",
                    response_id="chatcmpl-capability",
                )
            ],
        )
        self.assertEqual(record.logical_call_kind, "recovery_capability")
        self.assertEqual(record.response_origin, "provider")
        self.assertTrue(record.provider_contacted)
        self.assertTrue(record.provider_authored_response)
        self.assertEqual(len(ledger.records), 1)
        with self.assertRaisesRegex(TASK039E3RecoveryCustodyV2Error, "only one"):
            _append(ledger, scientific=False, attempts=list(record.transport_attempts))

    def test_capability_attempt_and_retry_accounting_is_independent(self) -> None:
        for attempts in (1, 2, 3):
            with self.subTest(attempts=attempts):
                accounting = build_typed_provider_accounting_v2(
                    capability_transport_attempts=attempts,
                    scientific_logical_calls=252,
                    scientific_transport_attempts=257,
                    full_scientific_run_complete=True,
                )
                self.assertEqual(
                    accounting.current_recovery_capability_transport_retries,
                    attempts - 1,
                )
                self.assertEqual(accounting.scientific_transport_retries, 5)
                self.assertEqual(accounting.local_compatibility_slots, 0)
                self.assertEqual(accounting.cumulative_real_provider_capability_probes, 2)
                self.assertEqual(accounting.current_run_real_provider_logical_calls, 253)
                self.assertEqual(
                    accounting.current_run_provider_transport_attempts,
                    attempts + 257,
                )

    def test_local_compatibility_slots_are_unrepresentable(self) -> None:
        self.assertEqual(LOCAL_COMPATIBILITY_SLOTS, 0)
        with self.assertRaisesRegex(
            TASK039E3RecoveryCustodyV2Error,
            "local compatibility slots",
        ):
            accounting = build_typed_provider_accounting_v2(
                capability_transport_attempts=1,
                scientific_logical_calls=252,
                scientific_transport_attempts=252,
                full_scientific_run_complete=True,
            )
            object.__setattr__(accounting, "local_compatibility_slots", 1)
            accounting.__post_init__()

    def test_capability_and_scientific_hash_chains_are_separate(self) -> None:
        capability = RecoveryCapabilityProviderLedgerV2()
        science = ScientificProviderLedgerV2(abort_on_model_mismatch=False)
        success = _attempt(
            1,
            outcome="successful_response",
            present=True,
            model="gpt-5.4-2026-03-05",
            response_id="chatcmpl-success",
        )
        _append(capability, scientific=False, attempts=[success])
        first = _append(science, scientific=True, attempts=[success], index=1)
        second = _append(science, scientific=True, attempts=[success], index=2)
        self.assertIsNone(capability.records[0].previous_record_hash)
        self.assertIsNone(first.previous_record_hash)
        self.assertEqual(second.previous_record_hash, first.record_hash)
        self.assertNotEqual(capability.ledger_hash, science.ledger_hash)
        self.assertTrue(all(record.slot.scientific for record in science.records))

    def test_model_mismatch_is_persisted_then_aborts_science(self) -> None:
        unexpected = _attempt(
            1,
            outcome="model_identity_integrity",
            present=True,
            model="gpt-unexpected",
            response_id="chatcmpl-unexpected",
        )
        ledger = ScientificProviderLedgerV2()
        with self.assertRaises(ScientificModelIdentityMismatchAbortV2) as caught:
            _append(
                ledger,
                scientific=True,
                attempts=[unexpected],
                metadata={
                    "outcome": "model_identity_integrity",
                    "status_code": 200,
                    "model": "gpt-unexpected",
                    "response_id": "chatcmpl-unexpected",
                },
            )
        self.assertEqual(len(ledger.records), 1)
        record = ledger.records[0]
        self.assertEqual(record.returned_model, "gpt-unexpected")
        self.assertEqual(record.response_id, "chatcmpl-unexpected")
        self.assertEqual(record.terminal_slot_state, "completed_model_identity_mismatch")
        self.assertEqual(record.parse_status, "model_identity_mismatch")
        self.assertEqual(caught.exception.actual_returned_model, "gpt-unexpected")
        self.assertFalse(caught.exception.automatic_resume_authorized)
        self.assertEqual(caught.exception.provider_ledger_hash, ledger.ledger_hash)

    def test_frozen_slot_executor_uses_v2_ledger_and_aborts_after_custody(self) -> None:
        class _MismatchTransport(MockProviderTransportV1):
            def __init__(self) -> None:
                pass

            def send(self, request: FrozenProviderRequestV1) -> MockProviderResponseV1:
                return MockProviderResponseV1(
                    response_present=True,
                    outcome="model_identity_integrity",
                    status_code=200,
                    model="gpt-unexpected",
                    content=None,
                    response_id="chatcmpl-unexpected",
                )

        detailed_attempts = [
            _attempt(
                1,
                outcome="model_identity_integrity",
                present=True,
                model="gpt-unexpected",
                response_id="chatcmpl-unexpected",
            )
        ]
        ledger = ScientificProviderLedgerV2(
            attempt_supplier=lambda: detailed_attempts
        )
        with self.assertRaises(ScientificModelIdentityMismatchAbortV2):
            execute_mock_provider_slot_v1(
                slot=_slot(scientific=True),
                request=build_recovery_capability_request_v1(),
                transport=_MismatchTransport(),
                ledger=ledger,  # type: ignore[arg-type]
                parse_kind="proposal",
            )
        self.assertEqual(len(ledger.records), 1)
        self.assertEqual(
            ledger.records[0].terminal_slot_state,
            "completed_model_identity_mismatch",
        )
        self.assertEqual(ledger.records[0].returned_model, "gpt-unexpected")

    def test_model_mismatch_metadata_cannot_be_discarded(self) -> None:
        with self.assertRaisesRegex(
            TASK039E3RecoveryCustodyV2Error,
            "preserve model and response ID",
        ):
            ProviderTransportAttemptCustodyV2.from_value(
                _attempt(
                    1,
                    outcome="model_identity_integrity",
                    present=True,
                    model=None,
                    response_id=None,
                ),
                request_hash=REQUEST_HASH,
                fallback_attempt_number=1,
                terminal_metadata={},
            )

    def test_durable_ledgers_use_distinct_files_and_hash_chains(self) -> None:
        success = _attempt(
            1,
            outcome="successful_response",
            present=True,
            model="gpt-5.4-2026-03-05",
            response_id="chatcmpl-success",
        )
        with TemporaryDirectory() as raw:
            root = Path(raw)
            capability_path = root / "capability.jsonl"
            scientific_path = root / "scientific.jsonl"
            capability = RecoveryCapabilityProviderLedgerV2(capability_path)
            scientific = ScientificProviderLedgerV2(
                scientific_path, abort_on_model_mismatch=False
            )
            _append(capability, scientific=False, attempts=[success])
            _append(scientific, scientific=True, attempts=[success])
            capability_document = json.loads(capability_path.read_text("utf-8"))
            scientific_document = json.loads(scientific_path.read_text("utf-8"))
            self.assertEqual(
                capability_document["logical_call_kind"], "recovery_capability"
            )
            self.assertEqual(scientific_document["logical_call_kind"], "scientific")
            self.assertNotEqual(capability.ledger_hash, scientific.ledger_hash)

    def test_full_run_range_and_scientific_retry_math_are_fail_closed(self) -> None:
        with self.assertRaisesRegex(TASK039E3RecoveryCustodyV2Error, "completed"):
            build_typed_provider_accounting_v2(
                capability_transport_attempts=1,
                scientific_logical_calls=251,
                scientific_transport_attempts=251,
                full_scientific_run_complete=True,
            )
        with self.assertRaisesRegex(TASK039E3RecoveryCustodyV2Error, "attempt"):
            build_typed_provider_accounting_v2(
                capability_transport_attempts=1,
                scientific_logical_calls=252,
                scientific_transport_attempts=251,
            )


if __name__ == "__main__":
    unittest.main()
