"""Authoritative, offline TASK-039E2 construction-execution freeze.

The module is deliberately pure apart from reading committed public artifacts
when ``build_task039e2_artifacts_v1`` is invoked.  It contains no provider
client, credential access, private-ledger loader, HAI loader, proposal
execution, or runtime authority path.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
import math
from pathlib import Path
import re
from types import MappingProxyType
from typing import Any, ClassVar, Mapping, Sequence

from paperworks.v6.common import (
    V6_FOUNDATION_SCHEMA_VERSION,
    freeze_json,
    stable_hash_v1,
    thaw_json,
)


TASK_ID = "TASK-039E2"
STATUS = "passed_task039e2_execution_configuration_freeze"
NEXT_TASK = "TASK-039E2-AUDIT"

AUTHORITATIVE_MAIN = "4a6b5875b59bdcc7c3bd0957e90fa27b71e0e9fb"
E2_PREP_COMMIT = "ad149f4836fcdefb65fe2a3bcd39b728284a0b84"
E2_AUTHORIZATION_HASH = "5a68559bc0e95c6e92061cbf5762ed3359817537f3cbe0c5ae885774d14250ff"
E0_PROTOCOL_BUNDLE_HASH = "a95aecffeaff82d0c67f966f19293ef947827cb0e1e7621a38ecd7c1fd96e17b"
E1_MATERIALIZATION_RESULT_HASH = "2831f175f777bc0544513c35926269e05b6360c17e13f70b89d1768f1c7aa164"
E1_CONSTRUCTION_EVIDENCE_COHORT_HASH = "4eb4da843a61a9c72aba59edcdf90e49766fc571af7eade14d500b3d04d363d4"
E1_PRIVATE_LEDGER_HASH = "0998c6600078b8a0aca7263b6e0b702808cc141b1cbcfe3d0026fddb98c408a7"
E0_CONTROLLER_HASH = "6cc22fea19a636d590cb5e744d896e8f8588946049d2e0743674883c9eae15b4"
E0_BUDGET_POLICY_HASH = "d36e297cb1de71d4a04f4ad99a31d7c75c076d1b2d6b2ccb74905bdcf4cc1c64"

RELATION_COUNT = 42
NUMERIC_BINDING_COUNT = 462
MAXIMUM_SCIENTIFIC_CALLS = 336
SCIENTIFIC_CONCURRENCY = 1

PROVIDER = "openai"
PROVIDER_NAME = "OpenAI"
ENDPOINT_FAMILY = "chat_completions"
API_BASE_URL = "https://api.openai.com"
API_ENDPOINT = "/v1/chat/completions"
EXACT_MODEL = "gpt-5.4-2026-03-05"
CREDENTIAL_ENVIRONMENT_VARIABLE = "OPENAI_API_KEY"

CALIBRATED_NUMERIC_ROLES = (
    "source_step_threshold",
    "source_stability_tolerance",
    "target_noise_scale",
)
WINDOW_NUMERIC_ROLES = (
    "source_pre_window_seconds",
    "source_post_window_seconds",
    "minimum_source_stability_fraction",
    "source_refractory_seconds",
    "cross_source_isolation_radius_seconds",
    "target_baseline_window_seconds",
    "target_response_window_seconds",
)

MAIN_INITIAL_PROMPT_V1 = """You construct one bounded delayed-response rule proposal candidate.
Use only the supplied ConstructionInputViewV1 scientific content. Return one
ProviderProposalCoreV1 object conforming exactly to the supplied strict JSON
schema. Bind the exact relation identity, source and target identities,
directions, selected delay horizon, approved numeric references, approved
window references, and runtime-logic family. The approved numeric values may
support reasoning, but the proposal must return their references and must not
invent replacement numeric literals. Do not add provenance, arm identity,
call number, controller actions, free-text runtime code, authority claims, or
unsupported variables. Project code adds proposal-envelope provenance after
parsing."""

T2_FOLLOWUP_PROMPT_V1 = """Produce one fresh corrected ProviderProposalCoreV1.
Use the original frozen ConstructionInputViewV1, the bounded deterministic
validity issue codes and affected fields, any approved targeted
re-presentation of evidence already present in the initial corpus, and the
previous proposal hash only for provenance. Do not provide chain-of-thought,
controller actions, human feedback, labels, utility outcomes, candidate-arm
results, new evidence, or authority claims. Return only the strict structured
proposal core."""

DIRECT_NUMBER_PROMPT_V1 = """Estimate exactly three construction-only numeric
quantities for the supplied relation context: source_step_threshold,
source_stability_tolerance, and target_noise_scale. The approved values and
references for those three roles are withheld. The relation identity,
directions, selected delay horizon, and preregistered window constants remain
provided. Return only the three finite JSON numbers under the strict schema.
These estimates grant no validity, rule, or runtime authority."""

_SHA256 = re.compile(r"^[a-f0-9]{64}$")
_PROHIBITED_MODEL_VISIBLE_KEYS = frozenset(
    {
        "construction_arm",
        "arm",
        "call_index",
        "call_number",
        "candidate_method_origin",
        "origin_arms",
        "META",
        "STAT",
        "GDN",
        "previous_other_arm_result",
        "t0_result",
        "utility_result",
    }
)


class TASK039E2ConfigurationError(ValueError):
    """Raised when an E2 execution-freeze invariant is violated."""


def _canonical_json(value: Mapping[str, Any]) -> str:
    return json.dumps(
        thaw_json(value),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    )


def _text_hash(value: str) -> str:
    return sha256(value.encode("utf-8")).hexdigest()


def _require_hash(value: object, name: str) -> str:
    if not isinstance(value, str) or _SHA256.fullmatch(value) is None:
        raise TASK039E2ConfigurationError(f"{name} must be a lowercase SHA-256")
    return value


def verify_self_hash_v1(document: Mapping[str, Any]) -> str:
    observed = document.get("artifact_hash")
    _require_hash(observed, "artifact_hash")
    content = {key: value for key, value in document.items() if key != "artifact_hash"}
    expected = stable_hash_v1(content)
    if observed != expected:
        raise TASK039E2ConfigurationError("artifact self-hash mismatch")
    return expected


@dataclass(frozen=True)
class _ClosedArtifactV1:
    """Small immutable closed record shared by the E2 policy artifacts."""

    payload: Mapping[str, Any]

    ARTIFACT_TYPE: ClassVar[str] = ""
    FIELDS: ClassVar[frozenset[str]] = frozenset()

    def __post_init__(self) -> None:
        frozen = freeze_json(self.payload)
        object.__setattr__(self, "payload", frozen)
        keys = set(frozen)
        if keys != set(self.FIELDS):
            missing = sorted(set(self.FIELDS) - keys)
            unknown = sorted(keys - set(self.FIELDS))
            raise TASK039E2ConfigurationError(
                f"{self.ARTIFACT_TYPE} field closure differs; missing={missing}, unknown={unknown}"
            )

    def _content_dict(self) -> dict[str, Any]:
        return {
            "schema_version": V6_FOUNDATION_SCHEMA_VERSION,
            "artifact_type": self.ARTIFACT_TYPE,
            **thaw_json(self.payload),
        }

    @property
    def artifact_hash(self) -> str:
        return stable_hash_v1(self._content_dict())

    def to_dict(self) -> dict[str, Any]:
        return {**self._content_dict(), "artifact_hash": self.artifact_hash}

    @classmethod
    def from_dict(cls, document: Mapping[str, Any]) -> "_ClosedArtifactV1":
        verify_self_hash_v1(document)
        expected = {"schema_version", "artifact_type", "artifact_hash", *cls.FIELDS}
        if set(document) != expected:
            raise TASK039E2ConfigurationError(f"{cls.ARTIFACT_TYPE} unknown field")
        if document["schema_version"] != V6_FOUNDATION_SCHEMA_VERSION:
            raise TASK039E2ConfigurationError("schema version differs")
        if document["artifact_type"] != cls.ARTIFACT_TYPE:
            raise TASK039E2ConfigurationError("artifact type differs")
        return cls({key: document[key] for key in cls.FIELDS})


class ProviderModelFreezeV1(_ClosedArtifactV1):
    ARTIFACT_TYPE = "provider_model_freeze_v1"
    FIELDS = frozenset(
        {
            "provider",
            "provider_name",
            "api_endpoint_family",
            "api_base_url",
            "api_endpoint",
            "exact_model_snapshot",
            "snapshot_locked",
            "model_alias_fallback_allowed",
            "automatic_upgrade_allowed",
            "alternative_model_fallback_allowed",
            "unavailable_snapshot_outcome",
            "transport_implementation",
            "provider_sdk_dependency",
            "credential_environment_variable",
            "credential_accessed",
            "provider_contacted",
            "account_snapshot_availability",
        }
    )


class ModelCapabilityReceiptV1(_ClosedArtifactV1):
    ARTIFACT_TYPE = "task039e2_authoritative_model_capability_receipt_v1"
    FIELDS = frozenset(
        {
            "provider",
            "model",
            "snapshot_locked",
            "chat_completions_supported",
            "structured_outputs_supported",
            "reasoning_effort_none_supported",
            "temperature_parameter_expected",
            "seed_capability",
            "seed_reproducibility_relied_upon",
            "account_specific_model_availability",
            "provider_contacted",
            "credential_availability",
            "capability_basis",
            "review_date",
            "source_documents",
        }
    )


class ConstructionExecutionConfigurationV1(_ClosedArtifactV1):
    ARTIFACT_TYPE = "task039e2_authoritative_construction_execution_configuration_v1"
    FIELDS = frozenset(
        {
            "provider_model_freeze_hash",
            "model_capability_receipt_hash",
            "shared_llm_arms",
            "sampling_configuration",
            "sampling_configuration_hash",
            "reasoning_methodological_rationale",
            "stateless_requests",
            "reasoning_persistence",
            "previous_response_id_used",
            "provider_managed_conversational_state",
            "prompt_template_bundle_hash",
            "main_structured_output_policy_hash",
            "direct_number_structured_output_policy_hash",
            "rendering_policy_hash",
            "retrieval_policy_hash",
            "t0_template_policy_hash",
            "schedule_hash",
            "transport_retry_policy_hash",
            "provider_response_custody_policy_hash",
            "direct_number_role_policy_hash",
            "provider_contacted",
            "credential_checked",
            "capability_probe_executed",
            "llm_called",
            "execution_authorized",
        }
    )


class PromptTemplateBundleV1(_ClosedArtifactV1):
    ARTIFACT_TYPE = "task039e2_prompt_template_bundle_v1"
    FIELDS = frozenset(
        {
            "main_initial_template_version",
            "main_initial_template_path",
            "main_initial_prompt_hash",
            "t2_followup_template_version",
            "t2_followup_template_path",
            "t2_followup_prompt_hash",
            "direct_number_template_version",
            "direct_number_template_path",
            "direct_number_prompt_hash",
            "main_initial_shared_arms",
            "initial_model_visible_content_hash_method",
            "initial_content_equality_required",
            "arm_identity_model_visible",
            "call_index_model_visible",
            "t1b_stateless_independent_requests",
            "t1b_previous_proposal_visible",
            "t1b_previous_validity_visible",
            "t1b_all_three_calls_required",
            "t1b_selection_rule",
            "raw_rendered_prompt_policy",
        }
    )


class MainStructuredOutputPolicyV1(_ClosedArtifactV1):
    ARTIFACT_TYPE = "task039e2_main_structured_output_policy_v1"
    FIELDS = frozenset(
        {
            "provider_core_contract",
            "project_envelope_contract",
            "strict",
            "provider_schema_path",
            "provider_schema_hash",
            "relation_specific_const_present",
            "relation_specific_singleton_enum_present",
            "model_generates_project_provenance",
            "arbitrary_numeric_literals_allowed",
            "semantic_binding_verified_by",
        }
    )


class DirectNumberStructuredOutputPolicyV1(_ClosedArtifactV1):
    ARTIFACT_TYPE = "task039e2_direct_number_structured_output_policy_v1"
    FIELDS = frozenset(
        {
            "strict",
            "provider_schema_path",
            "provider_schema_hash",
            "numeric_roles",
            "exact_numeric_field_count",
            "finite_json_numbers_required",
            "relation_specific_calibrated_bounds_present",
            "validity_authority",
            "runtime_authority",
        }
    )


class ConstructionEvidenceRenderingPolicyV1(_ClosedArtifactV1):
    ARTIFACT_TYPE = "task039e2_construction_evidence_rendering_policy_v1"
    FIELDS = frozenset(
        {
            "input_contract",
            "approved_source",
            "model_visible_fields",
            "prohibited_fields",
            "main_calibrated_values_visible",
            "main_proposal_outputs_references",
            "raw_rendered_prompt_policy",
            "rendered_prompt_hash_recorded",
            "construction_input_view_hash_recorded",
            "private_evidence_ledger_accessed_in_e2",
            "hai_accessed",
        }
    )


class T2RetrievalCorpusPolicyV1(_ClosedArtifactV1):
    ARTIFACT_TYPE = "task039e2_authoritative_t2_retrieval_corpus_policy_v1"
    FIELDS = frozenset(
        {
            "underlying_corpus",
            "retrieval_semantics",
            "allowed_slices",
            "prohibited_sources",
            "new_scientific_evidence_allowed",
            "maximum_retrieval_actions_per_relation",
            "provider_generation_calls_consumed_by_retrieval",
            "subsequent_revision_consumes_generation_call",
            "controller_hash",
            "controller_is_project_owned",
            "model_selects_controller_action",
        }
    )


class T0TemplatePolicyV1(_ClosedArtifactV1):
    ARTIFACT_TYPE = "task039e2_t0_template_policy_v1"
    FIELDS = frozenset(
        {
            "template_version",
            "template_specification",
            "template_hash",
            "proposal_core_contract",
            "proposal_envelope_contract",
            "uses_approved_e1_references",
            "llm_used",
            "search_used",
            "fallback_used",
            "synthetic_tests_only_in_e2",
            "real_relation_generated",
        }
    )


class ConstructionExecutionScheduleV1(_ClosedArtifactV1):
    ARTIFACT_TYPE = "task039e2_authoritative_construction_execution_schedule_v1"
    FIELDS = frozenset(
        {
            "e1_cohort_hash",
            "relation_count",
            "relation_order_policy",
            "relation_identities",
            "relation_identity_order_hash",
            "serialization_order_is_scientific_rank",
            "per_relation_sequence",
            "t0_provider_calls",
            "t1_maximum_scientific_calls",
            "t1b_fixed_scientific_calls",
            "t2_maximum_scientific_calls",
            "direct_number_scientific_calls",
            "maximum_scientific_calls",
            "scientific_concurrency",
            "result_dependent_ordering",
            "cross_arm_output_visibility",
            "t2_own_validity_feedback_only",
            "capability_probe_count",
            "capability_probe_fixture",
            "capability_probe_scientific_call",
            "capability_probe_may_change_frozen_configuration",
            "capability_probe_unsupported_outcome",
        }
    )


class TransportRetryPolicyV1(_ClosedArtifactV1):
    ARTIFACT_TYPE = "task039e2_transport_retry_policy_v1"
    FIELDS = frozenset(
        {
            "maximum_transport_retries_per_request",
            "scientific_generation_retries",
            "retryable_no_response_outcomes",
            "non_retryable_outcomes",
            "fixed_retry_delays_seconds",
            "retry_after_429_policy",
            "retry_after_validity_policy",
            "response_failures_consume_scientific_call",
            "retry_exhaustion_outcome",
            "relation_skip_allowed",
        }
    )


class ProviderResponseCustodyPolicyV1(_ClosedArtifactV1):
    ARTIFACT_TYPE = "task039e2_provider_response_custody_policy_v1"
    FIELDS = frozenset(
        {
            "required_receipt_fields",
            "structured_parsed_response_is_scientific_record",
            "raw_model_output_policy",
            "prohibited_stored_fields",
            "provider_refusal_consumes_scientific_call",
            "incomplete_output_consumes_scientific_call",
            "schema_parse_failure_consumes_scientific_call",
            "verifier_rejection_consumes_scientific_call",
            "provider_refusal_repairability",
            "provider_refusal_t2_outcome",
            "received_failure_is_transport_failure",
            "arm_response_handling",
        }
    )


class DirectNumberRolePolicyV1(_ClosedArtifactV1):
    ARTIFACT_TYPE = "task039e2_direct_number_role_policy_v1"
    FIELDS = frozenset(
        {
            "arm",
            "designated_comparator",
            "calls_per_relation",
            "numeric_roles",
            "withheld_values",
            "withheld_references",
            "provided_context",
            "retrieval_allowed",
            "normalized_absolute_error_formula",
            "additional_metrics",
            "label_free",
            "validity_authority",
            "runtime_authority",
        }
    )


class TASK039E2ProtocolBundleV1(_ClosedArtifactV1):
    ARTIFACT_TYPE = "task039e2_protocol_bundle_v1"
    FIELDS = frozenset(
        {
            "task_id",
            "status",
            "next_task",
            "authoritative_main",
            "e2_prep_commit",
            "e2_authorization_hash",
            "e0_protocol_bundle_hash",
            "e1_materialization_result_hash",
            "e1_construction_evidence_cohort_hash",
            "e1_private_ledger_hash",
            "relation_count",
            "numeric_binding_count",
            "component_hashes",
            "provider_contacted",
            "credential_checked",
            "capability_probe_executed",
            "llm_called",
            "real_t0_generated",
            "t1_generated",
            "t1b_generated",
            "t2_generated",
            "direct_number_executed",
            "e3_authorization_created",
            "rule_v2_authorized",
            "runtime_authority",
            "e1_private_evidence_accessed",
            "hai_accessed",
        }
    )


ARTIFACT_CLASSES = (
    ProviderModelFreezeV1,
    ModelCapabilityReceiptV1,
    ConstructionExecutionConfigurationV1,
    PromptTemplateBundleV1,
    MainStructuredOutputPolicyV1,
    DirectNumberStructuredOutputPolicyV1,
    ConstructionEvidenceRenderingPolicyV1,
    T2RetrievalCorpusPolicyV1,
    T0TemplatePolicyV1,
    ConstructionExecutionScheduleV1,
    TransportRetryPolicyV1,
    ProviderResponseCustodyPolicyV1,
    DirectNumberRolePolicyV1,
    TASK039E2ProtocolBundleV1,
)


MAIN_PROVIDER_SCHEMA_V1: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "additionalProperties": False,
    "required": [
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
    ],
    "properties": {
        "dsl_family": {
            "type": "string",
            "enum": ["canonical_delayed_response_rule_v1_candidate"],
        },
        "relation_identity": {"type": "string", "minLength": 1},
        "source": {"type": "string", "minLength": 1},
        "source_step_direction": {
            "type": "string",
            "enum": ["step_down", "step_up"],
        },
        "target": {"type": "string", "minLength": 1},
        "target_response_direction": {
            "type": "string",
            "enum": ["decrease", "increase"],
        },
        "selected_delay_horizon_seconds": {
            "type": "integer",
            "enum": [1, 5, 10, 30, 60],
        },
        "source_threshold_reference": {"type": "string", "pattern": "^[a-f0-9]{64}$"},
        "source_stability_reference": {"type": "string", "pattern": "^[a-f0-9]{64}$"},
        "target_scale_reference": {"type": "string", "pattern": "^[a-f0-9]{64}$"},
        "window_constant_references": {
            "type": "object",
            "additionalProperties": False,
            "required": list(WINDOW_NUMERIC_ROLES),
            "properties": {
                role: {"type": "string", "pattern": "^[a-f0-9]{64}$"}
                for role in WINDOW_NUMERIC_ROLES
            },
        },
        "variables": {
            "type": "array",
            "minItems": 2,
            "maxItems": 2,
            "uniqueItems": True,
            "items": {"type": "string", "minLength": 1},
        },
        "runtime_logic_family": {
            "type": "string",
            "enum": ["missing_expected_delayed_response"],
        },
    },
}

DIRECT_NUMBER_PROVIDER_SCHEMA_V1: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "additionalProperties": False,
    "required": list(CALIBRATED_NUMERIC_ROLES),
    "properties": {role: {"type": "number"} for role in CALIBRATED_NUMERIC_ROLES},
}


def assert_generic_main_schema_v1(schema: Mapping[str, Any]) -> None:
    """Reject relation-answer leakage while allowing generic DSL enums."""

    if schema.get("type") != "object" or schema.get("additionalProperties") is not False:
        raise TASK039E2ConfigurationError("main structured output schema must be closed")
    def has_const(item: Any) -> bool:
        if isinstance(item, Mapping):
            return "const" in item or any(has_const(value) for value in item.values())
        if isinstance(item, (list, tuple)):
            return any(has_const(value) for value in item)
        return False

    if has_const(schema):
        raise TASK039E2ConfigurationError("relation-specific const leakage is prohibited")
    properties = schema.get("properties", {})
    for key in ("source", "target", "relation_identity"):
        definition = properties.get(key, {})
        if "enum" in definition:
            raise TASK039E2ConfigurationError("relation-specific singleton enum leakage")


def validate_sampling_configuration_v1(config: Mapping[str, Any]) -> None:
    expected = {
        "model": EXACT_MODEL,
        "reasoning_effort": "none",
        "temperature": 0.7,
        "top_p": 1.0,
        "max_completion_tokens": 1024,
        "n": 1,
        "seed": None,
        "seed_used": False,
        "seed_determinism_claimed": False,
        "presence_penalty": 0,
        "frequency_penalty": 0,
        "stream": False,
        "store": False,
        "tools": [],
        "tool_choice": None,
    }
    if thaw_json(config) != expected:
        raise TASK039E2ConfigurationError("sampling configuration differs")


def assert_model_visible_input_boundary_v1(value: Mapping[str, Any]) -> None:
    def walk(item: Any, path: str) -> None:
        if isinstance(item, Mapping):
            for key, nested in item.items():
                if key in _PROHIBITED_MODEL_VISIBLE_KEYS:
                    raise TASK039E2ConfigurationError(
                        f"prohibited model-visible field at {path}.{key}"
                    )
                walk(nested, f"{path}.{key}")
        elif isinstance(item, (list, tuple)):
            for index, nested in enumerate(item):
                walk(nested, f"{path}[{index}]")

    walk(value, "$input")


def render_main_initial_model_content_v1(view: Mapping[str, Any]) -> str:
    assert_model_visible_input_boundary_v1(view)
    return MAIN_INITIAL_PROMPT_V1 + "\n\nCONSTRUCTION_INPUT_VIEW_JSON\n" + _canonical_json(view)


def initial_model_visible_content_hash_v1(view: Mapping[str, Any]) -> str:
    return _text_hash(render_main_initial_model_content_v1(view))


def render_t2_followup_model_content_v1(
    *,
    original_view: Mapping[str, Any],
    verifier_issue_codes: Sequence[str],
    affected_fields: Sequence[str],
    previous_proposal_hash: str,
    retrieved_evidence: Mapping[str, Any] | None,
) -> str:
    assert_model_visible_input_boundary_v1(original_view)
    _require_hash(previous_proposal_hash, "previous_proposal_hash")
    if not verifier_issue_codes or not all(isinstance(item, str) and item for item in verifier_issue_codes):
        raise TASK039E2ConfigurationError("bounded verifier issue codes required")
    if not affected_fields or not all(isinstance(item, str) and item for item in affected_fields):
        raise TASK039E2ConfigurationError("bounded affected fields required")
    payload = {
        "original_construction_input": thaw_json(original_view),
        "verifier_issue_codes": list(verifier_issue_codes),
        "affected_fields": list(affected_fields),
        "retrieved_evidence": thaw_json(retrieved_evidence) if retrieved_evidence else None,
        "previous_proposal_hash": previous_proposal_hash,
    }
    return T2_FOLLOWUP_PROMPT_V1 + "\n\nT2_FOLLOWUP_INPUT_JSON\n" + _canonical_json(payload)


def render_direct_number_model_content_v1(view: Mapping[str, Any]) -> str:
    assert_model_visible_input_boundary_v1(view)
    rendered = thaw_json(view)
    bindings = rendered.get("numeric_bindings")
    if not isinstance(bindings, list):
        raise TASK039E2ConfigurationError("direct-number view requires numeric_bindings")
    retained = []
    observed_withheld: set[str] = set()
    withheld_evidence_identities: set[str] = set()
    withheld_references: set[str] = set()
    for item in bindings:
        if not isinstance(item, Mapping) or "numeric_role" not in item:
            raise TASK039E2ConfigurationError("numeric binding is malformed")
        role = str(item["numeric_role"])
        if role in CALIBRATED_NUMERIC_ROLES:
            observed_withheld.add(role)
            if "evidence_identity" in item:
                withheld_evidence_identities.add(str(item["evidence_identity"]))
            reference = item.get("reference", item.get("numeric_reference"))
            if reference is not None:
                withheld_references.add(str(reference))
            continue
        retained.append(dict(item))
    if observed_withheld != set(CALIBRATED_NUMERIC_ROLES):
        raise TASK039E2ConfigurationError("direct-number calibrated roles differ")
    rendered["numeric_bindings"] = retained
    references = rendered.get("numeric_references")
    if references is not None:
        if not isinstance(references, Mapping):
            raise TASK039E2ConfigurationError("numeric reference map is malformed")
        rendered["numeric_references"] = {
            role: reference
            for role, reference in references.items()
            if role not in CALIBRATED_NUMERIC_ROLES
        }
    approved_evidence_identities = rendered.get("approved_evidence_identities")
    if approved_evidence_identities is not None and not isinstance(
        approved_evidence_identities, list
    ):
        raise TASK039E2ConfigurationError(
            "approved evidence identity list is malformed"
        )
    if approved_evidence_identities is not None:
        rendered["approved_evidence_identities"] = [
            identity
            for identity in approved_evidence_identities
            if identity not in withheld_evidence_identities
        ]
    text = _canonical_json(rendered)
    for role in CALIBRATED_NUMERIC_ROLES:
        if role in text:
            raise TASK039E2ConfigurationError("calibrated role leaked into direct-number input")
    for withheld in withheld_references | withheld_evidence_identities:
        if withheld in text:
            raise TASK039E2ConfigurationError(
                "calibrated evidence leaked into direct-number input"
            )
    return DIRECT_NUMBER_PROMPT_V1 + "\n\nDIRECT_NUMBER_INPUT_JSON\n" + text


def build_chat_completions_request_body_v1(
    *,
    model_visible_content: str,
    provider_schema: Mapping[str, Any],
    schema_name: str,
) -> dict[str, Any]:
    """Build a future stateless request body without transport or credentials."""

    if not isinstance(model_visible_content, str) or not model_visible_content:
        raise TASK039E2ConfigurationError("model-visible content is required")
    if not isinstance(schema_name, str) or not schema_name:
        raise TASK039E2ConfigurationError("structured schema name is required")
    if provider_schema.get("type") != "object" or provider_schema.get("additionalProperties") is not False:
        raise TASK039E2ConfigurationError("provider schema must be a closed object")
    sampling = _sampling_configuration()
    return {
        "model": sampling["model"],
        "messages": [{"role": "user", "content": model_visible_content}],
        "reasoning_effort": sampling["reasoning_effort"],
        "temperature": sampling["temperature"],
        "top_p": sampling["top_p"],
        "max_completion_tokens": sampling["max_completion_tokens"],
        "n": sampling["n"],
        "presence_penalty": sampling["presence_penalty"],
        "frequency_penalty": sampling["frequency_penalty"],
        "stream": sampling["stream"],
        "store": sampling["store"],
        "response_format": {
            "type": "json_schema",
            "json_schema": {
                "name": schema_name,
                "strict": True,
                "schema": thaw_json(provider_schema),
            },
        },
    }


@dataclass(frozen=True)
class ProviderProposalCoreV1:
    dsl_family: str
    relation_identity: str
    source: str
    source_step_direction: str
    target: str
    target_response_direction: str
    selected_delay_horizon_seconds: int
    source_threshold_reference: str
    source_stability_reference: str
    target_scale_reference: str
    window_constant_references: Mapping[str, str]
    variables: tuple[str, str]
    runtime_logic_family: str

    def __post_init__(self) -> None:
        document = self.to_dict()
        if set(document) != set(MAIN_PROVIDER_SCHEMA_V1["required"]):
            raise TASK039E2ConfigurationError("provider proposal core closure differs")
        for key in (
            "source_threshold_reference",
            "source_stability_reference",
            "target_scale_reference",
        ):
            _require_hash(document[key], key)
        if set(document["window_constant_references"]) != set(WINDOW_NUMERIC_ROLES):
            raise TASK039E2ConfigurationError("window reference roles differ")
        for role, value in document["window_constant_references"].items():
            _require_hash(value, role)
        if self.dsl_family != "canonical_delayed_response_rule_v1_candidate":
            raise TASK039E2ConfigurationError("DSL family differs")
        if self.runtime_logic_family != "missing_expected_delayed_response":
            raise TASK039E2ConfigurationError("runtime logic family differs")
        if self.source_step_direction not in {"step_up", "step_down"}:
            raise TASK039E2ConfigurationError("source direction differs")
        if self.target_response_direction not in {"increase", "decrease"}:
            raise TASK039E2ConfigurationError("target direction differs")
        if self.selected_delay_horizon_seconds not in {1, 5, 10, 30, 60}:
            raise TASK039E2ConfigurationError("selected horizon differs")

    def to_dict(self) -> dict[str, Any]:
        return {
            "dsl_family": self.dsl_family,
            "relation_identity": self.relation_identity,
            "source": self.source,
            "source_step_direction": self.source_step_direction,
            "target": self.target,
            "target_response_direction": self.target_response_direction,
            "selected_delay_horizon_seconds": self.selected_delay_horizon_seconds,
            "source_threshold_reference": self.source_threshold_reference,
            "source_stability_reference": self.source_stability_reference,
            "target_scale_reference": self.target_scale_reference,
            "window_constant_references": dict(self.window_constant_references),
            "variables": list(self.variables),
            "runtime_logic_family": self.runtime_logic_family,
        }

    @property
    def proposal_core_hash(self) -> str:
        return stable_hash_v1(self.to_dict())


@dataclass(frozen=True)
class RuleProposalEnvelopeV1:
    proposal_core: ProviderProposalCoreV1
    construction_arm: str
    local_call_number: int
    budget_policy_hash: str
    evidence_hash: str
    prompt_hash: str
    provider_model_receipt_hash: str | None
    execution_schedule_hash: str

    def __post_init__(self) -> None:
        if self.construction_arm not in {"T0", "T1", "T1-B", "T2"}:
            raise TASK039E2ConfigurationError("construction arm differs")
        if isinstance(self.local_call_number, bool) or self.local_call_number < 0:
            raise TASK039E2ConfigurationError("local call number differs")
        for name in (
            "budget_policy_hash",
            "evidence_hash",
            "prompt_hash",
            "execution_schedule_hash",
        ):
            _require_hash(getattr(self, name), name)
        if self.provider_model_receipt_hash is not None:
            _require_hash(self.provider_model_receipt_hash, "provider_model_receipt_hash")


def generate_synthetic_t0_core_v1(view: Mapping[str, Any]) -> ProviderProposalCoreV1:
    relation = str(view.get("relation_identity", ""))
    if not relation.startswith("SYNTHETIC_"):
        raise TASK039E2ConfigurationError("real T0 generation is prohibited in E2")
    refs = view.get("numeric_references")
    if not isinstance(refs, Mapping):
        raise TASK039E2ConfigurationError("synthetic T0 requires numeric references")
    windows = {role: str(refs[role]) for role in WINDOW_NUMERIC_ROLES}
    return ProviderProposalCoreV1(
        dsl_family="canonical_delayed_response_rule_v1_candidate",
        relation_identity=relation,
        source=str(view["source"]),
        source_step_direction=str(view["source_step_direction"]),
        target=str(view["target"]),
        target_response_direction=str(view["target_response_direction"]),
        selected_delay_horizon_seconds=int(view["selected_delay_horizon_seconds"]),
        source_threshold_reference=str(refs["source_step_threshold"]),
        source_stability_reference=str(refs["source_stability_tolerance"]),
        target_scale_reference=str(refs["target_noise_scale"]),
        window_constant_references=windows,
        variables=(str(view["source"]), str(view["target"])),
        runtime_logic_family="missing_expected_delayed_response",
    )


def validate_retrieval_request_v1(
    *,
    initial_evidence_identities: Sequence[str],
    requested_evidence_identities: Sequence[str],
    retrieval_actions_already_used: int,
) -> tuple[str, ...]:
    if retrieval_actions_already_used != 0:
        raise TASK039E2ConfigurationError("maximum one retrieval action")
    initial = tuple(initial_evidence_identities)
    requested = tuple(requested_evidence_identities)
    if not requested or not set(requested).issubset(set(initial)):
        raise TASK039E2ConfigurationError("retrieval cannot introduce new evidence")
    return requested


def classify_transport_outcome_v1(
    outcome: str, *, model_response_received: bool
) -> tuple[bool, bool]:
    retryable = {
        "connection_failure",
        "connection_reset",
        "timeout_before_response",
        "http_429",
        "http_5xx",
    }
    if model_response_received:
        return (True, False)
    if outcome in retryable:
        return (False, True)
    return (False, False)


def _provider_model_freeze() -> ProviderModelFreezeV1:
    return ProviderModelFreezeV1(
        {
            "provider": PROVIDER,
            "provider_name": PROVIDER_NAME,
            "api_endpoint_family": ENDPOINT_FAMILY,
            "api_base_url": API_BASE_URL,
            "api_endpoint": API_ENDPOINT,
            "exact_model_snapshot": EXACT_MODEL,
            "snapshot_locked": True,
            "model_alias_fallback_allowed": False,
            "automatic_upgrade_allowed": False,
            "alternative_model_fallback_allowed": False,
            "unavailable_snapshot_outcome": "block_task039e3",
            "transport_implementation": "python_stdlib_urllib_request_future_e3_only",
            "provider_sdk_dependency": False,
            "credential_environment_variable": CREDENTIAL_ENVIRONMENT_VARIABLE,
            "credential_accessed": False,
            "provider_contacted": False,
            "account_snapshot_availability": "not_probed",
        }
    )


def _model_capability_receipt() -> ModelCapabilityReceiptV1:
    urls = (
        "https://platform.openai.com/docs/models/gpt-5.4",
        "https://platform.openai.com/docs/guides/structured-outputs",
        "https://platform.openai.com/docs/api-reference/chat/create",
    )
    return ModelCapabilityReceiptV1(
        {
            "provider": PROVIDER_NAME,
            "model": EXACT_MODEL,
            "snapshot_locked": True,
            "chat_completions_supported": True,
            "structured_outputs_supported": True,
            "reasoning_effort_none_supported": True,
            "temperature_parameter_expected": True,
            "seed_capability": "deprecated_beta_not_relied_upon",
            "seed_reproducibility_relied_upon": False,
            "account_specific_model_availability": "not_probed",
            "provider_contacted": False,
            "credential_availability": "not_probed",
            "capability_basis": "static_official_document_reference_only",
            "review_date": "2026-08-11",
            "source_documents": [
                {
                    "url": url,
                    "url_identity_hash": _text_hash(url),
                    "identity_class": "url_identity_not_live_content_digest",
                }
                for url in urls
            ],
        }
    )


def _sampling_configuration() -> dict[str, Any]:
    value = {
        "model": EXACT_MODEL,
        "reasoning_effort": "none",
        "temperature": 0.7,
        "top_p": 1.0,
        "max_completion_tokens": 1024,
        "n": 1,
        "seed": None,
        "seed_used": False,
        "seed_determinism_claimed": False,
        "presence_penalty": 0,
        "frequency_penalty": 0,
        "stream": False,
        "store": False,
        "tools": [],
        "tool_choice": None,
    }
    validate_sampling_configuration_v1(value)
    return value


def _prompt_bundle() -> PromptTemplateBundleV1:
    return PromptTemplateBundleV1(
        {
            "main_initial_template_version": "MAIN_INITIAL_PROMPT_V1",
            "main_initial_template_path": "prompts/task039e2/main_initial_v1.txt",
            "main_initial_prompt_hash": _text_hash(MAIN_INITIAL_PROMPT_V1 + "\n"),
            "t2_followup_template_version": "T2_FOLLOWUP_PROMPT_V1",
            "t2_followup_template_path": "prompts/task039e2/t2_followup_v1.txt",
            "t2_followup_prompt_hash": _text_hash(T2_FOLLOWUP_PROMPT_V1 + "\n"),
            "direct_number_template_version": "DIRECT_NUMBER_PROMPT_V1",
            "direct_number_template_path": "prompts/task039e2/direct_number_v1.txt",
            "direct_number_prompt_hash": _text_hash(DIRECT_NUMBER_PROMPT_V1 + "\n"),
            "main_initial_shared_arms": ["T1", "T1-B-1", "T1-B-2", "T1-B-3", "T2-1"],
            "initial_model_visible_content_hash_method": "sha256_utf8_exact_rendered_scientific_content",
            "initial_content_equality_required": True,
            "arm_identity_model_visible": False,
            "call_index_model_visible": False,
            "t1b_stateless_independent_requests": True,
            "t1b_previous_proposal_visible": False,
            "t1b_previous_validity_visible": False,
            "t1b_all_three_calls_required": True,
            "t1b_selection_rule": "lowest_admissible_call_index_else_no_rule",
            "raw_rendered_prompt_policy": "raw_rendered_prompt_not_persisted",
        }
    )


def _main_output_policy() -> MainStructuredOutputPolicyV1:
    assert_generic_main_schema_v1(MAIN_PROVIDER_SCHEMA_V1)
    return MainStructuredOutputPolicyV1(
        {
            "provider_core_contract": "ProviderProposalCoreV1",
            "project_envelope_contract": "RuleProposalEnvelopeV1",
            "strict": True,
            "provider_schema_path": "schemas/v6/task039e2_provider_proposal_core_v1_schema.json",
            "provider_schema_hash": stable_hash_v1(MAIN_PROVIDER_SCHEMA_V1),
            "relation_specific_const_present": False,
            "relation_specific_singleton_enum_present": False,
            "model_generates_project_provenance": False,
            "arbitrary_numeric_literals_allowed": False,
            "semantic_binding_verified_by": "task039e0_validity_v2",
        }
    )


def _direct_output_policy() -> DirectNumberStructuredOutputPolicyV1:
    return DirectNumberStructuredOutputPolicyV1(
        {
            "strict": True,
            "provider_schema_path": "schemas/v6/task039e2_direct_number_response_v1_schema.json",
            "provider_schema_hash": stable_hash_v1(DIRECT_NUMBER_PROVIDER_SCHEMA_V1),
            "numeric_roles": list(CALIBRATED_NUMERIC_ROLES),
            "exact_numeric_field_count": 3,
            "finite_json_numbers_required": True,
            "relation_specific_calibrated_bounds_present": False,
            "validity_authority": False,
            "runtime_authority": False,
        }
    )


def _rendering_policy() -> ConstructionEvidenceRenderingPolicyV1:
    return ConstructionEvidenceRenderingPolicyV1(
        {
            "input_contract": "ConstructionInputViewV1",
            "approved_source": "task039e1_construction_evidence_cohort_and_private_resolver_future_e3",
            "model_visible_fields": [
                "public_relation_identity",
                "source",
                "target",
                "source_direction",
                "target_direction",
                "selected_horizon",
                "approved_calibrated_numeric_values",
                "approved_numeric_references",
                "approved_window_constants",
                "bounded_semantic_process_metadata",
            ],
            "prohibited_fields": [
                "raw_hai",
                "event_timestamps",
                "labels",
                "attacks",
                "test_data",
                "utility_outcomes",
                "candidate_method_metrics",
                "construction_arm",
                "call_index",
            ],
            "main_calibrated_values_visible": True,
            "main_proposal_outputs_references": True,
            "raw_rendered_prompt_policy": "raw_rendered_prompt_not_persisted",
            "rendered_prompt_hash_recorded": True,
            "construction_input_view_hash_recorded": True,
            "private_evidence_ledger_accessed_in_e2": False,
            "hai_accessed": False,
        }
    )


def _retrieval_policy() -> T2RetrievalCorpusPolicyV1:
    return T2RetrievalCorpusPolicyV1(
        {
            "underlying_corpus": "same_approved_e1_construction_evidence_as_initial_view",
            "retrieval_semantics": "targeted_re_presentation_of_existing_evidence",
            "allowed_slices": [
                "approved_numeric_provenance_slice",
                "confirmed_relation_binding_slice",
                "approved_semantic_process_metadata_slice",
                "preregistered_window_constant_slice",
            ],
            "prohibited_sources": [
                "new_d1_d2_statistics",
                "raw_hai",
                "labels",
                "attacks",
                "test",
                "train4",
                "utility_outcomes",
                "meta_stat_gdn_results",
            ],
            "new_scientific_evidence_allowed": False,
            "maximum_retrieval_actions_per_relation": 1,
            "provider_generation_calls_consumed_by_retrieval": 0,
            "subsequent_revision_consumes_generation_call": True,
            "controller_hash": E0_CONTROLLER_HASH,
            "controller_is_project_owned": True,
            "model_selects_controller_action": False,
        }
    )


def _t0_policy() -> T0TemplatePolicyV1:
    specification = {
        "dsl_family": "canonical_delayed_response_rule_v1_candidate",
        "runtime_logic_family": "missing_expected_delayed_response",
        "identity_fields": [
            "relation_identity",
            "source",
            "source_step_direction",
            "target",
            "target_response_direction",
            "selected_delay_horizon_seconds",
        ],
        "reference_fields": [
            "source_threshold_reference",
            "source_stability_reference",
            "target_scale_reference",
            "window_constant_references",
        ],
        "numeric_literals": "prohibited",
    }
    return T0TemplatePolicyV1(
        {
            "template_version": "T0_TEMPLATE_V1",
            "template_specification": specification,
            "template_hash": stable_hash_v1(specification),
            "proposal_core_contract": "ProviderProposalCoreV1",
            "proposal_envelope_contract": "RuleProposalEnvelopeV1",
            "uses_approved_e1_references": True,
            "llm_used": False,
            "search_used": False,
            "fallback_used": False,
            "synthetic_tests_only_in_e2": True,
            "real_relation_generated": False,
        }
    )


def _schedule(relations: Sequence[Mapping[str, Any]]) -> ConstructionExecutionScheduleV1:
    identities = [str(item["relation_identity"]) for item in relations]
    if len(identities) != RELATION_COUNT or len(set(identities)) != RELATION_COUNT:
        raise TASK039E2ConfigurationError("exact 42-relation schedule required")
    identity_order_hash = stable_hash_v1({"relation_identities": identities})
    return ConstructionExecutionScheduleV1(
        {
            "e1_cohort_hash": E1_CONSTRUCTION_EVIDENCE_COHORT_HASH,
            "relation_count": RELATION_COUNT,
            "relation_order_policy": "exact_e1_cohort_serialization_order",
            "relation_identities": identities,
            "relation_identity_order_hash": identity_order_hash,
            "serialization_order_is_scientific_rank": False,
            "per_relation_sequence": [
                "T0_LOCAL_PROPOSAL",
                "T1_CALL_1",
                "T1B_CALL_1",
                "T1B_CALL_2",
                "T1B_CALL_3",
                "T2_CALL_1",
                "T2_CALL_2_IF_CONTROLLER_REQUIRES",
                "T2_CALL_3_IF_CONTROLLER_REQUIRES",
                "T1_DIRECT_NUMBER_CALL_1",
            ],
            "t0_provider_calls": 0,
            "t1_maximum_scientific_calls": 42,
            "t1b_fixed_scientific_calls": 126,
            "t2_maximum_scientific_calls": 126,
            "direct_number_scientific_calls": 42,
            "maximum_scientific_calls": MAXIMUM_SCIENTIFIC_CALLS,
            "scientific_concurrency": SCIENTIFIC_CONCURRENCY,
            "result_dependent_ordering": False,
            "cross_arm_output_visibility": False,
            "t2_own_validity_feedback_only": True,
            "capability_probe_count": 1,
            "capability_probe_fixture": "SYNTHETIC_CAPABILITY_CHECK",
            "capability_probe_scientific_call": False,
            "capability_probe_may_change_frozen_configuration": False,
            "capability_probe_unsupported_outcome": "block_task039e3",
        }
    )


def _transport_policy() -> TransportRetryPolicyV1:
    return TransportRetryPolicyV1(
        {
            "maximum_transport_retries_per_request": 2,
            "scientific_generation_retries": 0,
            "retryable_no_response_outcomes": [
                "connection_failure",
                "connection_reset",
                "timeout_before_response",
                "http_429",
                "http_5xx",
            ],
            "non_retryable_outcomes": [
                "http_400",
                "http_401",
                "http_403",
                "provider_refusal",
                "schema_invalid_response",
                "malformed_scientific_output",
                "verifier_rejection",
                "low_quality_proposal",
            ],
            "fixed_retry_delays_seconds": [2, 4],
            "retry_after_429_policy": "valid_retry_after_overrides_corresponding_fixed_delay",
            "retry_after_validity_policy": "provider_header_must_parse_as_standard_retry_after",
            "response_failures_consume_scientific_call": True,
            "retry_exhaustion_outcome": "abort_full_scientific_run",
            "relation_skip_allowed": False,
        }
    )


def _custody_policy() -> ProviderResponseCustodyPolicyV1:
    return ProviderResponseCustodyPolicyV1(
        {
            "required_receipt_fields": [
                "request_sequence_number",
                "relation_binding_hash",
                "local_arm",
                "local_call_number",
                "provider_response_id",
                "returned_model_id",
                "system_fingerprint_if_returned",
                "finish_reason",
                "usage_tokens",
                "transport_retry_count",
                "structured_parse_status",
                "provider_refusal_state",
                "proposal_core_hash",
            ],
            "structured_parsed_response_is_scientific_record": True,
            "raw_model_output_policy": "not_committed_structured_parsed_response_retained",
            "prohibited_stored_fields": [
                "api_key",
                "authorization_header",
                "chain_of_thought",
                "raw_hai",
            ],
            "provider_refusal_consumes_scientific_call": True,
            "incomplete_output_consumes_scientific_call": True,
            "schema_parse_failure_consumes_scientific_call": True,
            "verifier_rejection_consumes_scientific_call": True,
            "provider_refusal_repairability": "non_repairable",
            "provider_refusal_t2_outcome": "no_rule_and_stop",
            "received_failure_is_transport_failure": False,
            "arm_response_handling": {
                "T1": "invalid_incomplete_or_refusal_yields_no_rule",
                "T1-B": "all_three_calls_still_execute_then_lowest_admissible_else_no_rule",
                "T2": "refusal_yields_no_rule_and_stop_other_rejections_use_frozen_controller_when_structurally_possible",
            },
        }
    )


def _direct_role_policy() -> DirectNumberRolePolicyV1:
    return DirectNumberRolePolicyV1(
        {
            "arm": "T1-DIRECT-NUMBER",
            "designated_comparator": "T1",
            "calls_per_relation": 1,
            "numeric_roles": list(CALIBRATED_NUMERIC_ROLES),
            "withheld_values": list(CALIBRATED_NUMERIC_ROLES),
            "withheld_references": list(CALIBRATED_NUMERIC_ROLES),
            "provided_context": [
                "relation_identity",
                "source_target_semantics",
                "source_target_directions",
                "selected_horizon",
                *WINDOW_NUMERIC_ROLES,
            ],
            "retrieval_allowed": False,
            "normalized_absolute_error_formula": "abs(proposed-approved)/max(abs(approved),1e-12)",
            "additional_metrics": [
                "missing_number_rate",
                "nonfinite_rate_where_representable",
                "domain_sign_violation_rate",
            ],
            "label_free": True,
            "validity_authority": False,
            "runtime_authority": False,
        }
    )


def _read_public_json(root: Path, relative: str) -> dict[str, Any]:
    path = (root / relative).resolve()
    if root.resolve() not in path.parents:
        raise TASK039E2ConfigurationError("public path escapes repository")
    document = json.loads(path.read_text(encoding="utf-8"))
    verify_self_hash_v1(document)
    return document


def _validate_public_inputs(root: Path) -> tuple[dict[str, Any], list[Mapping[str, Any]]]:
    authorization = _read_public_json(root, "docs/task_reports/TASK-039E2_AUTHORIZATION.json")
    if authorization["artifact_hash"] != E2_AUTHORIZATION_HASH:
        raise TASK039E2ConfigurationError("E2 authorization hash differs")
    if authorization["status"] != "authorized_task039e2_configuration_freeze_only":
        raise TASK039E2ConfigurationError("E2 authorization status differs")
    for field in (
        "provider_model_call_authorized",
        "real_t0_generation_authorized",
        "real_t1_t1b_t2_generation_authorized",
        "direct_number_execution_authorized",
        "rule_v2_authorized",
        "detector_runtime_authorized",
        "hai_test_labels_attacks_authorized",
    ):
        if authorization[field] is not False:
            raise TASK039E2ConfigurationError("E2 authority boundary differs")
    e0 = _read_public_json(root, "docs/task_reports/TASK-039E0_PROTOCOL_BUNDLE.json")
    result = _read_public_json(root, "docs/task_reports/TASK-039E1_MATERIALIZATION_RESULT.json")
    cohort = _read_public_json(root, "docs/task_reports/TASK-039E1_CONSTRUCTION_EVIDENCE_COHORT.json")
    if e0["artifact_hash"] != E0_PROTOCOL_BUNDLE_HASH:
        raise TASK039E2ConfigurationError("E0 protocol hash differs")
    if result["artifact_hash"] != E1_MATERIALIZATION_RESULT_HASH:
        raise TASK039E2ConfigurationError("E1 result hash differs")
    if cohort["artifact_hash"] != E1_CONSTRUCTION_EVIDENCE_COHORT_HASH:
        raise TASK039E2ConfigurationError("E1 cohort hash differs")
    if result["private_ledger_hash"] != E1_PRIVATE_LEDGER_HASH:
        raise TASK039E2ConfigurationError("E1 private-ledger binding differs")
    relations = cohort["confirmed_relation_primitives"]
    if len(relations) != RELATION_COUNT:
        raise TASK039E2ConfigurationError("E1 relation count differs")
    return authorization, relations


def build_task039e2_artifacts_v1(
    repository_root: str | Path,
) -> dict[str, _ClosedArtifactV1]:
    """Build the authoritative E2 freeze from committed public inputs only."""

    root = Path(repository_root).resolve()
    _authorization, relations = _validate_public_inputs(root)

    provider_freeze = _provider_model_freeze()
    capability = _model_capability_receipt()
    prompts = _prompt_bundle()
    main_output = _main_output_policy()
    direct_output = _direct_output_policy()
    rendering = _rendering_policy()
    retrieval = _retrieval_policy()
    t0 = _t0_policy()
    schedule = _schedule(relations)
    transport = _transport_policy()
    custody = _custody_policy()
    direct_roles = _direct_role_policy()
    sampling = _sampling_configuration()
    sampling_hash = stable_hash_v1(sampling)
    configuration = ConstructionExecutionConfigurationV1(
        {
            "provider_model_freeze_hash": provider_freeze.artifact_hash,
            "model_capability_receipt_hash": capability.artifact_hash,
            "shared_llm_arms": ["T1", "T1-B", "T2", "T1-DIRECT-NUMBER"],
            "sampling_configuration": sampling,
            "sampling_configuration_hash": sampling_hash,
            "reasoning_methodological_rationale": [
                "external_verifier_feedback_is_the_agentic_treatment",
                "minimize_hidden_internal_reasoning_as_an_uncontrolled_treatment_dimension",
            ],
            "stateless_requests": True,
            "reasoning_persistence": False,
            "previous_response_id_used": False,
            "provider_managed_conversational_state": False,
            "prompt_template_bundle_hash": prompts.artifact_hash,
            "main_structured_output_policy_hash": main_output.artifact_hash,
            "direct_number_structured_output_policy_hash": direct_output.artifact_hash,
            "rendering_policy_hash": rendering.artifact_hash,
            "retrieval_policy_hash": retrieval.artifact_hash,
            "t0_template_policy_hash": t0.artifact_hash,
            "schedule_hash": schedule.artifact_hash,
            "transport_retry_policy_hash": transport.artifact_hash,
            "provider_response_custody_policy_hash": custody.artifact_hash,
            "direct_number_role_policy_hash": direct_roles.artifact_hash,
            "provider_contacted": False,
            "credential_checked": False,
            "capability_probe_executed": False,
            "llm_called": False,
            "execution_authorized": False,
        }
    )
    components = {
        "provider_model_freeze": provider_freeze.artifact_hash,
        "model_capability_receipt": capability.artifact_hash,
        "execution_configuration": configuration.artifact_hash,
        "prompt_template_bundle": prompts.artifact_hash,
        "main_structured_output_policy": main_output.artifact_hash,
        "direct_number_structured_output_policy": direct_output.artifact_hash,
        "rendering_policy": rendering.artifact_hash,
        "retrieval_policy": retrieval.artifact_hash,
        "t0_template_policy": t0.artifact_hash,
        "execution_schedule": schedule.artifact_hash,
        "transport_retry_policy": transport.artifact_hash,
        "provider_response_custody_policy": custody.artifact_hash,
        "direct_number_role_policy": direct_roles.artifact_hash,
    }
    bundle = TASK039E2ProtocolBundleV1(
        {
            "task_id": TASK_ID,
            "status": STATUS,
            "next_task": NEXT_TASK,
            "authoritative_main": AUTHORITATIVE_MAIN,
            "e2_prep_commit": E2_PREP_COMMIT,
            "e2_authorization_hash": E2_AUTHORIZATION_HASH,
            "e0_protocol_bundle_hash": E0_PROTOCOL_BUNDLE_HASH,
            "e1_materialization_result_hash": E1_MATERIALIZATION_RESULT_HASH,
            "e1_construction_evidence_cohort_hash": E1_CONSTRUCTION_EVIDENCE_COHORT_HASH,
            "e1_private_ledger_hash": E1_PRIVATE_LEDGER_HASH,
            "relation_count": RELATION_COUNT,
            "numeric_binding_count": NUMERIC_BINDING_COUNT,
            "component_hashes": components,
            "provider_contacted": False,
            "credential_checked": False,
            "capability_probe_executed": False,
            "llm_called": False,
            "real_t0_generated": False,
            "t1_generated": False,
            "t1b_generated": False,
            "t2_generated": False,
            "direct_number_executed": False,
            "e3_authorization_created": False,
            "rule_v2_authorized": False,
            "runtime_authority": False,
            "e1_private_evidence_accessed": False,
            "hai_accessed": False,
        }
    )
    return {
        "provider_model_freeze": provider_freeze,
        "model_capability_receipt": capability,
        "execution_configuration": configuration,
        "prompt_template_bundle": prompts,
        "main_structured_output_policy": main_output,
        "direct_number_structured_output_policy": direct_output,
        "rendering_policy": rendering,
        "retrieval_policy": retrieval,
        "t0_template_policy": t0,
        "execution_schedule": schedule,
        "transport_retry_policy": transport,
        "provider_response_custody_policy": custody,
        "direct_number_role_policy": direct_roles,
        "protocol_bundle": bundle,
    }


def _infer_schema(value: Any, field_name: str | None = None) -> dict[str, Any]:
    if isinstance(value, Mapping):
        properties = {key: _infer_schema(item, key) for key, item in value.items()}
        return {
            "type": "object",
            "additionalProperties": False,
            "required": list(value.keys()),
            "properties": properties,
        }
    if isinstance(value, list):
        item_schema = _infer_schema(value[0]) if value else {}
        return {"type": "array", "items": item_schema}
    if value is None:
        return {"type": "null"}
    if type(value) is bool:
        return {"type": "boolean"}
    if type(value) is int:
        return {"type": "integer"}
    if type(value) is float:
        if not math.isfinite(value):
            raise TASK039E2ConfigurationError("schema example is nonfinite")
        return {"type": "number"}
    if isinstance(value, str):
        result: dict[str, Any] = {"type": "string"}
        if field_name and (field_name.endswith("_hash") or field_name.endswith("_reference")):
            result["pattern"] = "^[a-f0-9]{64}$"
        return result
    raise TASK039E2ConfigurationError("unsupported schema example type")


def schema_documents_v1(
    artifacts: Mapping[str, _ClosedArtifactV1],
) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for artifact in artifacts.values():
        document = artifact.to_dict()
        schema = _infer_schema(document)
        schema.update(
            {
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "$id": f"https://paperworks.local/schemas/v6/{artifact.ARTIFACT_TYPE}.schema.json",
                "title": artifact.ARTIFACT_TYPE,
            }
        )
        schema["properties"]["schema_version"] = {
            "type": "string",
            "const": V6_FOUNDATION_SCHEMA_VERSION,
        }
        schema["properties"]["artifact_type"] = {
            "type": "string",
            "const": artifact.ARTIFACT_TYPE,
        }
        schema["properties"]["artifact_hash"] = {
            "type": "string",
            "pattern": "^[a-f0-9]{64}$",
        }
        result[artifact.ARTIFACT_TYPE] = schema
    return result


PUBLIC_REPORT_FILES = {
    "provider_model_freeze": "TASK-039E2_PROVIDER_MODEL_FREEZE.json",
    "model_capability_receipt": "TASK-039E2_MODEL_CAPABILITY_RECEIPT.json",
    "execution_configuration": "TASK-039E2_EXECUTION_CONFIGURATION.json",
    "prompt_template_bundle": "TASK-039E2_PROMPT_BUNDLE.json",
    "main_structured_output_policy": "TASK-039E2_OUTPUT_SCHEMA_POLICY.json",
    "direct_number_structured_output_policy": "TASK-039E2_DIRECT_NUMBER_OUTPUT_SCHEMA_POLICY.json",
    "rendering_policy": "TASK-039E2_RENDERING_POLICY.json",
    "retrieval_policy": "TASK-039E2_RETRIEVAL_POLICY.json",
    "t0_template_policy": "TASK-039E2_T0_TEMPLATE_POLICY.json",
    "execution_schedule": "TASK-039E2_EXECUTION_SCHEDULE.json",
    "transport_retry_policy": "TASK-039E2_TRANSPORT_RETRY_POLICY.json",
    "provider_response_custody_policy": "TASK-039E2_PROVIDER_RESPONSE_CUSTODY_POLICY.json",
    "direct_number_role_policy": "TASK-039E2_DIRECT_NUMBER_ROLE_POLICY.json",
    "protocol_bundle": "TASK-039E2_PROTOCOL_BUNDLE.json",
}


__all__ = [
    "ARTIFACT_CLASSES",
    "API_ENDPOINT",
    "CALIBRATED_NUMERIC_ROLES",
    "ConstructionEvidenceRenderingPolicyV1",
    "ConstructionExecutionConfigurationV1",
    "ConstructionExecutionScheduleV1",
    "DIRECT_NUMBER_PROMPT_V1",
    "DIRECT_NUMBER_PROVIDER_SCHEMA_V1",
    "DirectNumberRolePolicyV1",
    "DirectNumberStructuredOutputPolicyV1",
    "EXACT_MODEL",
    "MAIN_INITIAL_PROMPT_V1",
    "MAIN_PROVIDER_SCHEMA_V1",
    "MAXIMUM_SCIENTIFIC_CALLS",
    "MainStructuredOutputPolicyV1",
    "ModelCapabilityReceiptV1",
    "NEXT_TASK",
    "PROVIDER",
    "PUBLIC_REPORT_FILES",
    "PromptTemplateBundleV1",
    "ProviderModelFreezeV1",
    "ProviderProposalCoreV1",
    "ProviderResponseCustodyPolicyV1",
    "RELATION_COUNT",
    "RuleProposalEnvelopeV1",
    "SCIENTIFIC_CONCURRENCY",
    "STATUS",
    "T0TemplatePolicyV1",
    "T2RetrievalCorpusPolicyV1",
    "T2_FOLLOWUP_PROMPT_V1",
    "TASK039E2ConfigurationError",
    "TASK039E2ProtocolBundleV1",
    "TransportRetryPolicyV1",
    "assert_generic_main_schema_v1",
    "build_chat_completions_request_body_v1",
    "build_task039e2_artifacts_v1",
    "classify_transport_outcome_v1",
    "generate_synthetic_t0_core_v1",
    "initial_model_visible_content_hash_v1",
    "render_direct_number_model_content_v1",
    "render_main_initial_model_content_v1",
    "render_t2_followup_model_content_v1",
    "schema_documents_v1",
    "validate_retrieval_request_v1",
    "validate_sampling_configuration_v1",
    "verify_self_hash_v1",
]
