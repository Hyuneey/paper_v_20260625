from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace
import unittest

from paperworks.v6 import task039e3_recovery_science_v2 as science
from paperworks.v6.task039e3_orchestration_v1 import (
    run_direct_number_v1,
    run_t1_v1,
    run_t1b_v1,
    run_t2_v1,
)
from paperworks.v6.task039e3_scientific_execution_v1 import run_real_t0_v1


_HASH = "a" * 64


@dataclass(frozen=True)
class _Slot:
    arm: str
    scientific: bool = True


@dataclass(frozen=True)
class _ProviderRecord:
    slot: _Slot


@dataclass(frozen=True)
class _Outcome:
    arm: str


class _Ledger:
    def __init__(self) -> None:
        self.records: list[object] = []

    def append(self, value: object) -> None:
        self.records.append(value)


class _OutcomeLedger(_Ledger):
    def __init__(self) -> None:
        super().__init__()
        self.asserted_schedule: tuple[str, ...] | None = None

    def assert_complete_future_cohort(self, schedule: tuple[str, ...]) -> None:
        self.asserted_schedule = tuple(schedule)


class _Evidence:
    def __init__(self, identity: str) -> None:
        self.relation = SimpleNamespace(
            relation_identity=identity,
            binding_hash=(identity.encode("utf-8").hex() + "0" * 64)[:64],
        )
        self.approved_evidence_identities = (f"evidence:{identity}",)


class _FrozenRunnerFakes:
    def __init__(self, *, t2_calls: int = 1, fail_with: Exception | None = None) -> None:
        self.t2_calls = t2_calls
        self.fail_with = fail_with

    def t0(self, *, evidence, proposal_ledger, outcome_ledger) -> None:
        outcome_ledger.append(_Outcome("T0"))

    def t1(
        self,
        *,
        relation_schedule_index,
        evidence,
        transport,
        call_ledger,
        proposal_ledger,
        outcome_ledger,
    ) -> None:
        if self.fail_with is not None:
            raise self.fail_with
        call_ledger.append(_ProviderRecord(_Slot("T1")))
        outcome_ledger.append(_Outcome("T1"))

    def t1b(
        self,
        *,
        relation_schedule_index,
        evidence,
        transport,
        call_ledger,
        proposal_ledger,
        outcome_ledger,
    ) -> None:
        for _ in range(3):
            call_ledger.append(_ProviderRecord(_Slot("T1-B")))
        outcome_ledger.append(_Outcome("T1-B"))

    def t2(
        self,
        *,
        relation_schedule_index,
        evidence,
        transport,
        call_ledger,
        proposal_ledger,
        outcome_ledger,
        retrieval_identity,
    ) -> None:
        self.testcase.assertEqual(
            retrieval_identity, evidence.approved_evidence_identities[0]
        )
        for _ in range(self.t2_calls):
            call_ledger.append(_ProviderRecord(_Slot("T2")))
        outcome_ledger.append(_Outcome("T2"))

    def direct_number(
        self, *, relation_schedule_index, evidence, transport, call_ledger
    ) -> object:
        call_ledger.append(_ProviderRecord(_Slot("T1-DIRECT-NUMBER")))
        return SimpleNamespace(relation_identity=evidence.relation.relation_identity)

    def bind(self, testcase: unittest.TestCase) -> science._FrozenArmRunnersV2:
        self.testcase = testcase
        return science._FrozenArmRunnersV2(
            t0=self.t0,
            t1=self.t1,
            t1b=self.t1b,
            t2=self.t2,
            direct_number=self.direct_number,
        )


class _DurableModelMismatch(RuntimeError):
    pass


class RecoveryScienceV2Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.schedule = tuple(f"relation-{index:02d}" for index in range(42))
        self.evidence = tuple(_Evidence(identity) for identity in self.schedule)
        self.authority = science.PostCapabilityAuthorityV2(
            gate_status="PASS",
            capability_custody_frozen=True,
            capability_receipt_durable=True,
            capability_receipt_hash=_HASH,
        )

    def _ledgers(self) -> science.ScientificLedgersV2:
        return science.ScientificLedgersV2(
            provider=_Ledger(),
            proposal=_Ledger(),
            outcome=_OutcomeLedger(),
            direct_number=_Ledger(),
        )

    def _run(
        self,
        *,
        authority: science.PostCapabilityAuthorityV2 | None = None,
        ledgers: science.ScientificLedgersV2 | None = None,
        fakes: _FrozenRunnerFakes | None = None,
        loader=None,
    ):
        selected_fakes = fakes or _FrozenRunnerFakes()
        return science._run_post_capability_scientific_execution_v2(
            authority=authority or self.authority,
            relation_identities=self.schedule,
            evidence_loader=loader or (lambda schedule: self.evidence),
            transport=object(),
            ledgers=ledgers or self._ledgers(),
            runners=selected_fakes.bind(self),
            progress=lambda message: None,
        )

    def test_capability_block_prevents_e1_loader(self) -> None:
        called = False

        def loader(schedule):
            nonlocal called
            called = True
            return self.evidence

        blocked = science.PostCapabilityAuthorityV2(
            gate_status="BLOCK",
            capability_custody_frozen=True,
            capability_receipt_durable=True,
            capability_receipt_hash=_HASH,
        )
        with self.assertRaisesRegex(science.TASK039E3RecoveryScienceV2Error, "PASS"):
            self._run(authority=blocked, loader=loader)
        self.assertFalse(called)

    def test_pass_without_frozen_custody_prevents_e1_loader(self) -> None:
        called = False

        def loader(schedule):
            nonlocal called
            called = True
            return self.evidence

        incomplete = science.PostCapabilityAuthorityV2(
            gate_status="PASS",
            capability_custody_frozen=False,
            capability_receipt_durable=True,
            capability_receipt_hash=_HASH,
        )
        with self.assertRaisesRegex(science.TASK039E3RecoveryScienceV2Error, "custody"):
            self._run(authority=incomplete, loader=loader)
        self.assertFalse(called)

    def test_pass_without_durable_receipt_prevents_e1_loader(self) -> None:
        called = False

        def loader(schedule):
            nonlocal called
            called = True
            return self.evidence

        incomplete = science.PostCapabilityAuthorityV2(
            gate_status="PASS",
            capability_custody_frozen=True,
            capability_receipt_durable=False,
            capability_receipt_hash=_HASH,
        )
        with self.assertRaisesRegex(science.TASK039E3RecoveryScienceV2Error, "receipt"):
            self._run(authority=incomplete, loader=loader)
        self.assertFalse(called)

    def test_minimum_schedule_is_science_only_and_has_no_local_slot(self) -> None:
        ledgers = self._ledgers()
        result = self._run(ledgers=ledgers)
        self.assertEqual(result.scientific_logical_calls, 252)
        self.assertEqual(result.t1_logical_calls, 42)
        self.assertEqual(result.t1b_logical_calls, 126)
        self.assertEqual(result.t2_logical_calls, 42)
        self.assertEqual(result.direct_number_logical_calls, 42)
        self.assertEqual(result.local_compatibility_slots, 0)
        self.assertTrue(all(record.slot.scientific for record in ledgers.provider.records))
        self.assertEqual(len(ledgers.outcome.records), 168)
        self.assertEqual(len(ledgers.direct_number.records), 42)
        self.assertEqual(ledgers.outcome.asserted_schedule, self.schedule)

    def test_maximum_t2_budget_preserves_upper_call_bound(self) -> None:
        result = self._run(fakes=_FrozenRunnerFakes(t2_calls=3))
        self.assertEqual(result.t2_logical_calls, 126)
        self.assertEqual(result.scientific_logical_calls, 336)

    def test_provider_ledger_must_begin_empty(self) -> None:
        ledgers = self._ledgers()
        ledgers.provider.append(_ProviderRecord(_Slot("T1")))
        called = False

        def loader(schedule):
            nonlocal called
            called = True
            return self.evidence

        with self.assertRaisesRegex(science.TASK039E3RecoveryScienceV2Error, "begin empty"):
            self._run(ledgers=ledgers, loader=loader)
        self.assertFalse(called)

    def test_evidence_projection_must_match_frozen_order(self) -> None:
        with self.assertRaisesRegex(science.TASK039E3RecoveryScienceV2Error, "order"):
            self._run(loader=lambda schedule: tuple(reversed(self.evidence)))

    def test_frozen_arm_functions_are_reused_by_identity(self) -> None:
        self.assertIs(science.FROZEN_ARM_RUNNERS_V2.t0, run_real_t0_v1)
        self.assertIs(science.FROZEN_ARM_RUNNERS_V2.t1, run_t1_v1)
        self.assertIs(science.FROZEN_ARM_RUNNERS_V2.t1b, run_t1b_v1)
        self.assertIs(science.FROZEN_ARM_RUNNERS_V2.t2, run_t2_v1)
        self.assertIs(science.FROZEN_ARM_RUNNERS_V2.direct_number, run_direct_number_v1)

    def test_dedicated_custody_model_mismatch_exception_propagates(self) -> None:
        mismatch = _DurableModelMismatch("completed_model_identity_mismatch")
        with self.assertRaises(_DurableModelMismatch) as caught:
            self._run(fakes=_FrozenRunnerFakes(fail_with=mismatch))
        self.assertIs(caught.exception, mismatch)

    def test_active_module_has_no_legacy_bridge_or_capability_payload(self) -> None:
        source = Path(science.__file__).read_text(encoding="utf-8")
        forbidden_bridge = "Recovery" + "ScientificCompatibilityTransportV1"
        legacy_snapshot_field = "model_" + "snapshot"
        legacy_support_field = "structured_output_" + "supported"
        self.assertNotIn(forbidden_bridge, source)
        self.assertNotIn(legacy_snapshot_field, source)
        self.assertNotIn(legacy_support_field, source)
        self.assertNotIn("task039e3_recovery_execution_v1", source)


if __name__ == "__main__":
    unittest.main()
