"""Wheel-portable embedded JSON-schema documents for VALIDATION V2."""

from __future__ import annotations

from typing import Any, Mapping


META = "https://json-schema.org/draft/2020-12/schema"
SHA = {"type": "string", "pattern": "^[0-9a-f]{64}$"}
TEXT = {"type": "string", "minLength": 1}
ARTIFACT_BINDING = {
    "type": "object",
    "additionalProperties": False,
    "required": ["artifact_id", "content_sha256", "relative_path"],
    "properties": {
        "artifact_id": {"$ref": "#/$defs/text"},
        "content_sha256": {"$ref": "#/$defs/sha256"},
        "relative_path": {
            "type": "string",
            "pattern": r"^(?!/)(?!.*(?:^|/)\.\.(?:/|$))(?!.*\\)(?!.*:).+$",
        },
    },
}
NUMERIC_BINDING = {
    "type": "object",
    "additionalProperties": False,
    "required": ["numeric_role", "reference_hash", "reference_id"],
    "properties": {
        "numeric_role": {"type": "string"},
        "reference_hash": {"$ref": "#/$defs/sha256"},
        "reference_id": {"$ref": "#/$defs/text"},
    },
}
DESCRIPTOR = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "artifact_type", "descriptor_hash", "numeric_authority_hash",
        "numeric_reference_bindings", "relation_binding_hash", "relation_id",
        "schema_version", "selected_horizon_seconds", "semantic_execution_hash",
        "source", "source_direction", "target", "target_direction",
    ],
    "properties": {
        "artifact_type": {"const": "validation_v2_formal_v4_rule_descriptor_v1"},
        "descriptor_hash": {"$ref": "#/$defs/sha256"},
        "numeric_authority_hash": {"$ref": "#/$defs/sha256"},
        "numeric_reference_bindings": {
            "type": "array", "minItems": 10, "maxItems": 10,
            "items": {"$ref": "#/$defs/numeric_binding"},
        },
        "relation_binding_hash": {"$ref": "#/$defs/sha256"},
        "relation_id": {"$ref": "#/$defs/text"},
        "schema_version": {"const": "1.0.0"},
        "selected_horizon_seconds": {"enum": [1, 5, 10, 30, 60]},
        "semantic_execution_hash": {"$ref": "#/$defs/sha256"},
        "source": {"$ref": "#/$defs/text"},
        "source_direction": {"enum": ["step_up", "step_down"]},
        "target": {"$ref": "#/$defs/text"},
        "target_direction": {"enum": ["increase", "decrease"]},
    },
}

PORTFOLIO_SCHEMA: Mapping[str, Any] = {
    "$schema": META,
    "$id": "paperworks://validation-v2/formal-v4-portfolio-authority-v1",
    "title": "VALIDATION V2 Formal V4 Portfolio Authority V1",
    "type": "object",
    "additionalProperties": False,
    "required": [
        "allowed_split_roles", "artifact_type", "authority_family", "authority_hash",
        "canonical_rule_v1_authoritative", "canonical_to_v4_bridge_used", "config_id",
        "descriptor_set_hash", "descriptors", "evaluator_contract_hash", "experiment_id",
        "feature_contract_binding", "file_contract_binding", "heldout_authorized", "method_id",
        "numeric_authority_binding", "portfolio_id", "relation_authority_binding",
        "sampling_contract_binding", "schema_version", "source_commit", "verifier_v1_authoritative",
    ],
    "properties": {
        "allowed_split_roles": {"const": ["DEVELOPMENT_TEST1"]},
        "artifact_type": {"const": "validation_v2_formal_v4_portfolio_authority_v1"},
        "authority_family": {"const": "FORMAL_V4"},
        "authority_hash": {"$ref": "#/$defs/sha256"},
        "canonical_rule_v1_authoritative": {"const": False},
        "canonical_to_v4_bridge_used": {"const": False},
        "config_id": {"$ref": "#/$defs/text"},
        "descriptor_set_hash": {"$ref": "#/$defs/sha256"},
        "descriptors": {"type": "array", "minItems": 1, "items": {"$ref": "#/$defs/descriptor"}},
        "evaluator_contract_hash": {"$ref": "#/$defs/sha256"},
        "experiment_id": {"$ref": "#/$defs/text"},
        "feature_contract_binding": {"$ref": "#/$defs/artifact_binding"},
        "file_contract_binding": {"$ref": "#/$defs/artifact_binding"},
        "heldout_authorized": {"const": False},
        "method_id": {"$ref": "#/$defs/text"},
        "numeric_authority_binding": {"$ref": "#/$defs/artifact_binding"},
        "portfolio_id": {"$ref": "#/$defs/text"},
        "relation_authority_binding": {"$ref": "#/$defs/artifact_binding"},
        "sampling_contract_binding": {"$ref": "#/$defs/artifact_binding"},
        "schema_version": {"const": "1.0.0"},
        "source_commit": {"$ref": "#/$defs/git_commit"},
        "verifier_v1_authoritative": {"const": False},
    },
    "$defs": {
        "artifact_binding": ARTIFACT_BINDING,
        "descriptor": DESCRIPTOR,
        "numeric_binding": NUMERIC_BINDING,
        "git_commit": {"type": "string", "pattern": "^[0-9a-f]{40}$"},
        "sha256": SHA,
        "text": TEXT,
    },
}

RUNTIME_SCHEMA: Mapping[str, Any] = {
    "$schema": META,
    "$id": "paperworks://validation-v2/formal-v4-runtime-authorization-v1",
    "title": "VALIDATION V2 Formal V4 Runtime Authorization V1",
    "type": "object",
    "additionalProperties": False,
    "required": [
        "artifact_type", "authority_family", "authority_hash", "authorization_hash",
        "authorization_id", "descriptor_set_hash", "evaluator_contract_hash",
        "execution_context_hash", "feature_contract_hash", "file_contract_hash",
        "heldout_authorized", "label_access_before_prediction_freeze",
        "numeric_authority_hash", "portfolio_id", "runtime_config_hash",
        "sampling_contract_hash", "schema_version", "split_role",
    ],
    "properties": {
        "artifact_type": {"const": "validation_v2_formal_v4_runtime_authorization_v1"},
        "authority_family": {"const": "FORMAL_V4"},
        "authority_hash": {"$ref": "#/$defs/sha256"},
        "authorization_hash": {"$ref": "#/$defs/sha256"},
        "authorization_id": {"type": "string", "pattern": "^V2-AUTH-[0-9a-f]{16}$"},
        "descriptor_set_hash": {"$ref": "#/$defs/sha256"},
        "evaluator_contract_hash": {"$ref": "#/$defs/sha256"},
        "execution_context_hash": {"$ref": "#/$defs/sha256"},
        "feature_contract_hash": {"$ref": "#/$defs/sha256"},
        "file_contract_hash": {"$ref": "#/$defs/sha256"},
        "heldout_authorized": {"const": False},
        "label_access_before_prediction_freeze": {"const": False},
        "numeric_authority_hash": {"$ref": "#/$defs/sha256"},
        "portfolio_id": {"$ref": "#/$defs/text"},
        "runtime_config_hash": {"$ref": "#/$defs/sha256"},
        "sampling_contract_hash": {"$ref": "#/$defs/sha256"},
        "schema_version": {"const": "1.0.0"},
        "split_role": {"const": "DEVELOPMENT_TEST1"},
    },
    "$defs": {"sha256": SHA, "text": TEXT},
}

PREDICTION_RECORD = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "file_id", "file_content_sha256", "row_index", "alarm",
        "contributing_rule_ids", "trace_hashes",
    ],
    "properties": {
        "file_id": {"$ref": "#/$defs/text"},
        "file_content_sha256": {"$ref": "#/$defs/sha256"},
        "row_index": {"type": "integer"},
        "alarm": {"type": "boolean"},
        "contributing_rule_ids": {"type": "array", "items": {"$ref": "#/$defs/text"}},
        "trace_hashes": {"type": "array", "items": {"$ref": "#/$defs/sha256"}},
    },
}

D1_PREDICTION_SCHEMA: Mapping[str, Any] = {
    "$schema": META,
    "$id": "paperworks://validation-v2/d1-prediction-artifact-v2",
    "title": "VALIDATION V2 Durable D1 Prediction Artifact V2",
    "type": "object",
    "additionalProperties": False,
    "required": [
        "schema", "schema_version", "method_id", "config_id", "experiment_id",
        "dataset_id", "split_role", "authority_hash", "runtime_authorization_hash",
        "execution_context_hash", "source_commit", "portfolio_hash",
        "file_contract_hash", "label_blind", "record_count", "alarm_count",
        "records", "self_hash",
    ],
    "properties": {
        "schema": {"const": "paperworks.validation_v2.d1_prediction_artifact_v2"},
        "schema_version": {"const": "2.0.0"},
        "method_id": {"$ref": "#/$defs/text"},
        "config_id": {"$ref": "#/$defs/text"},
        "experiment_id": {"$ref": "#/$defs/text"},
        "dataset_id": {"$ref": "#/$defs/text"},
        "split_role": {"const": "DEVELOPMENT_TEST1"},
        "authority_hash": {"$ref": "#/$defs/sha256"},
        "runtime_authorization_hash": {"$ref": "#/$defs/sha256"},
        "execution_context_hash": {"$ref": "#/$defs/sha256"},
        "source_commit": {"type": "string", "pattern": "^[0-9a-f]{40}$"},
        "portfolio_hash": {"$ref": "#/$defs/sha256"},
        "file_contract_hash": {"$ref": "#/$defs/sha256"},
        "label_blind": {"const": True},
        "record_count": {"type": "integer"},
        "alarm_count": {"type": "integer"},
        "records": {"type": "array", "minItems": 1, "items": {"$ref": "#/$defs/prediction_record"}},
        "self_hash": {"$ref": "#/$defs/sha256"},
    },
    "$defs": {"prediction_record": PREDICTION_RECORD, "sha256": SHA, "text": TEXT},
}

FREEZE_RECEIPT_SCHEMA: Mapping[str, Any] = {
    "$schema": META,
    "$id": "paperworks://validation-v2/durable-prediction-freeze-receipt-v1",
    "title": "VALIDATION V2 Durable Prediction Freeze Receipt V1",
    "type": "object",
    "additionalProperties": False,
    "required": [
        "schema", "schema_version", "prediction_relative_path",
        "prediction_bytes_sha256", "prediction_self_hash", "authority_hash",
        "runtime_authorization_hash", "execution_context_hash", "source_commit",
        "portfolio_hash", "file_contract_hash",
        "record_count", "publication_method", "file_fsync", "directory_fsync",
        "state", "self_hash",
    ],
    "properties": {
        "schema": {"const": "paperworks.validation_v2.durable_prediction_freeze_receipt_v1"},
        "schema_version": {"const": "1.0.0"},
        "prediction_relative_path": {
            "type": "string",
            "pattern": r"^(?!/)(?!.*(?:^|/)\.\.(?:/|$))(?!.*\\)(?!.*:).+$",
        },
        "prediction_bytes_sha256": {"$ref": "#/$defs/sha256"},
        "prediction_self_hash": {"$ref": "#/$defs/sha256"},
        "authority_hash": {"$ref": "#/$defs/sha256"},
        "runtime_authorization_hash": {"$ref": "#/$defs/sha256"},
        "execution_context_hash": {"$ref": "#/$defs/sha256"},
        "source_commit": {"type": "string", "pattern": "^[0-9a-f]{40}$"},
        "portfolio_hash": {"$ref": "#/$defs/sha256"},
        "file_contract_hash": {"$ref": "#/$defs/sha256"},
        "record_count": {"type": "integer"},
        "publication_method": {"const": "HARD_LINK_NO_OVERWRITE"},
        "file_fsync": {"const": True},
        "directory_fsync": {"enum": ["PERFORMED", "UNSUPPORTED_WINDOWS"]},
        "state": {"const": "REOPENED_AND_REPLAYED"},
        "self_hash": {"$ref": "#/$defs/sha256"},
    },
    "$defs": {"sha256": SHA},
}

LABEL_ACCESS_LEASE_SCHEMA: Mapping[str, Any] = {
    "$schema": META,
    "$id": "paperworks://validation-v2/label-access-authorization-lease-v1",
    "title": "VALIDATION V2 Label Access Authorization Lease V1",
    "type": "object",
    "additionalProperties": False,
    "required": [
        "schema", "schema_version", "prediction_bytes_sha256",
        "freeze_receipt_bytes_sha256", "authority_hash",
        "runtime_authorization_hash", "execution_context_hash", "source_commit",
        "portfolio_hash", "file_contract_hash", "state", "self_hash",
    ],
    "properties": {
        "schema": {"const": "paperworks.validation_v2.label_access_authorization_lease_v1"},
        "schema_version": {"const": "1.0.0"},
        "prediction_bytes_sha256": {"$ref": "#/$defs/sha256"},
        "freeze_receipt_bytes_sha256": {"$ref": "#/$defs/sha256"},
        "authority_hash": {"$ref": "#/$defs/sha256"},
        "runtime_authorization_hash": {"$ref": "#/$defs/sha256"},
        "execution_context_hash": {"$ref": "#/$defs/sha256"},
        "source_commit": {"type": "string", "pattern": "^[0-9a-f]{40}$"},
        "portfolio_hash": {"$ref": "#/$defs/sha256"},
        "file_contract_hash": {"$ref": "#/$defs/sha256"},
        "state": {"const": "LABEL_ACCESS_AUTHORIZED"},
        "self_hash": {"$ref": "#/$defs/sha256"},
    },
    "$defs": {"sha256": SHA},
}

COMMON_METRIC_CONTRACT_SCHEMA: Mapping[str, Any] = {
    "$schema": META,
    "$id": "paperworks://validation-v2/common-metric-contract-v1",
    "title": "VALIDATION V2 Common Metric Contract V1",
    "type": "object",
    "additionalProperties": False,
    "required": [
        "schema", "schema_version", "protocol_hash", "sampling_seconds",
        "coordinate_scope", "timestamp_validation", "event_construction",
        "event_hit_rule", "point_adjustment", "episode_construction",
        "episode_allowed_gap_seconds", "mixed_episode_policy", "normal_exposure",
        "far_formula", "zero_attack_events", "zero_normal_exposure",
        "d1_system_error_policy", "contract_hash",
    ],
    "properties": {
        "schema": {"const": "paperworks.validation_v2.common_metric_contract_v1"},
        "schema_version": {"const": "1.0.0"},
        "protocol_hash": {"$ref": "#/$defs/sha256"},
        "sampling_seconds": {"const": 1},
        "coordinate_scope": {"$ref": "#/$defs/text"},
        "timestamp_validation": {"$ref": "#/$defs/text"},
        "event_construction": {"$ref": "#/$defs/text"},
        "event_hit_rule": {"$ref": "#/$defs/text"},
        "point_adjustment": {"$ref": "#/$defs/text"},
        "episode_construction": {"$ref": "#/$defs/text"},
        "episode_allowed_gap_seconds": {"const": 0},
        "mixed_episode_policy": {"$ref": "#/$defs/text"},
        "normal_exposure": {"$ref": "#/$defs/text"},
        "far_formula": {"$ref": "#/$defs/text"},
        "zero_attack_events": {"$ref": "#/$defs/text"},
        "zero_normal_exposure": {"$ref": "#/$defs/text"},
        "d1_system_error_policy": {"$ref": "#/$defs/text"},
        "contract_hash": {"$ref": "#/$defs/sha256"},
    },
    "$defs": {"sha256": SHA, "text": TEXT},
}

COMMON_EVALUATION_BUNDLE_SCHEMA: Mapping[str, Any] = {
    "$schema": META,
    "$id": "paperworks://validation-v2/common-evaluation-bundle-v1",
    "title": "VALIDATION V2 Synthetic Common Evaluation Bundle V1",
    "type": "object",
    "additionalProperties": False,
    "required": [
        "schema", "schema_version", "execution_scope", "scientific_eligible",
        "protocol_hash", "metric_contract_hash", "result_hashes",
        "comparison_hashes", "self_hash",
    ],
    "properties": {
        "schema": {"const": "paperworks.validation_v2.common_evaluation_bundle_v1"},
        "schema_version": {"const": "1.0.0"},
        "execution_scope": {"const": "SYNTHETIC_CONTRACT_ONLY"},
        "scientific_eligible": {"const": False},
        "protocol_hash": {"$ref": "#/$defs/sha256"},
        "metric_contract_hash": {"$ref": "#/$defs/sha256"},
        "result_hashes": {"type": "array", "minItems": 1, "items": {"$ref": "#/$defs/sha256"}},
        "comparison_hashes": {"type": "array", "items": {"$ref": "#/$defs/sha256"}},
        "self_hash": {"$ref": "#/$defs/sha256"},
    },
    "$defs": {"sha256": SHA},
}

FILE_SECOND_SERIES_SCHEMA: Mapping[str, Any] = {
    "$schema": META,
    "$id": "paperworks://validation-v2/file-second-series-authority-v1",
    "title": "VALIDATION V2 File Second Series Authority V1",
    "type": "object", "additionalProperties": False,
    "required": ["schema", "schema_version", "dataset_id", "sampling_contract_hash", "coordinates", "file_rows", "self_hash"],
    "properties": {
        "schema": {"const": "paperworks.validation_v2.file_second_series_authority_v1"},
        "schema_version": {"const": "1.0.0"},
        "dataset_id": {"$ref": "#/$defs/text"},
        "sampling_contract_hash": {"$ref": "#/$defs/sha256"},
        "coordinates": {"type": "array", "minItems": 1, "items": {}},
        "file_rows": {"type": "array", "minItems": 1, "items": {}},
        "self_hash": {"$ref": "#/$defs/sha256"},
    },
    "$defs": {"sha256": SHA, "text": TEXT},
}

COMMON_ALARM_TIMELINE_SCHEMA: Mapping[str, Any] = {
    "$schema": META,
    "$id": "paperworks://validation-v2/common-alarm-timeline-v1",
    "title": "VALIDATION V2 Common Alarm Timeline V1",
    "type": "object", "additionalProperties": False,
    "required": [
        "schema", "schema_version", "method_id", "config_id", "source_prediction_sha256",
        "prediction_freeze_receipt_sha256", "adapter_id", "native_evidence_sha256",
        "file_series_hash", "protocol_hash", "metric_contract_hash", "points",
        "native_state_counts", "self_hash",
    ],
    "properties": {
        "schema": {"const": "paperworks.validation_v2.common_alarm_timeline_v1"},
        "schema_version": {"const": "1.0.0"},
        "method_id": {"$ref": "#/$defs/text"}, "config_id": {"$ref": "#/$defs/text"},
        "source_prediction_sha256": {"$ref": "#/$defs/sha256"},
        "prediction_freeze_receipt_sha256": {"$ref": "#/$defs/sha256"},
        "adapter_id": {"$ref": "#/$defs/text"}, "native_evidence_sha256": {"$ref": "#/$defs/sha256"},
        "file_series_hash": {"$ref": "#/$defs/sha256"}, "protocol_hash": {"$ref": "#/$defs/sha256"},
        "metric_contract_hash": {"$ref": "#/$defs/sha256"},
        "points": {"type": "array", "minItems": 1, "items": {}},
        "native_state_counts": {"type": "array", "items": {}},
        "self_hash": {"$ref": "#/$defs/sha256"},
    },
    "$defs": {"sha256": SHA, "text": TEXT},
}

LABEL_TIMELINE_SCHEMA: Mapping[str, Any] = {
    "$schema": META,
    "$id": "paperworks://validation-v2/label-timeline-v1",
    "title": "VALIDATION V2 Label Timeline V1",
    "type": "object", "additionalProperties": False,
    "required": ["schema", "schema_version", "dataset_id", "label_authority_sha256", "file_series_hash", "points", "self_hash"],
    "properties": {
        "schema": {"const": "paperworks.validation_v2.label_timeline_v1"},
        "schema_version": {"const": "1.0.0"},
        "dataset_id": {"$ref": "#/$defs/text"}, "label_authority_sha256": {"$ref": "#/$defs/sha256"},
        "file_series_hash": {"$ref": "#/$defs/sha256"},
        "points": {"type": "array", "minItems": 1, "items": {}},
        "self_hash": {"$ref": "#/$defs/sha256"},
    },
    "$defs": {"sha256": SHA, "text": TEXT},
}

COMMON_EVALUATION_RESULT_SCHEMA: Mapping[str, Any] = {
    "$schema": META,
    "$id": "paperworks://validation-v2/common-evaluation-result-v1",
    "title": "VALIDATION V2 Common Evaluation Result V1",
    "type": "object", "additionalProperties": False,
    "required": [
        "schema", "schema_version", "method_id", "config_id", "protocol_hash", "metric_contract_hash",
        "prediction_timeline_hash", "label_timeline_hash", "attack_events", "attack_detection",
        "alarm_seconds", "alarm_episodes", "normal_false_episodes", "normal_exposure_seconds",
        "recall", "far_per_hour", "native_state_counts", "self_hash",
    ],
    "properties": {
        "schema": {"const": "paperworks.validation_v2.common_evaluation_result_v1"},
        "schema_version": {"const": "1.0.0"},
        "method_id": {"$ref": "#/$defs/text"}, "config_id": {"$ref": "#/$defs/text"},
        "protocol_hash": {"$ref": "#/$defs/sha256"}, "metric_contract_hash": {"$ref": "#/$defs/sha256"},
        "prediction_timeline_hash": {"$ref": "#/$defs/sha256"}, "label_timeline_hash": {"$ref": "#/$defs/sha256"},
        "attack_events": {"type": "array", "items": {}}, "attack_detection": {"type": "array", "items": {}},
        "alarm_seconds": {"type": "integer"}, "alarm_episodes": {"type": "array", "items": {}},
        "normal_false_episodes": {"type": "integer"}, "normal_exposure_seconds": {"type": "integer"},
        "recall": {}, "far_per_hour": {}, "native_state_counts": {"type": "array", "items": {}},
        "self_hash": {"$ref": "#/$defs/sha256"},
    },
    "$defs": {"sha256": SHA, "text": TEXT},
}

COMMON_COMPARISON_RESULT_SCHEMA: Mapping[str, Any] = {
    "$schema": META,
    "$id": "paperworks://validation-v2/common-comparison-result-v1",
    "title": "VALIDATION V2 Common Comparison and Incremental Metric Result V1",
    "type": "object", "additionalProperties": False,
    "required": [
        "schema", "schema_version", "baseline_method_id", "candidate_method_id", "baseline_result_hash",
        "candidate_result_hash", "both", "baseline_only", "candidate_only", "neither",
        "incremental_detected_units", "incremental_false_episodes", "baseline_miss_recovery",
        "incremental_recall", "incremental_far_per_hour", "self_hash",
    ],
    "properties": {
        "schema": {"const": "paperworks.validation_v2.common_comparison_result_v1"},
        "schema_version": {"const": "1.0.0"},
        "baseline_method_id": {"$ref": "#/$defs/text"}, "candidate_method_id": {"$ref": "#/$defs/text"},
        "baseline_result_hash": {"$ref": "#/$defs/sha256"}, "candidate_result_hash": {"$ref": "#/$defs/sha256"},
        "both": {"type": "integer"}, "baseline_only": {"type": "integer"},
        "candidate_only": {"type": "integer"}, "neither": {"type": "integer"},
        "incremental_detected_units": {"type": "integer"}, "incremental_false_episodes": {"type": "integer"},
        "baseline_miss_recovery": {}, "incremental_recall": {}, "incremental_far_per_hour": {},
        "self_hash": {"$ref": "#/$defs/sha256"},
    },
    "$defs": {"sha256": SHA, "text": TEXT},
}


def _exp01_closed_schema(
    *, schema_id: str, title: str, required: tuple[str, ...], schema_token: str, version: str,
    property_overrides: Mapping[str, Any] | None = None,
) -> Mapping[str, Any]:
    properties: dict[str, Any] = {name: {} for name in required}
    properties["schema"] = {"const": schema_token}
    properties["schema_version"] = {"const": version}
    for name in required:
        if name.endswith("_hash") or name.endswith("_sha256"):
            properties[name] = {"$ref": "#/$defs/sha256"}
    if "source_commit" in properties:
        properties["source_commit"] = {"type": "string", "pattern": "^[0-9a-f]{40}$"}
    if property_overrides:
        properties.update(property_overrides)
    return {
        "$schema": META,
        "$id": schema_id,
        "title": title,
        "type": "object",
        "additionalProperties": False,
        "required": list(required),
        "properties": properties,
        "$defs": {"sha256": SHA},
    }


EXP01_PREREGISTRATION_SCHEMA = _exp01_closed_schema(
    schema_id="paperworks://validation-v2/exp01-preregistration-v1",
    title="VALIDATION V2 EXP-01 Preregistration V1",
    schema_token="paperworks.validation_v2.exp01_preregistration_v1",
    version="1.0.0",
    required=(
        "schema", "schema_version", "source_commit", "protocol_hash", "candidate_universe_hash",
        "feature_contract_hash", "data_authority_hash", "neighbor_policy_hash", "training_config_hash",
        "seeds", "primary_k", "sensitivity_k", "fit_roles", "confirmation_role", "functional_role",
        "test1_authorized", "labels_authorized", "test2_authorized", "heldout_authorized",
        "upstream_commit", "arms", "required_views", "functional_threshold", "failure_rule",
        "seed_stability_rule", "split_stability_rule", "topk_prefix_rule", "primary_mask_rule",
        "intervention_rule", "functional_inclusion_rule", "claim_boundary", "inclusion_rule",
        "preregistration_hash",
    ),
    property_overrides={
        "seeds": {"const": [11, 23, 37]},
        "primary_k": {"const": 20},
        "sensitivity_k": {"const": [10, 40]},
        "fit_roles": {"const": ["train1", "train2"]},
        "confirmation_role": {"const": "train3"},
        "functional_role": {"const": "train4"},
        "test1_authorized": {"const": False},
        "labels_authorized": {"const": False},
        "test2_authorized": {"const": False},
        "heldout_authorized": {"const": False},
        "upstream_commit": {"const": "9853899da860682669a134e4af315d036aab4eca"},
        "arms": {"const": ["META_REFERENCE", "STAT_REFERENCE", "GDN_FROZEN_SELF_ELIGIBLE", "GDN_CORRECTED_SELF_EXCLUDED"]},
        "required_views": {"const": ["TRAIN1_TRAIN2_COMBINED", "TRAIN1_ONLY", "TRAIN2_ONLY"]},
        "functional_threshold": {"const": "DELTA_GT_MAX_1E-12_OR_1E-9_TIMES_ABS_BASELINE"},
        "failure_rule": {"const": "INCOMPLETE_AUTHORITY_OR_EXECUTION_FAILS_CLOSED_NOT_NEGATIVE_EVIDENCE"},
        "seed_stability_rule": {"const": "PAIR_PRESENT_IN_AT_LEAST_TWO_OF_SEEDS_11_23_37"},
        "split_stability_rule": {"const": "PAIR_PRESENT_IN_BOTH_TRAIN1_ONLY_AND_TRAIN2_ONLY"},
        "topk_prefix_rule": {"const": "EXACT_UNPADDED_PREFIX_K_WITH_DUPLICATES_FORBIDDEN"},
        "primary_mask_rule": {"const": "CORRECTED_INTERSECT_UNIQUE_INTERSECT_SEED_STABLE_INTERSECT_SPLIT_STABLE_INTERSECT_CONFIRMED"},
        "intervention_rule": {"const": "MASK_EXACT_PRIMARY_EDGES_AND_COMPARE_HELD_NORMAL_TRAIN4_MSE_PER_SEED"},
        "functional_inclusion_rule": {"const": "POSITIVE_DELTA_IN_AT_LEAST_TWO_SEEDS_AND_POSITIVE_MEDIAN"},
        "claim_boundary": {"const": "NORMAL_DATA_CANDIDATE_GUIDANCE_NOT_CAUSALITY_OR_DETECTION_PERFORMANCE"},
        "inclusion_rule": {"const": "STABLE_UNIQUE_CONFIRMED_AND_FUNCTIONALLY_USED"},
    },
)

EXP01_RUN_AUTHORIZATION_SCHEMA = _exp01_closed_schema(
    schema_id="paperworks://validation-v2/exp01-run-authorization-v2",
    title="VALIDATION V2 EXP-01 Run Authorization V2",
    schema_token="paperworks.validation_v2.exp01_run_authorization_v2",
    version="2.0.0",
    required=(
        "schema", "schema_version", "preregistration_hash", "data_authority_hash",
        "feature_contract_hash", "candidate_universe_hash", "training_config_hash",
        "neighbor_policy_hash", "source_commit", "split_roles", "labels_authorized",
        "test1_authorized", "test2_authorized", "heldout_authorized", "authorization_hash",
    ),
    property_overrides={
        "split_roles": {"const": ["train1", "train2"]},
        "labels_authorized": {"const": False},
        "test1_authorized": {"const": False},
        "test2_authorized": {"const": False},
        "heldout_authorized": {"const": False},
    },
)

EXP01_TRAINING_INPUT_SCHEMA = _exp01_closed_schema(
    schema_id="paperworks://validation-v2/exp01-training-input-v2",
    title="VALIDATION V2 EXP-01 Authorized Training Input V2",
    schema_token="paperworks.validation_v2.exp01_authorized_training_input_v2",
    version="2.0.0",
    required=(
        "schema", "schema_version", "segments", "feature_order", "candidate_pairs",
        "data_authority_hash", "feature_contract_hash", "candidate_universe_hash", "input_hash",
    ),
    property_overrides={
        "segments": {"type": "array", "minItems": 1, "items": {"type": "array", "minItems": 1, "items": {"type": "array", "minItems": 1}}},
        "feature_order": {"type": "array", "minItems": 6, "items": {"type": "string", "minLength": 1}},
        "candidate_pairs": {"type": "array", "minItems": 1, "items": {"type": "array", "minItems": 2, "maxItems": 2, "items": {"type": "string", "minLength": 1}}},
    },
)

EXP01_SEED_RECEIPT_SCHEMA = _exp01_closed_schema(
    schema_id="paperworks://validation-v2/exp01-seed-receipt-v2",
    title="VALIDATION V2 EXP-01 Seed Run Receipt V2",
    schema_token="paperworks.validation_v2.exp01_seed_run_receipt_v2",
    version="2.0.0",
    required=(
        "schema", "schema_version", "seed", "preregistration_hash", "authorization_hash", "input_hash",
        "neighbor_policy_hash", "training_config_hash", "forward_internal_graph_hash",
        "extraction_internal_graph_hash", "selected_edges", "candidate_similarities", "epoch_count",
        "best_validation_loss", "graph_hash", "receipt_hash",
    ),
    property_overrides={
        "seed": {"enum": [11, 23, 37]},
        "selected_edges": {"type": "array", "items": {"type": "array", "minItems": 2, "maxItems": 2}},
        "candidate_similarities": {"type": "array", "items": {"type": "array", "minItems": 3, "maxItems": 3}},
        "epoch_count": {"type": "integer"},
    },
)

EXP01_SEED_BUNDLE_SCHEMA = _exp01_closed_schema(
    schema_id="paperworks://validation-v2/exp01-seed-bundle-v1",
    title="VALIDATION V2 EXP-01 Seed Bundle Receipt V1",
    schema_token="paperworks.validation_v2.exp01_seed_bundle_receipt_v1",
    version="1.0.0",
    required=(
        "schema", "schema_version", "preregistration_hash", "authorization_hash", "input_hash",
        "seeds", "seed_receipt_hashes", "seed_graph_hashes", "bundle_hash",
    ),
    property_overrides={
        "seeds": {"const": [11, 23, 37]},
        "seed_receipt_hashes": {"type": "array", "minItems": 3, "maxItems": 3, "items": {"$ref": "#/$defs/sha256"}},
        "seed_graph_hashes": {"type": "array", "minItems": 3, "maxItems": 3, "items": {"$ref": "#/$defs/sha256"}},
    },
)

EXP01_ANALYSIS_RECEIPT_SCHEMA = _exp01_closed_schema(
    schema_id="paperworks://validation-v2/exp01-analysis-receipt-v1",
    title="VALIDATION V2 EXP-01 Analysis Receipt V1",
    schema_token="paperworks.validation_v2.exp01_analysis_receipt_v1",
    version="1.0.0",
    required=(
        "schema", "schema_version", "receipt_type", "preregistration_hash", "candidate_universe_hash",
        "training_config_hash", "neighbor_policy_hash", "input_hashes", "output_hash", "receipt_hash",
    ),
    property_overrides={
        "receipt_type": {"enum": ["CHECKPOINT_SET", "PROVENANCE", "CONFIRMATION", "INTERVENTION"]},
        "input_hashes": {"type": "array", "minItems": 1, "maxItems": 3, "items": {"$ref": "#/$defs/sha256"}},
    },
)

EXP01_CONTRIBUTION_EVIDENCE_SCHEMA = _exp01_closed_schema(
    schema_id="paperworks://validation-v2/exp01-contribution-evidence-v1",
    title="VALIDATION V2 EXP-01 Contribution Evidence V1",
    schema_token="paperworks.validation_v2.exp01_contribution_evidence_v1",
    version="1.0.0",
    required=(
        "schema", "schema_version", "preregistration_hash", "candidate_universe_hash",
        "training_config_hash", "neighbor_policy_hash", "seed_run_receipt_hashes", "authority_complete",
        "execution_complete", "privacy_pass", "all_required_seeds_complete", "corrected_self_neighbor_count",
        "forward_extraction_match", "corrected_top20_pairs", "unique_pairs", "seed_stable_pairs",
        "split_stable_pairs", "confirmed_pairs", "primary_mask_pairs", "masking_delta_by_seed",
        "masking_baseline_by_seed", "checkpoint_receipt", "provenance_receipt", "confirmation_receipt",
        "intervention_receipt", "prohibited_input_used", "result_driven_change_used", "failure_reason",
        "evidence_hash",
    ),
    property_overrides={
        "seed_run_receipt_hashes": {"type": "array", "minItems": 3, "maxItems": 3, "items": {"$ref": "#/$defs/sha256"}},
        "authority_complete": {"type": "boolean"},
        "execution_complete": {"type": "boolean"},
        "privacy_pass": {"type": "boolean"},
        "all_required_seeds_complete": {"type": "boolean"},
        "corrected_self_neighbor_count": {"type": "integer"},
        "forward_extraction_match": {"type": "boolean"},
        "corrected_top20_pairs": {"type": "array", "maxItems": 20, "items": {"type": "array", "minItems": 2, "maxItems": 2}},
        "unique_pairs": {"type": "array", "items": {"type": "array", "minItems": 2, "maxItems": 2}},
        "seed_stable_pairs": {"type": "array", "items": {"type": "array", "minItems": 2, "maxItems": 2}},
        "split_stable_pairs": {"type": "array", "items": {"type": "array", "minItems": 2, "maxItems": 2}},
        "confirmed_pairs": {"type": "array", "items": {"type": "array", "minItems": 2, "maxItems": 2}},
        "primary_mask_pairs": {"type": "array", "items": {"type": "array", "minItems": 2, "maxItems": 2}},
        "masking_delta_by_seed": {"type": "array", "minItems": 3, "maxItems": 3},
        "masking_baseline_by_seed": {"type": "array", "minItems": 3, "maxItems": 3},
        "checkpoint_receipt": {"type": "object"},
        "provenance_receipt": {"type": "object"},
        "confirmation_receipt": {"type": "object"},
        "intervention_receipt": {"type": "object"},
        "prohibited_input_used": {"type": "boolean"},
        "result_driven_change_used": {"type": "boolean"},
    },
)

EMBEDDED_VALIDATION_V2_SCHEMAS: Mapping[str, Mapping[str, Any]] = {
    "common_alarm_timeline_v1.schema.json": COMMON_ALARM_TIMELINE_SCHEMA,
    "common_comparison_result_v1.schema.json": COMMON_COMPARISON_RESULT_SCHEMA,
    "common_evaluation_bundle_v1.schema.json": COMMON_EVALUATION_BUNDLE_SCHEMA,
    "common_evaluation_result_v1.schema.json": COMMON_EVALUATION_RESULT_SCHEMA,
    "common_metric_contract_v1.schema.json": COMMON_METRIC_CONTRACT_SCHEMA,
    "d1_prediction_artifact_v2.schema.json": D1_PREDICTION_SCHEMA,
    "durable_prediction_freeze_receipt_v1.schema.json": FREEZE_RECEIPT_SCHEMA,
    "label_access_authorization_lease_v1.schema.json": LABEL_ACCESS_LEASE_SCHEMA,
    "formal_v4_portfolio_authority_v1.schema.json": PORTFOLIO_SCHEMA,
    "formal_v4_runtime_authorization_v1.schema.json": RUNTIME_SCHEMA,
    "file_second_series_authority_v1.schema.json": FILE_SECOND_SERIES_SCHEMA,
    "label_timeline_v1.schema.json": LABEL_TIMELINE_SCHEMA,
    "exp01_preregistration_v1.schema.json": EXP01_PREREGISTRATION_SCHEMA,
    "exp01_run_authorization_v2.schema.json": EXP01_RUN_AUTHORIZATION_SCHEMA,
    "exp01_authorized_training_input_v2.schema.json": EXP01_TRAINING_INPUT_SCHEMA,
    "exp01_seed_run_receipt_v2.schema.json": EXP01_SEED_RECEIPT_SCHEMA,
    "exp01_seed_bundle_receipt_v1.schema.json": EXP01_SEED_BUNDLE_SCHEMA,
    "exp01_analysis_receipt_v1.schema.json": EXP01_ANALYSIS_RECEIPT_SCHEMA,
    "exp01_contribution_evidence_v1.schema.json": EXP01_CONTRIBUTION_EVIDENCE_SCHEMA,
}
