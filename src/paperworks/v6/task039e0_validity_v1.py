"""Label-free deterministic validity skeleton for TASK-039E0-PREP.

This verifier checks proposal-envelope admissibility only.  It never invokes
an LLM, consumes utility labels, materializes Rule v1/v2, or grants runtime
authority.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping, Sequence

from paperworks.v6.task039e0_rule_construction_prep_v1 import (
    MAIN_NUMERIC_ORIGIN,
    PROPOSAL_ARTIFACT_TYPE,
    PROPOSAL_DSL_FAMILY,
    RUNTIME_LOGIC,
    ApprovedNumericEvidenceBundleV1,
    ConfirmedRelationPrimitiveV1,
    FairGenerationBudgetPolicyV1,
    FROZEN_ARM_PROTOCOLS,
    ProposalConstructionProvenanceV1,
    TASK039E0PreparationError,
    canonical_proposal_hash_v1,
)
from paperworks.v6.common import (
    V6_FOUNDATION_SCHEMA_VERSION,
    V6FoundationError,
    require_identifier,
    require_sha256,
    stable_hash_v1,
)
from paperworks.v6.outcomes_v1 import ConstructionArmV1


VERIFIER_VERSION = "task039e0_preparation_validity_v1"
PROPOSAL_FIELDS = frozenset(
    {
        "schema_version",
        "artifact_type",
        "construction_arm",
        "dsl_family",
        "relation_binding_hash",
        "relation_identity",
        "source",
        "source_step_direction",
        "target",
        "target_response_direction",
        "selected_delay_horizon_seconds",
        "numeric_origin",
        "source_threshold_reference",
        "source_stability_reference",
        "target_scale_reference",
        "fit_evidence_reference",
        "confirmation_evidence_reference",
        "preregistered_window_constant_references",
        "variables",
        "runtime_logic",
        "free_text_runtime_logic",
        "numeric_literals",
        "prohibited_data_references",
        "construction_provenance_hash",
        "canonical_rule_materialized",
        "validity_authority_granted",
        "runtime_authority_granted",
        "proposal_hash",
    }
)


class ValidityIssueCodeV1(str, Enum):
    LABEL_INPUT_PROHIBITED = "VALIDITY_LABEL_INPUT_PROHIBITED"
    UTILITY_INPUT_PROHIBITED = "VALIDITY_UTILITY_INPUT_PROHIBITED"
    MALFORMED_DSL = "VALIDITY_MALFORMED_DSL"
    DSL_FAMILY_UNSUPPORTED = "VALIDITY_DSL_FAMILY_UNSUPPORTED"
    RELATION_BINDING_MISMATCH = "VALIDITY_RELATION_BINDING_MISMATCH"
    RELATION_IDENTITY_MISMATCH = "VALIDITY_RELATION_IDENTITY_MISMATCH"
    SOURCE_NOT_ALLOWED = "VALIDITY_SOURCE_NOT_ALLOWED"
    TARGET_NOT_ALLOWED = "VALIDITY_TARGET_NOT_ALLOWED"
    SOURCE_BINDING_MISMATCH = "VALIDITY_SOURCE_BINDING_MISMATCH"
    TARGET_BINDING_MISMATCH = "VALIDITY_TARGET_BINDING_MISMATCH"
    SOURCE_DIRECTION_MISMATCH = "VALIDITY_SOURCE_DIRECTION_MISMATCH"
    TARGET_DIRECTION_MISMATCH = "VALIDITY_TARGET_DIRECTION_MISMATCH"
    HORIZON_MISMATCH = "VALIDITY_HORIZON_MISMATCH"
    NUMERIC_EVIDENCE_BUNDLE_INVALID = (
        "VALIDITY_NUMERIC_EVIDENCE_BUNDLE_INVALID"
    )
    NUMERIC_REFERENCE_MISMATCH = "VALIDITY_NUMERIC_REFERENCE_MISMATCH"
    NUMERIC_ORIGIN_UNAPPROVED = "VALIDITY_NUMERIC_ORIGIN_UNAPPROVED"
    UNAPPROVED_NUMERIC_LITERAL = "VALIDITY_UNAPPROVED_NUMERIC_LITERAL"
    UNSUPPORTED_VARIABLE = "VALIDITY_UNSUPPORTED_VARIABLE"
    RUNTIME_LOGIC_UNSUPPORTED = "VALIDITY_RUNTIME_LOGIC_UNSUPPORTED"
    FREE_TEXT_RUNTIME_LOGIC = "VALIDITY_FREE_TEXT_RUNTIME_LOGIC"
    PROHIBITED_DATA_REFERENCE = "VALIDITY_PROHIBITED_DATA_REFERENCE"
    SERIALIZATION_HASH_MISMATCH = "VALIDITY_SERIALIZATION_HASH_MISMATCH"
    CONSTRUCTION_PROVENANCE_INVALID = (
        "VALIDITY_CONSTRUCTION_PROVENANCE_INVALID"
    )
    RULE_MATERIALIZATION_PRECLAIMED = (
        "VALIDITY_RULE_MATERIALIZATION_PRECLAIMED"
    )
    AUTHORITY_PRECLAIMED = "VALIDITY_AUTHORITY_PRECLAIMED"


class ValidityRepairabilityV1(str, Enum):
    REPAIRABLE = "repairable"
    NON_REPAIRABLE = "non_repairable"


@dataclass(frozen=True)
class ValidityIssueV1:
    code: ValidityIssueCodeV1
    field: str
    repairability: ValidityRepairabilityV1

    def __post_init__(self) -> None:
        require_identifier(self.field, "validity_issue_field")

    def to_dict(self) -> dict[str, str]:
        return {
            "code": self.code.value,
            "field": self.field,
            "repairability": self.repairability.value,
        }


@dataclass(frozen=True)
class PreparedValidityResultV1:
    proposal_hash: str
    relation_binding_hash: str
    evidence_bundle_hash: str
    construction_provenance_hash: str
    budget_policy_hash: str
    status: str
    issues: tuple[ValidityIssueV1, ...]
    verifier_version: str = VERIFIER_VERSION
    project_owned_deterministic_code: bool = True
    label_input_used: bool = False
    utility_input_used: bool = False
    llm_chain_of_thought_used: bool = False
    canonical_rule_materialized: bool = False
    validity_authority_granted: bool = False
    runtime_authority_granted: bool = False

    def __post_init__(self) -> None:
        for field_name in (
            "proposal_hash",
            "relation_binding_hash",
            "evidence_bundle_hash",
            "construction_provenance_hash",
            "budget_policy_hash",
        ):
            require_sha256(getattr(self, field_name), field_name)
        require_identifier(self.verifier_version, "verifier_version")
        if self.status not in {"admissible", "rejected"}:
            raise TASK039E0PreparationError("validity status is invalid")
        if self.status == "admissible" and self.issues:
            raise TASK039E0PreparationError(
                "admissible validity result cannot contain issues"
            )
        if self.status == "rejected" and not self.issues:
            raise TASK039E0PreparationError(
                "rejected validity result requires bounded issues"
            )
        if self.project_owned_deterministic_code is not True:
            raise TASK039E0PreparationError(
                "validity verifier must remain project-owned deterministic code"
            )
        for field_name in (
            "label_input_used",
            "utility_input_used",
            "llm_chain_of_thought_used",
            "canonical_rule_materialized",
            "validity_authority_granted",
            "runtime_authority_granted",
        ):
            if getattr(self, field_name) is not False:
                raise TASK039E0PreparationError(
                    f"{field_name} must remain false in PREP"
                )

    def _content_dict(self) -> dict[str, Any]:
        return {
            "schema_version": V6_FOUNDATION_SCHEMA_VERSION,
            "artifact_type": "task039e0_prepared_validity_result_v1",
            "proposal_hash": self.proposal_hash,
            "relation_binding_hash": self.relation_binding_hash,
            "evidence_bundle_hash": self.evidence_bundle_hash,
            "construction_provenance_hash": (
                self.construction_provenance_hash
            ),
            "budget_policy_hash": self.budget_policy_hash,
            "status": self.status,
            "issues": [item.to_dict() for item in self.issues],
            "verifier_version": self.verifier_version,
            "project_owned_deterministic_code": (
                self.project_owned_deterministic_code
            ),
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
        payload = self._content_dict()
        payload["artifact_hash"] = self.artifact_hash
        return payload


def _issue(
    code: ValidityIssueCodeV1,
    field: str,
    repairability: ValidityRepairabilityV1 = (
        ValidityRepairabilityV1.NON_REPAIRABLE
    ),
) -> ValidityIssueV1:
    return ValidityIssueV1(code, field, repairability)


def _issue_key(issue: ValidityIssueV1) -> tuple[str, str, str]:
    return issue.code.value, issue.field, issue.repairability.value


def _safe_proposal_hash(proposal: object) -> str:
    if not isinstance(proposal, Mapping):
        return stable_hash_v1({"malformed_proposal": True})
    try:
        return canonical_proposal_hash_v1(proposal)
    except (TypeError, ValueError, V6FoundationError):
        return stable_hash_v1({"malformed_proposal": True})


def _result(
    *,
    proposal_hash: str,
    relation: ConfirmedRelationPrimitiveV1,
    numeric_evidence: ApprovedNumericEvidenceBundleV1,
    provenance: ProposalConstructionProvenanceV1,
    budget: FairGenerationBudgetPolicyV1,
    issues: Sequence[ValidityIssueV1],
) -> PreparedValidityResultV1:
    normalized = tuple(sorted(set(issues), key=_issue_key))
    return PreparedValidityResultV1(
        proposal_hash=proposal_hash,
        relation_binding_hash=relation.binding_hash,
        evidence_bundle_hash=numeric_evidence.artifact_hash,
        construction_provenance_hash=provenance.artifact_hash,
        budget_policy_hash=budget.artifact_hash,
        status="rejected" if normalized else "admissible",
        issues=normalized,
    )


def _structurally_closed(proposal: Mapping[str, Any]) -> bool:
    if set(proposal) != PROPOSAL_FIELDS:
        return False
    string_fields = (
        "schema_version",
        "artifact_type",
        "construction_arm",
        "dsl_family",
        "relation_binding_hash",
        "relation_identity",
        "source",
        "source_step_direction",
        "target",
        "target_response_direction",
        "numeric_origin",
        "source_threshold_reference",
        "source_stability_reference",
        "target_scale_reference",
        "fit_evidence_reference",
        "confirmation_evidence_reference",
        "runtime_logic",
        "construction_provenance_hash",
        "proposal_hash",
    )
    if any(not isinstance(proposal[field], str) for field in string_fields):
        return False
    if (
        isinstance(proposal["selected_delay_horizon_seconds"], bool)
        or not isinstance(proposal["selected_delay_horizon_seconds"], int)
    ):
        return False
    for field in (
        "preregistered_window_constant_references",
        "variables",
        "numeric_literals",
        "prohibited_data_references",
    ):
        if not isinstance(proposal[field], list):
            return False
    for field in (
        "canonical_rule_materialized",
        "validity_authority_granted",
        "runtime_authority_granted",
    ):
        if not isinstance(proposal[field], bool):
            return False
    return proposal["free_text_runtime_logic"] is None or isinstance(
        proposal["free_text_runtime_logic"], str
    )


def verify_prepared_rule_proposal_v1(
    proposal: object,
    *,
    relation: ConfirmedRelationPrimitiveV1,
    numeric_evidence: ApprovedNumericEvidenceBundleV1,
    provenance: ProposalConstructionProvenanceV1,
    budget: FairGenerationBudgetPolicyV1,
    allowed_variables: frozenset[str],
    label_input: object | None = None,
    utility_input: object | None = None,
) -> PreparedValidityResultV1:
    """Verify one proposal without reading labels, utility, data, or CoT."""

    proposal_hash = _safe_proposal_hash(proposal)
    issues: list[ValidityIssueV1] = []
    if label_input is not None:
        issues.append(
            _issue(
                ValidityIssueCodeV1.LABEL_INPUT_PROHIBITED,
                "validity_input",
            )
        )
    if utility_input is not None:
        issues.append(
            _issue(
                ValidityIssueCodeV1.UTILITY_INPUT_PROHIBITED,
                "validity_input",
            )
        )
    try:
        numeric_evidence.assert_matches(relation)
    except TASK039E0PreparationError:
        issues.append(
            _issue(
                ValidityIssueCodeV1.NUMERIC_EVIDENCE_BUNDLE_INVALID,
                "numeric_evidence",
            )
        )
    if not isinstance(proposal, Mapping) or not _structurally_closed(proposal):
        issues.append(
            _issue(
                ValidityIssueCodeV1.MALFORMED_DSL,
                "proposal",
                ValidityRepairabilityV1.REPAIRABLE,
            )
        )
        return _result(
            proposal_hash=proposal_hash,
            relation=relation,
            numeric_evidence=numeric_evidence,
            provenance=provenance,
            budget=budget,
            issues=issues,
        )

    if (
        proposal["schema_version"] != V6_FOUNDATION_SCHEMA_VERSION
        or proposal["artifact_type"] != PROPOSAL_ARTIFACT_TYPE
    ):
        issues.append(
            _issue(
                ValidityIssueCodeV1.MALFORMED_DSL,
                "schema_version",
                ValidityRepairabilityV1.REPAIRABLE,
            )
        )
    if proposal["dsl_family"] != PROPOSAL_DSL_FAMILY:
        issues.append(
            _issue(
                ValidityIssueCodeV1.DSL_FAMILY_UNSUPPORTED,
                "dsl_family",
            )
        )
    try:
        proposal_arm = ConstructionArmV1(proposal["construction_arm"])
    except ValueError:
        proposal_arm = None
        issues.append(
            _issue(
                ValidityIssueCodeV1.MALFORMED_DSL,
                "construction_arm",
            )
        )
    if proposal["relation_binding_hash"] != relation.binding_hash:
        issues.append(
            _issue(
                ValidityIssueCodeV1.RELATION_BINDING_MISMATCH,
                "relation_binding_hash",
            )
        )
    if proposal["relation_identity"] != relation.relation_identity:
        issues.append(
            _issue(
                ValidityIssueCodeV1.RELATION_IDENTITY_MISMATCH,
                "relation_identity",
            )
        )
    for variable in allowed_variables:
        require_identifier(variable, "allowed_variable")
    if proposal["source"] not in allowed_variables:
        issues.append(
            _issue(ValidityIssueCodeV1.SOURCE_NOT_ALLOWED, "source")
        )
    if proposal["target"] not in allowed_variables:
        issues.append(
            _issue(ValidityIssueCodeV1.TARGET_NOT_ALLOWED, "target")
        )
    if proposal["source"] != relation.source:
        issues.append(
            _issue(ValidityIssueCodeV1.SOURCE_BINDING_MISMATCH, "source")
        )
    if proposal["target"] != relation.target:
        issues.append(
            _issue(ValidityIssueCodeV1.TARGET_BINDING_MISMATCH, "target")
        )
    if proposal["source_step_direction"] != relation.source_step_direction:
        issues.append(
            _issue(
                ValidityIssueCodeV1.SOURCE_DIRECTION_MISMATCH,
                "source_step_direction",
            )
        )
    if (
        proposal["target_response_direction"]
        != relation.target_response_direction
    ):
        issues.append(
            _issue(
                ValidityIssueCodeV1.TARGET_DIRECTION_MISMATCH,
                "target_response_direction",
            )
        )
    if (
        proposal["selected_delay_horizon_seconds"]
        != relation.selected_delay_horizon_seconds
    ):
        issues.append(
            _issue(
                ValidityIssueCodeV1.HORIZON_MISMATCH,
                "selected_delay_horizon_seconds",
            )
        )
    if proposal["numeric_origin"] != MAIN_NUMERIC_ORIGIN:
        issues.append(
            _issue(
                ValidityIssueCodeV1.NUMERIC_ORIGIN_UNAPPROVED,
                "numeric_origin",
            )
        )
    expected_numeric_refs = {
        "source_threshold_reference": numeric_evidence.source_threshold_reference,
        "source_stability_reference": numeric_evidence.source_stability_reference,
        "target_scale_reference": numeric_evidence.target_scale_reference,
        "fit_evidence_reference": numeric_evidence.fit_evidence_reference,
        "confirmation_evidence_reference": (
            numeric_evidence.confirmation_evidence_reference
        ),
        "preregistered_window_constant_references": list(
            numeric_evidence.preregistered_window_constant_references
        ),
    }
    if any(
        proposal[field] != expected
        for field, expected in expected_numeric_refs.items()
    ):
        issues.append(
            _issue(
                ValidityIssueCodeV1.NUMERIC_REFERENCE_MISMATCH,
                "numeric_references",
            )
        )
    if proposal["numeric_literals"]:
        issues.append(
            _issue(
                ValidityIssueCodeV1.UNAPPROVED_NUMERIC_LITERAL,
                "numeric_literals",
            )
        )
    variables = proposal["variables"]
    if (
        any(not isinstance(item, str) for item in variables)
        or len(variables) != len(set(variables))
        or set(variables) != {relation.source, relation.target}
        or any(item not in allowed_variables for item in variables)
    ):
        issues.append(
            _issue(
                ValidityIssueCodeV1.UNSUPPORTED_VARIABLE,
                "variables",
            )
        )
    if proposal["runtime_logic"] != RUNTIME_LOGIC:
        issues.append(
            _issue(
                ValidityIssueCodeV1.RUNTIME_LOGIC_UNSUPPORTED,
                "runtime_logic",
            )
        )
    if proposal["free_text_runtime_logic"] is not None:
        issues.append(
            _issue(
                ValidityIssueCodeV1.FREE_TEXT_RUNTIME_LOGIC,
                "free_text_runtime_logic",
            )
        )
    if proposal["prohibited_data_references"]:
        issues.append(
            _issue(
                ValidityIssueCodeV1.PROHIBITED_DATA_REFERENCE,
                "prohibited_data_references",
            )
        )
    if proposal["proposal_hash"] != canonical_proposal_hash_v1(proposal):
        issues.append(
            _issue(
                ValidityIssueCodeV1.SERIALIZATION_HASH_MISMATCH,
                "proposal_hash",
            )
        )
    expected_arm_protocol = next(
        item for item in FROZEN_ARM_PROTOCOLS if item.arm is provenance.construction_arm
    )
    provenance_valid = (
        proposal["construction_provenance_hash"] == provenance.artifact_hash
        and proposal_arm is provenance.construction_arm
        and provenance.arm_protocol_hash == expected_arm_protocol.protocol_hash
        and provenance.evidence_bundle_hash == numeric_evidence.artifact_hash
        and provenance.budget_policy_hash == budget.artifact_hash
    )
    if not provenance_valid:
        issues.append(
            _issue(
                ValidityIssueCodeV1.CONSTRUCTION_PROVENANCE_INVALID,
                "construction_provenance_hash",
            )
        )
    if proposal["canonical_rule_materialized"]:
        issues.append(
            _issue(
                ValidityIssueCodeV1.RULE_MATERIALIZATION_PRECLAIMED,
                "canonical_rule_materialized",
            )
        )
    if (
        proposal["validity_authority_granted"]
        or proposal["runtime_authority_granted"]
    ):
        issues.append(
            _issue(
                ValidityIssueCodeV1.AUTHORITY_PRECLAIMED,
                "authority",
            )
        )
    return _result(
        proposal_hash=proposal_hash,
        relation=relation,
        numeric_evidence=numeric_evidence,
        provenance=provenance,
        budget=budget,
        issues=issues,
    )


__all__ = [
    "PROPOSAL_FIELDS",
    "PreparedValidityResultV1",
    "ValidityIssueCodeV1",
    "ValidityIssueV1",
    "ValidityRepairabilityV1",
    "VERIFIER_VERSION",
    "verify_prepared_rule_proposal_v1",
]
