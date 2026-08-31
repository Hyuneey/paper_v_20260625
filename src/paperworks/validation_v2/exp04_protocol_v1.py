"""Prospective, label-blind EXP-04 method and fusion policy contract.

This module fixes the development comparison before any Validation V2 test1
outcome is observed.  It is pure computation and never opens data or labels.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
from typing import Any, Mapping

from .formal_v4_authority_v1 import (
    FormalV4AuthorizedRuntimeV1,
    FormalV4ExecutionContextV1,
    canonical_document_hash_v1,
    validate_formal_v4_runtime_authorization_v1,
)
from .evaluation_custody_v1 import (
    DenseBooleanPredictionArtifactV1,
    HashOnlyPredictionFreezeReceiptV1,
    PredictionFreezeReferenceV1,
    replay_dense_prediction_before_label_v1,
)
from .prediction_custody_v1 import (
    DurablePredictionFreezeReceiptV1,
    replay_prediction_before_label_v1,
)
from .runtime_v1 import FORMAL_V4_RUNTIME_VERSION, FormalV4RuntimeTraceV1


HEX = frozenset("0123456789abcdef")
EXP04_EXPERIMENT_ID = "VALIDATION_V2_EXP04_DEVELOPMENT_V1"
EXP04_METHOD_IDS = tuple(sorted((
    "V2_D0_PCA_SPE_NORMAL_ONLY_V1",
    "V2_D2_PCA_RULE_CONFIRM2_SAME_SECOND_V1",
    "V2_D2_IF_RULE_CONFIRM2_SAME_SECOND_V1",
    "V2_ISOLATION_FOREST_FIXED_NORMAL_ONLY_V1",
    "V2_VERIFIED_RELATIONAL_RULE_ONLY_V1",
)))
EXP04_FUSION_POLICY_ID = "BASE_OR_D1_FAIL_AT_SAME_FILE_ROW_WITH_AT_LEAST_2_DISTINCT_SOURCES_V1"
EXP04_PRIMARY_METRICS = ("ATTACK_EVENT_RECALL", "NORMAL_FALSE_EPISODES_PER_HOUR")
EXP04_SECONDARY_METRICS = (
    "D0_D1_EVENT_OVERLAP",
    "DETECTOR_MISS_RECOVERY",
    "INCREMENTAL_RECALL",
    "INCREMENTAL_NORMAL_FAR",
    "RULE_COVERAGE",
    "RULE_ABSTAIN_RATE",
    "RULE_CONFLICT_COUNT",
)


class Exp04ProtocolError(ValueError):
    pass


def _canonical_bytes(value: Mapping[str, Any]) -> bytes:
    return json.dumps(dict(value), sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


def _hash(value: Mapping[str, Any]) -> str:
    return sha256(_canonical_bytes(value)).hexdigest()


def _sha(value: object, name: str) -> None:
    if type(value) is not str or len(value) != 64 or set(value) - HEX:
        raise Exp04ProtocolError(f"{name} must be lowercase sha256")


def _commit(value: object) -> None:
    if type(value) is not str or len(value) != 40 or set(value) - HEX:
        raise Exp04ProtocolError("source_commit must be a lowercase Git commit")


def _identifier(value: object, name: str) -> None:
    if type(value) is not str or not value or value in (".", "..") or any(ch in value for ch in ("/", "\\", ":", "|")):
        raise Exp04ProtocolError(f"invalid {name}")


def exp04_opportunity_id_v1(*, file_id: str, row_index: int, rule_id: str) -> str:
    _identifier(file_id, "file_id")
    _identifier(rule_id, "rule_id")
    if type(row_index) is not int or row_index < 0:
        raise Exp04ProtocolError("row_index must be a nonnegative integer")
    return f"EXP04V2|{file_id}|{row_index}|{rule_id}"


@dataclass(frozen=True)
class Exp04PreregistrationV1:
    source_commit: str
    validation_protocol_hash: str
    metric_contract_hash: str
    d0_authority_contract_hash: str
    isolation_forest_contract_hash: str
    rule_portfolio_contract_hash: str
    evaluation_custody_contract_hash: str
    method_ids: tuple[str, ...] = EXP04_METHOD_IDS
    fusion_policy_id: str = EXP04_FUSION_POLICY_ID
    fusion_min_distinct_sources: int = 2
    primary_metrics: tuple[str, ...] = EXP04_PRIMARY_METRICS
    secondary_metrics: tuple[str, ...] = EXP04_SECONDARY_METRICS
    split_role: str = "DEVELOPMENT_TEST1"
    policy_selection_role: str = "FROZEN_BEFORE_TEST1_FEATURE_ACCESS"
    point_adjustment: str = "NONE_PA_FREE"
    post_result_policy_change_allowed: bool = False
    test2_authorized: bool = False
    heldout_authorized: bool = False
    schema: str = "paperworks.validation_v2.exp04_preregistration_v1"
    schema_version: str = "1.0.0"
    preregistration_hash: str = ""

    def __post_init__(self) -> None:
        _commit(self.source_commit)
        for name in (
            "validation_protocol_hash", "metric_contract_hash", "d0_authority_contract_hash",
            "isolation_forest_contract_hash", "rule_portfolio_contract_hash",
            "evaluation_custody_contract_hash",
        ):
            _sha(getattr(self, name), name)
        if self.method_ids != EXP04_METHOD_IDS:
            raise Exp04ProtocolError("EXP-04 method set or order changed")
        if self.fusion_policy_id != EXP04_FUSION_POLICY_ID or self.fusion_min_distinct_sources != 2:
            raise Exp04ProtocolError("EXP-04 fusion policy changed")
        if self.primary_metrics != EXP04_PRIMARY_METRICS or self.secondary_metrics != EXP04_SECONDARY_METRICS:
            raise Exp04ProtocolError("EXP-04 metric plan changed")
        if (
            self.split_role != "DEVELOPMENT_TEST1"
            or self.policy_selection_role != "FROZEN_BEFORE_TEST1_FEATURE_ACCESS"
            or self.point_adjustment != "NONE_PA_FREE"
        ):
            raise Exp04ProtocolError("EXP-04 split or event contract changed")
        for name in ("post_result_policy_change_allowed", "test2_authorized", "heldout_authorized"):
            if type(getattr(self, name)) is not bool or getattr(self, name):
                raise Exp04ProtocolError("EXP-04 forbids post-result changes and held-out access")
        if self.schema != "paperworks.validation_v2.exp04_preregistration_v1" or self.schema_version != "1.0.0":
            raise Exp04ProtocolError("EXP-04 schema changed")
        if self.preregistration_hash and self.preregistration_hash != _hash(self.to_document(include_hash=False)):
            raise Exp04ProtocolError("EXP-04 preregistration replay mismatch")

    def to_document(self, *, include_hash: bool = True) -> dict[str, Any]:
        value: dict[str, Any] = {
            "schema": self.schema,
            "schema_version": self.schema_version,
            "source_commit": self.source_commit,
            "validation_protocol_hash": self.validation_protocol_hash,
            "metric_contract_hash": self.metric_contract_hash,
            "d0_authority_contract_hash": self.d0_authority_contract_hash,
            "isolation_forest_contract_hash": self.isolation_forest_contract_hash,
            "rule_portfolio_contract_hash": self.rule_portfolio_contract_hash,
            "evaluation_custody_contract_hash": self.evaluation_custody_contract_hash,
            "method_ids": list(self.method_ids),
            "fusion_policy_id": self.fusion_policy_id,
            "fusion_min_distinct_sources": self.fusion_min_distinct_sources,
            "primary_metrics": list(self.primary_metrics),
            "secondary_metrics": list(self.secondary_metrics),
            "split_role": self.split_role,
            "policy_selection_role": self.policy_selection_role,
            "point_adjustment": self.point_adjustment,
            "post_result_policy_change_allowed": self.post_result_policy_change_allowed,
            "test2_authorized": self.test2_authorized,
            "heldout_authorized": self.heldout_authorized,
            "claim_boundary": "TEST1_DEVELOPMENT_ONLY_NOT_HELDOUT_VALIDATION",
        }
        if include_hash:
            value["preregistration_hash"] = self.preregistration_hash
        return value


def build_exp04_preregistration_v1(**values: object) -> Exp04PreregistrationV1:
    provisional = Exp04PreregistrationV1(**values)
    return Exp04PreregistrationV1(
        **{**provisional.__dict__, "preregistration_hash": _hash(provisional.to_document(include_hash=False))}
    )


@dataclass(frozen=True)
class RuleOutcomeEvidenceV1:
    file_id: str
    feature_file_sha256: str
    row_index: int
    rule_id: str
    source_id: str
    outcome: str
    descriptor_hash: str
    trace_hash: str
    portfolio_authority_hash: str
    runtime_authorization_hash: str
    runtime_trace: FormalV4RuntimeTraceV1

    def __post_init__(self) -> None:
        _identifier(self.file_id, "file_id")
        _identifier(self.rule_id, "rule_id")
        _identifier(self.source_id, "source_id")
        _sha(self.feature_file_sha256, "feature_file_sha256")
        for value, name in (
            (self.descriptor_hash, "descriptor_hash"),
            (self.trace_hash, "trace_hash"),
            (self.portfolio_authority_hash, "portfolio_authority_hash"),
            (self.runtime_authorization_hash, "runtime_authorization_hash"),
        ):
            _sha(value, name)
        if type(self.row_index) is not int or self.row_index < 0:
            raise Exp04ProtocolError("row_index must be a nonnegative integer")
        if self.outcome not in ("PASS", "FAIL", "ABSTAIN"):
            raise Exp04ProtocolError("rule outcome must be PASS, FAIL, or ABSTAIN")
        if type(self.runtime_trace) is not FormalV4RuntimeTraceV1:
            raise Exp04ProtocolError("typed Formal V4 runtime trace required")
        trace_payload = {
            "alarm_emitted": self.runtime_trace.alarm_emitted,
            "authorization_hash": self.runtime_trace.authorization_hash,
            "descriptor_hash": self.runtime_trace.descriptor_hash,
            "execution_context_hash": self.runtime_trace.execution_context_hash,
            "final_outcome": self.runtime_trace.final_outcome,
            "opportunity_id": self.runtime_trace.opportunity_id,
            "reason": self.runtime_trace.reason,
            "relation_id": self.runtime_trace.relation_id,
            "runtime_version": FORMAL_V4_RUNTIME_VERSION,
        }
        if (
            canonical_document_hash_v1(trace_payload) != self.runtime_trace.trace_hash
            or self.trace_hash != self.runtime_trace.trace_hash
            or self.rule_id != self.runtime_trace.relation_id
            or self.descriptor_hash != self.runtime_trace.descriptor_hash
            or self.runtime_authorization_hash != self.runtime_trace.authorization_hash
            or self.outcome != self.runtime_trace.final_outcome
            or self.runtime_trace.alarm_emitted is not (self.outcome == "FAIL")
            or self.runtime_trace.opportunity_id != exp04_opportunity_id_v1(
                file_id=self.file_id, row_index=self.row_index, rule_id=self.rule_id,
            )
        ):
            raise Exp04ProtocolError("rule outcome does not replay its runtime trace")


@dataclass(frozen=True)
class RuleAuthorityBindingV1:
    rule_id: str
    source_id: str
    descriptor_hash: str

    def __post_init__(self) -> None:
        _identifier(self.rule_id, "rule_id")
        _identifier(self.source_id, "source_id")
        _sha(self.descriptor_hash, "descriptor_hash")

    def to_document(self) -> dict[str, str]:
        return {
            "rule_id": self.rule_id,
            "source_id": self.source_id,
            "descriptor_hash": self.descriptor_hash,
        }


@dataclass(frozen=True)
class RuleOutcomeAuthorityV1:
    portfolio_authority_hash: str
    runtime_authorization_hash: str
    execution_context_hash: str
    descriptor_set_hash: str
    bindings: tuple[RuleAuthorityBindingV1, ...]
    authority_hash: str = ""

    def __post_init__(self) -> None:
        _sha(self.portfolio_authority_hash, "portfolio_authority_hash")
        _sha(self.runtime_authorization_hash, "runtime_authorization_hash")
        _sha(self.execution_context_hash, "execution_context_hash")
        _sha(self.descriptor_set_hash, "descriptor_set_hash")
        if type(self.bindings) is not tuple or not self.bindings:
            raise Exp04ProtocolError("rule authority bindings must be nonempty")
        if any(type(item) is not RuleAuthorityBindingV1 for item in self.bindings):
            raise Exp04ProtocolError("foreign rule authority binding")
        keys = tuple(item.rule_id for item in self.bindings)
        if keys != tuple(sorted(set(keys))):
            raise Exp04ProtocolError("rule authority bindings must be sorted and unique")
        expected = _hash(self.to_document(include_hash=False))
        if self.authority_hash and self.authority_hash != expected:
            raise Exp04ProtocolError("rule outcome authority replay mismatch")

    def to_document(self, *, include_hash: bool = True) -> dict[str, Any]:
        document: dict[str, Any] = {
            "schema": "paperworks.validation_v2.exp04_rule_outcome_authority_v1",
            "schema_version": "1.0.0",
            "portfolio_authority_hash": self.portfolio_authority_hash,
            "runtime_authorization_hash": self.runtime_authorization_hash,
            "execution_context_hash": self.execution_context_hash,
            "descriptor_set_hash": self.descriptor_set_hash,
            "bindings": [item.to_document() for item in self.bindings],
        }
        if include_hash:
            document["authority_hash"] = self.authority_hash
        return document


def build_rule_outcome_authority_v1(
    *,
    authorized_runtime: FormalV4AuthorizedRuntimeV1,
    execution_context: FormalV4ExecutionContextV1,
    repository_root: Path,
) -> RuleOutcomeAuthorityV1:
    if type(authorized_runtime) is not FormalV4AuthorizedRuntimeV1:
        raise Exp04ProtocolError("typed Formal V4 authorized runtime required")
    if type(execution_context) is not FormalV4ExecutionContextV1:
        raise Exp04ProtocolError("typed Formal V4 execution context required")
    try:
        validate_formal_v4_runtime_authorization_v1(
            authorized_runtime,
            execution_context=execution_context,
            repository_root=repository_root,
        )
    except ValueError as exc:
        raise Exp04ProtocolError("Formal V4 runtime authority replay failed") from exc
    authority = authorized_runtime.authority
    bindings = tuple(
        RuleAuthorityBindingV1(
            rule_id=descriptor.relation_id,
            source_id=descriptor.source,
            descriptor_hash=descriptor.descriptor_hash,
        )
        for descriptor in authority.descriptors
    )
    if tuple(item.rule_id for item in bindings) != tuple(sorted(item.rule_id for item in bindings)):
        raise Exp04ProtocolError("Formal V4 descriptor order is not canonical")
    provisional = RuleOutcomeAuthorityV1(
        portfolio_authority_hash=authority.authority_hash,
        runtime_authorization_hash=authorized_runtime.receipt.authorization_hash,
        execution_context_hash=execution_context.context_hash,
        descriptor_set_hash=authority.descriptor_set_hash,
        bindings=bindings,
    )
    return RuleOutcomeAuthorityV1(
        portfolio_authority_hash=authority.authority_hash,
        runtime_authorization_hash=authorized_runtime.receipt.authorization_hash,
        execution_context_hash=execution_context.context_hash,
        descriptor_set_hash=authority.descriptor_set_hash,
        bindings=bindings,
        authority_hash=_hash(provisional.to_document(include_hash=False)),
    )


@dataclass(frozen=True)
class DenseAlarmV1:
    file_id: str
    feature_file_sha256: str
    row_index: int
    alarm: bool

    def __post_init__(self) -> None:
        _identifier(self.file_id, "file_id")
        _sha(self.feature_file_sha256, "feature_file_sha256")
        if type(self.row_index) is not int or self.row_index < 0 or type(self.alarm) is not bool:
            raise Exp04ProtocolError("invalid dense alarm")

    def to_document(self) -> dict[str, Any]:
        return {
            "alarm": self.alarm,
            "feature_file_sha256": self.feature_file_sha256,
            "file_id": self.file_id,
            "row_index": self.row_index,
        }


@dataclass(frozen=True)
class DetectorPredictionAuthorityV1:
    method_id: str
    source_commit: str
    prediction_hash: str
    freeze_receipt_hash: str
    file_contract_hash: str
    record_count: int
    authority_hash: str = ""

    def __post_init__(self) -> None:
        _identifier(self.method_id, "method_id")
        _commit(self.source_commit)
        for value, name in (
            (self.prediction_hash, "prediction_hash"),
            (self.freeze_receipt_hash, "freeze_receipt_hash"),
            (self.file_contract_hash, "file_contract_hash"),
        ):
            _sha(value, name)
        if type(self.record_count) is not int or self.record_count <= 0:
            raise Exp04ProtocolError("detector prediction record count must be positive")
        expected = _hash(self.to_document(include_hash=False))
        if self.authority_hash and self.authority_hash != expected:
            raise Exp04ProtocolError("detector prediction authority replay mismatch")

    def to_document(self, *, include_hash: bool = True) -> dict[str, Any]:
        document: dict[str, Any] = {
            "schema": "paperworks.validation_v2.exp04_detector_prediction_authority_v1",
            "schema_version": "1.0.0",
            "method_id": self.method_id,
            "source_commit": self.source_commit,
            "prediction_hash": self.prediction_hash,
            "freeze_receipt_hash": self.freeze_receipt_hash,
            "file_contract_hash": self.file_contract_hash,
            "record_count": self.record_count,
        }
        if include_hash:
            document["authority_hash"] = self.authority_hash
        return document


def build_detector_prediction_authority_v1(
    *, artifact: DenseBooleanPredictionArtifactV1,
    receipt: HashOnlyPredictionFreezeReceiptV1,
) -> DetectorPredictionAuthorityV1:
    if type(artifact) is not DenseBooleanPredictionArtifactV1 or type(receipt) is not HashOnlyPredictionFreezeReceiptV1:
        raise Exp04ProtocolError("typed durable detector prediction and receipt required")
    document = artifact.to_document()
    if (
        receipt.method_id != artifact.method_id
        or receipt.prediction_self_hash != document["self_hash"]
        or receipt.authority_hash != artifact.authority_hash
        or receipt.file_contract_hash != artifact.file_contract_hash
        or receipt.source_commit != artifact.source_commit
        or receipt.record_count != len(artifact.records)
    ):
        raise Exp04ProtocolError("detector freeze receipt binding mismatch")
    values = {
        "method_id": artifact.method_id, "source_commit": artifact.source_commit,
        "prediction_hash": document["self_hash"],
        "freeze_receipt_hash": receipt.self_hash,
        "file_contract_hash": artifact.file_contract_hash,
        "record_count": len(artifact.records),
    }
    provisional = DetectorPredictionAuthorityV1(**values)
    return DetectorPredictionAuthorityV1(
        **{**values, "authority_hash": _hash(provisional.to_document(include_hash=False))}
    )


@dataclass(frozen=True)
class FusionDecisionV1:
    file_id: str
    feature_file_sha256: str
    row_index: int
    base_alarm: bool
    distinct_fail_sources: tuple[str, ...]
    rule_addition: bool
    final_alarm: bool
    fusion_policy_id: str = EXP04_FUSION_POLICY_ID

    def __post_init__(self) -> None:
        _identifier(self.file_id, "file_id")
        _sha(self.feature_file_sha256, "feature_file_sha256")
        if type(self.row_index) is not int or self.row_index < 0:
            raise Exp04ProtocolError("invalid fusion row index")
        if type(self.distinct_fail_sources) is not tuple or self.distinct_fail_sources != tuple(sorted(set(self.distinct_fail_sources))):
            raise Exp04ProtocolError("fusion sources must be sorted and distinct")
        if any(type(value) is not str or not value for value in self.distinct_fail_sources):
            raise Exp04ProtocolError("invalid fusion source identity")
        expected_addition = len(self.distinct_fail_sources) >= 2
        if self.rule_addition is not expected_addition or self.final_alarm is not (self.base_alarm or expected_addition):
            raise Exp04ProtocolError("fusion decision does not replay the frozen policy")
        if self.fusion_policy_id != EXP04_FUSION_POLICY_ID:
            raise Exp04ProtocolError("foreign fusion policy")


def fuse_detector_with_rules_v1(
    *,
    base_custody_root: Path,
    base_prediction_reference: PredictionFreezeReferenceV1,
    expected_evaluation_policy_hash: str,
    expected_metric_contract_hash: str,
    d1_custody_root: Path,
    d1_receipt_relative_path: str,
    d1_freeze_receipt: DurablePredictionFreezeReceiptV1,
    rule_outcomes: tuple[RuleOutcomeEvidenceV1, ...],
    authorized_runtime: FormalV4AuthorizedRuntimeV1,
    execution_context: FormalV4ExecutionContextV1,
    repository_root: Path,
) -> tuple[FusionDecisionV1, ...]:
    if type(rule_outcomes) is not tuple or any(type(item) is not RuleOutcomeEvidenceV1 for item in rule_outcomes):
        raise Exp04ProtocolError("rule outcomes must be a typed tuple")
    try:
        base_artifact = replay_dense_prediction_before_label_v1(
            artifact_root=base_custody_root,
            reference=base_prediction_reference,
            expected_policy_hash=expected_evaluation_policy_hash,
            expected_metric_contract_hash=expected_metric_contract_hash,
            expected_source_commit=authorized_runtime.authority.source_commit,
        )
        d1_artifact = replay_prediction_before_label_v1(
            artifact_root=d1_custody_root,
            prediction_relative_path=d1_freeze_receipt.prediction_relative_path,
            receipt_relative_path=d1_receipt_relative_path,
            expected_receipt=d1_freeze_receipt,
            expected_authority_hash=authorized_runtime.authority.authority_hash,
            expected_runtime_authorization_hash=authorized_runtime.receipt.authorization_hash,
            expected_execution_context_hash=execution_context.context_hash,
            expected_source_commit=authorized_runtime.authority.source_commit,
            expected_portfolio_hash=authorized_runtime.authority.authority_hash,
            expected_file_contract_hash=execution_context.file_contract_binding.content_sha256,
        )
    except (ValueError, RuntimeError) as exc:
        raise Exp04ProtocolError("durable upstream prediction replay failed") from exc
    build_detector_prediction_authority_v1(
        artifact=base_artifact, receipt=base_prediction_reference.receipt,
    )
    base_predictions = tuple(
        DenseAlarmV1(item.file_id, item.file_content_sha256, item.row_index, item.alarm)
        for item in base_artifact.records
    )
    rule_authority = build_rule_outcome_authority_v1(
        authorized_runtime=authorized_runtime,
        execution_context=execution_context,
        repository_root=repository_root,
    )
    expected_bindings = {
        item.rule_id: (item.source_id, item.descriptor_hash)
        for item in rule_authority.bindings
    }
    coordinates = tuple((item.file_id, item.row_index) for item in base_predictions)
    if coordinates != tuple(sorted(set(coordinates))):
        raise Exp04ProtocolError("base prediction coordinates must be sorted and unique")
    by_coordinate: dict[tuple[str, int], set[str]] = {}
    file_hashes = {(item.file_id, item.row_index): item.feature_file_sha256 for item in base_predictions}
    d1_coordinates = tuple((item.file_id, item.row_index) for item in d1_artifact.records)
    if d1_coordinates != tuple(file_hashes):
        raise Exp04ProtocolError("D1 and detector dense coordinate census mismatch")
    evidence_keys: set[tuple[str, int, str]] = set()
    for item in rule_outcomes:
        coordinate = (item.file_id, item.row_index)
        if coordinate not in file_hashes or file_hashes[coordinate] != item.feature_file_sha256:
            raise Exp04ProtocolError("rule evidence coordinate is outside the base prediction")
        evidence_key = (item.file_id, item.row_index, item.rule_id)
        if evidence_key in evidence_keys:
            raise Exp04ProtocolError("duplicate or contradictory rule outcome evidence")
        evidence_keys.add(evidence_key)
        if expected_bindings.get(item.rule_id) != (item.source_id, item.descriptor_hash):
            raise Exp04ProtocolError("rule outcome source or descriptor authority mismatch")
        if (
            item.portfolio_authority_hash != rule_authority.portfolio_authority_hash
            or item.runtime_authorization_hash != rule_authority.runtime_authorization_hash
            or item.runtime_trace.execution_context_hash != rule_authority.execution_context_hash
        ):
            raise Exp04ProtocolError("rule outcome uses foreign runtime authority")
        if item.outcome == "FAIL":
            by_coordinate.setdefault(coordinate, set()).add(item.source_id)
    fail_records: dict[tuple[str, int], list[RuleOutcomeEvidenceV1]] = {}
    for item in rule_outcomes:
        if item.outcome == "FAIL":
            fail_records.setdefault((item.file_id, item.row_index), []).append(item)
    for record in d1_artifact.records:
        coordinate = (record.file_id, record.row_index)
        observed = fail_records.get(coordinate, [])
        if (
            record.file_content_sha256 != file_hashes[coordinate]
            or record.alarm is not bool(observed)
            or record.contributing_rule_ids != tuple(sorted(item.rule_id for item in observed))
            or record.trace_hashes != tuple(sorted(item.trace_hash for item in observed))
        ):
            raise Exp04ProtocolError("D1 frozen FAIL evidence census mismatch")
    return tuple(
        FusionDecisionV1(
            file_id=item.file_id,
            feature_file_sha256=item.feature_file_sha256,
            row_index=item.row_index,
            base_alarm=item.alarm,
            distinct_fail_sources=tuple(sorted(by_coordinate.get((item.file_id, item.row_index), set()))),
            rule_addition=len(by_coordinate.get((item.file_id, item.row_index), set())) >= 2,
            final_alarm=item.alarm or len(by_coordinate.get((item.file_id, item.row_index), set())) >= 2,
        )
        for item in base_predictions
    )


EXP04_FUSION_POLICY_HASH = _hash({
    "policy_id": EXP04_FUSION_POLICY_ID,
    "minimum_distinct_sources": 2,
    "coordinate": "SAME_FILE_ID_AND_ROW_INDEX",
    "eligible_rule_outcome": "FAIL_ONLY",
    "source_deduplication": "DISTINCT_SOURCE_ID",
    "base_preservation": "POINTWISE_OR",
})


__all__ = [
    "DenseAlarmV1", "DetectorPredictionAuthorityV1", "EXP04_EXPERIMENT_ID", "EXP04_FUSION_POLICY_HASH",
    "EXP04_FUSION_POLICY_ID", "EXP04_METHOD_IDS", "EXP04_PRIMARY_METRICS",
    "EXP04_SECONDARY_METRICS", "Exp04PreregistrationV1", "Exp04ProtocolError",
    "FusionDecisionV1", "RuleAuthorityBindingV1", "RuleOutcomeAuthorityV1",
    "RuleOutcomeEvidenceV1", "build_detector_prediction_authority_v1",
    "build_exp04_preregistration_v1", "build_rule_outcome_authority_v1",
    "exp04_opportunity_id_v1", "fuse_detector_with_rules_v1",
]
