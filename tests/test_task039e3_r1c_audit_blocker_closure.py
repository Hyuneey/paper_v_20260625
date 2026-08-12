"""Independent offline oracle for TASK-039E3-R1C blocker closure.

The tests deliberately reproduce the three R1B-AUDIT findings against the
historical V1 implementation before checking the additive V2 path.  They use
only synthetic responses and temporary custody roots.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from paperworks.v6.common import stable_hash_v1
from paperworks.v6.task039e3_execution_prep_v1 import (
    MockProviderResponseV1,
    ProviderCallSlotV1,
    build_capability_probe_request_v1,
)
from paperworks.v6.task039e3_recovery_capability_v1 import (
    RECOVERY_CAPABILITY_FIXTURE_ID,
    RECOVERY_CAPABILITY_TOKEN,
    build_recovery_capability_request_v1,
    evaluate_recovery_capability_response_v1,
)
from paperworks.v6.task039e3_recovery_custody_v2 import (
    RecoveryCapabilityProviderLedgerV2,
    ScientificProviderLedgerV2,
    build_typed_provider_accounting_v2,
)
from paperworks.v6.task039e3_recovery_execution_v1 import (
    RecoveryScientificCompatibilityTransportV1,
)
from paperworks.v6.task039e3_recovery_execution_v2 import (
    build_recovery_capability_receipt_v2,
    execute_recovery_capability_probe_v2,
    freeze_capability_custody_v2,
    run_capability_then_science_v2,
)
from paperworks.v6.task039e3_recovery_live_transport_v2 import (
    RecoveryLiveOpenAIChatCompletionsTransportV2,
)


_MODEL = "gpt-5.4-2026-03-05"
_HASH = "a" * 64


class _HTTPResponse:
    def __init__(self, document: object) -> None:
        self.status = 200
        self._raw = json.dumps(document).encode("utf-8")

    def __enter__(self) -> "_HTTPResponse":
        return self

    def __exit__(self, *_args: object) -> None:
        return None

    def read(self) -> bytes:
        return self._raw


def _document(
    *,
    model: str = _MODEL,
    response_id: str = "chatcmpl-r1c-audit",
    refusal: str | None = None,
) -> dict[str, object]:
    return {
        "id": response_id,
        "model": model,
        "system_fingerprint": "fp-r1c-audit",
        "choices": [
            {
                "finish_reason": "stop",
                "message": {
                    "content": json.dumps(
                        {
                            "fixture_id": RECOVERY_CAPABILITY_FIXTURE_ID,
                            "capability_token": RECOVERY_CAPABILITY_TOKEN,
                        },
                        sort_keys=True,
                        separators=(",", ":"),
                    ),
                    "refusal": refusal,
                },
            }
        ],
        "usage": {"prompt_tokens": 3, "completion_tokens": 2, "total_tokens": 5},
    }


@dataclass
class _HistoricalDelegate:
    calls: int = 0

    @property
    def request_hashes(self) -> tuple[str, ...]:
        return ()

    @property
    def attempt_custody(self) -> tuple[object, ...]:
        return ()

    def send(self, _request: object) -> MockProviderResponseV1:
        self.calls += 1
        raise AssertionError("historical delegate must not be reached")


class R1CIndependentBlockerClosureAudit(unittest.TestCase):
    def test_b1_historical_adapter_defect_reproduced_but_v2_block_stops(self) -> None:
        refused = MockProviderResponseV1(
            True,
            "provider_refusal",
            200,
            _MODEL,
            None,
            refusal=True,
            finish_reason="stop",
            response_id="chatcmpl-historical-refusal",
        )
        self.assertEqual(
            evaluate_recovery_capability_response_v1(refused).gate_status,
            "BLOCK",
        )
        delegate = _HistoricalDelegate()
        historical = RecoveryScientificCompatibilityTransportV1(
            delegate=delegate,  # type: ignore[arg-type]
            recovery_response=refused,
        )
        local = historical.send(build_capability_probe_request_v1())
        self.assertEqual(local.outcome, "local_corrected_gate_compatibility_acknowledgement")
        self.assertEqual(delegate.calls, 0)

        transport = RecoveryLiveOpenAIChatCompletionsTransportV2(
            api_key="synthetic-audit-only",
            opener=lambda *_args, **_kwargs: _HTTPResponse(
                _document(refusal="synthetic refusal")
            ),
            sleeper=lambda _seconds: self.fail("refusal must not retry"),
        )
        with TemporaryDirectory(prefix="task039e3-r1c-audit-b1-") as raw:
            root = Path(raw)
            result = run_capability_then_science_v2(
                execution_commit=_HASH,
                source_manifest_hash=_HASH,
                r2_authorization_hash=_HASH,
                e1_private_root=root / "forbidden-e1-root",
                recovery_private_root=root / "recovery",
                public_cohort={},
                relation_identities=(),
                transport=transport,
                progress=lambda _message: None,
            )
            self.assertEqual(result["status"], "blocked_task039e3_recovery_capability_gate")
            self.assertEqual(result["scientific_calls"], 0)
            self.assertEqual(result["local_compatibility_slots"], 0)
            self.assertFalse((root / "recovery" / "scientific").exists())
            durable = (root / "recovery" / "recovery_capability_provider_v2.jsonl").read_text(
                encoding="utf-8"
            )
        self.assertNotIn("local_corrected_gate_compatibility_acknowledgement", durable)
        self.assertEqual(transport.calls, 1)

    def test_b2_typed_accounting_has_no_cross_family_cancellation(self) -> None:
        for success_attempt in (1, 2, 3):
            with self.subTest(success_attempt=success_attempt):
                calls = 0

                def opener(*_args: object, **_kwargs: object) -> _HTTPResponse:
                    nonlocal calls
                    calls += 1
                    if calls < success_attempt:
                        raise TimeoutError("synthetic offline timeout")
                    return _HTTPResponse(_document())

                transport = RecoveryLiveOpenAIChatCompletionsTransportV2(
                    api_key="synthetic-audit-only",
                    opener=opener,
                    sleeper=lambda _seconds: None,
                )
                execution = execute_recovery_capability_probe_v2(transport)
                self.assertEqual(execution.transport_attempts, success_attempt)
                self.assertEqual(execution.transport_retries, success_attempt - 1)
                accounting = build_typed_provider_accounting_v2(
                    capability_transport_attempts=success_attempt,
                    scientific_logical_calls=252,
                    scientific_transport_attempts=259,
                    full_scientific_run_complete=True,
                )
                self.assertEqual(accounting.current_recovery_capability_logical_calls, 1)
                self.assertEqual(
                    accounting.current_recovery_capability_transport_retries,
                    success_attempt - 1,
                )
                self.assertEqual(accounting.scientific_logical_calls, 252)
                self.assertEqual(accounting.scientific_transport_retries, 7)
                self.assertEqual(accounting.local_compatibility_slots, 0)
                self.assertEqual(
                    accounting.current_run_provider_transport_attempts,
                    success_attempt + 259,
                )

    def test_b3_v1_loss_reproduced_and_v2_preserves_through_receipt_and_ledgers(self) -> None:
        unexpected_model = "gpt-unexpected-snapshot"
        unexpected_id = "chatcmpl-unexpected"
        transport = RecoveryLiveOpenAIChatCompletionsTransportV2(
            api_key="synthetic-audit-only",
            opener=lambda *_args, **_kwargs: _HTTPResponse(
                _document(model=unexpected_model, response_id=unexpected_id)
            ),
            sleeper=lambda _seconds: self.fail("model mismatch must not retry"),
        )
        execution = execute_recovery_capability_probe_v2(transport)
        self.assertEqual(execution.gate.gate_status, "BLOCK")
        self.assertEqual(execution.response.model, unexpected_model)
        self.assertEqual(execution.response.response_id, unexpected_id)
        attempt = transport.attempt_custody[0]
        self.assertEqual(attempt.returned_model, unexpected_model)
        self.assertEqual(attempt.response_id, unexpected_id)
        self.assertEqual(attempt.terminal_classification, "completed_model_identity_mismatch")
        self.assertFalse(attempt.retry_eligible)

        with TemporaryDirectory(prefix="task039e3-r1c-audit-b3-") as raw:
            ledger = RecoveryCapabilityProviderLedgerV2(Path(raw) / "capability.jsonl")
            custody = freeze_capability_custody_v2(
                execution=execution,
                transport=transport,
                ledger=ledger,
            )
            receipt = build_recovery_capability_receipt_v2(
                execution=execution,
                execution_commit=_HASH,
                source_manifest_hash=_HASH,
                r2_authorization_hash=_HASH,
                custody_binding=custody,
            )
            durable = json.loads((Path(raw) / "capability.jsonl").read_text("utf-8"))
        self.assertEqual(durable["returned_model"], unexpected_model)
        self.assertEqual(durable["response_id"], unexpected_id)
        self.assertEqual(durable["terminal_slot_state"], "completed_model_identity_mismatch")
        self.assertEqual(receipt["returned_model"], unexpected_model)
        self.assertEqual(receipt["response_id"], unexpected_id)
        self.assertEqual(receipt["gate"]["gate_status"], "BLOCK")

        science = ScientificProviderLedgerV2(abort_on_model_mismatch=False)
        record = science.append(
            slot=ProviderCallSlotV1(
                0,
                stable_hash_v1({"synthetic": "relation"}),
                "T1",
                1,
                True,
            ),
            request_hash=build_recovery_capability_request_v1().request_hash,
            response_present=True,
            provider_response_metadata={
                "outcome": execution.response.outcome,
                "status_code": 200,
                "model": unexpected_model,
                "response_id": unexpected_id,
                "finish_reason": "stop",
                "token_usage": {"total_tokens": 5},
            },
            transport_attempts=transport.attempt_custody,
            parse_status="rejected",
            proposal_core_hash=None,
            terminal_slot_state="completed_invalid_response",
        )
        self.assertEqual(record.returned_model, unexpected_model)
        self.assertEqual(record.response_id, unexpected_id)
        self.assertEqual(record.terminal_slot_state, "completed_model_identity_mismatch")


if __name__ == "__main__":
    unittest.main()
