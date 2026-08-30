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

EMBEDDED_VALIDATION_V2_SCHEMAS: Mapping[str, Mapping[str, Any]] = {
    "formal_v4_portfolio_authority_v1.schema.json": PORTFOLIO_SCHEMA,
    "formal_v4_runtime_authorization_v1.schema.json": RUNTIME_SCHEMA,
}
