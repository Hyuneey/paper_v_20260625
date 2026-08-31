"""Fail-closed EXP-03 construction comparison contracts.

This module is deliberately transport-free.  It freezes the terminal taxonomy,
arm budgets, receipts, schedules, and natural/stress aggregation boundaries
needed before DG-03.  No function reads credentials, opens a network
connection, or accesses scientific data.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum
import math
import re
from typing import Iterable, Mapping, Sequence

from paperworks.v6.common import stable_hash_v1


EXP03_VERSION = "1.0.0"
NATURAL_NAMESPACE = "VALIDATION_V2_EXP03_NATURAL"
STRESS_NAMESPACE = "VALIDATION_V2_EXP03_SYNTHETIC_STRESS"
STOCHASTIC_REPEATS = (1, 2, 3)
T1B_DRAWS = (1, 2, 3)
MAX_PROVIDER_CALLS_PER_RELATION = 21
SEMANTIC_NO_RULE_OUTCOMES = (
    "INTENTIONAL_NO_RULE",
    "UNSUPPORTED_EVIDENCE",
)
NEVER_NO_RULE_OUTCOMES = (
    "PROVIDER_ERROR",
    "EMPTY_RESPONSE",
    "PARSE_FAILURE",
    "VERIFIER_REJECTION",
    "BUDGET_EXHAUSTION",
    "RETRIEVAL_FAILURE",
    "SYSTEM_ERROR",
)

_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]*$")


class Exp03ContractError(ValueError):
    """A closed EXP-03 contract failed validation."""

    def __init__(self, issue_code: str, message: str) -> None:
        super().__init__(f"{issue_code}: {message}")
        self.issue_code = issue_code


def _fail(code: str, message: str) -> None:
    raise Exp03ContractError(code, message)


def _text(value: object, name: str) -> str:
    if type(value) is not str or not value:
        _fail("EXP03_TEXT_INVALID", f"{name} must be a non-empty exact string")
    return value


def _identifier(value: object, name: str) -> str:
    result = _text(value, name)
    if _SAFE_ID.fullmatch(result) is None or result in {".", ".."}:
        _fail("EXP03_IDENTIFIER_INVALID", f"{name} must be a safe identifier")
    return result


def _hash(value: object, name: str) -> str:
    result = _text(value, name)
    if _SHA256.fullmatch(result) is None:
        _fail("EXP03_HASH_INVALID", f"{name} must be a lowercase SHA-256")
    return result


def _strict_int(value: object, name: str, *, minimum: int = 0) -> int:
    if type(value) is not int or value < minimum:
        _fail("EXP03_INTEGER_INVALID", f"{name} must be an integer >= {minimum}")
    return value


def _strict_bool(value: object, name: str) -> bool:
    if type(value) is not bool:
        _fail("EXP03_BOOLEAN_INVALID", f"{name} must be an exact Boolean")
    return value


def _finite_nonnegative(value: object, name: str) -> float:
    if type(value) not in {int, float} or isinstance(value, bool):
        _fail("EXP03_NUMBER_INVALID", f"{name} must be a finite number")
    result = float(value)
    if not math.isfinite(result) or result < 0:
        _fail("EXP03_NUMBER_INVALID", f"{name} must be finite and non-negative")
    return result


def _expected_hash(document: Mapping[str, object]) -> str:
    return stable_hash_v1({key: value for key, value in document.items() if key != "self_hash"})


class CohortKindV1(str, Enum):
    NATURAL = "NATURAL"
    SYNTHETIC_STRESS = "SYNTHETIC_STRESS"


class ConstructionArmV1(str, Enum):
    T0 = "T0"
    T1 = "T1"
    T1_B = "T1-B"
    T2 = "T2"


class ConstructionTerminalClassV1(str, Enum):
    INTENTIONAL_NO_RULE = "INTENTIONAL_NO_RULE"
    UNSUPPORTED_EVIDENCE = "UNSUPPORTED_EVIDENCE"
    PROVIDER_ERROR = "PROVIDER_ERROR"
    EMPTY_RESPONSE = "EMPTY_RESPONSE"
    PARSE_FAILURE = "PARSE_FAILURE"
    VERIFIER_REJECTION = "VERIFIER_REJECTION"
    BUDGET_EXHAUSTION = "BUDGET_EXHAUSTION"
    RETRIEVAL_FAILURE = "RETRIEVAL_FAILURE"
    SYSTEM_ERROR = "SYSTEM_ERROR"


class ConstructionOutcomeV1(str, Enum):
    ACCEPTED_PROPOSAL = "ACCEPTED_PROPOSAL"
    ALL_DRAWS_FAILED = "ALL_DRAWS_FAILED"
    INTENTIONAL_NO_RULE = "INTENTIONAL_NO_RULE"
    UNSUPPORTED_EVIDENCE = "UNSUPPORTED_EVIDENCE"
    PROVIDER_ERROR = "PROVIDER_ERROR"
    EMPTY_RESPONSE = "EMPTY_RESPONSE"
    PARSE_FAILURE = "PARSE_FAILURE"
    VERIFIER_REJECTION = "VERIFIER_REJECTION"
    BUDGET_EXHAUSTION = "BUDGET_EXHAUSTION"
    RETRIEVAL_FAILURE = "RETRIEVAL_FAILURE"
    SYSTEM_ERROR = "SYSTEM_ERROR"


TERMINAL_CLASSES = tuple(item.value for item in ConstructionTerminalClassV1)

TERMINAL_REASON_CODES: Mapping[str, str] = {
    "ALL_DRAWS_FAILED": "T1B_ALL_DRAWS_FAILED",
    "INTENTIONAL_NO_RULE": "MODEL_INTENTIONAL_NO_RULE",
    "UNSUPPORTED_EVIDENCE": "PRECONSTRUCTION_EVIDENCE_INELIGIBLE",
    "PROVIDER_ERROR": "PROVIDER_TRANSPORT_OR_REFUSAL",
    "EMPTY_RESPONSE": "EMPTY_OR_INCOMPLETE_STRUCTURED_RESPONSE",
    "PARSE_FAILURE": "STRICT_PARSE_OR_SCHEMA_FAILURE",
    "VERIFIER_REJECTION": "DETERMINISTIC_VERIFIER_REJECTION",
    "BUDGET_EXHAUSTION": "REPAIR_BUDGET_EXHAUSTED",
    "RETRIEVAL_FAILURE": "RETRIEVAL_IDENTITY_OR_INTEGRITY_FAILURE",
    "SYSTEM_ERROR": "LOCAL_SYSTEM_OR_CUSTODY_FAILURE",
}


def provider_call_maximum_v1(relation_count: int) -> int:
    """Return the preregistered 3-repeat maximum: ``21 * N``."""

    return MAX_PROVIDER_CALLS_PER_RELATION * _strict_int(
        relation_count, "relation_count", minimum=1
    )


@dataclass(frozen=True)
class ProviderExecutionAuthorizationV1:
    """Explicit DG-03 decision input; it is not a provider transport."""

    approved: bool
    decision_gate: str
    approval_reference: str
    provider_id: str
    model_snapshot: str
    natural_relation_count: int
    repeat_count: int
    maximum_calls: int
    maximum_input_tokens_per_call: int
    maximum_output_tokens_per_call: int
    maximum_total_tokens: int
    config_hash: str
    evidence_projection_hash: str
    model_policy_hash: str
    template_hash: str
    privacy_assessment_hash: str
    expected_artifact_hash: str
    self_hash: str = ""

    def __post_init__(self) -> None:
        _strict_bool(self.approved, "approved")
        if self.decision_gate != "DG-03":
            _fail("EXP03_DG03_REQUIRED", "provider authorization must be a DG-03 decision")
        for name in ("approval_reference", "provider_id", "model_snapshot"):
            _identifier(getattr(self, name), name)
        _strict_int(self.natural_relation_count, "natural_relation_count", minimum=1)
        if self.repeat_count != 3:
            _fail("EXP03_REPEAT_POLICY_CHANGED", "EXP-03 uses exactly three stochastic repeats")
        if self.maximum_calls != provider_call_maximum_v1(self.natural_relation_count):
            _fail("EXP03_CALL_CAP_INVALID", "maximum_calls must equal 21N")
        for name in (
            "maximum_input_tokens_per_call",
            "maximum_output_tokens_per_call",
            "maximum_total_tokens",
        ):
            _strict_int(getattr(self, name), name, minimum=1)
        per_call = self.maximum_input_tokens_per_call + self.maximum_output_tokens_per_call
        if self.maximum_total_tokens > self.maximum_calls * per_call:
            _fail("EXP03_TOKEN_CAP_INVALID", "total token cap exceeds the call-level hard bound")
        for name in (
            "config_hash",
            "evidence_projection_hash",
            "model_policy_hash",
            "template_hash",
            "privacy_assessment_hash",
            "expected_artifact_hash",
        ):
            _hash(getattr(self, name), name)
        if self.self_hash:
            _hash(self.self_hash, "self_hash")
            if self.self_hash != _expected_hash(self.to_dict()):
                _fail("EXP03_AUTHORIZATION_REPLAY_MISMATCH", "DG-03 authorization mutated")

    def to_dict(self) -> dict[str, object]:
        return {
            "schema": "paperworks.validation_v2.exp03_provider_authorization_v1",
            "schema_version": EXP03_VERSION,
            "approved": self.approved,
            "decision_gate": self.decision_gate,
            "approval_reference": self.approval_reference,
            "provider_id": self.provider_id,
            "model_snapshot": self.model_snapshot,
            "natural_relation_count": self.natural_relation_count,
            "repeat_count": self.repeat_count,
            "maximum_calls": self.maximum_calls,
            "maximum_input_tokens_per_call": self.maximum_input_tokens_per_call,
            "maximum_output_tokens_per_call": self.maximum_output_tokens_per_call,
            "maximum_total_tokens": self.maximum_total_tokens,
            "config_hash": self.config_hash,
            "evidence_projection_hash": self.evidence_projection_hash,
            "model_policy_hash": self.model_policy_hash,
            "template_hash": self.template_hash,
            "privacy_assessment_hash": self.privacy_assessment_hash,
            "expected_artifact_hash": self.expected_artifact_hash,
            "self_hash": self.self_hash,
        }


def build_provider_execution_authorization_v1(
    *,
    dg03_approved: bool,
    approval_reference: str,
    provider_id: str,
    model_snapshot: str,
    natural_relation_count: int,
    maximum_input_tokens_per_call: int,
    maximum_output_tokens_per_call: int,
    maximum_total_tokens: int,
    config_hash: str,
    evidence_projection_hash: str,
    model_policy_hash: str,
    template_hash: str,
    privacy_assessment_hash: str,
    expected_artifact_hash: str,
) -> ProviderExecutionAuthorizationV1:
    """Materialize an already-approved DG-03 input for receipt tests/runners.

    ``dg03_approved=False`` always fails before credentials or network access.
    """

    if type(dg03_approved) is not bool or not dg03_approved:
        _fail("EXP03_PROVIDER_NOT_AUTHORIZED", "DG-03 approval is required before any provider attempt")
    provisional = ProviderExecutionAuthorizationV1(
        approved=True,
        decision_gate="DG-03",
        approval_reference=approval_reference,
        provider_id=provider_id,
        model_snapshot=model_snapshot,
        natural_relation_count=natural_relation_count,
        repeat_count=3,
        maximum_calls=provider_call_maximum_v1(natural_relation_count),
        maximum_input_tokens_per_call=maximum_input_tokens_per_call,
        maximum_output_tokens_per_call=maximum_output_tokens_per_call,
        maximum_total_tokens=maximum_total_tokens,
        config_hash=config_hash,
        evidence_projection_hash=evidence_projection_hash,
        model_policy_hash=model_policy_hash,
        template_hash=template_hash,
        privacy_assessment_hash=privacy_assessment_hash,
        expected_artifact_hash=expected_artifact_hash,
    )
    return replace(provisional, self_hash=_expected_hash(provisional.to_dict()))


@dataclass(frozen=True)
class ProviderInputProjectionV1:
    """Closed, aggregate-only model-visible relation projection."""

    relation_id: str
    source_id: str
    target_id: str
    source_direction: str
    target_direction: str
    selected_horizon_seconds: int
    numeric_reference_ids: tuple[str, ...]
    normal_evidence_summary_hash: str
    config_hash: str
    evidence_projection_hash: str
    model_policy_hash: str
    template_hash: str
    self_hash: str = ""

    def to_dict(self) -> dict[str, object]:
        return {
            "schema": "paperworks.validation_v2.exp03_provider_input_projection_v1",
            "schema_version": EXP03_VERSION,
            **{**self.__dict__, "numeric_reference_ids": list(self.numeric_reference_ids)},
        }


def build_provider_input_projection_v1(
    payload: Mapping[str, object], authorization: ProviderExecutionAuthorizationV1
) -> ProviderInputProjectionV1:
    """Validate a closed provider-visible projection without reading raw data."""

    _validate_authorization(authorization)
    allowed = {
        "relation_id", "source_id", "target_id", "source_direction", "target_direction",
        "selected_horizon_seconds", "numeric_reference_ids", "normal_evidence_summary_hash",
    }
    if type(payload) is not dict or set(payload) != allowed:
        _fail(
            "EXP03_PROVIDER_PROJECTION_CLOSED_FIELD_VIOLATION",
            "provider projection has missing or prohibited fields",
        )
    relation = _identifier(payload["relation_id"], "relation_id")
    source = _identifier(payload["source_id"], "source_id")
    target = _identifier(payload["target_id"], "target_id")
    if source == target:
        _fail("EXP03_PROVIDER_PROJECTION_SELF_RELATION", "source and target must differ")
    source_direction = _text(payload["source_direction"], "source_direction")
    target_direction = _text(payload["target_direction"], "target_direction")
    if source_direction not in {"step_up", "step_down"} or target_direction not in {"increase", "decrease"}:
        _fail("EXP03_PROVIDER_PROJECTION_DIRECTION_INVALID", "directions are outside the relation family")
    horizon = _strict_int(payload["selected_horizon_seconds"], "selected_horizon_seconds", minimum=1)
    raw_refs = payload["numeric_reference_ids"]
    if type(raw_refs) not in {tuple, list}:
        _fail("EXP03_PROVIDER_PROJECTION_REFERENCE_INVALID", "numeric references must be an ordered sequence")
    refs = tuple(_identifier(item, "numeric_reference_id") for item in raw_refs)
    if not refs or len(refs) != len(set(refs)):
        _fail("EXP03_PROVIDER_PROJECTION_REFERENCE_INVALID", "numeric references must be non-empty and unique")
    summary_hash = _hash(payload["normal_evidence_summary_hash"], "normal_evidence_summary_hash")
    provisional = ProviderInputProjectionV1(
        relation_id=relation,
        source_id=source,
        target_id=target,
        source_direction=source_direction,
        target_direction=target_direction,
        selected_horizon_seconds=horizon,
        numeric_reference_ids=refs,
        normal_evidence_summary_hash=summary_hash,
        config_hash=authorization.config_hash,
        evidence_projection_hash=authorization.evidence_projection_hash,
        model_policy_hash=authorization.model_policy_hash,
        template_hash=authorization.template_hash,
    )
    return replace(provisional, self_hash=_expected_hash(provisional.to_dict()))


def execute_provider_transport_v1(*_args: object, **_kwargs: object) -> None:
    """There is intentionally no real provider transport in the preparation contract."""

    _fail("EXP03_PROVIDER_TRANSPORT_NOT_IMPLEMENTED", "DG-03 receipt contracts do not implement transport")


@dataclass(frozen=True)
class ProviderAttemptReceiptV1:
    authorization_hash: str
    namespace: str
    relation_id: str
    arm: str
    repeat_index: int
    call_index: int
    attempt_index: int
    request_hash: str
    response_hash: str | None
    result_class: str
    provider_id: str
    model_snapshot: str
    config_hash: str
    evidence_projection_hash: str
    model_policy_hash: str
    template_hash: str
    input_tokens: int
    output_tokens: int
    latency_ms: float
    self_hash: str = ""

    def to_dict(self) -> dict[str, object]:
        return {
            "schema": "paperworks.validation_v2.exp03_provider_attempt_receipt_v1",
            "schema_version": EXP03_VERSION,
            **self.__dict__,
        }


def _validate_authorization(authorization: ProviderExecutionAuthorizationV1) -> None:
    if type(authorization) is not ProviderExecutionAuthorizationV1:
        _fail("EXP03_PROVIDER_NOT_AUTHORIZED", "an exact DG-03 authorization object is required")
    if not authorization.approved or authorization.self_hash != _expected_hash(authorization.to_dict()):
        _fail("EXP03_AUTHORIZATION_REPLAY_MISMATCH", "authorization is absent, stale, or mutated")


def build_provider_attempt_receipt_v1(
    *,
    authorization: ProviderExecutionAuthorizationV1 | None,
    relation_id: str,
    arm: ConstructionArmV1,
    repeat_index: int,
    call_index: int,
    attempt_index: int,
    request_hash: str,
    response_hash: str | None,
    result_class: str,
    input_tokens: int,
    output_tokens: int,
    latency_ms: float,
) -> ProviderAttemptReceiptV1:
    if authorization is None:
        _fail("EXP03_PROVIDER_NOT_AUTHORIZED", "provider attempts are disabled by default")
    _validate_authorization(authorization)
    if type(arm) is not ConstructionArmV1 or arm is ConstructionArmV1.T0:
        _fail("EXP03_ARM_CALL_INVALID", "provider attempts are limited to T1, T1-B, and T2")
    _identifier(relation_id, "relation_id")
    if repeat_index not in STOCHASTIC_REPEATS:
        _fail("EXP03_REPEAT_INVALID", "provider attempt repeat must be 1, 2, or 3")
    maximum = 1 if arm is ConstructionArmV1.T1 else 3
    if call_index not in range(1, maximum + 1):
        _fail("EXP03_CALL_INDEX_INVALID", "call index exceeds the frozen arm budget")
    _strict_int(attempt_index, "attempt_index", minimum=1)
    _hash(request_hash, "request_hash")
    if response_hash is not None:
        _hash(response_hash, "response_hash")
    if result_class not in {"SUCCESS", "RETRYABLE_PROVIDER_ERROR", "TERMINAL_PROVIDER_ERROR"}:
        _fail("EXP03_ATTEMPT_CLASS_INVALID", "attempt result class is closed")
    if result_class == "SUCCESS" and response_hash is None:
        _fail("EXP03_ATTEMPT_RESPONSE_MISSING", "successful attempts require a response hash")
    for name, value in (("input_tokens", input_tokens), ("output_tokens", output_tokens)):
        _strict_int(value, name)
    _finite_nonnegative(latency_ms, "latency_ms")
    if input_tokens > authorization.maximum_input_tokens_per_call or output_tokens > authorization.maximum_output_tokens_per_call:
        _fail("EXP03_TOKEN_CAP_EXCEEDED", "attempt exceeds the approved per-call token cap")
    provisional = ProviderAttemptReceiptV1(
        authorization_hash=authorization.self_hash,
        namespace=NATURAL_NAMESPACE,
        relation_id=relation_id,
        arm=arm.value,
        repeat_index=repeat_index,
        call_index=call_index,
        attempt_index=attempt_index,
        request_hash=request_hash,
        response_hash=response_hash,
        result_class=result_class,
        provider_id=authorization.provider_id,
        model_snapshot=authorization.model_snapshot,
        config_hash=authorization.config_hash,
        evidence_projection_hash=authorization.evidence_projection_hash,
        model_policy_hash=authorization.model_policy_hash,
        template_hash=authorization.template_hash,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        latency_ms=float(latency_ms),
    )
    return replace(provisional, self_hash=_expected_hash(provisional.to_dict()))


def verify_provider_attempt_receipt_v1(
    receipt: ProviderAttemptReceiptV1,
    authorization: ProviderExecutionAuthorizationV1,
) -> str:
    _validate_authorization(authorization)
    if type(receipt) is not ProviderAttemptReceiptV1:
        _fail("EXP03_ATTEMPT_TYPE_INVALID", "attempt receipt must use the exact contract type")
    if receipt.self_hash != _expected_hash(receipt.to_dict()):
        _fail("EXP03_ATTEMPT_REPLAY_MISMATCH", "attempt receipt mutated")
    expected = (
        authorization.self_hash,
        authorization.provider_id,
        authorization.model_snapshot,
        authorization.config_hash,
        authorization.evidence_projection_hash,
        authorization.model_policy_hash,
        authorization.template_hash,
    )
    observed = (
        receipt.authorization_hash,
        receipt.provider_id,
        receipt.model_snapshot,
        receipt.config_hash,
        receipt.evidence_projection_hash,
        receipt.model_policy_hash,
        receipt.template_hash,
    )
    if observed != expected:
        _fail("EXP03_ATTEMPT_AUTHORITY_MISMATCH", "attempt authority is stale or mismatched")
    return receipt.self_hash


@dataclass(frozen=True)
class ProviderCallReceiptV1:
    authorization_hash: str
    namespace: str
    relation_id: str
    arm: str
    repeat_index: int
    call_index: int
    request_hash: str
    response_hash: str | None
    completion_class: str
    attempt_receipts: tuple[ProviderAttemptReceiptV1, ...]
    provider_id: str
    model_snapshot: str
    config_hash: str
    evidence_projection_hash: str
    model_policy_hash: str
    template_hash: str
    input_tokens: int
    output_tokens: int
    latency_ms: float
    self_hash: str = ""

    def to_dict(self) -> dict[str, object]:
        return {
            "schema": "paperworks.validation_v2.exp03_provider_call_receipt_v1",
            "schema_version": EXP03_VERSION,
            **{
                **self.__dict__,
                "attempt_receipts": [item.to_dict() for item in self.attempt_receipts],
            },
        }


def build_provider_call_receipt_v1(
    *,
    authorization: ProviderExecutionAuthorizationV1,
    attempts: Sequence[ProviderAttemptReceiptV1],
    completion_class: str,
) -> ProviderCallReceiptV1:
    _validate_authorization(authorization)
    rows = tuple(attempts)
    if not rows:
        _fail("EXP03_PARTIAL_CALL_RECEIPT", "a call requires at least one immutable attempt")
    for row in rows:
        verify_provider_attempt_receipt_v1(row, authorization)
    identity = (
        rows[0].relation_id,
        rows[0].arm,
        rows[0].repeat_index,
        rows[0].call_index,
        rows[0].request_hash,
    )
    if any((row.relation_id, row.arm, row.repeat_index, row.call_index, row.request_hash) != identity for row in rows):
        _fail("EXP03_ATTEMPT_IDENTITY_MISMATCH", "attempts from different calls cannot be combined")
    if tuple(row.attempt_index for row in rows) != tuple(range(1, len(rows) + 1)):
        _fail("EXP03_ATTEMPT_SEQUENCE_INVALID", "attempt indices must be complete and consecutive")
    if completion_class not in {"NONEMPTY_RESPONSE", "EMPTY_RESPONSE", "PROVIDER_ERROR"}:
        _fail("EXP03_CALL_COMPLETION_INVALID", "call completion class is closed")
    last = rows[-1]
    if completion_class in {"NONEMPTY_RESPONSE", "EMPTY_RESPONSE"}:
        if last.result_class != "SUCCESS" or last.response_hash is None:
            _fail("EXP03_CALL_COMPLETION_MISMATCH", "response completion requires a successful final attempt")
        response_hash = last.response_hash
    else:
        if last.result_class == "SUCCESS":
            _fail("EXP03_CALL_COMPLETION_MISMATCH", "provider error cannot end in success")
        response_hash = None
    input_tokens = sum(row.input_tokens for row in rows)
    output_tokens = sum(row.output_tokens for row in rows)
    latency_ms = sum(row.latency_ms for row in rows)
    if input_tokens > authorization.maximum_input_tokens_per_call or output_tokens > authorization.maximum_output_tokens_per_call:
        _fail("EXP03_TOKEN_CAP_EXCEEDED", "call attempts exceed the approved per-call token cap")
    provisional = ProviderCallReceiptV1(
        authorization_hash=authorization.self_hash,
        namespace=NATURAL_NAMESPACE,
        relation_id=last.relation_id,
        arm=last.arm,
        repeat_index=last.repeat_index,
        call_index=last.call_index,
        request_hash=last.request_hash,
        response_hash=response_hash,
        completion_class=completion_class,
        attempt_receipts=rows,
        provider_id=authorization.provider_id,
        model_snapshot=authorization.model_snapshot,
        config_hash=authorization.config_hash,
        evidence_projection_hash=authorization.evidence_projection_hash,
        model_policy_hash=authorization.model_policy_hash,
        template_hash=authorization.template_hash,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        latency_ms=latency_ms,
    )
    return replace(provisional, self_hash=_expected_hash(provisional.to_dict()))


def verify_provider_call_receipt_v1(
    receipt: ProviderCallReceiptV1,
    authorization: ProviderExecutionAuthorizationV1,
) -> str:
    _validate_authorization(authorization)
    if type(receipt) is not ProviderCallReceiptV1:
        _fail("EXP03_CALL_TYPE_INVALID", "call receipt must use the exact contract type")
    if receipt.self_hash != _expected_hash(receipt.to_dict()):
        _fail("EXP03_CALL_REPLAY_MISMATCH", "call receipt mutated")
    rebuilt = build_provider_call_receipt_v1(
        authorization=authorization,
        attempts=receipt.attempt_receipts,
        completion_class=receipt.completion_class,
    )
    if rebuilt != receipt:
        _fail("EXP03_CALL_REPLAY_MISMATCH", "call receipt is stale or incomplete")
    return receipt.self_hash


def validate_provider_call_budget_v1(
    calls: Iterable[ProviderCallReceiptV1],
    authorization: ProviderExecutionAuthorizationV1,
) -> int:
    _validate_authorization(authorization)
    rows = tuple(calls)
    if len(rows) > authorization.maximum_calls:
        _fail("EXP03_CALL_BUDGET_EXCEEDED", "provider call count exceeds 21N")
    keys: set[tuple[str, str, int, int]] = set()
    total_tokens = 0
    for row in rows:
        verify_provider_call_receipt_v1(row, authorization)
        key = (row.relation_id, row.arm, row.repeat_index, row.call_index)
        if key in keys:
            _fail("EXP03_DUPLICATE_CALL", "provider call key is duplicated")
        keys.add(key)
        total_tokens += row.input_tokens + row.output_tokens
    if total_tokens > authorization.maximum_total_tokens:
        _fail("EXP03_TOKEN_CAP_EXCEEDED", "provider call receipts exceed the total token cap")
    return len(rows)


@dataclass(frozen=True)
class ConstructionTerminalRecordV1:
    namespace: str
    cohort_kind: str
    relation_id: str
    arm: str
    repeat_index: int
    outcome: str
    reason_code: str
    config_hash: str
    evidence_projection_hash: str
    model_policy_hash: str
    template_hash: str
    proposal_hash: str | None
    verifier_result_hash: str | None
    call_receipts: tuple[ProviderCallReceiptV1, ...]
    t1b_selection_receipt: T1BSelectionReceiptV1 | None
    controller_actions: tuple[str, ...]
    semantic_no_rule_confirmed: bool | None
    self_hash: str = ""

    @property
    def key(self) -> tuple[str, str, int]:
        return (self.relation_id, self.arm, self.repeat_index)

    @property
    def generation_calls(self) -> int:
        return len(self.call_receipts)

    def to_dict(self) -> dict[str, object]:
        return {
            "schema": "paperworks.validation_v2.exp03_terminal_record_v1",
            "schema_version": EXP03_VERSION,
            **{
                **self.__dict__,
                "call_receipts": [item.to_dict() for item in self.call_receipts],
                "t1b_selection_receipt": (
                    self.t1b_selection_receipt.to_dict()
                    if self.t1b_selection_receipt is not None else None
                ),
                "controller_actions": list(self.controller_actions),
            },
        }


def _validate_terminal_fields(
    *,
    outcome: ConstructionOutcomeV1,
    reason_code: str,
    proposal_hash: str | None,
    verifier_result_hash: str | None,
    semantic_no_rule_confirmed: bool | None,
) -> None:
    if type(outcome) is not ConstructionOutcomeV1:
        _fail("EXP03_OUTCOME_INVALID", "outcome must use the closed EXP-03 enum")
    if outcome is ConstructionOutcomeV1.ACCEPTED_PROPOSAL:
        if reason_code != "VERIFIER_ACCEPTED" or proposal_hash is None or verifier_result_hash is None:
            _fail("EXP03_ACCEPTED_BINDING_INCOMPLETE", "accepted outcomes require proposal and verifier bindings")
        if semantic_no_rule_confirmed is not None:
            _fail("EXP03_NO_RULE_FLAG_INVALID", "accepted outcomes cannot carry no-rule validation")
    elif outcome is ConstructionOutcomeV1.ALL_DRAWS_FAILED:
        if reason_code != TERMINAL_REASON_CODES[outcome.value]:
            _fail("EXP03_REASON_CLASS_MISMATCH", "T1-B all-failed summary reason changed")
        if proposal_hash is not None or verifier_result_hash is not None:
            _fail("EXP03_T1B_SUMMARY_BINDING_INVALID", "all-failed summary cannot bind a selected proposal")
        if semantic_no_rule_confirmed is not None:
            _fail("EXP03_FAILURE_TO_NO_RULE_FORBIDDEN", "all-failed summary is not semantic no-rule")
    else:
        if reason_code != TERMINAL_REASON_CODES[outcome.value]:
            _fail("EXP03_REASON_CLASS_MISMATCH", "terminal reason cannot be relabelled")
        if outcome is ConstructionOutcomeV1.VERIFIER_REJECTION:
            if proposal_hash is None or verifier_result_hash is None:
                _fail("EXP03_VERIFIER_BINDING_INCOMPLETE", "verifier rejection requires proposal and result hashes")
        if outcome.value in SEMANTIC_NO_RULE_OUTCOMES:
            _strict_bool(semantic_no_rule_confirmed, "semantic_no_rule_confirmed")
        elif semantic_no_rule_confirmed is not None:
            _fail("EXP03_FAILURE_TO_NO_RULE_FORBIDDEN", "operational failures cannot carry semantic no-rule state")
    if proposal_hash is not None:
        _hash(proposal_hash, "proposal_hash")
    if verifier_result_hash is not None:
        _hash(verifier_result_hash, "verifier_result_hash")


def build_terminal_record_v1(
    *,
    authorization: ProviderExecutionAuthorizationV1 | None,
    relation_id: str,
    arm: ConstructionArmV1,
    repeat_index: int,
    outcome: ConstructionOutcomeV1,
    reason_code: str,
    config_hash: str,
    evidence_projection_hash: str,
    model_policy_hash: str,
    template_hash: str,
    proposal_hash: str | None = None,
    verifier_result_hash: str | None = None,
    call_receipts: Sequence[ProviderCallReceiptV1] = (),
    t1b_selection_receipt: T1BSelectionReceiptV1 | None = None,
    controller_actions: Sequence[str] = (),
    semantic_no_rule_confirmed: bool | None = None,
) -> ConstructionTerminalRecordV1:
    _identifier(relation_id, "relation_id")
    if type(arm) is not ConstructionArmV1:
        _fail("EXP03_ARM_INVALID", "arm must use the closed EXP-03 enum")
    expected_repeat = (0,) if arm is ConstructionArmV1.T0 else STOCHASTIC_REPEATS
    if repeat_index not in expected_repeat:
        _fail("EXP03_REPEAT_INVALID", "repeat does not match the arm contract")
    for name, value in (
        ("config_hash", config_hash),
        ("evidence_projection_hash", evidence_projection_hash),
        ("model_policy_hash", model_policy_hash),
        ("template_hash", template_hash),
    ):
        _hash(value, name)
    _validate_terminal_fields(
        outcome=outcome,
        reason_code=reason_code,
        proposal_hash=proposal_hash,
        verifier_result_hash=verifier_result_hash,
        semantic_no_rule_confirmed=semantic_no_rule_confirmed,
    )
    calls = tuple(call_receipts)
    expected_calls = {ConstructionArmV1.T0: 0, ConstructionArmV1.T1: 1, ConstructionArmV1.T1_B: 3}
    if arm in expected_calls and len(calls) != expected_calls[arm]:
        _fail("EXP03_ARM_CALL_COUNT_INVALID", "T0=0, T1=1, and T1-B=3 are exact")
    if arm is ConstructionArmV1.T2:
        if len(calls) > 3:
            _fail("EXP03_FOURTH_CALL_FORBIDDEN", "T2 permits at most three generation calls")
        zero_call_allowed = outcome in {
            ConstructionOutcomeV1.UNSUPPORTED_EVIDENCE,
            ConstructionOutcomeV1.SYSTEM_ERROR,
        }
        if not calls and not zero_call_allowed:
            _fail("EXP03_T2_CALL_REQUIRED", "T2 outcome requires receipt-first provider custody")
    if calls:
        if authorization is None:
            _fail("EXP03_PROVIDER_NOT_AUTHORIZED", "provider-backed records require DG-03 authorization")
        _validate_authorization(authorization)
        expected_indices = tuple(range(1, len(calls) + 1))
        if tuple(item.call_index for item in calls) != expected_indices:
            _fail("EXP03_PARTIAL_CALL_RECEIPT", "call receipts must be complete and consecutive")
        for item in calls:
            verify_provider_call_receipt_v1(item, authorization)
            observed = (item.relation_id, item.arm, item.repeat_index)
            if observed != (relation_id, arm.value, repeat_index):
                _fail("EXP03_CALL_IDENTITY_MISMATCH", "call receipt belongs to another schedule record")
            bound = (item.config_hash, item.evidence_projection_hash, item.model_policy_hash, item.template_hash)
            if bound != (config_hash, evidence_projection_hash, model_policy_hash, template_hash):
                _fail("EXP03_CALL_AUTHORITY_MISMATCH", "call authority does not match terminal record")
        completion = calls[-1].completion_class
        if outcome is ConstructionOutcomeV1.PROVIDER_ERROR and completion != "PROVIDER_ERROR":
            _fail("EXP03_OUTCOME_CALL_MISMATCH", "PROVIDER_ERROR requires a provider-error final call")
        if outcome is ConstructionOutcomeV1.EMPTY_RESPONSE and completion != "EMPTY_RESPONSE":
            _fail("EXP03_OUTCOME_CALL_MISMATCH", "EMPTY_RESPONSE requires an empty final response")
        if outcome in {
            ConstructionOutcomeV1.ACCEPTED_PROPOSAL,
            ConstructionOutcomeV1.INTENTIONAL_NO_RULE,
            ConstructionOutcomeV1.PARSE_FAILURE,
            ConstructionOutcomeV1.VERIFIER_REJECTION,
            ConstructionOutcomeV1.BUDGET_EXHAUSTION,
        } and completion != "NONEMPTY_RESPONSE":
            _fail("EXP03_OUTCOME_CALL_MISMATCH", "outcome requires a non-empty final provider response")
    if arm is ConstructionArmV1.T1_B:
        if t1b_selection_receipt is None or authorization is None:
            _fail("EXP03_T1B_SELECTION_REQUIRED", "T1-B terminal requires its verified selection receipt")
        verify_t1b_selection_v1(t1b_selection_receipt, authorization)
        if (t1b_selection_receipt.relation_id, t1b_selection_receipt.repeat_index) != (relation_id, repeat_index):
            _fail("EXP03_T1B_SELECTION_IDENTITY_MISMATCH", "T1-B selection belongs to another record")
        if tuple(item.call_receipt for item in t1b_selection_receipt.draw_outcomes) != calls:
            _fail("EXP03_T1B_SELECTION_CALL_MISMATCH", "T1-B selection calls differ from terminal custody")
        if t1b_selection_receipt.selected_draw_index is None:
            if outcome is not ConstructionOutcomeV1.ALL_DRAWS_FAILED:
                _fail("EXP03_T1B_SELECTION_OUTCOME_MISMATCH", "all-failed selection requires arm summary")
        else:
            selected_draw = t1b_selection_receipt.draw_outcomes[t1b_selection_receipt.selected_draw_index - 1]
            if outcome is not ConstructionOutcomeV1.ACCEPTED_PROPOSAL:
                _fail("EXP03_T1B_SELECTION_OUTCOME_MISMATCH", "admissible T1-B draw requires accepted arm outcome")
            if (proposal_hash, verifier_result_hash) != (selected_draw.proposal_hash, selected_draw.verifier_result_hash):
                _fail("EXP03_T1B_SELECTION_BINDING_MISMATCH", "arm proposal must equal the selected draw")
    elif t1b_selection_receipt is not None:
        _fail("EXP03_T1B_SELECTION_ARM_MISMATCH", "selection receipts are exclusive to T1-B")
    actions = tuple(controller_actions)
    if any(item not in {"revise", "retrieve"} for item in actions):
        _fail("EXP03_CONTROLLER_ACTION_INVALID", "only revise and retrieve are allowed")
    if arm is not ConstructionArmV1.T2 and actions:
        _fail("EXP03_FEEDBACK_ARM_INVALID", "only T2 can carry verifier feedback actions")
    if actions and not calls:
        _fail("EXP03_FEEDBACK_WITHOUT_CALL", "feedback actions require a preceding provider call")
    if actions.count("retrieve") > 1:
        _fail("EXP03_REPEATED_RETRIEVAL_FORBIDDEN", "the same-corpus retrieval route may occur at most once")
    if len(actions) > 2:
        _fail("EXP03_CONTROLLER_ACTION_BUDGET", "T2 permits at most two feedback transitions")
    if arm is ConstructionArmV1.T2:
        expected_action_count = (
            len(calls)
            if outcome is ConstructionOutcomeV1.RETRIEVAL_FAILURE
            else max(0, len(calls) - 1)
        )
        if len(actions) != expected_action_count:
            _fail(
                "EXP03_T2_ACTION_SEQUENCE_INVALID",
                "T2 must bind one feedback transition before every additional call and no dangling action",
            )
    if outcome is ConstructionOutcomeV1.BUDGET_EXHAUSTION and (
        arm is not ConstructionArmV1.T2 or len(calls) != 3 or len(actions) != 2
    ):
        _fail("EXP03_BUDGET_EXHAUSTION_INVALID", "budget exhaustion requires three T2 calls and two feedback transitions")
    if outcome is ConstructionOutcomeV1.RETRIEVAL_FAILURE and (
        arm is not ConstructionArmV1.T2 or not actions or actions[-1] != "retrieve"
    ):
        _fail("EXP03_RETRIEVAL_FAILURE_INVALID", "retrieval failure requires a T2 retrieve action")
    provisional = ConstructionTerminalRecordV1(
        namespace=NATURAL_NAMESPACE,
        cohort_kind=CohortKindV1.NATURAL.value,
        relation_id=relation_id,
        arm=arm.value,
        repeat_index=repeat_index,
        outcome=outcome.value,
        reason_code=reason_code,
        config_hash=config_hash,
        evidence_projection_hash=evidence_projection_hash,
        model_policy_hash=model_policy_hash,
        template_hash=template_hash,
        proposal_hash=proposal_hash,
        verifier_result_hash=verifier_result_hash,
        call_receipts=calls,
        t1b_selection_receipt=t1b_selection_receipt,
        controller_actions=actions,
        semantic_no_rule_confirmed=semantic_no_rule_confirmed,
    )
    return replace(provisional, self_hash=_expected_hash(provisional.to_dict()))


def verify_terminal_record_v1(
    record: ConstructionTerminalRecordV1,
    authorization: ProviderExecutionAuthorizationV1 | None,
) -> str:
    if type(record) is not ConstructionTerminalRecordV1:
        _fail("EXP03_TERMINAL_TYPE_INVALID", "terminal record must use the exact natural-cohort type")
    if record.namespace != NATURAL_NAMESPACE or record.cohort_kind != CohortKindV1.NATURAL.value:
        _fail("EXP03_COHORT_NAMESPACE_MISMATCH", "natural record namespace changed")
    if record.self_hash != _expected_hash(record.to_dict()):
        _fail("EXP03_TERMINAL_REPLAY_MISMATCH", "terminal record mutated")
    try:
        arm = ConstructionArmV1(record.arm)
        outcome = ConstructionOutcomeV1(record.outcome)
    except ValueError:
        _fail("EXP03_TERMINAL_ENUM_INVALID", "terminal record uses an unknown arm or outcome")
    rebuilt = build_terminal_record_v1(
        authorization=authorization,
        relation_id=record.relation_id,
        arm=arm,
        repeat_index=record.repeat_index,
        outcome=outcome,
        reason_code=record.reason_code,
        config_hash=record.config_hash,
        evidence_projection_hash=record.evidence_projection_hash,
        model_policy_hash=record.model_policy_hash,
        template_hash=record.template_hash,
        proposal_hash=record.proposal_hash,
        verifier_result_hash=record.verifier_result_hash,
        call_receipts=record.call_receipts,
        t1b_selection_receipt=record.t1b_selection_receipt,
        controller_actions=record.controller_actions,
        semantic_no_rule_confirmed=record.semantic_no_rule_confirmed,
    )
    if rebuilt != record:
        _fail("EXP03_TERMINAL_REPLAY_MISMATCH", "terminal record is stale or incomplete")
    return record.self_hash


@dataclass(frozen=True)
class T1BDrawOutcomeV1:
    draw_index: int
    outcome: str
    reason_code: str
    proposal_hash: str | None
    verifier_result_hash: str | None
    call_receipt: ProviderCallReceiptV1
    self_hash: str = ""

    def to_dict(self) -> dict[str, object]:
        return {
            "schema": "paperworks.validation_v2.exp03_t1b_draw_v1",
            "schema_version": EXP03_VERSION,
            **{**self.__dict__, "call_receipt": self.call_receipt.to_dict()},
        }


def build_t1b_draw_v1(
    *,
    authorization: ProviderExecutionAuthorizationV1,
    draw_index: int,
    call_receipt: ProviderCallReceiptV1,
    outcome: ConstructionOutcomeV1,
    reason_code: str,
    proposal_hash: str | None = None,
    verifier_result_hash: str | None = None,
) -> T1BDrawOutcomeV1:
    if draw_index not in T1B_DRAWS or call_receipt.call_index != draw_index:
        _fail("EXP03_T1B_DRAW_INDEX_INVALID", "T1-B draw and call indices must be 1, 2, 3")
    if call_receipt.arm != ConstructionArmV1.T1_B.value:
        _fail("EXP03_T1B_DRAW_ARM_INVALID", "draw receipt must belong to T1-B")
    verify_provider_call_receipt_v1(call_receipt, authorization)
    if outcome is ConstructionOutcomeV1.UNSUPPORTED_EVIDENCE:
        _fail("EXP03_T1B_DRAW_OUTCOME_INVALID", "pre-construction evidence rejection cannot occur after a draw")
    _validate_terminal_fields(
        outcome=outcome,
        reason_code=reason_code,
        proposal_hash=proposal_hash,
        verifier_result_hash=verifier_result_hash,
        semantic_no_rule_confirmed=False if outcome.value in SEMANTIC_NO_RULE_OUTCOMES else None,
    )
    provisional = T1BDrawOutcomeV1(
        draw_index=draw_index,
        outcome=outcome.value,
        reason_code=reason_code,
        proposal_hash=proposal_hash,
        verifier_result_hash=verifier_result_hash,
        call_receipt=call_receipt,
    )
    expected_completion = {
        ConstructionOutcomeV1.PROVIDER_ERROR: "PROVIDER_ERROR",
        ConstructionOutcomeV1.EMPTY_RESPONSE: "EMPTY_RESPONSE",
    }.get(outcome, "NONEMPTY_RESPONSE")
    if call_receipt.completion_class != expected_completion:
        _fail("EXP03_T1B_DRAW_CALL_MISMATCH", "draw outcome and call completion differ")
    return replace(provisional, self_hash=_expected_hash(provisional.to_dict()))


def verify_t1b_draw_v1(
    receipt: T1BDrawOutcomeV1,
    authorization: ProviderExecutionAuthorizationV1,
) -> str:
    if type(receipt) is not T1BDrawOutcomeV1:
        _fail("EXP03_T1B_DRAW_TYPE_INVALID", "exact T1-B draw receipt required")
    if receipt.self_hash != _expected_hash(receipt.to_dict()):
        _fail("EXP03_T1B_DRAW_REPLAY_MISMATCH", "T1-B draw mutated")
    try:
        outcome = ConstructionOutcomeV1(receipt.outcome)
    except ValueError:
        _fail("EXP03_T1B_DRAW_OUTCOME_INVALID", "T1-B draw uses an unknown outcome")
    if outcome is ConstructionOutcomeV1.ALL_DRAWS_FAILED:
        _fail("EXP03_T1B_DRAW_OUTCOME_INVALID", "arm summary cannot be used as a draw outcome")
    rebuilt = build_t1b_draw_v1(
        authorization=authorization,
        draw_index=receipt.draw_index,
        call_receipt=receipt.call_receipt,
        outcome=outcome,
        reason_code=receipt.reason_code,
        proposal_hash=receipt.proposal_hash,
        verifier_result_hash=receipt.verifier_result_hash,
    )
    if rebuilt != receipt:
        _fail("EXP03_T1B_DRAW_REPLAY_MISMATCH", "T1-B draw is stale or incomplete")
    return receipt.self_hash


@dataclass(frozen=True)
class T1BSelectionReceiptV1:
    relation_id: str
    repeat_index: int
    draw_outcomes: tuple[T1BDrawOutcomeV1, ...]
    selected_draw_index: int | None
    selection_outcome: str
    preserved_failure_causes: tuple[str, ...]
    self_hash: str = ""

    def to_dict(self) -> dict[str, object]:
        return {
            "schema": "paperworks.validation_v2.exp03_t1b_selection_v1",
            "schema_version": EXP03_VERSION,
            **{
                **self.__dict__,
                "draw_outcomes": [item.to_dict() for item in self.draw_outcomes],
                "preserved_failure_causes": list(self.preserved_failure_causes),
            },
        }


def select_t1b_lowest_admissible_v1(
    draws: Sequence[T1BDrawOutcomeV1],
    authorization: ProviderExecutionAuthorizationV1,
) -> T1BSelectionReceiptV1:
    rows = tuple(draws)
    if len(rows) != 3 or tuple(item.draw_index for item in rows) != T1B_DRAWS:
        _fail("EXP03_T1B_EXACT_THREE_REQUIRED", "T1-B must retain exactly three ordered draws")
    for row in rows:
        verify_t1b_draw_v1(row, authorization)
    identity = {(item.call_receipt.relation_id, item.call_receipt.repeat_index) for item in rows}
    if len(identity) != 1:
        _fail("EXP03_T1B_DRAW_IDENTITY_MISMATCH", "T1-B draws cross relation or repeat boundaries")
    accepted = tuple(item.draw_index for item in rows if item.outcome == "ACCEPTED_PROPOSAL")
    selected = min(accepted) if accepted else None
    causes = tuple(item.outcome for item in rows if item.outcome != "ACCEPTED_PROPOSAL")
    relation_id, repeat_index = next(iter(identity))
    provisional = T1BSelectionReceiptV1(
        relation_id=relation_id,
        repeat_index=repeat_index,
        draw_outcomes=rows,
        selected_draw_index=selected,
        selection_outcome="ACCEPTED_PROPOSAL" if selected is not None else "ALL_DRAWS_FAILED",
        preserved_failure_causes=causes,
    )
    return replace(provisional, self_hash=_expected_hash(provisional.to_dict()))


def verify_t1b_selection_v1(
    receipt: T1BSelectionReceiptV1, authorization: ProviderExecutionAuthorizationV1
) -> str:
    if type(receipt) is not T1BSelectionReceiptV1:
        _fail("EXP03_T1B_SELECTION_TYPE_INVALID", "exact T1-B selection receipt required")
    if receipt.self_hash != _expected_hash(receipt.to_dict()):
        _fail("EXP03_T1B_SELECTION_REPLAY_MISMATCH", "T1-B selection mutated")
    rebuilt = select_t1b_lowest_admissible_v1(receipt.draw_outcomes, authorization)
    if rebuilt != receipt:
        _fail("EXP03_T1B_SELECTION_REPLAY_MISMATCH", "T1-B selection is stale")
    return receipt.self_hash


@dataclass(frozen=True, order=True)
class NaturalScheduleEntryV1:
    relation_id: str
    arm: str
    repeat_index: int

    def __post_init__(self) -> None:
        _identifier(self.relation_id, "relation_id")
        ConstructionArmV1(self.arm)
        expected = (0,) if self.arm == "T0" else STOCHASTIC_REPEATS
        if self.repeat_index not in expected:
            _fail("EXP03_SCHEDULE_REPEAT_INVALID", "schedule repeat does not match arm")

    def to_dict(self) -> dict[str, object]:
        return {"relation_id": self.relation_id, "arm": self.arm, "repeat_index": self.repeat_index}


@dataclass(frozen=True)
class NaturalScheduleReceiptV1:
    namespace: str
    cohort_hash: str
    config_hash: str
    evidence_projection_hash: str
    entries: tuple[NaturalScheduleEntryV1, ...]
    self_hash: str = ""

    def to_dict(self) -> dict[str, object]:
        return {
            "schema": "paperworks.validation_v2.exp03_natural_schedule_v1",
            "schema_version": EXP03_VERSION,
            "namespace": self.namespace,
            "cohort_hash": self.cohort_hash,
            "config_hash": self.config_hash,
            "evidence_projection_hash": self.evidence_projection_hash,
            "entries": [item.to_dict() for item in self.entries],
            "self_hash": self.self_hash,
        }


def build_natural_schedule_v1(
    *, relation_ids: Sequence[str], cohort_hash: str, config_hash: str, evidence_projection_hash: str
) -> NaturalScheduleReceiptV1:
    relations = tuple(relation_ids)
    if not relations or len(relations) != len(set(relations)):
        _fail("EXP03_RELATION_SCHEDULE_INVALID", "relation schedule must be non-empty and unique")
    for relation in relations:
        _identifier(relation, "relation_id")
    for name, value in (("cohort_hash", cohort_hash), ("config_hash", config_hash), ("evidence_projection_hash", evidence_projection_hash)):
        _hash(value, name)
    entries: list[NaturalScheduleEntryV1] = []
    for relation in sorted(relations):
        entries.append(NaturalScheduleEntryV1(relation, "T0", 0))
        for arm in ("T1", "T1-B", "T2"):
            entries.extend(NaturalScheduleEntryV1(relation, arm, repeat) for repeat in STOCHASTIC_REPEATS)
    provisional = NaturalScheduleReceiptV1(
        namespace=NATURAL_NAMESPACE,
        cohort_hash=cohort_hash,
        config_hash=config_hash,
        evidence_projection_hash=evidence_projection_hash,
        entries=tuple(entries),
    )
    return replace(provisional, self_hash=_expected_hash(provisional.to_dict()))


def validate_complete_natural_schedule_v1(
    schedule: NaturalScheduleReceiptV1,
    records: Sequence[ConstructionTerminalRecordV1],
    authorization: ProviderExecutionAuthorizationV1 | None,
) -> str:
    if type(schedule) is not NaturalScheduleReceiptV1 or schedule.namespace != NATURAL_NAMESPACE:
        _fail("EXP03_SCHEDULE_TYPE_INVALID", "natural schedule contract required")
    if schedule.self_hash != _expected_hash(schedule.to_dict()):
        _fail("EXP03_SCHEDULE_REPLAY_MISMATCH", "schedule mutated")
    relation_ids = tuple(sorted({entry.relation_id for entry in schedule.entries}))
    canonical = build_natural_schedule_v1(
        relation_ids=relation_ids,
        cohort_hash=schedule.cohort_hash,
        config_hash=schedule.config_hash,
        evidence_projection_hash=schedule.evidence_projection_hash,
    )
    if canonical != schedule:
        _fail("EXP03_SCHEDULE_REPLAY_MISMATCH", "schedule is rehashed but incomplete or non-canonical")
    relation_count = len({entry.relation_id for entry in schedule.entries})
    if authorization is not None:
        _validate_authorization(authorization)
        if relation_count != authorization.natural_relation_count:
            _fail("EXP03_SCHEDULE_AUTHORITY_MISMATCH", "schedule cohort size differs from DG-03 authorization")
    rows = tuple(records)
    for row in rows:
        verify_terminal_record_v1(row, authorization)
        if row.config_hash != schedule.config_hash or row.evidence_projection_hash != schedule.evidence_projection_hash:
            _fail("EXP03_STALE_RECORD_AUTHORITY", "record authority differs from frozen schedule")
    keys = tuple(row.key for row in rows)
    if len(keys) != len(set(keys)):
        _fail("EXP03_DUPLICATE_TERMINAL", "one schedule key has multiple terminal records")
    expected = tuple((item.relation_id, item.arm, item.repeat_index) for item in schedule.entries)
    if tuple(sorted(keys)) != tuple(sorted(expected)):
        _fail("EXP03_INCOMPLETE_SCHEDULE", "every scheduled relation-arm-repeat needs exactly one terminal")
    if authorization is not None:
        validate_provider_call_budget_v1(
            (call for record in rows for call in record.call_receipts), authorization
        )
    return schedule.self_hash


@dataclass(frozen=True)
class NaturalMetricsV1:
    namespace: str
    scheduled_records: int
    accepted_records: int
    terminal_counts: tuple[tuple[str, int], ...]
    semantic_no_rule_denominator: int
    semantic_no_rule_confirmed: int
    semantic_no_rule_appropriateness: float | str
    self_hash: str = ""

    def to_dict(self) -> dict[str, object]:
        return {
            "schema": "paperworks.validation_v2.exp03_natural_metrics_v1",
            "schema_version": EXP03_VERSION,
            **{**self.__dict__, "terminal_counts": [list(item) for item in self.terminal_counts]},
        }


def aggregate_natural_metrics_v1(
    records: Sequence[ConstructionTerminalRecordV1],
    authorization: ProviderExecutionAuthorizationV1 | None,
) -> NaturalMetricsV1:
    rows = tuple(records)
    if not rows:
        _fail("EXP03_NATURAL_METRICS_EMPTY", "natural metrics require terminal records")
    for row in rows:
        verify_terminal_record_v1(row, authorization)
    counted_outcomes = (*TERMINAL_CLASSES, ConstructionOutcomeV1.ALL_DRAWS_FAILED.value)
    counts = tuple((name, sum(row.outcome == name for row in rows)) for name in counted_outcomes)
    semantic = tuple(row for row in rows if row.outcome in SEMANTIC_NO_RULE_OUTCOMES)
    confirmed = sum(row.semantic_no_rule_confirmed is True for row in semantic)
    score: float | str = "NOT_OBSERVED" if not semantic else confirmed / len(semantic)
    provisional = NaturalMetricsV1(
        namespace=NATURAL_NAMESPACE,
        scheduled_records=len(rows),
        accepted_records=sum(row.outcome == "ACCEPTED_PROPOSAL" for row in rows),
        terminal_counts=counts,
        semantic_no_rule_denominator=len(semantic),
        semantic_no_rule_confirmed=confirmed,
        semantic_no_rule_appropriateness=score,
    )
    return replace(provisional, self_hash=_expected_hash(provisional.to_dict()))


@dataclass(frozen=True)
class StressFixtureReceiptV1:
    namespace: str
    cohort_kind: str
    fixture_id: str
    expected_terminal: str
    observed_terminal: str
    provider_calls: int
    controller_actions: tuple[str, ...]
    synthetic_input_hash: str
    self_hash: str = ""

    def to_dict(self) -> dict[str, object]:
        return {
            "schema": "paperworks.validation_v2.exp03_stress_fixture_v1",
            "schema_version": EXP03_VERSION,
            **self.__dict__,
        }


def build_stress_fixture_receipt_v1(
    *, fixture_id: str, expected_terminal: ConstructionTerminalClassV1,
    observed_terminal: ConstructionTerminalClassV1, synthetic_input_hash: str,
    controller_actions: Sequence[str] = (),
) -> StressFixtureReceiptV1:
    _identifier(fixture_id, "fixture_id")
    if type(expected_terminal) is not ConstructionTerminalClassV1 or type(observed_terminal) is not ConstructionTerminalClassV1:
        _fail("EXP03_STRESS_TERMINAL_INVALID", "stress terminals must use the exact nine-class enum")
    _hash(synthetic_input_hash, "synthetic_input_hash")
    actions = tuple(controller_actions)
    if any(item not in {"revise", "retrieve"} for item in actions):
        _fail("EXP03_CONTROLLER_ACTION_INVALID", "stress routes are limited to revise and retrieve")
    if actions.count("retrieve") > 1:
        _fail("EXP03_REPEATED_RETRIEVAL_FORBIDDEN", "stress fixture repeats retrieval")
    if len(actions) > 2:
        _fail("EXP03_CONTROLLER_ACTION_BUDGET", "stress route exceeds controller budget")
    provisional = StressFixtureReceiptV1(
        namespace=STRESS_NAMESPACE,
        cohort_kind=CohortKindV1.SYNTHETIC_STRESS.value,
        fixture_id=fixture_id,
        expected_terminal=expected_terminal.value,
        observed_terminal=observed_terminal.value,
        provider_calls=0,
        controller_actions=actions,
        synthetic_input_hash=synthetic_input_hash,
    )
    return replace(provisional, self_hash=_expected_hash(provisional.to_dict()))


@dataclass(frozen=True)
class StressMetricsV1:
    namespace: str
    result_label: str
    fixture_count: int
    exact_match_count: int
    terminal_coverage: tuple[str, ...]
    no_rule_conflation_count: int
    provider_calls: int
    controller_route_coverage: tuple[str, ...]
    self_hash: str = ""

    def to_dict(self) -> dict[str, object]:
        return {
            "schema": "paperworks.validation_v2.exp03_stress_metrics_v1",
            "schema_version": EXP03_VERSION,
            **{
                **self.__dict__,
                "terminal_coverage": list(self.terminal_coverage),
                "controller_route_coverage": list(self.controller_route_coverage),
            },
        }


def aggregate_stress_metrics_v1(fixtures: Sequence[StressFixtureReceiptV1]) -> StressMetricsV1:
    rows = tuple(fixtures)
    if not rows:
        _fail("EXP03_STRESS_METRICS_EMPTY", "stress metrics require preregistered fixtures")
    seen: set[str] = set()
    for row in rows:
        if type(row) is not StressFixtureReceiptV1:
            _fail("EXP03_NATURAL_STRESS_MIX_FORBIDDEN", "natural and stress artifacts cannot be pooled")
        if row.namespace != STRESS_NAMESPACE or row.cohort_kind != CohortKindV1.SYNTHETIC_STRESS.value:
            _fail("EXP03_STRESS_NAMESPACE_MISMATCH", "stress namespace changed")
        if row.provider_calls != 0:
            _fail("EXP03_STRESS_PROVIDER_CALL_FORBIDDEN", "synthetic stress must use zero provider calls")
        if row.self_hash != _expected_hash(row.to_dict()):
            _fail("EXP03_STRESS_REPLAY_MISMATCH", "stress fixture mutated")
        try:
            expected_terminal = ConstructionTerminalClassV1(row.expected_terminal)
            observed_terminal = ConstructionTerminalClassV1(row.observed_terminal)
        except ValueError:
            _fail("EXP03_STRESS_TERMINAL_INVALID", "stress fixture uses an unknown terminal class")
        rebuilt = build_stress_fixture_receipt_v1(
            fixture_id=row.fixture_id,
            expected_terminal=expected_terminal,
            observed_terminal=observed_terminal,
            synthetic_input_hash=row.synthetic_input_hash,
            controller_actions=row.controller_actions,
        )
        if rebuilt != row:
            _fail("EXP03_STRESS_REPLAY_MISMATCH", "stress fixture is stale or semantically invalid")
        if row.fixture_id in seen:
            _fail("EXP03_DUPLICATE_STRESS_FIXTURE", "stress fixture identity is duplicated")
        seen.add(row.fixture_id)
    coverage = tuple(sorted({row.expected_terminal for row in rows}))
    if coverage != tuple(sorted(TERMINAL_CLASSES)):
        _fail("EXP03_STRESS_COVERAGE_INCOMPLETE", "stress cohort must cover all nine terminal classes")
    conflation = sum(
        row.expected_terminal in NEVER_NO_RULE_OUTCOMES and row.observed_terminal in SEMANTIC_NO_RULE_OUTCOMES
        for row in rows
    )
    route_coverage = tuple(sorted({action for row in rows for action in row.controller_actions}))
    if route_coverage != ("retrieve", "revise"):
        _fail("EXP03_STRESS_ROUTE_COVERAGE_INCOMPLETE", "stress cohort must cover revise and retrieve")
    provisional = StressMetricsV1(
        namespace=STRESS_NAMESPACE,
        result_label="SYNTHETIC_STRESS_ONLY",
        fixture_count=len(rows),
        exact_match_count=sum(row.expected_terminal == row.observed_terminal for row in rows),
        terminal_coverage=coverage,
        no_rule_conflation_count=conflation,
        provider_calls=0,
        controller_route_coverage=route_coverage,
    )
    return replace(provisional, self_hash=_expected_hash(provisional.to_dict()))


__all__ = [
    "CohortKindV1", "ConstructionArmV1", "ConstructionOutcomeV1",
    "ConstructionTerminalClassV1", "ConstructionTerminalRecordV1",
    "Exp03ContractError", "NaturalMetricsV1", "NaturalScheduleReceiptV1",
    "ProviderAttemptReceiptV1", "ProviderCallReceiptV1",
    "ProviderExecutionAuthorizationV1", "ProviderInputProjectionV1",
    "StressFixtureReceiptV1", "StressMetricsV1",
    "T1BDrawOutcomeV1", "T1BSelectionReceiptV1", "TERMINAL_CLASSES",
    "aggregate_natural_metrics_v1", "aggregate_stress_metrics_v1",
    "build_natural_schedule_v1", "build_provider_attempt_receipt_v1",
    "build_provider_call_receipt_v1", "build_provider_execution_authorization_v1",
    "build_provider_input_projection_v1",
    "build_stress_fixture_receipt_v1", "build_t1b_draw_v1", "build_terminal_record_v1",
    "execute_provider_transport_v1", "provider_call_maximum_v1",
    "select_t1b_lowest_admissible_v1", "validate_complete_natural_schedule_v1",
    "validate_provider_call_budget_v1", "verify_provider_attempt_receipt_v1",
    "verify_provider_call_receipt_v1", "verify_t1b_draw_v1", "verify_t1b_selection_v1", "verify_terminal_record_v1",
]
