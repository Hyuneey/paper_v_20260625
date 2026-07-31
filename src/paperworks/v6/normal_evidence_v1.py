"""Normal-only delayed-response evidence contracts for the v6 MVP."""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping

from paperworks.data.contracts_v2 import SplitRoleV2
from paperworks.v6.common import (
    CreationMetadataV1,
    V6_FOUNDATION_SCHEMA_VERSION,
    V6FoundationError,
    canonical_json_v1,
    deterministic_id,
    reject_unknown_fields,
    require_finite,
    require_identifier,
    require_sha256,
    require_sha256_refs,
    require_unique_strings,
    stable_hash_v1,
    verify_identity_fields,
)


NORMAL_EVIDENCE_ARTIFACT_TYPE = "normal_relation_evidence"
REQUIRED_PROHIBITED_CLAIMS = frozenset(
    {"physical_causality", "root_cause", "universal_invariant"}
)
NO_RULE_EVIDENCE_REASON_CODES = frozenset(
    {
        "insufficient_trigger_support",
        "insufficient_matched_response_support",
        "unstable_response_direction",
        "unstable_lag",
        "unstable_magnitude",
        "missing_matched_normal_reference",
        "missing_calibration_parameter",
        "relation_not_reproducible",
    }
)


class ResponseDirectionV1(str, Enum):
    INCREASE = "increase"
    DECREASE = "decrease"


class StabilityStatusV1(str, Enum):
    STABLE = "stable"
    UNSTABLE = "unstable"
    NOT_ASSESSED = "not_assessed"


class EvidenceStatusV1(str, Enum):
    SUPPORTED = "supported"
    INSUFFICIENT_SUPPORT = "insufficient_support"
    UNSTABLE = "unstable"


class OperatingRegimeStatusV1(str, Enum):
    VERIFIED = "verified"
    UNVERIFIED = "unverified"
    UNKNOWN = "unknown"


class CalibrationParameterRoleV1(str, Enum):
    LAG = "lag"
    TOLERANCE = "tolerance"
    PERSISTENCE = "persistence"


@dataclass(frozen=True)
class RelationSupportSummaryV1:
    trigger_count: int
    evaluable_trigger_count: int
    matched_response_count: int
    missing_response_count: int
    right_censored_count: int

    def __post_init__(self) -> None:
        values = (
            self.trigger_count,
            self.evaluable_trigger_count,
            self.matched_response_count,
            self.missing_response_count,
            self.right_censored_count,
        )
        if any(isinstance(item, bool) or not isinstance(item, int) or item < 0 for item in values):
            raise V6FoundationError("support counts must be non-negative integers")
        if self.trigger_count != self.evaluable_trigger_count + self.right_censored_count:
            raise V6FoundationError(
                "trigger_count must equal evaluable_trigger_count plus right_censored_count"
            )
        if self.evaluable_trigger_count != self.matched_response_count + self.missing_response_count:
            raise V6FoundationError(
                "evaluable_trigger_count must equal matched_response_count plus missing_response_count"
            )

    def to_dict(self) -> dict[str, int]:
        return {
            "trigger_count": self.trigger_count,
            "evaluable_trigger_count": self.evaluable_trigger_count,
            "matched_response_count": self.matched_response_count,
            "missing_response_count": self.missing_response_count,
            "right_censored_count": self.right_censored_count,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "RelationSupportSummaryV1":
        reject_unknown_fields(
            data,
            frozenset(
                {
                    "trigger_count",
                    "evaluable_trigger_count",
                    "matched_response_count",
                    "missing_response_count",
                    "right_censored_count",
                }
            ),
            "support_summary",
        )
        return cls(
            trigger_count=int(data["trigger_count"]),
            evaluable_trigger_count=int(data["evaluable_trigger_count"]),
            matched_response_count=int(data["matched_response_count"]),
            missing_response_count=int(data["missing_response_count"]),
            right_censored_count=int(data["right_censored_count"]),
        )


@dataclass(frozen=True)
class DistributionSummaryV1:
    count: int
    minimum: float
    p50: float
    p95: float | None
    maximum: float
    unit: str
    method: str
    value_semantics: str

    def __post_init__(self) -> None:
        if isinstance(self.count, bool) or not isinstance(self.count, int) or self.count < 0:
            raise V6FoundationError("distribution summary count must be non-negative")
        minimum = require_finite(self.minimum, "distribution_summary.minimum")
        p50 = require_finite(self.p50, "distribution_summary.p50")
        maximum = require_finite(self.maximum, "distribution_summary.maximum")
        p95 = (
            require_finite(self.p95, "distribution_summary.p95")
            if self.p95 is not None
            else None
        )
        if not self.unit or not self.method or not self.value_semantics:
            raise V6FoundationError(
                "distribution summary unit, method, and value_semantics are required"
            )
        if minimum > p50 or p50 > maximum:
            raise V6FoundationError("distribution statistics are not ordered")
        if p95 is not None and (p50 > p95 or p95 > maximum):
            raise V6FoundationError("distribution p95 is not ordered")
        if self.value_semantics in {
            "lag",
            "absolute_response_magnitude",
            "persistence",
        } and minimum < 0:
            raise V6FoundationError(
                f"{self.value_semantics} summary values must be non-negative"
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "count": self.count,
            "minimum": self.minimum,
            "p50": self.p50,
            "p95": self.p95,
            "maximum": self.maximum,
            "unit": self.unit,
            "method": self.method,
            "value_semantics": self.value_semantics,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "DistributionSummaryV1":
        reject_unknown_fields(
            data,
            frozenset(
                {
                    "count",
                    "minimum",
                    "p50",
                    "p95",
                    "maximum",
                    "unit",
                    "method",
                    "value_semantics",
                }
            ),
            "distribution_summary",
        )
        return cls(
            count=int(data["count"]),
            minimum=float(data["minimum"]),
            p50=float(data["p50"]),
            p95=float(data["p95"]) if data.get("p95") is not None else None,
            maximum=float(data["maximum"]),
            unit=str(data["unit"]),
            method=str(data["method"]),
            value_semantics=str(data["value_semantics"]),
        )


@dataclass(frozen=True)
class RelationStabilitySummaryV1:
    status: StabilityStatusV1
    method: str
    replicate_count: int
    variation_measure: float | None
    confidence_lower: float | None = None
    confidence_upper: float | None = None

    def __post_init__(self) -> None:
        if (
            isinstance(self.replicate_count, bool)
            or not isinstance(self.replicate_count, int)
            or self.replicate_count < 0
        ):
            raise V6FoundationError("stability replicate_count must be non-negative")
        if (self.confidence_lower is None) != (self.confidence_upper is None):
            raise V6FoundationError("stability confidence bounds must be paired")
        if self.status is StabilityStatusV1.NOT_ASSESSED:
            if (
                self.method != "not_assessed"
                or self.replicate_count != 0
                or self.variation_measure is not None
                or self.confidence_lower is not None
            ):
                raise V6FoundationError(
                    "not_assessed stability fields are inconsistent"
                )
            return
        if not self.method or self.method == "not_assessed":
            raise V6FoundationError("assessed stability requires a method")
        if self.replicate_count <= 0 or self.variation_measure is None:
            raise V6FoundationError(
                "assessed stability requires replicates and variation_measure"
            )
        require_finite(self.variation_measure, "stability.variation_measure")
        if self.confidence_lower is not None and self.confidence_upper is not None:
            lower = require_finite(self.confidence_lower, "stability.confidence_lower")
            upper = require_finite(self.confidence_upper, "stability.confidence_upper")
            if lower > upper:
                raise V6FoundationError("stability confidence bounds are inverted")

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status.value,
            "method": self.method,
            "replicate_count": self.replicate_count,
            "variation_measure": self.variation_measure,
            "confidence_lower": self.confidence_lower,
            "confidence_upper": self.confidence_upper,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "RelationStabilitySummaryV1":
        reject_unknown_fields(
            data,
            frozenset(
                {
                    "status",
                    "method",
                    "replicate_count",
                    "variation_measure",
                    "confidence_lower",
                    "confidence_upper",
                }
            ),
            "stability_summary",
        )
        return cls(
            status=StabilityStatusV1(str(data["status"])),
            method=str(data["method"]),
            replicate_count=int(data["replicate_count"]),
            variation_measure=(
                float(data["variation_measure"])
                if data.get("variation_measure") is not None
                else None
            ),
            confidence_lower=(
                float(data["confidence_lower"])
                if data.get("confidence_lower") is not None
                else None
            ),
            confidence_upper=(
                float(data["confidence_upper"])
                if data.get("confidence_upper") is not None
                else None
            ),
        )


@dataclass(frozen=True)
class CalibrationParameterReferenceV1:
    role: CalibrationParameterRoleV1
    artifact_ref: str

    def __post_init__(self) -> None:
        require_sha256(self.artifact_ref, "calibration_parameter_ref.artifact_ref")

    def to_dict(self) -> dict[str, str]:
        return {"role": self.role.value, "artifact_ref": self.artifact_ref}

    @classmethod
    def from_dict(
        cls, data: Mapping[str, Any]
    ) -> "CalibrationParameterReferenceV1":
        reject_unknown_fields(
            data,
            frozenset({"role", "artifact_ref"}),
            "calibration_parameter_ref",
        )
        return cls(
            role=CalibrationParameterRoleV1(str(data["role"])),
            artifact_ref=str(data["artifact_ref"]),
        )


@dataclass(frozen=True)
class NormalRelationEvidenceV1:
    dataset_manifest_id: str
    data_view_id: str
    split_manifest_id: str
    split_role: SplitRoleV2
    process_scope: tuple[str, ...]
    source_variable: str
    target_variable: str
    source_metadata_ref: str
    target_metadata_ref: str
    candidate_universe_ref: str
    candidate_edge_refs: tuple[str, ...]
    relation_family: str
    response_direction: ResponseDirectionV1
    operating_regime_id: str
    operating_regime_status: OperatingRegimeStatusV1
    operating_regime_condition_refs: tuple[str, ...]
    support_summary: RelationSupportSummaryV1
    lag_summary: DistributionSummaryV1 | None
    response_magnitude_summary: DistributionSummaryV1 | None
    persistence_summary: DistributionSummaryV1 | None
    stability_summary: RelationStabilitySummaryV1
    evidence_status: EvidenceStatusV1
    evidence_insufficiency_reasons: tuple[str, ...]
    matched_normal_reference_refs: tuple[str, ...]
    calibration_parameter_refs: tuple[CalibrationParameterReferenceV1, ...]
    provenance_references: tuple[str, ...]
    creation_metadata: CreationMetadataV1
    raw_values_included: bool
    label_performance_used: bool
    detector_context_used: bool
    prohibited_claims: tuple[str, ...]
    validity_authority_granted: bool
    runtime_authority_granted: bool
    claim_boundary: str
    schema_version: str = V6_FOUNDATION_SCHEMA_VERSION
    artifact_type: str = NORMAL_EVIDENCE_ARTIFACT_TYPE

    def __post_init__(self) -> None:
        if self.schema_version != V6_FOUNDATION_SCHEMA_VERSION:
            raise V6FoundationError("unsupported normal evidence schema_version")
        if self.artifact_type != NORMAL_EVIDENCE_ARTIFACT_TYPE:
            raise V6FoundationError("invalid normal evidence artifact_type")
        for field_name, value in (
            ("dataset_manifest_id", self.dataset_manifest_id),
            ("data_view_id", self.data_view_id),
            ("split_manifest_id", self.split_manifest_id),
            ("source_metadata_ref", self.source_metadata_ref),
            ("target_metadata_ref", self.target_metadata_ref),
            ("candidate_universe_ref", self.candidate_universe_ref),
        ):
            require_sha256(value, field_name)
        if self.split_role is not SplitRoleV2.NORMAL_RELATION_CALIBRATION:
            raise V6FoundationError(
                "normal evidence requires normal_relation_calibration split role"
            )
        object.__setattr__(
            self,
            "process_scope",
            require_unique_strings(
                self.process_scope, "process_scope", allow_empty=False
            ),
        )
        require_identifier(self.source_variable, "source_variable")
        require_identifier(self.target_variable, "target_variable")
        if self.source_variable == self.target_variable:
            raise V6FoundationError("source_variable and target_variable must differ")
        object.__setattr__(
            self,
            "candidate_edge_refs",
            require_sha256_refs(
                self.candidate_edge_refs, "candidate_edge_refs", allow_empty=False
            ),
        )
        if self.relation_family != "delayed_response":
            raise V6FoundationError("only delayed_response relation evidence is supported")
        require_identifier(self.operating_regime_id, "operating_regime_id")
        object.__setattr__(
            self,
            "operating_regime_condition_refs",
            require_sha256_refs(
                self.operating_regime_condition_refs,
                "operating_regime_condition_refs",
            ),
        )
        if (
            self.operating_regime_status is OperatingRegimeStatusV1.VERIFIED
            and not self.operating_regime_condition_refs
        ):
            raise V6FoundationError(
                "verified operating regime requires condition references"
            )
        for name, summary in (
            ("lag_summary", self.lag_summary),
            ("response_magnitude_summary", self.response_magnitude_summary),
            ("persistence_summary", self.persistence_summary),
        ):
            if summary is not None and summary.count > self.support_summary.matched_response_count:
                raise V6FoundationError(
                    f"{name}.count exceeds matched normal response support"
                )
        if self.lag_summary is not None and self.lag_summary.value_semantics != "lag":
            raise V6FoundationError("lag_summary must use lag value semantics")
        if (
            self.response_magnitude_summary is not None
            and self.response_magnitude_summary.value_semantics
            != "absolute_response_magnitude"
        ):
            raise V6FoundationError(
                "response magnitude must use absolute_response_magnitude semantics"
            )
        if (
            self.persistence_summary is not None
            and self.persistence_summary.value_semantics != "persistence"
        ):
            raise V6FoundationError(
                "persistence_summary must use persistence value semantics"
            )
        object.__setattr__(
            self,
            "evidence_insufficiency_reasons",
            require_unique_strings(
                self.evidence_insufficiency_reasons,
                "evidence_insufficiency_reasons",
            ),
        )
        unknown_reasons = set(self.evidence_insufficiency_reasons) - NO_RULE_EVIDENCE_REASON_CODES
        if unknown_reasons:
            raise V6FoundationError("unregistered evidence insufficiency reason")
        object.__setattr__(
            self,
            "matched_normal_reference_refs",
            require_sha256_refs(
                self.matched_normal_reference_refs,
                "matched_normal_reference_refs",
            ),
        )
        roles = tuple(item.role for item in self.calibration_parameter_refs)
        if len(roles) != len(set(roles)):
            raise V6FoundationError("calibration parameter roles must be unique")
        object.__setattr__(
            self,
            "provenance_references",
            require_sha256_refs(
                self.provenance_references,
                "provenance_references",
                allow_empty=False,
            ),
        )
        if self.evidence_status is EvidenceStatusV1.SUPPORTED:
            required_roles = {
                CalibrationParameterRoleV1.LAG,
                CalibrationParameterRoleV1.TOLERANCE,
            }
            if self.support_summary.matched_response_count < 1:
                raise V6FoundationError(
                    "supported evidence requires a matched normal response"
                )
            if self.stability_summary.status is not StabilityStatusV1.STABLE:
                raise V6FoundationError("supported evidence requires stable relation")
            if self.lag_summary is None or self.response_magnitude_summary is None:
                raise V6FoundationError(
                    "supported evidence requires lag and magnitude summaries"
                )
            if (
                self.lag_summary.count < 1
                or self.response_magnitude_summary.count < 1
            ):
                raise V6FoundationError(
                    "supported evidence summaries require positive support"
                )
            if not self.matched_normal_reference_refs:
                raise V6FoundationError(
                    "supported evidence requires matched-normal references"
                )
            if not required_roles.issubset(roles):
                raise V6FoundationError(
                    "supported evidence requires lag and tolerance parameter references"
                )
            if self.evidence_insufficiency_reasons:
                raise V6FoundationError(
                    "supported evidence cannot contain insufficiency reasons"
                )
        elif self.evidence_status is EvidenceStatusV1.INSUFFICIENT_SUPPORT:
            if not self.evidence_insufficiency_reasons:
                raise V6FoundationError(
                    "insufficient evidence requires a machine-readable reason"
                )
        elif self.stability_summary.status is not StabilityStatusV1.UNSTABLE:
            raise V6FoundationError(
                "unstable evidence requires an unstable stability result"
            )
        if self.evidence_status is EvidenceStatusV1.UNSTABLE and not self.evidence_insufficiency_reasons:
            raise V6FoundationError("unstable evidence requires a reason code")
        if self.raw_values_included:
            raise V6FoundationError("normal evidence cannot contain raw values")
        if self.label_performance_used:
            raise V6FoundationError(
                "label performance cannot determine normal evidence"
            )
        if self.detector_context_used:
            raise V6FoundationError(
                "detector context cannot determine normal relation evidence"
            )
        object.__setattr__(
            self,
            "prohibited_claims",
            require_unique_strings(self.prohibited_claims, "prohibited_claims"),
        )
        if not REQUIRED_PROHIBITED_CLAIMS.issubset(self.prohibited_claims):
            raise V6FoundationError("normal evidence claim boundary is incomplete")
        if self.validity_authority_granted or self.runtime_authority_granted:
            raise V6FoundationError(
                "normal evidence cannot grant validity or runtime authority"
            )
        if not self.claim_boundary:
            raise V6FoundationError("claim_boundary is required")

    def _content_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "artifact_type": self.artifact_type,
            "dataset_manifest_id": self.dataset_manifest_id,
            "data_view_id": self.data_view_id,
            "split_manifest_id": self.split_manifest_id,
            "split_role": self.split_role.value,
            "process_scope": list(self.process_scope),
            "source_variable": self.source_variable,
            "target_variable": self.target_variable,
            "source_metadata_ref": self.source_metadata_ref,
            "target_metadata_ref": self.target_metadata_ref,
            "candidate_universe_ref": self.candidate_universe_ref,
            "candidate_edge_refs": list(self.candidate_edge_refs),
            "relation_family": self.relation_family,
            "response_direction": self.response_direction.value,
            "operating_regime_id": self.operating_regime_id,
            "operating_regime_status": self.operating_regime_status.value,
            "operating_regime_condition_refs": list(
                self.operating_regime_condition_refs
            ),
            "support_summary": self.support_summary.to_dict(),
            "lag_summary": self.lag_summary.to_dict() if self.lag_summary else None,
            "response_magnitude_summary": (
                self.response_magnitude_summary.to_dict()
                if self.response_magnitude_summary
                else None
            ),
            "persistence_summary": (
                self.persistence_summary.to_dict()
                if self.persistence_summary
                else None
            ),
            "stability_summary": self.stability_summary.to_dict(),
            "evidence_status": self.evidence_status.value,
            "evidence_insufficiency_reasons": list(
                self.evidence_insufficiency_reasons
            ),
            "matched_normal_reference_refs": list(
                self.matched_normal_reference_refs
            ),
            "calibration_parameter_refs": [
                item.to_dict() for item in self.calibration_parameter_refs
            ],
            "provenance_references": list(self.provenance_references),
            "creation_metadata": self.creation_metadata.to_dict(),
            "raw_values_included": self.raw_values_included,
            "label_performance_used": self.label_performance_used,
            "detector_context_used": self.detector_context_used,
            "prohibited_claims": list(self.prohibited_claims),
            "validity_authority_granted": self.validity_authority_granted,
            "runtime_authority_granted": self.runtime_authority_granted,
            "claim_boundary": self.claim_boundary,
        }

    @property
    def evidence_id(self) -> str:
        return deterministic_id("NRE-V1", self._content_dict())

    @property
    def artifact_hash(self) -> str:
        payload = self._content_dict()
        payload["evidence_id"] = self.evidence_id
        return stable_hash_v1(payload)

    def to_dict(self) -> dict[str, Any]:
        payload = self._content_dict()
        payload["evidence_id"] = self.evidence_id
        payload["artifact_hash"] = self.artifact_hash
        return payload

    def to_json(self) -> str:
        return canonical_json_v1(self.to_dict())

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "NormalRelationEvidenceV1":
        reject_unknown_fields(
            data,
            frozenset(
                {
                    "schema_version",
                    "artifact_type",
                    "evidence_id",
                    "artifact_hash",
                    "dataset_manifest_id",
                    "data_view_id",
                    "split_manifest_id",
                    "split_role",
                    "process_scope",
                    "source_variable",
                    "target_variable",
                    "source_metadata_ref",
                    "target_metadata_ref",
                    "candidate_universe_ref",
                    "candidate_edge_refs",
                    "relation_family",
                    "response_direction",
                    "operating_regime_id",
                    "operating_regime_status",
                    "operating_regime_condition_refs",
                    "support_summary",
                    "lag_summary",
                    "response_magnitude_summary",
                    "persistence_summary",
                    "stability_summary",
                    "evidence_status",
                    "evidence_insufficiency_reasons",
                    "matched_normal_reference_refs",
                    "calibration_parameter_refs",
                    "provenance_references",
                    "creation_metadata",
                    "raw_values_included",
                    "label_performance_used",
                    "detector_context_used",
                    "prohibited_claims",
                    "validity_authority_granted",
                    "runtime_authority_granted",
                    "claim_boundary",
                }
            ),
            NORMAL_EVIDENCE_ARTIFACT_TYPE,
        )
        lag = data.get("lag_summary")
        magnitude = data.get("response_magnitude_summary")
        persistence = data.get("persistence_summary")
        result = cls(
            dataset_manifest_id=str(data["dataset_manifest_id"]),
            data_view_id=str(data["data_view_id"]),
            split_manifest_id=str(data["split_manifest_id"]),
            split_role=SplitRoleV2(str(data["split_role"])),
            process_scope=tuple(str(item) for item in data["process_scope"]),
            source_variable=str(data["source_variable"]),
            target_variable=str(data["target_variable"]),
            source_metadata_ref=str(data["source_metadata_ref"]),
            target_metadata_ref=str(data["target_metadata_ref"]),
            candidate_universe_ref=str(data["candidate_universe_ref"]),
            candidate_edge_refs=tuple(
                str(item) for item in data["candidate_edge_refs"]
            ),
            relation_family=str(data["relation_family"]),
            response_direction=ResponseDirectionV1(str(data["response_direction"])),
            operating_regime_id=str(data["operating_regime_id"]),
            operating_regime_status=OperatingRegimeStatusV1(
                str(data["operating_regime_status"])
            ),
            operating_regime_condition_refs=tuple(
                str(item) for item in data["operating_regime_condition_refs"]
            ),
            support_summary=RelationSupportSummaryV1.from_dict(
                data["support_summary"]
            ),
            lag_summary=DistributionSummaryV1.from_dict(lag) if lag else None,
            response_magnitude_summary=(
                DistributionSummaryV1.from_dict(magnitude)
                if magnitude
                else None
            ),
            persistence_summary=(
                DistributionSummaryV1.from_dict(persistence)
                if persistence
                else None
            ),
            stability_summary=RelationStabilitySummaryV1.from_dict(
                data["stability_summary"]
            ),
            evidence_status=EvidenceStatusV1(str(data["evidence_status"])),
            evidence_insufficiency_reasons=tuple(
                str(item) for item in data["evidence_insufficiency_reasons"]
            ),
            matched_normal_reference_refs=tuple(
                str(item) for item in data["matched_normal_reference_refs"]
            ),
            calibration_parameter_refs=tuple(
                CalibrationParameterReferenceV1.from_dict(item)
                for item in data["calibration_parameter_refs"]
            ),
            provenance_references=tuple(
                str(item) for item in data["provenance_references"]
            ),
            creation_metadata=CreationMetadataV1.from_dict(
                data["creation_metadata"]
            ),
            raw_values_included=data["raw_values_included"] is True,
            label_performance_used=data["label_performance_used"] is True,
            detector_context_used=data["detector_context_used"] is True,
            prohibited_claims=tuple(
                str(item) for item in data["prohibited_claims"]
            ),
            validity_authority_granted=data["validity_authority_granted"] is True,
            runtime_authority_granted=data["runtime_authority_granted"] is True,
            claim_boundary=str(data["claim_boundary"]),
            schema_version=str(
                data.get("schema_version", V6_FOUNDATION_SCHEMA_VERSION)
            ),
            artifact_type=str(
                data.get("artifact_type", NORMAL_EVIDENCE_ARTIFACT_TYPE)
            ),
        )
        verify_identity_fields(
            data,
            id_field="evidence_id",
            observed_id=result.evidence_id,
            observed_hash=result.artifact_hash,
        )
        return result

    @classmethod
    def from_json(cls, text: str) -> "NormalRelationEvidenceV1":
        document = json.loads(text)
        if not isinstance(document, dict):
            raise V6FoundationError("normal evidence must be a JSON object")
        return cls.from_dict(document)
