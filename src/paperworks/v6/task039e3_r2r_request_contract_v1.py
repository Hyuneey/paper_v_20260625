"""Offline request-contract remediation for the TASK-039E3 R2R cohort.

The provider-facing V2 schema deliberately performs only structured
serialization and basic type/enum validation.  Project-owned deterministic
validity remains the scientific admissibility authority after parsing.
"""

from __future__ import annotations

from hashlib import sha256
from typing import Any, Mapping, Sequence

from paperworks.v6.common import freeze_json, stable_hash_v1
from paperworks.v6.task039e2_execution_configuration_v1 import (
    DIRECT_NUMBER_PROVIDER_SCHEMA_V1,
    MAIN_PROVIDER_SCHEMA_V1,
    WINDOW_NUMERIC_ROLES,
    build_chat_completions_request_body_v1,
    render_t2_followup_model_content_v1,
)
from paperworks.v6.task039e3_execution_prep_v1 import (
    ConstructionInputViewV1,
    FrozenProviderRequestV1,
    build_direct_number_request_v1,
    render_main_construction_input_v1,
)


RECOVERY_MAIN_PROVIDER_SCHEMA_V2: Mapping[str, Any] = freeze_json(
    {
        "type": "object",
        "additionalProperties": False,
        "required": list(MAIN_PROVIDER_SCHEMA_V1["required"]),
        "properties": {
            "dsl_family": {
                "type": "string",
                "enum": ["canonical_delayed_response_rule_v1_candidate"],
            },
            "relation_identity": {"type": "string"},
            "source": {"type": "string"},
            "source_step_direction": {
                "type": "string",
                "enum": ["step_down", "step_up"],
            },
            "target": {"type": "string"},
            "target_response_direction": {
                "type": "string",
                "enum": ["decrease", "increase"],
            },
            "selected_delay_horizon_seconds": {
                "type": "integer",
                "enum": [1, 5, 10, 30, 60],
            },
            "source_threshold_reference": {"type": "string"},
            "source_stability_reference": {"type": "string"},
            "target_scale_reference": {"type": "string"},
            "window_constant_references": {
                "type": "object",
                "additionalProperties": False,
                "required": list(WINDOW_NUMERIC_ROLES),
                "properties": {
                    role: {"type": "string"} for role in WINDOW_NUMERIC_ROLES
                },
            },
            "variables": {
                "type": "array",
                "items": {"type": "string"},
            },
            "runtime_logic_family": {
                "type": "string",
                "enum": ["missing_expected_delayed_response"],
            },
        },
    }
)

RECOVERY_MAIN_PROVIDER_SCHEMA_V2_HASH = (
    "bcbc9debc32ec9e4b02d5781c7f8b512023752ccb90f60154648bb5d9de67aa1"
)
ORIGINAL_MAIN_PROVIDER_SCHEMA_V1_HASH = (
    "92c628faf78e5ebdcfc3ec2dbeb9daa42b6beff0875cbf226c87c2f2c43cc216"
)
DIRECT_NUMBER_PROVIDER_SCHEMA_V1_HASH = (
    "b1b91bf27fd191da57984be625a2547e4e5ee96a0aca52535df071af92bfd6ca"
)
RECOVERY_MAIN_PROVIDER_SCHEMA_NAME_V2 = "recovery_provider_proposal_core_v2"
DIRECT_NUMBER_SCHEMA_POLICY = "UNCHANGED"


def _text_hash(value: str) -> str:
    return sha256(value.encode("utf-8")).hexdigest()


def assert_r2r_request_contract_v1() -> None:
    """Fail closed if the frozen V1 or recovery V2 schema identities drift."""

    if stable_hash_v1(MAIN_PROVIDER_SCHEMA_V1) != ORIGINAL_MAIN_PROVIDER_SCHEMA_V1_HASH:
        raise ValueError("original main provider schema V1 differs")
    if (
        stable_hash_v1(RECOVERY_MAIN_PROVIDER_SCHEMA_V2)
        != RECOVERY_MAIN_PROVIDER_SCHEMA_V2_HASH
    ):
        raise ValueError("recovery main provider schema V2 differs")
    if (
        stable_hash_v1(DIRECT_NUMBER_PROVIDER_SCHEMA_V1)
        != DIRECT_NUMBER_PROVIDER_SCHEMA_V1_HASH
    ):
        raise ValueError("direct-number provider schema V1 differs")


def _build_r2r_main_request_v1(
    *, purpose: str, model_visible_content: str
) -> FrozenProviderRequestV1:
    assert_r2r_request_contract_v1()
    body = build_chat_completions_request_body_v1(
        model_visible_content=model_visible_content,
        provider_schema=RECOVERY_MAIN_PROVIDER_SCHEMA_V2,
        schema_name=RECOVERY_MAIN_PROVIDER_SCHEMA_NAME_V2,
    )
    return FrozenProviderRequestV1(
        purpose=purpose,
        request_body=body,
        model_visible_content_hash=_text_hash(model_visible_content),
        provider_schema_hash=RECOVERY_MAIN_PROVIDER_SCHEMA_V2_HASH,
        schema_name=RECOVERY_MAIN_PROVIDER_SCHEMA_NAME_V2,
    )


def build_r2r_main_request_v1(
    view: ConstructionInputViewV1,
) -> FrozenProviderRequestV1:
    """Build the shared T1, T1-B, and initial-T2 recovery request."""

    return _build_r2r_main_request_v1(
        purpose="main_initial",
        model_visible_content=render_main_construction_input_v1(view),
    )


def build_r2r_t2_followup_request_v1(
    *,
    view: ConstructionInputViewV1,
    verifier_issue_codes: Sequence[str],
    affected_fields: Sequence[str],
    previous_proposal_hash: str,
    retrieved_evidence: Mapping[str, Any] | None,
) -> FrozenProviderRequestV1:
    """Build a T2 follow-up with the unchanged prompt and recovery V2 schema."""

    content = render_t2_followup_model_content_v1(
        original_view=view.to_dict(),
        verifier_issue_codes=verifier_issue_codes,
        affected_fields=affected_fields,
        previous_proposal_hash=previous_proposal_hash,
        retrieved_evidence=retrieved_evidence,
    )
    return _build_r2r_main_request_v1(
        purpose="t2_followup",
        model_visible_content=content,
    )


def build_r2r_direct_number_request_v1(
    view: ConstructionInputViewV1,
) -> FrozenProviderRequestV1:
    """Preserve the frozen direct-number V1 request without modification."""

    assert_r2r_request_contract_v1()
    return build_direct_number_request_v1(view)


assert_r2r_request_contract_v1()


__all__ = [
    "DIRECT_NUMBER_PROVIDER_SCHEMA_V1_HASH",
    "DIRECT_NUMBER_SCHEMA_POLICY",
    "ORIGINAL_MAIN_PROVIDER_SCHEMA_V1_HASH",
    "RECOVERY_MAIN_PROVIDER_SCHEMA_NAME_V2",
    "RECOVERY_MAIN_PROVIDER_SCHEMA_V2",
    "RECOVERY_MAIN_PROVIDER_SCHEMA_V2_HASH",
    "assert_r2r_request_contract_v1",
    "build_r2r_direct_number_request_v1",
    "build_r2r_main_request_v1",
    "build_r2r_t2_followup_request_v1",
]
