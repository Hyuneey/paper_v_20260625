"""Authoritative TASK-039E0 construction-protocol freeze.

This module consumes only audited public D2 identities.  It never reads HAI,
opens a private D1/D2 ledger, generates a proposal, calls a provider, or
grants rule/runtime authority.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Any, Mapping, Sequence

from paperworks.v6.common import (
    V6_FOUNDATION_SCHEMA_VERSION,
    V6FoundationError,
    canonical_json_v1,
    require_identifier,
    require_sha256,
    stable_hash_v1,
)
from paperworks.v6.task039e0_validity_v1 import ValidityIssueCodeV1


TASK_ID = "TASK-039E0"
STATUS = "passed_task039e0_rule_construction_protocol_freeze"
PROCESS = "P1"
RELATION_FAMILY = "continuous_step_delayed_response_v1"
EXPECTED_RELATIONS = 42
EXPECTED_PAIRS = 23
E0_AUTHORIZATION_HASH = (
    "d209b8332705535b8addc62e186e834288ab7c12f8454e8be85265321b663ae6"
)
D2_RESULT_HASH = (
    "3b5bdce629b6ed2bcf26751fae4e870cb63cac1e9fd3e5d3022085615c3ad09d"
)
D2_DIRECTIONAL_SUMMARY_HASH = (
    "4f5057380c4b1b995bd0d5a714d307df556ce05094223fa909b6e2ed7dfec666"
)
D2_PAIR_SUMMARY_HASH = (
    "3929e84c680422a75069d59e1bef756f054a476ecc95f3e4e9573c7dfe368ad5"
)
D1_SOURCE_LEDGER_HASH = (
    "3eb6ff199dbc67b183d35a804754e557bdfa869a899c754e551cd77e8dcfb304"
)
D1_TARGET_LEDGER_HASH = (
    "f36f4b424c85b228043f9685a22a25c73d6b165e28714b627cf51e8bbb77f96e"
)
D1_DIRECTIONAL_LEDGER_HASH = (
    "e372d7ccf4a7dde5f7ccd91049cc73b443b3b19a3a0c563f451aea50e8faddc7"
)
D2_PRIVATE_LEDGER_HASH = (
    "d349421ae9a866b924c329dcb2546088466866e09f45851ec5d18090509dc062"
)


class TASK039E0ProtocolError(V6FoundationError):
    """Raised when the authoritative E0 protocol differs from the freeze."""


def _require_false(value: bool, name: str) -> None:
    if value is not False:
        raise TASK039E0ProtocolError(f"{name} must remain false")


def _require_true(value: bool, name: str) -> None:
    if value is not True:
        raise TASK039E0ProtocolError(f"{name} must remain true")


def _with_hash(payload: Mapping[str, Any]) -> dict[str, Any]:
    result = dict(payload)
    result["artifact_hash"] = stable_hash_v1(payload)
    return result


def verify_self_hash_v1(document: Mapping[str, Any]) -> bool:
    supplied = document.get("artifact_hash")
    if not isinstance(supplied, str):
        return False
    payload = {key: value for key, value in document.items() if key != "artifact_hash"}
    return stable_hash_v1(payload) == supplied


def _identity_content(
    source: str,
    source_step_direction: str,
    target: str,
    target_response_direction: str,
) -> dict[str, str]:
    return {
        "source": source,
        "source_step_direction": source_step_direction,
        "target": target,
        "target_response_direction": target_response_direction,
        "relation_family": RELATION_FAMILY,
    }


@dataclass(frozen=True)
class ConfirmedRelationIdentityV1:
    source: str
    source_step_direction: str
    target: str
    target_response_direction: str
    selected_delay_horizon_seconds: int
    d1_directional_record_hash: str
    d2_confirmation_record_hash: str
    d2_result_hash: str = D2_RESULT_HASH
    relation_family: str = RELATION_FAMILY

    def __post_init__(self) -> None:
        require_identifier(self.source, "source")
        require_identifier(self.target, "target")
        if self.source == self.target:
            raise TASK039E0ProtocolError("source and target must differ")
        if self.source_step_direction not in {"step_up", "step_down"}:
            raise TASK039E0ProtocolError("source step direction is invalid")
        if self.target_response_direction not in {"increase", "decrease"}:
            raise TASK039E0ProtocolError("target response direction is invalid")
        if (
            isinstance(self.selected_delay_horizon_seconds, bool)
            or self.selected_delay_horizon_seconds not in {1, 5, 10, 30, 60}
        ):
            raise TASK039E0ProtocolError("selected horizon is outside the freeze")
        for name in (
            "d1_directional_record_hash",
            "d2_confirmation_record_hash",
            "d2_result_hash",
        ):
            require_sha256(getattr(self, name), name)
        if self.d2_result_hash != D2_RESULT_HASH:
            raise TASK039E0ProtocolError("D2 result hash differs from the audit")
        if self.relation_family != RELATION_FAMILY:
            raise TASK039E0ProtocolError("relation family differs from the freeze")

    @property
    def relation_identity(self) -> str:
        return "directional_relation:" + stable_hash_v1(
            _identity_content(
                self.source,
                self.source_step_direction,
                self.target,
                self.target_response_direction,
            )
        )

    @property
    def identity_hash(self) -> str:
        return stable_hash_v1(self.identity_dict())

    def identity_dict(self) -> dict[str, Any]:
        return {
            "relation_identity": self.relation_identity,
            "source": self.source,
            "source_step_direction": self.source_step_direction,
            "target": self.target,
            "target_response_direction": self.target_response_direction,
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            **self.identity_dict(),
            "selected_delay_horizon_seconds": self.selected_delay_horizon_seconds,
            "d1_directional_record_hash": self.d1_directional_record_hash,
            "d2_confirmation_record_hash": self.d2_confirmation_record_hash,
            "d2_result_hash": self.d2_result_hash,
            "relation_family": self.relation_family,
            "identity_hash": self.identity_hash,
        }


@dataclass(frozen=True)
class ConfirmedRelationIdentityCohortV1:
    relations: tuple[ConfirmedRelationIdentityV1, ...]
    source_artifact_hash: str = D2_DIRECTIONAL_SUMMARY_HASH
    process: str = PROCESS
    relation_family: str = RELATION_FAMILY
    scientific_ranking_created: bool = False
    candidate_method_preference_used: bool = False
    private_numeric_values_included: bool = False

    def __post_init__(self) -> None:
        require_sha256(self.source_artifact_hash, "source_artifact_hash")
        if self.source_artifact_hash != D2_DIRECTIONAL_SUMMARY_HASH:
            raise TASK039E0ProtocolError("directional summary binding differs")
        if self.process != PROCESS or self.relation_family != RELATION_FAMILY:
            raise TASK039E0ProtocolError("cohort scientific identity differs")
        if len(self.relations) != EXPECTED_RELATIONS:
            raise TASK039E0ProtocolError("confirmed relation count must be 42")
        identities = tuple(item.relation_identity for item in self.relations)
        if len(set(identities)) != EXPECTED_RELATIONS:
            raise TASK039E0ProtocolError("directional identities must be unique")
        pairs = {(item.source, item.target) for item in self.relations}
        if len(pairs) != EXPECTED_PAIRS:
            raise TASK039E0ProtocolError("confirmed pair context must be 23")
        for name in (
            "scientific_ranking_created",
            "candidate_method_preference_used",
            "private_numeric_values_included",
        ):
            _require_false(getattr(self, name), name)

    @property
    def identity_list_hash(self) -> str:
        return stable_hash_v1(
            {
                "relation_identities": [item.identity_dict() for item in self.relations]
            }
        )

    def _content_dict(self) -> dict[str, Any]:
        return {
            "schema_version": V6_FOUNDATION_SCHEMA_VERSION,
            "artifact_type": "confirmed_relation_identity_cohort_v1",
            "task_id": TASK_ID,
            "status": "frozen_task039e0_confirmed_relation_identity_cohort",
            "process": self.process,
            "relation_family": self.relation_family,
            "source_artifact_hash": self.source_artifact_hash,
            "confirmed_directional_relation_count": len(self.relations),
            "confirmed_pair_context_count": len(
                {(item.source, item.target) for item in self.relations}
            ),
            "relations": [item.to_dict() for item in self.relations],
            "identity_list_hash": self.identity_list_hash,
            "serialization_order_is_scientific_rank": False,
            "scientific_ranking_created": self.scientific_ranking_created,
            "candidate_method_preference_used": self.candidate_method_preference_used,
            "private_numeric_values_included": self.private_numeric_values_included,
        }

    @property
    def artifact_hash(self) -> str:
        return stable_hash_v1(self._content_dict())

    def to_dict(self) -> dict[str, Any]:
        return _with_hash(self._content_dict())


@dataclass(frozen=True)
class FairGenerationBudgetPolicyV2:
    relation_count: int = EXPECTED_RELATIONS
    t0_calls_per_relation: int = 0
    t1_calls_per_relation: int = 1
    t1b_calls_per_relation: int = 3
    t2_maximum_calls_per_relation: int = 3
    t2_retrieve_maximum_per_relation: int = 1
    relation_identities_visible_at_budget_freeze: bool = True
    confirmed_relation_count_known_at_budget_freeze: bool = True
    calibrated_private_numeric_values_visible_at_budget_freeze: bool = False
    construction_evidence_bundles_materialized_at_budget_freeze: bool = False
    rule_proposals_visible_at_budget_freeze: bool = False
    validity_outcomes_visible_at_budget_freeze: bool = False
    utility_outcomes_visible_at_budget_freeze: bool = False
    budget_selected_from_relation_specific_difficulty: bool = False
    budget_rationale: str = "bounded_agent_depth_and_cost_precommit"
    result_dependent_extra_calls: bool = False
    scientific_generation_retries: str = "none"
    transport_retry_allowed_reasons: tuple[str, ...] = (
        "connection_failure",
        "provider_5xx",
        "timeout_before_model_response",
        "preregistered_non_scientific_transport_failure",
    )
    response_failures_consume_scientific_call: tuple[str, ...] = (
        "malformed_response",
        "invalid_response",
        "low_quality_response",
        "verifier_rejected_response",
    )

    def __post_init__(self) -> None:
        if self.relation_count != EXPECTED_RELATIONS:
            raise TASK039E0ProtocolError("budget relation count must be 42")
        if (self.t0_calls_per_relation, self.t1_calls_per_relation) != (0, 1):
            raise TASK039E0ProtocolError("T0/T1 budgets must be 0/1")
        if (self.t1b_calls_per_relation, self.t2_maximum_calls_per_relation) != (3, 3):
            raise TASK039E0ProtocolError("T1-B/T2 budgets must be exactly 3/3")
        if self.t2_retrieve_maximum_per_relation != 1:
            raise TASK039E0ProtocolError("T2 retrieval maximum must be one")
        for name in (
            "relation_identities_visible_at_budget_freeze",
            "confirmed_relation_count_known_at_budget_freeze",
        ):
            _require_true(getattr(self, name), name)
        for name in (
            "calibrated_private_numeric_values_visible_at_budget_freeze",
            "construction_evidence_bundles_materialized_at_budget_freeze",
            "rule_proposals_visible_at_budget_freeze",
            "validity_outcomes_visible_at_budget_freeze",
            "utility_outcomes_visible_at_budget_freeze",
            "budget_selected_from_relation_specific_difficulty",
            "result_dependent_extra_calls",
        ):
            _require_false(getattr(self, name), name)
        if self.budget_rationale != "bounded_agent_depth_and_cost_precommit":
            raise TASK039E0ProtocolError("budget rationale differs")
        if self.scientific_generation_retries != "none":
            raise TASK039E0ProtocolError("scientific retries are prohibited")
        if len(set(self.transport_retry_allowed_reasons)) != 4:
            raise TASK039E0ProtocolError("transport retry reasons differ")
        if len(set(self.response_failures_consume_scientific_call)) != 4:
            raise TASK039E0ProtocolError("scientific-call accounting differs")

    def _content_dict(self) -> dict[str, Any]:
        return {
            "schema_version": V6_FOUNDATION_SCHEMA_VERSION,
            "artifact_type": "fair_generation_budget_policy_v2",
            "policy_id": "task039e0_fair_generation_budget_v2",
            "timing_disclosure_classification": "methodological_timing_disclosure",
            "historical_v1_preserved": True,
            "relation_count": self.relation_count,
            "relation_identities_visible_at_budget_freeze": self.relation_identities_visible_at_budget_freeze,
            "confirmed_relation_count_known_at_budget_freeze": self.confirmed_relation_count_known_at_budget_freeze,
            "calibrated_private_numeric_values_visible_at_budget_freeze": self.calibrated_private_numeric_values_visible_at_budget_freeze,
            "construction_evidence_bundles_materialized_at_budget_freeze": self.construction_evidence_bundles_materialized_at_budget_freeze,
            "rule_proposals_visible_at_budget_freeze": self.rule_proposals_visible_at_budget_freeze,
            "validity_outcomes_visible_at_budget_freeze": self.validity_outcomes_visible_at_budget_freeze,
            "utility_outcomes_visible_at_budget_freeze": self.utility_outcomes_visible_at_budget_freeze,
            "budget_selected_from_relation_specific_difficulty": self.budget_selected_from_relation_specific_difficulty,
            "budget_rationale": self.budget_rationale,
            "t0_calls_per_relation": self.t0_calls_per_relation,
            "t1_calls_per_relation": self.t1_calls_per_relation,
            "t1b_calls_per_relation": self.t1b_calls_per_relation,
            "t2_maximum_calls_per_relation": self.t2_maximum_calls_per_relation,
            "t1b_fixed_total_calls": self.relation_count * self.t1b_calls_per_relation,
            "t2_maximum_total_calls": self.relation_count * self.t2_maximum_calls_per_relation,
            "t2_may_terminate_early": True,
            "t2_retrieve_maximum_per_relation": self.t2_retrieve_maximum_per_relation,
            "result_dependent_extra_calls": self.result_dependent_extra_calls,
            "scientific_generation_retries": self.scientific_generation_retries,
            "transport_retry_allowed_reasons": list(self.transport_retry_allowed_reasons),
            "response_failures_consume_scientific_call": list(self.response_failures_consume_scientific_call),
        }

    @property
    def artifact_hash(self) -> str:
        return stable_hash_v1(self._content_dict())

    def to_dict(self) -> dict[str, Any]:
        return _with_hash(self._content_dict())


@dataclass(frozen=True)
class T1BSelectionPolicyV1:
    budget_policy_hash: str

    def __post_init__(self) -> None:
        require_sha256(self.budget_policy_hash, "budget_policy_hash")

    def select(self, admissible_by_call: Sequence[bool]) -> int | None:
        if len(admissible_by_call) != 3 or any(type(item) is not bool for item in admissible_by_call):
            raise TASK039E0ProtocolError("T1-B requires exactly three outcomes")
        for index, admissible in enumerate(admissible_by_call, start=1):
            if admissible:
                return index
        return None

    def _content_dict(self) -> dict[str, Any]:
        return {
            "schema_version": V6_FOUNDATION_SCHEMA_VERSION,
            "artifact_type": "t1b_selection_policy_v1",
            "policy_id": "task039e0_t1b_selection_v1",
            "budget_policy_hash": self.budget_policy_hash,
            "generation_calls_required": 3,
            "calls_are_independent": True,
            "same_initial_evidence_view": True,
            "same_prompt_template": True,
            "same_model_config": True,
            "prior_proposal_visible": False,
            "verifier_feedback_visible": False,
            "cross_call_memory": False,
            "all_calls_run_even_after_admissible": True,
            "selection_rule": "lowest_admissible_call_index",
            "none_admissible_outcome": "no_rule",
            "utility_based_selection": False,
        }

    @property
    def artifact_hash(self) -> str:
        return stable_hash_v1(self._content_dict())

    def to_dict(self) -> dict[str, Any]:
        return _with_hash(self._content_dict())


REPAIRABLE_REVISE_CODES = frozenset(
    {
        ValidityIssueCodeV1.MALFORMED_DSL.value,
        ValidityIssueCodeV1.SERIALIZATION_HASH_MISMATCH.value,
        ValidityIssueCodeV1.CONSTRUCTION_PROVENANCE_INVALID.value,
    }
)
REPAIRABLE_RETRIEVE_CODES = frozenset(
    {
        ValidityIssueCodeV1.NUMERIC_EVIDENCE_BUNDLE_INVALID.value,
        ValidityIssueCodeV1.NUMERIC_REFERENCE_MISMATCH.value,
    }
)


def validity_issue_action_map_v1() -> dict[str, dict[str, str]]:
    result: dict[str, dict[str, str]] = {}
    for code in ValidityIssueCodeV1:
        if code.value in REPAIRABLE_REVISE_CODES:
            result[code.value] = {"repairability": "repairable", "t2_action_class": "revise"}
        elif code.value in REPAIRABLE_RETRIEVE_CODES:
            result[code.value] = {"repairability": "repairable", "t2_action_class": "retrieve"}
        else:
            result[code.value] = {"repairability": "non_repairable", "t2_action_class": "no_rule"}
    return result


@dataclass(frozen=True)
class TASK039E0ValidityPolicyV2:
    budget_policy_hash: str
    prep_verifier_source_hash: str
    verifier_version: str = "task039e0_validity_v2"

    def __post_init__(self) -> None:
        require_sha256(self.budget_policy_hash, "budget_policy_hash")
        require_sha256(self.prep_verifier_source_hash, "prep_verifier_source_hash")
        if self.verifier_version != "task039e0_validity_v2":
            raise TASK039E0ProtocolError("validity verifier version differs")

    def _content_dict(self) -> dict[str, Any]:
        issue_map = validity_issue_action_map_v1()
        return {
            "schema_version": V6_FOUNDATION_SCHEMA_VERSION,
            "artifact_type": "task039e0_validity_policy_v2",
            "verifier_version": self.verifier_version,
            "budget_policy_version": "fair_generation_budget_policy_v2",
            "budget_policy_hash": self.budget_policy_hash,
            "prep_verifier_preserved": True,
            "prep_verifier_source_hash": self.prep_verifier_source_hash,
            "project_owned_deterministic_code": True,
            "label_free": True,
            "utility_free": True,
            "llm_chain_of_thought_used": False,
            "allowed_statuses": ["admissible", "rejected"],
            "checks": [
                "schema_dsl_validity", "relation_binding", "source_target_identity",
                "source_target_direction", "selected_horizon", "numeric_reference_binding",
                "numeric_origin", "arbitrary_literal_rejection", "unsupported_variables",
                "runtime_logic_family", "prohibited_data_references", "proposal_hash",
                "construction_provenance", "budget_provenance", "premature_authority",
            ],
            "issue_action_map": issue_map,
            "issue_code_count": len(issue_map),
            "canonical_rule_materialized": False,
            "validity_auto_grants_runtime": False,
        }

    @property
    def artifact_hash(self) -> str:
        return stable_hash_v1(self._content_dict())

    def to_dict(self) -> dict[str, Any]:
        return _with_hash(self._content_dict())


@dataclass(frozen=True)
class T2DeterministicControllerPolicyV1:
    budget_policy_hash: str
    validity_policy_hash: str

    def __post_init__(self) -> None:
        require_sha256(self.budget_policy_hash, "budget_policy_hash")
        require_sha256(self.validity_policy_hash, "validity_policy_hash")

    def next_action(
        self,
        *,
        validity_status: str,
        issue_codes: Sequence[str],
        calls_consumed: int,
        retrieval_used: bool,
        retrievable_slice_exists: bool,
    ) -> str:
        if validity_status == "admissible":
            return "accept"
        if validity_status != "rejected" or not issue_codes:
            raise TASK039E0ProtocolError("controller requires bounded validity output")
        if calls_consumed >= 3:
            return "no_rule"
        mapping = validity_issue_action_map_v1()
        try:
            actions = {mapping[code]["t2_action_class"] for code in issue_codes}
        except KeyError as exc:
            raise TASK039E0ProtocolError("unknown validity issue code") from exc
        if "no_rule" in actions:
            return "no_rule"
        if (
            actions == {"retrieve"}
            and not retrieval_used
            and retrievable_slice_exists
        ):
            return "retrieve"
        return "revise"

    def _content_dict(self) -> dict[str, Any]:
        return {
            "schema_version": V6_FOUNDATION_SCHEMA_VERSION,
            "artifact_type": "t2_deterministic_controller_policy_v1",
            "policy_id": "task039e0_t2_controller_v1",
            "budget_policy_hash": self.budget_policy_hash,
            "validity_policy_hash": self.validity_policy_hash,
            "controller_is_project_owned_deterministic_code": True,
            "llm_controls_orchestration": False,
            "allowed_generated_followup_actions": ["revise", "retrieve", "no_rule"],
            "admissible_action": "accept",
            "non_repairable_action": "no_rule",
            "repairable_reference_action": "retrieve",
            "other_repairable_action": "revise",
            "maximum_generation_calls": 3,
            "maximum_retrieval_actions": 1,
            "retrieval_invokes_llm": False,
            "retrieval_allowed_slices": [
                "approved_numeric_provenance_slice",
                "confirmed_relation_binding_slice",
                "approved_semantic_process_metadata_slice",
                "preregistered_window_constant_slice",
            ],
            "retrieval_prohibited_sources": [
                "raw_hai", "labels", "attacks", "test", "train4", "br2_outcomes", "utility_outcomes",
            ],
            "followup_input_fields": [
                "original_frozen_construction_input", "bounded_verifier_issue_codes",
                "affected_field_identifiers", "approved_retrieved_evidence",
                "previous_proposal_hash",
            ],
            "chain_of_thought_feedback_prohibited": True,
            "result_dependent_budget_extension": False,
            "budget_exhaustion_outcome": "no_rule",
        }

    @property
    def artifact_hash(self) -> str:
        return stable_hash_v1(self._content_dict())

    def to_dict(self) -> dict[str, Any]:
        return _with_hash(self._content_dict())


@dataclass(frozen=True)
class ConstructionEvidenceMaterializationPolicyV1:
    cohort_hash: str
    identity_list_hash: str

    def __post_init__(self) -> None:
        require_sha256(self.cohort_hash, "cohort_hash")
        require_sha256(self.identity_list_hash, "identity_list_hash")

    def _content_dict(self) -> dict[str, Any]:
        return {
            "schema_version": V6_FOUNDATION_SCHEMA_VERSION,
            "artifact_type": "construction_evidence_materialization_policy_v1",
            "policy_id": "task039e1_evidence_materialization_v1",
            "cohort_hash": self.cohort_hash,
            "identity_list_hash": self.identity_list_hash,
            "expected_record_count": EXPECTED_RELATIONS,
            "expected_relation_binding_count": EXPECTED_RELATIONS,
            "numeric_roles": [
                "source_step_threshold", "source_stability_tolerance", "target_noise_scale",
                "selected_delay_horizon", "source_pre_window", "source_post_window",
                "minimum_source_stability_fraction", "source_refractory",
                "cross_source_isolation_radius", "target_baseline_window", "target_response_window",
            ],
            "private_view": "PrivateConstructionEvidenceV1",
            "public_view": "PublicConstructionEvidenceManifestV1",
            "private_view_may_contain_approved_derived_numeric_values": True,
            "public_view_contains_private_numeric_values": False,
            "d1_source_ledger_hash": D1_SOURCE_LEDGER_HASH,
            "d1_target_ledger_hash": D1_TARGET_LEDGER_HASH,
            "d1_directional_ledger_hash": D1_DIRECTIONAL_LEDGER_HASH,
            "d2_private_ledger_hash": D2_PRIVATE_LEDGER_HASH,
            "fit_evidence_binding_required": True,
            "confirmation_evidence_binding_required": True,
            "raw_hai_allowed": False,
            "llm_required_to_invent_numeric_values": False,
            "all_main_arms_share_same_logical_evidence": True,
            "e1_result_requires_independent_audit_before_generation": True,
        }

    @property
    def artifact_hash(self) -> str:
        return stable_hash_v1(self._content_dict())

    def to_dict(self) -> dict[str, Any]:
        return _with_hash(self._content_dict())


@dataclass(frozen=True)
class LLMDirectNumberEvaluationPolicyV1:
    budget_policy_hash: str

    def __post_init__(self) -> None:
        require_sha256(self.budget_policy_hash, "budget_policy_hash")

    @staticmethod
    def normalized_absolute_error(proposed: float, approved: float) -> float:
        if not all(isinstance(value, (int, float)) and not isinstance(value, bool) for value in (proposed, approved)):
            raise TASK039E0ProtocolError("direct-number comparison requires numeric values")
        result = abs(float(proposed) - float(approved)) / max(abs(float(approved)), 1e-12)
        if result == float("inf") or result != result:
            raise TASK039E0ProtocolError("direct-number error must be finite")
        return result

    def _content_dict(self) -> dict[str, Any]:
        return {
            "schema_version": V6_FOUNDATION_SCHEMA_VERSION,
            "artifact_type": "llm_direct_number_evaluation_policy_v1",
            "policy_id": "task039e0_t1_direct_number_v1",
            "arm": "T1-DIRECT-NUMBER",
            "designated_comparator": "T1",
            "generation_calls_per_relation": 1,
            "budget_policy_hash": self.budget_policy_hash,
            "same_relation_identity": True,
            "same_semantic_context": True,
            "same_model_execution_policy": True,
            "same_prompt_family_structure": True,
            "calibrated_numeric_values_given_as_answer": False,
            "numeric_origin": "llm_direct_number_ablation",
            "normalized_absolute_error_formula": "abs(proposed-approved)/max(abs(approved),1e-12)",
            "reported_rates": ["nonfinite_proposal_rate", "missing_number_rate", "sign_domain_violation_rate"],
            "isolated_from_main_arms": True,
            "may_replace_main_method": False,
            "validity_authority_granted": False,
            "runtime_authority_granted": False,
            "label_input_used": False,
        }

    @property
    def artifact_hash(self) -> str:
        return stable_hash_v1(self._content_dict())

    def to_dict(self) -> dict[str, Any]:
        return _with_hash(self._content_dict())


@dataclass(frozen=True)
class ConstructionMetricPolicyV1:
    def _content_dict(self) -> dict[str, Any]:
        return {
            "schema_version": V6_FOUNDATION_SCHEMA_VERSION,
            "artifact_type": "construction_metric_policy_v1",
            "policy_id": "task039e0_construction_metrics_v1",
            "eligible_relation_count": EXPECTED_RELATIONS,
            "main_arms": ["T0", "T1", "T1-B", "T2"],
            "common_metrics": [
                "accepted_proposal_count", "accepted_proposal_rate", "no_rule_count", "no_rule_rate",
                "verifier_rejected_proposal_count", "first_call_admissible_rate", "eventual_admissible_rate",
                "generation_calls_consumed", "verifier_invocations", "retrieval_count", "revise_count",
                "budget_exhaustion_count",
            ],
            "t1b_metrics": ["any_admissible_among_3_rate", "selected_call_index_distribution"],
            "t2_metrics": [
                "feedback_recovery_count", "feedback_recovery_rate", "accepted_after_revise",
                "accepted_after_retrieve", "no_rule_due_non_repairable_issue",
                "no_rule_due_budget_exhaustion",
            ],
            "separate_outcome_counters": [
                "accepted_proposal", "no_rule", "verifier_rejection", "budget_exhaustion",
            ],
            "no_rule_is_transport_failure": False,
            "no_rule_is_runtime_abstention": False,
            "utility_metrics_used": False,
            "anomaly_labels_used": False,
            "winner_selected_in_e0": False,
        }

    @property
    def artifact_hash(self) -> str:
        return stable_hash_v1(self._content_dict())

    def to_dict(self) -> dict[str, Any]:
        return _with_hash(self._content_dict())


@dataclass(frozen=True)
class TASK039E1AuthorizationV1:
    protocol_bundle_hash: str
    cohort_hash: str
    identity_list_hash: str
    materialization_policy_hash: str

    def __post_init__(self) -> None:
        for name in (
            "protocol_bundle_hash", "cohort_hash", "identity_list_hash", "materialization_policy_hash"
        ):
            require_sha256(getattr(self, name), name)

    def _content_dict(self) -> dict[str, Any]:
        return {
            "schema_version": V6_FOUNDATION_SCHEMA_VERSION,
            "artifact_type": "task039e1_authorization_v1",
            "task_id": "TASK-039E1",
            "task_name": "Confirmed Relation Construction-Evidence Materialization",
            "status": "authorized_task039e1_evidence_materialization_only",
            "protocol_bundle_hash": self.protocol_bundle_hash,
            "cohort_hash": self.cohort_hash,
            "identity_list_hash": self.identity_list_hash,
            "materialization_policy_hash": self.materialization_policy_hash,
            "confirmed_relation_count": EXPECTED_RELATIONS,
            "d1_source_private_ledger_read_authorized": True,
            "d1_target_private_ledger_read_authorized": True,
            "d1_directional_private_ledger_read_authorized": True,
            "d2_private_confirmation_ledger_read_authorized": True,
            "public_hash_provenance_manifest_authorized": True,
            "hai_access_authorized": False,
            "train1_train2_train3_reread_authorized": False,
            "train4_authorized": False,
            "test_labels_attacks_authorized": False,
            "llm_calls_authorized": False,
            "t0_generation_authorized": False,
            "t1_t1b_t2_generation_authorized": False,
            "direct_number_ablation_execution_authorized": False,
            "rule_v2_materialization_authorized": False,
            "agent_execution_authorized": False,
            "detector_runtime_authorized": False,
        }

    @property
    def artifact_hash(self) -> str:
        return stable_hash_v1(self._content_dict())

    def to_dict(self) -> dict[str, Any]:
        return _with_hash(self._content_dict())


@dataclass(frozen=True)
class TASK039E0ProtocolBundleV1:
    cohort_hash: str
    identity_list_hash: str
    budget_policy_hash: str
    t1b_selection_policy_hash: str
    controller_policy_hash: str
    validity_policy_hash: str
    materialization_policy_hash: str
    direct_number_policy_hash: str
    metric_policy_hash: str
    prep_commit: str = "239c6bf8cd52566f201e29cec50569a06b6fc74e"
    prep_status: str = "passed_task039e0_rule_construction_protocol_preparation"

    def __post_init__(self) -> None:
        for name in (
            "cohort_hash", "identity_list_hash", "budget_policy_hash", "t1b_selection_policy_hash",
            "controller_policy_hash", "validity_policy_hash", "materialization_policy_hash",
            "direct_number_policy_hash", "metric_policy_hash",
        ):
            require_sha256(getattr(self, name), name)
        if self.prep_commit != "239c6bf8cd52566f201e29cec50569a06b6fc74e":
            raise TASK039E0ProtocolError("PREP commit differs")

    def _content_dict(self) -> dict[str, Any]:
        return {
            "schema_version": V6_FOUNDATION_SCHEMA_VERSION,
            "artifact_type": "task039e0_protocol_bundle_v1",
            "task_id": TASK_ID,
            "status": STATUS,
            "process": PROCESS,
            "relation_family": RELATION_FAMILY,
            "e0_authorization_hash": E0_AUTHORIZATION_HASH,
            "d2_result_hash": D2_RESULT_HASH,
            "d2_directional_summary_hash": D2_DIRECTIONAL_SUMMARY_HASH,
            "d2_pair_summary_hash": D2_PAIR_SUMMARY_HASH,
            "prep_commit": self.prep_commit,
            "prep_status": self.prep_status,
            "prep_v1_timing_claim_preserved_as_history": True,
            "cohort_hash": self.cohort_hash,
            "identity_list_hash": self.identity_list_hash,
            "confirmed_directional_relation_count": EXPECTED_RELATIONS,
            "confirmed_pair_context_count": EXPECTED_PAIRS,
            "budget_policy_hash": self.budget_policy_hash,
            "t1b_selection_policy_hash": self.t1b_selection_policy_hash,
            "controller_policy_hash": self.controller_policy_hash,
            "validity_policy_hash": self.validity_policy_hash,
            "materialization_policy_hash": self.materialization_policy_hash,
            "direct_number_policy_hash": self.direct_number_policy_hash,
            "construction_metric_policy_hash": self.metric_policy_hash,
            "proposal_dsl_family": "canonical_delayed_response_rule_v1_candidate",
            "runtime_logic_family": "missing_expected_delayed_response",
            "main_numeric_origin": "deterministic_calibrated_evidence",
            "main_arms": ["T0", "T1", "T1-B", "T2"],
            "arm_protocols": {
                "T0": {
                    "mode": "deterministic_template",
                    "generation_calls": 0,
                    "proposal_count": 1,
                    "llm_used": False,
                    "search_used": False,
                    "fallback_used": False,
                    "rejection_outcome": "record_rejection",
                },
                "T1": {
                    "mode": "one_shot_constrained_llm",
                    "generation_calls": 1,
                    "verifier_feedback_to_model": False,
                    "admissible_outcome": "accepted_proposal",
                    "rejected_outcome": "no_rule",
                    "second_call_allowed": False,
                },
                "T1-B": {
                    "mode": "independent_feedback_free_repeated_generation",
                    "generation_calls": 3,
                    "all_calls_required": True,
                    "previous_proposal_visible": False,
                    "verifier_feedback_to_model": False,
                    "selection": "lowest_admissible_call_index",
                    "none_admissible_outcome": "no_rule",
                },
                "T2": {
                    "mode": "bounded_verifier_feedback_construction",
                    "maximum_generation_calls": 3,
                    "maximum_followup_generations": 2,
                    "maximum_retrieval_actions": 1,
                    "controller": "project_owned_deterministic_code",
                    "allowed_actions": ["revise", "retrieve", "no_rule"],
                    "early_stop_after_accept_or_no_rule": True,
                    "result_dependent_extension": False,
                },
            },
            "no_rule_semantics": {
                "valid_construction_outcome": True,
                "transport_failure": False,
                "runtime_abstention": False,
                "invalid_system_state": False,
                "forced_rule_required": False,
                "separate_counters": [
                    "accepted_proposal", "no_rule", "verifier_rejection", "budget_exhaustion",
                ],
            },
            "fair_input_policy": {
                "t1_and_each_t1b_call_same_initial_view": True,
                "t2_call1_same_initial_view": True,
                "later_t2_feedback_is_treatment_difference": True,
                "t1b_cross_call_memory": False,
            },
            "future_model_execution_freeze": {
                "required_before_any_real_llm_call": True,
                "selection_may_use_future_proposal_quality": False,
                "required_fields": [
                    "provider_identifier", "exact_model_identifier_version",
                    "prompt_template_version_hash", "decoding_parameters",
                    "structured_output_mode", "seed_policy", "call_ordering",
                    "transport_retry_policy",
                ],
                "same_model_config_arms": ["T1", "T1-B", "T2", "T1-DIRECT-NUMBER"],
            },
            "future_call_receipt_policy": {
                "required_fields": [
                    "construction_arm", "relation_binding", "provider", "model",
                    "prompt_template", "decoding_settings", "call_number", "seed",
                    "evidence_bundle_hash", "verifier_feedback_hash",
                    "retrieved_evidence_hash", "proposal_hash", "validity_result_hash",
                    "accepted_no_rule_state", "calls_consumed", "transport_retries",
                ],
                "chain_of_thought_stored": False,
                "raw_hai_stored": False,
                "unrestricted_hidden_prompt_state_stored": False,
            },
            "relation_inclusion_policy": {
                "all_42_confirmed_directional_relations_eligible": True,
                "candidate_origin_filtering": False,
                "difficulty_filtering": False,
                "origin_provenance_descriptive_only": True,
            },
            "real_d2_result_consumed": True,
            "d1_d2_private_ledgers_accessed": False,
            "hai_accessed": False,
            "llm_called": False,
            "t0_generated": False,
            "t1_t1b_t2_generated": False,
            "rule_v2_created": False,
            "runtime_authority_granted": False,
            "utility_evaluation_executed": False,
        }

    @property
    def artifact_hash(self) -> str:
        return stable_hash_v1(self._content_dict())

    def to_dict(self) -> dict[str, Any]:
        return _with_hash(self._content_dict())


def load_confirmed_relation_cohort_v1(document: Mapping[str, Any]) -> ConfirmedRelationIdentityCohortV1:
    if document.get("artifact_hash") != D2_DIRECTIONAL_SUMMARY_HASH:
        raise TASK039E0ProtocolError("audited D2 directional summary hash differs")
    relations_raw = document.get("relations")
    if not isinstance(relations_raw, list):
        raise TASK039E0ProtocolError("D2 directional relations are missing")
    confirmed: list[ConfirmedRelationIdentityV1] = []
    for item in relations_raw:
        if not isinstance(item, Mapping):
            raise TASK039E0ProtocolError("D2 directional relation is malformed")
        if item.get("confirmation_status") != "calibration_confirmed":
            continue
        confirmed.append(
            ConfirmedRelationIdentityV1(
                source=str(item["source"]),
                source_step_direction=str(item["source_step_direction"]),
                target=str(item["target"]),
                target_response_direction=str(item["target_response_direction"]),
                selected_delay_horizon_seconds=int(item["selected_horizon_seconds"]),
                d1_directional_record_hash=str(item["d1_directional_record_hash"]),
                d2_confirmation_record_hash=str(item["private_confirmation_record_hash"]),
            )
        )
    return ConfirmedRelationIdentityCohortV1(tuple(confirmed))


def source_blob_sha256_v1(repository_root: Path, relative: str) -> str:
    path = repository_root / relative
    if not path.is_file():
        raise TASK039E0ProtocolError(f"required source is missing: {relative}")
    return sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def schema_for_example_v1(example: Mapping[str, Any]) -> dict[str, Any]:
    def infer(value: Any, field: str = "") -> dict[str, Any]:
        if value is None:
            return {"type": "null"}
        if type(value) is bool:
            return {"type": "boolean"}
        if type(value) is int:
            return {"type": "integer"}
        if type(value) is float:
            return {"type": "number"}
        if isinstance(value, str):
            result: dict[str, Any] = {"type": "string"}
            if field.endswith("hash") or field.endswith("_hash"):
                result["pattern"] = "^[a-f0-9]{64}$"
            if field == "artifact_type" or field == "schema_version":
                result["const"] = value
            return result
        if isinstance(value, list):
            return {"type": "array", "items": infer(value[0]) if value else {}}
        if isinstance(value, Mapping):
            return {
                "type": "object",
                "additionalProperties": False,
                "required": list(value),
                "properties": {key: infer(item, key) for key, item in value.items()},
            }
        raise TASK039E0ProtocolError("unsupported schema example")

    schema = infer(example)
    schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    schema["$id"] = (
        "https://paperworks.local/schemas/v6/"
        + str(example["artifact_type"])
        + "_schema.json"
    )
    schema["title"] = str(example["artifact_type"])
    return schema


def canonical_bytes_v1(document: Mapping[str, Any]) -> bytes:
    return (canonical_json_v1(document) + "\n").encode("utf-8")


__all__ = [
    "ConstructionEvidenceMaterializationPolicyV1",
    "ConstructionMetricPolicyV1",
    "ConfirmedRelationIdentityCohortV1",
    "ConfirmedRelationIdentityV1",
    "FairGenerationBudgetPolicyV2",
    "LLMDirectNumberEvaluationPolicyV1",
    "T1BSelectionPolicyV1",
    "T2DeterministicControllerPolicyV1",
    "TASK039E0ProtocolBundleV1",
    "TASK039E0ProtocolError",
    "TASK039E0ValidityPolicyV2",
    "TASK039E1AuthorizationV1",
    "canonical_bytes_v1",
    "load_confirmed_relation_cohort_v1",
    "schema_for_example_v1",
    "source_blob_sha256_v1",
    "validity_issue_action_map_v1",
    "verify_self_hash_v1",
]
