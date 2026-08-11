"""Clearly synthetic fixtures for the independent E1 audit preparation."""

from __future__ import annotations

from hashlib import sha256

from paperworks.v6.task039e1_audit_prep_v1 import (
    NUMERIC_ROLES,
    ROLE_ORIGINS,
    WINDOW_ROLES,
    IndependentApprovedNumericBundleV1,
    IndependentNumericBindingV1,
    IndependentPrivateConstructionEvidenceV1,
    IndependentPublicManifestEntryV1,
    IndependentPublicRelationPrimitiveV1,
    PublicWindowProtocolConstantV1,
    SyntheticConstructionEvidenceAuditDatasetV1,
    independent_cohort_identity_list_hash_v1,
    independent_numeric_reference_v1,
)


def synthetic_hash(label: str) -> str:
    return sha256(f"SYNTHETIC_ONLY::{label}".encode("utf-8")).hexdigest()


def make_relation_fixture(
    index: int = 0,
) -> tuple[
    IndependentPublicRelationPrimitiveV1,
    IndependentPrivateConstructionEvidenceV1,
    IndependentApprovedNumericBundleV1,
    IndependentPublicManifestEntryV1,
]:
    pair_index = index // 2 if index < 38 else 19 + (index - 38)
    relation_binding_hash = synthetic_hash(f"relation-binding-{index}")
    source_parameter_hash = synthetic_hash(f"source-parameter-{index}")
    target_parameter_hash = synthetic_hash(f"target-parameter-{index}")
    d1_hash = synthetic_hash(f"d1-directional-evidence-{index}")
    d2_hash = synthetic_hash(f"d2-confirmation-evidence-{index}")
    window_hash = synthetic_hash("d0-window-constant-bundle")
    horizon = (1, 5, 10, 30, 60)[index % 5]
    primitive = IndependentPublicRelationPrimitiveV1(
        relation_identity=f"SYNTHETIC_RELATION_{index:03d}",
        pair_context_identity=f"SYNTHETIC_PAIR_{pair_index:02d}",
        source=f"SYNTHETIC_SOURCE_{pair_index:02d}",
        source_step_direction="step_up" if index % 2 == 0 else "step_down",
        target=f"SYNTHETIC_TARGET_{pair_index:02d}",
        target_response_direction="increase" if index % 3 else "decrease",
        selected_delay_horizon=horizon,
        relation_binding_hash=relation_binding_hash,
        d1_directional_record_hash=d1_hash,
        d2_confirmation_record_hash=d2_hash,
    )
    values: dict[str, int | float] = {
        "source_step_threshold": 1000.25 + index,
        "source_stability_tolerance": 2000.5 + index,
        "target_noise_scale": 3000.75 + index,
        "selected_delay_horizon": horizon,
        "source_pre_window": 4001,
        "source_post_window": 4002,
        "minimum_source_stability_fraction": 4003.5,
        "source_refractory": 4004,
        "cross_source_isolation_radius": 4005,
        "target_baseline_window": 4006,
        "target_response_window": 4007,
    }
    bindings = tuple(
        IndependentNumericBindingV1(
            relation_binding_hash=relation_binding_hash,
            numeric_role=role,
            numeric_value=values[role],
            value_origin=ROLE_ORIGINS[role],
            source_parameter_record_hash=source_parameter_hash,
            target_parameter_record_hash=target_parameter_hash,
            d1_evidence_record_hash=d1_hash,
            d2_evidence_record_hash=d2_hash,
            window_constant_bundle_hash=window_hash,
            numeric_reference=independent_numeric_reference_v1(
                numeric_role=role,
                numeric_value=values[role],
                value_origin=ROLE_ORIGINS[role],
                source_parameter_record_hash=source_parameter_hash,
                target_parameter_record_hash=target_parameter_hash,
                d1_evidence_record_hash=d1_hash,
                d2_evidence_record_hash=d2_hash,
                window_constant_bundle_hash=window_hash,
            ),
        )
        for role in NUMERIC_ROLES
    )
    private = IndependentPrivateConstructionEvidenceV1(
        relation_identity=primitive.relation_identity,
        pair_context_identity=primitive.pair_context_identity,
        relation_binding_hash=relation_binding_hash,
        source=primitive.source,
        source_step_direction=primitive.source_step_direction,
        target=primitive.target,
        target_response_direction=primitive.target_response_direction,
        selected_delay_horizon=horizon,
        source_parameter_record_hash=source_parameter_hash,
        target_parameter_record_hash=target_parameter_hash,
        d1_evidence_record_hash=d1_hash,
        d2_evidence_record_hash=d2_hash,
        window_constant_bundle_hash=window_hash,
        confirmation_status="calibration_confirmed",
        numeric_bindings=bindings,
    )
    by_role = {item.numeric_role: item for item in bindings}
    bundle = IndependentApprovedNumericBundleV1(
        relation_binding_hash=relation_binding_hash,
        source_threshold_reference=by_role["source_step_threshold"].numeric_reference,
        source_stability_reference=by_role[
            "source_stability_tolerance"
        ].numeric_reference,
        target_scale_reference=by_role["target_noise_scale"].numeric_reference,
        selected_horizon_reference=by_role[
            "selected_delay_horizon"
        ].numeric_reference,
        window_constant_references=tuple(
            by_role[role].numeric_reference for role in WINDOW_ROLES
        ),
        d1_evidence_record_hash=d1_hash,
        d2_evidence_record_hash=d2_hash,
    )
    manifest = IndependentPublicManifestEntryV1(
        relation_identity=primitive.relation_identity,
        pair_context_identity=primitive.pair_context_identity,
        relation_binding_hash=relation_binding_hash,
        source=primitive.source,
        source_step_direction=primitive.source_step_direction,
        target=primitive.target,
        target_response_direction=primitive.target_response_direction,
        selected_delay_horizon=horizon,
        private_evidence_record_hash=private.artifact_hash,
        approved_numeric_roles=NUMERIC_ROLES,
        source_parameter_record_hash=source_parameter_hash,
        target_parameter_record_hash=target_parameter_hash,
        d1_evidence_record_hash=d1_hash,
        d2_evidence_record_hash=d2_hash,
        window_constant_bundle_hash=window_hash,
        public_window_protocol_constants=tuple(
            PublicWindowProtocolConstantV1(role, values[role])
            for role in WINDOW_ROLES
        ),
    )
    return primitive, private, bundle, manifest


def make_exact_synthetic_dataset() -> SyntheticConstructionEvidenceAuditDatasetV1:
    fixtures = tuple(make_relation_fixture(index) for index in range(42))
    primitives = tuple(item[0] for item in fixtures)
    return SyntheticConstructionEvidenceAuditDatasetV1(
        e0_cohort_identity_list_hash=independent_cohort_identity_list_hash_v1(
            primitives
        ),
        public_relation_primitives=primitives,
        private_evidence_records=tuple(item[1] for item in fixtures),
        approved_numeric_bundles=tuple(item[2] for item in fixtures),
        public_manifest_entries=tuple(item[3] for item in fixtures),
    )
