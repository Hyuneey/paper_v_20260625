"""Independent offline oracles for the remediated R2R adapter interface."""

from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Any, Callable
import unittest
from unittest.mock import patch

from paperworks.v6.task039e3_execution_prep_v1 import (
    MockProviderTransportV1,
    ProviderCallLedgerV1,
    ProviderCallSlotV1,
    TASK039E3PreparationError,
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
    capture_r2r_integrity_snapshot_v1,
)
from paperworks.v6.task039e3_r2r_request_contract_v1 import (
    DIRECT_NUMBER_PROVIDER_SCHEMA_V1_HASH,
    RECOVERY_MAIN_PROVIDER_SCHEMA_V2_HASH,
    build_r2r_main_request_v1,
)
from task039e3_support import make_evidence, valid_core_document


class _OfflineHTTPResponse:
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

    def __enter__(self) -> "_OfflineHTTPResponse":
        return self

    def __exit__(self, *_args: object) -> None:
        return None

    def read(self, _size: int = -1) -> bytes:
        return self._raw


class _NeverNetworkOpener:
    """In-memory URL-opener seam with no socket or network capability."""

    def __init__(self, payload: object, order: list[str]) -> None:
        self._payload = payload
        self._order = order
        self.calls = 0

    def __call__(self, request: object, *, timeout: float) -> _OfflineHTTPResponse:
        if timeout != 30.0:
            raise AssertionError("frozen timeout differs")
        if not isinstance(getattr(request, "data", None), bytes):
            raise AssertionError("frozen outbound request bytes are absent")
        self.calls += 1
        self._order.append("delegate_send")
        document = {
            "id": "chatcmpl-independent-interface-offline",
            "model": "gpt-5.4-2026-03-05",
            "choices": [
                {
                    "finish_reason": "stop",
                    "message": {
                        "content": json.dumps(
                            self._payload,
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
            "system_fingerprint": "fp-independent-interface-offline",
        }
        return _OfflineHTTPResponse(document)


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
        scientific_accounting_behavior_hash=R2R_SCIENTIFIC_ACCOUNTING_BEHAVIOR_HASH_V1,
        recovery_execution_configuration_hash="7" * 64,
    )


def _guard(order: list[str]) -> tuple[R2RPostContactIntegrityGuardV1, list[int]]:
    state = _integrity_state()
    observations: list[int] = []

    def load() -> R2RObservedIntegrityStateV1:
        observations.append(1)
        order.append("integrity_guard")
        return state

    return (
        R2RPostContactIntegrityGuardV1(
            capture_r2r_integrity_snapshot_v1(state),
            load,
        ),
        observations,
    )


@dataclass(frozen=True)
class _HistoricalStructuralPattern:
    """Local oracle for the old non-MockProviderTransportV1 wrapper shape."""

    transport: Any
    integrity_guard: Any

    @property
    def calls(self) -> int:
        return self.transport.calls

    @property
    def request_hashes(self) -> tuple[str, ...]:
        return self.transport.request_hashes

    @property
    def attempt_custody(self) -> tuple[Any, ...]:
        return self.transport.attempt_custody

    def send(self, request: Any) -> Any:
        return self.integrity_guard.invoke_guarded_provider_attempt(
            lambda: self.transport.send(request)
        )


class _ProjectionDelegate:
    def __init__(self) -> None:
        self.calls = object()
        self.request_hashes = object()
        self.attempt_custody = object()
        self.send_calls = 0

    def send(self, request: object) -> object:
        self.send_calls += 1
        return request


class _ProjectionGuard:
    def __init__(self) -> None:
        self.calls = 0

    def invoke_guarded_provider_attempt(self, attempt: Callable[[], Any]) -> Any:
        self.calls += 1
        return attempt()


class R2RLiveExecutorIndependentAuditInterfaceTests(unittest.TestCase):
    def test_wrapper_is_compatibility_type_without_mock_script_initialization(self) -> None:
        delegate = _ProjectionDelegate()
        guard = _ProjectionGuard()
        with patch.object(
            MockProviderTransportV1,
            "__init__",
            side_effect=AssertionError("mock initializer must remain unused"),
        ):
            wrapper = R2RIntegrityGuardedTransportV1(delegate, guard)

        self.assertIsInstance(wrapper, MockProviderTransportV1)
        self.assertNotIn("_events", wrapper.__dict__)
        self.assertNotIn("_cursor", wrapper.__dict__)
        self.assertNotIn("_request_hashes", wrapper.__dict__)
        self.assertEqual(set(wrapper.__dict__), {"transport", "integrity_guard"})

    def test_properties_are_exact_projections_and_send_is_one_guarded_delegate_call(self) -> None:
        delegate = _ProjectionDelegate()
        guard = _ProjectionGuard()
        wrapper = R2RIntegrityGuardedTransportV1(delegate, guard)

        self.assertIs(wrapper.calls, delegate.calls)
        self.assertIs(wrapper.request_hashes, delegate.request_hashes)
        self.assertIs(wrapper.attempt_custody, delegate.attempt_custody)
        request = object()
        self.assertIs(wrapper.send(request), request)
        self.assertEqual((guard.calls, delegate.send_calls), (1, 1))

    def test_exact_first_t1_boundary_accepts_real_live_delegate_offline(self) -> None:
        evidence = make_evidence(1)
        proposals = ConstructionProposalLedgerV1()
        outcomes = ConstructionOutcomeLedgerV1()
        t0 = R2R_ARM_RUNNERS_V1.t0(
            evidence=evidence,
            proposal_ledger=proposals,
            outcome_ledger=outcomes,
        )
        self.assertEqual((len(proposals.records), len(outcomes.records)), (1, 1))
        self.assertEqual(t0.outcome, "accepted_proposal")

        request = build_r2r_main_request_v1(evidence.render_view())
        slot = ProviderCallSlotV1(
            0,
            evidence.relation.binding_hash,
            "T1",
            1,
            True,
        )
        order: list[str] = []
        opener = _NeverNetworkOpener(valid_core_document(evidence), order)
        raw = R2RLiveOpenAIChatCompletionsTransportV1(
            api_key="synthetic-offline-only",
            opener=opener,
            sleeper=lambda _delay: self.fail("success path must not sleep"),
        )
        integrity, observations = _guard(order)
        wrapper = R2RIntegrityGuardedTransportV1(raw, integrity)
        ledger = ProviderCallLedgerV1()

        result = execute_mock_provider_slot_v1(
            slot=slot,
            request=request,
            transport=wrapper,
            ledger=ledger,
            parse_kind="proposal",
        )

        self.assertEqual(result.record.slot.slot_hash, slot.slot_hash)
        self.assertEqual(order, ["integrity_guard", "delegate_send"])
        self.assertEqual((len(observations), opener.calls, raw.calls), (1, 1, 1))
        self.assertEqual(wrapper.calls, raw.calls)
        self.assertEqual(wrapper.request_hashes, raw.request_hashes)
        self.assertEqual(wrapper.attempt_custody, raw.attempt_custody)
        self.assertEqual(wrapper.request_hashes, (request.request_hash,))
        self.assertEqual(len(wrapper.attempt_custody), 1)
        self.assertEqual(len(ledger.records), 1)
        self.assertNotIn("_events", raw.__dict__)
        self.assertNotIn("_cursor", raw.__dict__)
        self.assertIs(raw._raw_opener, opener)

    def test_old_noncompatibility_shape_fails_before_guard_or_delegate(self) -> None:
        evidence = make_evidence(2)
        request = build_r2r_main_request_v1(evidence.render_view())
        slot = ProviderCallSlotV1(
            0,
            evidence.relation.binding_hash,
            "T1",
            1,
            True,
        )
        order: list[str] = []
        opener = _NeverNetworkOpener(valid_core_document(evidence), order)
        raw = R2RLiveOpenAIChatCompletionsTransportV1(
            api_key="synthetic-offline-only",
            opener=opener,
            sleeper=lambda _delay: self.fail("rejected boundary must not sleep"),
        )
        integrity, observations = _guard(order)
        old_wrapper = _HistoricalStructuralPattern(raw, integrity)

        with self.assertRaisesRegex(
            TASK039E3PreparationError,
            "TASK-039E3-PREP accepts MockProviderTransportV1 only",
        ):
            execute_mock_provider_slot_v1(
                slot=slot,
                request=request,
                transport=old_wrapper,  # type: ignore[arg-type]
                ledger=ProviderCallLedgerV1(),
                parse_kind="proposal",
            )

        self.assertEqual(order, [])
        self.assertEqual((len(observations), opener.calls, raw.calls), (0, 0, 0))


if __name__ == "__main__":
    unittest.main()
