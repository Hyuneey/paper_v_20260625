"""Normal-only HAI source-eligibility diagnosis and route-decision contracts.

This module does not evaluate source-target relations. It classifies the frozen
TASK-039B exclusions, summarizes continuous control-source morphology, audits
Rule v1 compatibility, and applies the predeclared route decision order.
"""

from __future__ import annotations

import csv
import math
import statistics
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
from typing import Any, Mapping, Sequence

from paperworks.v6.common import require_sha256, stable_hash_v1


SCHEMA_VERSION = "1.0.0"
TASK039B_RESULT_COMMIT = "6543ca5b88779262d01c5e0c24e51216dd0835e9"
TASK039B_SELECTION_HASH = "544ff2f3f06e3cfc0b683509ee0ef7aa85fd1f858d62206c9ea93ee9873d403c"

SOURCE_EXCLUSION_CATEGORIES = (
    "eligible_under_failed_discrete_policy",
    "documented_continuous_control_command",
    "documented_continuous_actuator_feedback",
    "documented_setpoint",
    "documented_process_sensor",
    "documented_status_or_alarm",
    "documented_internal_or_derived",
    "discrete_but_not_control_semantics",
    "control_semantics_but_constant",
    "control_semantics_but_insufficient_changes",
    "semantic_role_unresolved",
    "value_domain_unresolved",
    "manual_and_data_evidence_conflict",
    "excluded_other",
)
CONTINUOUS_SOURCE_ROLES = (
    "control_command",
    "actuator_state",
    "actuator_feedback",
)
ROUTE_DECISIONS = (
    "versioned_continuous_step_delayed_response_on_HAI",
    "audit_HAIEnd_P1_control_logic",
    "reopen_primary_dataset_decision",
    "blocked_relation_family_decision_indeterminate",
)
AUTHORIZED_TRAIN_FILES = (
    "hai-23.05/hai-train1.csv",
    "hai-23.05/hai-train2.csv",
    "hai-23.05/hai-train3.csv",
)
_PROHIBITED_PATH_TOKENS = (
    "hai-train4",
    "hai-test",
    "label-test",
    "summary_label",
    "custody",
    "attack",
    "private",
)


class HAISourceDiagnosisError(ValueError):
    """Raised when TASK-039BR0 evidence or access violates the frozen policy."""


def _artifact_dict(content: Mapping[str, Any]) -> dict[str, Any]:
    result = dict(content)
    result["artifact_hash"] = stable_hash_v1(content)
    return result


def _finite(value: float, field_name: str) -> float:
    result = float(value)
    if not math.isfinite(result):
        raise HAISourceDiagnosisError(f"{field_name} must be finite")
    return result


def _require_process(process_id: str) -> str:
    if process_id not in {"P1", "P3"}:
        raise HAISourceDiagnosisError("process_id must be P1 or P3")
    return process_id


def _validate_relative_path(relative_path: str) -> str:
    candidate = PurePosixPath(relative_path)
    if candidate.is_absolute() or ".." in candidate.parts:
        raise HAISourceDiagnosisError("TASK039BR0_PROHIBITED_DATA_ACCESS")
    lowered = relative_path.lower()
    if any(token in lowered for token in _PROHIBITED_PATH_TOKENS):
        raise HAISourceDiagnosisError("TASK039BR0_PROHIBITED_DATA_ACCESS")
    if relative_path not in AUTHORIZED_TRAIN_FILES:
        raise HAISourceDiagnosisError("TASK039BR0_PROHIBITED_DATA_ACCESS")
    return relative_path


@dataclass(frozen=True)
class HAISourceExclusionRecordV1:
    variable_name: str
    process_id: str
    documented_semantic_role: str
    observed_domain: str
    task039b_source_eligibility: bool
    primary_exclusion_reason: str
    secondary_exclusion_reasons: tuple[str, ...]
    manual_reference: tuple[int, ...]
    official_graph_references: tuple[str, ...]
    aggregate_domain_diagnostic_ref: str
    review_status: str
    metadata_confidence: str
    raw_values_included: bool = False
    schema_version: str = SCHEMA_VERSION
    artifact_type: str = "hai_source_exclusion_record_v1"

    def __post_init__(self) -> None:
        _require_process(self.process_id)
        if not self.variable_name.startswith(f"{self.process_id}_"):
            raise HAISourceDiagnosisError("variable does not match process scope")
        if self.primary_exclusion_reason not in SOURCE_EXCLUSION_CATEGORIES:
            raise HAISourceDiagnosisError("unknown source-exclusion category")
        if len(set(self.secondary_exclusion_reasons)) != len(
            self.secondary_exclusion_reasons
        ):
            raise HAISourceDiagnosisError("secondary exclusions must be unique")
        require_sha256(
            self.aggregate_domain_diagnostic_ref,
            "aggregate_domain_diagnostic_ref",
        )
        if self.raw_values_included:
            raise HAISourceDiagnosisError("source-exclusion records cannot contain values")

    def _content_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "artifact_type": self.artifact_type,
            "variable_name": self.variable_name,
            "process_id": self.process_id,
            "documented_semantic_role": self.documented_semantic_role,
            "observed_domain": self.observed_domain,
            "task039b_source_eligibility": self.task039b_source_eligibility,
            "primary_exclusion_reason": self.primary_exclusion_reason,
            "secondary_exclusion_reasons": list(self.secondary_exclusion_reasons),
            "manual_reference": list(self.manual_reference),
            "official_graph_references": list(self.official_graph_references),
            "aggregate_domain_diagnostic_ref": self.aggregate_domain_diagnostic_ref,
            "review_status": self.review_status,
            "metadata_confidence": self.metadata_confidence,
            "raw_values_included": self.raw_values_included,
        }

    @property
    def artifact_hash(self) -> str:
        return stable_hash_v1(self._content_dict())

    def to_dict(self) -> dict[str, Any]:
        return _artifact_dict(self._content_dict())


def classify_source_exclusion(
    metadata: Mapping[str, Any],
    *,
    source_change_count: int | None = None,
    manual_data_conflict: bool = False,
) -> str:
    """Return exactly one primary exclusion using metadata before behavior."""

    role = str(metadata.get("semantic_role", "unknown"))
    domain = str(metadata.get("observed_value_domain", "unknown"))
    reviewed = str(metadata.get("review_status", "unresolved")) == "reviewed"
    confidence = str(metadata.get("metadata_confidence", "insufficient"))
    eligible = bool(metadata.get("source_eligibility", False))
    if eligible:
        return "eligible_under_failed_discrete_policy"
    if manual_data_conflict:
        return "manual_and_data_evidence_conflict"
    if not reviewed or confidence == "insufficient":
        return "semantic_role_unresolved"
    if domain == "unknown":
        return "value_domain_unresolved"
    if role in CONTINUOUS_SOURCE_ROLES and domain == "constant":
        return "control_semantics_but_constant"
    if (
        role in CONTINUOUS_SOURCE_ROLES
        and domain in {"binary", "discrete"}
        and source_change_count is not None
        and source_change_count < 2
    ):
        return "control_semantics_but_insufficient_changes"
    if role == "control_command" and domain == "continuous":
        return "documented_continuous_control_command"
    if role in {"actuator_state", "actuator_feedback"} and domain == "continuous":
        return "documented_continuous_actuator_feedback"
    if role == "setpoint":
        return "documented_setpoint"
    if role == "process_sensor":
        return "documented_process_sensor"
    if role == "status_or_alarm":
        return "documented_status_or_alarm"
    if role == "derived_or_internal":
        return "documented_internal_or_derived"
    if domain in {"binary", "discrete"} and role not in CONTINUOUS_SOURCE_ROLES:
        return "discrete_but_not_control_semantics"
    return "excluded_other"


@dataclass(frozen=True)
class HAISourceExclusionSummaryV1:
    task039b_result_commit: str
    task039b_selection_hash: str
    frozen_status: str
    frozen_metrics: tuple[Mapping[str, Any], ...]
    counts_by_process: tuple[Mapping[str, Any], ...]
    private_detail_ledger_hash: str
    no_process_selected: bool = True
    raw_values_included: bool = False
    schema_version: str = SCHEMA_VERSION
    artifact_type: str = "hai_source_exclusion_summary_v1"

    def __post_init__(self) -> None:
        if self.task039b_result_commit != TASK039B_RESULT_COMMIT:
            raise HAISourceDiagnosisError("TASK-039B result commit mismatch")
        require_sha256(self.task039b_selection_hash, "task039b_selection_hash")
        require_sha256(self.private_detail_ledger_hash, "private_detail_ledger_hash")
        if self.frozen_status != "blocked_no_feasible_delayed_response_process":
            raise HAISourceDiagnosisError("TASK-039B frozen status changed")
        if not self.no_process_selected or self.raw_values_included:
            raise HAISourceDiagnosisError("source summary crossed its claim boundary")

    def _content_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "artifact_type": self.artifact_type,
            "task039b_result_commit": self.task039b_result_commit,
            "task039b_selection_hash": self.task039b_selection_hash,
            "frozen_status": self.frozen_status,
            "frozen_metrics": [dict(item) for item in self.frozen_metrics],
            "counts_by_process": [dict(item) for item in self.counts_by_process],
            "private_detail_ledger_hash": self.private_detail_ledger_hash,
            "no_process_selected": self.no_process_selected,
            "raw_values_included": self.raw_values_included,
        }

    @property
    def artifact_hash(self) -> str:
        return stable_hash_v1(self._content_dict())

    def to_dict(self) -> dict[str, Any]:
        return _artifact_dict(self._content_dict())


@dataclass(frozen=True)
class MorphologyFileSummaryV1:
    relative_path: str
    finite_value_status: str
    nonconstant_status: bool
    distinct_value_count: int
    distinct_count_capped: bool
    zero_difference_ratio: float
    nonzero_change_count: int
    piecewise_constant_run_count: int
    runs_at_least_3_seconds: int
    large_change_candidate_count: int
    positive_change_available: bool
    negative_change_available: bool
    diagnostic_noise_scale: float
    repeated_bounded_changes: bool

    def __post_init__(self) -> None:
        _validate_relative_path(self.relative_path)
        for field_value in (
            self.distinct_value_count,
            self.nonzero_change_count,
            self.piecewise_constant_run_count,
            self.runs_at_least_3_seconds,
            self.large_change_candidate_count,
        ):
            if field_value < 0:
                raise HAISourceDiagnosisError("morphology counts must be non-negative")
        if not 0.0 <= self.zero_difference_ratio <= 1.0:
            raise HAISourceDiagnosisError("zero_difference_ratio must be in [0, 1]")
        if _finite(self.diagnostic_noise_scale, "diagnostic_noise_scale") <= 0:
            raise HAISourceDiagnosisError("diagnostic_noise_scale must be positive")

    def to_dict(self) -> dict[str, Any]:
        return {
            "relative_path": self.relative_path,
            "finite_value_status": self.finite_value_status,
            "nonconstant_status": self.nonconstant_status,
            "distinct_value_count": self.distinct_value_count,
            "distinct_count_capped": self.distinct_count_capped,
            "zero_difference_ratio": self.zero_difference_ratio,
            "nonzero_change_count": self.nonzero_change_count,
            "piecewise_constant_run_count": self.piecewise_constant_run_count,
            "runs_at_least_3_seconds": self.runs_at_least_3_seconds,
            "large_change_candidate_count": self.large_change_candidate_count,
            "positive_change_available": self.positive_change_available,
            "negative_change_available": self.negative_change_available,
            "diagnostic_noise_scale": self.diagnostic_noise_scale,
            "repeated_bounded_changes": self.repeated_bounded_changes,
        }


@dataclass(frozen=True)
class HAIContinuousSourceMorphologyV1:
    variable_name: str
    process_id: str
    documented_semantic_role: str
    manual_reference: tuple[int, ...]
    file_summaries: tuple[MorphologyFileSummaryV1, ...]
    cross_file_availability: bool
    manual_semantic_coverage: bool
    manual_data_conflict: bool
    large_change_multiplier: float = 5.0
    diagnostic_threshold_authoritative: bool = False
    source_target_pairs_evaluated: bool = False
    raw_values_included: bool = False
    transition_timestamps_included: bool = False
    schema_version: str = SCHEMA_VERSION
    artifact_type: str = "hai_continuous_source_morphology_v1"

    def __post_init__(self) -> None:
        _require_process(self.process_id)
        if self.documented_semantic_role not in CONTINUOUS_SOURCE_ROLES:
            raise HAISourceDiagnosisError("morphology requires control/feedback semantics")
        if tuple(item.relative_path for item in self.file_summaries) != AUTHORIZED_TRAIN_FILES:
            raise HAISourceDiagnosisError("morphology must cover train1, train2, train3")
        if self.large_change_multiplier != 5.0:
            raise HAISourceDiagnosisError("large-change diagnostic multiplier is frozen")
        if (
            self.diagnostic_threshold_authoritative
            or self.source_target_pairs_evaluated
            or self.raw_values_included
            or self.transition_timestamps_included
        ):
            raise HAISourceDiagnosisError("morphology crossed its diagnosis boundary")

    def _content_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "artifact_type": self.artifact_type,
            "variable_name": self.variable_name,
            "process_id": self.process_id,
            "documented_semantic_role": self.documented_semantic_role,
            "manual_reference": list(self.manual_reference),
            "file_summaries": [item.to_dict() for item in self.file_summaries],
            "cross_file_availability": self.cross_file_availability,
            "manual_semantic_coverage": self.manual_semantic_coverage,
            "manual_data_conflict": self.manual_data_conflict,
            "large_change_multiplier": self.large_change_multiplier,
            "diagnostic_threshold_authoritative": self.diagnostic_threshold_authoritative,
            "source_target_pairs_evaluated": self.source_target_pairs_evaluated,
            "raw_values_included": self.raw_values_included,
            "transition_timestamps_included": self.transition_timestamps_included,
        }

    @property
    def artifact_hash(self) -> str:
        return stable_hash_v1(self._content_dict())

    def to_dict(self) -> dict[str, Any]:
        return _artifact_dict(self._content_dict())


@dataclass(frozen=True)
class HAIContinuousRouteReadinessV1:
    process_records: tuple[Mapping[str, Any], ...]
    readiness_definition: str
    ready_process_ids: tuple[str, ...]
    private_morphology_ledger_hash: str
    source_target_pairs_evaluated: bool = False
    process_selected: bool = False
    schema_version: str = SCHEMA_VERSION
    artifact_type: str = "hai_continuous_route_readiness_v1"

    def __post_init__(self) -> None:
        require_sha256(
            self.private_morphology_ledger_hash,
            "private_morphology_ledger_hash",
        )
        if tuple(item["process_id"] for item in self.process_records) != ("P1", "P3"):
            raise HAISourceDiagnosisError("continuous readiness must contain P1 then P3")
        expected = tuple(
            item["process_id"]
            for item in self.process_records
            if item["route_status"]
            == "continuous_step_route_ready_for_versioned_feasibility"
        )
        if self.ready_process_ids != expected:
            raise HAISourceDiagnosisError("ready process IDs disagree with records")
        if self.source_target_pairs_evaluated or self.process_selected:
            raise HAISourceDiagnosisError("readiness cannot evaluate pairs or select process")

    def _content_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "artifact_type": self.artifact_type,
            "process_records": [dict(item) for item in self.process_records],
            "readiness_definition": self.readiness_definition,
            "ready_process_ids": list(self.ready_process_ids),
            "private_morphology_ledger_hash": self.private_morphology_ledger_hash,
            "source_target_pairs_evaluated": self.source_target_pairs_evaluated,
            "process_selected": self.process_selected,
        }

    @property
    def artifact_hash(self) -> str:
        return stable_hash_v1(self._content_dict())

    def to_dict(self) -> dict[str, Any]:
        return _artifact_dict(self._content_dict())


@dataclass(frozen=True)
class HAIEndRouteReadinessV1:
    official_repository: str
    snapshot_commit: str
    official_directory: str
    pointer_inventory: tuple[Mapping[str, Any], ...]
    file_count: int
    expected_point_count: int
    train_file_count: int
    test_file_count: int
    normal_data_availability_documented: bool
    same_experiment_version_context_documented: bool
    boiler_internal_control_logic_documented: bool
    technical_manual_per_point_coverage_verified: bool
    official_graph_relevance: str
    license_and_citation_compatible: bool
    payload_downloaded_or_opened: bool
    binary_or_discrete_claim_made: bool
    row_synchronization_claim_made: bool
    complete_auditable_p1_candidate_route: bool
    route_status: str
    schema_version: str = SCHEMA_VERSION
    artifact_type: str = "haiend_route_readiness_v1"

    def __post_init__(self) -> None:
        if self.snapshot_commit != "2a814cebc9a66b06c9e5cd545e2d72e65d383737":
            raise HAISourceDiagnosisError("HAIEnd snapshot commit mismatch")
        if self.official_directory != "haiend-23.05" or self.file_count != len(
            self.pointer_inventory
        ):
            raise HAISourceDiagnosisError("HAIEnd inventory is inconsistent")
        if self.payload_downloaded_or_opened:
            raise HAISourceDiagnosisError("TASK-039BR0 cannot open HAIEnd payloads")
        if self.binary_or_discrete_claim_made or self.row_synchronization_claim_made:
            raise HAISourceDiagnosisError("HAIEnd claim ceiling exceeded")
        if self.route_status != "haiend_route_requires_separate_provenance_and_feasibility":
            raise HAISourceDiagnosisError("HAIEnd route status is invalid")

    def _content_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "artifact_type": self.artifact_type,
            "official_repository": self.official_repository,
            "snapshot_commit": self.snapshot_commit,
            "official_directory": self.official_directory,
            "pointer_inventory": [dict(item) for item in self.pointer_inventory],
            "file_count": self.file_count,
            "expected_point_count": self.expected_point_count,
            "train_file_count": self.train_file_count,
            "test_file_count": self.test_file_count,
            "normal_data_availability_documented": self.normal_data_availability_documented,
            "same_experiment_version_context_documented": self.same_experiment_version_context_documented,
            "boiler_internal_control_logic_documented": self.boiler_internal_control_logic_documented,
            "technical_manual_per_point_coverage_verified": self.technical_manual_per_point_coverage_verified,
            "official_graph_relevance": self.official_graph_relevance,
            "license_and_citation_compatible": self.license_and_citation_compatible,
            "payload_downloaded_or_opened": self.payload_downloaded_or_opened,
            "binary_or_discrete_claim_made": self.binary_or_discrete_claim_made,
            "row_synchronization_claim_made": self.row_synchronization_claim_made,
            "complete_auditable_p1_candidate_route": self.complete_auditable_p1_candidate_route,
            "route_status": self.route_status,
        }

    @property
    def artifact_hash(self) -> str:
        return stable_hash_v1(self._content_dict())

    def to_dict(self) -> dict[str, Any]:
        return _artifact_dict(self._content_dict())


@dataclass(frozen=True)
class RuleV1CompatibilityRecordV1:
    rule_schema_sha256: str
    rule_parser_sha256: str
    verifier_sha256: str
    runtime_sha256: str
    exactly_one_source: bool
    exactly_one_target: bool
    delayed_response_only: bool
    state_changes_to_only: bool
    literal_state_value_required: bool
    trigger_threshold_references_rejected: bool
    trigger_range_references_rejected: bool
    trigger_duration_references_rejected: bool
    increase_only: bool
    missing_expected_response_only: bool
    verifier_runtime_bound_to_semantics: bool
    continuous_source_route_classification: str
    rule_v1_modified: bool = False
    schema_version: str = SCHEMA_VERSION
    artifact_type: str = "rule_v1_compatibility_record_v1"

    def __post_init__(self) -> None:
        for name in (
            "rule_schema_sha256",
            "rule_parser_sha256",
            "verifier_sha256",
            "runtime_sha256",
        ):
            require_sha256(getattr(self, name), name)
        required = (
            self.exactly_one_source,
            self.exactly_one_target,
            self.delayed_response_only,
            self.state_changes_to_only,
            self.literal_state_value_required,
            self.trigger_threshold_references_rejected,
            self.trigger_range_references_rejected,
            self.trigger_duration_references_rejected,
            self.increase_only,
            self.missing_expected_response_only,
            self.verifier_runtime_bound_to_semantics,
        )
        if not all(required):
            raise HAISourceDiagnosisError("Rule v1 restriction audit is incomplete")
        if self.continuous_source_route_classification != "requires_versioned_rule_semantics":
            raise HAISourceDiagnosisError("continuous route must require versioned semantics")
        if self.rule_v1_modified:
            raise HAISourceDiagnosisError("TASK-039BR0 cannot modify Rule v1")

    def _content_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "artifact_type": self.artifact_type,
            "rule_schema_sha256": self.rule_schema_sha256,
            "rule_parser_sha256": self.rule_parser_sha256,
            "verifier_sha256": self.verifier_sha256,
            "runtime_sha256": self.runtime_sha256,
            "exactly_one_source": self.exactly_one_source,
            "exactly_one_target": self.exactly_one_target,
            "delayed_response_only": self.delayed_response_only,
            "state_changes_to_only": self.state_changes_to_only,
            "literal_state_value_required": self.literal_state_value_required,
            "trigger_threshold_references_rejected": self.trigger_threshold_references_rejected,
            "trigger_range_references_rejected": self.trigger_range_references_rejected,
            "trigger_duration_references_rejected": self.trigger_duration_references_rejected,
            "increase_only": self.increase_only,
            "missing_expected_response_only": self.missing_expected_response_only,
            "verifier_runtime_bound_to_semantics": self.verifier_runtime_bound_to_semantics,
            "continuous_source_route_classification": self.continuous_source_route_classification,
            "rule_v1_modified": self.rule_v1_modified,
        }

    @property
    def artifact_hash(self) -> str:
        return stable_hash_v1(self._content_dict())

    def to_dict(self) -> dict[str, Any]:
        return _artifact_dict(self._content_dict())


@dataclass(frozen=True)
class RelationFamilyRouteDecisionV1:
    diagnostic_status: str
    recommended_route: str
    next_task: str
    continuous_readiness_ref: str
    haiend_readiness_ref: str
    rule_v1_compatibility_ref: str
    source_exclusion_summary_ref: str
    decision_reasons: tuple[str, ...]
    thesis_contribution_preservation: tuple[Mapping[str, Any], ...]
    weighted_score_used: bool = False
    process_selected: bool = False
    task039c_authorized: bool = False
    task039b_gate_lowered: bool = False
    attack_information_used: bool = False
    schema_version: str = SCHEMA_VERSION
    artifact_type: str = "relation_family_route_decision_v1"

    def __post_init__(self) -> None:
        if self.diagnostic_status != "passed_source_eligibility_root_cause_audit":
            raise HAISourceDiagnosisError("diagnostic status is invalid")
        if self.recommended_route not in ROUTE_DECISIONS:
            raise HAISourceDiagnosisError("route decision is invalid")
        for name in (
            "continuous_readiness_ref",
            "haiend_readiness_ref",
            "rule_v1_compatibility_ref",
            "source_exclusion_summary_ref",
        ):
            require_sha256(getattr(self, name), name)
        if any(
            (
                self.weighted_score_used,
                self.process_selected,
                self.task039c_authorized,
                self.task039b_gate_lowered,
                self.attack_information_used,
            )
        ):
            raise HAISourceDiagnosisError("route decision crossed a frozen boundary")

    def _content_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "artifact_type": self.artifact_type,
            "diagnostic_status": self.diagnostic_status,
            "recommended_route": self.recommended_route,
            "next_task": self.next_task,
            "continuous_readiness_ref": self.continuous_readiness_ref,
            "haiend_readiness_ref": self.haiend_readiness_ref,
            "rule_v1_compatibility_ref": self.rule_v1_compatibility_ref,
            "source_exclusion_summary_ref": self.source_exclusion_summary_ref,
            "decision_reasons": list(self.decision_reasons),
            "thesis_contribution_preservation": [
                dict(item) for item in self.thesis_contribution_preservation
            ],
            "weighted_score_used": self.weighted_score_used,
            "process_selected": self.process_selected,
            "task039c_authorized": self.task039c_authorized,
            "task039b_gate_lowered": self.task039b_gate_lowered,
            "attack_information_used": self.attack_information_used,
        }

    @property
    def artifact_hash(self) -> str:
        return stable_hash_v1(self._content_dict())

    def to_dict(self) -> dict[str, Any]:
        return _artifact_dict(self._content_dict())


@dataclass(frozen=True)
class TASK039BR0DataAccessAuditV1:
    authorized_feature_files: tuple[str, ...]
    feature_access_entries: tuple[Mapping[str, Any], ...]
    test_file_access_count: int
    label_file_access_count: int
    attack_summary_access_count: int
    private_custody_access_count: int
    normal_guard_feature_values_accessed: bool
    p2_p4_feature_values_accessed: bool
    prohibited_data_access_count: int
    haiend_payload_opened: bool
    schema_version: str = SCHEMA_VERSION
    artifact_type: str = "task039br0_data_access_audit_v1"

    def __post_init__(self) -> None:
        if self.authorized_feature_files != AUTHORIZED_TRAIN_FILES:
            raise HAISourceDiagnosisError("authorized feature-file set changed")
        if any(
            count != 0
            for count in (
                self.test_file_access_count,
                self.label_file_access_count,
                self.attack_summary_access_count,
                self.private_custody_access_count,
                self.prohibited_data_access_count,
            )
        ):
            raise HAISourceDiagnosisError("TASK039BR0_PROHIBITED_DATA_ACCESS")
        if (
            self.normal_guard_feature_values_accessed
            or self.p2_p4_feature_values_accessed
            or self.haiend_payload_opened
        ):
            raise HAISourceDiagnosisError("TASK039BR0_PROHIBITED_DATA_ACCESS")

    def _content_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "artifact_type": self.artifact_type,
            "authorized_feature_files": list(self.authorized_feature_files),
            "feature_access_entries": [dict(item) for item in self.feature_access_entries],
            "test_file_access_count": self.test_file_access_count,
            "label_file_access_count": self.label_file_access_count,
            "attack_summary_access_count": self.attack_summary_access_count,
            "private_custody_access_count": self.private_custody_access_count,
            "normal_guard_feature_values_accessed": self.normal_guard_feature_values_accessed,
            "p2_p4_feature_values_accessed": self.p2_p4_feature_values_accessed,
            "prohibited_data_access_count": self.prohibited_data_access_count,
            "haiend_payload_opened": self.haiend_payload_opened,
        }

    @property
    def artifact_hash(self) -> str:
        return stable_hash_v1(self._content_dict())

    def to_dict(self) -> dict[str, Any]:
        return _artifact_dict(self._content_dict())


@dataclass
class TASK039BR0DataAccessLedger:
    _entries: list[dict[str, Any]] = field(default_factory=list)

    def authorize_feature_access(
        self, relative_path: str, process_id: str, variable_names: Sequence[str]
    ) -> None:
        _validate_relative_path(relative_path)
        _require_process(process_id)
        if not variable_names or any(
            not name.startswith(f"{process_id}_") for name in variable_names
        ):
            raise HAISourceDiagnosisError("TASK039BR0_PROHIBITED_DATA_ACCESS")
        self._entries.append(
            {
                "relative_path": relative_path,
                "process_id": process_id,
                "variable_count": len(tuple(variable_names)),
                "purpose": "aggregate_continuous_source_morphology_only",
            }
        )

    def reject_path(self, path: str) -> None:
        _validate_relative_path(path)

    def freeze(self) -> TASK039BR0DataAccessAuditV1:
        return TASK039BR0DataAccessAuditV1(
            authorized_feature_files=AUTHORIZED_TRAIN_FILES,
            feature_access_entries=tuple(dict(item) for item in self._entries),
            test_file_access_count=0,
            label_file_access_count=0,
            attack_summary_access_count=0,
            private_custody_access_count=0,
            normal_guard_feature_values_accessed=False,
            p2_p4_feature_values_accessed=False,
            prohibited_data_access_count=0,
            haiend_payload_opened=False,
        )


@dataclass
class _MorphologyAccumulator:
    values_seen: int = 0
    invalid_seen: int = 0
    previous: float | None = None
    run_length: int = 0
    run_count: int = 0
    runs_at_least_three: int = 0
    distinct: set[float] = field(default_factory=set)
    distinct_capped: bool = False
    changes: list[float] = field(default_factory=list)

    def add(self, raw: str, *, distinct_cap: int) -> None:
        try:
            value = float(raw)
        except (TypeError, ValueError):
            self.invalid_seen += 1
            self._close_run()
            self.previous = None
            return
        if not math.isfinite(value):
            self.invalid_seen += 1
            self._close_run()
            self.previous = None
            return
        self.values_seen += 1
        if len(self.distinct) < distinct_cap + 1:
            self.distinct.add(value)
        if len(self.distinct) > distinct_cap:
            self.distinct_capped = True
        if self.previous is None:
            self.run_length = 1
        else:
            change = value - self.previous
            self.changes.append(change)
            if change == 0.0:
                self.run_length += 1
            else:
                self._close_run()
                self.run_length = 1
        self.previous = value

    def _close_run(self) -> None:
        if self.run_length:
            self.run_count += 1
            if self.run_length >= 3:
                self.runs_at_least_three += 1
            self.run_length = 0

    def finish(
        self,
        relative_path: str,
        *,
        distinct_cap: int,
        epsilon: float,
        minimum_repeated_changes: int,
    ) -> MorphologyFileSummaryV1:
        self._close_run()
        if self.changes:
            center = statistics.median(self.changes)
            mad = statistics.median(abs(item - center) for item in self.changes)
            noise_scale = max(1.4826 * mad, epsilon)
        else:
            noise_scale = epsilon
        threshold = 5.0 * noise_scale
        nonzero = sum(item != 0.0 for item in self.changes)
        large = sum(abs(item) > threshold for item in self.changes)
        repeated = (
            self.invalid_seen == 0
            and len(self.distinct) > 1
            and nonzero >= minimum_repeated_changes
            and large >= minimum_repeated_changes
        )
        return MorphologyFileSummaryV1(
            relative_path=relative_path,
            finite_value_status=(
                "all_finite" if self.invalid_seen == 0 else "missing_or_nonfinite_present"
            ),
            nonconstant_status=len(self.distinct) > 1,
            distinct_value_count=min(len(self.distinct), distinct_cap),
            distinct_count_capped=self.distinct_capped,
            zero_difference_ratio=(
                sum(item == 0.0 for item in self.changes) / len(self.changes)
                if self.changes
                else 1.0
            ),
            nonzero_change_count=nonzero,
            piecewise_constant_run_count=self.run_count,
            runs_at_least_3_seconds=self.runs_at_least_three,
            large_change_candidate_count=large,
            positive_change_available=any(item > 0.0 for item in self.changes),
            negative_change_available=any(item < 0.0 for item in self.changes),
            diagnostic_noise_scale=noise_scale,
            repeated_bounded_changes=repeated,
        )


def diagnose_continuous_source_morphology(
    *,
    data_root: Path,
    process_id: str,
    metadata_records: Sequence[Mapping[str, Any]],
    ledger: TASK039BR0DataAccessLedger,
    distinct_cap: int = 4096,
    numeric_epsilon: float = 1e-12,
    minimum_repeated_changes: int = 2,
) -> tuple[HAIContinuousSourceMorphologyV1, ...]:
    """Stream only documented continuous control columns from train1--train3."""

    _require_process(process_id)
    candidates = tuple(
        record
        for record in metadata_records
        if record.get("process_id") == process_id
        and record.get("semantic_role") in CONTINUOUS_SOURCE_ROLES
        and record.get("observed_value_domain") == "continuous"
        and record.get("review_status") == "reviewed"
        and record.get("metadata_confidence") in {"high", "medium"}
    )
    names = tuple(str(item["variable_name"]) for item in candidates)
    if len(names) != len(set(names)):
        raise HAISourceDiagnosisError("duplicate continuous source metadata")
    if not names:
        return ()
    summaries: dict[str, list[MorphologyFileSummaryV1]] = {name: [] for name in names}
    for relative_path in AUTHORIZED_TRAIN_FILES:
        ledger.authorize_feature_access(relative_path, process_id, names)
        path = data_root / PurePosixPath(relative_path).name
        if not path.is_file():
            raise HAISourceDiagnosisError("authorized training file is missing")
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.reader(handle)
            try:
                header = next(reader)
            except StopIteration as exc:
                raise HAISourceDiagnosisError("training file is empty") from exc
            indexes = []
            for name in names:
                if name not in header:
                    raise HAISourceDiagnosisError("continuous source column is missing")
                indexes.append(header.index(name))
            accumulators = {name: _MorphologyAccumulator() for name in names}
            for row in reader:
                if len(row) != len(header):
                    raise HAISourceDiagnosisError("training row field count mismatch")
                for name, index in zip(names, indexes, strict=True):
                    accumulators[name].add(row[index], distinct_cap=distinct_cap)
        for name in names:
            summaries[name].append(
                accumulators[name].finish(
                    relative_path,
                    distinct_cap=distinct_cap,
                    epsilon=numeric_epsilon,
                    minimum_repeated_changes=minimum_repeated_changes,
                )
            )
    records = []
    by_name = {str(item["variable_name"]): item for item in candidates}
    for name in names:
        metadata = by_name[name]
        file_summaries = tuple(summaries[name])
        records.append(
            HAIContinuousSourceMorphologyV1(
                variable_name=name,
                process_id=process_id,
                documented_semantic_role=str(metadata["semantic_role"]),
                manual_reference=tuple(int(item) for item in metadata["manual_reference"]),
                file_summaries=file_summaries,
                cross_file_availability=all(
                    item.finite_value_status == "all_finite" for item in file_summaries
                ),
                manual_semantic_coverage=bool(metadata["manual_reference"]),
                manual_data_conflict=False,
            )
        )
    return tuple(records)


def build_continuous_route_readiness(
    morphology: Sequence[HAIContinuousSourceMorphologyV1],
    *,
    private_morphology_ledger_hash: str,
) -> HAIContinuousRouteReadinessV1:
    process_records = []
    ready_ids = []
    for process_id in ("P1", "P3"):
        records = [item for item in morphology if item.process_id == process_id]
        nonconstant = {
            path: sum(
                next(
                    summary.nonconstant_status
                    for summary in item.file_summaries
                    if summary.relative_path == path
                )
                for item in records
            )
            for path in AUTHORIZED_TRAIN_FILES
        }
        repeated_all = sum(
            all(summary.repeated_bounded_changes for summary in item.file_summaries)
            for item in records
        )
        conflicts = sum(item.manual_data_conflict for item in records)
        manual_complete = sum(item.manual_semantic_coverage for item in records)
        ready = (
            len(records) >= 2
            and all(nonconstant[path] >= 2 for path in AUTHORIZED_TRAIN_FILES)
            and repeated_all >= 2
            and manual_complete == len(records)
            and conflicts == 0
        )
        status = (
            "continuous_step_route_ready_for_versioned_feasibility"
            if ready
            else "continuous_step_route_not_ready"
        )
        if ready:
            ready_ids.append(process_id)
        process_records.append(
            {
                "process_id": process_id,
                "documented_continuous_control_feedback_candidates": len(records),
                "nonconstant_candidates_train1": nonconstant[AUTHORIZED_TRAIN_FILES[0]],
                "nonconstant_candidates_train2": nonconstant[AUTHORIZED_TRAIN_FILES[1]],
                "nonconstant_candidates_train3": nonconstant[AUTHORIZED_TRAIN_FILES[2]],
                "candidates_with_repeated_bounded_changes_all_files": repeated_all,
                "manual_semantic_coverage_count": manual_complete,
                "manual_data_conflict_count": conflicts,
                "morphology_record_hashes": [item.artifact_hash for item in records],
                "route_status": status,
            }
        )
    return HAIContinuousRouteReadinessV1(
        process_records=tuple(process_records),
        readiness_definition=(
            "at_least_two_documented_candidates_nonconstant_with_at_least_two_"
            "nonzero_and_large_change_candidates_in_each_of_train1_train2_train3"
        ),
        ready_process_ids=tuple(ready_ids),
        private_morphology_ledger_hash=private_morphology_ledger_hash,
    )


def decide_relation_family_route(
    *,
    continuous: HAIContinuousRouteReadinessV1,
    haiend: HAIEndRouteReadinessV1,
    rule_v1: RuleV1CompatibilityRecordV1,
    source_summary: HAISourceExclusionSummaryV1,
    evidence_conflict: bool = False,
) -> RelationFamilyRouteDecisionV1:
    """Apply Route 1, Route 2, Route 3, then indeterminate without scoring."""

    if evidence_conflict:
        route = "blocked_relation_family_decision_indeterminate"
        next_task = "researcher_review_required"
        reasons = ("evidence_conflict_prevents_unique_route",)
    elif continuous.ready_process_ids:
        route = "versioned_continuous_step_delayed_response_on_HAI"
        next_task = "TASK-039BR1"
        reasons = (
            "at_least_one_HAI_process_satisfies_all_source_morphology_readiness_gates",
            "continuous_trigger_requires_a_second_predefined_versioned_rule_family",
        )
    elif haiend.complete_auditable_p1_candidate_route:
        route = "audit_HAIEnd_P1_control_logic"
        next_task = "TASK-039A-END"
        reasons = (
            "continuous_step_route_failed",
            "official_HAIEnd_inventory_supports_a_separate_auditable_P1_route",
        )
    else:
        route = "reopen_primary_dataset_decision"
        next_task = "new_primary_dataset_source_decision"
        reasons = (
            "neither_HAI_route_is_currently_defensible",
            "another_dataset_requires_a_new_approved_source_decision",
        )
    principles = (
        "bounded_rule_family",
        "normal_only_evidence_construction",
        "constrained_agent_action_space",
        "deterministic_verifier_authority",
        "llm_free_runtime",
        "detector_false_negative_correction",
        "trace_grounded_explanation",
        "validity_utility_separation",
    )
    preservation = tuple(
        {
            "principle": principle,
            "preserved": True,
            "required_guard": (
                "second_predefined_versioned_trigger_family"
                if principle == "bounded_rule_family" and route.startswith("versioned_")
                else "existing_v6_boundary_retained"
            ),
        }
        for principle in principles
    )
    return RelationFamilyRouteDecisionV1(
        diagnostic_status="passed_source_eligibility_root_cause_audit",
        recommended_route=route,
        next_task=next_task,
        continuous_readiness_ref=continuous.artifact_hash,
        haiend_readiness_ref=haiend.artifact_hash,
        rule_v1_compatibility_ref=rule_v1.artifact_hash,
        source_exclusion_summary_ref=source_summary.artifact_hash,
        decision_reasons=reasons,
        thesis_contribution_preservation=preservation,
    )
