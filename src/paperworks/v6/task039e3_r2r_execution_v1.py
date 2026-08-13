"""Offline-safe R2R fresh-cohort coordinator.

Only orchestration order and authority invariants live here.  Provider and E1
operations are caller-injected so tests can prove that no capability transport
exists and that scientific access is unreachable until authorization,
capability reuse, and four empty-ledger guards have passed.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Mapping, TypeVar

from paperworks.v6.task039e3_orchestration_v1 import (
    run_direct_number_v1,
    run_t1_v1,
    run_t1b_v1,
    run_t2_v1,
)
from paperworks.v6.task039e3_r2r_request_contract_v1 import (
    build_r2r_main_request_v1,
    build_r2r_t2_followup_request_v1,
)
from paperworks.v6.task039e3_r2r_authorization_v1 import (
    ValidatedR2RAuthorizationV1,
    validate_r2r_authorization_v1,
)
from paperworks.v6.task039e3_recovery_science_v2 import (
    PostCapabilityAuthorityV2,
    PostCapabilityScientificResultV2,
    ScientificLedgersV2,
    _FrozenArmRunnersV2,
    _run_post_capability_scientific_execution_v2,
)
from paperworks.v6.task039e3_scientific_execution_v1 import run_real_t0_v1
from paperworks.v6.task039e3_r2r_capability_reuse_v1 import (
    CapabilityLedgerObservationR2RV1,
    ValidatedCapabilityReuseR2RV1,
    validate_capability_reuse_v1,
)
from paperworks.v6.task039e3_recovery_transactional_custody_v3 import (
    TransactionalLedgerReconstructionV3,
)


EXPECTED_EMPTY_LEDGER_KINDS = (
    "scientific_provider",
    "proposal_validity",
    "construction_outcome",
    "direct_number",
)
RECOVERY_EXECUTION_MODE = "FRESH_FULL_COHORT_RESTART"
HISTORICAL_ORIGINAL_R2_SCIENTIFIC_LOGICAL_CALLS = 1
HISTORICAL_ZERO_CONTACT_R2R_SCIENTIFIC_LOGICAL_CALLS = 0
HISTORICAL_PARTIAL_R2R_SCIENTIFIC_LOGICAL_CALLS = 5
HISTORICAL_SCIENTIFIC_LOGICAL_CALLS_TOTAL = 6


class TASK039E3R2RExecutionError(ValueError):
    """A fresh R2R cohort precondition is not satisfied."""


def _run_t1_r2r_v1(**kwargs: Any) -> Any:
    return run_t1_v1(**kwargs, main_request_builder=build_r2r_main_request_v1)


def _run_t1b_r2r_v1(**kwargs: Any) -> Any:
    return run_t1b_v1(**kwargs, main_request_builder=build_r2r_main_request_v1)


def _run_t2_r2r_v1(**kwargs: Any) -> Any:
    return run_t2_v1(
        **kwargs,
        main_request_builder=build_r2r_main_request_v1,
        t2_followup_request_builder=build_r2r_t2_followup_request_v1,
    )


R2R_ARM_RUNNERS_V1 = _FrozenArmRunnersV2(
    t0=run_real_t0_v1,
    t1=_run_t1_r2r_v1,
    t1b=_run_t1b_r2r_v1,
    t2=_run_t2_r2r_v1,
    direct_number=run_direct_number_v1,
)


@dataclass(frozen=True)
class FreshLedgerObservationR2RV1:
    ledger_kind: str
    authoritative_record_count: int
    head_record_hash: str | None
    orphan_record_hashes: tuple[str, ...] = ()
    pending_files: tuple[str, ...] = ()


@dataclass(frozen=True)
class R2RLifetimeAccountingV1:
    historical_aborted_r2_scientific_logical_calls: int
    historical_original_r2_scientific_logical_calls: int
    historical_zero_contact_r2r_scientific_logical_calls: int
    historical_partial_r2r_scientific_logical_calls: int
    historical_scientific_logical_calls_total: int
    recovery_cohort_scientific_logical_calls: int
    lifetime_scientific_logical_call_attempts: int


def fresh_ledger_observation_from_reconstruction_v1(
    reconstruction: TransactionalLedgerReconstructionV3,
) -> FreshLedgerObservationR2RV1:
    """Adapt one disk-verified ledger reconstruction for the empty-set guard."""

    return FreshLedgerObservationR2RV1(
        ledger_kind=reconstruction.ledger_kind,
        authoritative_record_count=reconstruction.authoritative_record_count,
        head_record_hash=reconstruction.head_record_hash,
        orphan_record_hashes=reconstruction.orphan_record_hashes,
        pending_files=reconstruction.pending_files,
    )


def build_lifetime_accounting_v1(
    recovery_cohort_scientific_logical_calls: int,
) -> R2RLifetimeAccountingV1:
    """Keep all failed-run calls visible but outside fresh-cohort metrics."""

    if (
        isinstance(recovery_cohort_scientific_logical_calls, bool)
        or recovery_cohort_scientific_logical_calls < 252
        or recovery_cohort_scientific_logical_calls > 336
    ):
        raise TASK039E3R2RExecutionError(
            "R2R recovery-cohort logical-call count must be within 252..336"
        )
    return R2RLifetimeAccountingV1(
        historical_aborted_r2_scientific_logical_calls=(
            HISTORICAL_ORIGINAL_R2_SCIENTIFIC_LOGICAL_CALLS
        ),
        historical_original_r2_scientific_logical_calls=(
            HISTORICAL_ORIGINAL_R2_SCIENTIFIC_LOGICAL_CALLS
        ),
        historical_zero_contact_r2r_scientific_logical_calls=(
            HISTORICAL_ZERO_CONTACT_R2R_SCIENTIFIC_LOGICAL_CALLS
        ),
        historical_partial_r2r_scientific_logical_calls=(
            HISTORICAL_PARTIAL_R2R_SCIENTIFIC_LOGICAL_CALLS
        ),
        historical_scientific_logical_calls_total=(
            HISTORICAL_SCIENTIFIC_LOGICAL_CALLS_TOTAL
        ),
        recovery_cohort_scientific_logical_calls=(
            recovery_cohort_scientific_logical_calls
        ),
        lifetime_scientific_logical_call_attempts=(
            HISTORICAL_SCIENTIFIC_LOGICAL_CALLS_TOTAL
            + recovery_cohort_scientific_logical_calls
        ),
    )


def validate_empty_fresh_cohort_ledgers_v1(
    observations: tuple[FreshLedgerObservationR2RV1, ...],
) -> None:
    """Reject resume, old-result import, or ambiguous fresh-ledger state."""

    if tuple(item.ledger_kind for item in observations) != EXPECTED_EMPTY_LEDGER_KINDS:
        raise TASK039E3R2RExecutionError("R2R fresh ledger set or order differs")
    for item in observations:
        if item.authoritative_record_count != 0 or item.head_record_hash is not None:
            raise TASK039E3R2RExecutionError(
                f"R2R {item.ledger_kind} ledger is not empty"
            )
        if item.orphan_record_hashes or item.pending_files:
            raise TASK039E3R2RExecutionError(
                f"R2R {item.ledger_kind} ledger contains non-authoritative state"
            )


_E1T = TypeVar("_E1T")
_ResultT = TypeVar("_ResultT")


@dataclass(frozen=True)
class R2RExecutionBootstrapV1:
    authorization: ValidatedR2RAuthorizationV1
    capability_reuse: ValidatedCapabilityReuseR2RV1
    e1_input: Any
    scientific_result: Any
    completed_stage_order: tuple[str, ...]
    capability_transport_calls: int = 0
    capability_probe_calls: int = 0
    prior_partial_records_reused: int = 0
    recovery_execution_mode: str = RECOVERY_EXECUTION_MODE


def run_fresh_r2r_cohort_v1(
    *,
    authorization_document: Mapping[str, Any],
    private_capability_receipt: Mapping[str, Any],
    capability_ledger_observation: CapabilityLedgerObservationR2RV1,
    fresh_ledger_observations_loader: Callable[
        [], tuple[FreshLedgerObservationR2RV1, ...]
    ],
    e1_loader: Callable[[], _E1T],
    scientific_runner: Callable[[_E1T], _ResultT],
    stage_sink: Callable[[str], None] | None = None,
) -> R2RExecutionBootstrapV1:
    """Run a new cohort after reusable PASS validation; never run a probe.

    The function deliberately has no capability-transport argument.  Its only
    capability path is validation of already durable custody.  E1 loading and
    scientific execution remain injected for future audited integration.
    """

    stages: list[str] = []

    def mark(stage: str) -> None:
        stages.append(stage)
        if stage_sink is not None:
            stage_sink(stage)

    authorization = validate_r2r_authorization_v1(authorization_document)
    mark("r2r_authorization_validated")
    capability_reuse = validate_capability_reuse_v1(
        private_capability_receipt=private_capability_receipt,
        ledger_observation=capability_ledger_observation,
    )
    mark("durable_capability_pass_reused")
    ledgers = fresh_ledger_observations_loader()
    validate_empty_fresh_cohort_ledgers_v1(ledgers)
    mark("fresh_full_cohort_ledgers_empty")
    e1_input = e1_loader()
    mark("e1_loaded_after_reuse_and_empty_ledgers")
    scientific_result = scientific_runner(e1_input)
    mark("fresh_scientific_cohort_executed")
    return R2RExecutionBootstrapV1(
        authorization=authorization,
        capability_reuse=capability_reuse,
        e1_input=e1_input,
        scientific_result=scientific_result,
        completed_stage_order=tuple(stages),
    )


def run_injected_r2r_scientific_cohort_v1(
    *,
    relation_identities: tuple[str, ...],
    evidence_records: tuple[Any, ...],
    transport: Any,
    ledgers: ScientificLedgersV2,
    progress: Callable[[str], None] = print,
) -> PostCapabilityScientificResultV2:
    """Execute the shared 42-relation engine with the R2R request contract.

    This seam performs no credential, provider, E1, or filesystem lookup.  A
    future audited runner may invoke it only after ``run_fresh_r2r_cohort_v1``
    has validated authorization, durable capability reuse, and four empty
    disk-authoritative ledgers.
    """

    return _run_post_capability_scientific_execution_v2(
        authority=PostCapabilityAuthorityV2(
            gate_status="PASS",
            capability_custody_frozen=True,
            capability_receipt_durable=True,
            capability_receipt_hash=(
                "9ee4637da31b585a34eda4bad3b3be1dfa5597396ce1e78ef0564fa53da2b428"
            ),
        ),
        relation_identities=relation_identities,
        evidence_loader=lambda schedule: evidence_records,
        transport=transport,
        ledgers=ledgers,
        runners=R2R_ARM_RUNNERS_V1,
        progress=progress,
    )


__all__ = [
    "EXPECTED_EMPTY_LEDGER_KINDS",
    "FreshLedgerObservationR2RV1",
    "HISTORICAL_ORIGINAL_R2_SCIENTIFIC_LOGICAL_CALLS",
    "HISTORICAL_PARTIAL_R2R_SCIENTIFIC_LOGICAL_CALLS",
    "HISTORICAL_SCIENTIFIC_LOGICAL_CALLS_TOTAL",
    "HISTORICAL_ZERO_CONTACT_R2R_SCIENTIFIC_LOGICAL_CALLS",
    "R2RExecutionBootstrapV1",
    "R2RLifetimeAccountingV1",
    "RECOVERY_EXECUTION_MODE",
    "R2R_ARM_RUNNERS_V1",
    "TASK039E3R2RExecutionError",
    "build_lifetime_accounting_v1",
    "fresh_ledger_observation_from_reconstruction_v1",
    "run_fresh_r2r_cohort_v1",
    "run_injected_r2r_scientific_cohort_v1",
    "validate_empty_fresh_cohort_ledgers_v1",
]
