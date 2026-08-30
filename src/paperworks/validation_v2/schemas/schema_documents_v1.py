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

EMBEDDED_VALIDATION_V2_SCHEMAS: Mapping[str, Mapping[str, Any]] = {
    "d1_prediction_artifact_v2.schema.json": D1_PREDICTION_SCHEMA,
    "durable_prediction_freeze_receipt_v1.schema.json": FREEZE_RECEIPT_SCHEMA,
    "label_access_authorization_lease_v1.schema.json": LABEL_ACCESS_LEASE_SCHEMA,
    "formal_v4_portfolio_authority_v1.schema.json": PORTFOLIO_SCHEMA,
    "formal_v4_runtime_authorization_v1.schema.json": RUNTIME_SCHEMA,
}
