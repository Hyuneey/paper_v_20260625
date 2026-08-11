"""Authoritative E0 deterministic validity adapter bound to budget V2."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from paperworks.v6.common import V6_FOUNDATION_SCHEMA_VERSION, require_sha256, stable_hash_v1
from paperworks.v6.task039e0_rule_construction_prep_v1 import (
    ApprovedNumericEvidenceBundleV1,
    ConfirmedRelationPrimitiveV1,
    ProposalConstructionProvenanceV1,
)
from paperworks.v6.task039e0_rule_construction_protocol_v1 import (
    FairGenerationBudgetPolicyV2,
    TASK039E0ProtocolError,
    validity_issue_action_map_v1,
)
from paperworks.v6.task039e0_validity_v1 import verify_prepared_rule_proposal_v1


VERIFIER_VERSION = "task039e0_validity_v2"


@dataclass(frozen=True)
class ValidityIssueV2:
    code: str
    field: str
    repairability: str
    t2_action_class: str

    def to_dict(self) -> dict[str, str]:
        return {
            "code": self.code,
            "field": self.field,
            "repairability": self.repairability,
            "t2_action_class": self.t2_action_class,
        }


@dataclass(frozen=True)
class PreparedValidityResultV2:
    proposal_hash: str
    relation_binding_hash: str
    evidence_bundle_hash: str
    construction_provenance_hash: str
    budget_policy_hash: str
    status: str
    issues: tuple[ValidityIssueV2, ...]
    verifier_version: str = VERIFIER_VERSION
    project_owned_deterministic_code: bool = True
    label_input_used: bool = False
    utility_input_used: bool = False
    llm_chain_of_thought_used: bool = False
    canonical_rule_materialized: bool = False
    validity_authority_granted: bool = False
    runtime_authority_granted: bool = False

    def __post_init__(self) -> None:
        for name in (
            "proposal_hash", "relation_binding_hash", "evidence_bundle_hash",
            "construction_provenance_hash", "budget_policy_hash",
        ):
            require_sha256(getattr(self, name), name)
        if self.verifier_version != VERIFIER_VERSION:
            raise TASK039E0ProtocolError("validity V2 version differs")
        if self.status not in {"admissible", "rejected"}:
            raise TASK039E0ProtocolError("validity V2 status differs")
        if (self.status == "admissible") == bool(self.issues):
            raise TASK039E0ProtocolError("validity V2 issue/status contract differs")
        if self.project_owned_deterministic_code is not True:
            raise TASK039E0ProtocolError("validity V2 must be deterministic project code")
        if any(
            (
                self.label_input_used, self.utility_input_used,
                self.llm_chain_of_thought_used, self.canonical_rule_materialized,
                self.validity_authority_granted, self.runtime_authority_granted,
            )
        ):
            raise TASK039E0ProtocolError("validity V2 cannot grant scientific authority")

    def _content_dict(self) -> dict[str, Any]:
        return {
            "schema_version": V6_FOUNDATION_SCHEMA_VERSION,
            "artifact_type": "task039e0_prepared_validity_result_v2",
            "proposal_hash": self.proposal_hash,
            "relation_binding_hash": self.relation_binding_hash,
            "evidence_bundle_hash": self.evidence_bundle_hash,
            "construction_provenance_hash": self.construction_provenance_hash,
            "budget_policy_hash": self.budget_policy_hash,
            "status": self.status,
            "issues": [item.to_dict() for item in self.issues],
            "verifier_version": self.verifier_version,
            "project_owned_deterministic_code": self.project_owned_deterministic_code,
            "label_input_used": self.label_input_used,
            "utility_input_used": self.utility_input_used,
            "llm_chain_of_thought_used": self.llm_chain_of_thought_used,
            "canonical_rule_materialized": self.canonical_rule_materialized,
            "validity_authority_granted": self.validity_authority_granted,
            "runtime_authority_granted": self.runtime_authority_granted,
        }

    @property
    def artifact_hash(self) -> str:
        return stable_hash_v1(self._content_dict())

    def to_dict(self) -> dict[str, Any]:
        result = self._content_dict()
        result["artifact_hash"] = self.artifact_hash
        return result


def verify_prepared_rule_proposal_v2(
    proposal: object,
    *,
    relation: ConfirmedRelationPrimitiveV1,
    numeric_evidence: ApprovedNumericEvidenceBundleV1,
    provenance: ProposalConstructionProvenanceV1,
    budget: FairGenerationBudgetPolicyV2,
    allowed_variables: frozenset[str],
    label_input: object | None = None,
    utility_input: object | None = None,
) -> PreparedValidityResultV2:
    """Reuse the prepared scientific checks while binding the true V2 budget."""

    if provenance.budget_policy_hash != budget.artifact_hash:
        raise TASK039E0ProtocolError("provenance is not bound to budget V2")
    prepared = verify_prepared_rule_proposal_v1(
        proposal,
        relation=relation,
        numeric_evidence=numeric_evidence,
        provenance=provenance,
        budget=budget,  # structural protocol: only artifact_hash is consumed
        allowed_variables=allowed_variables,
        label_input=label_input,
        utility_input=utility_input,
    )
    mapping = validity_issue_action_map_v1()
    issues = tuple(
        ValidityIssueV2(
            code=item.code.value,
            field=item.field,
            repairability=mapping[item.code.value]["repairability"],
            t2_action_class=mapping[item.code.value]["t2_action_class"],
        )
        for item in prepared.issues
    )
    return PreparedValidityResultV2(
        proposal_hash=prepared.proposal_hash,
        relation_binding_hash=prepared.relation_binding_hash,
        evidence_bundle_hash=prepared.evidence_bundle_hash,
        construction_provenance_hash=prepared.construction_provenance_hash,
        budget_policy_hash=budget.artifact_hash,
        status=prepared.status,
        issues=issues,
    )


__all__ = [
    "PreparedValidityResultV2",
    "ValidityIssueV2",
    "VERIFIER_VERSION",
    "verify_prepared_rule_proposal_v2",
]
