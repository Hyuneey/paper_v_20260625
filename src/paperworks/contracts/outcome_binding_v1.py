"""Separate authority receipts for v6 construction and governance outcomes."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from paperworks.contracts.accepted_rule import (
    canonical_rule_verification_subject_sha256,
)
from paperworks.contracts.canonical_collection_v1 import (
    CanonicalDelayedResponseArtifactCollectionV1,
)
from paperworks.contracts.rule_v1 import (
    DelayedResponseRuleV1,
    canonical_rule_document_sha256,
)
from paperworks.contracts.verifier_v1 import (
    DelayedResponseVerifierPolicyV1,
    VerifierResultV1,
    verify_verifier_result_binding,
)
from paperworks.v6.common import (
    CreationMetadataV1,
    V6_FOUNDATION_SCHEMA_VERSION,
    V6FoundationError,
    require_identifier,
    require_sha256,
    stable_hash_v1,
)
from paperworks.v6.normal_evidence_v1 import NormalRelationEvidenceV1
from paperworks.v6.outcomes_v1 import (
    ConstructionTerminalStatusV1,
    GovernanceDecisionV1,
    RuleConstructionOutcomeV1,
    RuleGovernanceOutcomeV1,
)


CONSTRUCTION_BINDING_ARTIFACT_TYPE = (
    "construction_candidate_binding_receipt"
)
GOVERNANCE_BINDING_ARTIFACT_TYPE = (
    "governance_authority_binding_receipt"
)
DEPLOYMENT_AUTHORIZATION_ARTIFACT_TYPE = (
    "v6_deployment_authorization_receipt"
)


def _receipt_id(prefix: str, content: dict[str, Any]) -> str:
    return f"{prefix}-{stable_hash_v1(content)[:20].upper()}"


@dataclass(frozen=True)
class ConstructionCandidateBindingReceiptV1:
    construction_id: str
    construction_outcome_hash: str
    construction_arm: str
    action_history_hash: str
    normal_relation_evidence_id: str
    normal_relation_evidence_hash: str
    rule_evidence_binding_id: str
    rule_evidence_binding_hash: str
    candidate_rule_id: str
    candidate_rule_transport_hash: str
    validity_authority_granted: bool
    runtime_authority_granted: bool
    creation_metadata: CreationMetadataV1
    schema_version: str = V6_FOUNDATION_SCHEMA_VERSION
    artifact_type: str = CONSTRUCTION_BINDING_ARTIFACT_TYPE

    def __post_init__(self) -> None:
        if self.schema_version != V6_FOUNDATION_SCHEMA_VERSION:
            raise V6FoundationError(
                "unsupported construction binding schema_version"
            )
        if self.artifact_type != CONSTRUCTION_BINDING_ARTIFACT_TYPE:
            raise V6FoundationError(
                "invalid construction binding artifact_type"
            )
        for name, value in (
            ("construction_id", self.construction_id),
            ("construction_arm", self.construction_arm),
            ("normal_relation_evidence_id", self.normal_relation_evidence_id),
            ("rule_evidence_binding_id", self.rule_evidence_binding_id),
            ("candidate_rule_id", self.candidate_rule_id),
        ):
            require_identifier(value, name)
        for name, value in (
            ("construction_outcome_hash", self.construction_outcome_hash),
            ("action_history_hash", self.action_history_hash),
            ("normal_relation_evidence_hash", self.normal_relation_evidence_hash),
            ("rule_evidence_binding_hash", self.rule_evidence_binding_hash),
            ("candidate_rule_transport_hash", self.candidate_rule_transport_hash),
        ):
            require_sha256(value, name)
        if (
            self.validity_authority_granted
            or self.runtime_authority_granted
        ):
            raise V6FoundationError(
                "construction candidate binding cannot grant authority"
            )

    def _content_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "artifact_type": self.artifact_type,
            "construction_id": self.construction_id,
            "construction_outcome_hash": self.construction_outcome_hash,
            "construction_arm": self.construction_arm,
            "action_history_hash": self.action_history_hash,
            "normal_relation_evidence_id": (
                self.normal_relation_evidence_id
            ),
            "normal_relation_evidence_hash": (
                self.normal_relation_evidence_hash
            ),
            "rule_evidence_binding_id": self.rule_evidence_binding_id,
            "rule_evidence_binding_hash": self.rule_evidence_binding_hash,
            "candidate_rule_id": self.candidate_rule_id,
            "candidate_rule_transport_hash": (
                self.candidate_rule_transport_hash
            ),
            "validity_authority_granted": self.validity_authority_granted,
            "runtime_authority_granted": self.runtime_authority_granted,
            "creation_metadata": self.creation_metadata.to_dict(),
        }

    @property
    def receipt_id(self) -> str:
        return _receipt_id("CONSTRUCT-BIND-V1", self._content_dict())

    @property
    def artifact_hash(self) -> str:
        payload = self._content_dict()
        payload["receipt_id"] = self.receipt_id
        return stable_hash_v1(payload)

    def to_dict(self) -> dict[str, Any]:
        payload = self._content_dict()
        payload["receipt_id"] = self.receipt_id
        payload["artifact_hash"] = self.artifact_hash
        return payload


@dataclass(frozen=True)
class GovernanceAuthorityBindingReceiptV1:
    governance_id: str
    governance_outcome_hash: str
    accepted_rule_id: str
    accepted_rule_transport_hash: str
    accepted_rule_hash: str
    verifier_result_id: str
    verifier_result_hash: str
    collection_id: str
    collection_hash: str
    normal_guard_assessment_ref: str
    inner_utility_assessment_ref: str
    governance_policy_ref: str
    decision: str
    deployable: bool
    runtime_authority_granted: bool
    creation_metadata: CreationMetadataV1
    schema_version: str = V6_FOUNDATION_SCHEMA_VERSION
    artifact_type: str = GOVERNANCE_BINDING_ARTIFACT_TYPE

    def __post_init__(self) -> None:
        if self.schema_version != V6_FOUNDATION_SCHEMA_VERSION:
            raise V6FoundationError(
                "unsupported governance binding schema_version"
            )
        if self.artifact_type != GOVERNANCE_BINDING_ARTIFACT_TYPE:
            raise V6FoundationError(
                "invalid governance binding artifact_type"
            )
        for name, value in (
            ("governance_id", self.governance_id),
            ("accepted_rule_id", self.accepted_rule_id),
            ("verifier_result_id", self.verifier_result_id),
            ("collection_id", self.collection_id),
        ):
            require_identifier(value, name)
        for name, value in (
            ("governance_outcome_hash", self.governance_outcome_hash),
            ("accepted_rule_transport_hash", self.accepted_rule_transport_hash),
            ("accepted_rule_hash", self.accepted_rule_hash),
            ("verifier_result_hash", self.verifier_result_hash),
            ("collection_hash", self.collection_hash),
            ("normal_guard_assessment_ref", self.normal_guard_assessment_ref),
            ("inner_utility_assessment_ref", self.inner_utility_assessment_ref),
            ("governance_policy_ref", self.governance_policy_ref),
        ):
            require_sha256(value, name)
        if self.decision not in {"selected_rule", "no_op"}:
            raise V6FoundationError("unsupported governance decision")
        if self.deployable != (self.decision == "selected_rule"):
            raise V6FoundationError(
                "governance deployability must follow the decision"
            )
        if self.runtime_authority_granted:
            raise V6FoundationError(
                "governance binding alone cannot grant runtime authority"
            )

    def _content_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "artifact_type": self.artifact_type,
            "governance_id": self.governance_id,
            "governance_outcome_hash": self.governance_outcome_hash,
            "accepted_rule_id": self.accepted_rule_id,
            "accepted_rule_transport_hash": (
                self.accepted_rule_transport_hash
            ),
            "accepted_rule_hash": self.accepted_rule_hash,
            "verifier_result_id": self.verifier_result_id,
            "verifier_result_hash": self.verifier_result_hash,
            "collection_id": self.collection_id,
            "collection_hash": self.collection_hash,
            "normal_guard_assessment_ref": (
                self.normal_guard_assessment_ref
            ),
            "inner_utility_assessment_ref": (
                self.inner_utility_assessment_ref
            ),
            "governance_policy_ref": self.governance_policy_ref,
            "decision": self.decision,
            "deployable": self.deployable,
            "runtime_authority_granted": self.runtime_authority_granted,
            "creation_metadata": self.creation_metadata.to_dict(),
        }

    @property
    def receipt_id(self) -> str:
        return _receipt_id("GOV-BIND-V1", self._content_dict())

    @property
    def artifact_hash(self) -> str:
        payload = self._content_dict()
        payload["receipt_id"] = self.receipt_id
        return stable_hash_v1(payload)

    def to_dict(self) -> dict[str, Any]:
        payload = self._content_dict()
        payload["receipt_id"] = self.receipt_id
        payload["artifact_hash"] = self.artifact_hash
        return payload


@dataclass(frozen=True)
class V6DeploymentAuthorizationReceiptV1:
    governance_binding_receipt_id: str
    governance_binding_hash: str
    runtime_authorization_id: str
    runtime_authorization_hash: str
    accepted_rule_id: str
    accepted_rule_hash: str
    verifier_result_id: str
    verifier_result_hash: str
    collection_id: str
    collection_hash: str
    runtime_scope: str
    deployable: bool
    creation_metadata: CreationMetadataV1
    schema_version: str = V6_FOUNDATION_SCHEMA_VERSION
    artifact_type: str = DEPLOYMENT_AUTHORIZATION_ARTIFACT_TYPE

    def __post_init__(self) -> None:
        if self.schema_version != V6_FOUNDATION_SCHEMA_VERSION:
            raise V6FoundationError(
                "unsupported deployment receipt schema_version"
            )
        if self.artifact_type != DEPLOYMENT_AUTHORIZATION_ARTIFACT_TYPE:
            raise V6FoundationError(
                "invalid deployment receipt artifact_type"
            )
        for name, value in (
            (
                "governance_binding_receipt_id",
                self.governance_binding_receipt_id,
            ),
            ("runtime_authorization_id", self.runtime_authorization_id),
            ("accepted_rule_id", self.accepted_rule_id),
            ("verifier_result_id", self.verifier_result_id),
            ("collection_id", self.collection_id),
        ):
            require_identifier(value, name)
        for name, value in (
            ("governance_binding_hash", self.governance_binding_hash),
            ("runtime_authorization_hash", self.runtime_authorization_hash),
            ("accepted_rule_hash", self.accepted_rule_hash),
            ("verifier_result_hash", self.verifier_result_hash),
            ("collection_hash", self.collection_hash),
        ):
            require_sha256(value, name)
        if not self.deployable:
            raise V6FoundationError(
                "deployment authorization receipt must be deployable"
            )
        if self.runtime_scope != "synthetic_only":
            raise V6FoundationError(
                "P1C deployment authorization is synthetic-only"
            )

    def _content_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "artifact_type": self.artifact_type,
            "governance_binding_receipt_id": (
                self.governance_binding_receipt_id
            ),
            "governance_binding_hash": self.governance_binding_hash,
            "runtime_authorization_id": self.runtime_authorization_id,
            "runtime_authorization_hash": self.runtime_authorization_hash,
            "accepted_rule_id": self.accepted_rule_id,
            "accepted_rule_hash": self.accepted_rule_hash,
            "verifier_result_id": self.verifier_result_id,
            "verifier_result_hash": self.verifier_result_hash,
            "collection_id": self.collection_id,
            "collection_hash": self.collection_hash,
            "runtime_scope": self.runtime_scope,
            "deployable": self.deployable,
            "creation_metadata": self.creation_metadata.to_dict(),
        }

    @property
    def receipt_id(self) -> str:
        return _receipt_id("DEPLOY-V6", self._content_dict())

    @property
    def artifact_hash(self) -> str:
        payload = self._content_dict()
        payload["receipt_id"] = self.receipt_id
        return stable_hash_v1(payload)

    def to_dict(self) -> dict[str, Any]:
        payload = self._content_dict()
        payload["receipt_id"] = self.receipt_id
        payload["artifact_hash"] = self.artifact_hash
        return payload


def bind_construction_candidate_v1(
    *,
    outcome: RuleConstructionOutcomeV1,
    normal_evidence: NormalRelationEvidenceV1,
    collection: CanonicalDelayedResponseArtifactCollectionV1,
    candidate_rule: DelayedResponseRuleV1,
    creation_metadata: CreationMetadataV1,
) -> ConstructionCandidateBindingReceiptV1:
    """Bind only a rule-candidate outcome to its exact Rule v1 transport."""

    if (
        outcome.terminal_status
        is not ConstructionTerminalStatusV1.RULE_CANDIDATE
    ):
        raise V6FoundationError(
            "only rule_candidate construction outcomes can bind"
        )
    transport_hash = canonical_rule_document_sha256(candidate_rule)
    if outcome.candidate_rule_ref != transport_hash:
        raise V6FoundationError(
            "construction candidate transport hash does not match Rule v1"
        )
    if (
        outcome.normal_relation_evidence_ref
        != normal_evidence.artifact_hash
        or collection.normal_relation_evidence.artifact_hash
        != normal_evidence.artifact_hash
    ):
        raise V6FoundationError(
            "construction evidence reference does not match canonical context"
        )
    if (
        candidate_rule.status not in {"candidate", "needs_repair"}
        or candidate_rule.verified_rule_hash is not None
        or candidate_rule.runtime_authorized
    ):
        raise V6FoundationError(
            "construction candidate preclaims accepted or runtime authority"
        )
    action_history_hash = stable_hash_v1(
        {"action_history": [item.to_dict() for item in outcome.action_history]}
    )
    return ConstructionCandidateBindingReceiptV1(
        construction_id=outcome.construction_id,
        construction_outcome_hash=outcome.artifact_hash,
        construction_arm=outcome.construction_arm.value,
        action_history_hash=action_history_hash,
        normal_relation_evidence_id=normal_evidence.evidence_id,
        normal_relation_evidence_hash=normal_evidence.artifact_hash,
        rule_evidence_binding_id=collection.evidence.evidence_id,
        rule_evidence_binding_hash=collection.evidence.artifact_hash,
        candidate_rule_id=candidate_rule.rule_id,
        candidate_rule_transport_hash=transport_hash,
        validity_authority_granted=False,
        runtime_authority_granted=False,
        creation_metadata=creation_metadata,
    )


def bind_governance_authority_v1(
    *,
    outcome: RuleGovernanceOutcomeV1,
    accepted_rule: DelayedResponseRuleV1,
    verifier_result: VerifierResultV1,
    collection: CanonicalDelayedResponseArtifactCollectionV1,
    verifier_policy: DelayedResponseVerifierPolicyV1,
    normal_guard_assessment_ref: str,
    inner_utility_assessment_ref: str,
    governance_policy_ref: str,
    creation_metadata: CreationMetadataV1,
) -> GovernanceAuthorityBindingReceiptV1:
    """Bind an already-computed utility outcome without recalculating it."""

    if (
        accepted_rule.status != "accepted"
        or accepted_rule.verified_rule_hash is None
        or verifier_result.status != "accepted"
    ):
        raise V6FoundationError(
            "governance authority requires accepted canonical validity"
        )
    transport_hash = canonical_rule_document_sha256(accepted_rule)
    if (
        outcome.accepted_rule_ref != transport_hash
        or outcome.verifier_result_ref != verifier_result.artifact_hash
    ):
        raise V6FoundationError(
            "governance outcome rule or verifier reference is invalid"
        )
    if (
        outcome.normal_guard_assessment_ref
        != normal_guard_assessment_ref
        or outcome.inner_utility_assessment_ref
        != inner_utility_assessment_ref
        or outcome.governance_policy_ref != governance_policy_ref
    ):
        raise V6FoundationError(
            "governance assessment or policy artifact is unavailable"
        )
    if outcome.outer_data_used or outcome.sealed_data_used:
        raise V6FoundationError(
            "outer or sealed governance evidence is prohibited"
        )
    verify_verifier_result_binding(
        accepted_rule,
        verifier_result,
        collection,
        policy=verifier_policy,
    )
    subject_hash = canonical_rule_verification_subject_sha256(accepted_rule)
    if accepted_rule.verified_rule_hash != subject_hash:
        raise V6FoundationError("accepted Rule v1 authority hash is invalid")
    deployable = outcome.decision is GovernanceDecisionV1.SELECTED_RULE
    if deployable and outcome.applied_rule_ref != transport_hash:
        raise V6FoundationError(
            "selected governance outcome applies another rule"
        )
    if not deployable and outcome.applied_rule_ref is not None:
        raise V6FoundationError("no_op cannot apply a rule")
    return GovernanceAuthorityBindingReceiptV1(
        governance_id=outcome.governance_id,
        governance_outcome_hash=outcome.artifact_hash,
        accepted_rule_id=accepted_rule.rule_id,
        accepted_rule_transport_hash=transport_hash,
        accepted_rule_hash=subject_hash,
        verifier_result_id=verifier_result.verifier_result_id,
        verifier_result_hash=verifier_result.artifact_hash,
        collection_id=collection.collection_id,
        collection_hash=collection.artifact_hash,
        normal_guard_assessment_ref=normal_guard_assessment_ref,
        inner_utility_assessment_ref=inner_utility_assessment_ref,
        governance_policy_ref=governance_policy_ref,
        decision=outcome.decision.value,
        deployable=deployable,
        runtime_authority_granted=False,
        creation_metadata=creation_metadata,
    )


def bind_v6_deployment_authority_v1(
    *,
    governance_binding: GovernanceAuthorityBindingReceiptV1,
    runtime_authorization_receipt: Any,
    collection: CanonicalDelayedResponseArtifactCollectionV1,
    creation_metadata: CreationMetadataV1,
) -> V6DeploymentAuthorizationReceiptV1:
    """Bind selected governance to a canonical synthetic runtime receipt."""

    if (
        governance_binding.decision != "selected_rule"
        or not governance_binding.deployable
    ):
        raise V6FoundationError(
            "no_op cannot create deployment or runtime authority"
        )
    if (
        governance_binding.collection_id != collection.collection_id
        or governance_binding.collection_hash != collection.artifact_hash
    ):
        raise V6FoundationError(
            "governance collection binding does not match runtime context"
        )
    checks = (
        runtime_authorization_receipt.accepted_rule_id
        == governance_binding.accepted_rule_id,
        runtime_authorization_receipt.accepted_rule_hash
        == governance_binding.accepted_rule_hash,
        runtime_authorization_receipt.verifier_result_id
        == governance_binding.verifier_result_id,
        runtime_authorization_receipt.verifier_result_hash
        == governance_binding.verifier_result_hash,
        runtime_authorization_receipt.graph_id == collection.graph.graph_id,
        runtime_authorization_receipt.graph_hash
        == collection.graph.artifact_hash,
        runtime_authorization_receipt.evidence_id
        == collection.evidence.evidence_id,
        runtime_authorization_receipt.evidence_hash
        == collection.evidence.artifact_hash,
        runtime_authorization_receipt.runtime_scope == "synthetic_only",
    )
    if not all(checks):
        raise V6FoundationError(
            "runtime authorization does not match governance authority"
        )
    return V6DeploymentAuthorizationReceiptV1(
        governance_binding_receipt_id=governance_binding.receipt_id,
        governance_binding_hash=governance_binding.artifact_hash,
        runtime_authorization_id=(
            runtime_authorization_receipt.authorization_id
        ),
        runtime_authorization_hash=(
            runtime_authorization_receipt.authorization_hash
        ),
        accepted_rule_id=governance_binding.accepted_rule_id,
        accepted_rule_hash=governance_binding.accepted_rule_hash,
        verifier_result_id=governance_binding.verifier_result_id,
        verifier_result_hash=governance_binding.verifier_result_hash,
        collection_id=collection.collection_id,
        collection_hash=collection.artifact_hash,
        runtime_scope=runtime_authorization_receipt.runtime_scope,
        deployable=True,
        creation_metadata=creation_metadata,
    )
