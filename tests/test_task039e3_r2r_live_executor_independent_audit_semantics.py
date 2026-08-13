"""Independent offline audit of R2R arm, retry, ledger, and integrity semantics."""

from __future__ import annotations

from dataclasses import replace
from io import BytesIO
import inspect
import json
from pathlib import Path
import tempfile
from typing import Callable
import unittest
from urllib.error import HTTPError

from paperworks.v6.common import stable_hash_v1
from paperworks.v6.task039e3_execution_prep_v1 import (
    MockProviderTransportV1,
    ProviderCallSlotV1,
    ScientificRunAbortV1,
    execute_mock_provider_slot_v1,
)
from paperworks.v6.task039e3_orchestration_v1 import (
    ConstructionOutcomeLedgerV1,
    ConstructionProposalLedgerV1,
)
from paperworks.v6.task039e3_r2r_execution_v1 import R2R_ARM_RUNNERS_V1
from paperworks.v6.task039e3_r2r_live_transport_v1 import (
    R2RLiveOpenAIChatCompletionsTransportV1,
)
from paperworks.v6.task039e3_r2r_precontact_v1 import (
    R2RIntegrityGuardedTransportV1,
    R2RObservedIntegrityStateV1,
    R2RPostContactIntegrityGuardV1,
    R2RSourceBlobIdentityV1,
    R2R_SCIENTIFIC_ACCOUNTING_BEHAVIOR_HASH_V1,
    TASK039E3R2RPrecontactError,
    capture_r2r_integrity_snapshot_v1,
)
from paperworks.v6.task039e3_r2r_request_contract_v1 import (
    DIRECT_NUMBER_PROVIDER_SCHEMA_V1_HASH,
    RECOVERY_MAIN_PROVIDER_SCHEMA_V2_HASH,
    build_r2r_main_request_v1,
)
from paperworks.v6.task039e3_recovery_execution_v3 import (
    TransactionalScientificProviderLedgerV3,
)
from paperworks.v6.task039e3_recovery_transactional_custody_v3 import (
    TransactionalHashChainCustodyV3,
)
from task039e3_support import direct_number_payload, make_evidence, valid_core_document


class _HTTP200:
    status = 200
    headers: dict[str, str] = {}

    def __init__(self, document: object) -> None:
        self._body = json.dumps(
            document,
            ensure_ascii=True,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")

    def __enter__(self) -> "_HTTP200":
        return self

    def __exit__(self, *_args: object) -> None:
        return None

    def read(self, _size: int = -1) -> bytes:
        return self._body


def _provider_response(payload: object, sequence: int) -> dict[str, object]:
    return {
        "id": f"chatcmpl-independent-audit-{sequence:04d}",
        "model": "gpt-5.4-2026-03-05",
        "choices": [
            {
                "finish_reason": "stop",
                "message": {
                    "content": json.dumps(
                        payload,
                        ensure_ascii=True,
                        allow_nan=False,
                        sort_keys=True,
                        separators=(",", ":"),
                    ),
                    "refusal": None,
                },
            }
        ],
        "usage": {
            "prompt_tokens": 13,
            "completion_tokens": 8,
            "total_tokens": 21,
        },
        "system_fingerprint": "fp-independent-live-executor-audit",
    }


class _SuccessOpener:
    def __init__(self, payloads: list[object]) -> None:
        self.payloads = list(payloads)
        self.request_bodies: list[dict[str, object]] = []
        self.calls = 0

    def __call__(self, request: object, *, timeout: float) -> _HTTP200:
        self.calls += 1
        if timeout != 30.0:
            raise AssertionError("unexpected offline timeout")
        raw = getattr(request, "data", None)
        if not isinstance(raw, bytes):
            raise AssertionError("request bytes absent")
        body = json.loads(raw.decode("utf-8"))
        if not isinstance(body, dict):
            raise AssertionError("request body is not an object")
        self.request_bodies.append(body)
        if not self.payloads:
            raise AssertionError("offline response script exhausted")
        return _HTTP200(_provider_response(self.payloads.pop(0), self.calls))


class _FaultOpener:
    def __init__(
        self,
        outcome: str,
        *,
        after_first: Callable[[], None] | None = None,
    ) -> None:
        self.outcome = outcome
        self.after_first = after_first
        self.calls = 0

    def __call__(self, *_args: object, **_kwargs: object) -> object:
        self.calls += 1
        if self.calls == 1 and self.after_first is not None:
            self.after_first()
        if self.outcome.startswith("http_"):
            status = int(self.outcome.split("_", 1)[1])
            raise HTTPError(
                "https://offline.invalid",
                status,
                "offline fault fixture",
                {},
                BytesIO(b"{}"),
            )
        if self.outcome == "timeout":
            raise TimeoutError("offline timeout fixture")
        if self.outcome == "connection":
            raise ConnectionResetError("offline connection fixture")
        raise AssertionError(f"unknown fault fixture: {self.outcome}")


def _integrity_state() -> R2RObservedIntegrityStateV1:
    return R2RObservedIntegrityStateV1(
        execution_commit="a" * 40,
        source_manifest_hash="1" * 64,
        source_blobs=(
            R2RSourceBlobIdentityV1("src/offline.py", "b" * 40, "2" * 64),
        ),
        authorization_hash="3" * 64,
        recovery_main_provider_schema_v2_hash=RECOVERY_MAIN_PROVIDER_SCHEMA_V2_HASH,
        main_prompt_hash=(
            "a251e4b9da31c33e72d14dd81da6b2b1d0d1437fdf37ca311330eccce226f1ba"
        ),
        t2_followup_prompt_hash=(
            "a633067a7c9927be158f68ce714236f4c18c09433d49c903dac941a9774eeca5"
        ),
        direct_number_prompt_hash=(
            "fb01d8990ee3a7affe540dfdf3556b46d7bd744cd1e3a04d6fd9d79772dd2769"
        ),
        direct_number_schema_hash=DIRECT_NUMBER_PROVIDER_SCHEMA_V1_HASH,
        exact_model="gpt-5.4-2026-03-05",
        endpoint="https://api.openai.com/v1/chat/completions",
        sampling_configuration_hash="4" * 64,
        timeout_seconds=30.0,
        retry_policy_hash="5" * 64,
        relation_schedule_hash=(
            "6db63485387924b28e9ce498aae46412a127ba69055a28e72880e1afffa4c4ca"
        ),
        scientific_concurrency=1,
        scientific_call_budget_hash="6" * 64,
        scientific_accounting_behavior_hash=(
            R2R_SCIENTIFIC_ACCOUNTING_BEHAVIOR_HASH_V1
        ),
        recovery_execution_configuration_hash="7" * 64,
    )


def _guard(
    state_box: dict[str, R2RObservedIntegrityStateV1] | None = None,
) -> tuple[R2RPostContactIntegrityGuardV1, list[int]]:
    baseline = _integrity_state()
    mutable = state_box if state_box is not None else {"state": baseline}
    checks: list[int] = []

    def load() -> R2RObservedIntegrityStateV1:
        checks.append(1)
        return mutable["state"]

    return (
        R2RPostContactIntegrityGuardV1(
            capture_r2r_integrity_snapshot_v1(baseline),
            load,
        ),
        checks,
    )


def _success_wrapper(
    payloads: list[object],
) -> tuple[
    R2RIntegrityGuardedTransportV1,
    R2RLiveOpenAIChatCompletionsTransportV1,
    _SuccessOpener,
    list[float],
    list[int],
]:
    opener = _SuccessOpener(payloads)
    sleeps: list[float] = []
    delegate = R2RLiveOpenAIChatCompletionsTransportV1(
        api_key="synthetic-offline-test-only",
        opener=opener,
        sleeper=sleeps.append,
    )
    guard, checks = _guard()
    wrapper = R2RIntegrityGuardedTransportV1(delegate, guard)
    return wrapper, delegate, opener, sleeps, checks


def _ledger(
    root: Path,
    wrapper: R2RIntegrityGuardedTransportV1,
) -> tuple[TransactionalScientificProviderLedgerV3, TransactionalHashChainCustodyV3]:
    custody = TransactionalHashChainCustodyV3(
        root,
        ledger_kind="scientific_provider",
        allowed_logical_call_kind="scientific",
    )
    ledger = TransactionalScientificProviderLedgerV3(
        custody,
        attempt_supplier=lambda: wrapper.attempt_custody,
    )
    return ledger, custody


def _schema_hash(request_body: dict[str, object]) -> str:
    response_format = request_body["response_format"]
    assert isinstance(response_format, dict)
    json_schema = response_format["json_schema"]
    assert isinstance(json_schema, dict)
    schema = json_schema["schema"]
    assert isinstance(schema, dict)
    return stable_hash_v1(schema)


class R2RLiveExecutorIndependentAuditSemanticsTests(unittest.TestCase):
    def test_t1_t1b_t2_and_direct_cross_real_delegate_contract(self) -> None:
        evidence = make_evidence(31)

        wrapper, delegate, opener, sleeps, checks = _success_wrapper(
            [valid_core_document(evidence)]
        )
        with tempfile.TemporaryDirectory() as temporary:
            ledger, custody = _ledger(Path(temporary), wrapper)
            result = R2R_ARM_RUNNERS_V1.t1(
                relation_schedule_index=0,
                evidence=evidence,
                transport=wrapper,
                call_ledger=ledger,
                proposal_ledger=ConstructionProposalLedgerV1(),
                outcome_ledger=ConstructionOutcomeLedgerV1(),
            )
            reconstructed = custody.reconstruct()
        self.assertEqual(result.generation_calls_consumed, 1)
        self.assertEqual((delegate.calls, opener.calls, len(checks)), (1, 1, 1))
        self.assertEqual(sleeps, [])
        self.assertEqual(_schema_hash(opener.request_bodies[0]), RECOVERY_MAIN_PROVIDER_SCHEMA_V2_HASH)
        self._assert_single_clean_science_record(reconstructed, expected_attempts=1)

        wrapper, delegate, opener, sleeps, checks = _success_wrapper(
            [valid_core_document(evidence) for _ in range(3)]
        )
        with tempfile.TemporaryDirectory() as temporary:
            ledger, custody = _ledger(Path(temporary), wrapper)
            result = R2R_ARM_RUNNERS_V1.t1b(
                relation_schedule_index=0,
                evidence=evidence,
                transport=wrapper,
                call_ledger=ledger,
                proposal_ledger=ConstructionProposalLedgerV1(),
                outcome_ledger=ConstructionOutcomeLedgerV1(),
            )
            reconstructed = custody.reconstruct()
        self.assertEqual(result.generation_calls_consumed, 3)
        self.assertEqual(result.accepted_call_index, 1)
        self.assertEqual((delegate.calls, opener.calls, len(checks)), (3, 3, 3))
        self.assertEqual(len(wrapper.request_hashes), 3)
        self.assertEqual(len(set(wrapper.request_hashes)), 1)
        self.assertEqual(wrapper.request_hashes, delegate.request_hashes)
        self.assertEqual(sleeps, [])
        self.assertEqual(reconstructed.authoritative_record_count, 3)
        self.assertTrue(all(
            _schema_hash(body) == RECOVERY_MAIN_PROVIDER_SCHEMA_V2_HASH
            for body in opener.request_bodies
        ))
        self._assert_clean_science_chain(reconstructed)

        wrapper, delegate, opener, sleeps, checks = _success_wrapper(
            [valid_core_document(evidence) for _ in range(3)]
        )
        with tempfile.TemporaryDirectory() as temporary:
            ledger, custody = _ledger(Path(temporary), wrapper)
            result = R2R_ARM_RUNNERS_V1.t2(
                relation_schedule_index=0,
                evidence=evidence,
                transport=wrapper,
                call_ledger=ledger,
                proposal_ledger=ConstructionProposalLedgerV1(),
                outcome_ledger=ConstructionOutcomeLedgerV1(),
                retrieval_identity=evidence.approved_evidence_identities[0],
                synthetic_validity_faults=(
                    "SYNTHETIC_REPAIRABLE_RETRIEVE",
                    "SYNTHETIC_REPAIRABLE_RETRIEVE",
                    "SYNTHETIC_REPAIRABLE_RETRIEVE",
                ),
            )
            reconstructed = custody.reconstruct()
        self.assertEqual(result.generation_calls_consumed, 3)
        self.assertEqual(result.retrieval_count, 1)
        self.assertLessEqual(result.revise_count, 2)
        self.assertEqual((delegate.calls, opener.calls, len(checks)), (3, 3, 3))
        self.assertEqual(sleeps, [])
        self.assertEqual(reconstructed.authoritative_record_count, 3)
        self.assertTrue(all(
            _schema_hash(body) == RECOVERY_MAIN_PROVIDER_SCHEMA_V2_HASH
            for body in opener.request_bodies
        ))
        self._assert_clean_science_chain(reconstructed)

        wrapper, delegate, opener, sleeps, checks = _success_wrapper(
            [direct_number_payload()]
        )
        with tempfile.TemporaryDirectory() as temporary:
            ledger, custody = _ledger(Path(temporary), wrapper)
            result = R2R_ARM_RUNNERS_V1.direct_number(
                relation_schedule_index=0,
                evidence=evidence,
                transport=wrapper,
                call_ledger=ledger,
            )
            reconstructed = custody.reconstruct()
        self.assertEqual(result.generation_calls_consumed, 1)
        self.assertEqual((delegate.calls, opener.calls, len(checks)), (1, 1, 1))
        self.assertEqual(sleeps, [])
        self.assertEqual(_schema_hash(opener.request_bodies[0]), DIRECT_NUMBER_PROVIDER_SCHEMA_V1_HASH)
        self._assert_single_clean_science_record(reconstructed, expected_attempts=1)

    def test_retry_ownership_is_slot_bounded_and_wrapper_is_one_to_one(self) -> None:
        evidence = make_evidence(32)
        request = build_r2r_main_request_v1(evidence.render_view())
        cases = (
            ("http_400", 1, []),
            ("http_429", 3, [2.0, 4.0]),
            ("http_503", 3, [2.0, 4.0]),
            ("timeout", 3, [2.0, 4.0]),
            ("connection", 3, [2.0, 4.0]),
        )
        for outcome, expected_attempts, expected_sleeps in cases:
            with self.subTest(outcome=outcome), tempfile.TemporaryDirectory() as temporary:
                opener = _FaultOpener(outcome)
                sleeps: list[float] = []
                delegate = R2RLiveOpenAIChatCompletionsTransportV1(
                    api_key="synthetic-offline-test-only",
                    opener=opener,
                    sleeper=sleeps.append,
                )
                guard, checks = _guard()
                wrapper = R2RIntegrityGuardedTransportV1(delegate, guard)
                ledger, custody = _ledger(Path(temporary), wrapper)
                with self.assertRaises(ScientificRunAbortV1):
                    execute_mock_provider_slot_v1(
                        slot=ProviderCallSlotV1(
                            0,
                            evidence.relation.binding_hash,
                            "T1",
                            1,
                            True,
                        ),
                        request=request,
                        transport=wrapper,
                        ledger=ledger,
                        parse_kind="proposal",
                    )
                reconstructed = custody.reconstruct()
                self.assertIsInstance(wrapper, MockProviderTransportV1)
                self.assertEqual(delegate.calls, expected_attempts)
                self.assertEqual(opener.calls, expected_attempts)
                self.assertEqual(len(checks), expected_attempts)
                self.assertEqual(len(delegate.attempt_custody), expected_attempts)
                self.assertEqual(wrapper.attempt_custody, delegate.attempt_custody)
                self.assertEqual(sleeps, expected_sleeps)
                self._assert_single_clean_science_record(
                    reconstructed,
                    expected_attempts=expected_attempts,
                )

        adapter_source = inspect.getsource(R2RIntegrityGuardedTransportV1.send)
        self.assertNotIn("sleep", adapter_source)
        self.assertNotIn("for ", adapter_source)
        self.assertNotIn("while ", adapter_source)
        self.assertEqual(adapter_source.count("self.transport.send(request)"), 1)

    def test_transactional_attempt_slice_is_exact_and_no_capability_slot_exists(self) -> None:
        evidence = make_evidence(33)
        wrapper, delegate, _opener, _sleeps, _checks = _success_wrapper(
            [valid_core_document(evidence) for _ in range(3)]
        )
        with tempfile.TemporaryDirectory() as temporary:
            ledger, custody = _ledger(Path(temporary), wrapper)
            R2R_ARM_RUNNERS_V1.t1b(
                relation_schedule_index=0,
                evidence=evidence,
                transport=wrapper,
                call_ledger=ledger,
                proposal_ledger=ConstructionProposalLedgerV1(),
                outcome_ledger=ConstructionOutcomeLedgerV1(),
            )
            reconstructed = custody.reconstruct()
        self.assertEqual(len(ledger.records), 3)
        self.assertEqual(len(delegate.attempt_custody), 3)
        self.assertEqual(wrapper.attempt_custody, delegate.attempt_custody)
        self.assertEqual(reconstructed.authoritative_record_count, 3)
        for sequence, record in enumerate(reconstructed.reachable_records):
            self.assertEqual(record["logical_call_kind"], "scientific")
            self.assertEqual(record["sequence_index"], sequence)
            payload = record["payload"]
            self.assertEqual(payload["logical_call_kind"], "scientific")
            self.assertTrue(payload["scientific"])
            self.assertEqual(len(payload["transport_attempts"]), 1)
            self.assertEqual(
                payload["transport_attempts"][0],
                delegate.attempt_custody[sequence].to_dict(),
            )
        self._assert_clean_science_chain(reconstructed)

    def test_integrity_drift_blocks_and_latches_before_second_delegate_send(self) -> None:
        evidence = make_evidence(34)
        baseline = _integrity_state()
        state_box = {"state": baseline}

        def mutate() -> None:
            state_box["state"] = replace(
                baseline,
                authorization_hash="8" * 64,
            )

        opener = _FaultOpener("http_429", after_first=mutate)
        sleeps: list[float] = []
        delegate = R2RLiveOpenAIChatCompletionsTransportV1(
            api_key="synthetic-offline-test-only",
            opener=opener,
            sleeper=sleeps.append,
        )
        guard, checks = _guard(state_box)
        wrapper = R2RIntegrityGuardedTransportV1(delegate, guard)
        with self.assertRaises(TASK039E3R2RPrecontactError):
            execute_mock_provider_slot_v1(
                slot=ProviderCallSlotV1(
                    0,
                    evidence.relation.binding_hash,
                    "T1",
                    1,
                    True,
                ),
                request=build_r2r_main_request_v1(evidence.render_view()),
                transport=wrapper,
                ledger=_RejectAppendLedger(),
                parse_kind="proposal",
            )
        self.assertTrue(guard.blocked)
        self.assertEqual((delegate.calls, opener.calls), (1, 1))
        self.assertEqual(len(delegate.attempt_custody), 1)
        self.assertEqual(len(checks), 2)
        self.assertEqual(sleeps, [])

        with self.assertRaises(TASK039E3R2RPrecontactError):
            wrapper.send(build_r2r_main_request_v1(evidence.render_view()))
        self.assertTrue(guard.blocked)
        self.assertEqual((delegate.calls, opener.calls), (1, 1))
        self.assertEqual(len(checks), 2)

    def _assert_single_clean_science_record(
        self,
        reconstructed: object,
        *,
        expected_attempts: int,
    ) -> None:
        self.assertEqual(reconstructed.authoritative_record_count, 1)
        record = reconstructed.reachable_records[0]
        self.assertEqual(record["logical_call_kind"], "scientific")
        self.assertEqual(record["payload"]["logical_call_kind"], "scientific")
        self.assertTrue(record["payload"]["scientific"])
        self.assertEqual(len(record["payload"]["transport_attempts"]), expected_attempts)
        self._assert_clean_science_chain(reconstructed)

    def _assert_clean_science_chain(self, reconstructed: object) -> None:
        self.assertFalse(reconstructed.orphan_record_hashes)
        self.assertFalse(reconstructed.pending_files)


class _RejectAppendLedger:
    """Proves the integrity guard fails before any slot commit is attempted."""

    records: tuple[object, ...] = ()
    ledger_hash = stable_hash_v1({"offline": "unreached-ledger"})

    def append(self, **_kwargs: object) -> None:
        raise AssertionError("integrity failure must precede ledger append")


if __name__ == "__main__":
    unittest.main()
