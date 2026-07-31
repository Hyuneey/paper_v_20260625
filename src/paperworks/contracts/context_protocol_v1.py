"""Structural collection and normalized evidence interfaces for Rule v1."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Protocol, runtime_checkable

from paperworks.contracts.evidence_v1 import (
    EvidenceLagRangeV1,
    EvidencePackageV1,
    EvidenceSelectionPolicyV1,
    evidence_package_to_dict,
    parse_evidence_package,
)
from paperworks.contracts.graph_v1 import CandidateGraphV1
from paperworks.contracts.normal_evidence_binding_v1 import (
    NormalReferenceSetBindingV1,
    RuleEvidenceBindingV1,
)
from paperworks.contracts.parameter_v1 import CalibrationParameterV1


BoundEvidenceV1 = EvidencePackageV1 | RuleEvidenceBindingV1


@runtime_checkable
class DelayedResponseArtifactCollectionProtocolV1(Protocol):
    """Bounded verifier/runtime surface shared by legacy and v6 collections."""

    graph: CandidateGraphV1
    evidence: BoundEvidenceV1
    parameters: tuple[CalibrationParameterV1, ...]

    @property
    def graph_by_id(self) -> Mapping[str, CandidateGraphV1]: ...

    @property
    def edge_by_id(self) -> Mapping[str, Any]: ...

    @property
    def evidence_by_id(self) -> Mapping[str, BoundEvidenceV1]: ...

    @property
    def normal_reference_by_id(self) -> Mapping[str, Any]: ...

    @property
    def parameter_by_id(self) -> Mapping[str, CalibrationParameterV1]: ...

    @property
    def rule_binding_verified(self) -> bool: ...

    @property
    def runtime_authorized(self) -> bool: ...


@dataclass(frozen=True)
class NormalizedEvidenceViewV1:
    evidence_id: str
    artifact_hash: str
    dataset_version: str
    subsystem: str
    source_variables: tuple[str, ...]
    target_variables: tuple[str, ...]
    operating_regime: str
    candidate_lag_range: EvidenceLagRangeV1
    data_split: str
    supported_claims: tuple[str, ...]
    prohibited_claims: tuple[str, ...]
    raw_values_included: bool
    label_performance_used: bool
    selection_policy: EvidenceSelectionPolicyV1
    normal_reference_ids: tuple[str, ...]
    normal_reference_binding_hash: str | None
    normal_relation_evidence_hash: str | None
    validity_authority_granted: bool
    runtime_authority_granted: bool
    evidence_kind: str


@dataclass(frozen=True)
class NormalizedNormalReferenceViewV1:
    reference_id: str
    operating_regime: str
    subsystem: str
    matching_method: str
    deterministic_tie_breaking: bool
    label_performance_used: bool
    source_reference_hashes: tuple[str, ...]
    binding_artifact_hash: str
    normal_relation_evidence_hash: str | None


def normalize_evidence_v1(
    evidence: BoundEvidenceV1,
) -> NormalizedEvidenceViewV1:
    """Project legacy and v6 evidence onto the verifier's bounded interface."""

    if isinstance(evidence, EvidencePackageV1):
        normal = evidence.matched_normal_reference
        return NormalizedEvidenceViewV1(
            evidence_id=evidence.evidence_id,
            artifact_hash=evidence.artifact_hash,
            dataset_version=evidence.dataset_version,
            subsystem=normal.subsystem,
            source_variables=evidence.source_variables,
            target_variables=evidence.target_variables,
            operating_regime=evidence.operating_regime,
            candidate_lag_range=evidence.candidate_lag_range,
            data_split=evidence.data_split,
            supported_claims=evidence.supported_claims,
            prohibited_claims=evidence.prohibited_claims,
            raw_values_included=evidence.raw_values_included,
            label_performance_used=(
                evidence.selection_policy.label_performance_used
            ),
            selection_policy=evidence.selection_policy,
            normal_reference_ids=(normal.reference_id,),
            normal_reference_binding_hash=None,
            normal_relation_evidence_hash=None,
            validity_authority_granted=False,
            runtime_authority_granted=False,
            evidence_kind="legacy_evidence_package",
        )
    if isinstance(evidence, RuleEvidenceBindingV1):
        return NormalizedEvidenceViewV1(
            evidence_id=evidence.evidence_id,
            artifact_hash=evidence.artifact_hash,
            dataset_version=evidence.dataset_version,
            subsystem=evidence.subsystem,
            source_variables=evidence.source_variables,
            target_variables=evidence.target_variables,
            operating_regime=evidence.operating_regime_id,
            candidate_lag_range=evidence.candidate_lag_range,
            data_split=evidence.data_split,
            supported_claims=evidence.supported_claims,
            prohibited_claims=evidence.prohibited_claims,
            raw_values_included=evidence.raw_values_included,
            label_performance_used=evidence.label_performance_used,
            selection_policy=evidence.selection_policy,
            normal_reference_ids=(evidence.normal_reference_binding_ref,),
            normal_reference_binding_hash=(
                evidence.normal_reference_binding_hash
            ),
            normal_relation_evidence_hash=(
                evidence.normal_relation_evidence_hash
            ),
            validity_authority_granted=(
                evidence.validity_authority_granted
            ),
            runtime_authority_granted=(
                evidence.runtime_authority_granted
            ),
            evidence_kind="v6_rule_evidence_binding",
        )
    raise TypeError("unsupported delayed-response evidence type")


def normalize_normal_reference_v1(
    reference: Any,
) -> NormalizedNormalReferenceViewV1:
    """Normalize one legacy or v6 normal-reference binding."""

    if isinstance(reference, NormalReferenceSetBindingV1):
        return NormalizedNormalReferenceViewV1(
            reference_id=reference.normal_reference_id,
            operating_regime=reference.operating_regime_id,
            subsystem=reference.subsystem,
            matching_method=reference.matching_method,
            deterministic_tie_breaking=(
                reference.deterministic_tie_breaking
            ),
            label_performance_used=reference.label_performance_used,
            source_reference_hashes=reference.source_normal_reference_hashes,
            binding_artifact_hash=reference.artifact_hash,
            normal_relation_evidence_hash=(
                reference.normal_relation_evidence_hash
            ),
        )
    required = (
        "reference_id",
        "operating_regime",
        "subsystem",
        "matching_method",
        "tie_breaker",
        "artifact_hash",
    )
    if all(hasattr(reference, name) for name in required):
        return NormalizedNormalReferenceViewV1(
            reference_id=str(reference.reference_id),
            operating_regime=str(reference.operating_regime),
            subsystem=str(reference.subsystem),
            matching_method=str(reference.matching_method),
            deterministic_tie_breaking=bool(reference.tie_breaker),
            label_performance_used=False,
            source_reference_hashes=(str(reference.artifact_hash),),
            binding_artifact_hash=str(reference.artifact_hash),
            normal_relation_evidence_hash=None,
        )
    raise TypeError("unsupported normal-reference type")


def bound_evidence_to_dict_v1(evidence: BoundEvidenceV1) -> dict[str, Any]:
    if isinstance(evidence, EvidencePackageV1):
        return evidence_package_to_dict(evidence)
    if isinstance(evidence, RuleEvidenceBindingV1):
        return evidence.to_dict()
    raise TypeError("unsupported delayed-response evidence type")


def reparse_bound_evidence_v1(evidence: BoundEvidenceV1) -> BoundEvidenceV1:
    """Reparse a bound evidence artifact using its exact concrete parser."""

    if isinstance(evidence, EvidencePackageV1):
        return parse_evidence_package(evidence_package_to_dict(evidence))
    if isinstance(evidence, RuleEvidenceBindingV1):
        return RuleEvidenceBindingV1.from_dict(evidence.to_dict())
    raise TypeError("unsupported delayed-response evidence type")
