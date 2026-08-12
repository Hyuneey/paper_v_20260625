"""Deterministic mock construction orchestration for TASK-039E3-PREP."""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Callable, Mapping, Sequence

from paperworks.v6.common import (
    V6_FOUNDATION_SCHEMA_VERSION,
    freeze_json,
    stable_hash_v1,
    thaw_json,
)
from paperworks.v6.outcomes_v1 import ConstructionArmV1
from paperworks.v6.task039e0_rule_construction_prep_v1 import (
    FROZEN_ARM_PROTOCOLS,
    MAIN_NUMERIC_ORIGIN,
    PROPOSAL_ARTIFACT_TYPE,
    ProposalConstructionProvenanceV1,
    canonical_proposal_hash_v1,
)
from paperworks.v6.task039e0_rule_construction_protocol_v1 import (
    FairGenerationBudgetPolicyV2,
    LLMDirectNumberEvaluationPolicyV1,
    T1BSelectionPolicyV1,
    T2DeterministicControllerPolicyV1,
)
from paperworks.v6.task039e0_validity_v2 import (
    PreparedValidityResultV2,
    verify_prepared_rule_proposal_v2,
)
from paperworks.v6.task039e2_execution_configuration_v1 import (
    CALIBRATED_NUMERIC_ROLES,
    EXACT_MODEL,
    PROVIDER,
    WINDOW_NUMERIC_ROLES,
    ProviderProposalCoreV1,
    RuleProposalEnvelopeV1,
    TASK039E2ConfigurationError,
    generate_synthetic_t0_core_v1,
    validate_retrieval_request_v1,
)
from paperworks.v6.task039e3_execution_prep_v1 import (
    E0_BUDGET_POLICY_HASH,
    E0_CONTROLLER_POLICY_HASH,
    E0_VALIDITY_POLICY_HASH,
    EXECUTION_SCHEDULE_HASH,
    INDIVIDUAL_PROPOSALS_PUBLIC,
    PROVIDER_MODEL_RECEIPT_HASH,
    ConstructionEvidenceContextV1,
    ConstructionInputViewV1,
    FrozenProviderRequestV1,
    MockProviderTransportV1,
    ProviderCallLedgerV1,
    ProviderCallSlotV1,
    TASK039E3PreparationError,
    build_direct_number_request_v1,
    build_main_request_v1,
    build_t2_followup_request_v1,
    execute_mock_provider_slot_v1,
)


MainRequestBuilderV1 = Callable[[ConstructionInputViewV1], FrozenProviderRequestV1]
T2FollowupRequestBuilderV1 = Callable[..., FrozenProviderRequestV1]


T0_TEMPLATE_HASH = "504328783b654054029ab3277360bc6efc7bbd8eef3d5f1f6cc98ea3aefb12ff"
_SYNTHETIC_FAULTS = {
    None,
    "SYNTHETIC_REPAIRABLE_REVISE",
    "SYNTHETIC_REPAIRABLE_RETRIEVE",
    "SYNTHETIC_NON_REPAIRABLE",
}


def _require_hash(value: str, field_name: str) -> None:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise TASK039E3PreparationError(f"{field_name} must be a SHA-256 hash")


def _require_nonempty_string(value: str, field_name: str) -> None:
    if not isinstance(value, str) or not value:
        raise TASK039E3PreparationError(f"{field_name} must be nonempty")


def _arm_enum(arm: str) -> ConstructionArmV1:
    try:
        return ConstructionArmV1("T1_B" if arm == "T1-B" else arm)
    except ValueError as exc:
        raise TASK039E3PreparationError("main construction arm differs") from exc


_BUDGET = FairGenerationBudgetPolicyV2()
if _BUDGET.artifact_hash != E0_BUDGET_POLICY_HASH:
    raise TASK039E3PreparationError("frozen E0 budget policy hash differs")
_CONTROLLER = T2DeterministicControllerPolicyV1(
    budget_policy_hash=E0_BUDGET_POLICY_HASH,
    validity_policy_hash=E0_VALIDITY_POLICY_HASH,
)
if _CONTROLLER.artifact_hash != E0_CONTROLLER_POLICY_HASH:
    raise TASK039E3PreparationError("frozen E0 controller policy hash differs")
_T1B_SELECTION = T1BSelectionPolicyV1(E0_BUDGET_POLICY_HASH)
_DIRECT_NUMBER_POLICY = LLMDirectNumberEvaluationPolicyV1(E0_BUDGET_POLICY_HASH)


def _provenance(
    *, evidence: ConstructionEvidenceContextV1, arm: str, prompt_version: str
) -> ProposalConstructionProvenanceV1:
    arm_enum = _arm_enum(arm)
    arm_protocol = next(
        protocol for protocol in FROZEN_ARM_PROTOCOLS if protocol.arm is arm_enum
    )
    return ProposalConstructionProvenanceV1(
        construction_arm=arm_enum,
        arm_protocol_hash=arm_protocol.protocol_hash,
        budget_policy_hash=E0_BUDGET_POLICY_HASH,
        evidence_bundle_hash=evidence.numeric_evidence.artifact_hash,
        prompt_template_version=prompt_version,
        execution_state="synthetic_preparation",
        future_call_record_refs=(),
        model_identifier="not_applicable" if arm == "T0" else EXACT_MODEL,
        provider_identifier="not_applicable" if arm == "T0" else PROVIDER,
    )


def _envelope_to_dict(envelope: RuleProposalEnvelopeV1) -> dict[str, Any]:
    return {
        "proposal_core": envelope.proposal_core.to_dict(),
        "construction_arm": envelope.construction_arm,
        "local_call_number": envelope.local_call_number,
        "budget_policy_hash": envelope.budget_policy_hash,
        "evidence_hash": envelope.evidence_hash,
        "prompt_hash": envelope.prompt_hash,
        "provider_model_receipt_hash": envelope.provider_model_receipt_hash,
        "execution_schedule_hash": envelope.execution_schedule_hash,
    }


def _project_proposal_document(
    *,
    core: ProviderProposalCoreV1,
    evidence: ConstructionEvidenceContextV1,
    provenance: ProposalConstructionProvenanceV1,
) -> dict[str, Any]:
    document: dict[str, Any] = {
        "schema_version": V6_FOUNDATION_SCHEMA_VERSION,
        "artifact_type": PROPOSAL_ARTIFACT_TYPE,
        "construction_arm": provenance.construction_arm.value,
        "dsl_family": core.dsl_family,
        "relation_binding_hash": evidence.relation.binding_hash,
        "relation_identity": core.relation_identity,
        "source": core.source,
        "source_step_direction": core.source_step_direction,
        "target": core.target,
        "target_response_direction": core.target_response_direction,
        "selected_delay_horizon_seconds": core.selected_delay_horizon_seconds,
        "numeric_origin": MAIN_NUMERIC_ORIGIN,
        "source_threshold_reference": core.source_threshold_reference,
        "source_stability_reference": core.source_stability_reference,
        "target_scale_reference": core.target_scale_reference,
        "fit_evidence_reference": evidence.numeric_evidence.fit_evidence_reference,
        "confirmation_evidence_reference": (
            evidence.numeric_evidence.confirmation_evidence_reference
        ),
        "preregistered_window_constant_references": [
            core.window_constant_references[role] for role in WINDOW_NUMERIC_ROLES
        ],
        "variables": list(core.variables),
        "runtime_logic": core.runtime_logic_family,
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


def _apply_synthetic_validity_fault(
    document: Mapping[str, Any], fault: str | None
) -> dict[str, Any]:
    if fault not in _SYNTHETIC_FAULTS:
        raise TASK039E3PreparationError("synthetic validity fault differs")
    result = dict(document)
    if fault == "SYNTHETIC_REPAIRABLE_REVISE":
        result["schema_version"] = "SYNTHETIC_MALFORMED_SCHEMA"
    elif fault == "SYNTHETIC_REPAIRABLE_RETRIEVE":
        result["source_threshold_reference"] = stable_hash_v1(
            {"synthetic_fault": "numeric_reference"}
        )
    elif fault == "SYNTHETIC_NON_REPAIRABLE":
        result["source"] = "SYNTHETIC_UNSUPPORTED_SOURCE"
    if fault is not None:
        result["proposal_hash"] = canonical_proposal_hash_v1(result)
    return result


@dataclass(frozen=True)
class ConstructionProposalRecordV1:
    relation_identity: str
    arm: str
    call_number: int
    proposal_envelope: RuleProposalEnvelopeV1
    project_proposal: Mapping[str, Any]
    validity_result: PreparedValidityResultV2

    def __post_init__(self) -> None:
        _require_nonempty_string(self.relation_identity, "proposal relation")
        _arm_enum(self.arm)
        if self.call_number < 0:
            raise TASK039E3PreparationError("proposal call number differs")
        proposal = freeze_json(self.project_proposal)
        object.__setattr__(self, "project_proposal", proposal)
        if proposal.get("proposal_hash") != self.validity_result.proposal_hash:
            raise TASK039E3PreparationError("proposal/validity hash differs")
        if self.validity_result.verifier_version != "task039e0_validity_v2":
            raise TASK039E3PreparationError("validity V2 binding differs")

    @property
    def proposal_hash(self) -> str:
        return str(self.project_proposal["proposal_hash"])

    @property
    def validity_hash(self) -> str:
        return self.validity_result.artifact_hash

    @property
    def record_hash(self) -> str:
        return stable_hash_v1(
            {
                "relation_identity": self.relation_identity,
                "arm": self.arm,
                "call_number": self.call_number,
                "proposal_envelope": _envelope_to_dict(self.proposal_envelope),
                "proposal_hash": self.proposal_hash,
                "validity_hash": self.validity_hash,
            }
        )


class ConstructionProposalLedgerV1:
    """Private append-only proposal and deterministic-validity custody."""

    def __init__(self) -> None:
        self._records: list[ConstructionProposalRecordV1] = []
        self._keys: set[tuple[str, str, int]] = set()

    @property
    def records(self) -> tuple[ConstructionProposalRecordV1, ...]:
        return tuple(self._records)

    @property
    def ledger_hash(self) -> str:
        return stable_hash_v1(
            {
                "artifact_type": "construction_proposal_ledger_v1",
                "record_hashes": [record.record_hash for record in self._records],
            }
        )

    def append(self, record: ConstructionProposalRecordV1) -> None:
        key = (record.relation_identity, record.arm, record.call_number)
        if key in self._keys:
            raise TASK039E3PreparationError("proposal ledger key already exists")
        self._records.append(record)
        self._keys.add(key)


def wrap_and_verify_core_v1(
    *,
    core: ProviderProposalCoreV1,
    evidence: ConstructionEvidenceContextV1,
    arm: str,
    call_number: int,
    prompt_hash: str,
    synthetic_validity_fault: str | None = None,
) -> ConstructionProposalRecordV1:
    _require_hash(prompt_hash, "prompt hash")
    _require_nonempty_string(evidence.relation.relation_identity, "relation identity")
    provenance = _provenance(
        evidence=evidence,
        arm=arm,
        prompt_version=(
            "T0_TEMPLATE_V1"
            if arm == "T0"
            else "T2_FOLLOWUP_PROMPT_V1"
            if arm == "T2" and call_number > 1
            else "MAIN_INITIAL_PROMPT_V1"
        ),
    )
    envelope = RuleProposalEnvelopeV1(
        proposal_core=core,
        construction_arm=arm,
        local_call_number=call_number,
        budget_policy_hash=E0_BUDGET_POLICY_HASH,
        evidence_hash=evidence.render_view().evidence_hash,
        prompt_hash=prompt_hash,
        provider_model_receipt_hash=(
            None if arm == "T0" else PROVIDER_MODEL_RECEIPT_HASH
        ),
        execution_schedule_hash=EXECUTION_SCHEDULE_HASH,
    )
    project_proposal = _project_proposal_document(
        core=core,
        evidence=evidence,
        provenance=provenance,
    )
    project_proposal = _apply_synthetic_validity_fault(
        project_proposal, synthetic_validity_fault
    )
    validity = verify_prepared_rule_proposal_v2(
        project_proposal,
        relation=evidence.relation,
        numeric_evidence=evidence.numeric_evidence,
        provenance=provenance,
        budget=_BUDGET,
        allowed_variables=frozenset(
            {evidence.relation.source, evidence.relation.target}
        ),
    )
    return ConstructionProposalRecordV1(
        relation_identity=evidence.relation.relation_identity,
        arm=arm,
        call_number=call_number,
        proposal_envelope=envelope,
        project_proposal=project_proposal,
        validity_result=validity,
    )


@dataclass(frozen=True)
class ConstructionOutcomeRecordV1:
    relation_identity: str
    arm: str
    outcome: str
    accepted_call_index: int | None
    generation_calls_consumed: int
    verifier_invocations: int
    verifier_rejected_proposal_count: int
    first_call_admissible: bool
    retrieval_count: int = 0
    revise_count: int = 0
    budget_exhaustion_count: int = 0
    no_rule_reason: str | None = None
    feedback_path: str | None = None

    def __post_init__(self) -> None:
        _require_nonempty_string(self.relation_identity, "outcome relation")
        _arm_enum(self.arm)
        if self.outcome not in {"accepted_proposal", "no_rule"}:
            raise TASK039E3PreparationError("construction outcome differs")
        if (self.outcome == "accepted_proposal") != (
            self.accepted_call_index is not None
        ):
            raise TASK039E3PreparationError("accepted call/outcome differs")
        for field_name in (
            "generation_calls_consumed",
            "verifier_invocations",
            "verifier_rejected_proposal_count",
            "retrieval_count",
            "revise_count",
            "budget_exhaustion_count",
        ):
            value = getattr(self, field_name)
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise TASK039E3PreparationError(f"{field_name} differs")
        if type(self.first_call_admissible) is not bool:
            raise TASK039E3PreparationError("first call flag differs")
        if self.arm == "T0" and self.generation_calls_consumed != 0:
            raise TASK039E3PreparationError("T0 provider calls must be zero")

    @property
    def artifact_hash(self) -> str:
        return stable_hash_v1(self.to_dict())

    def to_dict(self) -> dict[str, Any]:
        return {
            "relation_identity": self.relation_identity,
            "arm": self.arm,
            "outcome": self.outcome,
            "accepted_call_index": self.accepted_call_index,
            "generation_calls_consumed": self.generation_calls_consumed,
            "verifier_invocations": self.verifier_invocations,
            "verifier_rejected_proposal_count": (
                self.verifier_rejected_proposal_count
            ),
            "first_call_admissible": self.first_call_admissible,
            "retrieval_count": self.retrieval_count,
            "revise_count": self.revise_count,
            "budget_exhaustion_count": self.budget_exhaustion_count,
            "no_rule_reason": self.no_rule_reason,
            "feedback_path": self.feedback_path,
        }


class ConstructionOutcomeLedgerV1:
    """Private per-relation outcomes for the four main construction arms."""

    def __init__(self) -> None:
        self._records: list[ConstructionOutcomeRecordV1] = []
        self._keys: set[tuple[str, str]] = set()

    @property
    def records(self) -> tuple[ConstructionOutcomeRecordV1, ...]:
        return tuple(self._records)

    @property
    def ledger_hash(self) -> str:
        return stable_hash_v1(
            {
                "artifact_type": "construction_outcome_ledger_v1",
                "record_hashes": [record.artifact_hash for record in self._records],
            }
        )

    def append(self, record: ConstructionOutcomeRecordV1) -> None:
        key = (record.relation_identity, record.arm)
        if key in self._keys:
            raise TASK039E3PreparationError("outcome ledger key already exists")
        self._records.append(record)
        self._keys.add(key)

    def assert_complete_future_cohort(
        self, relation_identities: Sequence[str]
    ) -> None:
        if len(relation_identities) != 42 or len(set(relation_identities)) != 42:
            raise TASK039E3PreparationError("future outcome cohort must contain 42 relations")
        expected = {
            (relation_identity, arm)
            for relation_identity in relation_identities
            for arm in ("T0", "T1", "T1-B", "T2")
        }
        if self._keys != expected or len(self._records) != 168:
            raise TASK039E3PreparationError(
                "future outcome ledger must contain 42 by 4 records with zero skip"
            )


def _parsed_proposal_result(
    result: Any,
) -> tuple[str, ProviderProposalCoreV1 | None]:
    parsed = result.parsed_proposal
    if parsed is None:
        raise TASK039E3PreparationError("provider proposal parser result missing")
    return parsed.parse_status, parsed.proposal_core


def run_t0_v1(
    *,
    evidence: ConstructionEvidenceContextV1,
    proposal_ledger: ConstructionProposalLedgerV1,
    outcome_ledger: ConstructionOutcomeLedgerV1,
    synthetic_validity_fault: str | None = None,
) -> ConstructionOutcomeRecordV1:
    view = evidence.render_view()
    core = generate_synthetic_t0_core_v1(view.to_dict())
    proposal = wrap_and_verify_core_v1(
        core=core,
        evidence=evidence,
        arm="T0",
        call_number=0,
        prompt_hash=T0_TEMPLATE_HASH,
        synthetic_validity_fault=synthetic_validity_fault,
    )
    proposal_ledger.append(proposal)
    admissible = proposal.validity_result.status == "admissible"
    outcome = ConstructionOutcomeRecordV1(
        relation_identity=evidence.relation.relation_identity,
        arm="T0",
        outcome="accepted_proposal" if admissible else "no_rule",
        accepted_call_index=0 if admissible else None,
        generation_calls_consumed=0,
        verifier_invocations=1,
        verifier_rejected_proposal_count=0 if admissible else 1,
        first_call_admissible=admissible,
        no_rule_reason=None if admissible else "t0_verifier_rejection",
    )
    outcome_ledger.append(outcome)
    return outcome


def run_t1_v1(
    *,
    relation_schedule_index: int,
    evidence: ConstructionEvidenceContextV1,
    transport: MockProviderTransportV1,
    call_ledger: ProviderCallLedgerV1,
    proposal_ledger: ConstructionProposalLedgerV1,
    outcome_ledger: ConstructionOutcomeLedgerV1,
    synthetic_validity_fault: str | None = None,
    main_request_builder: MainRequestBuilderV1 = build_main_request_v1,
) -> ConstructionOutcomeRecordV1:
    request = main_request_builder(evidence.render_view())
    slot = ProviderCallSlotV1(
        relation_schedule_index,
        evidence.relation.binding_hash,
        "T1",
        1,
        True,
    )
    result = execute_mock_provider_slot_v1(
        slot=slot,
        request=request,
        transport=transport,
        ledger=call_ledger,
        parse_kind="proposal",
    )
    parse_status, core = _parsed_proposal_result(result)
    if core is None:
        outcome = ConstructionOutcomeRecordV1(
            relation_identity=evidence.relation.relation_identity,
            arm="T1",
            outcome="no_rule",
            accepted_call_index=None,
            generation_calls_consumed=1,
            verifier_invocations=0,
            verifier_rejected_proposal_count=0,
            first_call_admissible=False,
            no_rule_reason=f"scientific_response:{parse_status}",
        )
        outcome_ledger.append(outcome)
        return outcome
    proposal = wrap_and_verify_core_v1(
        core=core,
        evidence=evidence,
        arm="T1",
        call_number=1,
        prompt_hash=request.model_visible_content_hash,
        synthetic_validity_fault=synthetic_validity_fault,
    )
    proposal_ledger.append(proposal)
    admissible = proposal.validity_result.status == "admissible"
    outcome = ConstructionOutcomeRecordV1(
        relation_identity=evidence.relation.relation_identity,
        arm="T1",
        outcome="accepted_proposal" if admissible else "no_rule",
        accepted_call_index=1 if admissible else None,
        generation_calls_consumed=1,
        verifier_invocations=1,
        verifier_rejected_proposal_count=0 if admissible else 1,
        first_call_admissible=admissible,
        no_rule_reason=None if admissible else "verifier_rejection",
    )
    outcome_ledger.append(outcome)
    return outcome


def run_t1b_v1(
    *,
    relation_schedule_index: int,
    evidence: ConstructionEvidenceContextV1,
    transport: MockProviderTransportV1,
    call_ledger: ProviderCallLedgerV1,
    proposal_ledger: ConstructionProposalLedgerV1,
    outcome_ledger: ConstructionOutcomeLedgerV1,
    synthetic_validity_faults: Sequence[str | None] = (None, None, None),
    main_request_builder: MainRequestBuilderV1 = build_main_request_v1,
) -> ConstructionOutcomeRecordV1:
    if len(synthetic_validity_faults) != 3:
        raise TASK039E3PreparationError("T1-B requires exactly three fault slots")
    request = main_request_builder(evidence.render_view())
    admissible: list[bool] = []
    verifier_invocations = 0
    verifier_rejections = 0
    for call_number in (1, 2, 3):
        slot = ProviderCallSlotV1(
            relation_schedule_index,
            evidence.relation.binding_hash,
            "T1-B",
            call_number,
            True,
        )
        result = execute_mock_provider_slot_v1(
            slot=slot,
            request=request,
            transport=transport,
            ledger=call_ledger,
            parse_kind="proposal",
        )
        _parse_status, core = _parsed_proposal_result(result)
        if core is None:
            admissible.append(False)
            continue
        proposal = wrap_and_verify_core_v1(
            core=core,
            evidence=evidence,
            arm="T1-B",
            call_number=call_number,
            prompt_hash=request.model_visible_content_hash,
            synthetic_validity_fault=synthetic_validity_faults[call_number - 1],
        )
        proposal_ledger.append(proposal)
        verifier_invocations += 1
        is_admissible = proposal.validity_result.status == "admissible"
        admissible.append(is_admissible)
        verifier_rejections += 0 if is_admissible else 1
    if len(set(transport.request_hashes[-3:])) != 1:
        raise TASK039E3PreparationError("T1-B initial requests differ")
    selected = _T1B_SELECTION.select(tuple(admissible))
    outcome = ConstructionOutcomeRecordV1(
        relation_identity=evidence.relation.relation_identity,
        arm="T1-B",
        outcome="accepted_proposal" if selected is not None else "no_rule",
        accepted_call_index=selected,
        generation_calls_consumed=3,
        verifier_invocations=verifier_invocations,
        verifier_rejected_proposal_count=verifier_rejections,
        first_call_admissible=admissible[0],
        no_rule_reason=None if selected is not None else "none_admissible_among_3",
    )
    outcome_ledger.append(outcome)
    return outcome


def retrieve_existing_evidence_v1(
    *,
    view: ConstructionInputViewV1,
    requested_evidence_identities: Sequence[str],
    retrieval_actions_already_used: int,
) -> Mapping[str, Any]:
    try:
        selected = validate_retrieval_request_v1(
            initial_evidence_identities=view.approved_evidence_identities,
            requested_evidence_identities=requested_evidence_identities,
            retrieval_actions_already_used=retrieval_actions_already_used,
        )
    except TASK039E2ConfigurationError as exc:
        raise TASK039E3PreparationError(
            "T2 same-corpus retrieval integrity violation"
        ) from exc
    bindings = [
        item.to_dict()
        for item in view.numeric_bindings
        if item.evidence_identity in set(selected)
    ]
    return MappingProxyType(
        {
            "retrieval_semantics": "targeted_re_presentation_of_existing_evidence",
            "evidence_identities": list(selected),
            "numeric_bindings": bindings,
        }
    )


def run_t2_v1(
    *,
    relation_schedule_index: int,
    evidence: ConstructionEvidenceContextV1,
    transport: MockProviderTransportV1,
    call_ledger: ProviderCallLedgerV1,
    proposal_ledger: ConstructionProposalLedgerV1,
    outcome_ledger: ConstructionOutcomeLedgerV1,
    synthetic_validity_faults: Sequence[str | None] = (None, None, None),
    retrieval_identity: str | None = None,
    main_request_builder: MainRequestBuilderV1 = build_main_request_v1,
    t2_followup_request_builder: T2FollowupRequestBuilderV1 = (
        build_t2_followup_request_v1
    ),
) -> ConstructionOutcomeRecordV1:
    if len(synthetic_validity_faults) != 3:
        raise TASK039E3PreparationError("T2 requires three precommitted fault slots")
    view = evidence.render_view()
    request = main_request_builder(view)
    retrieval_used = False
    retrieval_count = 0
    revise_count = 0
    rejected = 0
    feedback_path: str | None = None
    for call_number in (1, 2, 3):
        slot = ProviderCallSlotV1(
            relation_schedule_index,
            evidence.relation.binding_hash,
            "T2",
            call_number,
            True,
        )
        result = execute_mock_provider_slot_v1(
            slot=slot,
            request=request,
            transport=transport,
            ledger=call_ledger,
            parse_kind="proposal",
        )
        parse_status, core = _parsed_proposal_result(result)
        if core is None:
            outcome = ConstructionOutcomeRecordV1(
                relation_identity=evidence.relation.relation_identity,
                arm="T2",
                outcome="no_rule",
                accepted_call_index=None,
                generation_calls_consumed=call_number,
                verifier_invocations=call_number - 1,
                verifier_rejected_proposal_count=rejected,
                first_call_admissible=False,
                retrieval_count=retrieval_count,
                revise_count=revise_count,
                no_rule_reason=f"scientific_response:{parse_status}",
                feedback_path=feedback_path,
            )
            outcome_ledger.append(outcome)
            return outcome
        proposal = wrap_and_verify_core_v1(
            core=core,
            evidence=evidence,
            arm="T2",
            call_number=call_number,
            prompt_hash=request.model_visible_content_hash,
            synthetic_validity_fault=synthetic_validity_faults[call_number - 1],
        )
        proposal_ledger.append(proposal)
        validity = proposal.validity_result
        if validity.status == "admissible":
            outcome = ConstructionOutcomeRecordV1(
                relation_identity=evidence.relation.relation_identity,
                arm="T2",
                outcome="accepted_proposal",
                accepted_call_index=call_number,
                generation_calls_consumed=call_number,
                verifier_invocations=call_number,
                verifier_rejected_proposal_count=rejected,
                first_call_admissible=call_number == 1,
                retrieval_count=retrieval_count,
                revise_count=revise_count,
                feedback_path=feedback_path,
            )
            outcome_ledger.append(outcome)
            return outcome
        rejected += 1
        issue_codes = [issue.code for issue in validity.issues]
        action = _CONTROLLER.next_action(
            validity_status=validity.status,
            issue_codes=issue_codes,
            calls_consumed=call_number,
            retrieval_used=retrieval_used,
            retrievable_slice_exists=retrieval_identity is not None,
        )
        if action == "no_rule":
            budget_exhausted = call_number >= 3 and all(
                issue.repairability == "repairable" for issue in validity.issues
            )
            outcome = ConstructionOutcomeRecordV1(
                relation_identity=evidence.relation.relation_identity,
                arm="T2",
                outcome="no_rule",
                accepted_call_index=None,
                generation_calls_consumed=call_number,
                verifier_invocations=call_number,
                verifier_rejected_proposal_count=rejected,
                first_call_admissible=False,
                retrieval_count=retrieval_count,
                revise_count=revise_count,
                budget_exhaustion_count=1 if budget_exhausted else 0,
                no_rule_reason=(
                    "budget_exhaustion" if budget_exhausted else "non_repairable_issue"
                ),
            )
            outcome_ledger.append(outcome)
            return outcome
        retrieved: Mapping[str, Any] | None = None
        if action == "retrieve":
            if retrieval_identity is None:
                raise TASK039E3PreparationError("retrieval identity is required")
            retrieved = retrieve_existing_evidence_v1(
                view=view,
                requested_evidence_identities=(retrieval_identity,),
                retrieval_actions_already_used=1 if retrieval_used else 0,
            )
            retrieval_used = True
            retrieval_count += 1
            feedback_path = "retrieve"
        else:
            revise_count += 1
            if feedback_path is None:
                feedback_path = "revise"
        if call_number == 3:
            raise TASK039E3PreparationError("T2 fourth call is prohibited")
        request = t2_followup_request_builder(
            view=view,
            verifier_issue_codes=issue_codes,
            affected_fields=[issue.field for issue in validity.issues],
            previous_proposal_hash=proposal.proposal_hash,
            retrieved_evidence=retrieved,
        )
    raise TASK039E3PreparationError("T2 orchestration did not terminate")


@dataclass(frozen=True)
class DirectNumberOutcomeV1:
    relation_identity: str
    parse_status: str
    normalized_absolute_errors: Mapping[str, float] | None
    missing_number: bool
    nonfinite_or_parse_failure: bool
    sign_domain_violation_roles: tuple[str, ...]
    generation_calls_consumed: int = 1
    validity_authority: bool = False
    runtime_authority: bool = False

    def __post_init__(self) -> None:
        _require_nonempty_string(self.relation_identity, "direct-number relation")
        if self.normalized_absolute_errors is not None:
            errors = freeze_json(self.normalized_absolute_errors)
            if set(errors) != set(CALIBRATED_NUMERIC_ROLES):
                raise TASK039E3PreparationError("direct-number error roles differ")
            object.__setattr__(self, "normalized_absolute_errors", errors)
        if self.generation_calls_consumed != 1:
            raise TASK039E3PreparationError("direct-number requires one call")
        if self.validity_authority is not False or self.runtime_authority is not False:
            raise TASK039E3PreparationError("direct-number grants no authority")


def run_direct_number_v1(
    *,
    relation_schedule_index: int,
    evidence: ConstructionEvidenceContextV1,
    transport: MockProviderTransportV1,
    call_ledger: ProviderCallLedgerV1,
) -> DirectNumberOutcomeV1:
    view = evidence.render_view()
    request = build_direct_number_request_v1(view)
    slot = ProviderCallSlotV1(
        relation_schedule_index,
        evidence.relation.binding_hash,
        "T1-DIRECT-NUMBER",
        1,
        True,
    )
    result = execute_mock_provider_slot_v1(
        slot=slot,
        request=request,
        transport=transport,
        ledger=call_ledger,
        parse_kind="direct_number",
    )
    parsed = result.parsed_direct_number
    if parsed is None:
        raise TASK039E3PreparationError("direct-number parser result missing")
    if parsed.values is None:
        return DirectNumberOutcomeV1(
            relation_identity=evidence.relation.relation_identity,
            parse_status=parsed.parse_status,
            normalized_absolute_errors=None,
            missing_number=parsed.parse_status in {
                "provider_refusal",
                "incomplete_response",
                "schema_parse_failure",
            },
            nonfinite_or_parse_failure=parsed.parse_status != "provider_refusal",
            sign_domain_violation_roles=(),
        )
    approved = {
        binding.numeric_role: float(binding.value)
        for binding in view.numeric_bindings
        if binding.numeric_role in CALIBRATED_NUMERIC_ROLES
    }
    errors = {
        role: _DIRECT_NUMBER_POLICY.normalized_absolute_error(
            float(parsed.values[role]), approved[role]
        )
        for role in CALIBRATED_NUMERIC_ROLES
    }
    violations = tuple(
        role for role in CALIBRATED_NUMERIC_ROLES if float(parsed.values[role]) <= 0
    )
    return DirectNumberOutcomeV1(
        relation_identity=evidence.relation.relation_identity,
        parse_status=parsed.parse_status,
        normalized_absolute_errors=errors,
        missing_number=False,
        nonfinite_or_parse_failure=False,
        sign_domain_violation_roles=violations,
    )


def _rate(numerator: int, denominator: int) -> float:
    return 0.0 if denominator == 0 else numerator / denominator


def aggregate_construction_metrics_v1(
    records: Sequence[ConstructionOutcomeRecordV1],
) -> dict[str, Any]:
    metrics: dict[str, Any] = {}
    for arm in ("T0", "T1", "T1-B", "T2"):
        items = [record for record in records if record.arm == arm]
        denominator = len(items)
        accepted = sum(item.outcome == "accepted_proposal" for item in items)
        no_rule = sum(item.outcome == "no_rule" for item in items)
        arm_metrics: dict[str, Any] = {
            "eligible_relation_count": denominator,
            "accepted_proposal_count": accepted,
            "accepted_proposal_rate": _rate(accepted, denominator),
            "no_rule_count": no_rule,
            "no_rule_rate": _rate(no_rule, denominator),
            "verifier_rejected_proposal_count": sum(
                item.verifier_rejected_proposal_count for item in items
            ),
            "first_call_admissible_rate": _rate(
                sum(item.first_call_admissible for item in items), denominator
            ),
            "eventual_admissible_rate": _rate(accepted, denominator),
            "generation_calls_consumed": sum(
                item.generation_calls_consumed for item in items
            ),
            "verifier_invocations": sum(item.verifier_invocations for item in items),
            "retrieval_count": sum(item.retrieval_count for item in items),
            "revise_count": sum(item.revise_count for item in items),
            "budget_exhaustion_count": sum(
                item.budget_exhaustion_count for item in items
            ),
        }
        if arm == "T1-B":
            selected = {
                str(index): sum(item.accepted_call_index == index for item in items)
                for index in (1, 2, 3)
            }
            any_admissible = sum(
                item.accepted_call_index is not None for item in items
            )
            arm_metrics.update(
                {
                    "any_admissible_among_3_rate": _rate(
                        any_admissible, denominator
                    ),
                    "selected_call_index_distribution": selected,
                }
            )
        if arm == "T2":
            recovered = sum(
                item.outcome == "accepted_proposal"
                and item.accepted_call_index is not None
                and item.accepted_call_index > 1
                for item in items
            )
            arm_metrics.update(
                {
                    "feedback_recovery_count": recovered,
                    "feedback_recovery_rate": _rate(recovered, denominator),
                    "accepted_after_revise": sum(
                        item.outcome == "accepted_proposal"
                        and item.feedback_path == "revise"
                        for item in items
                    ),
                    "accepted_after_retrieve": sum(
                        item.outcome == "accepted_proposal"
                        and item.feedback_path == "retrieve"
                        for item in items
                    ),
                    "no_rule_due_non_repairable_issue": sum(
                        item.no_rule_reason == "non_repairable_issue" for item in items
                    ),
                    "no_rule_due_budget_exhaustion": sum(
                        item.no_rule_reason == "budget_exhaustion" for item in items
                    ),
                }
            )
        metrics[arm] = arm_metrics
    return metrics


def aggregate_direct_number_metrics_v1(
    outcomes: Sequence[DirectNumberOutcomeV1],
) -> dict[str, Any]:
    denominator = len(outcomes)
    role_errors = {
        role: [
            float(outcome.normalized_absolute_errors[role])
            for outcome in outcomes
            if outcome.normalized_absolute_errors is not None
        ]
        for role in CALIBRATED_NUMERIC_ROLES
    }
    return {
        "eligible_relation_count": denominator,
        "normalized_absolute_error_by_role": role_errors,
        "missing_number_rate": _rate(
            sum(outcome.missing_number for outcome in outcomes), denominator
        ),
        "nonfinite_or_parse_failure_rate": _rate(
            sum(outcome.nonfinite_or_parse_failure for outcome in outcomes),
            denominator,
        ),
        "sign_domain_violation_rate": _rate(
            sum(bool(outcome.sign_domain_violation_roles) for outcome in outcomes),
            denominator,
        ),
        "validity_authority": False,
        "runtime_authority": False,
    }


@dataclass(frozen=True)
class PublicConstructionMetricsV1:
    provider_call_ledger_hash: str
    proposal_ledger_hash: str
    outcome_ledger_hash: str
    main_metrics: Mapping[str, Any]
    direct_number_metrics: Mapping[str, Any]
    scientific_slot_count: int
    provider: str = PROVIDER
    model: str = EXACT_MODEL
    e2_protocol_bundle_hash: str = (
        "2295f6e57aff47081419d70e942af02101de33fa545a758ea4a7e6476a46e6e8"
    )
    schedule_hash: str = EXECUTION_SCHEDULE_HASH
    individual_proposals_public: bool = INDIVIDUAL_PROPOSALS_PUBLIC
    raw_private_evidence_public: bool = False
    rendered_prompts_public: bool = False
    credentials_public: bool = False
    runtime_authority: bool = False

    def __post_init__(self) -> None:
        for field_name in (
            "provider_call_ledger_hash",
            "proposal_ledger_hash",
            "outcome_ledger_hash",
            "e2_protocol_bundle_hash",
            "schedule_hash",
        ):
            _require_hash(getattr(self, field_name), field_name)
        if self.scientific_slot_count < 0 or self.scientific_slot_count > 336:
            raise TASK039E3PreparationError("public scientific slot count differs")
        object.__setattr__(self, "main_metrics", freeze_json(self.main_metrics))
        object.__setattr__(
            self, "direct_number_metrics", freeze_json(self.direct_number_metrics)
        )
        for field_name in (
            "individual_proposals_public",
            "raw_private_evidence_public",
            "rendered_prompts_public",
            "credentials_public",
            "runtime_authority",
        ):
            if getattr(self, field_name) is not False:
                raise TASK039E3PreparationError(f"{field_name} must remain false")

    @property
    def artifact_hash(self) -> str:
        return stable_hash_v1(self._content_dict())

    def _content_dict(self) -> dict[str, Any]:
        return {
            "artifact_type": "public_construction_metrics_v1",
            "provider_call_ledger_hash": self.provider_call_ledger_hash,
            "proposal_ledger_hash": self.proposal_ledger_hash,
            "outcome_ledger_hash": self.outcome_ledger_hash,
            "main_metrics": thaw_json(self.main_metrics),
            "direct_number_metrics": thaw_json(self.direct_number_metrics),
            "scientific_slot_count": self.scientific_slot_count,
            "provider": self.provider,
            "model": self.model,
            "e2_protocol_bundle_hash": self.e2_protocol_bundle_hash,
            "schedule_hash": self.schedule_hash,
            "individual_proposals_public": self.individual_proposals_public,
            "raw_private_evidence_public": self.raw_private_evidence_public,
            "rendered_prompts_public": self.rendered_prompts_public,
            "credentials_public": self.credentials_public,
            "runtime_authority": self.runtime_authority,
        }

    def to_dict(self) -> dict[str, Any]:
        document = self._content_dict()
        document["artifact_hash"] = self.artifact_hash
        return document


__all__ = [
    "ConstructionOutcomeLedgerV1",
    "ConstructionOutcomeRecordV1",
    "ConstructionProposalLedgerV1",
    "ConstructionProposalRecordV1",
    "DirectNumberOutcomeV1",
    "PublicConstructionMetricsV1",
    "aggregate_construction_metrics_v1",
    "aggregate_direct_number_metrics_v1",
    "retrieve_existing_evidence_v1",
    "run_direct_number_v1",
    "run_t0_v1",
    "run_t1_v1",
    "run_t1b_v1",
    "run_t2_v1",
    "wrap_and_verify_core_v1",
]
