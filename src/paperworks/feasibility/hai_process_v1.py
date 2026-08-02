"""HAI P1/P3 normal-only delayed-response feasibility contracts and logic."""

from __future__ import annotations

import json
import math
import re
from array import array
from collections import Counter
from dataclasses import dataclass
from enum import Enum
from hashlib import sha256
from pathlib import Path, PurePosixPath
from statistics import median
from typing import Any, Iterable, Mapping, Sequence

from paperworks.data.contracts_v2 import (
    AggregationDescriptionV2,
    CreationMetadataV2,
    DataViewKindV2,
    DataViewManifestV2,
    ProvenanceStatusV2,
    RawRangeV2,
    SealedAccessStatusV2,
    SplitManifestV2,
    SplitRoleV2,
)
from paperworks.data.splits_v2 import validate_split_collection_v2


SCHEMA_VERSION = "1.0.0"
APPROVED_TRAIN_FILES = (
    "hai-23.05/hai-train1.csv",
    "hai-23.05/hai-train2.csv",
    "hai-23.05/hai-train3.csv",
    "hai-23.05/hai-train4.csv",
)
PROHIBITED_PATH_TOKENS = (
    "hai-test",
    "label-test",
    "summary_label",
    "private",
    "custody",
    "attack",
)
FIXED_HORIZONS = (1, 5, 10, 30, 60)
PROCESS_NAMES = {"P1": "Boiler", "P3": "Water Treatment"}
_SHA256 = re.compile(r"^[a-f0-9]{64}$")
_COMMIT = re.compile(r"^[a-f0-9]{40}$")


class HAIFeasibilityError(ValueError):
    """Raised when a TASK-039B scientific or artifact contract fails closed."""


class TASK039BDataAccessError(PermissionError):
    """Raised before a prohibited TASK-039B file or column access."""

    issue_code = "TASK039B_PROHIBITED_DATA_ACCESS"


class SemanticRoleV2(str, Enum):
    CONTROL_COMMAND = "control_command"
    ACTUATOR_STATE = "actuator_state"
    ACTUATOR_FEEDBACK = "actuator_feedback"
    SETPOINT = "setpoint"
    PROCESS_SENSOR = "process_sensor"
    STATUS_OR_ALARM = "status_or_alarm"
    DERIVED_OR_INTERNAL = "derived_or_internal"
    UNKNOWN = "unknown"


class ObservedDomainV1(str, Enum):
    BINARY = "binary"
    DISCRETE = "discrete"
    CONTINUOUS = "continuous"
    CONSTANT = "constant"
    UNKNOWN = "unknown"


class MetadataConfidenceV1(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    INSUFFICIENT = "insufficient"


class MetadataReviewStatusV1(str, Enum):
    REVIEWED = "reviewed"
    UNRESOLVED = "unresolved"


class ResponseDirectionV1(str, Enum):
    INCREASE = "increase"
    DECREASE = "decrease"
    AMBIGUOUS = "ambiguous"


def canonical_json(value: Mapping[str, Any]) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    )


def canonical_self_hash(value: Mapping[str, Any], field_name: str = "artifact_hash") -> str:
    payload = dict(value)
    payload.pop(field_name, None)
    return sha256(canonical_json(payload).encode("utf-8")).hexdigest()


def _artifact_dict(content: Mapping[str, Any]) -> dict[str, Any]:
    payload = dict(content)
    payload["artifact_hash"] = canonical_self_hash(payload)
    return payload


def _require_hash(value: str, field_name: str) -> None:
    if _SHA256.fullmatch(value) is None:
        raise HAIFeasibilityError(f"{field_name} must be a lowercase SHA-256")


def _require_commit(value: str, field_name: str) -> None:
    if _COMMIT.fullmatch(value) is None:
        raise HAIFeasibilityError(f"{field_name} must be a full Git commit")


def _finite(value: float, field_name: str) -> float:
    converted = float(value)
    if not math.isfinite(converted):
        raise HAIFeasibilityError(f"{field_name} must be finite")
    return converted


def _unique_strings(values: Iterable[str], field_name: str) -> tuple[str, ...]:
    normalized = tuple(str(item) for item in values)
    if any(not item for item in normalized) or len(normalized) != len(set(normalized)):
        raise HAIFeasibilityError(f"{field_name} must contain unique non-empty strings")
    return normalized


@dataclass(frozen=True)
class HAIMetadataEvidenceRecordV1:
    evidence_id: str
    evidence_type: str
    source_reference: str
    page_references: tuple[int, ...]
    excerpt_hash: str | None
    supports_semantic_role: bool
    supports_unit_or_quantity: bool
    claim_boundary: str
    schema_version: str = SCHEMA_VERSION
    artifact_type: str = "hai_metadata_evidence_record_v1"

    def __post_init__(self) -> None:
        if not self.evidence_id or not self.evidence_type or not self.source_reference:
            raise HAIFeasibilityError("metadata evidence identity is required")
        if tuple(sorted(set(self.page_references))) != self.page_references:
            raise HAIFeasibilityError("page references must be sorted and unique")
        if any(item <= 0 for item in self.page_references):
            raise HAIFeasibilityError("page references must be positive")
        if self.excerpt_hash is not None:
            _require_hash(self.excerpt_hash, "excerpt_hash")
        if self.claim_boundary != "metadata_only_not_causal_evidence":
            raise HAIFeasibilityError("metadata evidence claim boundary is invalid")

    def _content_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "artifact_type": self.artifact_type,
            "evidence_id": self.evidence_id,
            "evidence_type": self.evidence_type,
            "source_reference": self.source_reference,
            "page_references": list(self.page_references),
            "excerpt_hash": self.excerpt_hash,
            "supports_semantic_role": self.supports_semantic_role,
            "supports_unit_or_quantity": self.supports_unit_or_quantity,
            "claim_boundary": self.claim_boundary,
        }

    @property
    def artifact_hash(self) -> str:
        return canonical_self_hash(self._content_dict())

    def to_dict(self) -> dict[str, Any]:
        return _artifact_dict(self._content_dict())


@dataclass(frozen=True)
class HAIVariableMetadataV2:
    variable_name: str
    process_id: str
    subsystem_or_stage: str
    semantic_role: SemanticRoleV2
    observed_value_domain: ObservedDomainV1
    physical_quantity_or_device: str
    unit: str
    description_summary: str
    manual_reference: tuple[int, ...]
    official_graph_references: tuple[str, ...]
    name_pattern_evidence: str
    data_domain_evidence: str
    metadata_confidence: MetadataConfidenceV1
    review_status: MetadataReviewStatusV1
    source_eligibility: bool
    target_eligibility: bool
    exclusion_reasons: tuple[str, ...]
    evidence_record_refs: tuple[str, ...]
    raw_values_included: bool = False
    schema_version: str = SCHEMA_VERSION
    artifact_type: str = "hai_variable_metadata_v2"

    def __post_init__(self) -> None:
        if self.process_id not in PROCESS_NAMES:
            raise HAIFeasibilityError("metadata process must be P1 or P3")
        if not self.variable_name.startswith(f"{self.process_id}_"):
            raise HAIFeasibilityError("variable name does not match process prefix")
        if not self.subsystem_or_stage or not self.physical_quantity_or_device:
            raise HAIFeasibilityError("metadata scope and quantity/device are required")
        if len(self.description_summary) > 320 or "\n" in self.description_summary:
            raise HAIFeasibilityError("description summary must be bounded to one line")
        if tuple(sorted(set(self.manual_reference))) != self.manual_reference:
            raise HAIFeasibilityError("manual references must be sorted and unique")
        _unique_strings(self.official_graph_references, "official_graph_references")
        _unique_strings(self.exclusion_reasons, "exclusion_reasons")
        for value in self.evidence_record_refs:
            _require_hash(value, "evidence_record_refs")
        if self.raw_values_included:
            raise HAIFeasibilityError("variable metadata cannot contain raw values")
        if self.review_status is MetadataReviewStatusV1.REVIEWED and not self.manual_reference:
            raise HAIFeasibilityError("reviewed metadata requires a manual reference")
        if self.source_eligibility and not (
            self.semantic_role
            in {
                SemanticRoleV2.CONTROL_COMMAND,
                SemanticRoleV2.ACTUATOR_STATE,
                SemanticRoleV2.ACTUATOR_FEEDBACK,
            }
            and self.observed_value_domain
            in {ObservedDomainV1.BINARY, ObservedDomainV1.DISCRETE}
            and self.review_status is MetadataReviewStatusV1.REVIEWED
            and self.metadata_confidence
            in {MetadataConfidenceV1.HIGH, MetadataConfidenceV1.MEDIUM}
        ):
            raise HAIFeasibilityError("source eligibility is not supported by metadata")
        if self.target_eligibility and not (
            self.semantic_role is SemanticRoleV2.PROCESS_SENSOR
            and self.observed_value_domain is ObservedDomainV1.CONTINUOUS
            and self.review_status is MetadataReviewStatusV1.REVIEWED
            and self.metadata_confidence
            in {MetadataConfidenceV1.HIGH, MetadataConfidenceV1.MEDIUM}
        ):
            raise HAIFeasibilityError("target eligibility is not supported by metadata")

    def _content_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "artifact_type": self.artifact_type,
            "variable_name": self.variable_name,
            "process_id": self.process_id,
            "subsystem_or_stage": self.subsystem_or_stage,
            "semantic_role": self.semantic_role.value,
            "observed_value_domain": self.observed_value_domain.value,
            "physical_quantity_or_device": self.physical_quantity_or_device,
            "unit": self.unit,
            "description_summary": self.description_summary,
            "manual_reference": list(self.manual_reference),
            "official_graph_references": list(self.official_graph_references),
            "name_pattern_evidence": self.name_pattern_evidence,
            "data_domain_evidence": self.data_domain_evidence,
            "metadata_confidence": self.metadata_confidence.value,
            "review_status": self.review_status.value,
            "source_eligibility": self.source_eligibility,
            "target_eligibility": self.target_eligibility,
            "exclusion_reasons": list(self.exclusion_reasons),
            "evidence_record_refs": list(self.evidence_record_refs),
            "raw_values_included": self.raw_values_included,
        }

    @property
    def artifact_hash(self) -> str:
        return canonical_self_hash(self._content_dict())

    def to_dict(self) -> dict[str, Any]:
        return _artifact_dict(self._content_dict())


@dataclass(frozen=True)
class HAIVariableDomainDiagnosticV1:
    variable_name: str
    process_id: str
    total_value_count: int
    finite_value_count: int
    missing_value_count: int
    nonfinite_value_count: int
    distinct_value_count: int
    distinct_count_capped: bool
    integer_like_ratio: float
    observed_domain: ObservedDomainV1
    transition_count_by_file: tuple[tuple[str, int], ...]
    nonconstant_by_file: tuple[tuple[str, bool], ...]
    one_step_robust_variation_scale: float | None
    value_domain_values_included: bool = False
    schema_version: str = SCHEMA_VERSION
    artifact_type: str = "hai_variable_domain_diagnostic_v1"

    def __post_init__(self) -> None:
        counts = (
            self.total_value_count,
            self.finite_value_count,
            self.missing_value_count,
            self.nonfinite_value_count,
            self.distinct_value_count,
        )
        if min(counts) < 0:
            raise HAIFeasibilityError("domain diagnostic counts must be non-negative")
        if self.total_value_count != (
            self.finite_value_count + self.missing_value_count + self.nonfinite_value_count
        ):
            raise HAIFeasibilityError("domain diagnostic value counts are inconsistent")
        if not 0.0 <= self.integer_like_ratio <= 1.0:
            raise HAIFeasibilityError("integer_like_ratio must be in [0, 1]")
        if self.one_step_robust_variation_scale is not None:
            _finite(self.one_step_robust_variation_scale, "variation scale")
            if self.one_step_robust_variation_scale <= 0:
                raise HAIFeasibilityError("variation scale must be positive")
        if self.value_domain_values_included:
            raise HAIFeasibilityError("public diagnostic cannot contain domain values")

    def _content_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "artifact_type": self.artifact_type,
            "variable_name": self.variable_name,
            "process_id": self.process_id,
            "total_value_count": self.total_value_count,
            "finite_value_count": self.finite_value_count,
            "missing_value_count": self.missing_value_count,
            "nonfinite_value_count": self.nonfinite_value_count,
            "distinct_value_count": self.distinct_value_count,
            "distinct_count_capped": self.distinct_count_capped,
            "integer_like_ratio": self.integer_like_ratio,
            "observed_domain": self.observed_domain.value,
            "transition_count_by_file": [
                {"relative_path": name, "count": count}
                for name, count in self.transition_count_by_file
            ],
            "nonconstant_by_file": [
                {"relative_path": name, "nonconstant": status}
                for name, status in self.nonconstant_by_file
            ],
            "one_step_robust_variation_scale": self.one_step_robust_variation_scale,
            "value_domain_values_included": self.value_domain_values_included,
        }

    @property
    def artifact_hash(self) -> str:
        return canonical_self_hash(self._content_dict())

    def to_dict(self) -> dict[str, Any]:
        return _artifact_dict(self._content_dict())


@dataclass(frozen=True)
class HAIDelayedResponseScreeningRecordV1:
    screening_id: str
    process_id: str
    source_variable: str
    target_variable: str
    destination_state_hash: str
    selected_horizon_seconds: int
    selected_direction: ResponseDirectionV1
    total_trigger_count: int
    isolated_trigger_count: int
    isolation_ratio: float
    usable_trigger_count: int
    right_censored_count: int
    median_delta: float
    directional_consistency: float
    robust_effect_ratio: float
    train1_isolated_count: int
    train2_isolated_count: int
    train1_directional_consistency: float
    train2_directional_consistency: float
    fit_supported: bool
    calibration_isolated_count: int
    calibration_directional_consistency: float
    calibration_robust_effect_ratio: float
    calibration_confirmed: bool
    readiness: str
    raw_values_included: bool = False
    trigger_timestamps_included: bool = False
    schema_version: str = SCHEMA_VERSION
    artifact_type: str = "hai_delayed_response_screening_v1"

    def __post_init__(self) -> None:
        _require_hash(self.screening_id, "screening_id")
        _require_hash(self.destination_state_hash, "destination_state_hash")
        if self.selected_horizon_seconds not in FIXED_HORIZONS:
            raise HAIFeasibilityError("screening horizon is outside the frozen grid")
        for value in (
            self.total_trigger_count,
            self.isolated_trigger_count,
            self.usable_trigger_count,
            self.right_censored_count,
            self.train1_isolated_count,
            self.train2_isolated_count,
            self.calibration_isolated_count,
        ):
            if value < 0:
                raise HAIFeasibilityError("screening counts must be non-negative")
        for value in (
            self.isolation_ratio,
            self.directional_consistency,
            self.train1_directional_consistency,
            self.train2_directional_consistency,
            self.calibration_directional_consistency,
        ):
            if not 0.0 <= value <= 1.0:
                raise HAIFeasibilityError("screening proportion must be in [0, 1]")
        for value in (
            self.median_delta,
            self.robust_effect_ratio,
            self.calibration_robust_effect_ratio,
        ):
            _finite(value, "screening metric")
        if self.raw_values_included or self.trigger_timestamps_included:
            raise HAIFeasibilityError("public screening records cannot contain raw evidence")
        if self.readiness not in {
            "canonical_increase_ready",
            "future_decrease_family_candidate",
            "unsupported_or_unstable",
        }:
            raise HAIFeasibilityError("screening readiness is invalid")

    def _content_dict(self) -> dict[str, Any]:
        return {
            key: (value.value if isinstance(value, Enum) else value)
            for key, value in self.__dict__.items()
        }

    @property
    def artifact_hash(self) -> str:
        return canonical_self_hash(self._content_dict())

    def to_dict(self) -> dict[str, Any]:
        return _artifact_dict(self._content_dict())


@dataclass(frozen=True)
class HAIProcessFeasibilityRecordV1:
    process_id: str
    process_name: str
    process_feature_count: int
    metadata_reviewed_count: int
    metadata_unresolved_count: int
    eligible_source_variable_count: int
    eligible_source_transition_count: int
    eligible_continuous_target_count: int
    screened_pair_count: int
    fit_supported_pair_count: int
    calibration_confirmed_pair_count: int
    canonical_increase_ready_pair_count: int
    future_decrease_pair_count: int
    distinct_confirmed_source_count: int
    distinct_confirmed_target_count: int
    fit_to_calibration_transfer_rate: float
    median_fit_isolated_trigger_count: float
    median_calibration_isolated_trigger_count: float
    median_isolation_ratio: float
    missing_or_nonfinite_rate: float
    official_graph_reference_available: bool
    manual_metadata_coverage: float
    boundary_violation_count: int
    candidate_fit_files: tuple[str, ...]
    calibration_file: str
    normal_guard_values_accessed: bool
    feasibility_gate_passed: bool
    private_screening_ledger_hash: str
    claim_boundary: str
    schema_version: str = SCHEMA_VERSION
    artifact_type: str = "hai_process_feasibility_v1"

    def __post_init__(self) -> None:
        if self.process_id not in PROCESS_NAMES or self.process_name != PROCESS_NAMES[self.process_id]:
            raise HAIFeasibilityError("process feasibility identity is invalid")
        _require_hash(self.private_screening_ledger_hash, "private_screening_ledger_hash")
        for value in (
            self.fit_to_calibration_transfer_rate,
            self.median_isolation_ratio,
            self.missing_or_nonfinite_rate,
            self.manual_metadata_coverage,
        ):
            if not 0.0 <= value <= 1.0:
                raise HAIFeasibilityError("process proportion must be in [0, 1]")
        if self.normal_guard_values_accessed:
            raise HAIFeasibilityError("normal guard feature values cannot be accessed")
        if self.claim_boundary != "normal_only_feasibility_not_causal_or_performance_evidence":
            raise HAIFeasibilityError("process claim boundary is invalid")

    def _content_dict(self) -> dict[str, Any]:
        content = dict(self.__dict__)
        content["candidate_fit_files"] = list(self.candidate_fit_files)
        return content

    @property
    def artifact_hash(self) -> str:
        return canonical_self_hash(self._content_dict())

    def to_dict(self) -> dict[str, Any]:
        return _artifact_dict(self._content_dict())


@dataclass(frozen=True)
class HAIProcessSelectionResultV1:
    selection_status: str
    selected_process_id: str | None
    excluded_process_id: str | None
    selection_policy_id: str
    selection_policy_hash: str
    p1_feasibility_report_hash: str
    p3_feasibility_report_hash: str
    selection_reason: str
    pareto_comparison: Mapping[str, Any]
    official_graph_used_for_scoring: bool
    attack_information_used: bool
    schema_version: str = SCHEMA_VERSION
    artifact_type: str = "hai_process_selection_result_v1"

    def __post_init__(self) -> None:
        if self.selection_status not in {
            "selected",
            "blocked_no_feasible_delayed_response_process",
            "blocked_process_selection_indeterminate",
        }:
            raise HAIFeasibilityError("selection status is invalid")
        for value in (
            self.selection_policy_hash,
            self.p1_feasibility_report_hash,
            self.p3_feasibility_report_hash,
        ):
            _require_hash(value, "selection hash")
        if self.selection_status == "selected":
            if {self.selected_process_id, self.excluded_process_id} != {"P1", "P3"}:
                raise HAIFeasibilityError("selected result must identify P1 and P3")
        elif self.selected_process_id is not None or self.excluded_process_id is not None:
            raise HAIFeasibilityError("blocked selection cannot identify a process")
        if self.official_graph_used_for_scoring or self.attack_information_used:
            raise HAIFeasibilityError("selection used prohibited evidence")

    def _content_dict(self) -> dict[str, Any]:
        content = dict(self.__dict__)
        content["pareto_comparison"] = json.loads(canonical_json(self.pareto_comparison))
        return content

    @property
    def artifact_hash(self) -> str:
        return canonical_self_hash(self._content_dict())

    def to_dict(self) -> dict[str, Any]:
        return _artifact_dict(self._content_dict())


@dataclass(frozen=True)
class HAIProcessFreezeV1:
    dataset_manifest_id: str
    selected_process_id: str
    selected_process_name: str
    excluded_process_id: str
    selection_policy_id: str
    selection_policy_hash: str
    selected_process_feasibility_report_hash: str
    excluded_process_feasibility_report_hash: str
    metadata_registry_hash: str
    private_screening_ledger_hash: str
    normal_candidate_fit_split_id: str
    normal_relation_calibration_split_id: str
    normal_guard_split_id: str
    canonical_rule_view_id: str
    candidate_learning_view_id: str
    gdn_view_status: str
    selection_status: str
    claim_boundary: str
    creation_metadata: CreationMetadataV2
    schema_version: str = SCHEMA_VERSION
    artifact_type: str = "hai_process_freeze_v1"

    def __post_init__(self) -> None:
        if self.selected_process_id not in PROCESS_NAMES:
            raise HAIFeasibilityError("process freeze selected process is invalid")
        if self.selected_process_name != PROCESS_NAMES[self.selected_process_id]:
            raise HAIFeasibilityError("process freeze name is invalid")
        if {self.selected_process_id, self.excluded_process_id} != {"P1", "P3"}:
            raise HAIFeasibilityError("process freeze must bind P1 and P3")
        for name, value in self.__dict__.items():
            if name.endswith("_hash") or name.endswith("_id") and name not in {
                "selected_process_id",
                "excluded_process_id",
                "selection_policy_id",
            }:
                _require_hash(str(value), name)
        if self.gdn_view_status != "pending_production_backend":
            raise HAIFeasibilityError("GDN view must remain pending")
        if self.selection_status != "passed_hai_2305_single_process_freeze":
            raise HAIFeasibilityError("process freeze status is invalid")
        if self.claim_boundary != "single_process_feasibility_freeze_not_performance_evidence":
            raise HAIFeasibilityError("process freeze claim boundary is invalid")

    def _content_dict(self) -> dict[str, Any]:
        content = dict(self.__dict__)
        content["creation_metadata"] = self.creation_metadata.to_dict()
        return content

    @property
    def artifact_hash(self) -> str:
        return canonical_self_hash(self._content_dict())

    def to_dict(self) -> dict[str, Any]:
        return _artifact_dict(self._content_dict())


@dataclass(frozen=True)
class HAIGDNViewReadinessV1:
    selected_process_id: str
    production_backend: str
    downsampling: str
    model_training: str
    candidate_mask: str
    authoritative_gdn_view_created: bool
    claim_boundary: str
    schema_version: str = SCHEMA_VERSION
    artifact_type: str = "hai_gdn_view_readiness_v1"

    def __post_init__(self) -> None:
        if self.selected_process_id not in PROCESS_NAMES:
            raise HAIFeasibilityError("GDN readiness process is invalid")
        if (
            self.production_backend != "unresolved"
            or self.downsampling != "not_approved"
            or self.model_training != "not_authorized"
            or self.candidate_mask != "required_in_future"
            or self.authoritative_gdn_view_created
        ):
            raise HAIFeasibilityError("GDN readiness exceeds TASK-039B authority")
        if self.claim_boundary != "readiness_plan_only_not_model_evidence":
            raise HAIFeasibilityError("GDN readiness claim boundary is invalid")

    def _content_dict(self) -> dict[str, Any]:
        return dict(self.__dict__)

    @property
    def artifact_hash(self) -> str:
        return canonical_self_hash(self._content_dict())

    def to_dict(self) -> dict[str, Any]:
        return _artifact_dict(self._content_dict())


@dataclass(frozen=True)
class TASK039BDataAccessEntryV1:
    relative_path: str
    purpose: str
    feature_values_accessed: bool
    process_scope: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "relative_path": self.relative_path,
            "purpose": self.purpose,
            "feature_values_accessed": self.feature_values_accessed,
            "process_scope": list(self.process_scope),
        }


@dataclass(frozen=True)
class TASK039BDataAccessAuditV1:
    entries: tuple[TASK039BDataAccessEntryV1, ...]
    prohibited_data_access_count: int
    normal_guard_feature_values_accessed: bool
    test_file_accessed: bool
    label_file_accessed: bool
    summary_file_accessed: bool
    private_custody_accessed: bool
    allowed_process_scopes: tuple[str, ...]
    schema_version: str = SCHEMA_VERSION
    artifact_type: str = "task039b_data_access_audit_v1"

    def __post_init__(self) -> None:
        if self.prohibited_data_access_count != 0:
            raise TASK039BDataAccessError("prohibited data access was recorded")
        if any(
            (
                self.normal_guard_feature_values_accessed,
                self.test_file_accessed,
                self.label_file_accessed,
                self.summary_file_accessed,
                self.private_custody_accessed,
            )
        ):
            raise TASK039BDataAccessError("TASK-039B access boundary was violated")
        if self.allowed_process_scopes != ("P1", "P3"):
            raise TASK039BDataAccessError("allowed process scopes must be P1 and P3")

    def _content_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "artifact_type": self.artifact_type,
            "entries": [item.to_dict() for item in self.entries],
            "prohibited_data_access_count": self.prohibited_data_access_count,
            "normal_guard_feature_values_accessed": self.normal_guard_feature_values_accessed,
            "test_file_accessed": self.test_file_accessed,
            "label_file_accessed": self.label_file_accessed,
            "summary_file_accessed": self.summary_file_accessed,
            "private_custody_accessed": self.private_custody_accessed,
            "allowed_process_scopes": list(self.allowed_process_scopes),
        }

    @property
    def artifact_hash(self) -> str:
        return canonical_self_hash(self._content_dict())

    def to_dict(self) -> dict[str, Any]:
        return _artifact_dict(self._content_dict())


class TASK039BDataAccessLedger:
    """Mutable execution ledger whose frozen projection is a public artifact."""

    def __init__(self) -> None:
        self._entries: list[TASK039BDataAccessEntryV1] = []

    def authorize(
        self,
        relative_path: str,
        *,
        purpose: str,
        feature_values_accessed: bool,
        process_scope: Sequence[str] = (),
    ) -> None:
        normalized = PurePosixPath(relative_path).as_posix()
        lower = normalized.lower()
        if normalized not in APPROVED_TRAIN_FILES or any(
            token in lower for token in PROHIBITED_PATH_TOKENS
        ):
            raise TASK039BDataAccessError(
                f"{TASK039BDataAccessError.issue_code}: path is not authorized"
            )
        scopes = tuple(process_scope)
        if any(item not in PROCESS_NAMES for item in scopes):
            raise TASK039BDataAccessError(
                f"{TASK039BDataAccessError.issue_code}: process scope is not authorized"
            )
        if normalized.endswith("hai-train4.csv") and feature_values_accessed:
            raise TASK039BDataAccessError(
                f"{TASK039BDataAccessError.issue_code}: normal guard values are prohibited"
            )
        if feature_values_accessed and not scopes:
            raise TASK039BDataAccessError(
                f"{TASK039BDataAccessError.issue_code}: value access requires a process scope"
            )
        self._entries.append(
            TASK039BDataAccessEntryV1(
                relative_path=normalized,
                purpose=purpose,
                feature_values_accessed=feature_values_accessed,
                process_scope=scopes,
            )
        )

    def freeze(self) -> TASK039BDataAccessAuditV1:
        return TASK039BDataAccessAuditV1(
            entries=tuple(self._entries),
            prohibited_data_access_count=0,
            normal_guard_feature_values_accessed=False,
            test_file_accessed=False,
            label_file_accessed=False,
            summary_file_accessed=False,
            private_custody_accessed=False,
            allowed_process_scopes=("P1", "P3"),
        )


@dataclass(frozen=True)
class DomainComputationV1:
    """Private in-memory domain result used to build redacted public records."""

    diagnostic: HAIVariableDomainDiagnosticV1
    distinct_values: tuple[float, ...]


@dataclass(frozen=True)
class HorizonScreeningSummaryV1:
    horizon_seconds: int
    usable_trigger_count: int
    right_censored_count: int
    median_delta: float
    positive_consistency: float
    negative_consistency: float
    robust_effect_ratio: float


@dataclass(frozen=True)
class ProcessScreeningResultV1:
    public_records: tuple[HAIDelayedResponseScreeningRecordV1, ...]
    private_ledger: Mapping[str, Any]


def _median_or_zero(values: Sequence[float]) -> float:
    return float(median(values)) if values else 0.0


def robust_noise_scale(
    file_values: Sequence[Sequence[float]], *, numeric_epsilon: float = 1e-12
) -> float:
    """Return 1.4826 times MAD of within-file one-step differences."""

    if numeric_epsilon <= 0 or not math.isfinite(numeric_epsilon):
        raise HAIFeasibilityError("numeric_epsilon must be finite and positive")
    differences: list[float] = []
    for values in file_values:
        for before, after in zip(values, values[1:]):
            if math.isfinite(before) and math.isfinite(after):
                differences.append(float(after - before))
    if not differences:
        return float(numeric_epsilon)
    center = float(median(differences))
    mad = float(median(abs(value - center) for value in differences))
    return max(1.4826 * mad, float(numeric_epsilon))


def classify_observed_domain(
    values: Sequence[float], *, discrete_cardinality_limit: int = 16
) -> tuple[ObservedDomainV1, tuple[float, ...], float]:
    """Classify value domain without assigning physical semantics."""

    finite = [float(item) for item in values if math.isfinite(float(item))]
    if not finite:
        return ObservedDomainV1.UNKNOWN, (), 0.0
    distinct = tuple(sorted(set(finite)))
    integer_like_ratio = sum(abs(item - round(item)) <= 1e-9 for item in finite) / len(
        finite
    )
    if len(distinct) == 1:
        domain = ObservedDomainV1.CONSTANT
    elif len(distinct) == 2 and integer_like_ratio >= 0.999:
        domain = ObservedDomainV1.BINARY
    elif len(distinct) <= discrete_cardinality_limit and integer_like_ratio >= 0.999:
        domain = ObservedDomainV1.DISCRETE
    else:
        domain = ObservedDomainV1.CONTINUOUS
    return domain, distinct, float(integer_like_ratio)


def build_domain_diagnostic(
    *,
    variable_name: str,
    process_id: str,
    values_by_file: Mapping[str, Sequence[float | None]],
    candidate_fit_files: Sequence[str],
    distinct_count_cap: int = 4096,
) -> DomainComputationV1:
    """Build aggregate domain diagnostics without retaining values publicly."""

    if process_id not in PROCESS_NAMES or not variable_name.startswith(f"{process_id}_"):
        raise HAIFeasibilityError("domain diagnostic process scope is invalid")
    finite_values: list[float] = []
    total = missing = nonfinite = 0
    transitions: list[tuple[str, int]] = []
    nonconstant: list[tuple[str, bool]] = []
    fit_numeric: list[list[float]] = []
    for relative_path, raw_values in values_by_file.items():
        current: list[float] = []
        for raw in raw_values:
            total += 1
            if raw is None:
                missing += 1
                continue
            value = float(raw)
            if not math.isfinite(value):
                nonfinite += 1
                continue
            current.append(value)
            finite_values.append(value)
        transitions.append(
            (relative_path, sum(before != after for before, after in zip(current, current[1:])))
        )
        nonconstant.append((relative_path, len(set(current)) > 1))
        if relative_path in candidate_fit_files:
            fit_numeric.append(current)
    domain, distinct, integer_ratio = classify_observed_domain(finite_values)
    scale = (
        robust_noise_scale(fit_numeric)
        if domain is ObservedDomainV1.CONTINUOUS
        else None
    )
    return DomainComputationV1(
        diagnostic=HAIVariableDomainDiagnosticV1(
            variable_name=variable_name,
            process_id=process_id,
            total_value_count=total,
            finite_value_count=len(finite_values),
            missing_value_count=missing,
            nonfinite_value_count=nonfinite,
            distinct_value_count=min(len(distinct), distinct_count_cap),
            distinct_count_capped=len(distinct) > distinct_count_cap,
            integer_like_ratio=integer_ratio,
            observed_domain=domain,
            transition_count_by_file=tuple(transitions),
            nonconstant_by_file=tuple(nonconstant),
            one_step_robust_variation_scale=scale,
        ),
        distinct_values=(distinct if len(distinct) <= distinct_count_cap else ()),
    )


def infer_semantic_role(
    variable_name: str, description: str
) -> tuple[SemanticRoleV2, str, str]:
    """Infer a bounded metadata role from an official description and tag pattern.

    Data behavior is deliberately absent from this function. A caller must still
    provide a manual page reference before the result can be marked reviewed.
    """

    text = f"{variable_name} {description}".lower()
    if re.search(r"\b(set[ -]?point|setpoint)\b|(?:^|_)sp(?:_|$)", text):
        return SemanticRoleV2.SETPOINT, "setpoint", "setpoint"
    if re.search(r"\b(alarm|trip|warning|status)\b", text):
        return SemanticRoleV2.STATUS_OR_ALARM, "status or alarm", "state"
    tag = variable_name.upper()
    if re.search(r"\b(command|control command|output command)\b", text) or re.search(
        r"(?:FCV|LCV|PCV|PP|PUMP|MV)\d*[A-Z]*D$", tag
    ):
        return SemanticRoleV2.CONTROL_COMMAND, "control command", "state"
    if re.search(r"\b(feedback|position feedback|run feedback)\b", text) or re.search(
        r"(?:FCV|LCV|PCV|PP|PUMP|MV)\d*[A-Z]*(?:R|Z)$", tag
    ):
        return SemanticRoleV2.ACTUATOR_FEEDBACK, "actuator feedback", "state"
    sensor_patterns = (
        r"\b(sensor|transmitter|measurement|measured)\b",
        r"\b(flow|level|pressure|temperature|conductivity|ph|turbidity|volume)\b",
        r"(?:^|_)(?:ai|ft|fit|lt|lit|pt|pit|tt|tit|ait|cit|wit)\d*",
    )
    if any(re.search(pattern, text) for pattern in sensor_patterns):
        return SemanticRoleV2.PROCESS_SENSOR, "process sensor", "unverified"
    if re.search(r"\b(valve|pump|motor|heater|switch|solenoid|actuator)\b", text):
        return SemanticRoleV2.ACTUATOR_STATE, "actuator state", "state"
    if re.search(r"\b(calculated|derived|internal|diagnostic)\b", text):
        return SemanticRoleV2.DERIVED_OR_INTERNAL, "derived or internal", "unverified"
    return SemanticRoleV2.UNKNOWN, "unknown", "unverified"


def build_variable_metadata(
    *,
    variable_name: str,
    process_id: str,
    description: str,
    unit: str,
    subsystem_or_stage: str,
    manual_pages: Sequence[int],
    official_graph_references: Sequence[str],
    domain: HAIVariableDomainDiagnosticV1,
    evidence_record_refs: Sequence[str],
) -> HAIVariableMetadataV2:
    """Combine official metadata and a domain diagnostic under a fixed policy."""

    role, quantity, inferred_unit = infer_semantic_role(variable_name, description)
    pages = tuple(sorted(set(int(item) for item in manual_pages)))
    reviewed = bool(pages and description.strip() and role is not SemanticRoleV2.UNKNOWN)
    confidence = (
        MetadataConfidenceV1.HIGH
        if reviewed and unit.strip()
        else MetadataConfidenceV1.MEDIUM
        if reviewed
        else MetadataConfidenceV1.INSUFFICIENT
    )
    review_status = (
        MetadataReviewStatusV1.REVIEWED
        if reviewed
        else MetadataReviewStatusV1.UNRESOLVED
    )
    source_eligible = (
        reviewed
        and role
        in {
            SemanticRoleV2.CONTROL_COMMAND,
            SemanticRoleV2.ACTUATOR_STATE,
            SemanticRoleV2.ACTUATOR_FEEDBACK,
        }
        and domain.observed_domain
        in {ObservedDomainV1.BINARY, ObservedDomainV1.DISCRETE}
    )
    target_eligible = (
        reviewed
        and role is SemanticRoleV2.PROCESS_SENSOR
        and domain.observed_domain is ObservedDomainV1.CONTINUOUS
        and all(status for _, status in domain.nonconstant_by_file)
    )
    exclusions: list[str] = []
    if role is SemanticRoleV2.SETPOINT:
        exclusions.append("setpoint_not_primary_trigger")
    if role in {SemanticRoleV2.STATUS_OR_ALARM, SemanticRoleV2.DERIVED_OR_INTERNAL}:
        exclusions.append("semantic_role_excluded")
    if role is SemanticRoleV2.UNKNOWN or not reviewed:
        exclusions.append("metadata_unresolved")
    if domain.observed_domain is ObservedDomainV1.CONSTANT:
        exclusions.append("constant_signal")
    if role in {
        SemanticRoleV2.CONTROL_COMMAND,
        SemanticRoleV2.ACTUATOR_STATE,
        SemanticRoleV2.ACTUATOR_FEEDBACK,
    } and domain.observed_domain is ObservedDomainV1.CONTINUOUS:
        exclusions.append("continuous_actuator_outside_first_mvp")
    if not source_eligible and not target_eligible and not exclusions:
        exclusions.append("not_eligible_for_first_mvp")
    return HAIVariableMetadataV2(
        variable_name=variable_name,
        process_id=process_id,
        subsystem_or_stage=subsystem_or_stage or "unverified",
        semantic_role=role,
        observed_value_domain=domain.observed_domain,
        physical_quantity_or_device=quantity,
        unit=unit.strip() or inferred_unit,
        description_summary=" ".join(description.split())[:320] or "unresolved",
        manual_reference=pages,
        official_graph_references=tuple(sorted(set(official_graph_references))),
        name_pattern_evidence="bounded_tag_and_manual_description_pattern",
        data_domain_evidence="aggregate_normal_candidate_fit_and_calibration_domain_only",
        metadata_confidence=confidence,
        review_status=review_status,
        source_eligibility=source_eligible,
        target_eligibility=target_eligible,
        exclusion_reasons=tuple(sorted(set(exclusions))),
        evidence_record_refs=tuple(evidence_record_refs),
    )


def transition_indices(values: Sequence[float], destination_state: float) -> tuple[int, ...]:
    """Return indexes entering one destination state."""

    return tuple(
        index
        for index in range(1, len(values))
        if values[index] == destination_state and values[index - 1] != destination_state
    )


def isolated_transition_indices(
    *,
    source_variable: str,
    source_values: Mapping[str, Sequence[float]],
    destination_state: float,
    radius_seconds: int = 2,
) -> tuple[int, ...]:
    """Filter source transitions when another eligible source changes nearby."""

    if source_variable not in source_values or radius_seconds < 0:
        raise HAIFeasibilityError("isolated transition inputs are invalid")
    base = transition_indices(source_values[source_variable], destination_state)
    other_changes: set[int] = set()
    expected_length = len(source_values[source_variable])
    for name, values in source_values.items():
        if len(values) != expected_length:
            raise HAIFeasibilityError("source series lengths must agree within a file")
        if name == source_variable:
            continue
        other_changes.update(
            index
            for index in range(1, len(values))
            if values[index] != values[index - 1]
        )
    return tuple(
        index
        for index in base
        if not any(
            candidate in other_changes
            for candidate in range(
                max(1, index - radius_seconds),
                min(expected_length - 1, index + radius_seconds) + 1,
            )
        )
    )


def screen_horizon(
    *,
    trigger_indices: Sequence[int],
    target_values: Sequence[float],
    horizon_seconds: int,
    noise_scale: float,
) -> HorizonScreeningSummaryV1:
    """Screen one target at one fixed horizon without crossing a file boundary."""

    if horizon_seconds not in FIXED_HORIZONS:
        raise HAIFeasibilityError("horizon is outside the frozen grid")
    if noise_scale <= 0 or not math.isfinite(noise_scale):
        raise HAIFeasibilityError("noise scale must be finite and positive")
    deltas: list[float] = []
    right_censored = 0
    for index in trigger_indices:
        if index <= 0 or index + horizon_seconds >= len(target_values):
            right_censored += 1
            continue
        baseline = float(target_values[index - 1])
        future = float(target_values[index + horizon_seconds])
        if not math.isfinite(baseline) or not math.isfinite(future):
            continue
        deltas.append(future - baseline)
    count = len(deltas)
    median_delta = _median_or_zero(deltas)
    positive = sum(value > noise_scale for value in deltas) / count if count else 0.0
    negative = sum(value < -noise_scale for value in deltas) / count if count else 0.0
    return HorizonScreeningSummaryV1(
        horizon_seconds=horizon_seconds,
        usable_trigger_count=count,
        right_censored_count=right_censored,
        median_delta=median_delta,
        positive_consistency=positive,
        negative_consistency=negative,
        robust_effect_ratio=abs(median_delta) / noise_scale,
    )


def _direction_for(summary: HorizonScreeningSummaryV1) -> ResponseDirectionV1:
    if summary.positive_consistency >= summary.negative_consistency:
        return ResponseDirectionV1.INCREASE
    return ResponseDirectionV1.DECREASE


def choose_fit_horizon(
    summaries: Sequence[HorizonScreeningSummaryV1],
) -> HorizonScreeningSummaryV1:
    """Apply the frozen consistency/effect/shortest-horizon ordering."""

    if {item.horizon_seconds for item in summaries} != set(FIXED_HORIZONS):
        raise HAIFeasibilityError("all and only fixed horizons are required")
    return sorted(
        summaries,
        key=lambda item: (
            -max(item.positive_consistency, item.negative_consistency),
            -item.robust_effect_ratio,
            item.horizon_seconds,
        ),
    )[0]


def _combine_horizon_summaries(
    per_file: Sequence[HorizonScreeningSummaryV1], *, noise_scale: float
) -> HorizonScreeningSummaryV1:
    """Combine file summaries exactly from their sufficient aggregate counts.

    Median deltas cannot be reconstructed from per-file medians, so callers use
    this helper only for public summaries after passing exact pooled deltas via
    ``screen_horizon``. It remains available for tests of count consistency.
    """

    if not per_file:
        raise HAIFeasibilityError("at least one horizon summary is required")
    horizon = per_file[0].horizon_seconds
    if any(item.horizon_seconds != horizon for item in per_file):
        raise HAIFeasibilityError("combined summaries must share a horizon")
    count = sum(item.usable_trigger_count for item in per_file)
    positive = (
        sum(item.positive_consistency * item.usable_trigger_count for item in per_file)
        / count
        if count
        else 0.0
    )
    negative = (
        sum(item.negative_consistency * item.usable_trigger_count for item in per_file)
        / count
        if count
        else 0.0
    )
    median_delta = _median_or_zero([item.median_delta for item in per_file])
    return HorizonScreeningSummaryV1(
        horizon_seconds=horizon,
        usable_trigger_count=count,
        right_censored_count=sum(item.right_censored_count for item in per_file),
        median_delta=median_delta,
        positive_consistency=positive,
        negative_consistency=negative,
        robust_effect_ratio=abs(median_delta) / noise_scale,
    )


def _pooled_horizon(
    *,
    trigger_indices_by_file: Mapping[str, Sequence[int]],
    target_values_by_file: Mapping[str, Sequence[float]],
    files: Sequence[str],
    horizon: int,
    noise_scale: float,
) -> HorizonScreeningSummaryV1:
    deltas: list[float] = []
    right_censored = 0
    for name in files:
        values = target_values_by_file[name]
        for index in trigger_indices_by_file[name]:
            if index <= 0 or index + horizon >= len(values):
                right_censored += 1
                continue
            before = float(values[index - 1])
            after = float(values[index + horizon])
            if math.isfinite(before) and math.isfinite(after):
                deltas.append(after - before)
    count = len(deltas)
    med = _median_or_zero(deltas)
    return HorizonScreeningSummaryV1(
        horizon_seconds=horizon,
        usable_trigger_count=count,
        right_censored_count=right_censored,
        median_delta=med,
        positive_consistency=(
            sum(value > noise_scale for value in deltas) / count if count else 0.0
        ),
        negative_consistency=(
            sum(value < -noise_scale for value in deltas) / count if count else 0.0
        ),
        robust_effect_ratio=abs(med) / noise_scale,
    )


def screen_delayed_response_pair(
    *,
    process_id: str,
    source_variable: str,
    target_variable: str,
    destination_state: float,
    source_values_by_file: Mapping[str, Mapping[str, Sequence[float]]],
    target_values_by_file: Mapping[str, Sequence[float]],
    noise_scale: float,
    fit_files: tuple[str, str],
    calibration_file: str,
    isolation_radius_seconds: int = 2,
    isolated_indices_by_file: Mapping[str, Sequence[int]] | None = None,
    total_trigger_counts_by_file: Mapping[str, int] | None = None,
) -> tuple[HAIDelayedResponseScreeningRecordV1, Mapping[str, Any]]:
    """Screen one documented source transition against one continuous target."""

    required_files = (*fit_files, calibration_file)
    if any(name not in source_values_by_file or name not in target_values_by_file for name in required_files):
        raise HAIFeasibilityError("screening files are incomplete")
    isolated: dict[str, tuple[int, ...]] = {}
    total_counts: dict[str, int] = {}
    for name in required_files:
        sources = source_values_by_file[name]
        if isolated_indices_by_file is None:
            isolated[name] = isolated_transition_indices(
                source_variable=source_variable,
                source_values=sources,
                destination_state=destination_state,
                radius_seconds=isolation_radius_seconds,
            )
        else:
            if name not in isolated_indices_by_file:
                raise HAIFeasibilityError("precomputed isolated trigger map is incomplete")
            isolated[name] = tuple(int(item) for item in isolated_indices_by_file[name])
        if total_trigger_counts_by_file is None:
            total_counts[name] = len(
                transition_indices(sources[source_variable], destination_state)
            )
        else:
            if name not in total_trigger_counts_by_file:
                raise HAIFeasibilityError("precomputed total trigger map is incomplete")
            total_counts[name] = int(total_trigger_counts_by_file[name])
    fit_summaries = [
        _pooled_horizon(
            trigger_indices_by_file=isolated,
            target_values_by_file=target_values_by_file,
            files=fit_files,
            horizon=horizon,
            noise_scale=noise_scale,
        )
        for horizon in FIXED_HORIZONS
    ]
    selected = choose_fit_horizon(fit_summaries)
    direction = _direction_for(selected)
    file_summaries = {
        name: screen_horizon(
            trigger_indices=isolated[name],
            target_values=target_values_by_file[name],
            horizon_seconds=selected.horizon_seconds,
            noise_scale=noise_scale,
        )
        for name in required_files
    }

    def consistency(item: HorizonScreeningSummaryV1) -> float:
        return (
            item.positive_consistency
            if direction is ResponseDirectionV1.INCREASE
            else item.negative_consistency
        )

    fit_consistency = consistency(selected)
    per_file_directions = tuple(_direction_for(file_summaries[name]) for name in fit_files)
    fit_supported = (
        sum(len(isolated[name]) for name in fit_files) >= 20
        and all(len(isolated[name]) >= 5 for name in fit_files)
        and fit_consistency >= 0.70
        and all(consistency(file_summaries[name]) >= 0.60 for name in fit_files)
        and selected.robust_effect_ratio >= 2.0
        and per_file_directions == (direction, direction)
    )
    calibration = file_summaries[calibration_file]
    calibration_consistency = consistency(calibration)
    calibration_confirmed = (
        fit_supported
        and len(isolated[calibration_file]) >= 5
        and _direction_for(calibration) is direction
        and calibration_consistency >= 0.60
        and calibration.robust_effect_ratio >= 1.0
    )
    readiness = (
        "canonical_increase_ready"
        if calibration_confirmed and direction is ResponseDirectionV1.INCREASE
        else "future_decrease_family_candidate"
        if calibration_confirmed
        else "unsupported_or_unstable"
    )
    destination_state_hash = sha256(
        canonical_json({"destination_state": float(destination_state)}).encode("utf-8")
    ).hexdigest()
    screening_id = sha256(
        canonical_json(
            {
                "process_id": process_id,
                "source_variable": source_variable,
                "target_variable": target_variable,
                "destination_state_hash": destination_state_hash,
            }
        ).encode("utf-8")
    ).hexdigest()
    total = sum(total_counts.values())
    isolated_total = sum(len(value) for value in isolated.values())
    record = HAIDelayedResponseScreeningRecordV1(
        screening_id=screening_id,
        process_id=process_id,
        source_variable=source_variable,
        target_variable=target_variable,
        destination_state_hash=destination_state_hash,
        selected_horizon_seconds=selected.horizon_seconds,
        selected_direction=direction,
        total_trigger_count=total,
        isolated_trigger_count=isolated_total,
        isolation_ratio=isolated_total / total if total else 0.0,
        usable_trigger_count=selected.usable_trigger_count,
        right_censored_count=selected.right_censored_count,
        median_delta=selected.median_delta,
        directional_consistency=fit_consistency,
        robust_effect_ratio=selected.robust_effect_ratio,
        train1_isolated_count=len(isolated[fit_files[0]]),
        train2_isolated_count=len(isolated[fit_files[1]]),
        train1_directional_consistency=consistency(file_summaries[fit_files[0]]),
        train2_directional_consistency=consistency(file_summaries[fit_files[1]]),
        fit_supported=fit_supported,
        calibration_isolated_count=len(isolated[calibration_file]),
        calibration_directional_consistency=calibration_consistency,
        calibration_robust_effect_ratio=calibration.robust_effect_ratio,
        calibration_confirmed=calibration_confirmed,
        readiness=readiness,
    )
    private = {
        "screening_id": screening_id,
        "destination_state": float(destination_state),
        "fixed_horizon_summaries": [item.__dict__ for item in fit_summaries],
        "per_file_selected_horizon": {
            name: item.__dict__ for name, item in file_summaries.items()
        },
    }
    return record, private


def build_process_feasibility(
    *,
    process_id: str,
    metadata: Sequence[HAIVariableMetadataV2],
    diagnostics: Sequence[HAIVariableDomainDiagnosticV1],
    screenings: Sequence[HAIDelayedResponseScreeningRecordV1],
    private_screening_ledger_hash: str,
    official_graph_reference_available: bool,
    boundary_violation_count: int = 0,
) -> HAIProcessFeasibilityRecordV1:
    """Aggregate process evidence and apply the frozen minimum gate."""

    sources = [item for item in metadata if item.source_eligibility]
    targets = [item for item in metadata if item.target_eligibility]
    confirmed = [item for item in screenings if item.calibration_confirmed]
    increase = [item for item in confirmed if item.readiness == "canonical_increase_ready"]
    decrease = [
        item for item in confirmed if item.readiness == "future_decrease_family_candidate"
    ]
    fit_supported = sum(item.fit_supported for item in screenings)
    transfer = len(confirmed) / fit_supported if fit_supported else 0.0
    total_values = sum(item.total_value_count for item in diagnostics)
    missing_nonfinite = sum(
        item.missing_value_count + item.nonfinite_value_count for item in diagnostics
    )
    reviewed = sum(item.review_status is MetadataReviewStatusV1.REVIEWED for item in metadata)
    transition_count = sum(
        item.distinct_value_count
        for item in diagnostics
        if any(meta.variable_name == item.variable_name for meta in sources)
    )
    confirmed_sources = {item.source_variable for item in confirmed}
    confirmed_targets = {item.target_variable for item in confirmed}
    gate = (
        boundary_violation_count == 0
        and all(
            item.review_status is MetadataReviewStatusV1.REVIEWED
            for item in (*sources, *targets)
        )
        and len(sources) >= 2
        and len(targets) >= 3
        and len(increase) >= 3
        and len(confirmed_sources) >= 2
        and len(confirmed_targets) >= 2
        and transfer >= 0.50
    )
    return HAIProcessFeasibilityRecordV1(
        process_id=process_id,
        process_name=PROCESS_NAMES[process_id],
        process_feature_count=len(metadata),
        metadata_reviewed_count=reviewed,
        metadata_unresolved_count=len(metadata) - reviewed,
        eligible_source_variable_count=len(sources),
        eligible_source_transition_count=transition_count,
        eligible_continuous_target_count=len(targets),
        screened_pair_count=len(screenings),
        fit_supported_pair_count=fit_supported,
        calibration_confirmed_pair_count=len(confirmed),
        canonical_increase_ready_pair_count=len(increase),
        future_decrease_pair_count=len(decrease),
        distinct_confirmed_source_count=len(confirmed_sources),
        distinct_confirmed_target_count=len(confirmed_targets),
        fit_to_calibration_transfer_rate=transfer,
        median_fit_isolated_trigger_count=_median_or_zero(
            [item.train1_isolated_count + item.train2_isolated_count for item in screenings]
        ),
        median_calibration_isolated_trigger_count=_median_or_zero(
            [item.calibration_isolated_count for item in screenings]
        ),
        median_isolation_ratio=_median_or_zero(
            [item.isolation_ratio for item in screenings]
        ),
        missing_or_nonfinite_rate=(missing_nonfinite / total_values if total_values else 0.0),
        official_graph_reference_available=official_graph_reference_available,
        manual_metadata_coverage=reviewed / len(metadata) if metadata else 0.0,
        boundary_violation_count=boundary_violation_count,
        candidate_fit_files=APPROVED_TRAIN_FILES[:2],
        calibration_file=APPROVED_TRAIN_FILES[2],
        normal_guard_values_accessed=False,
        feasibility_gate_passed=gate,
        private_screening_ledger_hash=private_screening_ledger_hash,
        claim_boundary="normal_only_feasibility_not_causal_or_performance_evidence",
    )


def select_process(
    *,
    p1: HAIProcessFeasibilityRecordV1,
    p3: HAIProcessFeasibilityRecordV1,
    selection_policy_id: str,
    selection_policy_hash: str,
) -> HAIProcessSelectionResultV1:
    """Apply eligibility followed by the frozen unweighted Pareto policy."""

    passed = [item for item in (p1, p3) if item.feasibility_gate_passed]
    comparison: dict[str, Any] = {"weighted_score_used": False, "metrics": {}}
    if not passed:
        status = "blocked_no_feasible_delayed_response_process"
        selected = excluded = None
        reason = "neither_process_passed_minimum_gate"
    elif len(passed) == 1:
        status = "selected"
        selected = passed[0].process_id
        excluded = "P3" if selected == "P1" else "P1"
        reason = "exactly_one_process_passed_minimum_gate"
    else:
        maximize = (
            "distinct_confirmed_source_count",
            "distinct_confirmed_target_count",
            "canonical_increase_ready_pair_count",
            "fit_to_calibration_transfer_rate",
            "median_calibration_isolated_trigger_count",
            "manual_metadata_coverage",
        )
        minimize = (
            "metadata_unresolved_ratio",
            "non_isolated_trigger_ratio",
            "missing_or_nonfinite_rate",
        )

        def metrics(item: HAIProcessFeasibilityRecordV1) -> dict[str, float]:
            return {
                **{name: float(getattr(item, name)) for name in maximize},
                "metadata_unresolved_ratio": (
                    item.metadata_unresolved_count / item.process_feature_count
                    if item.process_feature_count
                    else 1.0
                ),
                "non_isolated_trigger_ratio": 1.0 - item.median_isolation_ratio,
                "missing_or_nonfinite_rate": item.missing_or_nonfinite_rate,
            }

        values = {"P1": metrics(p1), "P3": metrics(p3)}
        comparison["metrics"] = values

        def dominates(left: str, right: str) -> bool:
            no_worse = all(values[left][name] >= values[right][name] for name in maximize)
            no_worse = no_worse and all(
                values[left][name] <= values[right][name] for name in minimize
            )
            better = sum(values[left][name] > values[right][name] for name in maximize)
            better += sum(values[left][name] < values[right][name] for name in minimize)
            return no_worse and better >= 2

        p1_dominates = dominates("P1", "P3")
        p3_dominates = dominates("P3", "P1")
        comparison["p1_dominates_p3"] = p1_dominates
        comparison["p3_dominates_p1"] = p3_dominates
        if p1_dominates ^ p3_dominates:
            status = "selected"
            selected = "P1" if p1_dominates else "P3"
            excluded = "P3" if selected == "P1" else "P1"
            reason = "selected_by_frozen_pareto_dominance"
        else:
            status = "blocked_process_selection_indeterminate"
            selected = excluded = None
            reason = "neither_process_uniquely_dominated_under_frozen_policy"
    return HAIProcessSelectionResultV1(
        selection_status=status,
        selected_process_id=selected,
        excluded_process_id=excluded,
        selection_policy_id=selection_policy_id,
        selection_policy_hash=selection_policy_hash,
        p1_feasibility_report_hash=p1.artifact_hash,
        p3_feasibility_report_hash=p3.artifact_hash,
        selection_reason=reason,
        pareto_comparison=comparison,
        official_graph_used_for_scoring=False,
        attack_information_used=False,
    )


def create_process_views(
    *,
    dataset_manifest_id: str,
    process_id: str,
    feature_names: Sequence[str],
    creation_metadata: CreationMetadataV2,
) -> tuple[DataViewManifestV2, DataViewManifestV2]:
    """Create canonical-rule and candidate-learning views for one process."""

    if process_id not in PROCESS_NAMES or not feature_names:
        raise HAIFeasibilityError("process view scope is invalid")
    if any(not name.startswith(f"{process_id}_") for name in feature_names):
        raise HAIFeasibilityError("process view contains an out-of-scope feature")
    feature_hash = sha256(canonical_json({"features": list(feature_names)}).encode()).hexdigest()
    aggregation = AggregationDescriptionV2(
        method="none",
        source_sampling_interval_seconds=1.0,
        output_sampling_interval_seconds=1.0,
        explicit=True,
        description="No aggregation or downsampling; preserve official one-second samples.",
    )
    canonical = DataViewManifestV2(
        view_kind=DataViewKindV2.CANONICAL_RULE,
        source_dataset_manifest_id=dataset_manifest_id,
        process_scope=(process_id,),
        sampling_interval_seconds=1.0,
        preprocessing_config={
            "column_selection": "verified_process_columns_only",
            "numeric_parsing": "deterministic",
            "interpolation": False,
            "downsampling": False,
            "scaling": False,
            "imputation": False,
        },
        aggregation=aggregation,
        feature_order_hash=feature_hash,
        second_level_rule_calibration_allowed=True,
        provenance_status=ProvenanceStatusV2.VERIFIED,
        creation_metadata=creation_metadata,
    )
    candidate = DataViewManifestV2(
        view_kind=DataViewKindV2.CANDIDATE_LEARNING,
        source_dataset_manifest_id=dataset_manifest_id,
        process_scope=(process_id,),
        sampling_interval_seconds=1.0,
        preprocessing_config={
            "normalization": "not_fitted_in_task039b",
            "normalization_fit_role": "normal_candidate_fit_only",
            "interpolation": False,
            "downsampling": False,
            "imputation": False,
        },
        aggregation=aggregation,
        feature_order_hash=feature_hash,
        second_level_rule_calibration_allowed=False,
        provenance_status=ProvenanceStatusV2.VERIFIED,
        creation_metadata=creation_metadata,
    )
    return canonical, candidate


def create_process_split_manifests(
    *,
    dataset_manifest_id: str,
    data_view_id: str,
    process_id: str,
    row_counts: Mapping[str, int],
    creation_metadata: CreationMetadataV2,
    purge_gap_samples: int = 120,
) -> tuple[SplitManifestV2, SplitManifestV2, SplitManifestV2]:
    """Create file-level ranges with explicit purge gaps before windowing."""

    if process_id not in PROCESS_NAMES or set(row_counts) != set(APPROVED_TRAIN_FILES):
        raise HAIFeasibilityError("split input inventory is invalid")
    starts: dict[str, int] = {}
    cursor = 0
    for name in APPROVED_TRAIN_FILES:
        starts[name] = cursor
        cursor += int(row_counts[name]) + purge_gap_samples
    common = dict(
        dataset_manifest_id=dataset_manifest_id,
        data_view_id=data_view_id,
        event_ids=None,
        purge_gap_samples=purge_gap_samples,
        process_scope=(process_id,),
        seed=None,
        provenance_status=ProvenanceStatusV2.VERIFIED,
        sealed_access_status=SealedAccessStatusV2.NOT_APPLICABLE,
        split_before_windowing=True,
        creation_metadata=creation_metadata,
    )
    fit = SplitManifestV2(
        role=SplitRoleV2.NORMAL_CANDIDATE_FIT,
        raw_ranges=tuple(
            RawRangeV2(starts[name], starts[name] + int(row_counts[name]))
            for name in APPROVED_TRAIN_FILES[:2]
        ),
        creation_policy="file_level_train1_train2_before_windowing",
        **common,
    )
    calibration_name = APPROVED_TRAIN_FILES[2]
    calibration = SplitManifestV2(
        role=SplitRoleV2.NORMAL_RELATION_CALIBRATION,
        raw_ranges=(
            RawRangeV2(
                starts[calibration_name], starts[calibration_name] + row_counts[calibration_name]
            ),
        ),
        creation_policy="file_level_train3_before_windowing",
        **common,
    )
    guard_name = APPROVED_TRAIN_FILES[3]
    guard = SplitManifestV2(
        role=SplitRoleV2.NORMAL_GUARD,
        raw_ranges=(
            RawRangeV2(starts[guard_name], starts[guard_name] + row_counts[guard_name]),
        ),
        creation_policy="file_level_train4_reserved_without_feature_value_access",
        **common,
    )
    validate_split_collection_v2(
        (fit, calibration, guard), window_size=61, maximum_required_lag=60
    )
    return fit, calibration, guard


def public_payload_has_prohibited_content(payload: Mapping[str, Any]) -> bool:
    """Conservative public report leak guard for TASK-039B outputs."""

    text = canonical_json(payload).lower()
    prohibited = (
        "trigger_timestamp",
        "attack_start",
        "attack_end",
        "raw_window",
        "raw_sequence",
        "absolute_path",
        "hai-test",
        "label-test",
        "summary_label",
    )
    return any(token in text for token in prohibited)
