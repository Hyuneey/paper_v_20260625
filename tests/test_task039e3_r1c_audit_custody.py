"""Independent custody and failure-path oracle for TASK-039E3-R1C-AUDIT.

The assertions deliberately characterize the frozen Commit-A behavior.  They
do not repair V2 production code and they use only synthetic provider events
and temporary roots.
"""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from paperworks.v6.common import stable_hash_v1
from paperworks.v6.task039e3_execution_prep_v1 import (
    ProviderCallSlotV1,
    ScientificRunAbortV1,
    execute_mock_provider_slot_v1,
)
from paperworks.v6.task039e3_recovery_capability_v1 import (
    RECOVERY_CAPABILITY_FIXTURE_ID,
    RECOVERY_CAPABILITY_TOKEN,
    build_recovery_capability_request_v1,
)
from paperworks.v6.task039e3_recovery_custody_v2 import (
    RecoveryCapabilityProviderLedgerV2,
    ScientificModelIdentityMismatchAbortV2,
    ScientificProviderLedgerV2,
    TASK039E3RecoveryCustodyV2Error,
)
from paperworks.v6.task039e3_recovery_live_transport_v2 import (
    RecoveryLiveOpenAIChatCompletionsTransportV2,
)
from paperworks.v6.task039e3_recovery_execution_v2 import (
    run_capability_then_science_v2,
)


_REQUEST_HASH = stable_hash_v1({"audit": "synthetic-request"})
_MODEL = "gpt-5.4-2026-03-05"


def _canonical_hash(document: dict[str, object]) -> str:
    encoded = json.dumps(
        document,
        ensure_ascii=True,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _slot(*, scientific: bool, index: int = 0) -> ProviderCallSlotV1:
    return ProviderCallSlotV1(
        relation_schedule_index=index if scientific else None,
        relation_binding_hash=stable_hash_v1({"relation": index}),
        arm="T1" if scientific else "CAPABILITY",
        arm_local_call_number=1,
        scientific=scientific,
    )


def _attempt(
    *,
    number: int = 1,
    outcome: str = "successful_response",
    present: bool = True,
    model: str | None = _MODEL,
    response_id: str | None = "chatcmpl-audit",
    retry: bool = False,
) -> dict[str, object]:
    return {
        "attempt_number": number,
        "request_hash": _REQUEST_HASH,
        "response_origin": "provider",
        "provider_contacted": True,
        "provider_authored_response": present,
        "status_code": 200 if present else None,
        "outcome": outcome,
        "response_present": present,
        "returned_model": model if present else None,
        "response_id": response_id if present else None,
        "finish_reason": "stop" if present else None,
        "usage": {"total_tokens": 3} if present else None,
        "system_fingerprint": "fp-audit" if present else None,
        "retry_eligible": retry,
        "actual_retry_delay_seconds": None,
        "retry_after_observed": None,
    }


def _append(
    ledger: object,
    *,
    scientific: bool,
    attempts: list[dict[str, object]],
    index: int = 0,
    response_present: bool = True,
    terminal: str = "completed_structured",
) -> object:
    last = attempts[-1]
    return ledger.append(  # type: ignore[attr-defined]
        slot=_slot(scientific=scientific, index=index),
        request_hash=_REQUEST_HASH,
        response_present=response_present,
        provider_response_metadata={
            "outcome": last["outcome"],
            "status_code": last["status_code"],
            "model": last["returned_model"],
            "response_id": last["response_id"],
            "finish_reason": last["finish_reason"],
            "token_usage": last["usage"],
        },
        transport_attempts=attempts,
        parse_status="valid_structured" if response_present else "transport_failure",
        proposal_core_hash=None,
        terminal_slot_state=terminal,
    )


class _HTTPResponse:
    status = 200

    def __init__(self, document: dict[str, object]) -> None:
        self._raw = json.dumps(document).encode("utf-8")

    def __enter__(self) -> "_HTTPResponse":
        return self

    def __exit__(self, *_args: object) -> None:
        return None

    def read(self) -> bytes:
        return self._raw


def _provider_document(*, refusal: str | None = None, content: str = "{}") -> dict[str, object]:
    return {
        "id": "chatcmpl-audit",
        "model": _MODEL,
        "choices": [
            {
                "finish_reason": "stop",
                "message": {"content": None if refusal else content, "refusal": refusal},
            }
        ],
        "usage": {"total_tokens": 3},
        "system_fingerprint": "fp-audit",
    }


class R1CAuditCustodyTests(unittest.TestCase):
    def test_capability_and_science_ledgers_are_type_separated(self) -> None:
        capability = RecoveryCapabilityProviderLedgerV2()
        science = ScientificProviderLedgerV2(abort_on_model_mismatch=False)
        success = [_attempt()]
        _append(capability, scientific=False, attempts=success)
        _append(science, scientific=True, attempts=success)
        capability_wrong_type = RecoveryCapabilityProviderLedgerV2()
        with self.assertRaisesRegex(TASK039E3RecoveryCustodyV2Error, "scientific"):
            _append(capability_wrong_type, scientific=True, attempts=success, index=1)
        with self.assertRaisesRegex(TASK039E3RecoveryCustodyV2Error, "non-scientific"):
            _append(science, scientific=False, attempts=success)
        self.assertEqual(capability.records[0].logical_call_kind, "recovery_capability")
        self.assertEqual(science.records[0].logical_call_kind, "scientific")
        self.assertNotEqual(capability.ledger_hash, science.ledger_hash)

    def test_disk_hash_chain_reconstructs_independently(self) -> None:
        with TemporaryDirectory() as raw:
            path = Path(raw) / "scientific.jsonl"
            ledger = ScientificProviderLedgerV2(path, abort_on_model_mismatch=False)
            _append(ledger, scientific=True, attempts=[_attempt(response_id="chatcmpl-1")])
            _append(
                ledger,
                scientific=True,
                index=1,
                attempts=[_attempt(response_id="chatcmpl-2")],
            )
            documents = [json.loads(line) for line in path.read_text("utf-8").splitlines()]
            self.assertEqual(len(documents), 2)
            previous: str | None = None
            for sequence, document in enumerate(documents):
                supplied = document.pop("record_hash")
                self.assertEqual(document["sequence_index"], sequence)
                self.assertEqual(document["previous_record_hash"], previous)
                self.assertEqual(supplied, _canonical_hash(document))
                previous = supplied
            self.assertEqual(previous, ledger.provider_ledger_head_hash)

    def test_model_mismatch_is_durable_before_abort(self) -> None:
        mismatch = _attempt(
            outcome="model_identity_integrity",
            model="gpt-unexpected-snapshot",
            response_id="chatcmpl-unexpected",
        )
        with TemporaryDirectory() as raw:
            path = Path(raw) / "scientific.jsonl"
            ledger = ScientificProviderLedgerV2(path)
            with self.assertRaises(ScientificModelIdentityMismatchAbortV2) as caught:
                _append(ledger, scientific=True, attempts=[mismatch])
            document = json.loads(path.read_text("utf-8"))
            self.assertEqual(document["returned_model"], "gpt-unexpected-snapshot")
            self.assertEqual(document["response_id"], "chatcmpl-unexpected")
            self.assertEqual(
                document["terminal_slot_state"], "completed_model_identity_mismatch"
            )
            self.assertEqual(caught.exception.provider_ledger_hash, ledger.ledger_hash)
            self.assertFalse(caught.exception.automatic_resume_authorized)

    def test_transport_exhaustion_is_custodied_before_abort(self) -> None:
        transport = RecoveryLiveOpenAIChatCompletionsTransportV2(
            api_key="synthetic-only",
            opener=lambda *_args, **_kwargs: (_ for _ in ()).throw(
                TimeoutError("synthetic timeout")
            ),
            sleeper=lambda _seconds: None,
        )
        with TemporaryDirectory() as raw:
            path = Path(raw) / "scientific.jsonl"
            ledger = ScientificProviderLedgerV2(
                path, attempt_supplier=lambda: transport.attempt_custody
            )
            with self.assertRaises(ScientificRunAbortV1) as caught:
                execute_mock_provider_slot_v1(
                    slot=_slot(scientific=True),
                    request=build_recovery_capability_request_v1(),
                    transport=transport,
                    ledger=ledger,  # type: ignore[arg-type]
                    parse_kind="proposal",
                )
            document = json.loads(path.read_text("utf-8"))
            self.assertEqual(len(document["transport_attempts"]), 3)
            self.assertEqual(document["terminal_slot_state"], "transport_exhausted")
            self.assertEqual(
                caught.exception.receipt.provider_call_ledger_hash, ledger.ledger_hash
            )

    def test_refusal_and_parser_rejection_are_durably_distinct(self) -> None:
        scenarios = (
            ("refusal", _provider_document(refusal="synthetic refusal"), "completed_refusal"),
            ("invalid", _provider_document(content="{"), "completed_invalid_response"),
        )
        for label, provider_document, terminal in scenarios:
            with self.subTest(label=label), TemporaryDirectory() as raw:
                transport = RecoveryLiveOpenAIChatCompletionsTransportV2(
                    api_key="synthetic-only",
                    opener=lambda *_args, doc=provider_document, **_kwargs: _HTTPResponse(doc),
                    sleeper=lambda _seconds: None,
                )
                path = Path(raw) / "scientific.jsonl"
                ledger = ScientificProviderLedgerV2(
                    path, attempt_supplier=lambda: transport.attempt_custody
                )
                execute_mock_provider_slot_v1(
                    slot=_slot(scientific=True),
                    request=build_recovery_capability_request_v1(),
                    transport=transport,
                    ledger=ledger,  # type: ignore[arg-type]
                    parse_kind="proposal",
                )
                document = json.loads(path.read_text("utf-8"))
                self.assertEqual(document["terminal_slot_state"], terminal)
                self.assertTrue(document["response_present"])
                self.assertTrue(document["provider_authored_response"])

    def test_fsync_failure_leaves_a_valid_looking_uncommitted_tail(self) -> None:
        """Characterize a BLOCKING ambiguity: disk and in-memory heads diverge."""

        with TemporaryDirectory() as raw:
            path = Path(raw) / "scientific.jsonl"
            ledger = ScientificProviderLedgerV2(path, abort_on_model_mismatch=False)
            _append(ledger, scientific=True, attempts=[_attempt(response_id="chatcmpl-1")])
            durable_head = ledger.provider_ledger_head_hash
            with patch(
                "paperworks.v6.task039e3_recovery_custody_v2.os.fsync",
                side_effect=OSError("synthetic fsync failure"),
            ):
                with self.assertRaisesRegex(
                    TASK039E3RecoveryCustodyV2Error, "durably frozen"
                ):
                    _append(
                        ledger,
                        scientific=True,
                        index=1,
                        attempts=[_attempt(response_id="chatcmpl-2")],
                    )
            visible = [json.loads(line) for line in path.read_text("utf-8").splitlines()]
            self.assertEqual(len(ledger.records), 1)
            self.assertEqual(ledger.provider_ledger_head_hash, durable_head)
            self.assertEqual(len(visible), 2)
            self.assertEqual(visible[1]["previous_record_hash"], durable_head)
            self.assertEqual(
                visible[1]["record_hash"],
                _canonical_hash({key: value for key, value in visible[1].items() if key != "record_hash"}),
            )

    def test_unhandled_scientific_exception_materializes_no_failure_receipt(self) -> None:
        """Characterize a BLOCKING failure-path artifact omission."""

        content = json.dumps(
            {
                "fixture_id": RECOVERY_CAPABILITY_FIXTURE_ID,
                "capability_token": RECOVERY_CAPABILITY_TOKEN,
            },
            sort_keys=True,
            separators=(",", ":"),
        )
        transport = RecoveryLiveOpenAIChatCompletionsTransportV2(
            api_key="synthetic-only",
            opener=lambda *_args, **_kwargs: _HTTPResponse(
                _provider_document(content=content)
            ),
            sleeper=lambda _seconds: None,
        )
        with TemporaryDirectory() as raw:
            root = Path(raw)
            with patch(
                "paperworks.v6.task039e3_recovery_execution_v2.run_post_capability_scientific_execution_v2",
                side_effect=RuntimeError("synthetic deterministic verifier failure"),
            ):
                with self.assertRaisesRegex(RuntimeError, "verifier failure"):
                    run_capability_then_science_v2(
                        execution_commit="b" * 40,
                        source_manifest_hash="a" * 64,
                        r2_authorization_hash="c" * 64,
                        e1_private_root=root / "synthetic-e1",
                        recovery_private_root=root / "synthetic-recovery",
                        public_cohort={},
                        relation_identities=tuple(f"r-{index}" for index in range(42)),
                        transport=transport,
                        progress=lambda _message: None,
                    )
            generated = {
                path.name for path in (root / "synthetic-recovery").rglob("*") if path.is_file()
            }
            self.assertIn("recovery_capability_receipt_v2.json", generated)
            self.assertFalse(any("failure" in name.lower() for name in generated))


if __name__ == "__main__":
    unittest.main()
