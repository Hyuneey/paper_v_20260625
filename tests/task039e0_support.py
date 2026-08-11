"""Clearly synthetic factories for TASK-039E0-PREP tests."""

from __future__ import annotations

from typing import Any

from paperworks.v6.task039e0_rule_construction_prep_v1 import (
    ApprovedNumericEvidenceBundleV1,
    ConfirmedRelationPrimitiveV1,
    FairGenerationBudgetPolicyV1,
    FROZEN_ARM_PROTOCOLS,
    ProposalConstructionProvenanceV1,
    canonical_proposal_hash_v1,
    prepare_rule_proposal_envelope_v1,
)
from paperworks.v6.common import stable_hash_v1
from paperworks.v6.outcomes_v1 import ConstructionArmV1


def synthetic_digest(label: str) -> str:
    return stable_hash_v1({"synthetic_task039e0_fixture": label})


def synthetic_relation(**overrides: Any) -> ConfirmedRelationPrimitiveV1:
    values: dict[str, Any] = {
        "relation_identity": "SYNTHETIC_RELATION_001",
        "source": "SYNTH_ACTUATOR_A",
        "source_step_direction": "step_up",
        "target": "SYNTH_SENSOR_B",
        "target_response_direction": "increase",
        "selected_delay_horizon_seconds": 5,
        "approved_source_threshold_reference": synthetic_digest(
            "fake-source-threshold"
        ),
        "approved_source_stability_reference": synthetic_digest(
            "fake-source-stability"
        ),
        "approved_target_scale_reference": synthetic_digest(
            "fake-target-scale"
        ),
        "fit_evidence_reference": synthetic_digest("fake-fit-evidence"),
        "confirmation_evidence_reference": synthetic_digest(
            "fake-confirmation-evidence"
        ),
    }
    values.update(overrides)
    return ConfirmedRelationPrimitiveV1(**values)


def synthetic_numeric_evidence(
    relation: ConfirmedRelationPrimitiveV1 | None = None,
    **overrides: Any,
) -> ApprovedNumericEvidenceBundleV1:
    item = relation or synthetic_relation()
    values: dict[str, Any] = {
        "relation_binding_hash": item.binding_hash,
        "source_threshold_reference": (
            item.approved_source_threshold_reference
        ),
        "source_stability_reference": (
            item.approved_source_stability_reference
        ),
        "target_scale_reference": item.approved_target_scale_reference,
        "fit_evidence_reference": item.fit_evidence_reference,
        "confirmation_evidence_reference": (
            item.confirmation_evidence_reference
        ),
        "preregistered_window_constant_references": (
            synthetic_digest("fake-pre-window-constant"),
            synthetic_digest("fake-response-window-constant"),
        ),
    }
    values.update(overrides)
    return ApprovedNumericEvidenceBundleV1(**values)


def synthetic_budget(**overrides: Any) -> FairGenerationBudgetPolicyV1:
    values: dict[str, Any] = {
        "policy_id": "SYNTHETIC_FAIR_BUDGET_V1",
        "t1b_total_generation_calls": 3,
        "t2_maximum_total_generation_calls": 3,
    }
    values.update(overrides)
    return FairGenerationBudgetPolicyV1(**values)


def synthetic_provenance(
    *,
    arm: ConstructionArmV1,
    evidence: ApprovedNumericEvidenceBundleV1,
    budget: FairGenerationBudgetPolicyV1,
    **overrides: Any,
) -> ProposalConstructionProvenanceV1:
    protocol = next(item for item in FROZEN_ARM_PROTOCOLS if item.arm is arm)
    values: dict[str, Any] = {
        "construction_arm": arm,
        "arm_protocol_hash": protocol.protocol_hash,
        "budget_policy_hash": budget.artifact_hash,
        "evidence_bundle_hash": evidence.artifact_hash,
        "prompt_template_version": (
            "SYNTHETIC_T0_TEMPLATE_V1"
            if arm is ConstructionArmV1.T0
            else "SYNTHETIC_CONSTRAINED_PROMPT_V1"
        ),
        "execution_state": "synthetic_preparation",
        "future_call_record_refs": (),
        "model_identifier": (
            "not_applicable"
            if arm is ConstructionArmV1.T0
            else "synthetic_model_not_called"
        ),
        "provider_identifier": (
            "not_applicable"
            if arm is ConstructionArmV1.T0
            else "synthetic_provider_not_called"
        ),
    }
    values.update(overrides)
    return ProposalConstructionProvenanceV1(**values)


def synthetic_proposal(
    *,
    arm: ConstructionArmV1 = ConstructionArmV1.T0,
    relation: ConfirmedRelationPrimitiveV1 | None = None,
    evidence: ApprovedNumericEvidenceBundleV1 | None = None,
    budget: FairGenerationBudgetPolicyV1 | None = None,
) -> tuple[
    dict[str, Any],
    ConfirmedRelationPrimitiveV1,
    ApprovedNumericEvidenceBundleV1,
    FairGenerationBudgetPolicyV1,
    ProposalConstructionProvenanceV1,
]:
    relation_item = relation or synthetic_relation()
    evidence_item = evidence or synthetic_numeric_evidence(relation_item)
    budget_item = budget or synthetic_budget()
    provenance = synthetic_provenance(
        arm=arm, evidence=evidence_item, budget=budget_item
    )
    proposal = prepare_rule_proposal_envelope_v1(
        relation=relation_item,
        numeric_evidence=evidence_item,
        provenance=provenance,
    )
    return proposal, relation_item, evidence_item, budget_item, provenance


def rehash_proposal(proposal: dict[str, Any]) -> None:
    proposal["proposal_hash"] = canonical_proposal_hash_v1(proposal)


__all__ = [
    "rehash_proposal",
    "synthetic_budget",
    "synthetic_digest",
    "synthetic_numeric_evidence",
    "synthetic_proposal",
    "synthetic_provenance",
    "synthetic_relation",
]
