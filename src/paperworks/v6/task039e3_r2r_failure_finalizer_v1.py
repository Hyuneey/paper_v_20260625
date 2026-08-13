"""Durable sanitized failure finalization for a future one-shot R2R run.

The helpers are provider-agnostic.  They neither retry nor resume work, and
they distinguish failure-receipt persistence failure from the original
scientific/finalization failure.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any, TypeVar

from paperworks.v6.task039e3_recovery_serialization_v1 import (
    write_public_artifact_atomic_v1,
)
from paperworks.v6.task039e3_r2r_execution_v1 import (
    HISTORICAL_ORIGINAL_R2_SCIENTIFIC_LOGICAL_CALLS,
    HISTORICAL_PARTIAL_R2R_SCIENTIFIC_LOGICAL_CALLS,
    HISTORICAL_SCIENTIFIC_LOGICAL_CALLS_TOTAL,
    HISTORICAL_ZERO_CONTACT_R2R_SCIENTIFIC_LOGICAL_CALLS,
)


FAILURE_STATUS = "failed_task039e3_r2r_scientific_execution"
DOUBLE_FAULT_CLASSIFICATION = "double_fault_failure_receipt_persistence_failed"
FAILURE_ARTIFACT_NAME = "TASK-039E3_R2R_EXECUTION_FAILURE.json"


class TASK039E3R2RFailureFinalizationError(RuntimeError):
    """Base error for R2R guarded failure finalization."""


class TASK039E3R2RGuardedExecutionFailure(TASK039E3R2RFailureFinalizationError):
    """The original failure was durably represented by a sanitized receipt."""

    def __init__(
        self, original_failure: BaseException, failure_receipt: Mapping[str, Any]
    ) -> None:
        super().__init__(FAILURE_STATUS)
        self.original_failure = original_failure
        self.failure_receipt = failure_receipt


class TASK039E3R2RFailureReceiptDoubleFault(TASK039E3R2RFailureFinalizationError):
    """Both execution and terminal failure-receipt persistence failed."""

    classification = DOUBLE_FAULT_CLASSIFICATION

    def __init__(
        self, original_failure: BaseException, persistence_failure: BaseException
    ) -> None:
        super().__init__(DOUBLE_FAULT_CLASSIFICATION)
        self.original_failure = original_failure
        self.persistence_failure = persistence_failure


def _require_failure_context(context: Mapping[str, Any]) -> dict[str, Any]:
    required = {
        "execution_commit",
        "source_manifest_hash",
        "authorization_hash",
        "configuration_fingerprint",
        "capability_reuse_status",
        "capability_provider_ledger_head_hash",
        "scientific_provider_ledger_head_hash",
        "last_attempted_scientific_slot",
        "completed_r2r_scientific_logical_calls",
        "r2r_scientific_transport_attempts",
        "proposal_committed_count",
        "outcome_committed_count",
        "direct_number_committed_count",
        "postcontact_integrity_status",
    }
    optional = {"actual_returned_model", "actual_response_id", "terminal_slot_state"}
    if (
        not isinstance(context, Mapping)
        or not required.issubset(context)
        or not set(context).issubset(required | optional)
    ):
        raise TASK039E3R2RFailureFinalizationError(
            "R2R failure receipt context differs"
        )
    values = dict(context)
    for field in optional:
        values.setdefault(field, None)
    return values


def write_terminal_failure_receipt_r2r_v1(
    *,
    destination: Path,
    failure_stage: str,
    failure: BaseException,
    context: Mapping[str, Any],
) -> dict[str, Any]:
    """Atomically persist only sanitized reconstruction metadata."""

    values = _require_failure_context(context)
    return write_public_artifact_atomic_v1(
        destination,
        {
            "schema_version": "1.0.0",
            "artifact_type": "task039e3_r2r_execution_failure_receipt_v1",
            "task_id": "TASK-039E3-R2R-SCIENTIFIC-EXECUTION",
            "status": FAILURE_STATUS,
            "failure_stage": failure_stage,
            "failure_classification": type(failure).__name__,
            **values,
            "historical_aborted_r2_scientific_logical_calls": (
                HISTORICAL_ORIGINAL_R2_SCIENTIFIC_LOGICAL_CALLS
            ),
            "historical_original_r2_scientific_logical_calls": (
                HISTORICAL_ORIGINAL_R2_SCIENTIFIC_LOGICAL_CALLS
            ),
            "historical_zero_contact_r2r_scientific_logical_calls": (
                HISTORICAL_ZERO_CONTACT_R2R_SCIENTIFIC_LOGICAL_CALLS
            ),
            "historical_partial_r2r_scientific_logical_calls": (
                HISTORICAL_PARTIAL_R2R_SCIENTIFIC_LOGICAL_CALLS
            ),
            "historical_scientific_logical_calls_total": (
                HISTORICAL_SCIENTIFIC_LOGICAL_CALLS_TOTAL
            ),
            "lifetime_scientific_logical_call_attempts": (
                HISTORICAL_SCIENTIFIC_LOGICAL_CALLS_TOTAL
                + values["completed_r2r_scientific_logical_calls"]
            ),
            "historical_partial_results_reused": False,
            "additional_capability_probes": 0,
            "third_capability_probe_authorized": False,
            "automatic_resume_authorized": False,
            "provider_recontact_authorized": False,
            "patch_and_continue_authorized": False,
            "rule_v2_authorized": False,
            "runtime_authority": False,
            "utility_evaluation_authorized": False,
            "winner_selected": False,
            "error_message_persisted": False,
            "credential_persisted": False,
            "authorization_header_persisted": False,
            "raw_provider_content_persisted_publicly": False,
            "raw_private_evidence_persisted": False,
            "chain_of_thought_persisted": False,
        },
    )


_ResultT = TypeVar("_ResultT")


def run_guarded_r2r_execution_v1(
    *,
    provider_contact_started: bool,
    execution_stage: str,
    execute_science: Callable[[], _ResultT],
    finalize_success: Callable[[_ResultT], Any],
    failure_receipt_writer: Callable[..., Mapping[str, Any]],
    failure_context: Mapping[str, Any] | Callable[[], Mapping[str, Any]],
) -> Any:
    """Run once; after contact, durably fail without retry, resume, or recontact."""

    try:
        result = execute_science()
        return finalize_success(result)
    except Exception as failure:
        if not provider_contact_started:
            raise
        try:
            context = failure_context() if callable(failure_context) else failure_context
            receipt = failure_receipt_writer(
                failure_stage=execution_stage,
                failure=failure,
                context=context,
            )
        except Exception as persistence_failure:
            raise TASK039E3R2RFailureReceiptDoubleFault(
                failure, persistence_failure
            ) from failure
        raise TASK039E3R2RGuardedExecutionFailure(failure, receipt) from failure


__all__ = [
    "DOUBLE_FAULT_CLASSIFICATION",
    "FAILURE_ARTIFACT_NAME",
    "FAILURE_STATUS",
    "TASK039E3R2RFailureFinalizationError",
    "TASK039E3R2RFailureReceiptDoubleFault",
    "TASK039E3R2RGuardedExecutionFailure",
    "run_guarded_r2r_execution_v1",
    "write_terminal_failure_receipt_r2r_v1",
]
