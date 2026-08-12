"""Offline regression oracles for the R2R live-executor adapter seam."""

from __future__ import annotations

from dataclasses import replace
from io import BytesIO
import json
from pathlib import Path
import tempfile
from typing import Callable
import unittest
from urllib.error import HTTPError

from paperworks.v6.common import stable_hash_v1
from paperworks.v6.task039e3_execution_prep_v1 import (
    MockProviderTransportV1,
    ProviderCallLedgerV1,
    ProviderCallSlotV1,
    ScientificRunAbortV1,
    execute_mock_provider_slot_v1,
)
from paperworks.v6.task039e3_orchestration_v1 import (
    ConstructionOutcomeLedgerV1,
    ConstructionProposalLedgerV1,
)
from paperworks.v6.task039e3_r2r_execution_v1 import (
    R2R_ARM_RUNNERS_V1,
    run_injected_r2r_scientific_cohort_v1,
)
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
from paperworks.v6.task039e3_recovery_science_v2 import ScientificLedgersV2
from paperworks.v6.task039e3_recovery_transactional_custody_v3 import (
    TransactionalHashChainCustodyV3,
)
from paperworks.v6.task039e3_recovery_execution_v3 import (
    TransactionalScientificProviderLedgerV3,
)
from task039e3_support import direct_number_payload, make_evidence, valid_core_document


class _HTTPResponse:
    status = 200
    headers: dict[str, str] = {}

    def __init__(self, document: object) -> None:
        self._raw = json.dumps(
            document,
            ensure_ascii=True,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")

    def __enter__(self) -> "_HTTPResponse":
        return self

    def __exit__(self, *_args: object) -> None:
        return None

    def read(self, _size: int = -1) -> bytes:
        return self._raw


def _provider_document(payload: object, sequence: int) -> dict[str, object]:
    return {
        "id": f"chatcmpl-offline-r2r-{sequence:04d}",
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
            "prompt_tokens": 11,
            "completion_tokens": 7,
            "total_tokens": 18,
        },
        "system_fingerprint": "fp-offline-r2r-remediation",
    }


class _ScriptedSuccessOpener:
    def __init__(self, payloads: list[object]) -> None:
        self._payloads = list(payloads)
        self.request_bodies: list[dict[str, object]] = []
        self.calls = 0

    @property
    def remaining(self) -> int:
        return len(self._payloads)

    def __call__(self, request: object, *, timeout: float) -> _HTTPResponse:
        if timeout != 30.0:
            raise AssertionError("offline transport timeout differs")
        data = getattr(request, "data", None)
        if not isinstance(data, bytes):
            raise AssertionError("outbound request bytes are absent")
        body = json.loads(data.decode("utf-8"))
        if not isinstance(body, dict):
            raise AssertionError("outbound request body is not an object")
        self.request_bodies.append(body)
        self.calls += 1
        if not self._payloads:
            raise AssertionError("offline provider script exhausted")
        payload = self._payloads.pop(0)
        return _HTTPResponse(_provider_document(payload, self.calls))


class _FaultOpener:
    def __init__(
        self,
        outcome: str,
        *,
        mutate_after_first_attempt: Callable[[], None] | None = None,
    ) -> None:
        self.outcome = outcome
        self.calls = 0
        self._mutate = mutate_after_first_attempt

    def __call__(self, *_args: object, **_kwargs: object) -> object:
        self.calls += 1
        if self.calls == 1 and self._mutate is not None:
            self._mutate()
        if self.outcome.startswith("http_"):
            status = int(self.outcome.split("_", 1)[1])
            raise HTTPError(
                "https://offline.invalid",
                status,
                "offline fixture",
                {},
                BytesIO(b"{}"),
            )
        if self.outcome == "timeout":
            raise TimeoutError("offline timeout fixture")
        if self.outcome == "connection_reset":
            raise ConnectionResetError("offline reset fixture")
        raise AssertionError("unknown offline fault")


class _DirectLedger:
    def __init__(self) -> None:
        self._records: list[object] = []

    @property
    def records(self) -> tuple[object, ...]:
        return tuple(self._records)

    def append(self, value: object) -> None:
        self._records.append(value)


def _integrity_state() -> R2RObservedIntegrityStateV1:
    return R2RObservedIntegrityStateV1(
        execution_commit="a" * 40,
        source_manifest_hash="1" * 64,
        source_blobs=(
            R2RSourceBlobIdentityV1("src/synthetic.py", "b" * 40, "2" * 64),
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
    observed: list[int] = []

    def load() -> R2RObservedIntegrityStateV1:
        observed.append(1)
        return mutable["state"]

    return (
        R2RPostContactIntegrityGuardV1(
            capture_r2r_integrity_snapshot_v1(baseline),
            load,
        ),
        observed,
    )


def _success_transport(
    payloads: list[object],
) -> tuple[
    R2RIntegrityGuardedTransportV1,
    R2RLiveOpenAIChatCompletionsTransportV1,
    _ScriptedSuccessOpener,
    list[float],
    list[int],
]:
    opener = _ScriptedSuccessOpener(payloads)
    delays: list[float] = []
    raw = R2RLiveOpenAIChatCompletionsTransportV1(
        api_key="synthetic-offline-only",
        opener=opener,
        sleeper=delays.append,
    )
    integrity, observations = _guard()
    return (
        R2RIntegrityGuardedTransportV1(raw, integrity),
        raw,
        opener,
        delays,
        observations,
    )


def _transactional_ledger(
    root: Path,
    transport: R2RIntegrityGuardedTransportV1,
) -> tuple[TransactionalScientificProviderLedgerV3, TransactionalHashChainCustodyV3]:
    custody = TransactionalHashChainCustodyV3(
        root,
        ledger_kind="scientific_provider",
        allowed_logical_call_kind="scientific",
    )
    return (
        TransactionalScientificProviderLedgerV3(
            custody,
            attempt_supplier=lambda: transport.attempt_custody,
        ),
        custody,
    )


def _provider_schema_hash(body: dict[str, object]) -> str:
    response_format = body["response_format"]
    assert isinstance(response_format, dict)
    json_schema = response_format["json_schema"]
    assert isinstance(json_schema, dict)
    schema = json_schema["schema"]
    assert isinstance(schema, dict)
    return stable_hash_v1(schema)


class R2RLiveExecutorRemediationTests(unittest.TestCase):
    def test_first_t1_crosses_former_mock_only_boundary_and_commits_once(self) -> None:
        evidence = make_evidence(1)
        guarded, raw, opener, delays, checks = _success_transport(
            [valid_core_document(evidence)]
        )
        self.assertIsInstance(guarded, MockProviderTransportV1)
        proposals = ConstructionProposalLedgerV1()
        outcomes = ConstructionOutcomeLedgerV1()
        R2R_ARM_RUNNERS_V1.t0(
            evidence=evidence,
            proposal_ledger=proposals,
            outcome_ledger=outcomes,
        )
        with tempfile.TemporaryDirectory() as temporary:
            ledger, custody = _transactional_ledger(Path(temporary), guarded)
            result = R2R_ARM_RUNNERS_V1.t1(
                relation_schedule_index=0,
                evidence=evidence,
                transport=guarded,
                call_ledger=ledger,
                proposal_ledger=proposals,
                outcome_ledger=outcomes,
            )
            reconstructed = custody.reconstruct()
        self.assertEqual(result.outcome, "accepted_proposal")
        self.assertEqual(raw.calls, 1)
        self.assertEqual(guarded.calls, raw.calls)
        self.assertEqual(guarded.request_hashes, raw.request_hashes)
        self.assertEqual(guarded.attempt_custody, raw.attempt_custody)
        self.assertEqual((opener.calls, delays, len(checks)), (1, [], 1))
        self.assertEqual(_provider_schema_hash(opener.request_bodies[0]), RECOVERY_MAIN_PROVIDER_SCHEMA_V2_HASH)
        self.assertEqual(reconstructed.authoritative_record_count, 1)
        self.assertFalse(reconstructed.orphan_record_hashes)
        self.assertFalse(reconstructed.pending_files)
        self.assertTrue(all(record.slot.scientific for record in ledger.records))

    def test_t1b_delegates_three_identical_request_hashes(self) -> None:
        evidence = make_evidence(2)
        guarded, raw, opener, delays, checks = _success_transport(
            [valid_core_document(evidence) for _ in range(3)]
        )
        with tempfile.TemporaryDirectory() as temporary:
            ledger, custody = _transactional_ledger(Path(temporary), guarded)
            result = R2R_ARM_RUNNERS_V1.t1b(
                relation_schedule_index=0,
                evidence=evidence,
                transport=guarded,
                call_ledger=ledger,
                proposal_ledger=ConstructionProposalLedgerV1(),
                outcome_ledger=ConstructionOutcomeLedgerV1(),
            )
            reconstructed = custody.reconstruct()
        self.assertEqual(result.generation_calls_consumed, 3)
        self.assertEqual(result.accepted_call_index, 1)
        self.assertEqual(len(set(guarded.request_hashes)), 1)
        self.assertEqual((raw.calls, opener.calls, len(checks)), (3, 3, 3))
        self.assertEqual(delays, [])
        self.assertTrue(all(
            _provider_schema_hash(body) == RECOVERY_MAIN_PROVIDER_SCHEMA_V2_HASH
            for body in opener.request_bodies
        ))
        self.assertEqual(reconstructed.authoritative_record_count, 3)

    def test_t2_v2_followups_stop_at_three_and_retrieve_at_most_once(self) -> None:
        evidence = make_evidence(3)
        guarded, raw, opener, delays, checks = _success_transport(
            [valid_core_document(evidence) for _ in range(3)]
        )
        with tempfile.TemporaryDirectory() as temporary:
            ledger, custody = _transactional_ledger(Path(temporary), guarded)
            result = R2R_ARM_RUNNERS_V1.t2(
                relation_schedule_index=0,
                evidence=evidence,
                transport=guarded,
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
        self.assertEqual(result.outcome, "no_rule")
        self.assertEqual(result.generation_calls_consumed, 3)
        self.assertEqual(result.retrieval_count, 1)
        self.assertLessEqual(result.revise_count, 2)
        self.assertEqual((raw.calls, opener.calls, len(checks)), (3, 3, 3))
        self.assertEqual(delays, [])
        self.assertTrue(all(
            _provider_schema_hash(body) == RECOVERY_MAIN_PROVIDER_SCHEMA_V2_HASH
            for body in opener.request_bodies
        ))
        self.assertNotEqual(guarded.request_hashes[0], guarded.request_hashes[1])
        self.assertEqual(reconstructed.authoritative_record_count, 3)

    def test_direct_number_uses_unchanged_v1_through_same_wrapper(self) -> None:
        evidence = make_evidence(4)
        guarded, raw, opener, delays, checks = _success_transport(
            [direct_number_payload()]
        )
        with tempfile.TemporaryDirectory() as temporary:
            ledger, custody = _transactional_ledger(Path(temporary), guarded)
            result = R2R_ARM_RUNNERS_V1.direct_number(
                relation_schedule_index=0,
                evidence=evidence,
                transport=guarded,
                call_ledger=ledger,
            )
            reconstructed = custody.reconstruct()
        self.assertEqual(result.generation_calls_consumed, 1)
        self.assertEqual((raw.calls, opener.calls, len(checks)), (1, 1, 1))
        self.assertEqual(delays, [])
        self.assertEqual(
            _provider_schema_hash(opener.request_bodies[0]),
            DIRECT_NUMBER_PROVIDER_SCHEMA_V1_HASH,
        )
        self.assertEqual(reconstructed.authoritative_record_count, 1)

    def test_retry_controller_remains_slot_owned_and_adapter_is_one_to_one(self) -> None:
        evidence = make_evidence(5)
        request = build_r2r_main_request_v1(evidence.render_view())
        cases = (
            ("http_400", 1, []),
            ("http_429", 3, [2.0, 4.0]),
            ("http_503", 3, [2.0, 4.0]),
            ("timeout", 3, [2.0, 4.0]),
            ("connection_reset", 3, [2.0, 4.0]),
        )
        for outcome, expected_calls, expected_delays in cases:
            with self.subTest(outcome=outcome):
                opener = _FaultOpener(outcome)
                delays: list[float] = []
                raw = R2RLiveOpenAIChatCompletionsTransportV1(
                    api_key="synthetic-offline-only",
                    opener=opener,
                    sleeper=delays.append,
                )
                integrity, checks = _guard()
                guarded = R2RIntegrityGuardedTransportV1(raw, integrity)
                ledger = ProviderCallLedgerV1()
                with self.assertRaises(ScientificRunAbortV1):
                    execute_mock_provider_slot_v1(
                        slot=ProviderCallSlotV1(
                            0, evidence.relation.binding_hash, "T1", 1, True
                        ),
                        request=request,
                        transport=guarded,
                        ledger=ledger,
                        parse_kind="proposal",
                    )
                self.assertEqual(raw.calls, expected_calls)
                self.assertEqual(opener.calls, expected_calls)
                self.assertEqual(len(checks), expected_calls)
                self.assertEqual(len(raw.attempt_custody), expected_calls)
                self.assertEqual(delays, expected_delays)
                self.assertEqual(len(ledger.records), 1)
                self.assertEqual(
                    len(ledger.records[0].transport_attempts), expected_calls
                )

    def test_integrity_drift_blocks_retry_before_delegate_or_sleep(self) -> None:
        evidence = make_evidence(6)
        baseline = _integrity_state()
        state_box = {"state": baseline}

        def mutate() -> None:
            state_box["state"] = replace(
                baseline,
                authorization_hash="8" * 64,
            )

        opener = _FaultOpener("http_429", mutate_after_first_attempt=mutate)
        delays: list[float] = []
        raw = R2RLiveOpenAIChatCompletionsTransportV1(
            api_key="synthetic-offline-only",
            opener=opener,
            sleeper=delays.append,
        )
        integrity, checks = _guard(state_box)
        guarded = R2RIntegrityGuardedTransportV1(raw, integrity)
        with self.assertRaises(TASK039E3R2RPrecontactError):
            execute_mock_provider_slot_v1(
                slot=ProviderCallSlotV1(
                    0, evidence.relation.binding_hash, "T1", 1, True
                ),
                request=build_r2r_main_request_v1(evidence.render_view()),
                transport=guarded,
                ledger=ProviderCallLedgerV1(),
                parse_kind="proposal",
            )
        self.assertTrue(integrity.blocked)
        self.assertEqual((raw.calls, opener.calls), (1, 1))
        self.assertEqual(len(raw.attempt_custody), 1)
        self.assertEqual(len(checks), 2)
        self.assertEqual(delays, [])

    def test_full_42_relation_offline_cohort_crosses_exact_adapter(self) -> None:
        evidence_records = tuple(make_evidence(index) for index in range(1, 43))
        payloads: list[object] = []
        for evidence in evidence_records:
            payloads.extend(valid_core_document(evidence) for _ in range(5))
            payloads.append(direct_number_payload())
        guarded, raw, opener, delays, checks = _success_transport(payloads)
        proposal = ConstructionProposalLedgerV1()
        outcome = ConstructionOutcomeLedgerV1()
        direct = _DirectLedger()
        with tempfile.TemporaryDirectory() as temporary:
            provider, custody = _transactional_ledger(Path(temporary), guarded)
            result = run_injected_r2r_scientific_cohort_v1(
                relation_identities=tuple(
                    item.relation.relation_identity for item in evidence_records
                ),
                evidence_records=evidence_records,
                transport=guarded,
                ledgers=ScientificLedgersV2(provider, proposal, outcome, direct),
                progress=lambda _message: None,
            )
            reconstructed = custody.reconstruct()
        self.assertEqual(result.relation_count, 42)
        self.assertEqual(result.t0_outcomes, 42)
        self.assertEqual(result.t1_logical_calls, 42)
        self.assertEqual(result.t1b_logical_calls, 126)
        self.assertEqual(result.t2_logical_calls, 42)
        self.assertEqual(result.direct_number_logical_calls, 42)
        self.assertEqual(result.scientific_logical_calls, 252)
        self.assertEqual((raw.calls, opener.calls, len(checks)), (252, 252, 252))
        self.assertEqual(len(guarded.request_hashes), 252)
        self.assertEqual(len(guarded.attempt_custody), 252)
        self.assertEqual(opener.remaining, 0)
        self.assertEqual(delays, [])
        self.assertEqual(reconstructed.authoritative_record_count, 252)
        self.assertFalse(reconstructed.orphan_record_hashes)
        self.assertFalse(reconstructed.pending_files)
        self.assertEqual(len(outcome.records), 168)
        self.assertEqual(len(direct.records), 42)
        self.assertEqual(
            sum(record.slot.arm == "T1-B" for record in provider.records),
            126,
        )
        for offset in range(0, 252, 6):
            self.assertTrue(all(
                _provider_schema_hash(body) == RECOVERY_MAIN_PROVIDER_SCHEMA_V2_HASH
                for body in opener.request_bodies[offset : offset + 5]
            ))
            self.assertEqual(
                _provider_schema_hash(opener.request_bodies[offset + 5]),
                DIRECT_NUMBER_PROVIDER_SCHEMA_V1_HASH,
            )
        self.assertTrue(all(record.slot.scientific for record in provider.records))


if __name__ == "__main__":
    unittest.main()
