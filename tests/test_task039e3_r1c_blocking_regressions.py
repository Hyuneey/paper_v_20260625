"""Independent regression oracle for the three R1B-AUDIT blockers.

The oracle is intentionally additive and offline.  It verifies the active V2
path rather than rewriting or treating historical R1B sources as remediated.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from paperworks.v6.common import stable_hash_v1, thaw_json
from paperworks.v6.task039e3_execution_prep_v1 import ProviderCallSlotV1
from paperworks.v6.task039e3_recovery_capability_v1 import (
    RECOVERY_CAPABILITY_FIXTURE_ID,
    RECOVERY_CAPABILITY_TOKEN,
    build_recovery_capability_request_v1,
)
from paperworks.v6.task039e3_recovery_custody_v2 import (
    RecoveryCapabilityProviderLedgerV2,
    ScientificModelIdentityMismatchAbortV2,
    ScientificProviderLedgerV2,
    build_typed_provider_accounting_v2,
)
from paperworks.v6.task039e3_recovery_live_transport_v2 import (
    RecoveryLiveOpenAIChatCompletionsTransportV2,
)
from paperworks.v6.task039e3_recovery_science_v2 import (
    PostCapabilityAuthorityV2,
    ScientificLedgersV2,
    TASK039E3RecoveryScienceV2Error,
    _FrozenArmRunnersV2,
    _run_post_capability_scientific_execution_v2,
)


_HASH = "a" * 64
_MODEL = "gpt-5.4-2026-03-05"
_RELATION_HASH = stable_hash_v1({"synthetic": "r1c-blocker-oracle"})


class _HTTPResponse:
    def __init__(self, document: object) -> None:
        self.status = 200
        self._body = json.dumps(document).encode("utf-8")

    def __enter__(self) -> "_HTTPResponse":
        return self

    def __exit__(self, *_args: object) -> None:
        return None

    def read(self) -> bytes:
        return self._body


def _document(
    *,
    model: str = _MODEL,
    response_id: str = "chatcmpl-r1c-blocker-oracle",
    refusal: str | None = None,
) -> dict[str, object]:
    return {
        "id": response_id,
        "model": model,
        "system_fingerprint": "fp-r1c-blocker-oracle",
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


class _Ledger:
    def __init__(self) -> None:
        self.records: list[object] = []

    def append(self, value: object) -> None:
        self.records.append(value)


@dataclass(frozen=True)
class _Evidence:
    relation: object
    approved_evidence_identities: tuple[str, ...]


class _ForbiddenRunner:
    def __call__(self, **_kwargs: object) -> None:
        raise AssertionError("scientific runner must be unreachable on capability BLOCK")


class R1CBlockingRegressionOracle(unittest.TestCase):
    def test_b1_refusal_block_cannot_reach_e1_or_any_scientific_runner(self) -> None:
        transport = RecoveryLiveOpenAIChatCompletionsTransportV2(
            api_key="synthetic-only",
            opener=lambda *_args, **_kwargs: _HTTPResponse(
                _document(refusal="synthetic refusal")
            ),
            sleeper=lambda _seconds: self.fail("refusal must not retry"),
        )
        response = transport.send(build_recovery_capability_request_v1())
        self.assertTrue(response.response_present)
        self.assertTrue(response.refusal)
        self.assertEqual(response.model, _MODEL)

        e1_reached = False

        def forbidden_e1(_schedule: object) -> tuple[object, ...]:
            nonlocal e1_reached
            e1_reached = True
            return ()

        forbidden = _ForbiddenRunner()
        with self.assertRaisesRegex(TASK039E3RecoveryScienceV2Error, "PASS"):
            _run_post_capability_scientific_execution_v2(
                authority=PostCapabilityAuthorityV2(
                    gate_status="BLOCK",
                    capability_custody_frozen=True,
                    capability_receipt_durable=True,
                    capability_receipt_hash=_HASH,
                ),
                relation_identities=tuple(f"relation-{index}" for index in range(42)),
                evidence_loader=forbidden_e1,
                transport=object(),
                ledgers=ScientificLedgersV2(
                    provider=_Ledger(),
                    proposal=_Ledger(),
                    outcome=_Ledger(),
                    direct_number=_Ledger(),
                ),
                runners=_FrozenArmRunnersV2(
                    t0=forbidden,
                    t1=forbidden,
                    t1b=forbidden,
                    t2=forbidden,
                    direct_number=forbidden,
                ),
                progress=lambda _message: None,
            )
        self.assertFalse(e1_reached)

    def test_b2_one_two_three_attempt_sequences_are_explicit_provider_attempts(self) -> None:
        for success_attempt in (1, 2, 3):
            with self.subTest(success_attempt=success_attempt):
                calls = 0

                def opener(*_args: object, **_kwargs: object) -> _HTTPResponse:
                    nonlocal calls
                    calls += 1
                    if calls < success_attempt:
                        raise TimeoutError("synthetic timeout")
                    return _HTTPResponse(_document())

                transport = RecoveryLiveOpenAIChatCompletionsTransportV2(
                    api_key="synthetic-only",
                    opener=opener,
                    sleeper=lambda _seconds: None,
                )
                request = build_recovery_capability_request_v1()
                response = None
                for _ in range(success_attempt):
                    response = transport.send(request)
                self.assertIsNotNone(response)
                self.assertTrue(response.response_present)
                attempts = tuple(item.to_dict() for item in transport.attempt_custody)
                self.assertEqual(len(attempts), success_attempt)
                self.assertEqual(
                    [item["attempt_number"] for item in attempts],
                    list(range(1, success_attempt + 1)),
                )
                self.assertTrue(all(item["response_origin"] == "provider" for item in attempts))
                self.assertTrue(all(item["provider_contacted"] is True for item in attempts))
                self.assertNotIn("local", json.dumps(attempts, sort_keys=True).lower())

                ledger = RecoveryCapabilityProviderLedgerV2()
                ledger.append(
                    slot=ProviderCallSlotV1(
                        relation_schedule_index=None,
                        relation_binding_hash=_RELATION_HASH,
                        arm="CAPABILITY",
                        arm_local_call_number=1,
                        scientific=False,
                    ),
                    request_hash=request.request_hash,
                    response_present=True,
                    provider_response_metadata={
                        "outcome": response.outcome,
                        "status_code": response.status_code,
                        "model": response.model,
                        "response_id": response.response_id,
                        "finish_reason": response.finish_reason,
                        "token_usage": thaw_json(response.token_usage),
                    },
                    transport_attempts=transport.attempt_custody,
                    parse_status="pass",
                    proposal_core_hash=None,
                    terminal_slot_state="completed_structured",
                )
                self.assertEqual(len(ledger.records), 1)
                self.assertEqual(
                    len(ledger.records[0].transport_attempts), success_attempt
                )

                accounting = build_typed_provider_accounting_v2(
                    capability_transport_attempts=success_attempt,
                    scientific_logical_calls=252,
                    scientific_transport_attempts=257,
                    full_scientific_run_complete=True,
                )
                self.assertEqual(
                    accounting.current_recovery_capability_transport_retries,
                    success_attempt - 1,
                )
                self.assertEqual(accounting.scientific_transport_retries, 5)
                self.assertEqual(accounting.local_compatibility_slots, 0)
                self.assertEqual(
                    accounting.current_run_provider_transport_attempts,
                    success_attempt + 257,
                )

    def test_b3_model_mismatch_is_preserved_in_mapping_and_attempt_custody(self) -> None:
        unexpected_model = "gpt-unexpected"
        unexpected_id = "chatcmpl-unexpected"
        transport = RecoveryLiveOpenAIChatCompletionsTransportV2(
            api_key="synthetic-only",
            opener=lambda *_args, **_kwargs: _HTTPResponse(
                _document(model=unexpected_model, response_id=unexpected_id)
            ),
            sleeper=lambda _seconds: self.fail("model mismatch must not retry"),
        )
        mapped = transport.send(build_recovery_capability_request_v1())
        self.assertTrue(mapped.response_present)
        self.assertEqual(mapped.outcome, "model_identity_integrity")
        self.assertEqual(mapped.model, unexpected_model)
        self.assertEqual(mapped.response_id, unexpected_id)
        custody = transport.attempt_custody[0].to_dict()
        self.assertEqual(custody["returned_model"], unexpected_model)
        self.assertEqual(custody["response_id"], unexpected_id)
        self.assertEqual(
            custody["terminal_classification"],
            "completed_model_identity_mismatch",
        )
        self.assertFalse(custody["retry_eligible"])

        with TemporaryDirectory(prefix="task039e3-r1c-blocker-oracle-") as raw:
            ledger_path = Path(raw) / "scientific_provider_ledger_v2.jsonl"
            ledger = ScientificProviderLedgerV2(
                ledger_path,
                attempt_supplier=lambda: transport.attempt_custody,
            )
            with self.assertRaises(ScientificModelIdentityMismatchAbortV2):
                ledger.append(
                    slot=ProviderCallSlotV1(
                        relation_schedule_index=0,
                        relation_binding_hash=_RELATION_HASH,
                        arm="T1",
                        arm_local_call_number=1,
                        scientific=True,
                    ),
                    request_hash=build_recovery_capability_request_v1().request_hash,
                    response_present=mapped.response_present,
                    provider_response_metadata={
                        "outcome": mapped.outcome,
                        "status_code": mapped.status_code,
                        "model": mapped.model,
                        "response_id": mapped.response_id,
                        "finish_reason": mapped.finish_reason,
                        "token_usage": thaw_json(mapped.token_usage),
                    },
                    transport_attempts=transport.attempt_custody,
                    parse_status="schema_parse_failure",
                    proposal_core_hash=None,
                    terminal_slot_state="completed_invalid_response",
                )
            self.assertEqual(len(ledger.records), 1)
            durable = json.loads(ledger_path.read_text(encoding="utf-8"))
        self.assertEqual(durable["returned_model"], unexpected_model)
        self.assertEqual(durable["response_id"], unexpected_id)
        self.assertEqual(
            durable["terminal_slot_state"],
            "completed_model_identity_mismatch",
        )
        self.assertEqual(durable["parse_status"], "model_identity_mismatch")

    def test_active_v2_science_source_excludes_bridge_and_legacy_self_report(self) -> None:
        repository = Path(__file__).resolve().parents[1]
        active_paths = [
            repository / "src/paperworks/v6/task039e3_recovery_science_v2.py",
        ]
        optional = (
            repository / "src/paperworks/v6/task039e3_recovery_execution_v2.py",
            repository / "scripts/run_task039e3_recovery_execution_v2.py",
        )
        active_paths.extend(path for path in optional if path.exists())
        forbidden = (
            "Recovery" + "ScientificCompatibilityTransportV1",
            "model_" + "snapshot",
            "structured_output_" + "supported",
        )
        for path in active_paths:
            source = path.read_text(encoding="utf-8")
            for token in forbidden:
                self.assertNotIn(token, source, f"{token} reached active V2 path via {path}")

    def test_v2_module_imports_do_not_name_historical_compatibility_execution(self) -> None:
        repository = Path(__file__).resolve().parents[1]
        for path in (
            repository / "src/paperworks/v6/task039e3_recovery_science_v2.py",
            repository / "src/paperworks/v6/task039e3_recovery_live_transport_v2.py",
        ):
            source = path.read_text(encoding="utf-8")
            self.assertNotIn("task039e3_recovery_execution_v1", source)


if __name__ == "__main__":
    unittest.main()
