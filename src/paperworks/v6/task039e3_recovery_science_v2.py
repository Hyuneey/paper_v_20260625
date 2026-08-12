"""Post-capability TASK-039E3 recovery scientific orchestration.

This additive coordinator starts only after the corrected recovery capability
gate has passed and its custody is durable.  It deliberately has no capability
probe path: the provider ledger supplied here is a new, science-only ledger and
the frozen arm implementations are invoked directly.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from paperworks.v6.task039e3_orchestration_v1 import (
    run_direct_number_v1,
    run_t1_v1,
    run_t1b_v1,
    run_t2_v1,
)
from paperworks.v6.task039e3_scientific_execution_v1 import (
    PRIVATE_LEDGER_FILE,
    load_real_evidence_schedule_v1,
    run_real_t0_v1,
)


RELATION_COUNT = 42
MINIMUM_SCIENTIFIC_LOGICAL_CALLS = 252
MAXIMUM_SCIENTIFIC_LOGICAL_CALLS = 336
SCIENTIFIC_CONCURRENCY = 1
SCIENTIFIC_GENERATION_RETRIES = 0
LOCAL_COMPATIBILITY_SLOTS = 0

_SCIENTIFIC_ARMS = ("T1", "T1-B", "T2", "T1-DIRECT-NUMBER")


class TASK039E3RecoveryScienceV2Error(RuntimeError):
    """Raised when a post-capability recovery-science invariant differs."""


def _require_hash(value: str, name: str) -> None:
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise TASK039E3RecoveryScienceV2Error(f"{name} must be a lowercase SHA-256")


@dataclass(frozen=True)
class PostCapabilityAuthorityV2:
    """Durable handoff from the corrected capability stage."""

    gate_status: str
    capability_custody_frozen: bool
    capability_receipt_durable: bool
    capability_receipt_hash: str

    def validate(self) -> None:
        if self.gate_status != "PASS":
            raise TASK039E3RecoveryScienceV2Error(
                "post-capability science requires corrected capability PASS"
            )
        if self.capability_custody_frozen is not True:
            raise TASK039E3RecoveryScienceV2Error(
                "post-capability science requires frozen capability custody"
            )
        if self.capability_receipt_durable is not True:
            raise TASK039E3RecoveryScienceV2Error(
                "post-capability science requires durable capability receipt"
            )
        _require_hash(self.capability_receipt_hash, "capability receipt hash")


@dataclass(frozen=True)
class ScientificLedgersV2:
    """Separate construction ledgers; the provider ledger is science-only."""

    provider: Any
    proposal: Any
    outcome: Any
    direct_number: Any


@dataclass(frozen=True)
class PostCapabilityScientificResultV2:
    relation_count: int
    t0_outcomes: int
    t1_logical_calls: int
    t1b_logical_calls: int
    t2_logical_calls: int
    direct_number_logical_calls: int
    scientific_logical_calls: int
    scientific_concurrency: int = SCIENTIFIC_CONCURRENCY
    scientific_generation_retries: int = SCIENTIFIC_GENERATION_RETRIES
    local_compatibility_slots: int = LOCAL_COMPATIBILITY_SLOTS

    def to_dict(self) -> dict[str, int]:
        return {
            "relation_count": self.relation_count,
            "t0_outcomes": self.t0_outcomes,
            "t1_logical_calls": self.t1_logical_calls,
            "t1b_logical_calls": self.t1b_logical_calls,
            "t2_logical_calls": self.t2_logical_calls,
            "direct_number_logical_calls": self.direct_number_logical_calls,
            "scientific_logical_calls": self.scientific_logical_calls,
            "scientific_concurrency": self.scientific_concurrency,
            "scientific_generation_retries": self.scientific_generation_retries,
            "local_compatibility_slots": self.local_compatibility_slots,
        }


@dataclass(frozen=True)
class _FrozenArmRunnersV2:
    t0: Callable[..., Any] = run_real_t0_v1
    t1: Callable[..., Any] = run_t1_v1
    t1b: Callable[..., Any] = run_t1b_v1
    t2: Callable[..., Any] = run_t2_v1
    direct_number: Callable[..., Any] = run_direct_number_v1


FROZEN_ARM_RUNNERS_V2 = _FrozenArmRunnersV2()


def _records(ledger: Any, name: str) -> Sequence[Any]:
    records = getattr(ledger, "records", None)
    if not isinstance(records, (list, tuple)):
        raise TASK039E3RecoveryScienceV2Error(f"{name} ledger records are unavailable")
    return records


def _relation_identity(evidence: Any) -> str:
    relation = getattr(evidence, "relation", None)
    identity = getattr(relation, "relation_identity", None)
    if not isinstance(identity, str) or not identity:
        raise TASK039E3RecoveryScienceV2Error("projected evidence identity is unavailable")
    return identity


def _validate_schedule(relation_identities: Sequence[str]) -> tuple[str, ...]:
    schedule = tuple(relation_identities)
    if (
        len(schedule) != RELATION_COUNT
        or len(set(schedule)) != RELATION_COUNT
        or any(not isinstance(identity, str) or not identity for identity in schedule)
    ):
        raise TASK039E3RecoveryScienceV2Error(
            "post-capability schedule must contain 42 unique relation identities"
        )
    return schedule


def _run_post_capability_scientific_execution_v2(
    *,
    authority: PostCapabilityAuthorityV2,
    relation_identities: Sequence[str],
    evidence_loader: Callable[[Sequence[str]], Sequence[Any]],
    transport: Any,
    ledgers: ScientificLedgersV2,
    runners: _FrozenArmRunnersV2,
    progress: Callable[[str], None],
) -> PostCapabilityScientificResultV2:
    """Pure orchestration seam used by the public runner and synthetic tests."""

    authority.validate()
    schedule = _validate_schedule(relation_identities)
    if _records(ledgers.provider, "scientific provider"):
        raise TASK039E3RecoveryScienceV2Error(
            "scientific provider ledger must begin empty and capability-free"
        )

    # This is deliberately the first externally supplied operation after the
    # PASS/custody and empty-ledger preconditions.
    evidence_records = tuple(evidence_loader(schedule))
    if len(evidence_records) != RELATION_COUNT:
        raise TASK039E3RecoveryScienceV2Error("E1 evidence schedule count differs")
    if tuple(_relation_identity(item) for item in evidence_records) != schedule:
        raise TASK039E3RecoveryScienceV2Error("E1 evidence schedule order differs")

    for index, evidence in enumerate(evidence_records):
        runners.t0(
            evidence=evidence,
            proposal_ledger=ledgers.proposal,
            outcome_ledger=ledgers.outcome,
        )
        runners.t1(
            relation_schedule_index=index,
            evidence=evidence,
            transport=transport,
            call_ledger=ledgers.provider,
            proposal_ledger=ledgers.proposal,
            outcome_ledger=ledgers.outcome,
        )
        runners.t1b(
            relation_schedule_index=index,
            evidence=evidence,
            transport=transport,
            call_ledger=ledgers.provider,
            proposal_ledger=ledgers.proposal,
            outcome_ledger=ledgers.outcome,
        )
        runners.t2(
            relation_schedule_index=index,
            evidence=evidence,
            transport=transport,
            call_ledger=ledgers.provider,
            proposal_ledger=ledgers.proposal,
            outcome_ledger=ledgers.outcome,
            retrieval_identity=evidence.approved_evidence_identities[0],
        )
        direct = runners.direct_number(
            relation_schedule_index=index,
            evidence=evidence,
            transport=transport,
            call_ledger=ledgers.provider,
        )
        ledgers.direct_number.append(direct)
        progress(f"relation {index + 1:02d}/42 completed")

    provider_records = _records(ledgers.provider, "scientific provider")
    counts = {arm: 0 for arm in _SCIENTIFIC_ARMS}
    for record in provider_records:
        slot = getattr(record, "slot", None)
        if slot is None or getattr(slot, "scientific", None) is not True:
            raise TASK039E3RecoveryScienceV2Error(
                "scientific provider ledger contains a non-scientific slot"
            )
        arm = getattr(slot, "arm", None)
        if arm not in counts:
            raise TASK039E3RecoveryScienceV2Error(
                "scientific provider ledger contains an unknown arm"
            )
        counts[arm] += 1

    if counts["T1"] != 42:
        raise TASK039E3RecoveryScienceV2Error("T1 logical call count differs")
    if counts["T1-B"] != 126:
        raise TASK039E3RecoveryScienceV2Error("T1-B logical call count differs")
    if not 42 <= counts["T2"] <= 126:
        raise TASK039E3RecoveryScienceV2Error("T2 logical call count differs")
    if counts["T1-DIRECT-NUMBER"] != 42:
        raise TASK039E3RecoveryScienceV2Error("direct-number logical call count differs")
    scientific_calls = sum(counts.values())
    if scientific_calls != 210 + counts["T2"]:
        raise TASK039E3RecoveryScienceV2Error("scientific logical call formula differs")
    if not MINIMUM_SCIENTIFIC_LOGICAL_CALLS <= scientific_calls <= MAXIMUM_SCIENTIFIC_LOGICAL_CALLS:
        raise TASK039E3RecoveryScienceV2Error("scientific logical call bounds differ")

    outcome_records = _records(ledgers.outcome, "construction outcome")
    outcome_counts = {
        arm: sum(getattr(item, "arm", None) == arm for item in outcome_records)
        for arm in ("T0", "T1", "T1-B", "T2")
    }
    if any(outcome_counts[arm] != 42 for arm in outcome_counts):
        raise TASK039E3RecoveryScienceV2Error("construction outcome count differs")
    direct_records = _records(ledgers.direct_number, "direct-number")
    if len(direct_records) != 42:
        raise TASK039E3RecoveryScienceV2Error("direct-number outcome count differs")
    assert_complete = getattr(ledgers.outcome, "assert_complete_future_cohort", None)
    if callable(assert_complete):
        assert_complete(schedule)

    return PostCapabilityScientificResultV2(
        relation_count=RELATION_COUNT,
        t0_outcomes=outcome_counts["T0"],
        t1_logical_calls=counts["T1"],
        t1b_logical_calls=counts["T1-B"],
        t2_logical_calls=counts["T2"],
        direct_number_logical_calls=counts["T1-DIRECT-NUMBER"],
        scientific_logical_calls=scientific_calls,
    )


def run_post_capability_scientific_execution_v2(
    *,
    authority: PostCapabilityAuthorityV2,
    e1_private_root: Path,
    public_cohort: Mapping[str, Any],
    relation_identities: Sequence[str],
    transport: Any,
    ledgers: ScientificLedgersV2,
    progress: Callable[[str], None] = print,
) -> PostCapabilityScientificResultV2:
    """Run frozen construction arms without another capability invocation."""

    def load(schedule: Sequence[str]) -> Sequence[Any]:
        return load_real_evidence_schedule_v1(
            private_ledger_path=e1_private_root / PRIVATE_LEDGER_FILE,
            public_cohort=public_cohort,
            relation_identities=schedule,
        )

    return _run_post_capability_scientific_execution_v2(
        authority=authority,
        relation_identities=relation_identities,
        evidence_loader=load,
        transport=transport,
        ledgers=ledgers,
        runners=FROZEN_ARM_RUNNERS_V2,
        progress=progress,
    )


__all__ = [
    "FROZEN_ARM_RUNNERS_V2",
    "LOCAL_COMPATIBILITY_SLOTS",
    "MAXIMUM_SCIENTIFIC_LOGICAL_CALLS",
    "MINIMUM_SCIENTIFIC_LOGICAL_CALLS",
    "PostCapabilityAuthorityV2",
    "PostCapabilityScientificResultV2",
    "RELATION_COUNT",
    "SCIENTIFIC_CONCURRENCY",
    "SCIENTIFIC_GENERATION_RETRIES",
    "ScientificLedgersV2",
    "TASK039E3RecoveryScienceV2Error",
    "run_post_capability_scientific_execution_v2",
]
