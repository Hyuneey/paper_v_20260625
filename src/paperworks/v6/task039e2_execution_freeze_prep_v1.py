"""Provider-neutral synthetic preparation for the TASK-039E2 execution freeze.

This module defines pure contracts and deterministic renderers.  It performs
no provider discovery or call, reads no E1 artifact, generates no real T0
proposal, and grants no rule or runtime authority.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any, Mapping, Sequence

from paperworks.v6.common import (
    V6_FOUNDATION_SCHEMA_VERSION,
    freeze_json,
    require_identifier,
    require_sha256,
    stable_hash_v1,
    thaw_json,
)
from paperworks.v6.outcomes_v1 import ConstructionArmV1
from paperworks.v6.task039e0_rule_construction_prep_v1 import (
    ApprovedNumericEvidenceBundleV1,
    ConfirmedRelationPrimitiveV1,
    FROZEN_ARM_PROTOCOLS,
    MAIN_NUMERIC_ORIGIN,
    PROPOSAL_ARTIFACT_TYPE,
    PROPOSAL_DSL_FAMILY,
    ProposalConstructionProvenanceV1,
    canonical_proposal_hash_v1,
    prepare_rule_proposal_envelope_v1,
)


TASK_ID = "TASK-039E2-PREP"
BASE_COMMIT = "20ca2e6f561ce0cdfaf822198f7b64d8e143215c"
BRANCH = "task-039e2-execution-freeze-prep"
PREPARATION_STATUS = "passed_task039e2_execution_freeze_preparation"

EXPECTED_RELATION_COUNT = 42
T1_CALLS_PER_RELATION = 1
T1B_CALLS_PER_RELATION = 3
T2_MAXIMUM_CALLS_PER_RELATION = 3
DIRECT_NUMBER_CALLS_PER_RELATION = 1
MAXIMUM_RETRIEVAL_ACTIONS = 1
EXPECTED_MAXIMUM_SCIENTIFIC_CALLS = EXPECTED_RELATION_COUNT * (
    T1_CALLS_PER_RELATION
    + T1B_CALLS_PER_RELATION
    + T2_MAXIMUM_CALLS_PER_RELATION
    + DIRECT_NUMBER_CALLS_PER_RELATION
)

REAL_E1_RESULT_CONSUMED = False
REAL_E1_PRIVATE_EVIDENCE_ACCESSED = False
REAL_CONFIRMED_IDENTITIES_CONSUMED = False
PROVIDER_SELECTED = False
MODEL_SELECTED = False
PROVIDER_CONTACTED = False
LLM_CALLED = False
REAL_T0_GENERATED = False
RULE_V2_AUTHORIZED = False
RUNTIME_AUTHORITY_GRANTED = False
E2_AUTHORIZATION_CREATED = False

SYNTHETIC_PREFIX = "SYNTHETIC_"
REQUIRED_NUMERIC_ROLES = (
    "source_step_threshold",
    "source_stability_tolerance",
    "target_noise_scale",
    "selected_delay_horizon",
    "source_pre_window",
    "source_post_window",
    "minimum_source_stability_fraction",
    "source_refractory",
    "cross_source_isolation_radius",
    "target_baseline_window",
    "target_response_window",
)
CALIBRATED_NUMERIC_ROLES = REQUIRED_NUMERIC_ROLES[:3]
WINDOW_NUMERIC_ROLES = REQUIRED_NUMERIC_ROLES[4:]
INITIAL_PROMPT_FAMILIES = ("T1", "T1-B", "T2_CALL_1")
ALL_PROMPT_FAMILIES = (
    "T1",
    "T1-B",
    "T2_CALL_1",
    "T2_FOLLOWUP",
    "T1-DIRECT-NUMBER",
)
DETERMINISTIC_ARM_ORDER = (
    "T0",
    "T1",
    "T1-B",
    "T2",
    "T1-DIRECT-NUMBER",
)
TRANSPORT_RETRY_REASONS = (
    "connection_failure",
    "provider_5xx",
    "timeout_before_model_response",
    "preregistered_non_scientific_transport_failure",
)
SCIENTIFIC_RESPONSE_FAILURES = (
    "malformed_response",
    "invalid_response",
    "low_quality_response",
    "verifier_rejected_response",
)
PROHIBITED_INPUT_KEYS = frozenset(
    {
        "raw_hai",
        "hai_rows",
        "labels",
        "attacks",
        "test_data",
        "test_outcomes",
        "utility_results",
        "utility_outcomes",
        "candidate_method_performance",
        "candidate_method_results",
    }
)
ALLOWED_T2_AFFECTED_FIELDS = frozenset(
    {
        "relation_binding_hash",
        "source",
        "source_step_direction",
        "target",
        "target_response_direction",
        "selected_delay_horizon_seconds",
        "source_threshold_reference",
        "source_stability_reference",
        "target_scale_reference",
        "preregistered_window_constant_references",
        "variables",
        "runtime_logic",
        "construction_provenance_hash",
    }
)


class TASK039E2PreparationError(ValueError):
    """Raised when the preparation boundary or frozen protocol is violated."""


def _require_false(value: bool, field_name: str) -> None:
    if value is not False:
        raise TASK039E2PreparationError(f"{field_name} must remain false")


def _require_true(value: bool, field_name: str) -> None:
    if value is not True:
        raise TASK039E2PreparationError(f"{field_name} must be true")


def _require_positive_integer(value: int, field_name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise TASK039E2PreparationError(f"{field_name} must be a positive integer")


def _require_nonnegative_integer(value: int, field_name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise TASK039E2PreparationError(
            f"{field_name} must be a non-negative integer"
        )


def _require_finite(value: int | float, field_name: str) -> float:
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(float(value))
    ):
        raise TASK039E2PreparationError(f"{field_name} must be finite")
    return float(value)


def _require_synthetic_identifier(value: str, field_name: str) -> None:
    require_identifier(value, field_name)
    if not value.startswith(SYNTHETIC_PREFIX):
        raise TASK039E2PreparationError(
            f"{field_name} must use a SYNTHETIC_ preparation identity"
        )


def _with_hash(content: Mapping[str, Any]) -> dict[str, Any]:
    payload = dict(content)
    payload["artifact_hash"] = stable_hash_v1(content)
    return payload


def assert_private_input_boundary_v1(value: Any, path: str = "$input") -> None:
    """Reject raw data, labels, utility, and candidate-performance content."""

    if isinstance(value, Mapping):
        for key, item in value.items():
            normalized = str(key).lower()
            if normalized in PROHIBITED_INPUT_KEYS:
                raise TASK039E2PreparationError(
                    f"prohibited construction input at {path}.{key}"
                )
            assert_private_input_boundary_v1(item, f"{path}.{key}")
    elif isinstance(value, (tuple, list)):
        for index, item in enumerate(value):
            assert_private_input_boundary_v1(item, f"{path}[{index}]")


@dataclass(frozen=True)
class ModelCapabilityReceiptV1:
    provider_identifier: str
    model_identifier: str
    stable_explicit_model_version: bool
    structured_schema_output_supported: bool
    temperature_control_supported: bool
    deterministic_decoding_supported: bool
    exposed_seed_control_supported: bool
    stateless_independent_calls_supported: bool
    maximum_input_tokens: int
    maximum_output_tokens: int
    required_evidence_envelope_tokens: int
    required_output_tokens: int
    unsupported_capabilities: tuple[str, ...]
    capability_evidence_reference: str
    preparation_only: bool = True
    real_provider_selected: bool = False

    def __post_init__(self) -> None:
        _require_synthetic_identifier(self.provider_identifier, "provider_identifier")
        _require_synthetic_identifier(self.model_identifier, "model_identifier")
        for field_name in (
            "maximum_input_tokens",
            "maximum_output_tokens",
            "required_evidence_envelope_tokens",
            "required_output_tokens",
        ):
            _require_positive_integer(getattr(self, field_name), field_name)
        require_sha256(
            self.capability_evidence_reference, "capability_evidence_reference"
        )
        if len(set(self.unsupported_capabilities)) != len(
            self.unsupported_capabilities
        ):
            raise TASK039E2PreparationError(
                "unsupported capabilities must be unique"
            )
        known = {
            "stable_explicit_model_version",
            "structured_schema_output",
            "temperature_control",
            "deterministic_or_seed_control",
            "stateless_independent_calls",
            "sufficient_input_tokens",
            "sufficient_output_tokens",
        }
        if not set(self.unsupported_capabilities).issubset(known):
            raise TASK039E2PreparationError("unknown unsupported capability")
        missing = set(self.missing_required_capabilities())
        if missing != set(self.unsupported_capabilities):
            raise TASK039E2PreparationError(
                "unsupported capabilities must be explicitly and exactly disclosed"
            )
        _require_true(self.preparation_only, "preparation_only")
        _require_false(self.real_provider_selected, "real_provider_selected")

    def missing_required_capabilities(self) -> tuple[str, ...]:
        missing: list[str] = []
        if not self.stable_explicit_model_version:
            missing.append("stable_explicit_model_version")
        if not self.structured_schema_output_supported:
            missing.append("structured_schema_output")
        if not self.temperature_control_supported:
            missing.append("temperature_control")
        if not (
            self.deterministic_decoding_supported
            or self.exposed_seed_control_supported
        ):
            missing.append("deterministic_or_seed_control")
        if not self.stateless_independent_calls_supported:
            missing.append("stateless_independent_calls")
        if self.maximum_input_tokens < self.required_evidence_envelope_tokens:
            missing.append("sufficient_input_tokens")
        if self.maximum_output_tokens < self.required_output_tokens:
            missing.append("sufficient_output_tokens")
        return tuple(missing)

    def assert_execution_capable(self) -> None:
        if self.missing_required_capabilities():
            raise TASK039E2PreparationError(
                "provider capability missing: "
                + ",".join(self.missing_required_capabilities())
            )

    def _content_dict(self) -> dict[str, Any]:
        return {
            "schema_version": V6_FOUNDATION_SCHEMA_VERSION,
            "artifact_type": "model_capability_receipt_v1",
            "provider_identifier": self.provider_identifier,
            "model_identifier": self.model_identifier,
            "stable_explicit_model_version": self.stable_explicit_model_version,
            "structured_schema_output_supported": self.structured_schema_output_supported,
            "temperature_control_supported": self.temperature_control_supported,
            "deterministic_decoding_supported": self.deterministic_decoding_supported,
            "exposed_seed_control_supported": self.exposed_seed_control_supported,
            "stateless_independent_calls_supported": self.stateless_independent_calls_supported,
            "maximum_input_tokens": self.maximum_input_tokens,
            "maximum_output_tokens": self.maximum_output_tokens,
            "required_evidence_envelope_tokens": self.required_evidence_envelope_tokens,
            "required_output_tokens": self.required_output_tokens,
            "unsupported_capabilities": list(self.unsupported_capabilities),
            "capability_evidence_reference": self.capability_evidence_reference,
            "preparation_only": self.preparation_only,
            "real_provider_selected": self.real_provider_selected,
        }

    @property
    def artifact_hash(self) -> str:
        return stable_hash_v1(self._content_dict())

    def to_dict(self) -> dict[str, Any]:
        return _with_hash(self._content_dict())


@dataclass(frozen=True)
class ConstructionExecutionConfigurationV1:
    provider_identifier: str
    exact_model_identifier: str
    model_capability_receipt_hash: str
    prompt_template_version: str
    prompt_template_hash: str
    structured_output_schema_hash: str
    temperature: float
    top_p: float | None
    maximum_output_tokens: int
    seed_value: int | None
    seed_policy: str
    stateless_calls_required: bool
    call_timeout_seconds: int
    transport_retry_policy_hash: str
    scientific_generation_budget_hash: str
    execution_schedule_hash: str
    construction_evidence_rendering_policy_hash: str
    preparation_only: bool = True
    provider_selected: bool = False
    model_selected: bool = False
    provider_contacted: bool = False
    execution_authorized: bool = False

    def __post_init__(self) -> None:
        _require_synthetic_identifier(self.provider_identifier, "provider_identifier")
        _require_synthetic_identifier(
            self.exact_model_identifier, "exact_model_identifier"
        )
        require_identifier(self.prompt_template_version, "prompt_template_version")
        for field_name in (
            "model_capability_receipt_hash",
            "prompt_template_hash",
            "structured_output_schema_hash",
            "transport_retry_policy_hash",
            "scientific_generation_budget_hash",
            "execution_schedule_hash",
            "construction_evidence_rendering_policy_hash",
        ):
            require_sha256(getattr(self, field_name), field_name)
        temperature = _require_finite(self.temperature, "temperature")
        if temperature < 0.0 or temperature > 2.0:
            raise TASK039E2PreparationError("temperature is outside the closed range")
        if self.top_p is not None:
            top_p = _require_finite(self.top_p, "top_p")
            if top_p <= 0.0 or top_p > 1.0:
                raise TASK039E2PreparationError("top_p is outside the closed range")
        _require_positive_integer(self.maximum_output_tokens, "maximum_output_tokens")
        if self.seed_value is not None and (
            isinstance(self.seed_value, bool) or not isinstance(self.seed_value, int)
        ):
            raise TASK039E2PreparationError("seed_value must be an integer or null")
        if self.seed_policy not in {
            "provider_exposed_fixed_seed",
            "deterministic_decoding_without_seed",
            "provider_seed_not_exposed_disclosed",
        }:
            raise TASK039E2PreparationError("seed policy is invalid")
        if self.seed_policy == "provider_exposed_fixed_seed" and self.seed_value is None:
            raise TASK039E2PreparationError("fixed seed policy requires a seed")
        if self.seed_policy != "provider_exposed_fixed_seed" and self.seed_value is not None:
            raise TASK039E2PreparationError("unexposed seed policy cannot carry a seed")
        _require_true(self.stateless_calls_required, "stateless_calls_required")
        _require_positive_integer(self.call_timeout_seconds, "call_timeout_seconds")
        _require_true(self.preparation_only, "preparation_only")
        for field_name in (
            "provider_selected",
            "model_selected",
            "provider_contacted",
            "execution_authorized",
        ):
            _require_false(getattr(self, field_name), field_name)

    def assert_capability_receipt(self, receipt: ModelCapabilityReceiptV1) -> None:
        if (
            receipt.artifact_hash != self.model_capability_receipt_hash
            or receipt.provider_identifier != self.provider_identifier
            or receipt.model_identifier != self.exact_model_identifier
        ):
            raise TASK039E2PreparationError(
                "configuration does not bind the capability receipt"
            )
        if self.maximum_output_tokens > receipt.maximum_output_tokens:
            raise TASK039E2PreparationError("configured output tokens exceed capability")
        if (
            self.seed_policy == "provider_exposed_fixed_seed"
            and not receipt.exposed_seed_control_supported
        ):
            raise TASK039E2PreparationError(
                "fixed seed configuration exceeds provider capability"
            )
        if (
            self.seed_policy == "deterministic_decoding_without_seed"
            and not receipt.deterministic_decoding_supported
        ):
            raise TASK039E2PreparationError(
                "deterministic decoding configuration exceeds provider capability"
            )
        receipt.assert_execution_capable()

    def _binding_content_dict(self) -> dict[str, Any]:
        return {
            "provider_identifier": self.provider_identifier,
            "exact_model_identifier": self.exact_model_identifier,
            "model_capability_receipt_hash": self.model_capability_receipt_hash,
            "prompt_template_version": self.prompt_template_version,
            "prompt_template_hash": self.prompt_template_hash,
            "structured_output_schema_hash": self.structured_output_schema_hash,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "maximum_output_tokens": self.maximum_output_tokens,
            "seed_value": self.seed_value,
            "seed_policy": self.seed_policy,
            "stateless_calls_required": self.stateless_calls_required,
            "call_timeout_seconds": self.call_timeout_seconds,
            "transport_retry_policy_hash": self.transport_retry_policy_hash,
            "scientific_generation_budget_hash": self.scientific_generation_budget_hash,
            "construction_evidence_rendering_policy_hash": self.construction_evidence_rendering_policy_hash,
        }

    @property
    def configuration_binding_hash(self) -> str:
        """Non-circular configuration core bound by the execution schedule."""

        return stable_hash_v1(self._binding_content_dict())

    def assert_schedule(self, schedule: ConstructionExecutionScheduleV1) -> None:
        if (
            schedule.artifact_hash != self.execution_schedule_hash
            or schedule.configuration_hash != self.configuration_binding_hash
            or schedule.scientific_generation_budget_hash
            != self.scientific_generation_budget_hash
        ):
            raise TASK039E2PreparationError(
                "configuration and execution schedule do not cross-bind"
            )

    def _content_dict(self) -> dict[str, Any]:
        return {
            "schema_version": V6_FOUNDATION_SCHEMA_VERSION,
            "artifact_type": "construction_execution_configuration_v1",
            "provider_identifier": self.provider_identifier,
            "exact_model_identifier": self.exact_model_identifier,
            "model_capability_receipt_hash": self.model_capability_receipt_hash,
            "prompt_template_version": self.prompt_template_version,
            "prompt_template_hash": self.prompt_template_hash,
            "structured_output_schema_hash": self.structured_output_schema_hash,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "maximum_output_tokens": self.maximum_output_tokens,
            "seed_value": self.seed_value,
            "seed_policy": self.seed_policy,
            "stateless_calls_required": self.stateless_calls_required,
            "call_timeout_seconds": self.call_timeout_seconds,
            "transport_retry_policy_hash": self.transport_retry_policy_hash,
            "scientific_generation_budget_hash": self.scientific_generation_budget_hash,
            "execution_schedule_hash": self.execution_schedule_hash,
            "construction_evidence_rendering_policy_hash": self.construction_evidence_rendering_policy_hash,
            "configuration_binding_hash": self.configuration_binding_hash,
            "preparation_only": self.preparation_only,
            "provider_selected": self.provider_selected,
            "model_selected": self.model_selected,
            "provider_contacted": self.provider_contacted,
            "execution_authorized": self.execution_authorized,
        }

    @property
    def artifact_hash(self) -> str:
        return stable_hash_v1(self._content_dict())

    def to_dict(self) -> dict[str, Any]:
        return _with_hash(self._content_dict())


@dataclass(frozen=True)
class TransportRetryPolicyV1:
    scientific_generation_retry: str = "none"
    allowed_transport_retry_reasons: tuple[str, ...] = TRANSPORT_RETRY_REASONS
    response_failures_consuming_scientific_call: tuple[str, ...] = (
        SCIENTIFIC_RESPONSE_FAILURES
    )
    transport_retry_requires_no_model_response: bool = True
    hidden_retry_allowed: bool = False

    def __post_init__(self) -> None:
        if self.scientific_generation_retry != "none":
            raise TASK039E2PreparationError("scientific generation retry must be none")
        if self.allowed_transport_retry_reasons != TRANSPORT_RETRY_REASONS:
            raise TASK039E2PreparationError("transport retry reasons differ")
        if (
            self.response_failures_consuming_scientific_call
            != SCIENTIFIC_RESPONSE_FAILURES
        ):
            raise TASK039E2PreparationError("response failure accounting differs")
        _require_true(
            self.transport_retry_requires_no_model_response,
            "transport_retry_requires_no_model_response",
        )
        _require_false(self.hidden_retry_allowed, "hidden_retry_allowed")

    def classify_attempt(
        self, *, outcome: str, model_response_received: bool
    ) -> tuple[bool, bool]:
        """Return (scientific_call_consumed, transport_retry_allowed)."""

        if outcome in self.allowed_transport_retry_reasons:
            if model_response_received:
                raise TASK039E2PreparationError(
                    "transport failure cannot be claimed after a model response"
                )
            return False, True
        if outcome in self.response_failures_consuming_scientific_call:
            if not model_response_received:
                raise TASK039E2PreparationError(
                    "response failure requires a received model response"
                )
            return True, False
        if outcome == "structured_response_received" and model_response_received:
            return True, False
        raise TASK039E2PreparationError("attempt outcome is not preregistered")

    def _content_dict(self) -> dict[str, Any]:
        return {
            "schema_version": V6_FOUNDATION_SCHEMA_VERSION,
            "artifact_type": "transport_retry_policy_v1",
            "scientific_generation_retry": self.scientific_generation_retry,
            "allowed_transport_retry_reasons": list(
                self.allowed_transport_retry_reasons
            ),
            "response_failures_consuming_scientific_call": list(
                self.response_failures_consuming_scientific_call
            ),
            "transport_retry_requires_no_model_response": self.transport_retry_requires_no_model_response,
            "hidden_retry_allowed": self.hidden_retry_allowed,
        }

    @property
    def artifact_hash(self) -> str:
        return stable_hash_v1(self._content_dict())

    def to_dict(self) -> dict[str, Any]:
        return _with_hash(self._content_dict())


@dataclass(frozen=True)
class ConstructionEvidenceRenderingPolicyV1:
    approved_numeric_roles: tuple[str, ...] = REQUIRED_NUMERIC_ROLES
    maximum_semantic_metadata_fields: int = 8
    approved_private_values_visible_in_model_input: bool = True
    main_output_uses_references_only: bool = True
    raw_hai_allowed: bool = False
    labels_attacks_test_allowed: bool = False
    utility_results_allowed: bool = False
    candidate_method_results_allowed: bool = False

    def __post_init__(self) -> None:
        if self.approved_numeric_roles != REQUIRED_NUMERIC_ROLES:
            raise TASK039E2PreparationError("rendering numeric roles differ")
        if self.maximum_semantic_metadata_fields != 8:
            raise TASK039E2PreparationError("semantic metadata bound differs")
        _require_true(
            self.approved_private_values_visible_in_model_input,
            "approved_private_values_visible_in_model_input",
        )
        _require_true(
            self.main_output_uses_references_only,
            "main_output_uses_references_only",
        )
        for field_name in (
            "raw_hai_allowed",
            "labels_attacks_test_allowed",
            "utility_results_allowed",
            "candidate_method_results_allowed",
        ):
            _require_false(getattr(self, field_name), field_name)

    def _content_dict(self) -> dict[str, Any]:
        return {
            "schema_version": V6_FOUNDATION_SCHEMA_VERSION,
            "artifact_type": "construction_evidence_rendering_policy_v1",
            "approved_numeric_roles": list(self.approved_numeric_roles),
            "maximum_semantic_metadata_fields": self.maximum_semantic_metadata_fields,
            "approved_private_values_visible_in_model_input": self.approved_private_values_visible_in_model_input,
            "main_output_uses_references_only": self.main_output_uses_references_only,
            "raw_hai_allowed": self.raw_hai_allowed,
            "labels_attacks_test_allowed": self.labels_attacks_test_allowed,
            "utility_results_allowed": self.utility_results_allowed,
            "candidate_method_results_allowed": self.candidate_method_results_allowed,
        }

    @property
    def artifact_hash(self) -> str:
        return stable_hash_v1(self._content_dict())

    def to_dict(self) -> dict[str, Any]:
        return _with_hash(self._content_dict())


@dataclass(frozen=True)
class ApprovedRenderedNumericValueV1:
    numeric_role: str
    numeric_value: int | float
    numeric_reference: str
    evidence_origin_reference: str

    def __post_init__(self) -> None:
        if self.numeric_role not in REQUIRED_NUMERIC_ROLES:
            raise TASK039E2PreparationError("numeric role is not approved")
        _require_finite(self.numeric_value, "numeric_value")
        require_sha256(self.numeric_reference, "numeric_reference")
        require_sha256(self.evidence_origin_reference, "evidence_origin_reference")

    def to_dict(self) -> dict[str, Any]:
        return {
            "numeric_role": self.numeric_role,
            "numeric_value": self.numeric_value,
            "numeric_reference": self.numeric_reference,
            "evidence_origin_reference": self.evidence_origin_reference,
        }


@dataclass(frozen=True)
class ConstructionInputViewV1:
    relation_identity: str
    relation_binding_hash: str
    source: str
    source_step_direction: str
    target: str
    target_response_direction: str
    selected_delay_horizon_seconds: int
    approved_numeric_values: tuple[ApprovedRenderedNumericValueV1, ...]
    fit_evidence_reference: str
    confirmation_evidence_reference: str
    bounded_semantic_metadata: tuple[tuple[str, str], ...]
    raw_hai_included: bool = False
    labels_included: bool = False
    attacks_included: bool = False
    test_or_utility_outcomes_included: bool = False
    candidate_method_results_included: bool = False
    runtime_authority_granted: bool = False

    def __post_init__(self) -> None:
        for field_name in ("relation_identity", "source", "target"):
            _require_synthetic_identifier(getattr(self, field_name), field_name)
        require_sha256(self.relation_binding_hash, "relation_binding_hash")
        require_sha256(self.fit_evidence_reference, "fit_evidence_reference")
        require_sha256(
            self.confirmation_evidence_reference, "confirmation_evidence_reference"
        )
        if self.source == self.target:
            raise TASK039E2PreparationError("source and target must differ")
        if self.source_step_direction not in {"step_up", "step_down"}:
            raise TASK039E2PreparationError("source direction is invalid")
        if self.target_response_direction not in {"increase", "decrease"}:
            raise TASK039E2PreparationError("target direction is invalid")
        _require_positive_integer(
            self.selected_delay_horizon_seconds,
            "selected_delay_horizon_seconds",
        )
        roles = tuple(item.numeric_role for item in self.approved_numeric_values)
        if roles != REQUIRED_NUMERIC_ROLES or len(set(roles)) != len(roles):
            raise TASK039E2PreparationError(
                "construction input must contain the exact eleven approved roles"
            )
        horizon = self.approved_numeric_values[
            REQUIRED_NUMERIC_ROLES.index("selected_delay_horizon")
        ].numeric_value
        if horizon != self.selected_delay_horizon_seconds:
            raise TASK039E2PreparationError("selected horizon numeric binding differs")
        if len(self.bounded_semantic_metadata) > 8:
            raise TASK039E2PreparationError("semantic metadata exceeds its bound")
        metadata_keys = tuple(item[0] for item in self.bounded_semantic_metadata)
        if len(set(metadata_keys)) != len(metadata_keys):
            raise TASK039E2PreparationError("semantic metadata keys must be unique")
        for key, value in self.bounded_semantic_metadata:
            require_identifier(key, "semantic_metadata_key")
            require_identifier(value, "semantic_metadata_value")
        assert_private_input_boundary_v1(dict(self.bounded_semantic_metadata))
        for field_name in (
            "raw_hai_included",
            "labels_included",
            "attacks_included",
            "test_or_utility_outcomes_included",
            "candidate_method_results_included",
            "runtime_authority_granted",
        ):
            _require_false(getattr(self, field_name), field_name)

    @property
    def evidence_identities(self) -> tuple[str, ...]:
        return (
            self.relation_binding_hash,
            self.fit_evidence_reference,
            self.confirmation_evidence_reference,
            *(item.numeric_reference for item in self.approved_numeric_values),
            *(item.evidence_origin_reference for item in self.approved_numeric_values),
        )

    def scientific_content_dict(self) -> dict[str, Any]:
        return {
            "relation_identity": self.relation_identity,
            "relation_binding_hash": self.relation_binding_hash,
            "source": self.source,
            "source_step_direction": self.source_step_direction,
            "target": self.target,
            "target_response_direction": self.target_response_direction,
            "selected_delay_horizon_seconds": self.selected_delay_horizon_seconds,
            "approved_numeric_values": [
                item.to_dict() for item in self.approved_numeric_values
            ],
            "fit_evidence_reference": self.fit_evidence_reference,
            "confirmation_evidence_reference": self.confirmation_evidence_reference,
            "bounded_semantic_metadata": [
                {"key": key, "value": value}
                for key, value in self.bounded_semantic_metadata
            ],
        }

    @property
    def initial_evidence_corpus_hash(self) -> str:
        return stable_hash_v1(self.scientific_content_dict())

    def _content_dict(self) -> dict[str, Any]:
        return {
            "schema_version": V6_FOUNDATION_SCHEMA_VERSION,
            "artifact_type": "construction_input_view_v1",
            **self.scientific_content_dict(),
            "initial_evidence_corpus_hash": self.initial_evidence_corpus_hash,
            "raw_hai_included": self.raw_hai_included,
            "labels_included": self.labels_included,
            "attacks_included": self.attacks_included,
            "test_or_utility_outcomes_included": self.test_or_utility_outcomes_included,
            "candidate_method_results_included": self.candidate_method_results_included,
            "runtime_authority_granted": self.runtime_authority_granted,
        }

    @property
    def artifact_hash(self) -> str:
        return stable_hash_v1(self._content_dict())

    def to_dict(self) -> dict[str, Any]:
        return _with_hash(self._content_dict())


def render_construction_input_view_v1(
    *,
    relation: ConfirmedRelationPrimitiveV1,
    numeric_evidence: ApprovedNumericEvidenceBundleV1,
    approved_values: Sequence[ApprovedRenderedNumericValueV1],
    bounded_semantic_metadata: Sequence[tuple[str, str]],
    rendering_policy: ConstructionEvidenceRenderingPolicyV1 | None = None,
) -> ConstructionInputViewV1:
    """Render a synthetic private view from approved reference-bound evidence."""

    policy = rendering_policy or ConstructionEvidenceRenderingPolicyV1()
    if policy.approved_numeric_roles != REQUIRED_NUMERIC_ROLES:
        raise TASK039E2PreparationError("construction rendering policy differs")
    if not relation.relation_identity.startswith(SYNTHETIC_PREFIX):
        raise TASK039E2PreparationError("real confirmed identities are unavailable")
    numeric_evidence.assert_matches(relation)
    by_role = {item.numeric_role: item for item in approved_values}
    if tuple(by_role) != REQUIRED_NUMERIC_ROLES:
        raise TASK039E2PreparationError("approved values differ from frozen roles")
    expected_references = {
        "source_step_threshold": numeric_evidence.source_threshold_reference,
        "source_stability_tolerance": numeric_evidence.source_stability_reference,
        "target_noise_scale": numeric_evidence.target_scale_reference,
    }
    for role, reference in expected_references.items():
        if by_role[role].numeric_reference != reference:
            raise TASK039E2PreparationError(
                f"approved numeric reference mismatch for {role}"
            )
    window_references = tuple(
        by_role[role].numeric_reference for role in WINDOW_NUMERIC_ROLES
    )
    if window_references != numeric_evidence.preregistered_window_constant_references:
        raise TASK039E2PreparationError("window constant references differ")
    return ConstructionInputViewV1(
        relation_identity=relation.relation_identity,
        relation_binding_hash=relation.binding_hash,
        source=relation.source,
        source_step_direction=relation.source_step_direction,
        target=relation.target,
        target_response_direction=relation.target_response_direction,
        selected_delay_horizon_seconds=relation.selected_delay_horizon_seconds,
        approved_numeric_values=tuple(approved_values),
        fit_evidence_reference=relation.fit_evidence_reference,
        confirmation_evidence_reference=relation.confirmation_evidence_reference,
        bounded_semantic_metadata=tuple(bounded_semantic_metadata),
    )


@dataclass(frozen=True)
class PromptTemplateContractV1:
    prompt_family: str
    template_version: str
    template_hash: str
    structured_output_schema_hash: str
    initial_scientific_content: bool
    verifier_feedback_allowed: bool
    targeted_retrieval_allowed: bool
    previous_proposal_hash_allowed: bool
    cross_call_memory_allowed: bool = False
    chain_of_thought_allowed: bool = False

    def __post_init__(self) -> None:
        if self.prompt_family not in ALL_PROMPT_FAMILIES:
            raise TASK039E2PreparationError("prompt family is not frozen")
        require_identifier(self.template_version, "template_version")
        require_sha256(self.template_hash, "template_hash")
        require_sha256(
            self.structured_output_schema_hash, "structured_output_schema_hash"
        )
        expected = {
            "T1": (True, False, False, False),
            "T1-B": (True, False, False, False),
            "T2_CALL_1": (True, False, False, False),
            "T2_FOLLOWUP": (False, True, True, True),
            "T1-DIRECT-NUMBER": (True, False, False, False),
        }[self.prompt_family]
        observed = (
            self.initial_scientific_content,
            self.verifier_feedback_allowed,
            self.targeted_retrieval_allowed,
            self.previous_proposal_hash_allowed,
        )
        if observed != expected:
            raise TASK039E2PreparationError("prompt family permissions differ")
        _require_false(self.cross_call_memory_allowed, "cross_call_memory_allowed")
        _require_false(self.chain_of_thought_allowed, "chain_of_thought_allowed")

    def _content_dict(self) -> dict[str, Any]:
        return {
            "schema_version": V6_FOUNDATION_SCHEMA_VERSION,
            "artifact_type": "prompt_template_contract_v1",
            "prompt_family": self.prompt_family,
            "template_version": self.template_version,
            "template_hash": self.template_hash,
            "structured_output_schema_hash": self.structured_output_schema_hash,
            "initial_scientific_content": self.initial_scientific_content,
            "verifier_feedback_allowed": self.verifier_feedback_allowed,
            "targeted_retrieval_allowed": self.targeted_retrieval_allowed,
            "previous_proposal_hash_allowed": self.previous_proposal_hash_allowed,
            "cross_call_memory_allowed": self.cross_call_memory_allowed,
            "chain_of_thought_allowed": self.chain_of_thought_allowed,
        }

    @property
    def artifact_hash(self) -> str:
        return stable_hash_v1(self._content_dict())

    def to_dict(self) -> dict[str, Any]:
        return _with_hash(self._content_dict())


@dataclass(frozen=True)
class ProviderNeutralPromptEnvelopeV1:
    prompt_family: str
    template_contract_hash: str
    relation_identity: str
    call_number: int
    scientific_content: Mapping[str, Any]
    scientific_content_hash: str
    stateless_call: bool
    verifier_issue_codes: tuple[str, ...] = ()
    affected_fields: tuple[str, ...] = ()
    represented_evidence_identities: tuple[str, ...] = ()
    previous_proposal_hash: str | None = None
    previous_t1b_proposal_visible: bool = False
    previous_t1b_verifier_result_visible: bool = False
    chain_of_thought_included: bool = False

    def __post_init__(self) -> None:
        if self.prompt_family not in ALL_PROMPT_FAMILIES:
            raise TASK039E2PreparationError("prompt family is invalid")
        require_sha256(self.template_contract_hash, "template_contract_hash")
        _require_synthetic_identifier(self.relation_identity, "relation_identity")
        _require_positive_integer(self.call_number, "call_number")
        require_sha256(self.scientific_content_hash, "scientific_content_hash")
        object.__setattr__(
            self, "scientific_content", freeze_json(self.scientific_content)
        )
        if stable_hash_v1(self.scientific_content) != self.scientific_content_hash:
            raise TASK039E2PreparationError("scientific prompt content hash mismatch")
        _require_true(self.stateless_call, "stateless_call")
        for code in self.verifier_issue_codes:
            require_identifier(code, "verifier_issue_code")
        if not set(self.affected_fields).issubset(ALLOWED_T2_AFFECTED_FIELDS):
            raise TASK039E2PreparationError("unsupported affected field")
        for reference in self.represented_evidence_identities:
            require_sha256(reference, "represented_evidence_identity")
        if self.previous_proposal_hash is not None:
            require_sha256(self.previous_proposal_hash, "previous_proposal_hash")
        for field_name in (
            "previous_t1b_proposal_visible",
            "previous_t1b_verifier_result_visible",
            "chain_of_thought_included",
        ):
            _require_false(getattr(self, field_name), field_name)
        if self.prompt_family in (*INITIAL_PROMPT_FAMILIES, "T1-DIRECT-NUMBER"):
            if any(
                (
                    self.verifier_issue_codes,
                    self.affected_fields,
                    self.represented_evidence_identities,
                    self.previous_proposal_hash,
                )
            ):
                raise TASK039E2PreparationError(
                    "initial prompt cannot contain feedback or retrieval"
                )
            if self.prompt_family != "T1-B" and self.call_number != 1:
                raise TASK039E2PreparationError("initial prompt call number differs")
            if self.prompt_family == "T1-B" and self.call_number not in {1, 2, 3}:
                raise TASK039E2PreparationError("T1-B call index must be 1..3")
        elif self.prompt_family == "T2_FOLLOWUP":
            if self.call_number not in {2, 3}:
                raise TASK039E2PreparationError("T2 follow-up must be call 2 or 3")
            if not self.verifier_issue_codes or self.previous_proposal_hash is None:
                raise TASK039E2PreparationError(
                    "T2 follow-up requires bounded verifier issues and proposal hash"
                )

    def _content_dict(self) -> dict[str, Any]:
        return {
            "schema_version": V6_FOUNDATION_SCHEMA_VERSION,
            "artifact_type": "provider_neutral_prompt_envelope_v1",
            "prompt_family": self.prompt_family,
            "template_contract_hash": self.template_contract_hash,
            "relation_identity": self.relation_identity,
            "call_number": self.call_number,
            "scientific_content": thaw_json(self.scientific_content),
            "scientific_content_hash": self.scientific_content_hash,
            "stateless_call": self.stateless_call,
            "verifier_issue_codes": list(self.verifier_issue_codes),
            "affected_fields": list(self.affected_fields),
            "represented_evidence_identities": list(
                self.represented_evidence_identities
            ),
            "previous_proposal_hash": self.previous_proposal_hash,
            "previous_t1b_proposal_visible": self.previous_t1b_proposal_visible,
            "previous_t1b_verifier_result_visible": self.previous_t1b_verifier_result_visible,
            "chain_of_thought_included": self.chain_of_thought_included,
        }

    @property
    def artifact_hash(self) -> str:
        return stable_hash_v1(self._content_dict())

    def to_dict(self) -> dict[str, Any]:
        return _with_hash(self._content_dict())


def render_initial_prompt_v1(
    *,
    view: ConstructionInputViewV1,
    template: PromptTemplateContractV1,
    call_number: int,
) -> ProviderNeutralPromptEnvelopeV1:
    if template.prompt_family not in INITIAL_PROMPT_FAMILIES:
        raise TASK039E2PreparationError("template is not an initial main-arm prompt")
    return ProviderNeutralPromptEnvelopeV1(
        prompt_family=template.prompt_family,
        template_contract_hash=template.artifact_hash,
        relation_identity=view.relation_identity,
        call_number=call_number,
        scientific_content=view.scientific_content_dict(),
        scientific_content_hash=view.initial_evidence_corpus_hash,
        stateless_call=True,
    )


@dataclass(frozen=True)
class TargetedEvidenceRepresentationV1:
    relation_identity: str
    underlying_corpus_hash: str
    represented_evidence_identities: tuple[str, ...]
    retrieval_action_number: int
    operation: str = "targeted_re-presentation_of_already-authorized_evidence"
    new_information_introduced: bool = False

    def __post_init__(self) -> None:
        _require_synthetic_identifier(self.relation_identity, "relation_identity")
        require_sha256(self.underlying_corpus_hash, "underlying_corpus_hash")
        if not self.represented_evidence_identities:
            raise TASK039E2PreparationError("retrieval representation cannot be empty")
        for reference in self.represented_evidence_identities:
            require_sha256(reference, "represented_evidence_identity")
        if len(set(self.represented_evidence_identities)) != len(
            self.represented_evidence_identities
        ):
            raise TASK039E2PreparationError("retrieved evidence identities repeat")
        if self.retrieval_action_number != 1:
            raise TASK039E2PreparationError("retrieval maximum is exactly one")
        if self.operation != (
            "targeted_re-presentation_of_already-authorized_evidence"
        ):
            raise TASK039E2PreparationError("retrieval operation differs")
        _require_false(self.new_information_introduced, "new_information_introduced")

    @property
    def artifact_hash(self) -> str:
        return stable_hash_v1(self.to_dict(include_hash=False))

    def to_dict(self, *, include_hash: bool = True) -> dict[str, Any]:
        payload = {
            "schema_version": V6_FOUNDATION_SCHEMA_VERSION,
            "artifact_type": "targeted_evidence_representation_v1",
            "relation_identity": self.relation_identity,
            "underlying_corpus_hash": self.underlying_corpus_hash,
            "represented_evidence_identities": list(
                self.represented_evidence_identities
            ),
            "retrieval_action_number": self.retrieval_action_number,
            "operation": self.operation,
            "new_information_introduced": self.new_information_introduced,
        }
        if include_hash:
            payload["artifact_hash"] = self.artifact_hash
        return payload


@dataclass(frozen=True)
class T2RetrievalCorpusPolicyV1:
    initial_evidence_corpus_hash: str
    maximum_retrieval_actions: int = MAXIMUM_RETRIEVAL_ACTIONS
    same_underlying_corpus_required: bool = True
    scientifically_new_information_allowed: bool = False
    raw_hai_allowed: bool = False
    labels_attacks_test_allowed: bool = False
    utility_or_candidate_results_allowed: bool = False

    def __post_init__(self) -> None:
        require_sha256(
            self.initial_evidence_corpus_hash, "initial_evidence_corpus_hash"
        )
        if self.maximum_retrieval_actions != MAXIMUM_RETRIEVAL_ACTIONS:
            raise TASK039E2PreparationError("T2 retrieval maximum must be one")
        _require_true(
            self.same_underlying_corpus_required,
            "same_underlying_corpus_required",
        )
        for field_name in (
            "scientifically_new_information_allowed",
            "raw_hai_allowed",
            "labels_attacks_test_allowed",
            "utility_or_candidate_results_allowed",
        ):
            _require_false(getattr(self, field_name), field_name)

    def targeted_represent(
        self,
        *,
        view: ConstructionInputViewV1,
        requested_evidence_identities: Sequence[str],
        retrieval_actions_already_used: int,
    ) -> TargetedEvidenceRepresentationV1:
        if view.initial_evidence_corpus_hash != self.initial_evidence_corpus_hash:
            raise TASK039E2PreparationError("retrieval corpus differs from initial view")
        if retrieval_actions_already_used != 0:
            raise TASK039E2PreparationError("retrieval maximum already exhausted")
        requested = tuple(requested_evidence_identities)
        if not set(requested).issubset(set(view.evidence_identities)):
            raise TASK039E2PreparationError(
                "retrieval introduces a new evidence identity"
            )
        return TargetedEvidenceRepresentationV1(
            relation_identity=view.relation_identity,
            underlying_corpus_hash=view.initial_evidence_corpus_hash,
            represented_evidence_identities=requested,
            retrieval_action_number=1,
        )

    def _content_dict(self) -> dict[str, Any]:
        return {
            "schema_version": V6_FOUNDATION_SCHEMA_VERSION,
            "artifact_type": "t2_retrieval_corpus_policy_v1",
            "initial_evidence_corpus_hash": self.initial_evidence_corpus_hash,
            "maximum_retrieval_actions": self.maximum_retrieval_actions,
            "same_underlying_corpus_required": self.same_underlying_corpus_required,
            "allowed_operation": "targeted_re-presentation_of_already-authorized_evidence",
            "scientifically_new_information_allowed": self.scientifically_new_information_allowed,
            "raw_hai_allowed": self.raw_hai_allowed,
            "labels_attacks_test_allowed": self.labels_attacks_test_allowed,
            "utility_or_candidate_results_allowed": self.utility_or_candidate_results_allowed,
        }

    @property
    def artifact_hash(self) -> str:
        return stable_hash_v1(self._content_dict())

    def to_dict(self) -> dict[str, Any]:
        return _with_hash(self._content_dict())


def render_t2_followup_prompt_v1(
    *,
    view: ConstructionInputViewV1,
    template: PromptTemplateContractV1,
    call_number: int,
    verifier_issue_codes: Sequence[str],
    affected_fields: Sequence[str],
    previous_proposal_hash: str,
    retrieved: TargetedEvidenceRepresentationV1 | None,
) -> ProviderNeutralPromptEnvelopeV1:
    if template.prompt_family != "T2_FOLLOWUP":
        raise TASK039E2PreparationError("template is not T2 follow-up")
    represented: tuple[str, ...] = ()
    if retrieved is not None:
        if (
            retrieved.relation_identity != view.relation_identity
            or retrieved.underlying_corpus_hash != view.initial_evidence_corpus_hash
            or not set(retrieved.represented_evidence_identities).issubset(
                set(view.evidence_identities)
            )
        ):
            raise TASK039E2PreparationError("retrieved evidence corpus mismatch")
        represented = retrieved.represented_evidence_identities
    return ProviderNeutralPromptEnvelopeV1(
        prompt_family="T2_FOLLOWUP",
        template_contract_hash=template.artifact_hash,
        relation_identity=view.relation_identity,
        call_number=call_number,
        scientific_content=view.scientific_content_dict(),
        scientific_content_hash=view.initial_evidence_corpus_hash,
        stateless_call=True,
        verifier_issue_codes=tuple(verifier_issue_codes),
        affected_fields=tuple(affected_fields),
        represented_evidence_identities=represented,
        previous_proposal_hash=previous_proposal_hash,
    )


@dataclass(frozen=True)
class DirectNumberRoleBindingRequirementV1:
    prompt_family: str = "T1-DIRECT-NUMBER"
    numeric_roles_bound: bool = False
    bound_numeric_roles: tuple[str, ...] = ()
    same_relation_and_semantic_context_as_t1: bool = True
    calibrated_numeric_answers_withheld: bool = True
    later_freeze_required_before_call: bool = True
    real_call_allowed: bool = False

    def __post_init__(self) -> None:
        if self.prompt_family != "T1-DIRECT-NUMBER":
            raise TASK039E2PreparationError("direct-number family differs")
        _require_false(self.numeric_roles_bound, "numeric_roles_bound")
        if self.bound_numeric_roles:
            raise TASK039E2PreparationError(
                "PREP must not decide direct-number scientific roles"
            )
        for field_name in (
            "same_relation_and_semantic_context_as_t1",
            "calibrated_numeric_answers_withheld",
            "later_freeze_required_before_call",
        ):
            _require_true(getattr(self, field_name), field_name)
        _require_false(self.real_call_allowed, "real_call_allowed")

    def assert_ready_for_call(self) -> None:
        raise TASK039E2PreparationError(
            "later E2 freeze must bind direct-number roles before any call"
        )

    def _content_dict(self) -> dict[str, Any]:
        return {
            "schema_version": V6_FOUNDATION_SCHEMA_VERSION,
            "artifact_type": "direct_number_role_binding_requirement_v1",
            "prompt_family": self.prompt_family,
            "numeric_roles_bound": self.numeric_roles_bound,
            "bound_numeric_roles": list(self.bound_numeric_roles),
            "same_relation_and_semantic_context_as_t1": self.same_relation_and_semantic_context_as_t1,
            "calibrated_numeric_answers_withheld": self.calibrated_numeric_answers_withheld,
            "later_freeze_required_before_call": self.later_freeze_required_before_call,
            "real_call_allowed": self.real_call_allowed,
        }

    @property
    def artifact_hash(self) -> str:
        return stable_hash_v1(self._content_dict())

    def to_dict(self) -> dict[str, Any]:
        return _with_hash(self._content_dict())


DIRECT_NUMBER_ROLE_REQUIREMENT = DirectNumberRoleBindingRequirementV1()


STRUCTURED_PROPOSAL_FIELDS = frozenset(
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


def validate_closed_structured_proposal_v1(
    document: Mapping[str, Any], *, view: ConstructionInputViewV1
) -> dict[str, Any]:
    """Validate the one closed structured proposal family without authority."""

    if set(document) != STRUCTURED_PROPOSAL_FIELDS:
        unknown = sorted(set(document) - STRUCTURED_PROPOSAL_FIELDS)
        missing = sorted(STRUCTURED_PROPOSAL_FIELDS - set(document))
        raise TASK039E2PreparationError(
            f"structured output closure violation unknown={unknown} missing={missing}"
        )
    if document["schema_version"] != V6_FOUNDATION_SCHEMA_VERSION:
        raise TASK039E2PreparationError("structured output schema version differs")
    if document["artifact_type"] != PROPOSAL_ARTIFACT_TYPE:
        raise TASK039E2PreparationError("structured proposal artifact type differs")
    if document["construction_arm"] not in {"T0", "T1", "T1_B", "T2"}:
        raise TASK039E2PreparationError("construction arm is unsupported")
    if document["dsl_family"] != PROPOSAL_DSL_FAMILY:
        raise TASK039E2PreparationError("proposal DSL family differs")
    expected_identity = {
        "relation_binding_hash": view.relation_binding_hash,
        "relation_identity": view.relation_identity,
        "source": view.source,
        "source_step_direction": view.source_step_direction,
        "target": view.target,
        "target_response_direction": view.target_response_direction,
        "selected_delay_horizon_seconds": view.selected_delay_horizon_seconds,
        "fit_evidence_reference": view.fit_evidence_reference,
        "confirmation_evidence_reference": view.confirmation_evidence_reference,
    }
    if any(document[key] != value for key, value in expected_identity.items()):
        raise TASK039E2PreparationError("structured proposal relation binding differs")
    by_role = {item.numeric_role: item for item in view.approved_numeric_values}
    expected_references = {
        "source_threshold_reference": by_role[
            "source_step_threshold"
        ].numeric_reference,
        "source_stability_reference": by_role[
            "source_stability_tolerance"
        ].numeric_reference,
        "target_scale_reference": by_role["target_noise_scale"].numeric_reference,
    }
    if any(document[key] != value for key, value in expected_references.items()):
        raise TASK039E2PreparationError("structured proposal numeric reference differs")
    if tuple(document["preregistered_window_constant_references"]) != tuple(
        by_role[role].numeric_reference for role in WINDOW_NUMERIC_ROLES
    ):
        raise TASK039E2PreparationError("structured proposal window references differ")
    if document["numeric_origin"] != MAIN_NUMERIC_ORIGIN:
        raise TASK039E2PreparationError("main numeric origin differs")
    if document["variables"] != [view.source, view.target]:
        raise TASK039E2PreparationError("unsupported variable rejected")
    if document["runtime_logic"] != "missing_expected_delayed_response":
        raise TASK039E2PreparationError("runtime logic family differs")
    if document["free_text_runtime_logic"] is not None:
        raise TASK039E2PreparationError("free-form runtime code rejected")
    if document["numeric_literals"] != []:
        raise TASK039E2PreparationError("arbitrary main-arm numeric literal rejected")
    if document["prohibited_data_references"] != []:
        raise TASK039E2PreparationError("prohibited data reference rejected")
    require_sha256(
        document["construction_provenance_hash"],
        "construction_provenance_hash",
    )
    for field_name in (
        "canonical_rule_materialized",
        "validity_authority_granted",
        "runtime_authority_granted",
    ):
        _require_false(document[field_name], field_name)
    require_sha256(document["proposal_hash"], "proposal_hash")
    if canonical_proposal_hash_v1(document) != document["proposal_hash"]:
        raise TASK039E2PreparationError("proposal hash mismatch")
    return dict(document)


def accept_provider_structured_output_v1(
    document: Mapping[str, Any], *, view: ConstructionInputViewV1
) -> dict[str, Any]:
    """Provider adapter: accepts proposal data, never controller actions."""

    if any(
        key in document
        for key in ("controller_action", "revise", "retrieve", "no_rule")
    ):
        raise TASK039E2PreparationError(
            "provider cannot choose a project-owned controller action"
        )
    if document.get("construction_arm") == "T0":
        raise TASK039E2PreparationError("provider cannot emit the T0 arm")
    return validate_closed_structured_proposal_v1(document, view=view)


def generate_synthetic_t0_proposal_v1(
    *,
    view: ConstructionInputViewV1,
    relation: ConfirmedRelationPrimitiveV1,
    numeric_evidence: ApprovedNumericEvidenceBundleV1,
    budget_policy_hash: str,
) -> dict[str, Any]:
    """Generate a synthetic T0 candidate through the exact E0 DSL template."""

    if not relation.relation_identity.startswith(SYNTHETIC_PREFIX):
        raise TASK039E2PreparationError("real T0 generation is locked")
    require_sha256(budget_policy_hash, "budget_policy_hash")
    if (
        relation.binding_hash != view.relation_binding_hash
    ):
        raise TASK039E2PreparationError("T0 input binding differs")
    numeric_evidence.assert_matches(relation)
    protocol = next(
        item for item in FROZEN_ARM_PROTOCOLS if item.arm is ConstructionArmV1.T0
    )
    provenance = ProposalConstructionProvenanceV1(
        construction_arm=ConstructionArmV1.T0,
        arm_protocol_hash=protocol.protocol_hash,
        budget_policy_hash=budget_policy_hash,
        evidence_bundle_hash=numeric_evidence.artifact_hash,
        prompt_template_version="task039e2_t0_template_v1",
        execution_state="synthetic_preparation",
        future_call_record_refs=(),
        model_identifier="not_applicable",
        provider_identifier="not_applicable",
    )
    proposal = prepare_rule_proposal_envelope_v1(
        relation=relation,
        numeric_evidence=numeric_evidence,
        provenance=provenance,
    )
    return validate_closed_structured_proposal_v1(proposal, view=view)


@dataclass(frozen=True)
class ConstructionExecutionScheduleV1:
    relation_identities: tuple[str, ...]
    configuration_hash: str
    scientific_generation_budget_hash: str
    deterministic_arm_order: tuple[str, ...] = DETERMINISTIC_ARM_ORDER
    relation_ordering_policy: str = "frozen_e0_cohort_order"
    result_dependent_ordering: bool = False
    t1_calls_per_relation: int = T1_CALLS_PER_RELATION
    t1b_calls_per_relation: int = T1B_CALLS_PER_RELATION
    t2_maximum_calls_per_relation: int = T2_MAXIMUM_CALLS_PER_RELATION
    direct_number_calls_per_relation: int = DIRECT_NUMBER_CALLS_PER_RELATION
    expected_maximum_scientific_calls: int = EXPECTED_MAXIMUM_SCIENTIFIC_CALLS
    hidden_extra_calls_allowed: bool = False
    same_provider_model_configuration_all_llm_arms: bool = True
    schedule_frozen_before_any_proposal: bool = True
    synthetic_preparation_schedule: bool = True
    actual_execution_schedule: bool = False

    def __post_init__(self) -> None:
        if len(self.relation_identities) != EXPECTED_RELATION_COUNT:
            raise TASK039E2PreparationError("execution schedule must include 42 relations")
        if len(set(self.relation_identities)) != EXPECTED_RELATION_COUNT:
            raise TASK039E2PreparationError("execution schedule has duplicate relations")
        for identity in self.relation_identities:
            _require_synthetic_identifier(identity, "scheduled_relation_identity")
        require_sha256(self.configuration_hash, "configuration_hash")
        require_sha256(
            self.scientific_generation_budget_hash,
            "scientific_generation_budget_hash",
        )
        if self.deterministic_arm_order != DETERMINISTIC_ARM_ORDER:
            raise TASK039E2PreparationError("deterministic arm ordering differs")
        if self.relation_ordering_policy != "frozen_e0_cohort_order":
            raise TASK039E2PreparationError("relation ordering policy differs")
        _require_false(self.result_dependent_ordering, "result_dependent_ordering")
        if (
            self.t1_calls_per_relation,
            self.t1b_calls_per_relation,
            self.t2_maximum_calls_per_relation,
            self.direct_number_calls_per_relation,
        ) != (1, 3, 3, 1):
            raise TASK039E2PreparationError("scientific call budget differs")
        if self.expected_maximum_scientific_calls != EXPECTED_MAXIMUM_SCIENTIFIC_CALLS:
            raise TASK039E2PreparationError("maximum scientific call count differs")
        for field_name in (
            "same_provider_model_configuration_all_llm_arms",
            "schedule_frozen_before_any_proposal",
            "synthetic_preparation_schedule",
        ):
            _require_true(getattr(self, field_name), field_name)
        for field_name in ("hidden_extra_calls_allowed", "actual_execution_schedule"):
            _require_false(getattr(self, field_name), field_name)

    def scientific_call_slots(self) -> tuple[tuple[str, str, int], ...]:
        slots: list[tuple[str, str, int]] = []
        calls = {
            "T1": 1,
            "T1-B": 3,
            "T2": 3,
            "T1-DIRECT-NUMBER": 1,
        }
        for arm in self.deterministic_arm_order:
            for relation in self.relation_identities:
                for call_number in range(1, calls.get(arm, 0) + 1):
                    slots.append((arm, relation, call_number))
        if len(slots) != self.expected_maximum_scientific_calls:
            raise TASK039E2PreparationError("hidden or missing scientific call slot")
        return tuple(slots)

    def _content_dict(self) -> dict[str, Any]:
        return {
            "schema_version": V6_FOUNDATION_SCHEMA_VERSION,
            "artifact_type": "construction_execution_schedule_v1",
            "relation_identities": list(self.relation_identities),
            "relation_count": len(self.relation_identities),
            "configuration_hash": self.configuration_hash,
            "scientific_generation_budget_hash": self.scientific_generation_budget_hash,
            "deterministic_arm_order": list(self.deterministic_arm_order),
            "relation_ordering_policy": self.relation_ordering_policy,
            "result_dependent_ordering": self.result_dependent_ordering,
            "t1_calls_per_relation": self.t1_calls_per_relation,
            "t1b_calls_per_relation": self.t1b_calls_per_relation,
            "t2_maximum_calls_per_relation": self.t2_maximum_calls_per_relation,
            "direct_number_calls_per_relation": self.direct_number_calls_per_relation,
            "expected_maximum_scientific_calls": self.expected_maximum_scientific_calls,
            "hidden_extra_calls_allowed": self.hidden_extra_calls_allowed,
            "same_provider_model_configuration_all_llm_arms": self.same_provider_model_configuration_all_llm_arms,
            "schedule_frozen_before_any_proposal": self.schedule_frozen_before_any_proposal,
            "synthetic_preparation_schedule": self.synthetic_preparation_schedule,
            "actual_execution_schedule": self.actual_execution_schedule,
        }

    @property
    def artifact_hash(self) -> str:
        return stable_hash_v1(self._content_dict())

    def to_dict(self) -> dict[str, Any]:
        return _with_hash(self._content_dict())


@dataclass(frozen=True)
class ProviderResponseCustodyReceiptV1:
    provider_identifier: str
    model_identifier: str
    call_number: int
    provider_request_identifier: str | None
    response_received: bool
    structured_parse_result: str
    transport_retry_count: int
    proposal_hash: str | None
    raw_output_retention_policy: str = "sanitized_structured_output_first"
    raw_model_output_stored: bool = False
    chain_of_thought_stored: bool = False
    runtime_authority_granted: bool = False

    def __post_init__(self) -> None:
        _require_synthetic_identifier(self.provider_identifier, "provider_identifier")
        _require_synthetic_identifier(self.model_identifier, "model_identifier")
        _require_positive_integer(self.call_number, "call_number")
        if self.provider_request_identifier is not None:
            _require_synthetic_identifier(
                self.provider_request_identifier, "provider_request_identifier"
            )
        if self.structured_parse_result not in {
            "parsed",
            "rejected",
            "not_received",
        }:
            raise TASK039E2PreparationError("structured parse result is invalid")
        _require_nonnegative_integer(self.transport_retry_count, "transport_retry_count")
        if self.response_received:
            if self.structured_parse_result == "not_received" or self.proposal_hash is None:
                raise TASK039E2PreparationError(
                    "received response requires parse result and proposal hash"
                )
            require_sha256(self.proposal_hash, "proposal_hash")
        elif self.structured_parse_result != "not_received" or self.proposal_hash is not None:
            raise TASK039E2PreparationError(
                "missing response cannot claim parse or proposal"
            )
        if self.raw_output_retention_policy != "sanitized_structured_output_first":
            raise TASK039E2PreparationError("raw output retention policy is not frozen")
        for field_name in (
            "raw_model_output_stored",
            "chain_of_thought_stored",
            "runtime_authority_granted",
        ):
            _require_false(getattr(self, field_name), field_name)

    def _content_dict(self) -> dict[str, Any]:
        return {
            "schema_version": V6_FOUNDATION_SCHEMA_VERSION,
            "artifact_type": "provider_response_custody_receipt_v1",
            "provider_identifier": self.provider_identifier,
            "model_identifier": self.model_identifier,
            "call_number": self.call_number,
            "provider_request_identifier": self.provider_request_identifier,
            "response_received": self.response_received,
            "structured_parse_result": self.structured_parse_result,
            "transport_retry_count": self.transport_retry_count,
            "proposal_hash": self.proposal_hash,
            "raw_output_retention_policy": self.raw_output_retention_policy,
            "raw_model_output_stored": self.raw_model_output_stored,
            "chain_of_thought_stored": self.chain_of_thought_stored,
            "runtime_authority_granted": self.runtime_authority_granted,
        }

    @property
    def artifact_hash(self) -> str:
        return stable_hash_v1(self._content_dict())

    def to_dict(self) -> dict[str, Any]:
        return _with_hash(self._content_dict())


@dataclass(frozen=True)
class T2ControllerIntegrationPolicyV1:
    provider_proposal_adapter_hash: str
    deterministic_validity_verifier_hash: str
    deterministic_t2_controller_hash: str
    retrieval_renderer_policy_hash: str
    provider_selects_controller_action: bool = False
    allowed_project_controller_actions: tuple[str, ...] = (
        "revise",
        "retrieve",
        "no_rule",
    )
    maximum_provider_calls: int = T2_MAXIMUM_CALLS_PER_RELATION
    maximum_retrieval_actions: int = MAXIMUM_RETRIEVAL_ACTIONS

    def __post_init__(self) -> None:
        for field_name in (
            "provider_proposal_adapter_hash",
            "deterministic_validity_verifier_hash",
            "deterministic_t2_controller_hash",
            "retrieval_renderer_policy_hash",
        ):
            require_sha256(getattr(self, field_name), field_name)
        _require_false(
            self.provider_selects_controller_action,
            "provider_selects_controller_action",
        )
        if self.allowed_project_controller_actions != (
            "revise",
            "retrieve",
            "no_rule",
        ):
            raise TASK039E2PreparationError("controller actions differ")
        if self.maximum_provider_calls != 3:
            raise TASK039E2PreparationError("T2 cannot have a hidden fourth call")
        if self.maximum_retrieval_actions != 1:
            raise TASK039E2PreparationError("T2 retrieval maximum differs")

    def assert_call_allowed(self, next_call_number: int) -> None:
        if next_call_number not in {1, 2, 3}:
            raise TASK039E2PreparationError("no hidden fourth T2 call")

    def _content_dict(self) -> dict[str, Any]:
        return {
            "schema_version": V6_FOUNDATION_SCHEMA_VERSION,
            "artifact_type": "t2_controller_integration_policy_v1",
            "provider_proposal_adapter_hash": self.provider_proposal_adapter_hash,
            "deterministic_validity_verifier_hash": self.deterministic_validity_verifier_hash,
            "deterministic_t2_controller_hash": self.deterministic_t2_controller_hash,
            "retrieval_renderer_policy_hash": self.retrieval_renderer_policy_hash,
            "provider_selects_controller_action": self.provider_selects_controller_action,
            "allowed_project_controller_actions": list(
                self.allowed_project_controller_actions
            ),
            "maximum_provider_calls": self.maximum_provider_calls,
            "maximum_retrieval_actions": self.maximum_retrieval_actions,
        }

    @property
    def artifact_hash(self) -> str:
        return stable_hash_v1(self._content_dict())

    def to_dict(self) -> dict[str, Any]:
        return _with_hash(self._content_dict())


def structured_output_schema_hash_v1(schema: Mapping[str, Any]) -> str:
    if schema.get("additionalProperties") is not False:
        raise TASK039E2PreparationError("structured output schema must be closed")
    return stable_hash_v1(schema)


def assert_preparation_boundary_v1(
    *,
    real_e1_result: object | None = None,
    real_e1_private_evidence: object | None = None,
    real_confirmed_identity: object | None = None,
    real_provider_identifier: object | None = None,
    real_model_identifier: object | None = None,
    provider_client: object | None = None,
    llm: object | None = None,
) -> None:
    if any(
        value is not None
        for value in (
            real_e1_result,
            real_e1_private_evidence,
            real_confirmed_identity,
            real_provider_identifier,
            real_model_identifier,
            provider_client,
            llm,
        )
    ):
        raise TASK039E2PreparationError(
            "TASK-039E2 preparation accepts synthetic, provider-neutral inputs only"
        )


__all__ = [
    "ALLOWED_T2_AFFECTED_FIELDS",
    "ALL_PROMPT_FAMILIES",
    "ApprovedRenderedNumericValueV1",
    "BASE_COMMIT",
    "BRANCH",
    "CALIBRATED_NUMERIC_ROLES",
    "ConstructionExecutionConfigurationV1",
    "ConstructionExecutionScheduleV1",
    "ConstructionEvidenceRenderingPolicyV1",
    "ConstructionInputViewV1",
    "DETERMINISTIC_ARM_ORDER",
    "DIRECT_NUMBER_ROLE_REQUIREMENT",
    "DirectNumberRoleBindingRequirementV1",
    "E2_AUTHORIZATION_CREATED",
    "EXPECTED_MAXIMUM_SCIENTIFIC_CALLS",
    "EXPECTED_RELATION_COUNT",
    "INITIAL_PROMPT_FAMILIES",
    "LLM_CALLED",
    "MAXIMUM_RETRIEVAL_ACTIONS",
    "MODEL_SELECTED",
    "ModelCapabilityReceiptV1",
    "PREPARATION_STATUS",
    "PROHIBITED_INPUT_KEYS",
    "PROVIDER_CONTACTED",
    "PROVIDER_SELECTED",
    "PromptTemplateContractV1",
    "ProviderNeutralPromptEnvelopeV1",
    "ProviderResponseCustodyReceiptV1",
    "REAL_CONFIRMED_IDENTITIES_CONSUMED",
    "REAL_E1_PRIVATE_EVIDENCE_ACCESSED",
    "REAL_E1_RESULT_CONSUMED",
    "REAL_T0_GENERATED",
    "REQUIRED_NUMERIC_ROLES",
    "RULE_V2_AUTHORIZED",
    "RUNTIME_AUTHORITY_GRANTED",
    "SCIENTIFIC_RESPONSE_FAILURES",
    "STRUCTURED_PROPOSAL_FIELDS",
    "T2ControllerIntegrationPolicyV1",
    "T2RetrievalCorpusPolicyV1",
    "TASK039E2PreparationError",
    "TASK_ID",
    "TRANSPORT_RETRY_REASONS",
    "TargetedEvidenceRepresentationV1",
    "TransportRetryPolicyV1",
    "WINDOW_NUMERIC_ROLES",
    "accept_provider_structured_output_v1",
    "assert_preparation_boundary_v1",
    "assert_private_input_boundary_v1",
    "generate_synthetic_t0_proposal_v1",
    "render_construction_input_view_v1",
    "render_initial_prompt_v1",
    "render_t2_followup_prompt_v1",
    "structured_output_schema_hash_v1",
    "validate_closed_structured_proposal_v1",
]
