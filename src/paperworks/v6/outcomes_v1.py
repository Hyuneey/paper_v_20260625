"""Explicit construction, governance, and runtime disposition outcomes for v6."""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping

from paperworks.v6.common import (
    CreationMetadataV1,
    V6_FOUNDATION_SCHEMA_VERSION,
    V6FoundationError,
    canonical_json_v1,
    deterministic_id,
    reject_unknown_fields,
    require_sha256,
    require_sha256_refs,
    require_unique_strings,
    stable_hash_v1,
    verify_identity_fields,
)
from paperworks.v6.normal_evidence_v1 import (
    EvidenceStatusV1,
    NO_RULE_EVIDENCE_REASON_CODES,
)


CONSTRUCTION_OUTCOME_ARTIFACT_TYPE = "rule_construction_outcome"
GOVERNANCE_OUTCOME_ARTIFACT_TYPE = "rule_governance_outcome"
NO_OP_REASON_CODES = frozenset(
    {
        "identity_not_worse",
        "tie_prefers_no_op",
        "insufficient_inner_utility",
        "safety_budget_exceeded",
        "duplicate_or_redundant",
        "unstable_inner_utility",
        "correction_direction_not_authorized",
    }
)


class ConstructionActionTypeV1(str, Enum):
    INSPECT = "inspect"
    PLAN = "plan"
    RETRIEVE = "retrieve"
    REVISE = "revise"
    NO_RULE = "no_rule"
    TERMINATE = "terminate"


class ConstructionArmV1(str, Enum):
    T0 = "T0"
    T1 = "T1"
    T1_B = "T1_B"
    T2 = "T2"


class ConstructionTerminalStatusV1(str, Enum):
    RULE_CANDIDATE = "rule_candidate"
    NO_RULE = "no_rule"
    PROVIDER_ERROR = "provider_error"
    INVALID_OUTPUT = "invalid_output"
    NON_REPAIRABLE_REJECTION = "non_repairable_rejection"
    BUDGET_EXHAUSTED = "budget_exhausted"


class GovernanceDecisionV1(str, Enum):
    SELECTED_RULE = "selected_rule"
    NO_OP = "no_op"


class RuntimeDispositionV1(str, Enum):
    EVALUATED = "evaluated"
    ABSTAIN = "abstain"


@dataclass(frozen=True)
class ConstructionActionRecordV1:
    action_index: int
    action_type: ConstructionActionTypeV1
    input_artifact_refs: tuple[str, ...]
    output_artifact_refs: tuple[str, ...]
    verifier_feedback_refs: tuple[str, ...]
    changed_fields: tuple[str, ...]
    reason_code: str
    provider_call_index: int | None

    def __post_init__(self) -> None:
        if (
            isinstance(self.action_index, bool)
            or not isinstance(self.action_index, int)
            or self.action_index < 0
        ):
            raise V6FoundationError("action_index must be a non-negative integer")
        object.__setattr__(
            self,
            "input_artifact_refs",
            require_sha256_refs(
                self.input_artifact_refs, "input_artifact_refs"
            ),
        )
        object.__setattr__(
            self,
            "output_artifact_refs",
            require_sha256_refs(
                self.output_artifact_refs, "output_artifact_refs"
            ),
        )
        object.__setattr__(
            self,
            "verifier_feedback_refs",
            require_sha256_refs(
                self.verifier_feedback_refs, "verifier_feedback_refs"
            ),
        )
        object.__setattr__(
            self,
            "changed_fields",
            require_unique_strings(self.changed_fields, "changed_fields"),
        )
        if any(
            field.startswith("/") or ".." in field or not field
            for field in self.changed_fields
        ):
            raise V6FoundationError("changed_fields must be bounded field names")
        if not self.reason_code:
            raise V6FoundationError("action reason_code is required")
        if self.provider_call_index is not None and (
            isinstance(self.provider_call_index, bool)
            or not isinstance(self.provider_call_index, int)
            or self.provider_call_index < 0
        ):
            raise V6FoundationError(
                "provider_call_index must be non-negative or null"
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "action_index": self.action_index,
            "action_type": self.action_type.value,
            "input_artifact_refs": list(self.input_artifact_refs),
            "output_artifact_refs": list(self.output_artifact_refs),
            "verifier_feedback_refs": list(self.verifier_feedback_refs),
            "changed_fields": list(self.changed_fields),
            "reason_code": self.reason_code,
            "provider_call_index": self.provider_call_index,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "ConstructionActionRecordV1":
        reject_unknown_fields(
            data,
            frozenset(
                {
                    "action_index",
                    "action_type",
                    "input_artifact_refs",
                    "output_artifact_refs",
                    "verifier_feedback_refs",
                    "changed_fields",
                    "reason_code",
                    "provider_call_index",
                }
            ),
            "construction_action_record",
        )
        return cls(
            action_index=int(data["action_index"]),
            action_type=ConstructionActionTypeV1(str(data["action_type"])),
            input_artifact_refs=tuple(
                str(item) for item in data["input_artifact_refs"]
            ),
            output_artifact_refs=tuple(
                str(item) for item in data["output_artifact_refs"]
            ),
            verifier_feedback_refs=tuple(
                str(item) for item in data["verifier_feedback_refs"]
            ),
            changed_fields=tuple(str(item) for item in data["changed_fields"]),
            reason_code=str(data["reason_code"]),
            provider_call_index=(
                int(data["provider_call_index"])
                if data.get("provider_call_index") is not None
                else None
            ),
        )


@dataclass(frozen=True)
class RuleConstructionOutcomeV1:
    construction_arm: ConstructionArmV1
    normal_relation_evidence_ref: str
    normal_evidence_status: EvidenceStatusV1
    parameter_strategy_ref: str
    candidate_rule_ref: str | None
    verifier_result_refs: tuple[str, ...]
    action_history: tuple[ConstructionActionRecordV1, ...]
    provider_call_budget: int
    provider_calls_used: int
    token_budget: int
    tokens_used: int
    independent_generation: bool
    terminal_status: ConstructionTerminalStatusV1
    reason_codes: tuple[str, ...]
    provider_failure: bool
    invalid_output_detected: bool
    provenance_references: tuple[str, ...]
    creation_metadata: CreationMetadataV1
    outer_data_used: bool
    sealed_data_used: bool
    validity_authority_granted: bool
    runtime_authority_granted: bool
    claim_boundary: str
    schema_version: str = V6_FOUNDATION_SCHEMA_VERSION
    artifact_type: str = CONSTRUCTION_OUTCOME_ARTIFACT_TYPE

    def __post_init__(self) -> None:
        if self.schema_version != V6_FOUNDATION_SCHEMA_VERSION:
            raise V6FoundationError(
                "unsupported construction outcome schema_version"
            )
        if self.artifact_type != CONSTRUCTION_OUTCOME_ARTIFACT_TYPE:
            raise V6FoundationError("invalid construction outcome artifact_type")
        require_sha256(
            self.normal_relation_evidence_ref,
            "normal_relation_evidence_ref",
        )
        require_sha256(self.parameter_strategy_ref, "parameter_strategy_ref")
        if self.candidate_rule_ref is not None:
            require_sha256(self.candidate_rule_ref, "candidate_rule_ref")
        object.__setattr__(
            self,
            "verifier_result_refs",
            require_sha256_refs(
                self.verifier_result_refs, "verifier_result_refs"
            ),
        )
        action_indexes = tuple(item.action_index for item in self.action_history)
        if action_indexes != tuple(sorted(action_indexes)) or len(action_indexes) != len(
            set(action_indexes)
        ):
            raise V6FoundationError(
                "construction action indexes must be ordered and unique"
            )
        for name, value in (
            ("provider_call_budget", self.provider_call_budget),
            ("provider_calls_used", self.provider_calls_used),
            ("token_budget", self.token_budget),
            ("tokens_used", self.tokens_used),
        ):
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise V6FoundationError(f"{name} must be a non-negative integer")
        if self.provider_calls_used > self.provider_call_budget:
            raise V6FoundationError("provider calls exceed the frozen budget")
        if self.tokens_used > self.token_budget:
            raise V6FoundationError("provider tokens exceed the frozen budget")
        object.__setattr__(
            self,
            "reason_codes",
            require_unique_strings(
                self.reason_codes, "reason_codes", allow_empty=False
            ),
        )
        object.__setattr__(
            self,
            "provenance_references",
            require_sha256_refs(
                self.provenance_references,
                "provenance_references",
                allow_empty=False,
            ),
        )
        action_types = tuple(item.action_type for item in self.action_history)
        has_feedback = any(item.verifier_feedback_refs for item in self.action_history)
        if self.construction_arm is ConstructionArmV1.T0:
            if self.provider_call_budget != 0 or self.provider_calls_used != 0:
                raise V6FoundationError("T0 cannot have a provider-call budget")
            if ConstructionActionTypeV1.REVISE in action_types or has_feedback:
                raise V6FoundationError("T0 cannot use verifier feedback")
        elif self.construction_arm is ConstructionArmV1.T1:
            if self.provider_calls_used > 1:
                raise V6FoundationError("T1 permits at most one provider call")
            if (
                ConstructionActionTypeV1.RETRIEVE in action_types
                or ConstructionActionTypeV1.REVISE in action_types
                or has_feedback
            ):
                raise V6FoundationError("T1 cannot retrieve, revise, or use feedback")
        elif self.construction_arm is ConstructionArmV1.T1_B:
            if (
                ConstructionActionTypeV1.RETRIEVE in action_types
                or ConstructionActionTypeV1.REVISE in action_types
                or has_feedback
            ):
                raise V6FoundationError(
                    "T1_B cannot retrieve, revise, or use verifier feedback"
                )
            if not self.independent_generation:
                raise V6FoundationError("T1_B requires independent generation")
        if self.construction_arm is not ConstructionArmV1.T1_B and self.independent_generation:
            raise V6FoundationError(
                "independent_generation is reserved for the T1_B arm"
            )
        if self.terminal_status is ConstructionTerminalStatusV1.RULE_CANDIDATE:
            if self.candidate_rule_ref is None:
                raise V6FoundationError(
                    "rule_candidate status requires candidate_rule_ref"
                )
        elif self.candidate_rule_ref is not None:
            raise V6FoundationError(
                "non-candidate construction status cannot expose a candidate rule"
            )
        if self.terminal_status is ConstructionTerminalStatusV1.NO_RULE:
            if self.provider_failure or self.invalid_output_detected:
                raise V6FoundationError(
                    "no_rule cannot represent provider or output failure"
                )
            if ConstructionActionTypeV1.NO_RULE not in action_types:
                raise V6FoundationError(
                    "no_rule outcome requires a no_rule action"
                )
            if self.normal_evidence_status is EvidenceStatusV1.SUPPORTED:
                raise V6FoundationError(
                    "no_rule requires insufficient or unstable normal evidence"
                )
            if not set(self.reason_codes).issubset(NO_RULE_EVIDENCE_REASON_CODES):
                raise V6FoundationError(
                    "no_rule reasons must be evidence-insufficiency reasons"
                )
        elif self.terminal_status is ConstructionTerminalStatusV1.PROVIDER_ERROR:
            if not self.provider_failure or self.invalid_output_detected:
                raise V6FoundationError("provider_error flags are inconsistent")
        elif self.terminal_status is ConstructionTerminalStatusV1.INVALID_OUTPUT:
            if not self.invalid_output_detected or self.provider_failure:
                raise V6FoundationError("invalid_output flags are inconsistent")
        elif self.provider_failure or self.invalid_output_detected:
            raise V6FoundationError(
                "provider/output failure flags do not match terminal status"
            )
        if (
            self.terminal_status
            is ConstructionTerminalStatusV1.NON_REPAIRABLE_REJECTION
            and not self.verifier_result_refs
        ):
            raise V6FoundationError(
                "non-repairable rejection requires verifier result evidence"
            )
        if self.terminal_status is ConstructionTerminalStatusV1.BUDGET_EXHAUSTED:
            if not (
                self.provider_calls_used == self.provider_call_budget
                or self.tokens_used == self.token_budget
            ):
                raise V6FoundationError(
                    "budget_exhausted requires an exhausted call or token budget"
                )
        if self.outer_data_used or self.sealed_data_used:
            raise V6FoundationError(
                "construction outcomes cannot use outer or sealed data"
            )
        if self.validity_authority_granted or self.runtime_authority_granted:
            raise V6FoundationError(
                "construction outcomes cannot grant validity or runtime authority"
            )
        if not self.claim_boundary:
            raise V6FoundationError("claim_boundary is required")

    def _content_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "artifact_type": self.artifact_type,
            "construction_arm": self.construction_arm.value,
            "normal_relation_evidence_ref": self.normal_relation_evidence_ref,
            "normal_evidence_status": self.normal_evidence_status.value,
            "parameter_strategy_ref": self.parameter_strategy_ref,
            "candidate_rule_ref": self.candidate_rule_ref,
            "verifier_result_refs": list(self.verifier_result_refs),
            "action_history": [item.to_dict() for item in self.action_history],
            "provider_call_budget": self.provider_call_budget,
            "provider_calls_used": self.provider_calls_used,
            "token_budget": self.token_budget,
            "tokens_used": self.tokens_used,
            "independent_generation": self.independent_generation,
            "terminal_status": self.terminal_status.value,
            "reason_codes": list(self.reason_codes),
            "provider_failure": self.provider_failure,
            "invalid_output_detected": self.invalid_output_detected,
            "provenance_references": list(self.provenance_references),
            "creation_metadata": self.creation_metadata.to_dict(),
            "outer_data_used": self.outer_data_used,
            "sealed_data_used": self.sealed_data_used,
            "validity_authority_granted": self.validity_authority_granted,
            "runtime_authority_granted": self.runtime_authority_granted,
            "claim_boundary": self.claim_boundary,
        }

    @property
    def construction_id(self) -> str:
        return deterministic_id("RCO-V1", self._content_dict())

    @property
    def artifact_hash(self) -> str:
        payload = self._content_dict()
        payload["construction_id"] = self.construction_id
        return stable_hash_v1(payload)

    def to_dict(self) -> dict[str, Any]:
        payload = self._content_dict()
        payload["construction_id"] = self.construction_id
        payload["artifact_hash"] = self.artifact_hash
        return payload

    def to_json(self) -> str:
        return canonical_json_v1(self.to_dict())

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "RuleConstructionOutcomeV1":
        reject_unknown_fields(
            data,
            frozenset(
                {
                    "schema_version",
                    "artifact_type",
                    "construction_id",
                    "artifact_hash",
                    "construction_arm",
                    "normal_relation_evidence_ref",
                    "normal_evidence_status",
                    "parameter_strategy_ref",
                    "candidate_rule_ref",
                    "verifier_result_refs",
                    "action_history",
                    "provider_call_budget",
                    "provider_calls_used",
                    "token_budget",
                    "tokens_used",
                    "independent_generation",
                    "terminal_status",
                    "reason_codes",
                    "provider_failure",
                    "invalid_output_detected",
                    "provenance_references",
                    "creation_metadata",
                    "outer_data_used",
                    "sealed_data_used",
                    "validity_authority_granted",
                    "runtime_authority_granted",
                    "claim_boundary",
                }
            ),
            CONSTRUCTION_OUTCOME_ARTIFACT_TYPE,
        )
        result = cls(
            construction_arm=ConstructionArmV1(str(data["construction_arm"])),
            normal_relation_evidence_ref=str(
                data["normal_relation_evidence_ref"]
            ),
            normal_evidence_status=EvidenceStatusV1(
                str(data["normal_evidence_status"])
            ),
            parameter_strategy_ref=str(data["parameter_strategy_ref"]),
            candidate_rule_ref=data.get("candidate_rule_ref"),
            verifier_result_refs=tuple(
                str(item) for item in data["verifier_result_refs"]
            ),
            action_history=tuple(
                ConstructionActionRecordV1.from_dict(item)
                for item in data["action_history"]
            ),
            provider_call_budget=int(data["provider_call_budget"]),
            provider_calls_used=int(data["provider_calls_used"]),
            token_budget=int(data["token_budget"]),
            tokens_used=int(data["tokens_used"]),
            independent_generation=data["independent_generation"] is True,
            terminal_status=ConstructionTerminalStatusV1(
                str(data["terminal_status"])
            ),
            reason_codes=tuple(str(item) for item in data["reason_codes"]),
            provider_failure=data["provider_failure"] is True,
            invalid_output_detected=data["invalid_output_detected"] is True,
            provenance_references=tuple(
                str(item) for item in data["provenance_references"]
            ),
            creation_metadata=CreationMetadataV1.from_dict(
                data["creation_metadata"]
            ),
            outer_data_used=data["outer_data_used"] is True,
            sealed_data_used=data["sealed_data_used"] is True,
            validity_authority_granted=data["validity_authority_granted"] is True,
            runtime_authority_granted=data["runtime_authority_granted"] is True,
            claim_boundary=str(data["claim_boundary"]),
            schema_version=str(
                data.get("schema_version", V6_FOUNDATION_SCHEMA_VERSION)
            ),
            artifact_type=str(
                data.get("artifact_type", CONSTRUCTION_OUTCOME_ARTIFACT_TYPE)
            ),
        )
        verify_identity_fields(
            data,
            id_field="construction_id",
            observed_id=result.construction_id,
            observed_hash=result.artifact_hash,
        )
        return result

    @classmethod
    def from_json(cls, text: str) -> "RuleConstructionOutcomeV1":
        document = json.loads(text)
        if not isinstance(document, dict):
            raise V6FoundationError("construction outcome must be a JSON object")
        return cls.from_dict(document)


@dataclass(frozen=True)
class RuleGovernanceOutcomeV1:
    accepted_rule_ref: str
    verifier_result_ref: str
    normal_guard_assessment_ref: str
    inner_utility_assessment_ref: str
    governance_policy_ref: str
    detector_error_context_refs: tuple[str, ...]
    decision: GovernanceDecisionV1
    decision_reason_codes: tuple[str, ...]
    applied_rule_ref: str | None
    label_performance_used: bool
    outer_data_used: bool
    sealed_data_used: bool
    authority_binding_verified: bool
    validity_reassessed: bool
    utility_assessment_only: bool
    provenance_references: tuple[str, ...]
    creation_metadata: CreationMetadataV1
    runtime_authority_granted: bool
    claim_boundary: str
    schema_version: str = V6_FOUNDATION_SCHEMA_VERSION
    artifact_type: str = GOVERNANCE_OUTCOME_ARTIFACT_TYPE

    def __post_init__(self) -> None:
        if self.schema_version != V6_FOUNDATION_SCHEMA_VERSION:
            raise V6FoundationError(
                "unsupported governance outcome schema_version"
            )
        if self.artifact_type != GOVERNANCE_OUTCOME_ARTIFACT_TYPE:
            raise V6FoundationError("invalid governance outcome artifact_type")
        for field_name, value in (
            ("accepted_rule_ref", self.accepted_rule_ref),
            ("verifier_result_ref", self.verifier_result_ref),
            ("normal_guard_assessment_ref", self.normal_guard_assessment_ref),
            ("inner_utility_assessment_ref", self.inner_utility_assessment_ref),
            ("governance_policy_ref", self.governance_policy_ref),
        ):
            require_sha256(value, field_name)
        object.__setattr__(
            self,
            "detector_error_context_refs",
            require_sha256_refs(
                self.detector_error_context_refs,
                "detector_error_context_refs",
            ),
        )
        object.__setattr__(
            self,
            "decision_reason_codes",
            require_unique_strings(
                self.decision_reason_codes,
                "decision_reason_codes",
                allow_empty=False,
            ),
        )
        if self.applied_rule_ref is not None:
            require_sha256(self.applied_rule_ref, "applied_rule_ref")
        if self.decision is GovernanceDecisionV1.SELECTED_RULE:
            if self.applied_rule_ref != self.accepted_rule_ref:
                raise V6FoundationError(
                    "selected_rule must apply the accepted rule"
                )
        else:
            if self.applied_rule_ref is not None:
                raise V6FoundationError("no_op cannot apply a rule")
            if not set(self.decision_reason_codes).issubset(NO_OP_REASON_CODES):
                raise V6FoundationError("no_op reason is not registered")
        if not self.label_performance_used:
            raise V6FoundationError(
                "rule governance requires label-aware inner utility evidence"
            )
        if self.outer_data_used or self.sealed_data_used:
            raise V6FoundationError(
                "rule governance cannot use outer or sealed data"
            )
        if self.authority_binding_verified:
            raise V6FoundationError(
                "P1B cannot verify canonical authority binding"
            )
        if self.validity_reassessed or not self.utility_assessment_only:
            raise V6FoundationError(
                "governance must remain separate from deterministic validity"
            )
        object.__setattr__(
            self,
            "provenance_references",
            require_sha256_refs(
                self.provenance_references,
                "provenance_references",
                allow_empty=False,
            ),
        )
        if self.runtime_authority_granted:
            raise V6FoundationError(
                "P1B governance outcomes cannot grant runtime authority"
            )
        if not self.claim_boundary:
            raise V6FoundationError("claim_boundary is required")

    def _content_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "artifact_type": self.artifact_type,
            "accepted_rule_ref": self.accepted_rule_ref,
            "verifier_result_ref": self.verifier_result_ref,
            "normal_guard_assessment_ref": self.normal_guard_assessment_ref,
            "inner_utility_assessment_ref": self.inner_utility_assessment_ref,
            "governance_policy_ref": self.governance_policy_ref,
            "detector_error_context_refs": list(
                self.detector_error_context_refs
            ),
            "decision": self.decision.value,
            "decision_reason_codes": list(self.decision_reason_codes),
            "applied_rule_ref": self.applied_rule_ref,
            "label_performance_used": self.label_performance_used,
            "outer_data_used": self.outer_data_used,
            "sealed_data_used": self.sealed_data_used,
            "authority_binding_verified": self.authority_binding_verified,
            "validity_reassessed": self.validity_reassessed,
            "utility_assessment_only": self.utility_assessment_only,
            "provenance_references": list(self.provenance_references),
            "creation_metadata": self.creation_metadata.to_dict(),
            "runtime_authority_granted": self.runtime_authority_granted,
            "claim_boundary": self.claim_boundary,
        }

    @property
    def governance_id(self) -> str:
        return deterministic_id("RGO-V1", self._content_dict())

    @property
    def artifact_hash(self) -> str:
        payload = self._content_dict()
        payload["governance_id"] = self.governance_id
        return stable_hash_v1(payload)

    def to_dict(self) -> dict[str, Any]:
        payload = self._content_dict()
        payload["governance_id"] = self.governance_id
        payload["artifact_hash"] = self.artifact_hash
        return payload

    def to_json(self) -> str:
        return canonical_json_v1(self.to_dict())

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "RuleGovernanceOutcomeV1":
        reject_unknown_fields(
            data,
            frozenset(
                {
                    "schema_version",
                    "artifact_type",
                    "governance_id",
                    "artifact_hash",
                    "accepted_rule_ref",
                    "verifier_result_ref",
                    "normal_guard_assessment_ref",
                    "inner_utility_assessment_ref",
                    "governance_policy_ref",
                    "detector_error_context_refs",
                    "decision",
                    "decision_reason_codes",
                    "applied_rule_ref",
                    "label_performance_used",
                    "outer_data_used",
                    "sealed_data_used",
                    "authority_binding_verified",
                    "validity_reassessed",
                    "utility_assessment_only",
                    "provenance_references",
                    "creation_metadata",
                    "runtime_authority_granted",
                    "claim_boundary",
                }
            ),
            GOVERNANCE_OUTCOME_ARTIFACT_TYPE,
        )
        result = cls(
            accepted_rule_ref=str(data["accepted_rule_ref"]),
            verifier_result_ref=str(data["verifier_result_ref"]),
            normal_guard_assessment_ref=str(
                data["normal_guard_assessment_ref"]
            ),
            inner_utility_assessment_ref=str(
                data["inner_utility_assessment_ref"]
            ),
            governance_policy_ref=str(data["governance_policy_ref"]),
            detector_error_context_refs=tuple(
                str(item) for item in data["detector_error_context_refs"]
            ),
            decision=GovernanceDecisionV1(str(data["decision"])),
            decision_reason_codes=tuple(
                str(item) for item in data["decision_reason_codes"]
            ),
            applied_rule_ref=data.get("applied_rule_ref"),
            label_performance_used=data["label_performance_used"] is True,
            outer_data_used=data["outer_data_used"] is True,
            sealed_data_used=data["sealed_data_used"] is True,
            authority_binding_verified=data["authority_binding_verified"] is True,
            validity_reassessed=data["validity_reassessed"] is True,
            utility_assessment_only=data["utility_assessment_only"] is True,
            provenance_references=tuple(
                str(item) for item in data["provenance_references"]
            ),
            creation_metadata=CreationMetadataV1.from_dict(
                data["creation_metadata"]
            ),
            runtime_authority_granted=data["runtime_authority_granted"] is True,
            claim_boundary=str(data["claim_boundary"]),
            schema_version=str(
                data.get("schema_version", V6_FOUNDATION_SCHEMA_VERSION)
            ),
            artifact_type=str(
                data.get("artifact_type", GOVERNANCE_OUTCOME_ARTIFACT_TYPE)
            ),
        )
        verify_identity_fields(
            data,
            id_field="governance_id",
            observed_id=result.governance_id,
            observed_hash=result.artifact_hash,
        )
        return result

    @classmethod
    def from_json(cls, text: str) -> "RuleGovernanceOutcomeV1":
        document = json.loads(text)
        if not isinstance(document, dict):
            raise V6FoundationError("governance outcome must be a JSON object")
        return cls.from_dict(document)


def project_runtime_disposition(
    runtime_trace_shape: Mapping[str, object],
) -> RuntimeDispositionV1:
    """Project canonical trace status without validating runtime authority."""

    reject_unknown_fields(
        runtime_trace_shape,
        frozenset({"status", "abstained", "violation_detected"}),
        "runtime_trace_projection",
    )
    if set(runtime_trace_shape) != {
        "status",
        "abstained",
        "violation_detected",
    }:
        raise V6FoundationError(
            "runtime disposition projection requires exactly three fields"
        )
    status = runtime_trace_shape["status"]
    abstained = runtime_trace_shape["abstained"]
    violation_detected = runtime_trace_shape["violation_detected"]
    if not isinstance(abstained, bool) or not isinstance(violation_detected, bool):
        raise V6FoundationError(
            "runtime disposition booleans must have bool type"
        )
    if status == "evaluated":
        if abstained:
            raise V6FoundationError("evaluated runtime trace cannot abstain")
        return RuntimeDispositionV1.EVALUATED
    if status == "abstained":
        if not abstained or violation_detected:
            raise V6FoundationError(
                "abstention must be explicit and cannot be marked as anomaly"
            )
        return RuntimeDispositionV1.ABSTAIN
    raise V6FoundationError("unknown canonical runtime trace status")
