"""Complete private proposal custody for future TASK-039E3 R2R runs.

The scientific proposal, validity, and record-hash formulas remain frozen.
This module only makes the full existing record-hash preimage durable and
verifiable after the in-memory proposal object has been discarded.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from paperworks.v6.common import stable_hash_v1
from paperworks.v6.task039e0_rule_construction_prep_v1 import (
    canonical_proposal_hash_v1,
)
from paperworks.v6.task039e0_validity_v2 import (
    PreparedValidityResultV2,
    ValidityIssueV2,
)
from paperworks.v6.task039e2_execution_configuration_v1 import (
    ProviderProposalCoreV1,
    RuleProposalEnvelopeV1,
    WINDOW_NUMERIC_ROLES,
)
from paperworks.v6.task039e3_orchestration_v1 import ConstructionProposalRecordV1
from paperworks.v6.task039e3_recovery_serialization_v1 import (
    normalize_plain_json_v1,
)


CUSTODY_RECORD_SCHEMA_VERSION_V2 = "2.0.0"
CUSTODY_RECORD_ARTIFACT_TYPE_V2 = (
    "task039e3_construction_proposal_custody_record_v2"
)

_RECORD_FIELDS_V2 = frozenset(
    {
        "schema_version",
        "artifact_type",
        "relation_identity",
        "arm",
        "call_number",
        "proposal_envelope",
        "project_proposal",
        "validity_result",
        "proposal_hash",
        "validity_hash",
        "record_hash",
    }
)
_ENVELOPE_FIELDS_V1 = frozenset(
    {
        "proposal_core",
        "construction_arm",
        "local_call_number",
        "budget_policy_hash",
        "evidence_hash",
        "prompt_hash",
        "provider_model_receipt_hash",
        "execution_schedule_hash",
    }
)
_CORE_FIELDS_V1 = frozenset(
    {
        "dsl_family",
        "relation_identity",
        "source",
        "source_step_direction",
        "target",
        "target_response_direction",
        "selected_delay_horizon_seconds",
        "source_threshold_reference",
        "source_stability_reference",
        "target_scale_reference",
        "window_constant_references",
        "variables",
        "runtime_logic_family",
    }
)


class TASK039E3ProposalCustodyError(ValueError):
    """Proposal custody is incomplete or differs from the frozen hashes."""


def _require_hash(value: Any, field: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise TASK039E3ProposalCustodyError(
            f"{field} must be a lowercase SHA-256"
        )
    return value


def _proposal_envelope_document_v1(
    envelope: RuleProposalEnvelopeV1,
) -> dict[str, Any]:
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


def proposal_record_hash_preimage_v1(
    document: Mapping[str, Any],
) -> dict[str, Any]:
    """Return the unchanged historical record-hash preimage."""

    normalized = normalize_plain_json_v1(document)
    if not isinstance(normalized, dict):
        raise TASK039E3ProposalCustodyError("proposal custody must be an object")
    required = {
        "relation_identity",
        "arm",
        "call_number",
        "proposal_envelope",
        "proposal_hash",
        "validity_hash",
    }
    if not required.issubset(normalized):
        raise TASK039E3ProposalCustodyError(
            "proposal custody omits the record-hash preimage"
        )
    return {field: normalized[field] for field in (
        "relation_identity",
        "arm",
        "call_number",
        "proposal_envelope",
        "proposal_hash",
        "validity_hash",
    )}


def _reconstruct_envelope_v1(document: Mapping[str, Any]) -> RuleProposalEnvelopeV1:
    if set(document) != _ENVELOPE_FIELDS_V1:
        raise TASK039E3ProposalCustodyError("proposal envelope is not exact and closed")
    core_document = document.get("proposal_core")
    if not isinstance(core_document, Mapping) or set(core_document) != _CORE_FIELDS_V1:
        raise TASK039E3ProposalCustodyError("proposal core is not exact and closed")
    variables = core_document.get("variables")
    windows = core_document.get("window_constant_references")
    if not isinstance(variables, list):
        raise TASK039E3ProposalCustodyError("proposal variables differ")
    if not isinstance(windows, Mapping):
        raise TASK039E3ProposalCustodyError("window references differ")
    try:
        core = ProviderProposalCoreV1(
            dsl_family=core_document["dsl_family"],
            relation_identity=core_document["relation_identity"],
            source=core_document["source"],
            source_step_direction=core_document["source_step_direction"],
            target=core_document["target"],
            target_response_direction=core_document["target_response_direction"],
            selected_delay_horizon_seconds=core_document[
                "selected_delay_horizon_seconds"
            ],
            source_threshold_reference=core_document[
                "source_threshold_reference"
            ],
            source_stability_reference=core_document[
                "source_stability_reference"
            ],
            target_scale_reference=core_document["target_scale_reference"],
            window_constant_references=dict(windows),
            variables=tuple(variables),
            runtime_logic_family=core_document["runtime_logic_family"],
        )
        envelope = RuleProposalEnvelopeV1(
            proposal_core=core,
            construction_arm=document["construction_arm"],
            local_call_number=document["local_call_number"],
            budget_policy_hash=document["budget_policy_hash"],
            evidence_hash=document["evidence_hash"],
            prompt_hash=document["prompt_hash"],
            provider_model_receipt_hash=document[
                "provider_model_receipt_hash"
            ],
            execution_schedule_hash=document["execution_schedule_hash"],
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise TASK039E3ProposalCustodyError(
            "proposal envelope differs from the frozen contract"
        ) from exc
    if _proposal_envelope_document_v1(envelope) != dict(document):
        raise TASK039E3ProposalCustodyError("proposal envelope normalization differs")
    return envelope


def _reconstruct_validity_v2(
    document: Mapping[str, Any],
) -> PreparedValidityResultV2:
    issues = document.get("issues")
    if not isinstance(issues, list):
        raise TASK039E3ProposalCustodyError("validity issues differ")
    try:
        result = PreparedValidityResultV2(
            proposal_hash=document["proposal_hash"],
            relation_binding_hash=document["relation_binding_hash"],
            evidence_bundle_hash=document["evidence_bundle_hash"],
            construction_provenance_hash=document[
                "construction_provenance_hash"
            ],
            budget_policy_hash=document["budget_policy_hash"],
            status=document["status"],
            issues=tuple(
                ValidityIssueV2(
                    code=item["code"],
                    field=item["field"],
                    repairability=item["repairability"],
                    t2_action_class=item["t2_action_class"],
                )
                for item in issues
            ),
            verifier_version=document["verifier_version"],
            project_owned_deterministic_code=document[
                "project_owned_deterministic_code"
            ],
            label_input_used=document["label_input_used"],
            utility_input_used=document["utility_input_used"],
            llm_chain_of_thought_used=document["llm_chain_of_thought_used"],
            canonical_rule_materialized=document[
                "canonical_rule_materialized"
            ],
            validity_authority_granted=document[
                "validity_authority_granted"
            ],
            runtime_authority_granted=document["runtime_authority_granted"],
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise TASK039E3ProposalCustodyError(
            "validity result differs from the frozen contract"
        ) from exc
    if result.to_dict() != dict(document):
        raise TASK039E3ProposalCustodyError("validity result normalization differs")
    return result


def verify_serialized_construction_proposal_custody_record_v2(
    document: Mapping[str, Any],
) -> dict[str, Any]:
    """Verify all three hashes using serialized custody alone."""

    normalized = normalize_plain_json_v1(document)
    if not isinstance(normalized, dict) or set(normalized) != _RECORD_FIELDS_V2:
        raise TASK039E3ProposalCustodyError(
            "proposal custody record is not exact and closed"
        )
    if (
        normalized["schema_version"] != CUSTODY_RECORD_SCHEMA_VERSION_V2
        or normalized["artifact_type"] != CUSTODY_RECORD_ARTIFACT_TYPE_V2
    ):
        raise TASK039E3ProposalCustodyError("proposal custody version differs")
    relation_identity = normalized["relation_identity"]
    arm = normalized["arm"]
    call_number = normalized["call_number"]
    if not isinstance(relation_identity, str) or not relation_identity:
        raise TASK039E3ProposalCustodyError("proposal relation identity differs")
    if arm not in {"T0", "T1", "T1-B", "T2"}:
        raise TASK039E3ProposalCustodyError("proposal arm differs")
    if isinstance(call_number, bool) or not isinstance(call_number, int):
        raise TASK039E3ProposalCustodyError("proposal call number differs")
    if (arm == "T0" and call_number != 0) or (
        arm != "T0" and call_number not in {1, 2, 3}
    ):
        raise TASK039E3ProposalCustodyError("proposal arm/call binding differs")

    envelope_document = normalized["proposal_envelope"]
    if not isinstance(envelope_document, Mapping):
        raise TASK039E3ProposalCustodyError("proposal envelope is missing")
    envelope = _reconstruct_envelope_v1(envelope_document)
    if (
        envelope.proposal_core.relation_identity != relation_identity
        or envelope.construction_arm != arm
        or envelope.local_call_number != call_number
    ):
        raise TASK039E3ProposalCustodyError("proposal envelope binding differs")

    proposal = normalized["project_proposal"]
    validity_document = normalized["validity_result"]
    if not isinstance(proposal, Mapping) or not isinstance(
        validity_document, Mapping
    ):
        raise TASK039E3ProposalCustodyError(
            "proposal or validity document is missing"
        )
    proposal_hash = _require_hash(normalized["proposal_hash"], "proposal hash")
    validity_hash = _require_hash(normalized["validity_hash"], "validity hash")
    _require_hash(normalized["record_hash"], "record hash")
    if (
        proposal.get("proposal_hash") != proposal_hash
        or canonical_proposal_hash_v1(proposal) != proposal_hash
    ):
        raise TASK039E3ProposalCustodyError("proposal hash differs")
    validity = _reconstruct_validity_v2(validity_document)
    if validity.proposal_hash != proposal_hash or validity.artifact_hash != validity_hash:
        raise TASK039E3ProposalCustodyError("proposal/validity hash binding differs")

    core = envelope.proposal_core
    expected_project_bindings = {
        "construction_arm": arm,
        "dsl_family": core.dsl_family,
        "relation_identity": core.relation_identity,
        "source": core.source,
        "source_step_direction": core.source_step_direction,
        "target": core.target,
        "target_response_direction": core.target_response_direction,
        "selected_delay_horizon_seconds": core.selected_delay_horizon_seconds,
        "source_threshold_reference": core.source_threshold_reference,
        "source_stability_reference": core.source_stability_reference,
        "target_scale_reference": core.target_scale_reference,
        "preregistered_window_constant_references": [
            core.window_constant_references[role] for role in WINDOW_NUMERIC_ROLES
        ],
        "variables": list(core.variables),
        "runtime_logic": core.runtime_logic_family,
    }
    if any(proposal.get(key) != value for key, value in expected_project_bindings.items()):
        raise TASK039E3ProposalCustodyError("proposal core/project binding differs")
    if (
        validity.relation_binding_hash != proposal.get("relation_binding_hash")
        or validity.construction_provenance_hash
        != proposal.get("construction_provenance_hash")
        or validity.budget_policy_hash != envelope.budget_policy_hash
    ):
        raise TASK039E3ProposalCustodyError("validity provenance binding differs")

    expected_record_hash = stable_hash_v1(
        proposal_record_hash_preimage_v1(normalized)
    )
    if expected_record_hash != normalized["record_hash"]:
        raise TASK039E3ProposalCustodyError("proposal record hash differs")
    return normalized


def serialize_construction_proposal_custody_record_v2(
    record: ConstructionProposalRecordV1,
) -> dict[str, Any]:
    """Build the sole working/final proposal custody representation."""

    document = {
        "schema_version": CUSTODY_RECORD_SCHEMA_VERSION_V2,
        "artifact_type": CUSTODY_RECORD_ARTIFACT_TYPE_V2,
        "relation_identity": record.relation_identity,
        "arm": record.arm,
        "call_number": record.call_number,
        "proposal_envelope": _proposal_envelope_document_v1(
            record.proposal_envelope
        ),
        "project_proposal": record.project_proposal,
        "validity_result": record.validity_result.to_dict(),
        "proposal_hash": record.proposal_hash,
        "validity_hash": record.validity_hash,
        "record_hash": record.record_hash,
    }
    return verify_serialized_construction_proposal_custody_record_v2(document)


__all__ = [
    "CUSTODY_RECORD_ARTIFACT_TYPE_V2",
    "CUSTODY_RECORD_SCHEMA_VERSION_V2",
    "TASK039E3ProposalCustodyError",
    "proposal_record_hash_preimage_v1",
    "serialize_construction_proposal_custody_record_v2",
    "verify_serialized_construction_proposal_custody_record_v2",
]
