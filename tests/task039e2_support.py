"""Clearly synthetic fixtures for TASK-039E2 execution-freeze preparation."""

from __future__ import annotations

from hashlib import sha256

from paperworks.v6.task039e0_rule_construction_prep_v1 import (
    ApprovedNumericEvidenceBundleV1,
    ConfirmedRelationPrimitiveV1,
    canonical_proposal_hash_v1,
)
from paperworks.v6.task039e2_execution_freeze_prep_v1 import (
    REQUIRED_NUMERIC_ROLES,
    WINDOW_NUMERIC_ROLES,
    ApprovedRenderedNumericValueV1,
    ConstructionExecutionConfigurationV1,
    ConstructionExecutionScheduleV1,
    ConstructionEvidenceRenderingPolicyV1,
    ConstructionInputViewV1,
    ModelCapabilityReceiptV1,
    PromptTemplateContractV1,
    TransportRetryPolicyV1,
    generate_synthetic_t0_proposal_v1,
    render_construction_input_view_v1,
)


def synthetic_hash(label: str) -> str:
    return sha256(f"SYNTHETIC_ONLY::{label}".encode("utf-8")).hexdigest()


def synthetic_relation_and_bundle() -> tuple[
    ConfirmedRelationPrimitiveV1,
    ApprovedNumericEvidenceBundleV1,
]:
    relation = ConfirmedRelationPrimitiveV1(
        relation_identity="SYNTHETIC_RELATION_001",
        source="SYNTHETIC_SOURCE_01",
        source_step_direction="step_up",
        target="SYNTHETIC_TARGET_01",
        target_response_direction="increase",
        selected_delay_horizon_seconds=5,
        approved_source_threshold_reference=synthetic_hash("threshold-ref"),
        approved_source_stability_reference=synthetic_hash("stability-ref"),
        approved_target_scale_reference=synthetic_hash("scale-ref"),
        fit_evidence_reference=synthetic_hash("fit-evidence"),
        confirmation_evidence_reference=synthetic_hash("confirmation-evidence"),
    )
    window_refs = tuple(synthetic_hash(f"window-ref-{role}") for role in WINDOW_NUMERIC_ROLES)
    bundle = ApprovedNumericEvidenceBundleV1(
        relation_binding_hash=relation.binding_hash,
        source_threshold_reference=relation.approved_source_threshold_reference,
        source_stability_reference=relation.approved_source_stability_reference,
        target_scale_reference=relation.approved_target_scale_reference,
        fit_evidence_reference=relation.fit_evidence_reference,
        confirmation_evidence_reference=relation.confirmation_evidence_reference,
        preregistered_window_constant_references=window_refs,
    )
    return relation, bundle


def synthetic_rendered_values() -> tuple[ApprovedRenderedNumericValueV1, ...]:
    relation, bundle = synthetic_relation_and_bundle()
    values: dict[str, int | float] = {
        "source_step_threshold": 1000.25,
        "source_stability_tolerance": 2000.5,
        "target_noise_scale": 3000.75,
        "selected_delay_horizon": 5,
        "source_pre_window": 4001,
        "source_post_window": 4002,
        "minimum_source_stability_fraction": 4003.5,
        "source_refractory": 4004,
        "cross_source_isolation_radius": 4005,
        "target_baseline_window": 4006,
        "target_response_window": 4007,
    }
    references = {
        "source_step_threshold": bundle.source_threshold_reference,
        "source_stability_tolerance": bundle.source_stability_reference,
        "target_noise_scale": bundle.target_scale_reference,
        "selected_delay_horizon": synthetic_hash("selected-horizon-ref"),
        **{
            role: reference
            for role, reference in zip(
                WINDOW_NUMERIC_ROLES,
                bundle.preregistered_window_constant_references,
                strict=True,
            )
        },
    }
    origins = {
        "source_step_threshold": synthetic_hash("d1-source-parameter"),
        "source_stability_tolerance": synthetic_hash("d1-source-parameter"),
        "target_noise_scale": synthetic_hash("d1-target-parameter"),
        "selected_delay_horizon": relation.fit_evidence_reference,
        **{role: synthetic_hash("d0-window-policy") for role in WINDOW_NUMERIC_ROLES},
    }
    return tuple(
        ApprovedRenderedNumericValueV1(
            numeric_role=role,
            numeric_value=values[role],
            numeric_reference=references[role],
            evidence_origin_reference=origins[role],
        )
        for role in REQUIRED_NUMERIC_ROLES
    )


def synthetic_view() -> ConstructionInputViewV1:
    relation, bundle = synthetic_relation_and_bundle()
    return render_construction_input_view_v1(
        relation=relation,
        numeric_evidence=bundle,
        approved_values=synthetic_rendered_values(),
        bounded_semantic_metadata=(
            ("process_scope", "SYNTHETIC_PROCESS"),
            ("relation_semantics", "SYNTHETIC_DELAYED_RESPONSE"),
        ),
    )


def synthetic_prompt_template(family: str) -> PromptTemplateContractV1:
    permissions = {
        "T1": (True, False, False, False),
        "T1-B": (True, False, False, False),
        "T2_CALL_1": (True, False, False, False),
        "T2_FOLLOWUP": (False, True, True, True),
        "T1-DIRECT-NUMBER": (True, False, False, False),
    }[family]
    return PromptTemplateContractV1(
        prompt_family=family,
        template_version=f"SYNTHETIC_{family.replace('-', '_')}_V1",
        template_hash=synthetic_hash(f"template-{family}"),
        structured_output_schema_hash=synthetic_hash("structured-schema"),
        initial_scientific_content=permissions[0],
        verifier_feedback_allowed=permissions[1],
        targeted_retrieval_allowed=permissions[2],
        previous_proposal_hash_allowed=permissions[3],
    )


def synthetic_capability_receipt() -> ModelCapabilityReceiptV1:
    return ModelCapabilityReceiptV1(
        provider_identifier="SYNTHETIC_PROVIDER",
        model_identifier="SYNTHETIC_MODEL_VERSION_001",
        stable_explicit_model_version=True,
        structured_schema_output_supported=True,
        temperature_control_supported=True,
        deterministic_decoding_supported=False,
        exposed_seed_control_supported=True,
        stateless_independent_calls_supported=True,
        maximum_input_tokens=16000,
        maximum_output_tokens=2000,
        required_evidence_envelope_tokens=4000,
        required_output_tokens=1000,
        unsupported_capabilities=(),
        capability_evidence_reference=synthetic_hash("capability-evidence"),
    )


def synthetic_configuration_and_schedule() -> tuple[
    ConstructionExecutionConfigurationV1,
    ConstructionExecutionScheduleV1,
]:
    capability = synthetic_capability_receipt()
    retry_policy = TransportRetryPolicyV1()
    common = {
        "provider_identifier": capability.provider_identifier,
        "exact_model_identifier": capability.model_identifier,
        "model_capability_receipt_hash": capability.artifact_hash,
        "prompt_template_version": "SYNTHETIC_PROMPT_V1",
        "prompt_template_hash": synthetic_hash("all-prompt-templates"),
        "structured_output_schema_hash": synthetic_hash("structured-schema"),
        "temperature": 0.0,
        "top_p": 1.0,
        "maximum_output_tokens": 1000,
        "seed_value": 17,
        "seed_policy": "provider_exposed_fixed_seed",
        "stateless_calls_required": True,
        "call_timeout_seconds": 30,
        "transport_retry_policy_hash": retry_policy.artifact_hash,
        "scientific_generation_budget_hash": synthetic_hash("e0-budget"),
        "construction_evidence_rendering_policy_hash": ConstructionEvidenceRenderingPolicyV1().artifact_hash,
    }
    provisional = ConstructionExecutionConfigurationV1(
        **common,
        execution_schedule_hash=synthetic_hash("provisional-schedule"),
    )
    schedule = ConstructionExecutionScheduleV1(
        relation_identities=tuple(
            f"SYNTHETIC_RELATION_{index:03d}" for index in range(42)
        ),
        configuration_hash=provisional.configuration_binding_hash,
        scientific_generation_budget_hash=common[
            "scientific_generation_budget_hash"
        ],
    )
    configuration = ConstructionExecutionConfigurationV1(
        **common,
        execution_schedule_hash=schedule.artifact_hash,
    )
    return configuration, schedule


def synthetic_t0_proposal() -> dict[str, object]:
    relation, bundle = synthetic_relation_and_bundle()
    return generate_synthetic_t0_proposal_v1(
        view=synthetic_view(),
        relation=relation,
        numeric_evidence=bundle,
        budget_policy_hash=synthetic_hash("e0-budget"),
    )


def synthetic_provider_proposal() -> dict[str, object]:
    proposal = synthetic_t0_proposal()
    proposal["construction_arm"] = "T1"
    proposal["construction_provenance_hash"] = synthetic_hash(
        "synthetic-provider-provenance"
    )
    proposal["proposal_hash"] = canonical_proposal_hash_v1(proposal)
    return proposal
