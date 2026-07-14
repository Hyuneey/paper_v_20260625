"""Immutable TASK-030 anomaly-anchored evidence package model."""

from __future__ import annotations

import copy
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from paperworks.contracts.artifact_hashing import (
    ContractArtifactHashError,
    canonical_contract_artifact_sha256,
    verify_contract_artifact_hash,
)
from paperworks.contracts.schema_registry import SchemaRegistry, load_schema_registry


class EvidenceV1ModelError(ValueError):
    def __init__(self, issue_code: str, field_path: str, message: str) -> None:
        super().__init__(f"{issue_code} at {field_path}: {message}")
        self.issue_code = issue_code
        self.field_path = field_path
        self.message = message


@dataclass(frozen=True)
class WindowReferenceV1:
    window_id: str
    start_offset: int
    end_offset: int
    unit: str
    artifact_hash: str


@dataclass(frozen=True)
class MatchedNormalReferenceV1:
    reference_id: str
    operating_regime: str
    subsystem: str
    matching_method: str
    tie_breaker: str
    artifact_hash: str


@dataclass(frozen=True)
class EvidenceLagRangeV1:
    minimum: int | float
    maximum: int | float
    unit: str


@dataclass(frozen=True)
class EvidenceSelectionPolicyV1:
    policy_id: str
    policy_version: str
    regime_match_required: bool
    subsystem_match_required: bool
    label_performance_used: bool
    deterministic_tie_breaking: bool
    pre_registered: bool


@dataclass(frozen=True)
class EvidencePackageV1:
    schema_version: str
    evidence_id: str
    artifact_hash: str
    event_anchor: WindowReferenceV1
    event_window: WindowReferenceV1
    pre_event_context: WindowReferenceV1
    post_event_context: WindowReferenceV1
    matched_normal_reference: MatchedNormalReferenceV1
    source_variables: tuple[str, ...]
    target_variables: tuple[str, ...]
    operating_regime: str
    candidate_lag_range: EvidenceLagRangeV1
    data_split: str
    dataset_version: str
    selection_policy: EvidenceSelectionPolicyV1
    selection_policy_hash: str
    supported_claims: tuple[str, ...]
    prohibited_claims: tuple[str, ...]
    raw_values_included: bool

    @property
    def runtime_authorized(self) -> bool:
        return False


def parse_evidence_package(
    document: Mapping[str, object], *, registry: SchemaRegistry | None = None
) -> EvidencePackageV1:
    snapshot = copy.deepcopy(dict(document))
    report = (registry or load_schema_registry()).validate_artifact("evidence_package", snapshot)
    if report.status != "valid":
        issue = report.issues[0] if report.issues else None
        _fail("EVIDENCE_V1_STRUCTURAL_INVALID", issue.instance_path if issue else "/", issue.issue_code if issue else "registry error")
    try:
        verify_contract_artifact_hash(snapshot)
    except ContractArtifactHashError as exc:
        _fail(exc.issue_code, "/artifact_hash", exc.message)
    evidence = _typed_evidence(snapshot)
    _validate_evidence(evidence)
    return evidence


def load_evidence_package(path: str | Path, *, registry: SchemaRegistry | None = None) -> EvidencePackageV1:
    try:
        document = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise EvidenceV1ModelError("EVIDENCE_V1_STRUCTURAL_INVALID", "/", "artifact is not readable UTF-8 JSON") from exc
    if not isinstance(document, dict):
        _fail("EVIDENCE_V1_STRUCTURAL_INVALID", "/", "artifact must be a JSON object")
    return parse_evidence_package(document, registry=registry)


def evidence_package_to_dict(evidence: EvidencePackageV1) -> dict[str, Any]:
    return {
        "schema_version": evidence.schema_version, "evidence_id": evidence.evidence_id,
        "artifact_hash": evidence.artifact_hash, "event_anchor": _window_to_dict(evidence.event_anchor),
        "event_window": _window_to_dict(evidence.event_window),
        "pre_event_context": _window_to_dict(evidence.pre_event_context),
        "post_event_context": _window_to_dict(evidence.post_event_context),
        "matched_normal_reference": {"reference_id": evidence.matched_normal_reference.reference_id,
            "operating_regime": evidence.matched_normal_reference.operating_regime,
            "subsystem": evidence.matched_normal_reference.subsystem,
            "matching_method": evidence.matched_normal_reference.matching_method,
            "tie_breaker": evidence.matched_normal_reference.tie_breaker,
            "artifact_hash": evidence.matched_normal_reference.artifact_hash},
        "source_variables": list(evidence.source_variables), "target_variables": list(evidence.target_variables),
        "operating_regime": evidence.operating_regime,
        "candidate_lag_range": {"minimum": evidence.candidate_lag_range.minimum,
            "maximum": evidence.candidate_lag_range.maximum, "unit": evidence.candidate_lag_range.unit},
        "data_split": evidence.data_split, "dataset_version": evidence.dataset_version,
        "selection_policy": {"policy_id": evidence.selection_policy.policy_id,
            "policy_version": evidence.selection_policy.policy_version,
            "regime_match_required": evidence.selection_policy.regime_match_required,
            "subsystem_match_required": evidence.selection_policy.subsystem_match_required,
            "label_performance_used": evidence.selection_policy.label_performance_used,
            "deterministic_tie_breaking": evidence.selection_policy.deterministic_tie_breaking,
            "pre_registered": evidence.selection_policy.pre_registered},
        "selection_policy_hash": evidence.selection_policy_hash,
        "supported_claims": list(evidence.supported_claims),
        "prohibited_claims": list(evidence.prohibited_claims),
        "raw_values_included": evidence.raw_values_included,
    }


def serialize_evidence_package(evidence: EvidencePackageV1) -> str:
    return json.dumps(evidence_package_to_dict(evidence), sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)


def canonical_evidence_package_sha256(evidence: EvidencePackageV1) -> str:
    return canonical_contract_artifact_sha256(evidence_package_to_dict(evidence))


def _typed_evidence(document: Mapping[str, Any]) -> EvidencePackageV1:
    normal, lag, policy = document["matched_normal_reference"], document["candidate_lag_range"], document["selection_policy"]
    return EvidencePackageV1(
        schema_version=document["schema_version"], evidence_id=document["evidence_id"], artifact_hash=document["artifact_hash"],
        event_anchor=_typed_window(document["event_anchor"]), event_window=_typed_window(document["event_window"]),
        pre_event_context=_typed_window(document["pre_event_context"]), post_event_context=_typed_window(document["post_event_context"]),
        matched_normal_reference=MatchedNormalReferenceV1(normal["reference_id"], normal["operating_regime"], normal["subsystem"], normal["matching_method"], normal["tie_breaker"], normal["artifact_hash"]),
        source_variables=tuple(document["source_variables"]), target_variables=tuple(document["target_variables"]),
        operating_regime=document["operating_regime"], candidate_lag_range=EvidenceLagRangeV1(lag["minimum"], lag["maximum"], lag["unit"]),
        data_split=document["data_split"], dataset_version=document["dataset_version"],
        selection_policy=EvidenceSelectionPolicyV1(policy["policy_id"], policy["policy_version"], policy["regime_match_required"], policy["subsystem_match_required"], policy["label_performance_used"], policy["deterministic_tie_breaking"], policy["pre_registered"]),
        selection_policy_hash=document["selection_policy_hash"], supported_claims=tuple(document["supported_claims"]),
        prohibited_claims=tuple(document["prohibited_claims"]), raw_values_included=document["raw_values_included"],
    )


def _typed_window(item: Mapping[str, Any]) -> WindowReferenceV1:
    return WindowReferenceV1(item["window_id"], item["start_offset"], item["end_offset"], item["unit"], item["artifact_hash"])


def _validate_evidence(evidence: EvidencePackageV1) -> None:
    windows = (evidence.event_anchor, evidence.event_window, evidence.pre_event_context, evidence.post_event_context)
    for index, window in enumerate(windows):
        if window.start_offset > window.end_offset:
            _fail("EVIDENCE_V1_WINDOW_ORDER", f"/windows/{index}", "window offsets are inverted")
    if evidence.candidate_lag_range.minimum > evidence.candidate_lag_range.maximum:
        _fail("EVIDENCE_V1_LAG_ORDER", "/candidate_lag_range", "candidate lag range is inverted")
    if set(evidence.source_variables) & set(evidence.target_variables):
        _fail("EVIDENCE_V1_VARIABLE_OVERLAP", "/target_variables", "source and target sets overlap")
    if evidence.raw_values_included:
        _fail("EVIDENCE_V1_RAW_VALUES", "/raw_values_included", "raw values are prohibited")
    required = {"physical_causality", "root_cause", "universal_invariant"}
    if not required.issubset(evidence.prohibited_claims):
        _fail("EVIDENCE_V1_CLAIM_BOUNDARY", "/prohibited_claims", "all prohibited claims are required")
    normal = evidence.matched_normal_reference
    if normal.matching_method == "exact_regime_subsystem" and normal.operating_regime != evidence.operating_regime:
        _fail("EVIDENCE_V1_REGIME_MISMATCH", "/matched_normal_reference/operating_regime", "exact-regime reference must match evidence regime")
    policy = evidence.selection_policy
    if not (policy.pre_registered and policy.deterministic_tie_breaking and policy.regime_match_required and policy.subsystem_match_required) or policy.label_performance_used:
        _fail("EVIDENCE_V1_SELECTION_POLICY", "/selection_policy", "selection policy must be pre-registered and label-performance-free")


def _window_to_dict(window: WindowReferenceV1) -> dict[str, Any]:
    return {"window_id": window.window_id, "start_offset": window.start_offset, "end_offset": window.end_offset,
            "unit": window.unit, "artifact_hash": window.artifact_hash}


def _fail(code: str, path: str, message: str) -> None:
    raise EvidenceV1ModelError(code, path, message)
