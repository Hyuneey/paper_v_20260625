"""Active, final-audit-bound recovery execution coordinator V3.

This additive R1D2 module composes the corrected capability gate, guarded V3
transport, transactional provider custody, unchanged frozen scientific arms,
and complete result finalization.  It deliberately contains no credential
lookup and no provider construction; those remain behind the runner's ordered
pre-contact guards.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
import subprocess
from typing import Any, Callable, Mapping, Sequence, TypeVar

from paperworks.v6.common import stable_hash_v1
from paperworks.v6.task039e3_execution_prep_v1 import (
    FrozenProviderRequestV1,
    MockProviderResponseV1,
    MockProviderTransportV1,
    ProviderCallSlotV1,
)
from paperworks.v6.task039e3_recovery_authorization_v3 import (
    CORRECTED_CUSTODY_ACCOUNTING_HASH,
    GitExecutionStateV3,
    HISTORICAL_BLOCKED_R1D_COMMIT,
    HISTORICAL_BLOCKED_R1D_DATA_ACCESS_AUDIT_HASH,
    HISTORICAL_BLOCKED_R1D_IMPLEMENTATION_RECEIPT_HASH,
    HISTORICAL_BLOCKED_R1D_PREFLIGHT_HASH,
    PriorAuthorityStateV3,
    R0_BUNDLE_HASH,
    R0_COMMIT,
    R1A_COMMIT,
    R1A_TIMEOUT_AUTHORITY_HASH,
    R1B_COMMIT_A,
    R1B_COMMIT_B,
    R1C_AUDIT_COMMIT_B,
    R1C_AUDIT_RECEIPT_HASH,
    R1C_COMMIT_A,
    R1C_COMMIT_B,
    R1C_IMPLEMENTATION_RECEIPT_HASH,
    R1C_INDEPENDENT_AUDIT_BUNDLE_HASH,
    R1C_REMEDIATION_BUNDLE_HASH,
    R1C_SOURCE_MANIFEST_HASH,
)
from paperworks.v6.task039e3_recovery_capability_v1 import (
    RecoveryCapabilityGateResultV1,
    build_recovery_capability_request_v1,
    evaluate_recovery_capability_response_v1,
)
from paperworks.v6.task039e3_recovery_integrity_v3 import (
    PostContactIntegrityGuardV3,
)
from paperworks.v6.task039e3_recovery_live_transport_v3 import (
    RecoveryLiveOpenAIChatCompletionsTransportV3,
    RecoveryProviderResponseV3,
    logical_parse_status_v3,
    terminal_classification_v3,
)
from paperworks.v6.task039e3_recovery_result_finalizer_v3 import (
    FinalizedScientificResultV3,
    PUBLIC_ARTIFACT_NAMES_V3,
    finalize_successful_scientific_result_v3,
    provider_custody_binding_from_reconstruction_v3,
)
from paperworks.v6.task039e3_recovery_science_v2 import (
    PostCapabilityAuthorityV2,
    ScientificLedgersV2,
    run_post_capability_scientific_execution_v2,
)
from paperworks.v6.task039e3_recovery_serialization_v1 import (
    finalize_public_artifact_v1,
    verify_public_artifact_v1,
    write_public_artifact_atomic_v1,
)
from paperworks.v6.task039e3_recovery_authorization_v1 import (
    RecoveryPrivateRootsV1,
    validate_recovery_private_roots_v1,
)
from paperworks.v6.task039e3_recovery_transactional_custody_v3 import (
    TransactionalHashChainCustodyV3,
)
from paperworks.v6.task039e3_scientific_execution_v1 import (
    DurableConstructionOutcomeLedgerV1,
    DurableConstructionProposalLedgerV1,
    DurableDirectNumberLedgerV1,
)


RECOVERY_CAPABILITY_PASS = "passed_task039e3_recovery_capability_gate"
RECOVERY_CAPABILITY_BLOCK = "blocked_task039e3_recovery_capability_gate"
FAILURE_STATUS = "failed_task039e3_r2_recovery_execution"
DOUBLE_FAULT_CLASSIFICATION = "double_fault_failure_receipt_persistence_failed"
_RETRYABLE = frozenset(
    {"connection_failure", "connection_reset", "timeout_before_response", "http_429", "http_5xx"}
)


class TASK039E3RecoveryExecutionV3Error(RuntimeError):
    """Fail-closed active V3 execution error."""


class TASK039E3RecoveryScientificAbortV3Error(TASK039E3RecoveryExecutionV3Error):
    """Raised after the observed provider result is transactionally durable."""

    def __init__(self, message: str, *, record: "TransactionalProviderRecordV3") -> None:
        super().__init__(message)
        self.record = record


class TASK039E3RecoveryGuardedExecutionFailureV3Error(TASK039E3RecoveryExecutionV3Error):
    """An ordinary post-contact failure with a durable sanitized receipt."""

    def __init__(self, original_failure: BaseException, failure_receipt: Mapping[str, Any]) -> None:
        super().__init__(f"post-contact execution failed: {type(original_failure).__name__}")
        self.original_failure = original_failure
        self.failure_receipt = failure_receipt


class TASK039E3RecoveryFailureReceiptDoubleFaultV3Error(TASK039E3RecoveryExecutionV3Error):
    """The execution failed and failure-receipt persistence also failed."""

    failure_classification = DOUBLE_FAULT_CLASSIFICATION

    def __init__(self, original_failure: BaseException, persistence_failure: BaseException) -> None:
        super().__init__(DOUBLE_FAULT_CLASSIFICATION)
        self.original_failure = original_failure
        self.persistence_failure = persistence_failure


@dataclass(frozen=True)
class RecoveryCapabilityExecutionV3:
    request: FrozenProviderRequestV1
    response: RecoveryProviderResponseV3
    gate: RecoveryCapabilityGateResultV1
    transport_attempts: int
    transport_retries: int

    def __post_init__(self) -> None:
        if self.transport_attempts not in {1, 2, 3}:
            raise TASK039E3RecoveryExecutionV3Error("capability attempt count differs")
        if self.transport_retries != self.transport_attempts - 1:
            raise TASK039E3RecoveryExecutionV3Error("capability retry count differs")


@dataclass(frozen=True)
class GuardedExecutionRootsV3:
    e1_private_root: Path
    historical_e3_private_root: Path
    recovery_e3_private_root: Path
    public_output_root: Path
    historical_e3_access_mode: str = "read_only"


def validate_execution_roots_v3(
    *,
    repository_root: Path,
    e1_private_value: str,
    historical_e3_private_value: str,
    recovery_e3_private_value: str,
    public_output_value: str,
) -> GuardedExecutionRootsV3:
    private: RecoveryPrivateRootsV1 = validate_recovery_private_roots_v1(
        repository_root=repository_root,
        e1_private_value=e1_private_value,
        historical_e3_private_value=historical_e3_private_value,
        recovery_e3_private_value=recovery_e3_private_value,
    )
    requested = Path(public_output_value)
    if (
        not public_output_value
        or not requested.is_absolute()
        or ".." in requested.parts
    ):
        raise TASK039E3RecoveryExecutionV3Error(
            "public output root must be an explicit absolute traversal-free path"
        )
    current = requested
    while True:
        junction = getattr(current, "is_junction", None)
        if current.is_symlink() or (callable(junction) and junction()):
            raise TASK039E3RecoveryExecutionV3Error(
                "public output root must not contain symlink or junction components"
            )
        if current.parent == current:
            break
        current = current.parent
    public = requested.resolve(strict=False)
    if public.exists() and (not public.is_dir() or any(public.iterdir())):
        raise TASK039E3RecoveryExecutionV3Error("public output root must be new or empty")
    if not public.exists() and not public.parent.is_dir():
        raise TASK039E3RecoveryExecutionV3Error("public output root parent must exist")
    repository = repository_root.resolve(strict=True)
    protected = (
        repository,
        private.e1_private_root,
        private.historical_e3_private_root,
        private.recovery_e3_private_root,
    )
    for other in protected:
        try:
            public.relative_to(other)
            overlaps = True
        except ValueError:
            try:
                other.relative_to(public)
                overlaps = True
            except ValueError:
                overlaps = False
        if overlaps:
            raise TASK039E3RecoveryExecutionV3Error(
                "public output root must remain distinct and unnested"
            )
    return GuardedExecutionRootsV3(
        e1_private_root=private.e1_private_root,
        historical_e3_private_root=private.historical_e3_private_root,
        recovery_e3_private_root=private.recovery_e3_private_root,
        public_output_root=public,
    )


@dataclass(frozen=True)
class TransactionalProviderRecordV3:
    """ProviderCallLedger-compatible view of one transactional record."""

    slot: ProviderCallSlotV1
    record_hash: str
    terminal_slot_state: str
    parse_status: str
    response_present: bool
    provider_response_metadata: Mapping[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "slot": self.slot.to_dict(),
            "slot_hash": self.slot.slot_hash,
            "record_hash": self.record_hash,
            "terminal_slot_state": self.terminal_slot_state,
            "parse_status": self.parse_status,
            "response_present": self.response_present,
            "provider_response_metadata": dict(self.provider_response_metadata),
            "logical_call_kind": "scientific" if self.slot.scientific else "recovery_capability",
            "scientific": self.slot.scientific,
        }


class IntegrityGuardedTransportV3(MockProviderTransportV1):
    """Frozen-transport-compatible wrapper that checks every real attempt."""

    def __init__(
        self,
        delegate: RecoveryLiveOpenAIChatCompletionsTransportV3,
        guard: PostContactIntegrityGuardV3,
    ) -> None:
        self._delegate = delegate
        self._guard = guard

    @property
    def calls(self) -> int:
        return self._delegate.calls

    @property
    def request_hashes(self) -> tuple[str, ...]:
        return self._delegate.request_hashes

    @property
    def attempt_custody(self) -> tuple[Any, ...]:
        return self._delegate.attempt_custody

    def send(self, request: FrozenProviderRequestV1) -> RecoveryProviderResponseV3:
        return self._guard.execute_provider_attempt(lambda: self._delegate.send(request))


class TransactionalScientificProviderLedgerV3:
    """Adapter from frozen arm append calls to HEAD-authoritative V3 custody."""

    def __init__(
        self,
        custody: TransactionalHashChainCustodyV3,
        *,
        attempt_supplier: Callable[[], Sequence[Any]],
    ) -> None:
        if custody.ledger_kind != "scientific_provider":
            raise TASK039E3RecoveryExecutionV3Error("scientific custody kind differs")
        self._custody = custody
        self._attempt_supplier = attempt_supplier
        self._attempt_cursor = 0
        self._records: list[TransactionalProviderRecordV3] = []

    @property
    def records(self) -> tuple[TransactionalProviderRecordV3, ...]:
        return tuple(self._records)

    @property
    def ledger_hash(self) -> str:
        return self._custody.ledger_hash

    @property
    def provider_ledger_head_hash(self) -> str | None:
        return self._custody.authoritative_head_hash

    def append(
        self,
        *,
        slot: ProviderCallSlotV1,
        request_hash: str,
        response_present: bool,
        provider_response_metadata: Mapping[str, Any],
        transport_attempts: Sequence[Any],
        parse_status: str,
        proposal_core_hash: str | None,
        terminal_slot_state: str,
    ) -> TransactionalProviderRecordV3:
        if not slot.scientific:
            raise TASK039E3RecoveryExecutionV3Error("capability slot in scientific ledger")
        observed = tuple(self._attempt_supplier())
        detailed = observed[self._attempt_cursor :]
        self._attempt_cursor = len(observed)
        if len(detailed) != len(transport_attempts) or not detailed:
            raise TASK039E3RecoveryExecutionV3Error("scientific attempt custody slice differs")
        last = detailed[-1]
        outcome = str(getattr(last, "outcome", provider_response_metadata.get("outcome", "")))
        actual_terminal = str(getattr(last, "terminal_classification", terminal_slot_state))
        actual_parse = parse_status
        actual_present = bool(getattr(last, "response_present", response_present))
        if (
            terminal_slot_state == "transport_exhausted"
            and actual_terminal == "retryable_transport_failure"
        ):
            actual_terminal = "transport_exhausted"
        if actual_terminal == "completed_schema_invalid_response":
            actual_parse = "schema_invalid_response"
            actual_present = True
        metadata = {
            **dict(provider_response_metadata),
            "outcome": outcome,
            "response_origin": "provider",
            "provider_contacted": True,
            "provider_authored_response": bool(
                getattr(last, "provider_authored_response", actual_present)
            ),
            "transport_response_received": bool(
                getattr(last, "transport_response_received", actual_present)
            ),
            "structured_payload_valid": bool(
                getattr(last, "structured_payload_valid", False)
            ),
            "model": getattr(last, "returned_model", provider_response_metadata.get("model")),
            "response_id": getattr(last, "response_id", provider_response_metadata.get("response_id")),
            "finish_reason": getattr(last, "finish_reason", provider_response_metadata.get("finish_reason")),
            "token_usage": getattr(last, "token_usage", provider_response_metadata.get("token_usage")),
        }
        payload = {
            "logical_call_kind": "scientific",
            "scientific": True,
            "slot": slot.to_dict(),
            "slot_hash": slot.slot_hash,
            "request_hash": request_hash,
            "response_present": actual_present,
            "provider_response_metadata": metadata,
            "transport_attempts": [item.to_dict() for item in detailed],
            "parse_status": actual_parse,
            "proposal_core_hash": proposal_core_hash,
            "terminal_slot_state": actual_terminal,
            "response_origin": "provider",
            "provider_contacted": True,
            "provider_authored_response": metadata["provider_authored_response"],
        }
        committed = self._custody.append(
            logical_call_kind="scientific",
            slot_identity=slot.slot_hash,
            payload=payload,
        )
        view = TransactionalProviderRecordV3(
            slot=slot,
            record_hash=str(committed["record_hash"]),
            terminal_slot_state=actual_terminal,
            parse_status=actual_parse,
            response_present=actual_present,
            provider_response_metadata=metadata,
        )
        self._records.append(view)
        if actual_terminal in {
            "completed_model_identity_mismatch",
            "completed_schema_invalid_response",
        }:
            raise TASK039E3RecoveryScientificAbortV3Error(
                actual_terminal, record=view
            )
        return view

    def close(self) -> None:
        self._custody.reconstruct()


def execute_recovery_capability_probe_v3(
    transport: IntegrityGuardedTransportV3,
) -> RecoveryCapabilityExecutionV3:
    if transport.calls != 0 or transport.attempt_custody:
        raise TASK039E3RecoveryExecutionV3Error("recovery capability transport must begin unused")
    request = build_recovery_capability_request_v1()
    response: RecoveryProviderResponseV3 | None = None
    attempts = 0
    for attempts in range(1, 4):
        response = transport.send(request)
        retryable = not response.response_present and response.outcome in _RETRYABLE
        if response.response_present or not retryable:
            break
    if response is None:
        raise TASK039E3RecoveryExecutionV3Error("capability transport returned no event")
    return RecoveryCapabilityExecutionV3(
        request=request,
        response=response,
        gate=evaluate_recovery_capability_response_v1(response),
        transport_attempts=attempts,
        transport_retries=attempts - 1,
    )


def freeze_capability_custody_v3(
    *,
    execution: RecoveryCapabilityExecutionV3,
    transport: IntegrityGuardedTransportV3,
    custody: TransactionalHashChainCustodyV3,
) -> Mapping[str, Any]:
    if custody.ledger_kind != "recovery_capability" or custody.authoritative_record_count:
        raise TASK039E3RecoveryExecutionV3Error("capability transactional ledger differs")
    slot = ProviderCallSlotV1(
        None,
        stable_hash_v1({"fixture": "SYNTHETIC_CAPABILITY_CHECK"}),
        "CAPABILITY",
        1,
        False,
    )
    response = execution.response
    attempts = tuple(transport.attempt_custody)
    terminal = terminal_classification_v3(response)
    payload = {
        "logical_call_kind": "recovery_capability",
        "scientific": False,
        "slot": slot.to_dict(),
        "slot_hash": slot.slot_hash,
        "request_hash": execution.request.request_hash,
        "response_origin": "provider",
        "provider_contacted": True,
        "provider_authored_response": response.provider_authored_response,
        "transport_response_received": response.transport_response_received,
        "provider_payload_received": response.provider_payload_received,
        "response_present": response.response_present,
        "structured_payload_valid": response.structured_payload_valid,
        "returned_model": response.model,
        "response_id": response.response_id,
        "finish_reason": response.finish_reason,
        "usage": dict(response.token_usage) if response.token_usage else None,
        "system_fingerprint": response.system_fingerprint,
        "transport_attempts": [item.to_dict() for item in attempts],
        "parse_status": logical_parse_status_v3(response),
        "terminal_slot_state": terminal,
        "gate_status": execution.gate.gate_status,
    }
    record = custody.append(
        logical_call_kind="recovery_capability",
        slot_identity=slot.slot_hash,
        payload=payload,
    )
    reconstruction = custody.reconstruct()
    if reconstruction.authoritative_record_count != 1:
        raise TASK039E3RecoveryExecutionV3Error("one capability record was not committed")
    return {
        "record_hash": record["record_hash"],
        "provider_ledger_hash": reconstruction.ledger_hash,
        "provider_ledger_head_hash": reconstruction.head_record_hash,
        "record_count": 1,
        "durably_frozen": True,
        "terminal_slot_state": terminal,
    }


def build_recovery_capability_receipt_v3(
    *,
    execution: RecoveryCapabilityExecutionV3,
    execution_commit: str,
    source_manifest_hash: str,
    r2_authorization_hash: str,
    custody_binding: Mapping[str, Any],
) -> dict[str, Any]:
    response = execution.response
    return finalize_public_artifact_v1(
        {
            "schema_version": "3.0.0",
            "artifact_type": "task039e3_recovery_capability_receipt_v3",
            "task_id": "TASK-039E3-R2_RECOVERY_EXECUTION",
            "status": RECOVERY_CAPABILITY_PASS if execution.gate.gate_status == "PASS" else RECOVERY_CAPABILITY_BLOCK,
            "gate_status": execution.gate.gate_status,
            "execution_commit": execution_commit,
            "source_manifest_hash": source_manifest_hash,
            "r2_authorization_hash": r2_authorization_hash,
            "historical_capability_probes": 1,
            "current_recovery_capability_logical_calls": 1,
            "cumulative_real_provider_capability_probes": 2,
            "transport_attempts": execution.transport_attempts,
            "transport_retries": execution.transport_retries,
            "response_present": response.response_present,
            "provider_authored_response": response.provider_authored_response,
            "returned_model": response.model,
            "response_id": response.response_id,
            "finish_reason": response.finish_reason,
            "usage": dict(response.token_usage) if response.token_usage else None,
            "terminal_slot_state": custody_binding["terminal_slot_state"],
            "capability_provider_ledger_hash": custody_binding["provider_ledger_hash"],
            "capability_provider_ledger_head_hash": custody_binding["provider_ledger_head_hash"],
            "gate": execution.gate.to_dict(),
            "local_compatibility_slots": 0,
            "credential_persisted": False,
            "authorization_header_persisted": False,
        }
    )


def _require_failure_context(context: Mapping[str, Any]) -> dict[str, Any]:
    required = {
        "execution_commit",
        "source_manifest_hash",
        "authorization_hash",
        "configuration_fingerprint",
        "capability_gate_status",
        "capability_provider_ledger_head_hash",
        "scientific_provider_ledger_head_hash",
        "last_completed_scientific_slot",
        "completed_scientific_logical_calls",
        "scientific_transport_attempts",
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
        raise TASK039E3RecoveryExecutionV3Error("failure receipt context differs")
    values = dict(context)
    for field in optional:
        values.setdefault(field, None)
    return values


def write_terminal_failure_receipt_v3(
    *,
    destination: Path,
    failure_stage: str,
    failure: BaseException,
    context: Mapping[str, Any],
) -> dict[str, Any]:
    """Atomically freeze a sanitized terminal failure receipt."""

    values = _require_failure_context(context)
    content = {
        "schema_version": "3.0.0",
        "artifact_type": "task039e3_r2_execution_failure_receipt_v3",
        "task_id": "TASK-039E3-R2_RECOVERY_EXECUTION",
        "status": FAILURE_STATUS,
        "failure_stage": failure_stage,
        "failure_classification": type(failure).__name__,
        **values,
        "automatic_resume_authorized": False,
        "provider_recontact_authorized": False,
        "rule_v2_authorized": False,
        "runtime_authority": False,
        "utility_evaluation_authorized": False,
        "winner_selected": False,
        "error_message_persisted": False,
        "credential_persisted": False,
        "authorization_header_persisted": False,
        "raw_private_evidence_persisted": False,
        "chain_of_thought_persisted": False,
    }
    return write_public_artifact_atomic_v1(destination, content)


_ResultT = TypeVar("_ResultT")


def run_guarded_execution_v3(
    *,
    provider_contact_started: bool,
    execution_stage: str,
    execute_science: Callable[[], _ResultT],
    finalize_success: Callable[[_ResultT], Any],
    failure_receipt_writer: Callable[..., Mapping[str, Any]],
    failure_context: Mapping[str, Any] | Callable[[], Mapping[str, Any]],
) -> Any:
    """Make PASS reachable only through success finalization; freeze failures."""

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
            raise TASK039E3RecoveryFailureReceiptDoubleFaultV3Error(
                failure, persistence_failure
            ) from failure
        raise TASK039E3RecoveryGuardedExecutionFailureV3Error(
            failure, receipt
        ) from failure


def build_typed_accounting_v3(
    *,
    capability_attempts: int,
    scientific_result: Any,
    scientific_transport_attempts: int,
) -> dict[str, int]:
    values = scientific_result.to_dict()
    scientific_calls = int(values["scientific_logical_calls"])
    if scientific_transport_attempts < scientific_calls:
        raise TASK039E3RecoveryExecutionV3Error("scientific attempt count differs")
    return {
        "historical_capability_probes": 1,
        "current_recovery_capability_logical_calls": 1,
        "current_recovery_capability_transport_attempts": capability_attempts,
        "current_recovery_capability_transport_retries": capability_attempts - 1,
        "cumulative_real_provider_capability_probes": 2,
        "t1_logical_calls": int(values["t1_logical_calls"]),
        "t1b_logical_calls": int(values["t1b_logical_calls"]),
        "t2_logical_calls": int(values["t2_logical_calls"]),
        "direct_number_logical_calls": int(values["direct_number_logical_calls"]),
        "scientific_logical_calls": scientific_calls,
        "scientific_transport_attempts": scientific_transport_attempts,
        "scientific_transport_retries": scientific_transport_attempts - scientific_calls,
        "scientific_concurrency": int(values["scientific_concurrency"]),
        "scientific_generation_retries": int(values["scientific_generation_retries"]),
        "local_compatibility_slots": 0,
    }


def _failure_context_from_state(
    *,
    execution_commit: str,
    source_manifest_hash: str,
    authorization_hash: str,
    configuration_fingerprint: str,
    capability_gate_status: str,
    capability_custody: TransactionalHashChainCustodyV3,
    scientific_custody: TransactionalHashChainCustodyV3 | None,
    proposal_records: Sequence[Any],
    outcome_records: Sequence[Any],
    direct_records: Sequence[Any],
    transport_attempts: int,
    integrity_guard: PostContactIntegrityGuardV3,
) -> dict[str, Any]:
    scientific_records = scientific_custody.records if scientific_custody else ()
    capability_records = capability_custody.records
    observed_payload = (
        scientific_records[-1].get("payload", {})
        if scientific_records
        else capability_records[-1].get("payload", {})
        if capability_records
        else {}
    )
    metadata = observed_payload.get("provider_response_metadata", {})
    last = scientific_records[-1].get("payload", {}).get("slot") if scientific_records else None
    return {
        "execution_commit": execution_commit,
        "source_manifest_hash": source_manifest_hash,
        "authorization_hash": authorization_hash,
        "configuration_fingerprint": configuration_fingerprint,
        "capability_gate_status": capability_gate_status,
        "capability_provider_ledger_head_hash": capability_custody.authoritative_head_hash,
        "scientific_provider_ledger_head_hash": (
            scientific_custody.authoritative_head_hash if scientific_custody else None
        ),
        "last_completed_scientific_slot": last,
        "completed_scientific_logical_calls": len(scientific_records),
        "scientific_transport_attempts": transport_attempts,
        "proposal_committed_count": len(proposal_records),
        "outcome_committed_count": len(outcome_records),
        "direct_number_committed_count": len(direct_records),
        "postcontact_integrity_status": (
            "integrity_mismatch" if integrity_guard.blocked else "verified_unchanged"
        ),
        "actual_returned_model": observed_payload.get(
            "returned_model", metadata.get("model") if isinstance(metadata, Mapping) else None
        ),
        "actual_response_id": observed_payload.get(
            "response_id", metadata.get("response_id") if isinstance(metadata, Mapping) else None
        ),
        "terminal_slot_state": observed_payload.get("terminal_slot_state"),
    }


def run_capability_then_science_v3(
    *,
    repository_root: Path,
    execution_commit: str,
    source_manifest_hash: str,
    r2_authorization_hash: str,
    authority_bindings: Mapping[str, Any],
    scientific_source_hashes: Mapping[str, str],
    e1_private_root: Path,
    historical_e3_private_root: Path,
    recovery_private_root: Path,
    public_output_root: Path,
    public_cohort: Mapping[str, Any],
    relation_identities: Sequence[str],
    transport: RecoveryLiveOpenAIChatCompletionsTransportV3,
    integrity_guard: PostContactIntegrityGuardV3,
    progress: Callable[[str], None] = print,
    scientific_runner: Callable[..., Any] = run_post_capability_scientific_execution_v2,
    success_finalizer: Callable[..., FinalizedScientificResultV3] = finalize_successful_scientific_result_v3,
) -> dict[str, Any]:
    """Execute the V3 capability/science/finalization state machine."""

    guarded_transport = IntegrityGuardedTransportV3(transport, integrity_guard)
    capability_root = recovery_private_root / "capability_provider_v3"
    capability_custody = TransactionalHashChainCustodyV3(
        capability_root,
        ledger_kind="recovery_capability",
        allowed_logical_call_kind="recovery_capability",
    )
    execution = execute_recovery_capability_probe_v3(guarded_transport)
    custody_state = freeze_capability_custody_v3(
        execution=execution, transport=guarded_transport, custody=capability_custody
    )
    capability_receipt = build_recovery_capability_receipt_v3(
        execution=execution,
        execution_commit=execution_commit,
        source_manifest_hash=source_manifest_hash,
        r2_authorization_hash=r2_authorization_hash,
        custody_binding=custody_state,
    )
    capability_receipt_path = recovery_private_root / "recovery_capability_receipt_v3.json"
    write_public_artifact_atomic_v1(capability_receipt_path, capability_receipt)
    if execution.gate.gate_status != "PASS":
        if not public_output_root.exists():
            public_output_root.mkdir()
        failure_context = _failure_context_from_state(
            execution_commit=execution_commit,
            source_manifest_hash=source_manifest_hash,
            authorization_hash=r2_authorization_hash,
            configuration_fingerprint=integrity_guard.checks[-1].execution_configuration_fingerprint,
            capability_gate_status=execution.gate.gate_status,
            capability_custody=capability_custody,
            scientific_custody=None,
            proposal_records=(),
            outcome_records=(),
            direct_records=(),
            transport_attempts=0,
            integrity_guard=integrity_guard,
        )
        failure = TASK039E3RecoveryExecutionV3Error("corrected recovery capability BLOCK")
        failure_receipt = write_terminal_failure_receipt_v3(
            destination=public_output_root / "TASK-039E3_R2_EXECUTION_FAILURE.json",
            failure_stage="recovery_capability_gate",
            failure=failure,
            context=failure_context,
        )
        return {
            "status": RECOVERY_CAPABILITY_BLOCK,
            "capability_receipt": capability_receipt,
            "failure_receipt": failure_receipt,
            "scientific_calls": 0,
            "local_compatibility_slots": 0,
        }

    attempt_start = len(guarded_transport.attempt_custody)
    scientific_custody: TransactionalHashChainCustodyV3 | None = None
    provider_ledger: TransactionalScientificProviderLedgerV3 | None = None
    proposal_ledger: DurableConstructionProposalLedgerV1 | None = None
    outcome_ledger: DurableConstructionOutcomeLedgerV1 | None = None
    direct_ledger: DurableDirectNumberLedgerV1 | None = None
    try:
        integrity_guard.assert_before_e1_access()
        integrity_guard.assert_before_scientific_phase()
        scientific_root = recovery_private_root / "scientific_v3"
        scientific_root.mkdir(exist_ok=False)
        scientific_custody = TransactionalHashChainCustodyV3(
            scientific_root / "provider",
            ledger_kind="scientific_provider",
            allowed_logical_call_kind="scientific",
        )
        provider_ledger = TransactionalScientificProviderLedgerV3(
            scientific_custody,
            attempt_supplier=lambda: guarded_transport.attempt_custody[attempt_start:],
        )
        proposal_ledger = DurableConstructionProposalLedgerV1(
            scientific_root / "proposals_working.jsonl"
        )
        outcome_ledger = DurableConstructionOutcomeLedgerV1(
            scientific_root / "outcomes_working.jsonl"
        )
        direct_ledger = DurableDirectNumberLedgerV1(
            scientific_root / "direct_working.jsonl"
        )
    except Exception as failure:
        if not public_output_root.exists():
            public_output_root.mkdir()
        context = _failure_context_from_state(
            execution_commit=execution_commit,
            source_manifest_hash=source_manifest_hash,
            authorization_hash=r2_authorization_hash,
            configuration_fingerprint=integrity_guard.checks[-1].execution_configuration_fingerprint,
            capability_gate_status=execution.gate.gate_status,
            capability_custody=capability_custody,
            scientific_custody=scientific_custody,
            proposal_records=proposal_ledger.records if proposal_ledger else (),
            outcome_records=outcome_ledger.records if outcome_ledger else (),
            direct_records=direct_ledger.records if direct_ledger else (),
            transport_attempts=len(guarded_transport.attempt_custody) - attempt_start,
            integrity_guard=integrity_guard,
        )
        try:
            receipt = write_terminal_failure_receipt_v3(
                destination=public_output_root / "TASK-039E3_R2_EXECUTION_FAILURE.json",
                failure_stage="before_e1_or_scientific_setup",
                failure=failure,
                context=context,
            )
        except Exception as persistence_failure:
            raise TASK039E3RecoveryFailureReceiptDoubleFaultV3Error(
                failure, persistence_failure
            ) from failure
        raise TASK039E3RecoveryGuardedExecutionFailureV3Error(
            failure, receipt
        ) from failure

    assert scientific_custody is not None
    assert provider_ledger is not None
    assert proposal_ledger is not None
    assert outcome_ledger is not None
    assert direct_ledger is not None

    def execute_science() -> Any:
        try:
            return scientific_runner(
                authority=PostCapabilityAuthorityV2(
                    gate_status="PASS",
                    capability_custody_frozen=True,
                    capability_receipt_durable=capability_receipt_path.is_file(),
                    capability_receipt_hash=capability_receipt["artifact_hash"],
                ),
                e1_private_root=e1_private_root,
                public_cohort=public_cohort,
                relation_identities=relation_identities,
                transport=guarded_transport,
                ledgers=ScientificLedgersV2(
                    provider=provider_ledger,
                    proposal=proposal_ledger,
                    outcome=outcome_ledger,
                    direct_number=direct_ledger,
                ),
                progress=lambda message: (
                    integrity_guard.assert_at_relation_boundary(), progress(message)
                )[-1],
            )
        finally:
            provider_ledger.close()
            proposal_ledger.close()
            outcome_ledger.close()
            direct_ledger.close()

    def finalize_success(scientific_result: Any) -> FinalizedScientificResultV3:
        integrity_guard.assert_before_metrics_finalization()
        scientific_attempts = len(guarded_transport.attempt_custody) - attempt_start
        accounting = build_typed_accounting_v3(
            capability_attempts=execution.transport_attempts,
            scientific_result=scientific_result,
            scientific_transport_attempts=scientific_attempts,
        )
        integrity_guard.assert_before_public_finalization()
        def guarded_artifact_writer(
            path: str | Path, document: Mapping[str, Any]
        ) -> dict[str, Any]:
            destination = Path(path)
            if destination.name == PUBLIC_ARTIFACT_NAMES_V3["execution_receipt"]:
                integrity_guard.assert_before_terminal_pass()
            else:
                integrity_guard.assert_integrity("before_authoritative_artifact_write")
            return write_public_artifact_atomic_v1(destination, document)

        result = success_finalizer(
            repository_root=repository_root,
            recovery_private_root=recovery_private_root,
            public_output_root=public_output_root,
            protected_private_roots=(e1_private_root, historical_e3_private_root),
            execution_commit=execution_commit,
            source_manifest_hash=source_manifest_hash,
            authorization_hash=r2_authorization_hash,
            configuration_fingerprint=integrity_guard.checks[-1].execution_configuration_fingerprint,
            postcontact_integrity_status="verified_unchanged",
            authority_bindings=authority_bindings,
            capability_receipt=capability_receipt,
            capability_provider_binding=provider_custody_binding_from_reconstruction_v3(
                capability_custody.reconstruct()
            ),
            scientific_provider_binding=provider_custody_binding_from_reconstruction_v3(
                scientific_custody.reconstruct()
            ),
            scientific_provider_records=[record["payload"] for record in scientific_custody.records],
            proposal_records=proposal_ledger.records,
            outcome_records=outcome_ledger.records,
            direct_number_records=direct_ledger.records,
            typed_accounting=accounting,
            scientific_source_hashes=scientific_source_hashes,
            artifact_writer=guarded_artifact_writer,
        )
        receipt_path = public_output_root / "TASK-039E3_R2_EXECUTION_RECEIPT.json"
        if not receipt_path.is_file():
            raise TASK039E3RecoveryExecutionV3Error("terminal PASS receipt is absent")
        verify_public_artifact_v1(json.loads(receipt_path.read_text(encoding="utf-8")))
        return result

    failure_destination = public_output_root / "TASK-039E3_R2_EXECUTION_FAILURE.json"
    if not public_output_root.exists():
        public_output_root.mkdir()
    finalized = run_guarded_execution_v3(
        provider_contact_started=integrity_guard.provider_contact_started,
        execution_stage="scientific_execution_or_finalization",
        execute_science=execute_science,
        finalize_success=finalize_success,
        failure_receipt_writer=lambda **kwargs: write_terminal_failure_receipt_v3(
            destination=failure_destination, **kwargs
        ),
        failure_context=lambda: _failure_context_from_state(
            execution_commit=execution_commit,
            source_manifest_hash=source_manifest_hash,
            authorization_hash=r2_authorization_hash,
            configuration_fingerprint=integrity_guard.checks[-1].execution_configuration_fingerprint,
            capability_gate_status=execution.gate.gate_status,
            capability_custody=capability_custody,
            scientific_custody=scientific_custody,
            proposal_records=proposal_ledger.records,
            outcome_records=outcome_ledger.records,
            direct_records=direct_ledger.records,
            transport_attempts=len(guarded_transport.attempt_custody) - attempt_start,
            integrity_guard=integrity_guard,
        ),
    )
    return {
        "status": finalized.status,
        "execution_receipt_hash": finalized.execution_receipt_hash,
        "capability_receipt": capability_receipt,
        "local_compatibility_slots": 0,
    }


def _verify_artifact(path: Path, expected_hash: str) -> Mapping[str, Any]:
    document = json.loads(path.read_text(encoding="utf-8"))
    field = "artifact_hash" if "artifact_hash" in document else "self_hash"
    content = {key: value for key, value in document.items() if key != field}
    if document.get(field) != expected_hash or stable_hash_v1(content) != expected_hash:
        raise TASK039E3RecoveryExecutionV3Error(f"artifact binding differs: {path.name}")
    return document


def load_prior_authority_state_v3(repository_root: Path) -> PriorAuthorityStateV3:
    reports = repository_root / "docs" / "task_reports"
    _verify_artifact(reports / "TASK-039E3_R0_RECEIPT.json", R0_BUNDLE_HASH)
    _verify_artifact(reports / "TASK-039E3_R1A_TIMEOUT_AUTHORITY.json", R1A_TIMEOUT_AUTHORITY_HASH)
    _verify_artifact(reports / "TASK-039E3_R1C_SOURCE_FREEZE.json", R1C_SOURCE_MANIFEST_HASH)
    _verify_artifact(reports / "TASK-039E3_R1C_IMPLEMENTATION_RECEIPT.json", R1C_IMPLEMENTATION_RECEIPT_HASH)
    _verify_artifact(reports / "TASK-039E3_R1C_AUDIT_RECEIPT.json", R1C_AUDIT_RECEIPT_HASH)
    custody = _verify_artifact(
        reports / "TASK-039E3_R1C_AUDIT_CUSTODY_ACCOUNTING.json",
        CORRECTED_CUSTODY_ACCOUNTING_HASH,
    )
    if custody.get("artifact_hash") != CORRECTED_CUSTODY_ACCOUNTING_HASH:
        raise TASK039E3RecoveryExecutionV3Error("corrected custody authority differs")
    _verify_artifact(reports / "TASK-039E3_R1D_BLOCKED_PREFLIGHT.json", HISTORICAL_BLOCKED_R1D_PREFLIGHT_HASH)
    _verify_artifact(reports / "TASK-039E3_R1D_IMPLEMENTATION_RECEIPT.json", HISTORICAL_BLOCKED_R1D_IMPLEMENTATION_RECEIPT_HASH)
    _verify_artifact(reports / "TASK-039E3_R1D_DATA_ACCESS_AUDIT.json", HISTORICAL_BLOCKED_R1D_DATA_ACCESS_AUDIT_HASH)
    return PriorAuthorityStateV3(
        R0_COMMIT,
        R0_BUNDLE_HASH,
        R1A_COMMIT,
        R1A_TIMEOUT_AUTHORITY_HASH,
        R1B_COMMIT_A,
        R1B_COMMIT_B,
        R1C_COMMIT_A,
        R1C_COMMIT_B,
        R1C_SOURCE_MANIFEST_HASH,
        R1C_IMPLEMENTATION_RECEIPT_HASH,
        R1C_REMEDIATION_BUNDLE_HASH,
        R1C_AUDIT_COMMIT_B,
        R1C_INDEPENDENT_AUDIT_BUNDLE_HASH,
        R1C_AUDIT_RECEIPT_HASH,
        CORRECTED_CUSTODY_ACCOUNTING_HASH,
        HISTORICAL_BLOCKED_R1D_COMMIT,
        HISTORICAL_BLOCKED_R1D_PREFLIGHT_HASH,
        HISTORICAL_BLOCKED_R1D_IMPLEMENTATION_RECEIPT_HASH,
        HISTORICAL_BLOCKED_R1D_DATA_ACCESS_AUDIT_HASH,
    )


def collect_git_execution_state_v3(
    repository_root: Path, source_manifest: Mapping[str, Any]
) -> GitExecutionStateV3:
    manifest = verify_public_artifact_v1(source_manifest)

    def run(*args: str, text: bool = True) -> Any:
        return subprocess.run(
            ["git", *args], cwd=repository_root, check=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=text,
        ).stdout

    head = run("rev-parse", "HEAD").strip()
    status = run("status", "--porcelain=v1")
    index_clean = subprocess.run(
        ["git", "diff", "--cached", "--quiet"], cwd=repository_root, check=False
    ).returncode == 0
    records = manifest.get("source_records")
    matched = isinstance(records, list) and bool(records)
    if matched:
        for record in records:
            if not isinstance(record, Mapping) or not isinstance(record.get("repository_path"), str):
                matched = False
                break
            path = str(record["repository_path"])
            blob = run("rev-parse", f"{head}:{path}").strip()
            data = run("show", f"{head}:{path}", text=False)
            if blob != record.get("git_blob_sha") or sha256(data).hexdigest() != record.get("sha256"):
                matched = False
                break
    return GitExecutionStateV3(
        head_commit=head,
        worktree_clean=not bool(status),
        index_clean=index_clean,
        source_manifest_hash=str(manifest["artifact_hash"]),
        source_blobs_match_manifest=matched,
    )


__all__ = [
    "IntegrityGuardedTransportV3",
    "RecoveryCapabilityExecutionV3",
    "TASK039E3RecoveryExecutionV3Error",
    "TASK039E3RecoveryFailureReceiptDoubleFaultV3Error",
    "TASK039E3RecoveryGuardedExecutionFailureV3Error",
    "TASK039E3RecoveryScientificAbortV3Error",
    "TransactionalProviderRecordV3",
    "TransactionalScientificProviderLedgerV3",
    "build_recovery_capability_receipt_v3",
    "build_typed_accounting_v3",
    "collect_git_execution_state_v3",
    "execute_recovery_capability_probe_v3",
    "freeze_capability_custody_v3",
    "load_prior_authority_state_v3",
    "run_capability_then_science_v3",
    "run_guarded_execution_v3",
    "write_terminal_failure_receipt_v3",
]
