"""Formal V4-specific deterministic explanation fidelity contracts.

This module is a preparation-only contract for EXP-05.  It does not execute
the runtime and it does not claim equivalence with canonical ``RuntimeTraceV1``.
The future scientific runner must connect materialization to the same
authorized call that emits ``FormalV4RuntimeTraceV1``; detached materialization
is deliberately marked as not scientifically authorized here.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any

from .formal_v4_authority_v1 import (
    V4_NUMERIC_ROLES,
    FormalV4ExecutionContextV1,
    FormalV4PortfolioAuthorityV1,
    FormalV4RuleDescriptorV1,
    FormalV4RuntimeAuthorizationReceiptV1,
    NumericReferenceBindingV1,
    canonical_document_hash_v1,
    canonical_json_bytes_v1,
)
from .runtime_policy_v1 import FORMAL_V4_TRACE_CONTRACT_HASH
from .runtime_v1 import (
    FORMAL_V4_RUNTIME_VERSION,
    FormalV4ObservationWindowV1,
    FormalV4RuntimeTraceV1,
)


EXP05_MATERIALIZED_TRACE_VERSION = "VALIDATION_V2_FORMAL_V4_MATERIALIZED_TRACE_V1"
EXP05_RENDERER_VERSION = "VALIDATION_V2_FORMAL_V4_EXPLANATION_RENDERER_V1"
EXP05_FIDELITY_VALIDATOR_VERSION = "VALIDATION_V2_EXP05_FIDELITY_VALIDATOR_V1"
EXP05_SCHEMA_VERSION = "1.0.0"
EXP05_SCIENTIFIC_RUNNER_AUTHORIZED = False

_HASH_ZERO = "0" * 64
_OUTCOME_REASON_ALARM = {
    ("PASS", "expected_response_observed", False),
    ("FAIL", "expected_response_not_observed", True),
    ("ABSTAIN", "incomplete_source_window", False),
    ("ABSTAIN", "source_not_triggered", False),
    ("ABSTAIN", "incomplete_target_response_window", False),
}
_SOURCE_DIRECTION_KO = {
    "step_up": "상승 step",
    "step_down": "하강 step",
}
_TARGET_DIRECTION_KO = {
    "increase": "증가",
    "decrease": "감소",
}
_OUTCOME_CLAUSE_KO = {
    ("PASS", "expected_response_observed"): "기대 방향 응답이 관찰되었습니다. 결과=PASS.",
    ("FAIL", "expected_response_not_observed"): "기대 방향 응답이 관찰되지 않았습니다. 결과=FAIL.",
    ("ABSTAIN", "incomplete_source_window"): "source window가 불완전하여 평가하지 못했습니다. 결과=ABSTAIN.",
    ("ABSTAIN", "source_not_triggered"): "source 조건이 발동하지 않아 평가하지 않았습니다. 결과=ABSTAIN.",
    ("ABSTAIN", "incomplete_target_response_window"): "target response window가 불완전하여 평가하지 못했습니다. 결과=ABSTAIN.",
}

_RENDERER_CONTRACT = {
    "allowed_narrative_number": "selected_horizon_seconds_only",
    "allowed_variables": ["source", "target"],
    "caller_authored_text": False,
    "causal_claim_allowed": False,
    "current_time_used": False,
    "human_usefulness_evaluated": False,
    "llm_used": False,
    "network_used": False,
    "numeric_values_rendered": False,
    "randomness_used": False,
    "renderer_version": EXP05_RENDERER_VERSION,
    "template_family": "formal_v4_exact_korean_template_v1",
}
EXP05_RENDERER_CONTRACT_HASH = canonical_document_hash_v1(_RENDERER_CONTRACT)

EXP05_FIDELITY_CHECK_IDS = (
    "SOURCE_MATCH",
    "TARGET_MATCH",
    "SOURCE_DIRECTION_MATCH",
    "TARGET_DIRECTION_MATCH",
    "HORIZON_MATCH",
    "NUMERIC_PROVENANCE_MATCH",
    "OUTCOME_MATCH",
    "NO_NEW_VARIABLE",
    "NO_NEW_NUMBER",
    "NO_CAUSAL_CLAIM",
    "DETERMINISTIC_REPLAY",
)


class ExplanationFidelityError(ValueError):
    """Fail-closed EXP-05 preparation contract error."""

    def __init__(self, issue_code: str, message: str) -> None:
        super().__init__(f"{issue_code}: {message}")
        self.issue_code = issue_code
        self.message = message


def _fail(code: str, message: str) -> None:
    raise ExplanationFidelityError(code, message)


def _text(value: object, name: str) -> str:
    if type(value) is not str or not value:
        _fail("EXP05_TEXT_INVALID", f"{name} must be a non-empty exact string")
    return value


def _hash(value: object, name: str) -> str:
    result = _text(value, name)
    if len(result) != 64 or any(character not in "0123456789abcdef" for character in result):
        _fail("EXP05_HASH_INVALID", f"{name} must be a lowercase SHA-256")
    return result


def _exact_bool(value: object, name: str) -> bool:
    if type(value) is not bool:
        _fail("EXP05_BOOL_INVALID", f"{name} must be an exact bool")
    return value


def _exact_nonnegative_int(value: object, name: str) -> int:
    if type(value) is not int or value < 0:
        _fail("EXP05_INTEGER_INVALID", f"{name} must be a non-negative exact int")
    return value


def _numeric_bindings_document(
    bindings: tuple[NumericReferenceBindingV1, ...],
) -> list[dict[str, Any]]:
    return [item.to_dict() for item in bindings]


def _validate_numeric_bindings(bindings: object) -> tuple[NumericReferenceBindingV1, ...]:
    if type(bindings) is not tuple:
        _fail("EXP05_NUMERIC_BINDINGS_TYPE_INVALID", "numeric bindings must be an exact tuple")
    if any(type(item) is not NumericReferenceBindingV1 for item in bindings):
        _fail("EXP05_NUMERIC_BINDING_TYPE_INVALID", "numeric binding type differs")
    if tuple(item.numeric_role for item in bindings) != V4_NUMERIC_ROLES:
        _fail("EXP05_NUMERIC_BINDING_ORDER_INVALID", "all ten roles are required in authority order")
    if len({item.reference_id for item in bindings}) != len(V4_NUMERIC_ROLES):
        _fail("EXP05_NUMERIC_REFERENCE_DUPLICATE", "numeric reference IDs duplicate")
    return bindings


def _trace_payload(trace: FormalV4RuntimeTraceV1) -> dict[str, Any]:
    return {
        "alarm_emitted": trace.alarm_emitted,
        "authorization_hash": trace.authorization_hash,
        "descriptor_hash": trace.descriptor_hash,
        "execution_context_hash": trace.execution_context_hash,
        "final_outcome": trace.final_outcome,
        "opportunity_id": trace.opportunity_id,
        "reason": trace.reason,
        "relation_id": trace.relation_id,
        "runtime_version": FORMAL_V4_RUNTIME_VERSION,
    }


def _authorization_payload(receipt: FormalV4RuntimeAuthorizationReceiptV1) -> dict[str, Any]:
    document = receipt.to_dict()
    observed_hash = document.pop("authorization_hash", None)
    if observed_hash != receipt.authorization_hash:
        _fail("EXP05_AUTHORIZATION_DOCUMENT_MISMATCH", "authorization document differs")
    return document


def _observation_window_payload(window: FormalV4ObservationWindowV1) -> dict[str, Any]:
    """Return the private hash preimage; callers only persist its hash."""

    return {
        "event_index": window.event_index,
        "feature_contract_hash": window.feature_contract_hash,
        "file_contract_hash": window.file_contract_hash,
        "future_window_complete": window.future_window_complete,
        "opportunity_id": window.opportunity_id,
        "relation_id": window.relation_id,
        "sampling_contract_hash": window.sampling_contract_hash,
        "seconds_since_previous_source_trigger": window.seconds_since_previous_source_trigger,
        "seconds_to_nearest_other_source_trigger": window.seconds_to_nearest_other_source_trigger,
        "source_post_values": list(window.source_post_values),
        "source_pre_values": list(window.source_pre_values),
        "target_baseline_values": list(window.target_baseline_values),
        "target_response_start_index": window.target_response_start_index,
        "target_response_values": list(window.target_response_values),
        "window_contract": "validation_v2_formal_v4_observation_window_hash_v1",
    }


def hash_formal_v4_observation_window_v1(window: FormalV4ObservationWindowV1) -> str:
    if type(window) is not FormalV4ObservationWindowV1:
        _fail("EXP05_WINDOW_TYPE_INVALID", "observation window type differs")
    return canonical_document_hash_v1(_observation_window_payload(window))


@dataclass(frozen=True)
class MaterializedFormalV4TraceV1:
    trace_id: str
    runtime_version: str
    runtime_trace_hash: str
    trace_contract_hash: str
    method_id: str
    config_id: str
    experiment_id: str
    portfolio_id: str
    portfolio_authority_hash: str
    descriptor_set_hash: str
    authorization_id: str
    authorization_hash: str
    execution_context_hash: str
    evaluator_contract_hash: str
    source_commit: str
    opportunity_id: str
    relation_id: str
    descriptor_hash: str
    relation_binding_hash: str
    semantic_execution_hash: str
    source: str
    target: str
    source_direction: str
    target_direction: str
    selected_horizon_seconds: int
    numeric_authority_hash: str
    ordered_numeric_reference_bindings: tuple[NumericReferenceBindingV1, ...]
    observation_window_hash: str
    feature_contract_hash: str
    file_contract_hash: str
    sampling_contract_hash: str
    event_index: int
    target_response_start_index: int
    final_outcome: str
    reason: str
    alarm_emitted: bool
    raw_numeric_values_embedded: bool
    raw_observations_embedded: bool
    labels_accessed: bool
    causal_claim_allowed: bool
    scientific_runner_authorized: bool
    self_hash: str

    def __post_init__(self) -> None:
        for name in (
            "trace_id", "runtime_version", "method_id", "config_id", "experiment_id",
            "portfolio_id", "authorization_id", "source_commit", "opportunity_id",
            "relation_id", "source", "target", "source_direction", "target_direction",
            "final_outcome", "reason",
        ):
            _text(getattr(self, name), name)
        for name in (
            "runtime_trace_hash", "trace_contract_hash", "portfolio_authority_hash",
            "descriptor_set_hash", "authorization_hash", "execution_context_hash",
            "evaluator_contract_hash", "descriptor_hash", "relation_binding_hash",
            "semantic_execution_hash", "numeric_authority_hash", "observation_window_hash",
            "feature_contract_hash", "file_contract_hash", "sampling_contract_hash", "self_hash",
        ):
            _hash(getattr(self, name), name)
        _exact_nonnegative_int(self.event_index, "event_index")
        _exact_nonnegative_int(self.target_response_start_index, "target_response_start_index")
        if type(self.selected_horizon_seconds) is not int or self.selected_horizon_seconds <= 0:
            _fail("EXP05_HORIZON_INVALID", "selected horizon must be a positive exact int")
        _validate_numeric_bindings(self.ordered_numeric_reference_bindings)
        _exact_bool(self.alarm_emitted, "alarm_emitted")
        for name in (
            "raw_numeric_values_embedded", "raw_observations_embedded", "labels_accessed",
            "causal_claim_allowed", "scientific_runner_authorized",
        ):
            _exact_bool(getattr(self, name), name)

    def _payload(self) -> dict[str, Any]:
        return {
            "alarm_emitted": self.alarm_emitted,
            "artifact_type": "validation_v2_materialized_formal_v4_trace_v1",
            "authorization_hash": self.authorization_hash,
            "authorization_id": self.authorization_id,
            "causal_claim_allowed": self.causal_claim_allowed,
            "config_id": self.config_id,
            "descriptor_hash": self.descriptor_hash,
            "descriptor_set_hash": self.descriptor_set_hash,
            "evaluator_contract_hash": self.evaluator_contract_hash,
            "event_index": self.event_index,
            "execution_context_hash": self.execution_context_hash,
            "experiment_id": self.experiment_id,
            "feature_contract_hash": self.feature_contract_hash,
            "file_contract_hash": self.file_contract_hash,
            "final_outcome": self.final_outcome,
            "labels_accessed": self.labels_accessed,
            "materialized_trace_version": EXP05_MATERIALIZED_TRACE_VERSION,
            "method_id": self.method_id,
            "numeric_authority_hash": self.numeric_authority_hash,
            "observation_window_hash": self.observation_window_hash,
            "opportunity_id": self.opportunity_id,
            "ordered_numeric_reference_bindings": _numeric_bindings_document(self.ordered_numeric_reference_bindings),
            "portfolio_authority_hash": self.portfolio_authority_hash,
            "portfolio_id": self.portfolio_id,
            "raw_numeric_values_embedded": self.raw_numeric_values_embedded,
            "raw_observations_embedded": self.raw_observations_embedded,
            "reason": self.reason,
            "relation_binding_hash": self.relation_binding_hash,
            "relation_id": self.relation_id,
            "runtime_trace_hash": self.runtime_trace_hash,
            "runtime_version": self.runtime_version,
            "sampling_contract_hash": self.sampling_contract_hash,
            "schema_version": EXP05_SCHEMA_VERSION,
            "scientific_runner_authorized": self.scientific_runner_authorized,
            "selected_horizon_seconds": self.selected_horizon_seconds,
            "semantic_execution_hash": self.semantic_execution_hash,
            "source": self.source,
            "source_commit": self.source_commit,
            "source_direction": self.source_direction,
            "target": self.target,
            "target_direction": self.target_direction,
            "target_response_start_index": self.target_response_start_index,
            "trace_contract_hash": self.trace_contract_hash,
            "trace_id": self.trace_id,
        }

    @property
    def expected_self_hash(self) -> str:
        return canonical_document_hash_v1(self._payload())

    def to_dict(self) -> dict[str, Any]:
        return {**self._payload(), "self_hash": self.self_hash}


def validate_materialized_formal_v4_trace_v1(trace: MaterializedFormalV4TraceV1) -> str:
    if type(trace) is not MaterializedFormalV4TraceV1:
        _fail("EXP05_MATERIALIZED_TRACE_TYPE_INVALID", "materialized trace type differs")
    if trace.self_hash != trace.expected_self_hash:
        _fail("EXP05_MATERIALIZED_TRACE_HASH_MISMATCH", "materialized trace self-hash differs")
    if trace.runtime_version != FORMAL_V4_RUNTIME_VERSION:
        _fail("EXP05_RUNTIME_VERSION_MISMATCH", "runtime version differs")
    if trace.trace_contract_hash != FORMAL_V4_TRACE_CONTRACT_HASH:
        _fail("EXP05_TRACE_CONTRACT_MISMATCH", "trace contract differs")
    if trace.source == trace.target:
        _fail("EXP05_SELF_RELATION_PROHIBITED", "source and target must differ")
    if trace.source_direction not in _SOURCE_DIRECTION_KO or trace.target_direction not in _TARGET_DIRECTION_KO:
        _fail("EXP05_DIRECTION_INVALID", "direction differs from Formal V4")
    if trace.target_response_start_index != trace.event_index + trace.selected_horizon_seconds:
        _fail("EXP05_HORIZON_COORDINATE_MISMATCH", "response start does not replay horizon")
    if (trace.final_outcome, trace.reason, trace.alarm_emitted) not in _OUTCOME_REASON_ALARM:
        _fail("EXP05_OUTCOME_MATRIX_INVALID", "outcome, reason, and alarm tuple differs")
    if any((trace.raw_numeric_values_embedded, trace.raw_observations_embedded, trace.labels_accessed, trace.causal_claim_allowed)):
        _fail("EXP05_PRIVATE_OR_CLAIM_BOUNDARY_VIOLATION", "raw values, labels, or causal claims are prohibited")
    if trace.scientific_runner_authorized:
        _fail("EXP05_SCIENTIFIC_RUNNER_NOT_AUTHORIZED", "preparation contract cannot authorize scientific execution")
    return trace.self_hash


def materialize_formal_v4_trace_v1(
    *,
    runtime_trace: FormalV4RuntimeTraceV1,
    descriptor: FormalV4RuleDescriptorV1,
    authority: FormalV4PortfolioAuthorityV1,
    receipt: FormalV4RuntimeAuthorizationReceiptV1,
    execution_context: FormalV4ExecutionContextV1,
    observation_window: FormalV4ObservationWindowV1,
) -> MaterializedFormalV4TraceV1:
    """Create a public-safe detached preparation trace; not a scientific runner."""

    if type(runtime_trace) is not FormalV4RuntimeTraceV1:
        _fail("EXP05_RUNTIME_TRACE_TYPE_INVALID", "runtime trace type differs")
    if type(descriptor) is not FormalV4RuleDescriptorV1:
        _fail("EXP05_DESCRIPTOR_TYPE_INVALID", "descriptor type differs")
    if type(authority) is not FormalV4PortfolioAuthorityV1:
        _fail("EXP05_AUTHORITY_TYPE_INVALID", "portfolio authority type differs")
    if type(receipt) is not FormalV4RuntimeAuthorizationReceiptV1:
        _fail("EXP05_RECEIPT_TYPE_INVALID", "authorization receipt type differs")
    if type(execution_context) is not FormalV4ExecutionContextV1:
        _fail("EXP05_CONTEXT_TYPE_INVALID", "execution context type differs")
    if type(observation_window) is not FormalV4ObservationWindowV1:
        _fail("EXP05_WINDOW_TYPE_INVALID", "observation window type differs")
    if runtime_trace.trace_hash != canonical_document_hash_v1(_trace_payload(runtime_trace)):
        _fail("EXP05_RUNTIME_TRACE_HASH_MISMATCH", "runtime trace does not replay")
    if (runtime_trace.final_outcome, runtime_trace.reason, runtime_trace.alarm_emitted) not in _OUTCOME_REASON_ALARM:
        _fail("EXP05_OUTCOME_MATRIX_INVALID", "runtime outcome tuple differs")
    if receipt.authorization_hash != canonical_document_hash_v1(_authorization_payload(receipt)):
        _fail("EXP05_AUTHORIZATION_HASH_MISMATCH", "authorization receipt does not replay")
    if descriptor not in authority.descriptors:
        _fail("EXP05_DESCRIPTOR_NOT_IN_PORTFOLIO", "descriptor is outside the exact portfolio")
    if (
        runtime_trace.descriptor_hash != descriptor.descriptor_hash
        or runtime_trace.relation_id != descriptor.relation_id
        or runtime_trace.authorization_hash != receipt.authorization_hash
        or runtime_trace.execution_context_hash != execution_context.context_hash
        or runtime_trace.opportunity_id != observation_window.opportunity_id
        or observation_window.relation_id != descriptor.relation_id
    ):
        _fail("EXP05_RUNTIME_TRACE_BINDING_MISMATCH", "runtime trace grounding differs")
    if (
        receipt.authority_hash != authority.authority_hash
        or receipt.portfolio_id != authority.portfolio_id
        or receipt.descriptor_set_hash != authority.descriptor_set_hash
        or receipt.numeric_authority_hash != authority.numeric_authority_binding.content_sha256
        or receipt.evaluator_contract_hash != authority.evaluator_contract_hash
        or receipt.execution_context_hash != execution_context.context_hash
        or authority.source_commit != execution_context.source_commit
        or receipt.runtime_config_hash != execution_context.runtime_config_hash
    ):
        _fail("EXP05_AUTHORITY_BINDING_MISMATCH", "portfolio, receipt, or context differs")
    context_authority_pairs = (
        (execution_context.relation_authority_binding, authority.relation_authority_binding),
        (execution_context.numeric_authority_binding, authority.numeric_authority_binding),
        (execution_context.feature_contract_binding, authority.feature_contract_binding),
        (execution_context.file_contract_binding, authority.file_contract_binding),
        (execution_context.sampling_contract_binding, authority.sampling_contract_binding),
    )
    if any(observed != expected for observed, expected in context_authority_pairs):
        _fail("EXP05_CONTEXT_AUTHORITY_BINDING_MISMATCH", "execution context differs from portfolio authority")
    if (
        receipt.feature_contract_hash != authority.feature_contract_binding.content_sha256
        or receipt.file_contract_hash != authority.file_contract_binding.content_sha256
        or receipt.sampling_contract_hash != authority.sampling_contract_binding.content_sha256
    ):
        _fail("EXP05_RECEIPT_AUTHORITY_BINDING_MISMATCH", "receipt contract hashes differ from portfolio authority")
    if (
        descriptor.numeric_authority_hash != receipt.numeric_authority_hash
        or observation_window.feature_contract_hash != receipt.feature_contract_hash
        or observation_window.file_contract_hash != receipt.file_contract_hash
        or observation_window.sampling_contract_hash != receipt.sampling_contract_hash
    ):
        _fail("EXP05_PROVENANCE_BINDING_MISMATCH", "numeric or observation authority differs")
    if observation_window.target_response_start_index != observation_window.event_index + descriptor.selected_horizon_seconds:
        _fail("EXP05_HORIZON_COORDINATE_MISMATCH", "response start does not replay descriptor horizon")

    provisional = MaterializedFormalV4TraceV1(
        trace_id=f"EXP05-TRACE-{runtime_trace.trace_hash[:16]}",
        runtime_version=FORMAL_V4_RUNTIME_VERSION,
        runtime_trace_hash=runtime_trace.trace_hash,
        trace_contract_hash=FORMAL_V4_TRACE_CONTRACT_HASH,
        method_id=authority.method_id,
        config_id=authority.config_id,
        experiment_id=authority.experiment_id,
        portfolio_id=authority.portfolio_id,
        portfolio_authority_hash=authority.authority_hash,
        descriptor_set_hash=authority.descriptor_set_hash,
        authorization_id=receipt.authorization_id,
        authorization_hash=receipt.authorization_hash,
        execution_context_hash=execution_context.context_hash,
        evaluator_contract_hash=authority.evaluator_contract_hash,
        source_commit=authority.source_commit,
        opportunity_id=runtime_trace.opportunity_id,
        relation_id=descriptor.relation_id,
        descriptor_hash=descriptor.descriptor_hash,
        relation_binding_hash=descriptor.relation_binding_hash,
        semantic_execution_hash=descriptor.semantic_execution_hash,
        source=descriptor.source,
        target=descriptor.target,
        source_direction=descriptor.source_direction,
        target_direction=descriptor.target_direction,
        selected_horizon_seconds=descriptor.selected_horizon_seconds,
        numeric_authority_hash=descriptor.numeric_authority_hash,
        ordered_numeric_reference_bindings=tuple(descriptor.numeric_reference_bindings),
        observation_window_hash=hash_formal_v4_observation_window_v1(observation_window),
        feature_contract_hash=observation_window.feature_contract_hash,
        file_contract_hash=observation_window.file_contract_hash,
        sampling_contract_hash=observation_window.sampling_contract_hash,
        event_index=observation_window.event_index,
        target_response_start_index=observation_window.target_response_start_index,
        final_outcome=runtime_trace.final_outcome,
        reason=runtime_trace.reason,
        alarm_emitted=runtime_trace.alarm_emitted,
        raw_numeric_values_embedded=False,
        raw_observations_embedded=False,
        labels_accessed=False,
        causal_claim_allowed=False,
        scientific_runner_authorized=EXP05_SCIENTIFIC_RUNNER_AUTHORIZED,
        self_hash=_HASH_ZERO,
    )
    result = replace(provisional, self_hash=provisional.expected_self_hash)
    validate_materialized_formal_v4_trace_v1(result)
    return result


@dataclass(frozen=True)
class FormalV4ExplanationRecordV1:
    explanation_id: str
    materialized_trace_hash: str
    runtime_trace_hash: str
    descriptor_hash: str
    portfolio_id: str
    portfolio_authority_hash: str
    authorization_hash: str
    execution_context_hash: str
    source: str
    target: str
    source_direction: str
    target_direction: str
    selected_horizon_seconds: int
    numeric_authority_hash: str
    ordered_numeric_reference_bindings: tuple[NumericReferenceBindingV1, ...]
    final_outcome: str
    reason: str
    alarm_emitted: bool
    natural_language_text: str
    renderer_version: str
    renderer_contract_hash: str
    causal_claim_made: bool
    root_cause_claim_made: bool
    human_usefulness_evaluated: bool
    artifact_hash: str

    def __post_init__(self) -> None:
        for name in (
            "explanation_id", "portfolio_id", "source", "target", "source_direction",
            "target_direction", "final_outcome", "reason", "natural_language_text", "renderer_version",
        ):
            _text(getattr(self, name), name)
        for name in (
            "materialized_trace_hash", "runtime_trace_hash", "descriptor_hash",
            "portfolio_authority_hash", "authorization_hash", "execution_context_hash",
            "numeric_authority_hash", "renderer_contract_hash", "artifact_hash",
        ):
            _hash(getattr(self, name), name)
        if type(self.selected_horizon_seconds) is not int or self.selected_horizon_seconds <= 0:
            _fail("EXP05_HORIZON_INVALID", "selected horizon must be a positive exact int")
        _validate_numeric_bindings(self.ordered_numeric_reference_bindings)
        for name in (
            "alarm_emitted", "causal_claim_made", "root_cause_claim_made", "human_usefulness_evaluated",
        ):
            _exact_bool(getattr(self, name), name)

    def _payload(self) -> dict[str, Any]:
        return {
            "alarm_emitted": self.alarm_emitted,
            "artifact_type": "validation_v2_formal_v4_explanation_record_v1",
            "authorization_hash": self.authorization_hash,
            "causal_claim_made": self.causal_claim_made,
            "descriptor_hash": self.descriptor_hash,
            "execution_context_hash": self.execution_context_hash,
            "explanation_id": self.explanation_id,
            "final_outcome": self.final_outcome,
            "human_usefulness_evaluated": self.human_usefulness_evaluated,
            "materialized_trace_hash": self.materialized_trace_hash,
            "natural_language_text": self.natural_language_text,
            "numeric_authority_hash": self.numeric_authority_hash,
            "ordered_numeric_reference_bindings": _numeric_bindings_document(self.ordered_numeric_reference_bindings),
            "portfolio_authority_hash": self.portfolio_authority_hash,
            "portfolio_id": self.portfolio_id,
            "reason": self.reason,
            "renderer_contract_hash": self.renderer_contract_hash,
            "renderer_version": self.renderer_version,
            "root_cause_claim_made": self.root_cause_claim_made,
            "runtime_trace_hash": self.runtime_trace_hash,
            "schema_version": EXP05_SCHEMA_VERSION,
            "selected_horizon_seconds": self.selected_horizon_seconds,
            "source": self.source,
            "source_direction": self.source_direction,
            "target": self.target,
            "target_direction": self.target_direction,
        }

    @property
    def expected_artifact_hash(self) -> str:
        return canonical_document_hash_v1(self._payload())

    def to_dict(self) -> dict[str, Any]:
        return {**self._payload(), "artifact_hash": self.artifact_hash}


def _render_text(trace: MaterializedFormalV4TraceV1) -> str:
    return (
        f"{trace.source}의 {_SOURCE_DIRECTION_KO[trace.source_direction]} 이후 승인된 "
        f"{trace.selected_horizon_seconds}초 지평에서 {trace.target}의 "
        f"{_TARGET_DIRECTION_KO[trace.target_direction]} 응답을 확인했습니다. "
        f"{_OUTCOME_CLAUSE_KO[(trace.final_outcome, trace.reason)]} "
        "수치 기준은 승인된 provenance 참조에만 결속됩니다."
    )


def render_formal_v4_explanation_v1(
    trace: MaterializedFormalV4TraceV1,
) -> FormalV4ExplanationRecordV1:
    validate_materialized_formal_v4_trace_v1(trace)
    provisional = FormalV4ExplanationRecordV1(
        explanation_id=f"EXP05-EXPLANATION-{trace.self_hash[:16]}",
        materialized_trace_hash=trace.self_hash,
        runtime_trace_hash=trace.runtime_trace_hash,
        descriptor_hash=trace.descriptor_hash,
        portfolio_id=trace.portfolio_id,
        portfolio_authority_hash=trace.portfolio_authority_hash,
        authorization_hash=trace.authorization_hash,
        execution_context_hash=trace.execution_context_hash,
        source=trace.source,
        target=trace.target,
        source_direction=trace.source_direction,
        target_direction=trace.target_direction,
        selected_horizon_seconds=trace.selected_horizon_seconds,
        numeric_authority_hash=trace.numeric_authority_hash,
        ordered_numeric_reference_bindings=tuple(trace.ordered_numeric_reference_bindings),
        final_outcome=trace.final_outcome,
        reason=trace.reason,
        alarm_emitted=trace.alarm_emitted,
        natural_language_text=_render_text(trace),
        renderer_version=EXP05_RENDERER_VERSION,
        renderer_contract_hash=EXP05_RENDERER_CONTRACT_HASH,
        causal_claim_made=False,
        root_cause_claim_made=False,
        human_usefulness_evaluated=False,
        artifact_hash=_HASH_ZERO,
    )
    return replace(provisional, artifact_hash=provisional.expected_artifact_hash)


@dataclass(frozen=True)
class ExplanationFidelityCheckV1:
    check_id: str
    passed: bool
    expected_hash: str
    observed_hash: str

    def __post_init__(self) -> None:
        if self.check_id not in EXP05_FIDELITY_CHECK_IDS:
            _fail("EXP05_CHECK_ID_INVALID", "fidelity check ID differs")
        _exact_bool(self.passed, "passed")
        _hash(self.expected_hash, "expected_hash")
        _hash(self.observed_hash, "observed_hash")

    def to_dict(self) -> dict[str, Any]:
        return {
            "check_id": self.check_id,
            "expected_hash": self.expected_hash,
            "observed_hash": self.observed_hash,
            "passed": self.passed,
        }


@dataclass(frozen=True)
class FormalV4ExplanationFidelityResultV1:
    materialized_trace_hash: str
    explanation_artifact_hash: str
    checks: tuple[ExplanationFidelityCheckV1, ...]
    all_checks_passed: bool
    validator_version: str
    result_hash: str

    def __post_init__(self) -> None:
        _hash(self.materialized_trace_hash, "materialized_trace_hash")
        _hash(self.explanation_artifact_hash, "explanation_artifact_hash")
        _hash(self.result_hash, "result_hash")
        if type(self.checks) is not tuple or any(type(item) is not ExplanationFidelityCheckV1 for item in self.checks):
            _fail("EXP05_CHECKS_TYPE_INVALID", "checks must be an exact typed tuple")
        if tuple(item.check_id for item in self.checks) != EXP05_FIDELITY_CHECK_IDS:
            _fail("EXP05_CHECK_ORDER_INVALID", "all fidelity checks are required in order")
        _exact_bool(self.all_checks_passed, "all_checks_passed")
        _text(self.validator_version, "validator_version")

    def _payload(self) -> dict[str, Any]:
        return {
            "all_checks_passed": self.all_checks_passed,
            "artifact_type": "validation_v2_formal_v4_explanation_fidelity_result_v1",
            "checks": [item.to_dict() for item in self.checks],
            "explanation_artifact_hash": self.explanation_artifact_hash,
            "materialized_trace_hash": self.materialized_trace_hash,
            "schema_version": EXP05_SCHEMA_VERSION,
            "validator_version": self.validator_version,
        }

    @property
    def expected_result_hash(self) -> str:
        return canonical_document_hash_v1(self._payload())

    def to_dict(self) -> dict[str, Any]:
        return {**self._payload(), "result_hash": self.result_hash}


def _value_hash(value: object) -> str:
    return canonical_document_hash_v1({"value": value})


def validate_formal_v4_explanation_fidelity_v1(
    trace: MaterializedFormalV4TraceV1,
    explanation: FormalV4ExplanationRecordV1,
) -> FormalV4ExplanationFidelityResultV1:
    validate_materialized_formal_v4_trace_v1(trace)
    if type(explanation) is not FormalV4ExplanationRecordV1:
        _fail("EXP05_EXPLANATION_TYPE_INVALID", "explanation type differs")
    expected_a = render_formal_v4_explanation_v1(trace)
    expected_b = render_formal_v4_explanation_v1(trace)
    exact_replay = canonical_json_bytes_v1(expected_a.to_dict()) == canonical_json_bytes_v1(expected_b.to_dict())
    artifact_integrity = explanation.artifact_hash == explanation.expected_artifact_hash
    comparisons: tuple[tuple[str, object, object, bool], ...] = (
        ("SOURCE_MATCH", expected_a.source, explanation.source, expected_a.source == explanation.source),
        ("TARGET_MATCH", expected_a.target, explanation.target, expected_a.target == explanation.target),
        ("SOURCE_DIRECTION_MATCH", expected_a.source_direction, explanation.source_direction, expected_a.source_direction == explanation.source_direction),
        ("TARGET_DIRECTION_MATCH", expected_a.target_direction, explanation.target_direction, expected_a.target_direction == explanation.target_direction),
        ("HORIZON_MATCH", expected_a.selected_horizon_seconds, explanation.selected_horizon_seconds, expected_a.selected_horizon_seconds == explanation.selected_horizon_seconds),
        (
            "NUMERIC_PROVENANCE_MATCH",
            [trace.numeric_authority_hash, _numeric_bindings_document(expected_a.ordered_numeric_reference_bindings)],
            [explanation.numeric_authority_hash, _numeric_bindings_document(explanation.ordered_numeric_reference_bindings)],
            trace.numeric_authority_hash == explanation.numeric_authority_hash
            and expected_a.ordered_numeric_reference_bindings == explanation.ordered_numeric_reference_bindings,
        ),
        (
            "OUTCOME_MATCH",
            [expected_a.final_outcome, expected_a.reason, expected_a.alarm_emitted],
            [explanation.final_outcome, explanation.reason, explanation.alarm_emitted],
            (expected_a.final_outcome, expected_a.reason, expected_a.alarm_emitted)
            == (explanation.final_outcome, explanation.reason, explanation.alarm_emitted),
        ),
        ("NO_NEW_VARIABLE", expected_a.natural_language_text, explanation.natural_language_text, expected_a.natural_language_text == explanation.natural_language_text),
        ("NO_NEW_NUMBER", expected_a.natural_language_text, explanation.natural_language_text, expected_a.natural_language_text == explanation.natural_language_text),
        (
            "NO_CAUSAL_CLAIM",
            [expected_a.natural_language_text, False, False],
            [explanation.natural_language_text, explanation.causal_claim_made, explanation.root_cause_claim_made],
            expected_a.natural_language_text == explanation.natural_language_text
            and explanation.causal_claim_made is False
            and explanation.root_cause_claim_made is False,
        ),
        (
            "DETERMINISTIC_REPLAY",
            expected_a.to_dict(),
            explanation.to_dict(),
            exact_replay
            and artifact_integrity
            and explanation.renderer_version == EXP05_RENDERER_VERSION
            and explanation.renderer_contract_hash == EXP05_RENDERER_CONTRACT_HASH
            and explanation.materialized_trace_hash == trace.self_hash
            and explanation.runtime_trace_hash == trace.runtime_trace_hash
            and explanation.descriptor_hash == trace.descriptor_hash
            and explanation.portfolio_id == trace.portfolio_id
            and explanation.portfolio_authority_hash == trace.portfolio_authority_hash
            and explanation.authorization_hash == trace.authorization_hash
            and explanation.execution_context_hash == trace.execution_context_hash
            and explanation.human_usefulness_evaluated is False
            and canonical_json_bytes_v1(expected_a.to_dict()) == canonical_json_bytes_v1(explanation.to_dict()),
        ),
    )
    checks = tuple(
        ExplanationFidelityCheckV1(
            check_id=check_id,
            passed=passed,
            expected_hash=_value_hash(expected),
            observed_hash=_value_hash(observed),
        )
        for check_id, expected, observed, passed in comparisons
    )
    all_passed = all(item.passed for item in checks)
    provisional = FormalV4ExplanationFidelityResultV1(
        materialized_trace_hash=trace.self_hash,
        explanation_artifact_hash=explanation.artifact_hash,
        checks=checks,
        all_checks_passed=all_passed,
        validator_version=EXP05_FIDELITY_VALIDATOR_VERSION,
        result_hash=_HASH_ZERO,
    )
    return replace(provisional, result_hash=provisional.expected_result_hash)
