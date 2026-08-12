"""Typed provider custody for the TASK-039E3 recovery V2 path.

Capability and scientific provider activity are deliberately represented by
different ledger types.  A capability attempt can therefore never cancel a
scientific slot (or a former local compatibility slot) in retry accounting.
All records in these ledgers describe real provider transport activity; the
R1B local compatibility acknowledgement is not representable here.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
import re
from typing import Any, Callable, Mapping, Sequence

from paperworks.v6.common import freeze_json, stable_hash_v1, thaw_json
from paperworks.v6.task039e3_execution_prep_v1 import ProviderCallSlotV1


HISTORICAL_CAPABILITY_PROBES = 1
MAXIMUM_ADDITIONAL_RECOVERY_PROBES = 1
MAXIMUM_CUMULATIVE_CAPABILITY_PROBES = 2
LOCAL_COMPATIBILITY_SLOTS = 0
_HASH_RE = re.compile(r"^[a-f0-9]{64}$")
_MODEL_MISMATCH_OUTCOME = "model_identity_integrity"
_MODEL_MISMATCH_TERMINAL = "completed_model_identity_mismatch"
_ALLOWED_LOGICAL_CALL_KINDS = frozenset({"recovery_capability", "scientific"})


class TASK039E3RecoveryCustodyV2Error(ValueError):
    """Raised when V2 custody or typed accounting violates its contract."""


class ScientificModelIdentityMismatchAbortV2(TASK039E3RecoveryCustodyV2Error):
    """Fail-closed abort raised only after mismatch custody is durable."""

    def __init__(self, record: "ProviderCustodyRecordV2", ledger_hash: str) -> None:
        super().__init__("model_identity_mismatch_full_scientific_run_failure")
        self.record = record
        self.provider_ledger_hash = ledger_hash
        self.actual_returned_model = record.returned_model
        self.actual_response_id = record.response_id
        self.automatic_resume_authorized = False


def _require_hash(value: str, label: str) -> str:
    if not isinstance(value, str) or _HASH_RE.fullmatch(value) is None:
        raise TASK039E3RecoveryCustodyV2Error(f"{label} must be a SHA-256 digest")
    return value


def _plain_attempt(value: Any) -> Mapping[str, Any]:
    if isinstance(value, Mapping):
        return value
    to_dict = getattr(value, "to_dict", None)
    if callable(to_dict):
        document = to_dict()
        if isinstance(document, Mapping):
            return document
    raise TASK039E3RecoveryCustodyV2Error("provider attempt is not serializable")


def _first(document: Mapping[str, Any], *names: str) -> Any:
    for name in names:
        if name in document:
            return document[name]
    return None


@dataclass(frozen=True)
class ProviderTransportAttemptCustodyV2:
    """One actual provider transport attempt, never a local acknowledgement."""

    attempt_number: int
    request_hash: str
    response_origin: str
    provider_contacted: bool
    provider_authored_response: bool
    status_code: int | None
    outcome: str
    response_present: bool
    returned_model: str | None
    response_id: str | None
    finish_reason: str | None
    usage: Mapping[str, int] | None
    system_fingerprint: str | None
    retry_eligible: bool
    actual_retry_delay_seconds: float | None
    retry_after_observed: float | None

    def __post_init__(self) -> None:
        if self.attempt_number not in {1, 2, 3}:
            raise TASK039E3RecoveryCustodyV2Error("transport attempt number differs")
        _require_hash(self.request_hash, "request hash")
        if self.response_origin != "provider" or self.provider_contacted is not True:
            raise TASK039E3RecoveryCustodyV2Error(
                "V2 custody accepts actual provider attempts only"
            )
        if not isinstance(self.outcome, str) or not self.outcome:
            raise TASK039E3RecoveryCustodyV2Error("transport outcome differs")
        if self.response_present and not self.provider_authored_response:
            raise TASK039E3RecoveryCustodyV2Error(
                "present response must be identified as provider-authored"
            )
        if self.outcome == _MODEL_MISMATCH_OUTCOME:
            if not self.response_present or not self.returned_model or not self.response_id:
                raise TASK039E3RecoveryCustodyV2Error(
                    "model mismatch custody must preserve model and response ID"
                )
            if self.retry_eligible:
                raise TASK039E3RecoveryCustodyV2Error("model mismatch cannot retry")
        if self.usage is not None:
            object.__setattr__(self, "usage", freeze_json(self.usage))

    @classmethod
    def from_value(
        cls,
        value: Any,
        *,
        request_hash: str,
        fallback_attempt_number: int,
        terminal_metadata: Mapping[str, Any],
    ) -> "ProviderTransportAttemptCustodyV2":
        document = _plain_attempt(value)
        attempt_number = _first(document, "attempt_number")
        if attempt_number is None:
            attempt_number = fallback_attempt_number
        response_present = bool(document.get("response_present", False))
        outcome = str(document.get("outcome", ""))
        is_terminal = bool(response_present or not document.get("retry_eligible", False))
        returned_model = _first(document, "returned_model", "model")
        response_id = document.get("response_id")
        finish_reason = document.get("finish_reason")
        usage = _first(document, "usage", "token_usage")
        if is_terminal:
            returned_model = returned_model or terminal_metadata.get("model")
            response_id = response_id or terminal_metadata.get("response_id")
            finish_reason = finish_reason or terminal_metadata.get("finish_reason")
            usage = usage or terminal_metadata.get("token_usage")
        provider_authored = document.get("provider_authored_response")
        if provider_authored is None:
            provider_authored = response_present or document.get("status_code") is not None
        return cls(
            attempt_number=int(attempt_number),
            request_hash=str(document.get("request_hash", request_hash)),
            response_origin=str(document.get("response_origin", "provider")),
            provider_contacted=bool(document.get("provider_contacted", True)),
            provider_authored_response=bool(provider_authored),
            status_code=(
                int(document["status_code"])
                if document.get("status_code") is not None
                else None
            ),
            outcome=outcome,
            response_present=response_present,
            returned_model=str(returned_model) if returned_model is not None else None,
            response_id=str(response_id) if response_id is not None else None,
            finish_reason=str(finish_reason) if finish_reason is not None else None,
            usage=(dict(usage) if isinstance(usage, Mapping) else None),
            system_fingerprint=(
                str(document["system_fingerprint"])
                if document.get("system_fingerprint") is not None
                else None
            ),
            retry_eligible=bool(document.get("retry_eligible", False)),
            actual_retry_delay_seconds=(
                float(_first(
                    document,
                    "actual_retry_delay_seconds",
                    "actual_retry_delay_before_attempt_seconds",
                ))
                if _first(
                    document,
                    "actual_retry_delay_seconds",
                    "actual_retry_delay_before_attempt_seconds",
                ) is not None
                else None
            ),
            retry_after_observed=(
                float(_first(
                    document,
                    "retry_after_observed",
                    "retry_after_seconds_observed",
                ))
                if _first(
                    document,
                    "retry_after_observed",
                    "retry_after_seconds_observed",
                ) is not None
                else None
            ),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "attempt_number": self.attempt_number,
            "request_hash": self.request_hash,
            "response_origin": self.response_origin,
            "provider_contacted": self.provider_contacted,
            "provider_authored_response": self.provider_authored_response,
            "status_code": self.status_code,
            "outcome": self.outcome,
            "response_present": self.response_present,
            "returned_model": self.returned_model,
            "response_id": self.response_id,
            "finish_reason": self.finish_reason,
            "usage": thaw_json(self.usage),
            "system_fingerprint": self.system_fingerprint,
            "retry_eligible": self.retry_eligible,
            "actual_retry_delay_seconds": self.actual_retry_delay_seconds,
            "retry_after_observed": self.retry_after_observed,
        }


@dataclass(frozen=True)
class ProviderCustodyRecordV2:
    sequence_index: int
    previous_record_hash: str | None
    logical_call_kind: str
    slot: ProviderCallSlotV1
    request_hash: str
    response_origin: str
    provider_contacted: bool
    provider_authored_response: bool
    response_present: bool
    returned_model: str | None
    response_id: str | None
    finish_reason: str | None
    usage: Mapping[str, int] | None
    system_fingerprint: str | None
    transport_attempts: tuple[ProviderTransportAttemptCustodyV2, ...]
    parse_status: str
    proposal_core_hash: str | None
    terminal_slot_state: str
    api_key_stored: bool = False
    authorization_header_stored: bool = False
    chain_of_thought_stored: bool = False

    def __post_init__(self) -> None:
        if self.sequence_index < 0:
            raise TASK039E3RecoveryCustodyV2Error("record sequence differs")
        if self.previous_record_hash is not None:
            _require_hash(self.previous_record_hash, "previous record hash")
        _require_hash(self.request_hash, "request hash")
        if self.proposal_core_hash is not None:
            _require_hash(self.proposal_core_hash, "proposal core hash")
        if self.logical_call_kind not in _ALLOWED_LOGICAL_CALL_KINDS:
            raise TASK039E3RecoveryCustodyV2Error("logical call kind differs")
        if self.response_origin != "provider" or self.provider_contacted is not True:
            raise TASK039E3RecoveryCustodyV2Error("provider provenance differs")
        if not self.transport_attempts or len(self.transport_attempts) > 3:
            raise TASK039E3RecoveryCustodyV2Error("transport attempt custody differs")
        if self.logical_call_kind == "scientific" and self.slot.scientific is not True:
            raise TASK039E3RecoveryCustodyV2Error("scientific ledger slot differs")
        if self.logical_call_kind == "recovery_capability" and self.slot.scientific:
            raise TASK039E3RecoveryCustodyV2Error("capability ledger slot differs")
        if self.terminal_slot_state == _MODEL_MISMATCH_TERMINAL:
            if not self.returned_model or not self.response_id:
                raise TASK039E3RecoveryCustodyV2Error(
                    "model mismatch record lost provider metadata"
                )
        if any(
            getattr(self, name) is not False
            for name in (
                "api_key_stored",
                "authorization_header_stored",
                "chain_of_thought_stored",
            )
        ):
            raise TASK039E3RecoveryCustodyV2Error("prohibited custody content")
        if self.usage is not None:
            object.__setattr__(self, "usage", freeze_json(self.usage))

    def _content_dict(self) -> dict[str, Any]:
        return {
            "sequence_index": self.sequence_index,
            "previous_record_hash": self.previous_record_hash,
            "logical_call_kind": self.logical_call_kind,
            "slot": self.slot.to_dict(),
            "slot_hash": self.slot.slot_hash,
            "request_hash": self.request_hash,
            "response_origin": self.response_origin,
            "provider_contacted": self.provider_contacted,
            "provider_authored_response": self.provider_authored_response,
            "response_present": self.response_present,
            "returned_model": self.returned_model,
            "response_id": self.response_id,
            "finish_reason": self.finish_reason,
            "usage": thaw_json(self.usage),
            "system_fingerprint": self.system_fingerprint,
            "transport_attempts": [item.to_dict() for item in self.transport_attempts],
            "parse_status": self.parse_status,
            "proposal_core_hash": self.proposal_core_hash,
            "terminal_slot_state": self.terminal_slot_state,
            "api_key_stored": self.api_key_stored,
            "authorization_header_stored": self.authorization_header_stored,
            "chain_of_thought_stored": self.chain_of_thought_stored,
        }

    @property
    def provider_response_metadata(self) -> Mapping[str, Any]:
        return freeze_json(
            {
                "outcome": self.transport_attempts[-1].outcome,
                "status_code": self.transport_attempts[-1].status_code,
                "model": self.returned_model,
                "response_id": self.response_id,
                "finish_reason": self.finish_reason,
                "token_usage": thaw_json(self.usage),
                "system_fingerprint": self.system_fingerprint,
                "response_origin": self.response_origin,
                "provider_contacted": self.provider_contacted,
                "provider_authored_response": self.provider_authored_response,
                "logical_call_kind": self.logical_call_kind,
            }
        )

    @property
    def record_hash(self) -> str:
        return stable_hash_v1(self._content_dict())

    def to_dict(self) -> dict[str, Any]:
        document = self._content_dict()
        document["record_hash"] = self.record_hash
        return document


AttemptSupplierV2 = Callable[[], Sequence[Any]]


class _TypedProviderLedgerV2:
    _logical_call_kind: str
    _artifact_type: str

    def __init__(
        self,
        path: Path | None = None,
        *,
        attempt_supplier: AttemptSupplierV2 | None = None,
        abort_on_model_mismatch: bool = False,
    ) -> None:
        if path is not None and path.exists():
            raise TASK039E3RecoveryCustodyV2Error("provider ledger path must be new")
        self._path = path
        self._attempt_supplier = attempt_supplier
        self._attempt_cursor = 0
        self._abort_on_model_mismatch = abort_on_model_mismatch
        self._records: list[ProviderCustodyRecordV2] = []
        self._slot_hashes: set[str] = set()

    @property
    def records(self) -> tuple[ProviderCustodyRecordV2, ...]:
        return tuple(self._records)

    @property
    def ledger_hash(self) -> str:
        return stable_hash_v1(
            {
                "artifact_type": self._artifact_type,
                "record_hashes": [item.record_hash for item in self._records],
            }
        )

    @property
    def provider_ledger_head_hash(self) -> str | None:
        return self._records[-1].record_hash if self._records else None

    def _detailed_attempt_slice(self, fallback: Sequence[Any]) -> Sequence[Any]:
        if self._attempt_supplier is None:
            return fallback
        supplied = tuple(self._attempt_supplier())
        if len(supplied) < self._attempt_cursor:
            raise TASK039E3RecoveryCustodyV2Error("attempt supplier moved backwards")
        result = supplied[self._attempt_cursor :]
        self._attempt_cursor = len(supplied)
        if len(result) != len(fallback):
            raise TASK039E3RecoveryCustodyV2Error("attempt supplier slice differs")
        return result

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
    ) -> ProviderCustodyRecordV2:
        if slot.slot_hash in self._slot_hashes:
            raise TASK039E3RecoveryCustodyV2Error("provider slot was already recorded")
        if self._logical_call_kind == "scientific" and not slot.scientific:
            raise TASK039E3RecoveryCustodyV2Error("non-scientific slot in science ledger")
        if self._logical_call_kind == "recovery_capability" and slot.scientific:
            raise TASK039E3RecoveryCustodyV2Error("scientific slot in capability ledger")
        detailed = self._detailed_attempt_slice(transport_attempts)
        attempts = tuple(
            ProviderTransportAttemptCustodyV2.from_value(
                value,
                request_hash=request_hash,
                fallback_attempt_number=index,
                terminal_metadata=provider_response_metadata,
            )
            for index, value in enumerate(detailed, 1)
        )
        terminal = attempts[-1]
        mismatch = terminal.outcome == _MODEL_MISMATCH_OUTCOME
        if mismatch:
            terminal_slot_state = _MODEL_MISMATCH_TERMINAL
            parse_status = "model_identity_mismatch"
        record = ProviderCustodyRecordV2(
            sequence_index=len(self._records),
            previous_record_hash=(self._records[-1].record_hash if self._records else None),
            logical_call_kind=self._logical_call_kind,
            slot=slot,
            request_hash=request_hash,
            response_origin="provider",
            provider_contacted=True,
            provider_authored_response=terminal.provider_authored_response,
            response_present=response_present,
            returned_model=terminal.returned_model,
            response_id=terminal.response_id,
            finish_reason=terminal.finish_reason,
            usage=thaw_json(terminal.usage),
            system_fingerprint=terminal.system_fingerprint,
            transport_attempts=attempts,
            parse_status=parse_status,
            proposal_core_hash=proposal_core_hash,
            terminal_slot_state=terminal_slot_state,
        )
        self._persist(record)
        self._records.append(record)
        self._slot_hashes.add(slot.slot_hash)
        if mismatch and self._logical_call_kind == "scientific" and self._abort_on_model_mismatch:
            raise ScientificModelIdentityMismatchAbortV2(record, self.ledger_hash)
        return record

    def _persist(self, record: ProviderCustodyRecordV2) -> None:
        if self._path is None:
            return
        self._path.parent.mkdir(parents=True, exist_ok=True)
        mode = "x" if not self._records else "a"
        try:
            with self._path.open(mode, encoding="utf-8", newline="\n") as handle:
                json.dump(
                    record.to_dict(),
                    handle,
                    ensure_ascii=True,
                    allow_nan=False,
                    sort_keys=True,
                    separators=(",", ":"),
                )
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
        except OSError as exc:
            raise TASK039E3RecoveryCustodyV2Error(
                "provider custody could not be durably frozen"
            ) from exc

    def close(self) -> None:
        """Compatibility no-op: each append is independently flushed and closed."""


class RecoveryCapabilityProviderLedgerV2(_TypedProviderLedgerV2):
    """Ledger for the single real corrected recovery capability call only."""

    _logical_call_kind = "recovery_capability"
    _artifact_type = "task039e3_recovery_capability_provider_ledger_v2"

    def append(self, **kwargs: Any) -> ProviderCustodyRecordV2:
        if self.records:
            raise TASK039E3RecoveryCustodyV2Error(
                "only one additional recovery capability probe is permitted"
            )
        return super().append(**kwargs)


class ScientificProviderLedgerV2(_TypedProviderLedgerV2):
    """ProviderCallLedgerV1-compatible ledger containing scientific slots only."""

    _logical_call_kind = "scientific"
    _artifact_type = "task039e3_scientific_provider_ledger_v2"

    def __init__(
        self,
        path: Path | None = None,
        *,
        attempt_supplier: AttemptSupplierV2 | None = None,
        abort_on_model_mismatch: bool = True,
    ) -> None:
        super().__init__(
            path,
            attempt_supplier=attempt_supplier,
            abort_on_model_mismatch=abort_on_model_mismatch,
        )


@dataclass(frozen=True)
class TypedProviderAccountingV2:
    """Independently typed logical-call and attempt counts; never subtracts families."""

    historical_capability_probes: int
    current_recovery_capability_logical_calls: int
    current_recovery_capability_transport_attempts: int
    current_recovery_capability_transport_retries: int
    scientific_logical_calls: int
    scientific_transport_attempts: int
    scientific_transport_retries: int
    local_compatibility_slots: int
    cumulative_real_provider_capability_probes: int
    full_scientific_run_complete: bool = False

    def __post_init__(self) -> None:
        if self.historical_capability_probes != HISTORICAL_CAPABILITY_PROBES:
            raise TASK039E3RecoveryCustodyV2Error("historical probe count differs")
        if self.current_recovery_capability_logical_calls != 1:
            raise TASK039E3RecoveryCustodyV2Error("recovery logical probe count differs")
        if self.current_recovery_capability_transport_attempts not in {1, 2, 3}:
            raise TASK039E3RecoveryCustodyV2Error("capability attempt count differs")
        if self.current_recovery_capability_transport_retries != (
            self.current_recovery_capability_transport_attempts - 1
        ):
            raise TASK039E3RecoveryCustodyV2Error("capability retry count differs")
        if self.scientific_logical_calls < 0:
            raise TASK039E3RecoveryCustodyV2Error("scientific logical calls differ")
        if self.scientific_transport_attempts < self.scientific_logical_calls:
            raise TASK039E3RecoveryCustodyV2Error("scientific attempt count differs")
        if self.scientific_transport_retries != (
            self.scientific_transport_attempts - self.scientific_logical_calls
        ):
            raise TASK039E3RecoveryCustodyV2Error("scientific retry count differs")
        if self.local_compatibility_slots != LOCAL_COMPATIBILITY_SLOTS:
            raise TASK039E3RecoveryCustodyV2Error("local compatibility slots must be zero")
        if self.cumulative_real_provider_capability_probes != (
            self.historical_capability_probes
            + self.current_recovery_capability_logical_calls
        ):
            raise TASK039E3RecoveryCustodyV2Error("cumulative capability count differs")
        if self.full_scientific_run_complete and not (
            252 <= self.scientific_logical_calls <= 336
        ):
            raise TASK039E3RecoveryCustodyV2Error("completed scientific call range differs")

    @property
    def current_run_real_provider_logical_calls(self) -> int:
        return (
            self.current_recovery_capability_logical_calls
            + self.scientific_logical_calls
        )

    @property
    def current_run_provider_transport_attempts(self) -> int:
        return (
            self.current_recovery_capability_transport_attempts
            + self.scientific_transport_attempts
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "historical_capability_probes": self.historical_capability_probes,
            "current_recovery_capability_logical_calls": (
                self.current_recovery_capability_logical_calls
            ),
            "current_recovery_capability_transport_attempts": (
                self.current_recovery_capability_transport_attempts
            ),
            "current_recovery_capability_transport_retries": (
                self.current_recovery_capability_transport_retries
            ),
            "scientific_logical_calls": self.scientific_logical_calls,
            "scientific_transport_attempts": self.scientific_transport_attempts,
            "scientific_transport_retries": self.scientific_transport_retries,
            "local_compatibility_slots": self.local_compatibility_slots,
            "cumulative_real_provider_capability_probes": (
                self.cumulative_real_provider_capability_probes
            ),
            "current_run_real_provider_logical_calls": (
                self.current_run_real_provider_logical_calls
            ),
            "current_run_provider_transport_attempts": (
                self.current_run_provider_transport_attempts
            ),
            "full_scientific_run_complete": self.full_scientific_run_complete,
        }


def build_typed_provider_accounting_v2(
    *,
    capability_transport_attempts: int,
    scientific_logical_calls: int,
    scientific_transport_attempts: int,
    full_scientific_run_complete: bool = False,
) -> TypedProviderAccountingV2:
    """Build typed accounting using only within-family retry subtraction."""

    return TypedProviderAccountingV2(
        historical_capability_probes=HISTORICAL_CAPABILITY_PROBES,
        current_recovery_capability_logical_calls=1,
        current_recovery_capability_transport_attempts=capability_transport_attempts,
        current_recovery_capability_transport_retries=capability_transport_attempts - 1,
        scientific_logical_calls=scientific_logical_calls,
        scientific_transport_attempts=scientific_transport_attempts,
        scientific_transport_retries=(
            scientific_transport_attempts - scientific_logical_calls
        ),
        local_compatibility_slots=LOCAL_COMPATIBILITY_SLOTS,
        cumulative_real_provider_capability_probes=(
            HISTORICAL_CAPABILITY_PROBES + 1
        ),
        full_scientific_run_complete=full_scientific_run_complete,
    )


__all__ = [
    "HISTORICAL_CAPABILITY_PROBES",
    "LOCAL_COMPATIBILITY_SLOTS",
    "MAXIMUM_ADDITIONAL_RECOVERY_PROBES",
    "MAXIMUM_CUMULATIVE_CAPABILITY_PROBES",
    "ProviderCustodyRecordV2",
    "ProviderTransportAttemptCustodyV2",
    "RecoveryCapabilityProviderLedgerV2",
    "ScientificModelIdentityMismatchAbortV2",
    "ScientificProviderLedgerV2",
    "TASK039E3RecoveryCustodyV2Error",
    "TypedProviderAccountingV2",
    "build_typed_provider_accounting_v2",
]
