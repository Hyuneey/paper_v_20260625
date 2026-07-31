"""Synthetic factories shared by TASK-039P1B tests."""

from __future__ import annotations

from hashlib import sha256
from typing import Any

from paperworks.data.contracts_v2 import SplitRoleV2
from paperworks.v6.common import CreationMetadataV1, stable_hash_v1
from paperworks.v6.detector_context_v1 import (
    DetectorContextPurposeV1,
    DetectorErrorContextV1,
    DetectorErrorDirectionV1,
)
from paperworks.v6.normal_evidence_v1 import (
    CalibrationParameterReferenceV1,
    CalibrationParameterRoleV1,
    DistributionSummaryV1,
    EvidenceStatusV1,
    NormalRelationEvidenceV1,
    OperatingRegimeStatusV1,
    RelationStabilitySummaryV1,
    RelationSupportSummaryV1,
    ResponseDirectionV1,
    StabilityStatusV1,
)
from paperworks.v6.outcomes_v1 import (
    ConstructionActionRecordV1,
    ConstructionActionTypeV1,
    ConstructionArmV1,
    ConstructionTerminalStatusV1,
    GovernanceDecisionV1,
    RuleConstructionOutcomeV1,
    RuleGovernanceOutcomeV1,
)


def digest(label: str) -> str:
    return sha256(label.encode("utf-8")).hexdigest()


def creation_metadata() -> CreationMetadataV1:
    return CreationMetadataV1(
        created_at="2026-07-31T00:00:00Z",
        created_by="task039p1b-test",
        code_commit="59715458",
        config_hash=digest("config"),
    )


def lag_summary() -> DistributionSummaryV1:
    return DistributionSummaryV1(
        count=3,
        minimum=1.0,
        p50=2.0,
        p95=2.8,
        maximum=3.0,
        unit="seconds",
        method="synthetic_quantiles",
        value_semantics="lag",
    )


def magnitude_summary() -> DistributionSummaryV1:
    return DistributionSummaryV1(
        count=3,
        minimum=0.1,
        p50=0.2,
        p95=0.35,
        maximum=0.4,
        unit="engineering_unit",
        method="synthetic_absolute_quantiles",
        value_semantics="absolute_response_magnitude",
    )


def stable_summary() -> RelationStabilitySummaryV1:
    return RelationStabilitySummaryV1(
        status=StabilityStatusV1.STABLE,
        method="synthetic_replicates",
        replicate_count=3,
        variation_measure=0.1,
        confidence_lower=0.0,
        confidence_upper=0.2,
    )


def supported_evidence(**overrides: Any) -> NormalRelationEvidenceV1:
    values: dict[str, Any] = {
        "dataset_manifest_id": digest("dataset"),
        "data_view_id": digest("view"),
        "split_manifest_id": digest("calibration-split"),
        "split_role": SplitRoleV2.NORMAL_RELATION_CALIBRATION,
        "process_scope": ("P1",),
        "source_variable": "ACTUATOR_1",
        "target_variable": "SENSOR_1",
        "source_metadata_ref": digest("source-metadata"),
        "target_metadata_ref": digest("target-metadata"),
        "candidate_universe_ref": digest("candidate-universe"),
        "candidate_edge_refs": (digest("candidate-edge"),),
        "relation_family": "delayed_response",
        "response_direction": ResponseDirectionV1.INCREASE,
        "operating_regime_id": "regime-1",
        "operating_regime_status": OperatingRegimeStatusV1.VERIFIED,
        "operating_regime_condition_refs": (digest("regime-condition"),),
        "support_summary": RelationSupportSummaryV1(
            trigger_count=5,
            evaluable_trigger_count=4,
            matched_response_count=3,
            missing_response_count=1,
            right_censored_count=1,
        ),
        "lag_summary": lag_summary(),
        "response_magnitude_summary": magnitude_summary(),
        "persistence_summary": None,
        "stability_summary": stable_summary(),
        "evidence_status": EvidenceStatusV1.SUPPORTED,
        "evidence_insufficiency_reasons": (),
        "matched_normal_reference_refs": (digest("matched-normal"),),
        "calibration_parameter_refs": (
            CalibrationParameterReferenceV1(
                CalibrationParameterRoleV1.LAG, digest("lag-parameter")
            ),
            CalibrationParameterReferenceV1(
                CalibrationParameterRoleV1.TOLERANCE,
                digest("tolerance-parameter"),
            ),
        ),
        "provenance_references": (digest("profile-provenance"),),
        "creation_metadata": creation_metadata(),
        "raw_values_included": False,
        "label_performance_used": False,
        "detector_context_used": False,
        "prohibited_claims": (
            "physical_causality",
            "root_cause",
            "universal_invariant",
        ),
        "validity_authority_granted": False,
        "runtime_authority_granted": False,
        "claim_boundary": "Normal relation evidence only; no causal claim.",
    }
    values.update(overrides)
    return NormalRelationEvidenceV1(**values)


def detector_context(**overrides: Any) -> DetectorErrorContextV1:
    values: dict[str, Any] = {
        "dataset_manifest_id": digest("dataset"),
        "data_view_id": digest("view"),
        "split_manifest_id": digest("development-split"),
        "split_role": SplitRoleV2.DEVELOPMENT,
        "process_scope": ("P1",),
        "normal_relation_evidence_ref": supported_evidence().artifact_hash,
        "error_direction": DetectorErrorDirectionV1.FALSE_NEGATIVE,
        "detector_artifact_ref": digest("detector"),
        "detector_config_ref": digest("detector-config"),
        "detector_prediction_ref": digest("detector-prediction"),
        "event_refs": (digest("event-ref"),),
        "context_window_refs": (digest("window-ref"),),
        "purpose": DetectorContextPurposeV1.DEVELOPMENT_DIAGNOSTIC,
        "supplementary_only": False,
        "primary_correction_direction": True,
        "provenance_references": (digest("detector-provenance"),),
        "creation_metadata": creation_metadata(),
        "raw_values_included": False,
        "outer_data_used": False,
        "sealed_data_used": False,
        "replaces_normal_evidence": False,
        "validity_authority_granted": False,
        "runtime_authority_granted": False,
        "claim_boundary": "Reference-only detector error context.",
    }
    values.update(overrides)
    return DetectorErrorContextV1(**values)


def action(
    action_type: ConstructionActionTypeV1 = ConstructionActionTypeV1.INSPECT,
    *,
    index: int = 0,
    feedback: bool = False,
) -> ConstructionActionRecordV1:
    return ConstructionActionRecordV1(
        action_index=index,
        action_type=action_type,
        input_artifact_refs=(digest(f"action-input-{index}"),),
        output_artifact_refs=(),
        verifier_feedback_refs=(
            (digest(f"feedback-{index}"),) if feedback else ()
        ),
        changed_fields=(),
        reason_code=f"{action_type.value}_reason",
        provider_call_index=None,
    )


def construction_outcome(**overrides: Any) -> RuleConstructionOutcomeV1:
    values: dict[str, Any] = {
        "construction_arm": ConstructionArmV1.T0,
        "normal_relation_evidence_ref": supported_evidence().artifact_hash,
        "normal_evidence_status": EvidenceStatusV1.SUPPORTED,
        "parameter_strategy_ref": digest("parameter-strategy"),
        "candidate_rule_ref": digest("candidate-rule"),
        "verifier_result_refs": (),
        "action_history": (action(),),
        "provider_call_budget": 0,
        "provider_calls_used": 0,
        "token_budget": 0,
        "tokens_used": 0,
        "independent_generation": False,
        "terminal_status": ConstructionTerminalStatusV1.RULE_CANDIDATE,
        "reason_codes": ("candidate_constructed",),
        "provider_failure": False,
        "invalid_output_detected": False,
        "provenance_references": (digest("construction-provenance"),),
        "creation_metadata": creation_metadata(),
        "outer_data_used": False,
        "sealed_data_used": False,
        "validity_authority_granted": False,
        "runtime_authority_granted": False,
        "claim_boundary": "Construction produces candidates, not accepted rules.",
    }
    values.update(overrides)
    return RuleConstructionOutcomeV1(**values)


def governance_outcome(**overrides: Any) -> RuleGovernanceOutcomeV1:
    accepted = digest("accepted-rule")
    values: dict[str, Any] = {
        "accepted_rule_ref": accepted,
        "verifier_result_ref": digest("verifier-result"),
        "normal_guard_assessment_ref": digest("normal-guard"),
        "inner_utility_assessment_ref": digest("inner-utility"),
        "governance_policy_ref": digest("governance-policy"),
        "detector_error_context_refs": (),
        "decision": GovernanceDecisionV1.SELECTED_RULE,
        "decision_reason_codes": ("selected_by_frozen_inner_policy",),
        "applied_rule_ref": accepted,
        "label_performance_used": True,
        "outer_data_used": False,
        "sealed_data_used": False,
        "authority_binding_verified": False,
        "validity_reassessed": False,
        "utility_assessment_only": True,
        "provenance_references": (digest("governance-provenance"),),
        "creation_metadata": creation_metadata(),
        "runtime_authority_granted": False,
        "claim_boundary": "Inner utility decision only.",
    }
    values.update(overrides)
    return RuleGovernanceOutcomeV1(**values)


def legacy_sources() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    profile: dict[str, Any] = {
        "schema_version": "1.0",
        "artifact_type": "relation_profile",
        "dataset": "synthetic",
        "split_name": "calibration_normal",
        "data_fingerprint": digest("legacy-data"),
        "config_hash": digest("legacy-config"),
        "code_commit": "59715458",
        "random_seed": 7,
        "created_at": "2026-07-31T00:00:00Z",
        "source": "ACTUATOR_1",
        "target": "SENSOR_1",
        "relation_type": "binary_actuator_to_continuous_sensor",
        "source_view": "canonical_rule_view",
        "sampling_period_seconds": 1.0,
        "trigger_count": 5,
        "matched_response_count": 3,
        "censored_or_missing_count": 2,
        "missing_response_count": 1,
        "right_censored_count": 1,
        "overlapping_window_count": 0,
        "delay_summary_seconds": {
            "count": 3.0,
            "min": 1.0,
            "max": 3.0,
            "mean": 2.0,
            "p50": 2.0,
        },
        "magnitude_summary": {
            "count": 3.0,
            "min": 0.1,
            "max": 0.4,
            "mean": 0.25,
            "p50": 0.2,
        },
        "normal_support_status": "supported",
        "upstream_artifact_ids": [digest("upstream")],
        "trigger_events": [{"synthetic": "omitted"}],
        "response_events": [{"synthetic": "omitted"}],
    }
    pack: dict[str, Any] = {
        "schema_version": "1.0",
        "artifact_type": "relation_evidence_pack",
        "source": "ACTUATOR_1",
        "target": "SENSOR_1",
        "relation_type": "binary_actuator_to_continuous_sensor",
        "recommended_rule_family": "changed_to_increase_within_response_missing",
        "relation_profile_id": stable_hash_v1(profile),
        "calibration_record_ids": {
            "max_response_delay_seconds": digest("legacy-delay-record"),
            "min_response_magnitude": digest("legacy-magnitude-record"),
        },
        "calibrated_parameters": {
            "max_response_delay_seconds": 3.0,
            "min_response_magnitude": 0.1,
        },
        "support_counts": {
            "trigger_count": 5,
            "matched_response_count": 3,
            "missing_response_count": 1,
            "right_censored_count": 1,
            "overlapping_window_count": 0,
        },
        "source_view": "canonical_rule_view",
        "sampling_period_seconds": 1.0,
        "upstream_artifact_ids": [digest("upstream")],
    }
    context: dict[str, Any] = {
        "dataset_manifest_id": digest("dataset"),
        "data_view_id": digest("view"),
        "split_manifest_id": digest("calibration-split"),
        "target_split_role": "normal_relation_calibration",
        "process_scope": ["P1"],
        "operating_regime_id": "regime-1",
        "operating_regime_condition_refs": [digest("regime-condition")],
        "source_metadata_ref": digest("source-metadata"),
        "target_metadata_ref": digest("target-metadata"),
        "candidate_universe_ref": digest("candidate-universe"),
        "candidate_edge_refs": [digest("candidate-edge")],
        "matched_normal_reference_refs": [digest("matched-normal")],
        "stability_summary": stable_summary().to_dict(),
        "calibration_parameter_refs": {
            "lag": digest("lag-parameter"),
            "tolerance": digest("tolerance-parameter"),
        },
        "response_direction": "increase",
        "creation_metadata": creation_metadata().to_dict(),
    }
    return profile, pack, context
