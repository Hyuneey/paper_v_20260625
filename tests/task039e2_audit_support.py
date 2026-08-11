"""Clearly synthetic fixtures for TASK-039E2-AUDIT-PREP tests."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from paperworks.v6.task039e2_audit_prep_v1 import (
    DIRECT_NUMBER_ALLOWED_SUPPLIED_ROLES,
    DIRECT_NUMBER_HIDDEN_ROLES,
    EXPECTED_ENDPOINT,
    EXPECTED_MAX_COMPLETION_TOKENS,
    EXPECTED_MODEL_SNAPSHOT,
    EXPECTED_PROVIDER,
    EXPECTED_REASONING,
    EXPECTED_TEMPERATURE,
    EXPECTED_TOP_P,
    IndependentDirectNumberAuditInputV1,
    IndependentExecutionConfigurationV1,
    IndependentFreezeHashBindingsV1,
    IndependentModelVisiblePromptV1,
    IndependentRetrievalRecordV1,
    PROMPT_HASH_FAMILIES,
    PROMPT_REQUEST_ROLES,
    build_synthetic_relation_major_schedule_v1,
    independent_hash_v1,
)


def synthetic_hash(label: str) -> str:
    return independent_hash_v1({"synthetic_fixture": label})


def make_hash_bindings() -> IndependentFreezeHashBindingsV1:
    return IndependentFreezeHashBindingsV1(
        prompt_family_hashes=tuple(
            (family, synthetic_hash(f"prompt::{family}"))
            for family in PROMPT_HASH_FAMILIES
        ),
        structured_schema_hash=synthetic_hash("structured-schema"),
        rendering_policy_hash=synthetic_hash("rendering-policy"),
        retrieval_policy_hash=synthetic_hash("retrieval-policy"),
        t0_template_hash=synthetic_hash("t0-template"),
        schedule_hash=synthetic_hash("schedule"),
        retry_policy_hash=synthetic_hash("retry-policy"),
        direct_number_role_policy_hash=synthetic_hash("direct-number-role-policy"),
    )


def make_configuration(**overrides: Any) -> IndependentExecutionConfigurationV1:
    bindings = make_hash_bindings()
    values: dict[str, Any] = {
        "provider": EXPECTED_PROVIDER,
        "endpoint": EXPECTED_ENDPOINT,
        "model": EXPECTED_MODEL_SNAPSHOT,
        "reasoning": EXPECTED_REASONING,
        "temperature": EXPECTED_TEMPERATURE,
        "top_p": EXPECTED_TOP_P,
        "max_completion_tokens": EXPECTED_MAX_COMPLETION_TOKENS,
        "seed": None,
        "stream": False,
        "store": False,
        "model_fallback": False,
        "prompt_hash_manifest_hash": bindings.prompt_hash_manifest_hash,
        "structured_schema_manifest_hash": (
            bindings.structured_schema_manifest_hash
        ),
        "rendering_policy_hash": bindings.rendering_policy_hash,
        "retrieval_policy_hash": bindings.retrieval_policy_hash,
        "t0_template_hash": bindings.t0_template_hash,
        "schedule_hash": bindings.schedule_hash,
        "retry_policy_hash": bindings.retry_policy_hash,
        "direct_number_role_policy_hash": bindings.direct_number_role_policy_hash,
    }
    values.update(overrides)
    return IndependentExecutionConfigurationV1(**values)


def generic_provider_schema() -> dict[str, Any]:
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "properties": {
            "outcome": {"type": "string", "enum": ["rule", "no_rule"]},
            "source": {
                "type": "string",
                "enum": ["SYNTHETIC_SOURCE_A", "SYNTHETIC_SOURCE_B"],
            },
            "target": {
                "type": "string",
                "enum": ["SYNTHETIC_TARGET_A", "SYNTHETIC_TARGET_B"],
            },
            "selected_delay_horizon": {"type": "integer", "enum": [5, 10]},
            "evidence_reference": {
                "type": "string",
                "pattern": "^[a-f0-9]{64}$",
            },
            "numeric_reference": {
                "type": "string",
                "pattern": "^[a-f0-9]{64}$",
            },
        },
        "required": [
            "outcome",
            "source",
            "target",
            "selected_delay_horizon",
            "evidence_reference",
            "numeric_reference",
        ],
        "additionalProperties": False,
    }


def prompt_content() -> dict[str, Any]:
    return {
        "relation_identity": "SYNTHETIC_RELATION_001",
        "evidence_bundle_hash": synthetic_hash("evidence-bundle-001"),
        "allowed_sources": ["SYNTHETIC_SOURCE_A", "SYNTHETIC_SOURCE_B"],
        "allowed_targets": ["SYNTHETIC_TARGET_A", "SYNTHETIC_TARGET_B"],
        "allowed_horizons": [5, 10],
        "structured_output_schema_hash": synthetic_hash("structured-schema"),
    }


def make_initial_prompts() -> tuple[IndependentModelVisiblePromptV1, ...]:
    configuration_hash = make_configuration().artifact_hash
    content = prompt_content()
    return tuple(
        IndependentModelVisiblePromptV1(
            relation_identity="SYNTHETIC_RELATION_001",
            request_role=role,
            configuration_hash=configuration_hash,
            model_visible_scientific_content=deepcopy(content),
        )
        for role in PROMPT_REQUEST_ROLES
    )


def make_retrieval(**overrides: Any) -> IndependentRetrievalRecordV1:
    initial = (synthetic_hash("e1-a"), synthetic_hash("e1-b"))
    values: dict[str, Any] = {
        "relation_identity": "SYNTHETIC_RELATION_001",
        "retrieval_action_number": 1,
        "initial_authorized_evidence_identities": initial,
        "retrieved_evidence_identities": (initial[1],),
        "model_visible_retrieval_content": {
            "approved_evidence": [{"identity": initial[1], "role": "context"}]
        },
    }
    values.update(overrides)
    return IndependentRetrievalRecordV1(**values)


def make_direct_number_input(**overrides: Any) -> IndependentDirectNumberAuditInputV1:
    values: dict[str, Any] = {
        "hidden_calibrated_roles": DIRECT_NUMBER_HIDDEN_ROLES,
        "supplied_nonhidden_numeric_roles": DIRECT_NUMBER_ALLOWED_SUPPLIED_ROLES,
        "calibrated_role_values": (
            ("source_step_threshold", 987.125),
            ("source_stability_tolerance", 654.375),
            ("target_noise_scale", 321.875),
        ),
        "calibrated_role_references": tuple(
            (role, synthetic_hash(f"private::{role}"))
            for role in DIRECT_NUMBER_HIDDEN_ROLES
        ),
        "model_visible_prompt": {
            "relation_identity": "SYNTHETIC_RELATION_001",
            "selected_delay_horizon": 17,
            "window_constants": {
                "source_pre_window": 3,
                "source_post_window": 4,
                "minimum_source_stability_fraction": 0.8,
                "source_refractory": 6,
                "cross_source_isolation_radius": 2,
                "target_baseline_window": 5,
                "target_response_window": 7,
            },
            "instruction": "propose the three withheld synthetic numeric roles",
        },
    }
    values.update(overrides)
    return IndependentDirectNumberAuditInputV1(**values)


def make_schedule():
    return build_synthetic_relation_major_schedule_v1(
        tuple(f"SYNTHETIC_RELATION_{index:03d}" for index in range(1, 43))
    )
