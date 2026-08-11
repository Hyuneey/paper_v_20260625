"""Clearly synthetic fixtures for TASK-039E3-PREP tests."""

from __future__ import annotations

from paperworks.v6.common import stable_hash_v1
from paperworks.v6.task039e0_rule_construction_prep_v1 import (
    ApprovedNumericEvidenceBundleV1,
    ConfirmedRelationPrimitiveV1,
)
from paperworks.v6.task039e2_execution_configuration_v1 import (
    CALIBRATED_NUMERIC_ROLES,
    WINDOW_NUMERIC_ROLES,
    ProviderProposalCoreV1,
    generate_synthetic_t0_core_v1,
)
from paperworks.v6.task039e3_execution_prep_v1 import (
    SyntheticNumericBindingV1,
    SyntheticPrivateConstructionEvidenceV1,
)


def synthetic_hash(label: str) -> str:
    return stable_hash_v1({"synthetic_fixture": label})


def make_evidence(index: int = 1) -> SyntheticPrivateConstructionEvidenceV1:
    relation_identity = f"SYNTHETIC_RELATION_{index:03d}"
    source = f"SYNTHETIC_SOURCE_{index:03d}"
    target = f"SYNTHETIC_TARGET_{index:03d}"
    refs = {
        "source_step_threshold": synthetic_hash(f"{index}:threshold"),
        "source_stability_tolerance": synthetic_hash(f"{index}:tolerance"),
        "target_noise_scale": synthetic_hash(f"{index}:target-scale"),
    }
    fit_hash = synthetic_hash(f"{index}:fit")
    confirmation_hash = synthetic_hash(f"{index}:confirmation")
    relation = ConfirmedRelationPrimitiveV1(
        relation_identity=relation_identity,
        source=source,
        source_step_direction="step_up" if index % 2 else "step_down",
        target=target,
        target_response_direction="increase" if index % 2 else "decrease",
        selected_delay_horizon_seconds=(1, 5, 10, 30, 60)[(index - 1) % 5],
        approved_source_threshold_reference=refs["source_step_threshold"],
        approved_source_stability_reference=refs[
            "source_stability_tolerance"
        ],
        approved_target_scale_reference=refs["target_noise_scale"],
        fit_evidence_reference=fit_hash,
        confirmation_evidence_reference=confirmation_hash,
    )
    window_refs = tuple(
        synthetic_hash(f"{index}:window:{role}") for role in WINDOW_NUMERIC_ROLES
    )
    numeric_evidence = ApprovedNumericEvidenceBundleV1(
        relation_binding_hash=relation.binding_hash,
        source_threshold_reference=refs["source_step_threshold"],
        source_stability_reference=refs["source_stability_tolerance"],
        target_scale_reference=refs["target_noise_scale"],
        fit_evidence_reference=fit_hash,
        confirmation_evidence_reference=confirmation_hash,
        preregistered_window_constant_references=window_refs,
    )
    roles = CALIBRATED_NUMERIC_ROLES + WINDOW_NUMERIC_ROLES
    values = (987.125, 654.375, 321.875, 3, 4, 0.8, 6, 2, 5, 7)
    references = (
        refs["source_step_threshold"],
        refs["source_stability_tolerance"],
        refs["target_noise_scale"],
    ) + window_refs
    bindings = tuple(
        SyntheticNumericBindingV1(
            numeric_role=role,
            value=value,
            reference=reference,
            evidence_identity=f"SYNTHETIC_EVIDENCE_{index:03d}_{slot:02d}",
        )
        for slot, (role, value, reference) in enumerate(
            zip(roles, values, references), start=1
        )
    )
    return SyntheticPrivateConstructionEvidenceV1(
        fixture_identity=f"SYNTHETIC_PRIVATE_E1_FIXTURE_{index:03d}",
        relation=relation,
        numeric_evidence=numeric_evidence,
        numeric_bindings=bindings,
        approved_evidence_identities=tuple(
            binding.evidence_identity for binding in bindings
        ),
        semantic_process_metadata={
            "process_identity": "SYNTHETIC_PROCESS",
            "relation_semantics": "SYNTHETIC_DELAYED_RESPONSE",
        },
    )


def valid_core(evidence: SyntheticPrivateConstructionEvidenceV1) -> ProviderProposalCoreV1:
    return generate_synthetic_t0_core_v1(evidence.render_view().to_dict())


def valid_core_document(
    evidence: SyntheticPrivateConstructionEvidenceV1,
) -> dict[str, object]:
    return valid_core(evidence).to_dict()


def capability_payload(*, model: str = "gpt-5.4-2026-03-05") -> dict[str, object]:
    return {"model_snapshot": model, "structured_output_supported": True}


def direct_number_payload(
    threshold: float = 987.125,
    tolerance: float = 654.375,
    target_scale: float = 321.875,
) -> dict[str, float]:
    return {
        "source_step_threshold": threshold,
        "source_stability_tolerance": tolerance,
        "target_noise_scale": target_scale,
    }
