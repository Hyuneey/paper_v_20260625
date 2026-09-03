"""Prospective VALIDATION V2 split, selection, and evaluation protocol.

This module freezes governance semantics only.  It contains no dataset reader,
metric runner, prediction runner, or held-out authorization.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from hashlib import sha256
import json
from typing import Any, Mapping

from .prediction_custody_v1 import LabelAccessCapabilityV1, validate_label_access_capability_v1


class ValidationProtocolError(RuntimeError):
    pass


class SplitRoleV1(str, Enum):
    NORMAL_FIT_PRIMARY = "NORMAL_FIT_PRIMARY"
    NORMAL_FIT_SECONDARY = "NORMAL_FIT_SECONDARY"
    NORMAL_CONFIRMATION_CALIBRATION = "NORMAL_CONFIRMATION_CALIBRATION"
    NORMAL_POLICY_SELECTION_SANITY = "NORMAL_POLICY_SELECTION_SANITY"
    DEVELOPMENT_ONLY = "DEVELOPMENT_ONLY"
    FUTURE_FINAL_HELDOUT = "FUTURE_FINAL_HELDOUT"


class ProtocolOperationV1(str, Enum):
    CANDIDATE_LEARNING = "CANDIDATE_LEARNING"
    RELATION_FIT = "RELATION_FIT"
    NUMERIC_FIT = "NUMERIC_FIT"
    DETECTOR_FIT = "DETECTOR_FIT"
    RELATION_CONFIRMATION = "RELATION_CONFIRMATION"
    THRESHOLD_CALIBRATION = "THRESHOLD_CALIBRATION"
    NORMAL_POLICY_SELECTION = "NORMAL_POLICY_SELECTION"
    NORMAL_SANITY = "NORMAL_SANITY"
    DEVELOPMENT_PREDICTION = "DEVELOPMENT_PREDICTION"
    DEVELOPMENT_LABEL_METRICS = "DEVELOPMENT_LABEL_METRICS"
    FINAL_PREDICTION = "FINAL_PREDICTION"
    FINAL_LABEL_METRICS = "FINAL_LABEL_METRICS"


class ProtocolGuardStateV1(str, Enum):
    CREATED = "CREATED"
    POLICIES_FROZEN = "POLICIES_FROZEN"
    DEVELOPMENT_PREDICTION_FROZEN = "DEVELOPMENT_PREDICTION_FROZEN"
    DEVELOPMENT_LABELS_ACCESSED = "DEVELOPMENT_LABELS_ACCESSED"
    COMPLETE = "COMPLETE"


def _fail(code: str) -> None:
    raise ValidationProtocolError(code)


def _canonical_bytes(document: Mapping[str, Any]) -> bytes:
    return json.dumps(document, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


@dataclass(frozen=True)
class SplitAssignmentV1:
    split_id: str
    role: SplitRoleV1
    labels_allowed: bool
    allowed_operations: tuple[ProtocolOperationV1, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "split_id": self.split_id,
            "role": self.role.value,
            "labels_allowed": self.labels_allowed,
            "allowed_operations": [item.value for item in self.allowed_operations],
        }


@dataclass(frozen=True)
class EventMetricPolicyV1:
    sampling_seconds: int = 1
    coordinate_scope: str = "FILE_LOCAL_ROW_INDEX"
    timestamp_validation: str = "STRICT_ONE_SECOND_MONOTONIC_NO_DUPLICATE_NO_MISSING"
    positive_label_condition: str = "STRICT_INTEGER_ONE"
    event_construction: str = "MAXIMAL_CONTIGUOUS_POSITIVE_RUN_HALF_OPEN"
    event_file_boundary: str = "NO_CROSS_FILE_MERGE"
    event_independence: str = "NOT_ESTABLISHED"
    event_hit_rule: str = "ANY_ALARM_SECOND_INSIDE_SAME_FILE_HALF_OPEN_EVENT"
    point_adjustment: str = "PROHIBITED"
    grace_window_seconds: int = 0
    minimum_alarm_duration_seconds: int = 0
    episode_construction: str = "MAXIMAL_CONTIGUOUS_UNIQUE_ALARM_SECONDS"
    episode_allowed_gap_seconds: int = 0
    episode_file_boundary: str = "NO_CROSS_FILE_MERGE"
    mixed_episode_policy: str = "ANY_ATTACK_OVERLAP_EXCLUDES_WHOLE_EPISODE_FROM_NORMAL_FP"
    normal_exposure: str = "STRICT_LABEL_ZERO_ROWS_TIMES_ONE_SECOND"
    far_formula: str = "NORMAL_FALSE_EPISODES_DIVIDED_BY_NORMAL_EXPOSURE_HOURS"
    false_episode_definition: str = "COMPLETE_EPISODE_WITH_NO_ATTACK_EVENT_OVERLAP"
    zero_attack_events: str = "UNDEFINED"
    zero_normal_exposure: str = "UNDEFINED"
    d1_common_alarm_states: tuple[str, ...] = ("FAIL",)
    d1_common_no_alarm_states: tuple[str, ...] = ("PASS", "ABSTAIN", "NO_OPPORTUNITY")
    d1_system_error_policy: str = "FAIL_CLOSED_NEVER_COERCE_TO_NO_ALARM"

    def __post_init__(self) -> None:
        if self.sampling_seconds != 1 or self.grace_window_seconds != 0:
            _fail("EVENT_TIME_POLICY_MUTATION_REJECTED")
        if self.minimum_alarm_duration_seconds != 0 or self.episode_allowed_gap_seconds != 0:
            _fail("POINT_ADJUSTMENT_OR_GAP_REJECTED")
        if self.point_adjustment != "PROHIBITED" or self.event_independence != "NOT_ESTABLISHED":
            _fail("EVENT_CLAIM_POLICY_MUTATION_REJECTED")
        if self.zero_attack_events != "UNDEFINED" or self.zero_normal_exposure != "UNDEFINED":
            _fail("UNDEFINED_METRIC_POLICY_MUTATION_REJECTED")
        if self.d1_common_alarm_states != ("FAIL",) or self.d1_system_error_policy != "FAIL_CLOSED_NEVER_COERCE_TO_NO_ALARM":
            _fail("D1_COMMON_INTERFACE_POLICY_MUTATION_REJECTED")

    def to_dict(self) -> dict[str, Any]:
        return {name: (value.value if isinstance(value, Enum) else value) for name, value in self.__dict__.items()}


@dataclass(frozen=True)
class ReportingPolicyV1:
    evaluation_status: str = "DEVELOPMENT_ONLY"
    primary_metrics: tuple[str, ...] = ("ATTACK_EVENT_RECALL", "NORMAL_FAR_EPISODES_PER_HOUR")
    secondary_metrics: tuple[str, ...] = ("OVERLAP", "D0_MISS_RECOVERY", "INCREMENTAL_RECALL", "INCREMENTAL_FAR", "RULE_COVERAGE", "ABSTAIN", "CONFLICT")
    required_identity_fields: tuple[str, ...] = (
        "protocol_id", "protocol_hash", "study_id", "evaluation_scope", "method_id",
        "config_id", "authority_hash", "source_commit", "dataset_id", "feature_contract_hash",
        "split_manifest_hash", "sampling_contract_hash", "split_role", "prediction_hash",
        "prediction_freeze_receipt_hash", "label_authority_hash", "metric_contract_hash",
        "policy_freeze_receipt_hash", "environment_hash",
    )
    required_status_fields: tuple[str, ...] = (
        "implementation_status", "execution_status", "integrity_status",
        "scientific_validation_status", "heldout_status",
    )
    inferential_statistics: str = "NONE_UNLESS_SEPARATELY_PREREGISTERED"
    attack_event_independence_claim: str = "PROHIBITED_UNLESS_SEPARATELY_ESTABLISHED"
    required_metric_fields: tuple[str, ...] = (
        "metric_id", "numerator", "denominator", "value", "defined", "undefined_reason",
    )
    required_failure_fields: tuple[str, ...] = ("status", "failure_stage", "failure_code")

    def to_dict(self) -> dict[str, Any]:
        return {
            "evaluation_status": self.evaluation_status,
            "primary_metrics": list(self.primary_metrics),
            "secondary_metrics": list(self.secondary_metrics),
            "required_identity_fields": list(self.required_identity_fields),
            "required_status_fields": list(self.required_status_fields),
            "inferential_statistics": self.inferential_statistics,
            "attack_event_independence_claim": self.attack_event_independence_claim,
            "required_metric_fields": list(self.required_metric_fields),
            "required_failure_fields": list(self.required_failure_fields),
        }


@dataclass(frozen=True)
class PolicyFreezeReceiptV1:
    protocol_hash: str
    source_commit: str
    candidate_set_hash: str
    selection_objective: str
    selection_split: str
    tie_break_rule: str
    selected_config_hash: str
    authority_hash: str
    method_policy_hashes: tuple[str, ...]
    metric_contract_hash: str
    receipt_hash: str

    def body_dict(self) -> dict[str, Any]:
        return {
            "schema": "paperworks.validation_v2.policy_freeze_receipt_v1",
            "schema_version": "1.0.0",
            "protocol_hash": self.protocol_hash,
            "source_commit": self.source_commit,
            "candidate_set_hash": self.candidate_set_hash,
            "selection_objective": self.selection_objective,
            "selection_split": self.selection_split,
            "tie_break_rule": self.tie_break_rule,
            "selected_config_hash": self.selected_config_hash,
            "authority_hash": self.authority_hash,
            "method_policy_hashes": list(self.method_policy_hashes),
            "metric_contract_hash": self.metric_contract_hash,
        }

    def to_dict(self) -> dict[str, Any]:
        document = self.body_dict()
        document["receipt_hash"] = self.receipt_hash
        return document


def _require_sha256(value: str, code: str) -> None:
    if type(value) is not str or len(value) != 64 or any(ch not in "0123456789abcdef" for ch in value):
        _fail(code)


def build_policy_freeze_receipt_v1(
    *,
    protocol: "ValidationProtocolV1",
    candidate_set_hash: str,
    selection_objective: str,
    tie_break_rule: str,
    selected_config_hash: str,
    authority_hash: str,
    method_policy_hashes: tuple[str, ...],
    metric_contract_hash: str,
) -> PolicyFreezeReceiptV1:
    validate_validation_protocol_v1(protocol)
    for value, code in (
        (candidate_set_hash, "INVALID_CANDIDATE_SET_HASH"),
        (selected_config_hash, "INVALID_SELECTED_CONFIG_HASH"),
        (authority_hash, "INVALID_AUTHORITY_HASH"),
        (metric_contract_hash, "INVALID_METRIC_CONTRACT_HASH"),
    ):
        _require_sha256(value, code)
    if type(method_policy_hashes) is not tuple or not method_policy_hashes:
        _fail("MISSING_METHOD_POLICY_HASHES")
    for value in method_policy_hashes:
        _require_sha256(value, "INVALID_METHOD_POLICY_HASH")
    if type(selection_objective) is not str or not selection_objective.strip():
        _fail("MISSING_SELECTION_OBJECTIVE")
    if type(tie_break_rule) is not str or not tie_break_rule.strip():
        _fail("MISSING_TIE_BREAK_RULE")
    provisional = PolicyFreezeReceiptV1(
        protocol_hash=protocol.protocol_hash,
        source_commit=protocol.source_commit,
        candidate_set_hash=candidate_set_hash,
        selection_objective=selection_objective,
        selection_split=protocol.selection_split,
        tie_break_rule=tie_break_rule,
        selected_config_hash=selected_config_hash,
        authority_hash=authority_hash,
        method_policy_hashes=method_policy_hashes,
        metric_contract_hash=metric_contract_hash,
        receipt_hash="",
    )
    return PolicyFreezeReceiptV1(
        **{**provisional.__dict__, "receipt_hash": sha256(_canonical_bytes(provisional.body_dict())).hexdigest()}
    )


def validate_policy_freeze_receipt_v1(
    receipt: PolicyFreezeReceiptV1,
    *,
    protocol: "ValidationProtocolV1",
) -> str:
    if type(receipt) is not PolicyFreezeReceiptV1:
        _fail("WRONG_POLICY_FREEZE_RECEIPT_TYPE")
    expected = build_policy_freeze_receipt_v1(
        protocol=protocol,
        candidate_set_hash=receipt.candidate_set_hash,
        selection_objective=receipt.selection_objective,
        tie_break_rule=receipt.tie_break_rule,
        selected_config_hash=receipt.selected_config_hash,
        authority_hash=receipt.authority_hash,
        method_policy_hashes=receipt.method_policy_hashes,
        metric_contract_hash=receipt.metric_contract_hash,
    )
    if receipt != expected:
        _fail("POLICY_FREEZE_RECEIPT_REPLAY_MISMATCH")
    return receipt.receipt_hash


@dataclass(frozen=True)
class ValidationProtocolV1:
    protocol_id: str
    study_id: str
    evaluation_scope: str
    source_commit: str
    split_assignments: tuple[SplitAssignmentV1, ...]
    event_metric_policy: EventMetricPolicyV1
    reporting_policy: ReportingPolicyV1
    selection_split: str
    development_split: str
    future_heldout_split: str
    heldout_authorized: bool
    no_post_test_tuning: bool
    hyperparameter_provenance_required: bool
    policy_freeze_receipt_required: bool
    prediction_before_label_required: bool
    failure_policy: str
    protocol_hash: str

    def body_dict(self) -> dict[str, Any]:
        return {
            "schema": "paperworks.validation_v2.protocol_v1",
            "schema_version": "1.0.0",
            "protocol_id": self.protocol_id,
            "study_id": self.study_id,
            "evaluation_scope": self.evaluation_scope,
            "source_commit": self.source_commit,
            "split_assignments": [item.to_dict() for item in self.split_assignments],
            "event_metric_policy": self.event_metric_policy.to_dict(),
            "reporting_policy": self.reporting_policy.to_dict(),
            "selection_split": self.selection_split,
            "development_split": self.development_split,
            "future_heldout_split": self.future_heldout_split,
            "heldout_authorized": self.heldout_authorized,
            "no_post_test_tuning": self.no_post_test_tuning,
            "hyperparameter_provenance_required": self.hyperparameter_provenance_required,
            "policy_freeze_receipt_required": self.policy_freeze_receipt_required,
            "prediction_before_label_required": self.prediction_before_label_required,
            "failure_policy": self.failure_policy,
        }

    def to_dict(self) -> dict[str, Any]:
        body = self.body_dict()
        body["protocol_hash"] = self.protocol_hash
        return body


def _assignment(split_id: str, role: SplitRoleV1, operations: tuple[ProtocolOperationV1, ...], *, labels: bool = False) -> SplitAssignmentV1:
    return SplitAssignmentV1(split_id, role, labels, operations)


def build_validation_protocol_v1(*, source_commit: str) -> ValidationProtocolV1:
    if type(source_commit) is not str or len(source_commit) != 40 or any(ch not in "0123456789abcdef" for ch in source_commit):
        _fail("INVALID_SOURCE_COMMIT")
    assignments = (
        _assignment("train1", SplitRoleV1.NORMAL_FIT_PRIMARY, (
            ProtocolOperationV1.CANDIDATE_LEARNING, ProtocolOperationV1.RELATION_FIT,
            ProtocolOperationV1.NUMERIC_FIT, ProtocolOperationV1.DETECTOR_FIT,
        )),
        _assignment("train2", SplitRoleV1.NORMAL_FIT_SECONDARY, (
            ProtocolOperationV1.CANDIDATE_LEARNING, ProtocolOperationV1.RELATION_FIT,
            ProtocolOperationV1.NUMERIC_FIT, ProtocolOperationV1.DETECTOR_FIT,
        )),
        _assignment("train3", SplitRoleV1.NORMAL_CONFIRMATION_CALIBRATION, (
            ProtocolOperationV1.RELATION_CONFIRMATION, ProtocolOperationV1.THRESHOLD_CALIBRATION,
        )),
        _assignment("train4", SplitRoleV1.NORMAL_POLICY_SELECTION_SANITY, (
            ProtocolOperationV1.NORMAL_POLICY_SELECTION, ProtocolOperationV1.NORMAL_SANITY,
        )),
        _assignment("test1", SplitRoleV1.DEVELOPMENT_ONLY, (
            ProtocolOperationV1.DEVELOPMENT_PREDICTION, ProtocolOperationV1.DEVELOPMENT_LABEL_METRICS,
        ), labels=True),
        _assignment("future_heldout", SplitRoleV1.FUTURE_FINAL_HELDOUT, (), labels=False),
    )
    provisional = ValidationProtocolV1(
        protocol_id="VALIDATION-V2-PROTOCOL-001", study_id="VALIDATION-V2-DEVELOPMENT-STUDY-001",
        evaluation_scope="TEST1_DEVELOPMENT_ONLY", source_commit=source_commit,
        split_assignments=assignments, event_metric_policy=EventMetricPolicyV1(), reporting_policy=ReportingPolicyV1(),
        selection_split="train4", development_split="test1", future_heldout_split="future_heldout",
        heldout_authorized=False, no_post_test_tuning=True, hyperparameter_provenance_required=True,
        policy_freeze_receipt_required=True, prediction_before_label_required=True,
        failure_policy="EXPLICIT_FAIL_CLOSED_NO_FAILURE_TO_NO_RULE_OR_NO_ALARM_COERCION", protocol_hash="",
    )
    return ValidationProtocolV1(**{**provisional.__dict__, "protocol_hash": sha256(_canonical_bytes(provisional.body_dict())).hexdigest()})


def validate_validation_protocol_v1(protocol: ValidationProtocolV1) -> str:
    if type(protocol) is not ValidationProtocolV1:
        _fail("WRONG_PROTOCOL_TYPE")
    expected = build_validation_protocol_v1(source_commit=protocol.source_commit)
    if protocol != expected:
        _fail("PROTOCOL_REPLAY_MISMATCH")
    if sha256(_canonical_bytes(protocol.body_dict())).hexdigest() != protocol.protocol_hash:
        _fail("PROTOCOL_HASH_MISMATCH")
    return protocol.protocol_hash


class ProtocolExecutionGuardV1:
    """Stateful ordering guard for one prospective development evaluation."""

    def __init__(self, protocol: ValidationProtocolV1) -> None:
        validate_validation_protocol_v1(protocol)
        self._protocol = protocol
        self._state = ProtocolGuardStateV1.CREATED
        self._policy_freeze_receipt_hash: str | None = None
        self._policy_freeze_receipt: PolicyFreezeReceiptV1 | None = None
        self._development_prediction_authorized = False
        self._development_label_metrics_authorized = False

    @property
    def state(self) -> ProtocolGuardStateV1:
        return self._state

    def freeze_policies(self, receipt: PolicyFreezeReceiptV1) -> None:
        if self._state is not ProtocolGuardStateV1.CREATED:
            _fail("POLICY_FREEZE_OUT_OF_ORDER")
        self._policy_freeze_receipt_hash = validate_policy_freeze_receipt_v1(receipt, protocol=self._protocol)
        self._policy_freeze_receipt = receipt
        self._state = ProtocolGuardStateV1.POLICIES_FROZEN

    def authorize(
        self,
        *,
        split_id: str,
        operation: ProtocolOperationV1,
        label_access_capability: LabelAccessCapabilityV1 | None = None,
    ) -> None:
        if type(split_id) is not str:
            _fail("SPLIT_ID_MUST_BE_EXACT_STRING")
        if type(operation) is not ProtocolOperationV1:
            _fail("OPERATION_MUST_BE_EXACT_PROTOCOL_ENUM")
        if label_access_capability is not None and type(label_access_capability) is not LabelAccessCapabilityV1:
            _fail("LABEL_CAPABILITY_MUST_BE_EXACT_CUSTODY_TYPE")
        if split_id in {"test2", "outer", "heldout", "sealed"}:
            _fail("UNAUTHORIZED_HELDOUT_ALIAS")
        assignments = {item.split_id: item for item in self._protocol.split_assignments}
        assignment = assignments.get(split_id)
        if assignment is None:
            _fail("UNKNOWN_SPLIT")
        if operation not in assignment.allowed_operations:
            _fail("OPERATION_NOT_ALLOWED_FOR_SPLIT")
        if self._state is ProtocolGuardStateV1.DEVELOPMENT_LABELS_ACCESSED and operation not in (
            ProtocolOperationV1.DEVELOPMENT_LABEL_METRICS,
        ):
            _fail("POST_TEST_TUNING_REJECTED")
        if operation is ProtocolOperationV1.DEVELOPMENT_PREDICTION:
            if self._state is not ProtocolGuardStateV1.POLICIES_FROZEN:
                _fail("DEVELOPMENT_PREDICTION_BEFORE_POLICY_FREEZE")
            if self._development_prediction_authorized:
                _fail("DEVELOPMENT_PREDICTION_ALREADY_AUTHORIZED")
            self._development_prediction_authorized = True
        elif operation is ProtocolOperationV1.DEVELOPMENT_LABEL_METRICS:
            if self._state is not ProtocolGuardStateV1.DEVELOPMENT_PREDICTION_FROZEN or label_access_capability is None:
                _fail("LABEL_ACCESS_BEFORE_DURABLE_PREDICTION_FREEZE")
            if self._development_label_metrics_authorized:
                _fail("DEVELOPMENT_LABEL_METRICS_ALREADY_AUTHORIZED")
            if self._policy_freeze_receipt is None:
                _fail("LABEL_ACCESS_WITHOUT_POLICY_FREEZE_RECEIPT")
            validate_label_access_capability_v1(
                label_access_capability,
                expected_authority_hash=self._policy_freeze_receipt.authority_hash,
                expected_source_commit=self._protocol.source_commit,
            )
            self._development_label_metrics_authorized = True
        elif self._state is not ProtocolGuardStateV1.CREATED:
            _fail("SELECTION_OR_FIT_AFTER_POLICY_FREEZE_REJECTED")

    def record_development_prediction_frozen(self) -> None:
        if self._state is not ProtocolGuardStateV1.POLICIES_FROZEN:
            _fail("PREDICTION_FREEZE_OUT_OF_ORDER")
        if not self._development_prediction_authorized:
            _fail("PREDICTION_FREEZE_WITHOUT_AUTHORIZATION")
        self._state = ProtocolGuardStateV1.DEVELOPMENT_PREDICTION_FROZEN

    def authorize_multi_method_label_metrics_v1(self, capability: object, *, exact_method_ids: tuple[str, ...],
                                               evaluation_policy_hash: str, metric_contract_hash: str,
                                               execution_source_commit: str) -> None:
        """Bundle-custody path; historical single-D1 capability remains unchanged."""
        from .evaluation_custody_v1 import validate_evaluation_label_capability_v1
        if (self._state is not ProtocolGuardStateV1.DEVELOPMENT_PREDICTION_FROZEN
            or self._policy_freeze_receipt is None or self._development_label_metrics_authorized):
            _fail("MULTI_METHOD_LABEL_AUTHORIZATION_OUT_OF_ORDER")
        if (metric_contract_hash != self._policy_freeze_receipt.metric_contract_hash
            or evaluation_policy_hash not in self._policy_freeze_receipt.method_policy_hashes):
            _fail("MULTI_METHOD_FROZEN_POLICY_MISMATCH")
        validate_evaluation_label_capability_v1(capability, exact_method_ids=exact_method_ids,
            evaluation_policy_hash=evaluation_policy_hash, metric_contract_hash=metric_contract_hash,
            source_commit=execution_source_commit)
        self._development_label_metrics_authorized = True

    def record_development_labels_accessed(self) -> None:
        if self._state is not ProtocolGuardStateV1.DEVELOPMENT_PREDICTION_FROZEN:
            _fail("LABEL_STATE_OUT_OF_ORDER")
        if not self._development_label_metrics_authorized:
            _fail("LABEL_STATE_WITHOUT_AUTHORIZATION")
        self._state = ProtocolGuardStateV1.DEVELOPMENT_LABELS_ACCESSED

    def complete(self) -> None:
        if self._state is not ProtocolGuardStateV1.DEVELOPMENT_LABELS_ACCESSED:
            _fail("PROTOCOL_COMPLETION_OUT_OF_ORDER")
        self._state = ProtocolGuardStateV1.COMPLETE


__all__ = [
    "EventMetricPolicyV1", "PolicyFreezeReceiptV1", "ProtocolExecutionGuardV1", "ProtocolGuardStateV1",
    "ProtocolOperationV1", "ReportingPolicyV1", "SplitAssignmentV1", "SplitRoleV1",
    "ValidationProtocolError", "ValidationProtocolV1", "build_policy_freeze_receipt_v1",
    "build_validation_protocol_v1", "validate_policy_freeze_receipt_v1", "validate_validation_protocol_v1",
]
