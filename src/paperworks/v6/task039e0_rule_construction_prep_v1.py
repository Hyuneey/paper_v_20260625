"""Synthetic-only TASK-039E0 rule-construction protocol preparation.

The contracts in this module freeze comparison structure and future input
boundaries.  They do not load D2 results, call a provider, run an Agent,
materialize a canonical rule, or grant validity/runtime authority.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping, Sequence

from paperworks.v6.common import (
    V6_FOUNDATION_SCHEMA_VERSION,
    V6FoundationError,
    freeze_json,
    require_finite,
    require_identifier,
    require_sha256,
    require_sha256_refs,
    stable_hash_v1,
    thaw_json,
)
from paperworks.v6.outcomes_v1 import ConstructionArmV1


TASK_ID = "TASK-039E0-PREP"
BASE_COMMIT = "301fb636b6944e2d2d86be4646605a3d38585165"
BRANCH = "task-039e0-rule-construction-prep"
PREPARATION_STATUS = (
    "passed_task039e0_rule_construction_protocol_preparation"
)

D2_RESULT_CONSUMED = False
REAL_CONFIRMED_RELATION_IDENTITY_CONSUMED = False
HAI_ACCESSED = False
LLM_CALLED = False
AGENT_RUN = False
RULE_V2_CREATED = False
RULE_V2_EXECUTION_AUTHORIZED = False
AGENT_EXECUTION_AUTHORIZED = False
DETECTOR_RUNTIME_AUTHORIZED = False

RELATION_FAMILY = "continuous_step_delayed_response_v1"
MAIN_NUMERIC_ORIGIN = "deterministic_calibrated_evidence"
LLM_DIRECT_NUMBER_ORIGIN = "llm_direct_number_ablation"
PROPOSAL_ARTIFACT_TYPE = "task039e0_rule_proposal_envelope_v1"
PROPOSAL_DSL_FAMILY = "canonical_delayed_response_rule_v1_candidate"
RUNTIME_LOGIC = "missing_expected_delayed_response"
T2_CONTROL_ACTIONS = ("revise", "retrieve", "no_rule")


class TASK039E0PreparationError(V6FoundationError):
    """Raised when a preparation contract fails closed."""


def _nonnegative_integer(value: int, field_name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise TASK039E0PreparationError(
            f"{field_name} must be a non-negative integer"
        )


def _positive_integer(value: int, field_name: str) -> None:
    _nonnegative_integer(value, field_name)
    if value == 0:
        raise TASK039E0PreparationError(f"{field_name} must be positive")


def _exact_false(value: bool, field_name: str) -> None:
    if value is not False:
        raise TASK039E0PreparationError(f"{field_name} must remain false")


@dataclass(frozen=True)
class ConfirmedRelationPrimitiveV1:
    """Generic future construction input bound only to approved references."""

    relation_identity: str
    source: str
    source_step_direction: str
    target: str
    target_response_direction: str
    selected_delay_horizon_seconds: int
    approved_source_threshold_reference: str
    approved_source_stability_reference: str
    approved_target_scale_reference: str
    fit_evidence_reference: str
    confirmation_evidence_reference: str
    relation_family: str = RELATION_FAMILY
    confirmed: bool = True
    rule_authority_granted: bool = False
    runtime_authority_granted: bool = False

    def __post_init__(self) -> None:
        require_identifier(self.relation_identity, "relation_identity")
        require_identifier(self.source, "source")
        require_identifier(self.target, "target")
        if self.source == self.target:
            raise TASK039E0PreparationError("source and target must differ")
        if self.source_step_direction not in {"step_up", "step_down"}:
            raise TASK039E0PreparationError("source direction is invalid")
        if self.target_response_direction not in {"increase", "decrease"}:
            raise TASK039E0PreparationError("target direction is invalid")
        _positive_integer(
            self.selected_delay_horizon_seconds,
            "selected_delay_horizon_seconds",
        )
        if self.relation_family != RELATION_FAMILY:
            raise TASK039E0PreparationError("relation family is not frozen")
        references = (
            self.approved_source_threshold_reference,
            self.approved_source_stability_reference,
            self.approved_target_scale_reference,
            self.fit_evidence_reference,
            self.confirmation_evidence_reference,
        )
        for index, reference in enumerate(references):
            require_sha256(reference, f"relation_reference[{index}]")
        if len(set(references[:3])) != 3:
            raise TASK039E0PreparationError(
                "numeric evidence references must have distinct roles"
            )
        if self.fit_evidence_reference == self.confirmation_evidence_reference:
            raise TASK039E0PreparationError(
                "fit and confirmation evidence references must differ"
            )
        if self.confirmed is not True:
            raise TASK039E0PreparationError(
                "construction primitive must represent a confirmed relation"
            )
        _exact_false(self.rule_authority_granted, "rule_authority_granted")
        _exact_false(
            self.runtime_authority_granted, "runtime_authority_granted"
        )

    def _content_dict(self) -> dict[str, Any]:
        return {
            "schema_version": V6_FOUNDATION_SCHEMA_VERSION,
            "artifact_type": "confirmed_relation_primitive_v1",
            "relation_identity": self.relation_identity,
            "relation_family": self.relation_family,
            "source": self.source,
            "source_step_direction": self.source_step_direction,
            "target": self.target,
            "target_response_direction": self.target_response_direction,
            "selected_delay_horizon_seconds": (
                self.selected_delay_horizon_seconds
            ),
            "approved_source_threshold_reference": (
                self.approved_source_threshold_reference
            ),
            "approved_source_stability_reference": (
                self.approved_source_stability_reference
            ),
            "approved_target_scale_reference": (
                self.approved_target_scale_reference
            ),
            "fit_evidence_reference": self.fit_evidence_reference,
            "confirmation_evidence_reference": (
                self.confirmation_evidence_reference
            ),
            "confirmed": self.confirmed,
            "rule_authority_granted": self.rule_authority_granted,
            "runtime_authority_granted": self.runtime_authority_granted,
        }

    @property
    def binding_hash(self) -> str:
        return stable_hash_v1(self._content_dict())

    def to_dict(self) -> dict[str, Any]:
        payload = self._content_dict()
        payload["binding_hash"] = self.binding_hash
        return payload


@dataclass(frozen=True)
class ApprovedNumericEvidenceBundleV1:
    """Reference-only numeric authority for all four main construction arms."""

    relation_binding_hash: str
    source_threshold_reference: str
    source_stability_reference: str
    target_scale_reference: str
    fit_evidence_reference: str
    confirmation_evidence_reference: str
    preregistered_window_constant_references: tuple[str, ...]
    numeric_origin: str = MAIN_NUMERIC_ORIGIN
    approved: bool = True
    raw_numeric_values_included: bool = False
    arbitrary_numeric_literals_allowed: bool = False

    def __post_init__(self) -> None:
        for field_name in (
            "relation_binding_hash",
            "source_threshold_reference",
            "source_stability_reference",
            "target_scale_reference",
            "fit_evidence_reference",
            "confirmation_evidence_reference",
        ):
            require_sha256(getattr(self, field_name), field_name)
        object.__setattr__(
            self,
            "preregistered_window_constant_references",
            require_sha256_refs(
                self.preregistered_window_constant_references,
                "preregistered_window_constant_references",
                allow_empty=False,
            ),
        )
        if self.numeric_origin != MAIN_NUMERIC_ORIGIN:
            raise TASK039E0PreparationError(
                "main numeric origin must be deterministic calibrated evidence"
            )
        if self.approved is not True:
            raise TASK039E0PreparationError("numeric evidence must be approved")
        _exact_false(
            self.raw_numeric_values_included, "raw_numeric_values_included"
        )
        _exact_false(
            self.arbitrary_numeric_literals_allowed,
            "arbitrary_numeric_literals_allowed",
        )

    def assert_matches(self, relation: ConfirmedRelationPrimitiveV1) -> None:
        expected = {
            "relation_binding_hash": relation.binding_hash,
            "source_threshold_reference": (
                relation.approved_source_threshold_reference
            ),
            "source_stability_reference": (
                relation.approved_source_stability_reference
            ),
            "target_scale_reference": relation.approved_target_scale_reference,
            "fit_evidence_reference": relation.fit_evidence_reference,
            "confirmation_evidence_reference": (
                relation.confirmation_evidence_reference
            ),
        }
        if any(getattr(self, key) != value for key, value in expected.items()):
            raise TASK039E0PreparationError(
                "numeric evidence bundle does not bind the confirmed relation"
            )

    def _content_dict(self) -> dict[str, Any]:
        return {
            "schema_version": V6_FOUNDATION_SCHEMA_VERSION,
            "artifact_type": "approved_numeric_evidence_bundle_v1",
            "relation_binding_hash": self.relation_binding_hash,
            "source_threshold_reference": self.source_threshold_reference,
            "source_stability_reference": self.source_stability_reference,
            "target_scale_reference": self.target_scale_reference,
            "fit_evidence_reference": self.fit_evidence_reference,
            "confirmation_evidence_reference": (
                self.confirmation_evidence_reference
            ),
            "preregistered_window_constant_references": list(
                self.preregistered_window_constant_references
            ),
            "numeric_origin": self.numeric_origin,
            "approved": self.approved,
            "raw_numeric_values_included": self.raw_numeric_values_included,
            "arbitrary_numeric_literals_allowed": (
                self.arbitrary_numeric_literals_allowed
            ),
        }

    @property
    def artifact_hash(self) -> str:
        return stable_hash_v1(self._content_dict())

    def to_dict(self) -> dict[str, Any]:
        payload = self._content_dict()
        payload["artifact_hash"] = self.artifact_hash
        return payload


@dataclass(frozen=True)
class ConstructionArmProtocolV1:
    """One preregistered main comparison arm."""

    arm: ConstructionArmV1
    deterministic_template: bool
    llm_generation: bool
    one_shot: bool
    independent_generation: bool
    verifier_feedback_allowed: bool
    allowed_control_actions: tuple[str, ...]
    generation_call_budget_binding: str
    numeric_origin: str = MAIN_NUMERIC_ORIGIN

    def __post_init__(self) -> None:
        expected: dict[ConstructionArmV1, tuple[Any, ...]] = {
            ConstructionArmV1.T0: (
                True,
                False,
                False,
                False,
                False,
                (),
                "zero_calls",
            ),
            ConstructionArmV1.T1: (
                False,
                True,
                True,
                False,
                False,
                (),
                "exactly_one_generation_call",
            ),
            ConstructionArmV1.T1_B: (
                False,
                True,
                False,
                True,
                False,
                (),
                "equals_t2_maximum_generation_calls",
            ),
            ConstructionArmV1.T2: (
                False,
                True,
                False,
                False,
                True,
                T2_CONTROL_ACTIONS,
                "precommitted_maximum_generation_calls",
            ),
        }
        observed = (
            self.deterministic_template,
            self.llm_generation,
            self.one_shot,
            self.independent_generation,
            self.verifier_feedback_allowed,
            self.allowed_control_actions,
            self.generation_call_budget_binding,
        )
        if observed != expected[self.arm]:
            raise TASK039E0PreparationError(
                f"{self.arm.value} protocol differs from the frozen comparison"
            )
        if self.numeric_origin != MAIN_NUMERIC_ORIGIN:
            raise TASK039E0PreparationError(
                "main construction arms must use calibrated numeric evidence"
            )

    @property
    def protocol_hash(self) -> str:
        return stable_hash_v1(self.to_dict())

    def to_dict(self) -> dict[str, Any]:
        return {
            "arm": self.arm.value,
            "deterministic_template": self.deterministic_template,
            "llm_generation": self.llm_generation,
            "one_shot": self.one_shot,
            "independent_generation": self.independent_generation,
            "verifier_feedback_allowed": self.verifier_feedback_allowed,
            "allowed_control_actions": list(self.allowed_control_actions),
            "generation_call_budget_binding": (
                self.generation_call_budget_binding
            ),
            "numeric_origin": self.numeric_origin,
        }


FROZEN_ARM_PROTOCOLS = (
    ConstructionArmProtocolV1(
        ConstructionArmV1.T0,
        True,
        False,
        False,
        False,
        False,
        (),
        "zero_calls",
    ),
    ConstructionArmProtocolV1(
        ConstructionArmV1.T1,
        False,
        True,
        True,
        False,
        False,
        (),
        "exactly_one_generation_call",
    ),
    ConstructionArmProtocolV1(
        ConstructionArmV1.T1_B,
        False,
        True,
        False,
        True,
        False,
        (),
        "equals_t2_maximum_generation_calls",
    ),
    ConstructionArmProtocolV1(
        ConstructionArmV1.T2,
        False,
        True,
        False,
        False,
        True,
        T2_CONTROL_ACTIONS,
        "precommitted_maximum_generation_calls",
    ),
)


@dataclass(frozen=True)
class FairGenerationBudgetPolicyV1:
    """Concrete future budget precommit; PREP intentionally has no default."""

    policy_id: str
    t1b_total_generation_calls: int
    t2_maximum_total_generation_calls: int
    t0_total_generation_calls: int = 0
    t1_total_generation_calls: int = 1
    frozen_before_relation_identities_visible: bool = True
    frozen_before_proposals_visible: bool = True
    result_dependent_extra_calls: bool = False
    scientific_generation_retry_policy: str = "none"
    transport_retry_policy: str = (
        "separate_preregistered_transport_retry_only"
    )

    def __post_init__(self) -> None:
        require_identifier(self.policy_id, "policy_id")
        for field_name in (
            "t0_total_generation_calls",
            "t1_total_generation_calls",
            "t1b_total_generation_calls",
            "t2_maximum_total_generation_calls",
        ):
            _nonnegative_integer(getattr(self, field_name), field_name)
        if self.t0_total_generation_calls != 0:
            raise TASK039E0PreparationError("T0 must remain zero-call")
        if self.t1_total_generation_calls != 1:
            raise TASK039E0PreparationError("T1 must remain one-shot")
        if self.t1b_total_generation_calls < 2:
            raise TASK039E0PreparationError(
                "T1-B must be an independent repeated-generation arm"
            )
        if (
            self.t1b_total_generation_calls
            != self.t2_maximum_total_generation_calls
        ):
            raise TASK039E0PreparationError(
                "T1-B total calls must equal T2 maximum total calls"
            )
        if (
            self.frozen_before_relation_identities_visible is not True
            or self.frozen_before_proposals_visible is not True
        ):
            raise TASK039E0PreparationError(
                "generation budget must freeze before identities and proposals"
            )
        _exact_false(
            self.result_dependent_extra_calls, "result_dependent_extra_calls"
        )
        if self.scientific_generation_retry_policy != "none":
            raise TASK039E0PreparationError(
                "hidden scientific generation retries are prohibited"
            )
        if self.transport_retry_policy != (
            "separate_preregistered_transport_retry_only"
        ):
            raise TASK039E0PreparationError(
                "transport retry policy must remain separate and preregistered"
            )

    def _content_dict(self) -> dict[str, Any]:
        return {
            "schema_version": V6_FOUNDATION_SCHEMA_VERSION,
            "artifact_type": "fair_generation_budget_policy_v1",
            "policy_id": self.policy_id,
            "t0_total_generation_calls": self.t0_total_generation_calls,
            "t1_total_generation_calls": self.t1_total_generation_calls,
            "t1b_total_generation_calls": self.t1b_total_generation_calls,
            "t2_maximum_total_generation_calls": (
                self.t2_maximum_total_generation_calls
            ),
            "frozen_before_relation_identities_visible": (
                self.frozen_before_relation_identities_visible
            ),
            "frozen_before_proposals_visible": (
                self.frozen_before_proposals_visible
            ),
            "result_dependent_extra_calls": self.result_dependent_extra_calls,
            "scientific_generation_retry_policy": (
                self.scientific_generation_retry_policy
            ),
            "transport_retry_policy": self.transport_retry_policy,
        }

    @property
    def artifact_hash(self) -> str:
        return stable_hash_v1(self._content_dict())

    def to_dict(self) -> dict[str, Any]:
        payload = self._content_dict()
        payload["artifact_hash"] = self.artifact_hash
        return payload


@dataclass(frozen=True)
class LLMDirectNumberAblationPolicyV1:
    """Isolated future ablation; never a main method or authority source."""

    policy_id: str
    designated_main_comparator: ConstructionArmV1
    comparator_budget_policy_hash: str
    budget_binding: str = "match_designated_main_comparator"
    numeric_origin: str = LLM_DIRECT_NUMBER_ORIGIN
    isolated_from_main_arms: bool = True
    main_numeric_evidence_reused: bool = False
    replaces_main_calibrated_method: bool = False
    execute_in_preparation: bool = False
    validity_authority_granted: bool = False
    runtime_authority_granted: bool = False

    def __post_init__(self) -> None:
        require_identifier(self.policy_id, "policy_id")
        if self.designated_main_comparator not in {
            ConstructionArmV1.T1,
            ConstructionArmV1.T1_B,
            ConstructionArmV1.T2,
        }:
            raise TASK039E0PreparationError(
                "direct-number ablation requires an LLM main comparator"
            )
        require_sha256(
            self.comparator_budget_policy_hash,
            "comparator_budget_policy_hash",
        )
        if self.budget_binding != "match_designated_main_comparator":
            raise TASK039E0PreparationError(
                "ablation call budget must match its designated comparator"
            )
        if self.numeric_origin != LLM_DIRECT_NUMBER_ORIGIN:
            raise TASK039E0PreparationError("ablation numeric origin is invalid")
        if self.isolated_from_main_arms is not True:
            raise TASK039E0PreparationError("ablation must remain isolated")
        for field_name in (
            "main_numeric_evidence_reused",
            "replaces_main_calibrated_method",
            "execute_in_preparation",
            "validity_authority_granted",
            "runtime_authority_granted",
        ):
            _exact_false(getattr(self, field_name), field_name)

    @property
    def artifact_hash(self) -> str:
        return stable_hash_v1(
            {
                "policy_id": self.policy_id,
                "designated_main_comparator": (
                    self.designated_main_comparator.value
                ),
                "comparator_budget_policy_hash": (
                    self.comparator_budget_policy_hash
                ),
                "budget_binding": self.budget_binding,
                "numeric_origin": self.numeric_origin,
                "isolated_from_main_arms": self.isolated_from_main_arms,
                "main_numeric_evidence_reused": (
                    self.main_numeric_evidence_reused
                ),
                "replaces_main_calibrated_method": (
                    self.replaces_main_calibrated_method
                ),
                "execute_in_preparation": self.execute_in_preparation,
                "validity_authority_granted": self.validity_authority_granted,
                "runtime_authority_granted": self.runtime_authority_granted,
            }
        )


class CallAcceptedStateV1(str, Enum):
    CANDIDATE_PROPOSED = "candidate_proposed"
    ACCEPTED = "accepted"
    NO_RULE = "no_rule"
    REJECTED = "rejected"


@dataclass(frozen=True)
class FutureGenerationCallRecordV1:
    """Receipt contract for future calls; instantiation performs no call."""

    construction_arm: ConstructionArmV1
    model_identifier: str
    provider_identifier: str
    prompt_template_version: str
    temperature: float
    decoding_settings: Mapping[str, Any]
    seed: int | None
    seed_exposed: bool
    call_number: int
    evidence_bundle_hash: str
    verifier_feedback_hash: str | None
    proposal_hash: str
    accepted_state: CallAcceptedStateV1
    total_calls_consumed: int
    independent_generation: bool
    transport_retry_count: int = 0
    transport_retries_scientific_generation: bool = False
    raw_prompt_stored: bool = False
    chain_of_thought_stored: bool = False
    raw_evidence_rows_stored: bool = False
    runtime_authority_granted: bool = False

    def __post_init__(self) -> None:
        if self.construction_arm not in {
            ConstructionArmV1.T1,
            ConstructionArmV1.T1_B,
            ConstructionArmV1.T2,
        }:
            raise TASK039E0PreparationError(
                "generation call record is only for LLM construction arms"
            )
        for field_name in (
            "model_identifier",
            "provider_identifier",
            "prompt_template_version",
        ):
            require_identifier(getattr(self, field_name), field_name)
        temperature = require_finite(self.temperature, "temperature")
        if temperature < 0.0:
            raise TASK039E0PreparationError("temperature must be non-negative")
        object.__setattr__(
            self, "decoding_settings", freeze_json(self.decoding_settings)
        )
        if self.seed_exposed:
            if isinstance(self.seed, bool) or not isinstance(self.seed, int):
                raise TASK039E0PreparationError(
                    "exposed provider seed must be an integer"
                )
        elif self.seed is not None:
            raise TASK039E0PreparationError(
                "seed must be null when provider does not expose it"
            )
        _positive_integer(self.call_number, "call_number")
        _positive_integer(self.total_calls_consumed, "total_calls_consumed")
        if self.total_calls_consumed < self.call_number:
            raise TASK039E0PreparationError(
                "total calls consumed cannot precede call number"
            )
        require_sha256(self.evidence_bundle_hash, "evidence_bundle_hash")
        require_sha256(self.proposal_hash, "proposal_hash")
        if self.verifier_feedback_hash is not None:
            require_sha256(
                self.verifier_feedback_hash, "verifier_feedback_hash"
            )
        if self.construction_arm is ConstructionArmV1.T1:
            if self.call_number != 1 or self.verifier_feedback_hash is not None:
                raise TASK039E0PreparationError(
                    "T1 is one-shot and cannot receive verifier feedback"
                )
        if self.construction_arm is ConstructionArmV1.T1_B:
            if (
                self.independent_generation is not True
                or self.verifier_feedback_hash is not None
            ):
                raise TASK039E0PreparationError(
                    "T1-B calls must be independent and feedback-free"
                )
        elif self.independent_generation:
            raise TASK039E0PreparationError(
                "independent generation is reserved for T1-B"
            )
        if (
            self.construction_arm is ConstructionArmV1.T2
            and self.call_number == 1
            and self.verifier_feedback_hash is not None
        ):
            raise TASK039E0PreparationError(
                "the first T2 call cannot have verifier feedback"
            )
        _nonnegative_integer(
            self.transport_retry_count, "transport_retry_count"
        )
        for field_name in (
            "transport_retries_scientific_generation",
            "raw_prompt_stored",
            "chain_of_thought_stored",
            "raw_evidence_rows_stored",
            "runtime_authority_granted",
        ):
            _exact_false(getattr(self, field_name), field_name)

    @property
    def artifact_hash(self) -> str:
        return stable_hash_v1(self._content_dict())

    def _content_dict(self) -> dict[str, Any]:
        return {
            "schema_version": V6_FOUNDATION_SCHEMA_VERSION,
            "artifact_type": "future_generation_call_record_v1",
            "construction_arm": self.construction_arm.value,
            "model_identifier": self.model_identifier,
            "provider_identifier": self.provider_identifier,
            "prompt_template_version": self.prompt_template_version,
            "temperature": self.temperature,
            "decoding_settings": thaw_json(self.decoding_settings),
            "seed": self.seed,
            "seed_exposed": self.seed_exposed,
            "call_number": self.call_number,
            "evidence_bundle_hash": self.evidence_bundle_hash,
            "verifier_feedback_hash": self.verifier_feedback_hash,
            "proposal_hash": self.proposal_hash,
            "accepted_state": self.accepted_state.value,
            "total_calls_consumed": self.total_calls_consumed,
            "independent_generation": self.independent_generation,
            "transport_retry_count": self.transport_retry_count,
            "transport_retries_scientific_generation": (
                self.transport_retries_scientific_generation
            ),
            "raw_prompt_stored": self.raw_prompt_stored,
            "chain_of_thought_stored": self.chain_of_thought_stored,
            "raw_evidence_rows_stored": self.raw_evidence_rows_stored,
            "runtime_authority_granted": self.runtime_authority_granted,
        }

    def to_dict(self) -> dict[str, Any]:
        payload = self._content_dict()
        payload["artifact_hash"] = self.artifact_hash
        return payload


@dataclass(frozen=True)
class ProposalConstructionProvenanceV1:
    """Construction provenance binding usable by synthetic proposal envelopes."""

    construction_arm: ConstructionArmV1
    arm_protocol_hash: str
    budget_policy_hash: str
    evidence_bundle_hash: str
    prompt_template_version: str
    execution_state: str
    future_call_record_refs: tuple[str, ...]
    model_identifier: str
    provider_identifier: str
    llm_called_in_preparation: bool = False
    agent_run_in_preparation: bool = False
    runtime_authority_granted: bool = False

    def __post_init__(self) -> None:
        for field_name in (
            "arm_protocol_hash",
            "budget_policy_hash",
            "evidence_bundle_hash",
        ):
            require_sha256(getattr(self, field_name), field_name)
        require_identifier(
            self.prompt_template_version, "prompt_template_version"
        )
        if self.execution_state not in {
            "synthetic_preparation",
            "future_recorded_execution",
        }:
            raise TASK039E0PreparationError("execution_state is invalid")
        object.__setattr__(
            self,
            "future_call_record_refs",
            require_sha256_refs(
                self.future_call_record_refs,
                "future_call_record_refs",
            ),
        )
        require_identifier(self.model_identifier, "model_identifier")
        require_identifier(self.provider_identifier, "provider_identifier")
        if self.execution_state == "synthetic_preparation":
            if self.future_call_record_refs:
                raise TASK039E0PreparationError(
                    "synthetic preparation cannot claim future call receipts"
                )
        elif (
            self.construction_arm is not ConstructionArmV1.T0
            and not self.future_call_record_refs
        ):
            raise TASK039E0PreparationError(
                "future LLM execution provenance requires call receipts"
            )
        if self.construction_arm is ConstructionArmV1.T0:
            if (
                self.model_identifier != "not_applicable"
                or self.provider_identifier != "not_applicable"
                or self.future_call_record_refs
            ):
                raise TASK039E0PreparationError(
                    "T0 provenance cannot identify a model, provider, or call"
                )
        for field_name in (
            "llm_called_in_preparation",
            "agent_run_in_preparation",
            "runtime_authority_granted",
        ):
            _exact_false(getattr(self, field_name), field_name)

    def _content_dict(self) -> dict[str, Any]:
        return {
            "construction_arm": self.construction_arm.value,
            "arm_protocol_hash": self.arm_protocol_hash,
            "budget_policy_hash": self.budget_policy_hash,
            "evidence_bundle_hash": self.evidence_bundle_hash,
            "prompt_template_version": self.prompt_template_version,
            "execution_state": self.execution_state,
            "future_call_record_refs": list(self.future_call_record_refs),
            "model_identifier": self.model_identifier,
            "provider_identifier": self.provider_identifier,
            "llm_called_in_preparation": self.llm_called_in_preparation,
            "agent_run_in_preparation": self.agent_run_in_preparation,
            "runtime_authority_granted": self.runtime_authority_granted,
        }

    @property
    def artifact_hash(self) -> str:
        return stable_hash_v1(self._content_dict())


@dataclass(frozen=True)
class T2ControlActionV1:
    action: str
    verifier_feedback_hash: str | None = None
    retrieved_evidence_reference: str | None = None
    no_rule_reason_code: str | None = None

    def __post_init__(self) -> None:
        if self.action not in T2_CONTROL_ACTIONS:
            raise TASK039E0PreparationError("T2 control action is not allowed")
        if self.verifier_feedback_hash is not None:
            require_sha256(
                self.verifier_feedback_hash, "verifier_feedback_hash"
            )
        if self.retrieved_evidence_reference is not None:
            require_sha256(
                self.retrieved_evidence_reference,
                "retrieved_evidence_reference",
            )
        if self.action == "revise":
            if (
                self.verifier_feedback_hash is None
                or self.retrieved_evidence_reference is not None
                or self.no_rule_reason_code is not None
            ):
                raise TASK039E0PreparationError(
                    "revise requires only bounded verifier feedback"
                )
        elif self.action == "retrieve":
            if (
                self.retrieved_evidence_reference is None
                or self.verifier_feedback_hash is not None
                or self.no_rule_reason_code is not None
            ):
                raise TASK039E0PreparationError(
                    "retrieve requires only an approved evidence reference"
                )
        elif (
            not self.no_rule_reason_code
            or self.verifier_feedback_hash is not None
            or self.retrieved_evidence_reference is not None
        ):
            raise TASK039E0PreparationError(
                "no_rule requires only a bounded reason code"
            )
        else:
            require_identifier(self.no_rule_reason_code, "no_rule_reason_code")


@dataclass(frozen=True)
class T2BudgetTransitionV1:
    action: str
    calls_before: int
    calls_after: int
    state: str


def forecast_t2_budget_transition_v1(
    *,
    calls_consumed: int,
    action: T2ControlActionV1,
    budget: FairGenerationBudgetPolicyV1,
) -> T2BudgetTransitionV1:
    """Pure budget forecast; it does not run an Agent or make a call."""

    _nonnegative_integer(calls_consumed, "calls_consumed")
    maximum = budget.t2_maximum_total_generation_calls
    if calls_consumed > maximum:
        raise TASK039E0PreparationError("calls already exceed the T2 maximum")
    if action.action == "no_rule":
        return T2BudgetTransitionV1(
            action.action, calls_consumed, calls_consumed, "no_rule"
        )
    if action.action == "retrieve":
        return T2BudgetTransitionV1(
            action.action, calls_consumed, calls_consumed, "active"
        )
    if calls_consumed >= maximum:
        return T2BudgetTransitionV1(
            action.action, calls_consumed, calls_consumed, "budget_exhausted"
        )
    return T2BudgetTransitionV1(
        action.action, calls_consumed, calls_consumed + 1, "active"
    )


def canonical_proposal_hash_v1(document: Mapping[str, Any]) -> str:
    payload = {
        key: value for key, value in document.items() if key != "proposal_hash"
    }
    return stable_hash_v1(payload)


def prepare_rule_proposal_envelope_v1(
    *,
    relation: ConfirmedRelationPrimitiveV1,
    numeric_evidence: ApprovedNumericEvidenceBundleV1,
    provenance: ProposalConstructionProvenanceV1,
) -> dict[str, Any]:
    """Create a bounded proposal envelope, never a canonical or accepted rule."""

    numeric_evidence.assert_matches(relation)
    arm_protocol = next(
        item for item in FROZEN_ARM_PROTOCOLS if item.arm is provenance.construction_arm
    )
    if provenance.arm_protocol_hash != arm_protocol.protocol_hash:
        raise TASK039E0PreparationError("construction arm protocol hash mismatch")
    if provenance.evidence_bundle_hash != numeric_evidence.artifact_hash:
        raise TASK039E0PreparationError("construction evidence hash mismatch")
    document: dict[str, Any] = {
        "schema_version": V6_FOUNDATION_SCHEMA_VERSION,
        "artifact_type": PROPOSAL_ARTIFACT_TYPE,
        "construction_arm": provenance.construction_arm.value,
        "dsl_family": PROPOSAL_DSL_FAMILY,
        "relation_binding_hash": relation.binding_hash,
        "relation_identity": relation.relation_identity,
        "source": relation.source,
        "source_step_direction": relation.source_step_direction,
        "target": relation.target,
        "target_response_direction": relation.target_response_direction,
        "selected_delay_horizon_seconds": (
            relation.selected_delay_horizon_seconds
        ),
        "numeric_origin": numeric_evidence.numeric_origin,
        "source_threshold_reference": (
            numeric_evidence.source_threshold_reference
        ),
        "source_stability_reference": (
            numeric_evidence.source_stability_reference
        ),
        "target_scale_reference": numeric_evidence.target_scale_reference,
        "fit_evidence_reference": numeric_evidence.fit_evidence_reference,
        "confirmation_evidence_reference": (
            numeric_evidence.confirmation_evidence_reference
        ),
        "preregistered_window_constant_references": list(
            numeric_evidence.preregistered_window_constant_references
        ),
        "variables": [relation.source, relation.target],
        "runtime_logic": RUNTIME_LOGIC,
        "free_text_runtime_logic": None,
        "numeric_literals": [],
        "prohibited_data_references": [],
        "construction_provenance_hash": provenance.artifact_hash,
        "canonical_rule_materialized": False,
        "validity_authority_granted": False,
        "runtime_authority_granted": False,
    }
    document["proposal_hash"] = canonical_proposal_hash_v1(document)
    return document


@dataclass(frozen=True)
class ValidityUtilitySeparationPolicyV1:
    validity_is_deterministic: bool = True
    validity_is_label_free: bool = True
    validity_is_construction_time: bool = True
    utility_is_separate_future_stage: bool = True
    utility_requires_explicit_authorization: bool = True
    utility_may_influence_validity: bool = False

    def __post_init__(self) -> None:
        if not all(
            (
                self.validity_is_deterministic,
                self.validity_is_label_free,
                self.validity_is_construction_time,
                self.utility_is_separate_future_stage,
                self.utility_requires_explicit_authorization,
            )
        ) or self.utility_may_influence_validity:
            raise TASK039E0PreparationError(
                "validity and utility separation is frozen"
            )


@dataclass(frozen=True)
class RuntimeBoundaryPolicyV1:
    construction_time_llm_only: bool = True
    runtime_llm_allowed: bool = False
    proposal_auto_authorizes_runtime: bool = False
    deterministic_validity_auto_authorizes_runtime: bool = False
    later_governance_required: bool = True

    def __post_init__(self) -> None:
        if (
            self.construction_time_llm_only is not True
            or self.runtime_llm_allowed
            or self.proposal_auto_authorizes_runtime
            or self.deterministic_validity_auto_authorizes_runtime
            or self.later_governance_required is not True
        ):
            raise TASK039E0PreparationError("runtime boundary is frozen")


@dataclass(frozen=True)
class ConstructionMetricPolicyV1:
    rule_construction_success_formula: str = (
        "rule_candidate_outcomes/eligible_construction_attempts"
    )
    no_rule_rate_formula: str = "no_rule_outcomes/eligible_construction_attempts"
    abstention_rate_formula: str = (
        "runtime_abstentions/authorized_runtime_evaluation_opportunities"
    )
    valid_rule_rate_formula: str = (
        "deterministically_valid_candidates/rule_candidate_outcomes"
    )
    explanation_rule_coverage_formula: str = (
        "trace_grounded_explanations/authorized_runtime_rule_firings"
    )
    no_rule_is_system_failure: bool = False
    abstention_is_no_rule: bool = False

    def __post_init__(self) -> None:
        for field_name in (
            "rule_construction_success_formula",
            "no_rule_rate_formula",
            "abstention_rate_formula",
            "valid_rule_rate_formula",
            "explanation_rule_coverage_formula",
        ):
            if not getattr(self, field_name):
                raise TASK039E0PreparationError("metric formula is required")
        _exact_false(
            self.no_rule_is_system_failure, "no_rule_is_system_failure"
        )
        _exact_false(self.abstention_is_no_rule, "abstention_is_no_rule")


FROZEN_VALIDITY_UTILITY_POLICY = ValidityUtilitySeparationPolicyV1()
FROZEN_RUNTIME_BOUNDARY = RuntimeBoundaryPolicyV1()
FROZEN_METRIC_POLICY = ConstructionMetricPolicyV1()


def assert_preparation_boundary_v1(
    *,
    d2_result: object | None = None,
    confirmed_real_relation_identity: object | None = None,
    hai_input: object | None = None,
    provider: object | None = None,
    agent: object | None = None,
) -> None:
    """Reject every real or executable input before any external operation."""

    if any(
        item is not None
        for item in (
            d2_result,
            confirmed_real_relation_identity,
            hai_input,
            provider,
            agent,
        )
    ):
        raise TASK039E0PreparationError(
            "TASK-039E0-PREP accepts no real result, data, provider, or Agent"
        )


__all__ = [
    "AGENT_EXECUTION_AUTHORIZED",
    "AGENT_RUN",
    "ApprovedNumericEvidenceBundleV1",
    "BASE_COMMIT",
    "BRANCH",
    "CallAcceptedStateV1",
    "ConfirmedRelationPrimitiveV1",
    "ConstructionArmProtocolV1",
    "ConstructionMetricPolicyV1",
    "D2_RESULT_CONSUMED",
    "DETECTOR_RUNTIME_AUTHORIZED",
    "FairGenerationBudgetPolicyV1",
    "FROZEN_ARM_PROTOCOLS",
    "FROZEN_METRIC_POLICY",
    "FROZEN_RUNTIME_BOUNDARY",
    "FROZEN_VALIDITY_UTILITY_POLICY",
    "FutureGenerationCallRecordV1",
    "HAI_ACCESSED",
    "LLMDirectNumberAblationPolicyV1",
    "LLM_CALLED",
    "MAIN_NUMERIC_ORIGIN",
    "PREPARATION_STATUS",
    "PROPOSAL_ARTIFACT_TYPE",
    "PROPOSAL_DSL_FAMILY",
    "ProposalConstructionProvenanceV1",
    "REAL_CONFIRMED_RELATION_IDENTITY_CONSUMED",
    "RULE_V2_CREATED",
    "RULE_V2_EXECUTION_AUTHORIZED",
    "RUNTIME_LOGIC",
    "RuntimeBoundaryPolicyV1",
    "T2BudgetTransitionV1",
    "T2ControlActionV1",
    "TASK039E0PreparationError",
    "T2_CONTROL_ACTIONS",
    "ValidityUtilitySeparationPolicyV1",
    "assert_preparation_boundary_v1",
    "canonical_proposal_hash_v1",
    "forecast_t2_budget_transition_v1",
    "prepare_rule_proposal_envelope_v1",
]
