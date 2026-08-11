"""Independent, provider-free TASK-039E2 execution-freeze audit preparation.

The oracle uses only the Python standard library.  It does not import an E2
freezer, read an E1/E2 result, inspect credentials, or contact a provider.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
import math
import re
from types import MappingProxyType
from typing import Any, Mapping, Sequence


TASK_ID = "TASK-039E2-AUDIT-PREP"
BASE_COMMIT = "4a6b5875b59bdcc7c3bd0957e90fa27b71e0e9fb"
BRANCH = "task-039e2-audit-prep"
PREPARATION_STATUS = "passed_task039e2_audit_preparation"

EXPECTED_PROVIDER = "openai"
EXPECTED_ENDPOINT = "/v1/chat/completions"
EXPECTED_MODEL_SNAPSHOT = "gpt-5.4-2026-03-05"
EXPECTED_REASONING = "none"
EXPECTED_TEMPERATURE = 0.7
EXPECTED_TOP_P = 1.0
EXPECTED_MAX_COMPLETION_TOKENS = 1024
EXPECTED_SEED = None
EXPECTED_STREAM = False
EXPECTED_STORE = False
EXPECTED_MODEL_FALLBACK = False

EXPECTED_RELATION_COUNT = 42
EXPECTED_T1_CALLS = 42
EXPECTED_T1B_CALLS = 126
MAXIMUM_T2_CALLS = 126
EXPECTED_DIRECT_NUMBER_CALLS = 42
MAXIMUM_PROVIDER_SCIENTIFIC_CALLS = 336
EXPECTED_CONCURRENCY = 1
MAXIMUM_TRANSPORT_RETRIES = 2
SCIENTIFIC_GENERATION_RETRIES = 0

PROMPT_REQUEST_ROLES = (
    "T1_INITIAL",
    "T1B_1_INITIAL",
    "T1B_2_INITIAL",
    "T1B_3_INITIAL",
    "T2_CALL1_INITIAL",
)
PROMPT_HASH_FAMILIES = (
    "T1",
    "T1-B",
    "T2_CALL_1",
    "T2_FOLLOWUP",
    "T1-DIRECT-NUMBER",
)
DIRECT_NUMBER_HIDDEN_ROLES = (
    "source_step_threshold",
    "source_stability_tolerance",
    "target_noise_scale",
)
DIRECT_NUMBER_ALLOWED_SUPPLIED_ROLES = (
    "selected_delay_horizon",
    "source_pre_window",
    "source_post_window",
    "minimum_source_stability_fraction",
    "source_refractory",
    "cross_source_isolation_radius",
    "target_baseline_window",
    "target_response_window",
)
TRANSPORT_RETRY_ELIGIBLE = (
    "connection_failure",
    "timeout_no_model_response",
    "http_429_no_model_response",
    "http_5xx_no_model_response",
)
NOT_TRANSPORT_RETRY = (
    "http_400",
    "http_401",
    "http_403",
    "provider_refusal",
    "malformed_output",
    "verifier_rejection",
)
PROHIBITED_MODEL_VISIBLE_KEYS = frozenset(
    {
        "arm",
        "arm_label",
        "construction_arm",
        "call_index",
        "call_number",
        "other_arm_outcome",
        "other_arm_outcomes",
        "candidate_method_provenance",
        "candidate_method_results",
    }
)
PROHIBITED_RETRIEVAL_KEYS = frozenset(
    {
        "raw_hai",
        "hai_rows",
        "labels",
        "attacks",
        "test",
        "test_data",
        "test_outcomes",
        "utility",
        "utility_results",
        "utility_outcomes",
        "candidate_method_results",
        "candidate_method_provenance",
    }
)

REAL_E2_RESULT_ACCESSED = False
REAL_E1_PRIVATE_EVIDENCE_ACCESSED = False
PROVIDER_CONTACTED = False
MODEL_CALLED = False
LLM_CALLED = False
API_KEY_ACCESSED = False
REAL_T0_GENERATED = False
RULE_GENERATED = False
RUNTIME_AUTHORITY_GRANTED = False
E3_AUTHORITY_GRANTED = False

_HASH = re.compile(r"^[a-f0-9]{64}$")
_IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]*$")
_SYNTHETIC = re.compile(r"^SYNTHETIC_[A-Za-z0-9._:-]+$")


class TASK039E2AuditPreparationError(ValueError):
    """Raised when a future E2 freeze would fail the independent oracle."""


def _freeze_json(value: Any) -> Any:
    if isinstance(value, Mapping):
        result: dict[str, Any] = {}
        for key, item in value.items():
            if not isinstance(key, str):
                raise TASK039E2AuditPreparationError("JSON keys must be strings")
            result[key] = _freeze_json(item)
        return MappingProxyType(result)
    if isinstance(value, (list, tuple)):
        return tuple(_freeze_json(item) for item in value)
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float) and math.isfinite(value):
        return value
    raise TASK039E2AuditPreparationError("value is not finite canonical JSON")


def _thaw_json(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {key: _thaw_json(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_thaw_json(item) for item in value]
    return value


def _canonical_bytes(value: Mapping[str, Any]) -> bytes:
    try:
        text = json.dumps(
            _thaw_json(value),
            ensure_ascii=True,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        )
    except (TypeError, ValueError) as exc:
        raise TASK039E2AuditPreparationError("document is not canonical JSON") from exc
    return text.encode("utf-8")


def independent_hash_v1(value: Mapping[str, Any]) -> str:
    return sha256(_canonical_bytes(value)).hexdigest()


def _with_hash(value: Mapping[str, Any]) -> dict[str, Any]:
    result = _thaw_json(value)
    result["artifact_hash"] = independent_hash_v1(value)
    return result


def _require_hash(value: str, field_name: str) -> None:
    if not isinstance(value, str) or _HASH.fullmatch(value) is None:
        raise TASK039E2AuditPreparationError(
            f"{field_name} must be a lowercase SHA-256 hash"
        )


def _require_identifier(value: str, field_name: str) -> None:
    if not isinstance(value, str) or _IDENTIFIER.fullmatch(value) is None:
        raise TASK039E2AuditPreparationError(f"{field_name} is not an identifier")


def _require_synthetic(value: str, field_name: str) -> None:
    if not isinstance(value, str) or _SYNTHETIC.fullmatch(value) is None:
        raise TASK039E2AuditPreparationError(
            f"{field_name} must use a SYNTHETIC_ audit fixture identity"
        )


def _require_false(value: bool, field_name: str) -> None:
    if value is not False:
        raise TASK039E2AuditPreparationError(f"{field_name} must remain false")


def _require_true(value: bool, field_name: str) -> None:
    if value is not True:
        raise TASK039E2AuditPreparationError(f"{field_name} must be true")


def _require_positive_integer(value: int, field_name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise TASK039E2AuditPreparationError(f"{field_name} must be positive")


def _walk_prohibited_keys(
    value: Any, *, prohibited: frozenset[str], label: str, path: str = "$"
) -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            normalized = str(key).lower()
            if normalized in prohibited:
                raise TASK039E2AuditPreparationError(
                    f"{label} leakage at {path}.{key}"
                )
            _walk_prohibited_keys(
                item,
                prohibited=prohibited,
                label=label,
                path=f"{path}.{key}",
            )
    elif isinstance(value, (tuple, list)):
        for index, item in enumerate(value):
            _walk_prohibited_keys(
                item,
                prohibited=prohibited,
                label=label,
                path=f"{path}[{index}]",
            )


@dataclass(frozen=True)
class IndependentExecutionConfigurationV1:
    provider: str
    endpoint: str
    model: str
    reasoning: str
    temperature: float
    top_p: float
    max_completion_tokens: int
    seed: int | None
    stream: bool
    store: bool
    model_fallback: bool
    prompt_hash_manifest_hash: str
    structured_schema_manifest_hash: str
    rendering_policy_hash: str
    retrieval_policy_hash: str
    t0_template_hash: str
    schedule_hash: str
    retry_policy_hash: str
    direct_number_role_policy_hash: str
    provider_contacted: bool = False
    execution_started: bool = False

    def __post_init__(self) -> None:
        expected = {
            "provider": EXPECTED_PROVIDER,
            "endpoint": EXPECTED_ENDPOINT,
            "model": EXPECTED_MODEL_SNAPSHOT,
            "reasoning": EXPECTED_REASONING,
            "temperature": EXPECTED_TEMPERATURE,
            "top_p": EXPECTED_TOP_P,
            "max_completion_tokens": EXPECTED_MAX_COMPLETION_TOKENS,
            "seed": EXPECTED_SEED,
            "stream": EXPECTED_STREAM,
            "store": EXPECTED_STORE,
            "model_fallback": EXPECTED_MODEL_FALLBACK,
        }
        for field_name, expected_value in expected.items():
            if getattr(self, field_name) != expected_value:
                raise TASK039E2AuditPreparationError(
                    f"execution configuration mismatch: {field_name}"
                )
        if type(self.temperature) is not float or type(self.top_p) is not float:
            raise TASK039E2AuditPreparationError(
                "temperature and top_p must be exact JSON floating-point settings"
            )
        if (
            isinstance(self.max_completion_tokens, bool)
            or not isinstance(self.max_completion_tokens, int)
        ):
            raise TASK039E2AuditPreparationError(
                "max_completion_tokens must be an integer"
            )
        for field_name in ("stream", "store", "model_fallback"):
            _require_false(getattr(self, field_name), field_name)
        for field_name in (
            "prompt_hash_manifest_hash",
            "structured_schema_manifest_hash",
            "rendering_policy_hash",
            "retrieval_policy_hash",
            "t0_template_hash",
            "schedule_hash",
            "retry_policy_hash",
            "direct_number_role_policy_hash",
        ):
            _require_hash(getattr(self, field_name), field_name)
        _require_false(self.provider_contacted, "provider_contacted")
        _require_false(self.execution_started, "execution_started")

    def _content_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "1.0.0",
            "artifact_type": "independent_execution_configuration_v1",
            "provider": self.provider,
            "endpoint": self.endpoint,
            "model": self.model,
            "reasoning": self.reasoning,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "max_completion_tokens": self.max_completion_tokens,
            "seed": self.seed,
            "stream": self.stream,
            "store": self.store,
            "model_fallback": self.model_fallback,
            "prompt_hash_manifest_hash": self.prompt_hash_manifest_hash,
            "structured_schema_manifest_hash": self.structured_schema_manifest_hash,
            "rendering_policy_hash": self.rendering_policy_hash,
            "retrieval_policy_hash": self.retrieval_policy_hash,
            "t0_template_hash": self.t0_template_hash,
            "schedule_hash": self.schedule_hash,
            "retry_policy_hash": self.retry_policy_hash,
            "direct_number_role_policy_hash": self.direct_number_role_policy_hash,
            "provider_contacted": self.provider_contacted,
            "execution_started": self.execution_started,
        }

    @property
    def artifact_hash(self) -> str:
        return independent_hash_v1(self._content_dict())

    def to_dict(self) -> dict[str, Any]:
        return _with_hash(self._content_dict())


@dataclass(frozen=True)
class IndependentFreezeHashBindingsV1:
    prompt_family_hashes: tuple[tuple[str, str], ...]
    structured_schema_hash: str
    rendering_policy_hash: str
    retrieval_policy_hash: str
    t0_template_hash: str
    schedule_hash: str
    retry_policy_hash: str
    direct_number_role_policy_hash: str

    def __post_init__(self) -> None:
        if tuple(name for name, _ in self.prompt_family_hashes) != PROMPT_HASH_FAMILIES:
            raise TASK039E2AuditPreparationError("prompt hash families are incomplete")
        for name, value in self.prompt_family_hashes:
            _require_identifier(name.replace("-", "_"), "prompt_family")
            _require_hash(value, f"prompt_family_hash[{name}]")
        for field_name in (
            "structured_schema_hash",
            "rendering_policy_hash",
            "retrieval_policy_hash",
            "t0_template_hash",
            "schedule_hash",
            "retry_policy_hash",
            "direct_number_role_policy_hash",
        ):
            _require_hash(getattr(self, field_name), field_name)

    @property
    def prompt_hash_manifest_hash(self) -> str:
        return independent_hash_v1(
            {
                "prompt_family_hashes": [
                    {"family": name, "hash": value}
                    for name, value in self.prompt_family_hashes
                ]
            }
        )

    @property
    def structured_schema_manifest_hash(self) -> str:
        return independent_hash_v1(
            {"structured_schema_hash": self.structured_schema_hash}
        )

    def assert_matches_configuration(
        self, configuration: IndependentExecutionConfigurationV1
    ) -> None:
        expected = {
            "prompt_hash_manifest_hash": self.prompt_hash_manifest_hash,
            "structured_schema_manifest_hash": self.structured_schema_manifest_hash,
            "rendering_policy_hash": self.rendering_policy_hash,
            "retrieval_policy_hash": self.retrieval_policy_hash,
            "t0_template_hash": self.t0_template_hash,
            "schedule_hash": self.schedule_hash,
            "retry_policy_hash": self.retry_policy_hash,
            "direct_number_role_policy_hash": self.direct_number_role_policy_hash,
        }
        if any(
            getattr(configuration, field_name) != expected_value
            for field_name, expected_value in expected.items()
        ):
            raise TASK039E2AuditPreparationError(
                "configuration does not bind every frozen policy hash"
            )


@dataclass(frozen=True)
class IndependentSchemaFairnessAuditResultV1:
    schema_hash: str
    syntactic_structured_output_enforced: bool
    relation_specific_answer_leakage_absent: bool
    semantic_validity_checked_separately: bool
    semantic_validity_result_used: bool = False

    def __post_init__(self) -> None:
        _require_hash(self.schema_hash, "schema_hash")
        for field_name in (
            "syntactic_structured_output_enforced",
            "relation_specific_answer_leakage_absent",
            "semantic_validity_checked_separately",
        ):
            _require_true(getattr(self, field_name), field_name)
        _require_false(self.semantic_validity_result_used, "semantic_validity_result_used")


_RELATION_ANSWER_FIELDS = frozenset(
    {
        "relation_identity",
        "source",
        "target",
        "selected_horizon",
        "selected_delay_horizon",
        "selected_delay_horizon_seconds",
    }
)
_GENERIC_CONST_FIELDS = frozenset(
    {
        "$schema",
        "$id",
        "schema_version",
        "artifact_type",
        "dsl_family",
        "runtime_logic",
        "numeric_origin",
        "canonical_rule_materialized",
        "validity_authority_granted",
        "runtime_authority_granted",
    }
)


def audit_provider_facing_schema_v1(
    schema: Mapping[str, Any],
) -> IndependentSchemaFairnessAuditResultV1:
    """Audit syntax closure independently from semantic rule validity."""

    frozen = _freeze_json(schema)
    if frozen.get("type") != "object" or frozen.get("additionalProperties") is not False:
        raise TASK039E2AuditPreparationError(
            "provider-facing structured schema must enforce a closed object"
        )

    def walk(value: Any, property_name: str | None, path: str) -> None:
        if not isinstance(value, Mapping):
            if isinstance(value, tuple):
                for index, item in enumerate(value):
                    walk(item, property_name, f"{path}[{index}]")
            return
        if property_name in _RELATION_ANSWER_FIELDS:
            if "const" in value:
                raise TASK039E2AuditPreparationError(
                    f"relation-specific schema const leakage at {path}"
                )
            enum = value.get("enum")
            if isinstance(enum, tuple) and len(enum) == 1:
                raise TASK039E2AuditPreparationError(
                    f"singleton relation answer leakage at {path}"
                )
        if "const" in value and property_name not in _GENERIC_CONST_FIELDS:
            constant = value["const"]
            lower_name = (property_name or "").lower()
            if (
                "evidence" in lower_name
                or "reference" in lower_name
                or lower_name.endswith("_hash")
                or (isinstance(constant, str) and _HASH.fullmatch(constant))
            ):
                raise TASK039E2AuditPreparationError(
                    f"expected hash/reference const leakage at {path}"
                )
        properties = value.get("properties")
        if isinstance(properties, Mapping):
            for name, definition in properties.items():
                walk(definition, name, f"{path}.properties.{name}")
        for key, item in value.items():
            if key == "properties":
                continue
            if isinstance(item, (Mapping, tuple, list)):
                walk(item, property_name, f"{path}.{key}")

    walk(frozen, None, "$schema")
    return IndependentSchemaFairnessAuditResultV1(
        schema_hash=independent_hash_v1(frozen),
        syntactic_structured_output_enforced=True,
        relation_specific_answer_leakage_absent=True,
        semantic_validity_checked_separately=True,
    )


@dataclass(frozen=True)
class IndependentModelVisiblePromptV1:
    relation_identity: str
    request_role: str
    configuration_hash: str
    model_visible_scientific_content: Mapping[str, Any]
    previous_proposal_visible: bool = False
    previous_validity_result_visible: bool = False
    cross_call_state_visible: bool = False

    def __post_init__(self) -> None:
        _require_synthetic(self.relation_identity, "relation_identity")
        if self.request_role not in PROMPT_REQUEST_ROLES:
            raise TASK039E2AuditPreparationError("prompt request role is invalid")
        _require_hash(self.configuration_hash, "configuration_hash")
        frozen = _freeze_json(self.model_visible_scientific_content)
        _walk_prohibited_keys(
            frozen,
            prohibited=PROHIBITED_MODEL_VISIBLE_KEYS,
            label="model-visible prompt",
        )
        object.__setattr__(self, "model_visible_scientific_content", frozen)
        for field_name in (
            "previous_proposal_visible",
            "previous_validity_result_visible",
            "cross_call_state_visible",
        ):
            _require_false(getattr(self, field_name), field_name)

    @property
    def scientific_content_hash(self) -> str:
        return independent_hash_v1(self.model_visible_scientific_content)

    @property
    def request_hash(self) -> str:
        return independent_hash_v1(
            {
                "relation_identity": self.relation_identity,
                "request_role": self.request_role,
                "configuration_hash": self.configuration_hash,
                "model_visible_scientific_content": _thaw_json(
                    self.model_visible_scientific_content
                ),
                "previous_proposal_visible": self.previous_proposal_visible,
                "previous_validity_result_visible": self.previous_validity_result_visible,
                "cross_call_state_visible": self.cross_call_state_visible,
            }
        )


@dataclass(frozen=True)
class PromptFairnessAuditResultV1:
    relation_identity: str
    request_count: int
    shared_scientific_content_hash: str
    model_visible_arm_labels_absent: bool
    model_visible_call_indices_absent: bool
    other_arm_outcomes_absent: bool
    candidate_method_provenance_absent: bool

    def __post_init__(self) -> None:
        _require_synthetic(self.relation_identity, "relation_identity")
        if self.request_count != 5:
            raise TASK039E2AuditPreparationError("prompt fairness requires five requests")
        _require_hash(
            self.shared_scientific_content_hash,
            "shared_scientific_content_hash",
        )
        for field_name in (
            "model_visible_arm_labels_absent",
            "model_visible_call_indices_absent",
            "other_arm_outcomes_absent",
            "candidate_method_provenance_absent",
        ):
            _require_true(getattr(self, field_name), field_name)


def audit_initial_prompt_fairness_v1(
    requests: Sequence[IndependentModelVisiblePromptV1],
) -> PromptFairnessAuditResultV1:
    if len(requests) != 5:
        raise TASK039E2AuditPreparationError("exactly five initial requests required")
    if tuple(item.request_role for item in requests) != PROMPT_REQUEST_ROLES:
        raise TASK039E2AuditPreparationError("initial prompt request roles differ")
    relations = {item.relation_identity for item in requests}
    configs = {item.configuration_hash for item in requests}
    hashes = {item.scientific_content_hash for item in requests}
    if len(relations) != 1:
        raise TASK039E2AuditPreparationError("initial prompts span multiple relations")
    if len(configs) != 1:
        raise TASK039E2AuditPreparationError("initial prompts use different configs")
    if len(hashes) != 1:
        raise TASK039E2AuditPreparationError(
            "initial model-visible scientific content differs"
        )
    return PromptFairnessAuditResultV1(
        relation_identity=requests[0].relation_identity,
        request_count=5,
        shared_scientific_content_hash=requests[0].scientific_content_hash,
        model_visible_arm_labels_absent=True,
        model_visible_call_indices_absent=True,
        other_arm_outcomes_absent=True,
        candidate_method_provenance_absent=True,
    )


@dataclass(frozen=True)
class IndependentT1BPolicyV1:
    requests_required: int = 3
    selection_policy: str = "lowest_admissible_call_index"
    result_dependent_fourth_call_allowed: bool = False

    def __post_init__(self) -> None:
        if self.requests_required != 3:
            raise TASK039E2AuditPreparationError("T1-B requires three requests")
        if self.selection_policy != "lowest_admissible_call_index":
            raise TASK039E2AuditPreparationError("T1-B selection policy differs")
        _require_false(
            self.result_dependent_fourth_call_allowed,
            "result_dependent_fourth_call_allowed",
        )

    def audit_requests(
        self, requests: Sequence[IndependentModelVisiblePromptV1]
    ) -> None:
        if len(requests) != 3:
            raise TASK039E2AuditPreparationError("T1-B requires exactly three requests")
        expected_roles = PROMPT_REQUEST_ROLES[1:4]
        if tuple(item.request_role for item in requests) != expected_roles:
            raise TASK039E2AuditPreparationError("T1-B request indices differ")
        if len({item.scientific_content_hash for item in requests}) != 1:
            raise TASK039E2AuditPreparationError("T1-B initial prompts differ")
        if len({item.configuration_hash for item in requests}) != 1:
            raise TASK039E2AuditPreparationError("T1-B configurations differ")
        if len({item.relation_identity for item in requests}) != 1:
            raise TASK039E2AuditPreparationError("T1-B relations differ")

    def select(self, admissible_by_call: Sequence[bool]) -> int | None:
        if len(admissible_by_call) != 3 or any(
            type(value) is not bool for value in admissible_by_call
        ):
            raise TASK039E2AuditPreparationError("T1-B requires three outcomes")
        for index, admissible in enumerate(admissible_by_call, start=1):
            if admissible:
                return index
        return None


@dataclass(frozen=True)
class IndependentRetrievalRecordV1:
    relation_identity: str
    retrieval_action_number: int
    initial_authorized_evidence_identities: tuple[str, ...]
    retrieved_evidence_identities: tuple[str, ...]
    model_visible_retrieval_content: Mapping[str, Any]

    def __post_init__(self) -> None:
        _require_synthetic(self.relation_identity, "relation_identity")
        if self.retrieval_action_number != 1:
            raise TASK039E2AuditPreparationError("maximum retrieval actions is one")
        for field_name in (
            "initial_authorized_evidence_identities",
            "retrieved_evidence_identities",
        ):
            values = getattr(self, field_name)
            if not values or len(set(values)) != len(values):
                raise TASK039E2AuditPreparationError(
                    f"{field_name} must be nonempty and unique"
                )
            for value in values:
                _require_hash(value, field_name)
        if not set(self.retrieved_evidence_identities).issubset(
            set(self.initial_authorized_evidence_identities)
        ):
            raise TASK039E2AuditPreparationError(
                "retrieved evidence identity is new"
            )
        frozen = _freeze_json(self.model_visible_retrieval_content)
        _walk_prohibited_keys(
            frozen,
            prohibited=PROHIBITED_RETRIEVAL_KEYS,
            label="retrieval",
        )
        object.__setattr__(self, "model_visible_retrieval_content", frozen)

    @property
    def initial_identity_set_hash(self) -> str:
        return independent_hash_v1(
            {"evidence_identities": list(self.initial_authorized_evidence_identities)}
        )

    @property
    def retrieved_identity_set_hash(self) -> str:
        return independent_hash_v1(
            {"evidence_identities": list(self.retrieved_evidence_identities)}
        )


def audit_retrieval_sequence_v1(
    retrievals: Sequence[IndependentRetrievalRecordV1],
) -> IndependentRetrievalRecordV1 | None:
    if len(retrievals) > 1:
        raise TASK039E2AuditPreparationError("second retrieval action rejected")
    return retrievals[0] if retrievals else None


@dataclass(frozen=True)
class IndependentDirectNumberAuditInputV1:
    hidden_calibrated_roles: tuple[str, ...]
    supplied_nonhidden_numeric_roles: tuple[str, ...]
    calibrated_role_values: tuple[tuple[str, int | float], ...]
    calibrated_role_references: tuple[tuple[str, str], ...]
    model_visible_prompt: Mapping[str, Any]

    def __post_init__(self) -> None:
        if self.hidden_calibrated_roles != DIRECT_NUMBER_HIDDEN_ROLES:
            raise TASK039E2AuditPreparationError(
                "direct-number hidden roles must be exactly the calibrated three"
            )
        if self.supplied_nonhidden_numeric_roles != DIRECT_NUMBER_ALLOWED_SUPPLIED_ROLES:
            raise TASK039E2AuditPreparationError(
                "direct-number supplied horizon/window roles differ"
            )
        if tuple(role for role, _ in self.calibrated_role_values) != (
            DIRECT_NUMBER_HIDDEN_ROLES
        ):
            raise TASK039E2AuditPreparationError("calibrated value roles differ")
        if tuple(role for role, _ in self.calibrated_role_references) != (
            DIRECT_NUMBER_HIDDEN_ROLES
        ):
            raise TASK039E2AuditPreparationError("calibrated reference roles differ")
        for role, value in self.calibrated_role_values:
            if (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not math.isfinite(float(value))
            ):
                raise TASK039E2AuditPreparationError(
                    f"calibrated value for {role} is not finite"
                )
        for role, reference in self.calibrated_role_references:
            _require_hash(reference, f"calibrated_reference[{role}]")
        frozen = _freeze_json(self.model_visible_prompt)
        serialized_values = tuple(
            value for _, value in self.calibrated_role_values
        )
        serialized_references = tuple(
            reference for _, reference in self.calibrated_role_references
        )

        def walk(value: Any, path: str) -> None:
            if isinstance(value, Mapping):
                for key, item in value.items():
                    walk(item, f"{path}.{key}")
            elif isinstance(value, tuple):
                for index, item in enumerate(value):
                    walk(item, f"{path}[{index}]")
            elif (
                not isinstance(value, bool)
                and isinstance(value, (int, float))
                and any(float(value) == float(expected) for expected in serialized_values)
            ):
                raise TASK039E2AuditPreparationError(
                    f"direct-number calibrated answer leak at {path}"
                )
            elif value in serialized_references:
                raise TASK039E2AuditPreparationError(
                    f"direct-number calibrated reference leak at {path}"
                )

        walk(frozen, "$direct_prompt")
        object.__setattr__(self, "model_visible_prompt", frozen)

    @property
    def prompt_hash(self) -> str:
        return independent_hash_v1(self.model_visible_prompt)


@dataclass(frozen=True)
class IndependentScheduleEntryV1:
    sequence_index: int
    relation_identity: str
    arm: str
    arm_call_number: int
    execution_kind: str
    t2_early_stop_conditional: bool = False

    def __post_init__(self) -> None:
        if (
            isinstance(self.sequence_index, bool)
            or not isinstance(self.sequence_index, int)
            or self.sequence_index < 0
        ):
            raise TASK039E2AuditPreparationError("sequence_index is invalid")
        _require_synthetic(self.relation_identity, "relation_identity")
        if self.arm not in {"T0", "T1", "T1-B", "T2", "T1-DIRECT-NUMBER"}:
            raise TASK039E2AuditPreparationError("schedule arm is invalid")
        _require_positive_integer(self.arm_call_number, "arm_call_number")
        if self.execution_kind not in {"local", "provider"}:
            raise TASK039E2AuditPreparationError("execution kind is invalid")
        if self.arm == "T0":
            if self.execution_kind != "local" or self.arm_call_number != 1:
                raise TASK039E2AuditPreparationError("T0 must be one local execution")
            _require_false(
                self.t2_early_stop_conditional,
                "t2_early_stop_conditional",
            )
        else:
            if self.execution_kind != "provider":
                raise TASK039E2AuditPreparationError("LLM arms must be provider slots")
            if self.arm == "T1" and self.arm_call_number != 1:
                raise TASK039E2AuditPreparationError("T1 has one call")
            if self.arm == "T1-B" and self.arm_call_number not in {1, 2, 3}:
                raise TASK039E2AuditPreparationError("T1-B call number differs")
            if self.arm == "T2":
                if self.arm_call_number not in {1, 2, 3}:
                    raise TASK039E2AuditPreparationError("fourth T2 call rejected")
                _require_true(
                    self.t2_early_stop_conditional,
                    "t2_early_stop_conditional",
                )
            else:
                _require_false(
                    self.t2_early_stop_conditional,
                    "t2_early_stop_conditional",
                )
                if self.arm == "T1-DIRECT-NUMBER" and self.arm_call_number != 1:
                    raise TASK039E2AuditPreparationError("direct-number has one call")


@dataclass(frozen=True)
class IndependentExecutionScheduleV1:
    relation_order: tuple[str, ...]
    entries: tuple[IndependentScheduleEntryV1, ...]
    concurrency: int = EXPECTED_CONCURRENCY
    ordering_policy: str = "relation_major"
    cross_arm_output_visibility: bool = False
    result_dependent_ordering: bool = False
    only_t2_may_early_stop: bool = True

    def __post_init__(self) -> None:
        if len(self.relation_order) != EXPECTED_RELATION_COUNT:
            raise TASK039E2AuditPreparationError("schedule relation count must be 42")
        if len(set(self.relation_order)) != EXPECTED_RELATION_COUNT:
            raise TASK039E2AuditPreparationError("schedule relation identities repeat")
        for relation in self.relation_order:
            _require_synthetic(relation, "relation_identity")
        if type(self.concurrency) is not int or self.concurrency != 1:
            raise TASK039E2AuditPreparationError("execution concurrency must be one")
        if self.ordering_policy != "relation_major":
            raise TASK039E2AuditPreparationError("schedule must be relation-major")
        _require_false(
            self.cross_arm_output_visibility,
            "cross_arm_output_visibility",
        )
        _require_false(self.result_dependent_ordering, "result_dependent_ordering")
        _require_true(self.only_t2_may_early_stop, "only_t2_may_early_stop")
        if tuple(entry.sequence_index for entry in self.entries) != tuple(
            range(len(self.entries))
        ):
            raise TASK039E2AuditPreparationError("schedule sequence is not contiguous")
        observed_relation_order: list[str] = []
        previous: str | None = None
        for entry in self.entries:
            if entry.relation_identity != previous:
                if entry.relation_identity in observed_relation_order:
                    raise TASK039E2AuditPreparationError(
                        "schedule is not relation-major"
                    )
                observed_relation_order.append(entry.relation_identity)
                previous = entry.relation_identity
        if tuple(observed_relation_order) != self.relation_order:
            raise TASK039E2AuditPreparationError("schedule relation order differs")
        expected_pattern = (
            ("T0", 1),
            ("T1", 1),
            ("T1-B", 1),
            ("T1-B", 2),
            ("T1-B", 3),
            ("T2", 1),
            ("T2", 2),
            ("T2", 3),
            ("T1-DIRECT-NUMBER", 1),
        )
        for relation in self.relation_order:
            pattern = tuple(
                (entry.arm, entry.arm_call_number)
                for entry in self.entries
                if entry.relation_identity == relation
            )
            if pattern != expected_pattern:
                raise TASK039E2AuditPreparationError(
                    "per-relation execution schedule differs"
                )
        counts = self.provider_call_counts()
        if counts != {
            "T1": EXPECTED_T1_CALLS,
            "T1-B": EXPECTED_T1B_CALLS,
            "T2": MAXIMUM_T2_CALLS,
            "T1-DIRECT-NUMBER": EXPECTED_DIRECT_NUMBER_CALLS,
        }:
            raise TASK039E2AuditPreparationError("provider call counts differ")
        if sum(counts.values()) != MAXIMUM_PROVIDER_SCIENTIFIC_CALLS:
            raise TASK039E2AuditPreparationError("336-call maximum differs")

    def provider_call_counts(self) -> dict[str, int]:
        return {
            arm: sum(
                1
                for entry in self.entries
                if entry.arm == arm and entry.execution_kind == "provider"
            )
            for arm in ("T1", "T1-B", "T2", "T1-DIRECT-NUMBER")
        }

    @property
    def artifact_hash(self) -> str:
        return independent_hash_v1(
            {
                "relation_order": list(self.relation_order),
                "entries": [
                    {
                        "sequence_index": entry.sequence_index,
                        "relation_identity": entry.relation_identity,
                        "arm": entry.arm,
                        "arm_call_number": entry.arm_call_number,
                        "execution_kind": entry.execution_kind,
                        "t2_early_stop_conditional": entry.t2_early_stop_conditional,
                    }
                    for entry in self.entries
                ],
                "concurrency": self.concurrency,
                "ordering_policy": self.ordering_policy,
                "cross_arm_output_visibility": self.cross_arm_output_visibility,
                "result_dependent_ordering": self.result_dependent_ordering,
                "only_t2_may_early_stop": self.only_t2_may_early_stop,
            }
        )


def build_synthetic_relation_major_schedule_v1(
    relation_order: Sequence[str],
) -> IndependentExecutionScheduleV1:
    """Build the frozen maximum schedule without observing construction results."""

    pattern = (
        ("T0", 1, "local", False),
        ("T1", 1, "provider", False),
        ("T1-B", 1, "provider", False),
        ("T1-B", 2, "provider", False),
        ("T1-B", 3, "provider", False),
        ("T2", 1, "provider", True),
        ("T2", 2, "provider", True),
        ("T2", 3, "provider", True),
        ("T1-DIRECT-NUMBER", 1, "provider", False),
    )
    entries: list[IndependentScheduleEntryV1] = []
    for relation_identity in relation_order:
        for arm, call_number, execution_kind, conditional in pattern:
            entries.append(
                IndependentScheduleEntryV1(
                    sequence_index=len(entries),
                    relation_identity=relation_identity,
                    arm=arm,
                    arm_call_number=call_number,
                    execution_kind=execution_kind,
                    t2_early_stop_conditional=conditional,
                )
            )
    return IndependentExecutionScheduleV1(
        relation_order=tuple(relation_order),
        entries=tuple(entries),
    )


@dataclass(frozen=True)
class IndependentRetryDecisionV1:
    outcome: str
    transport_retry_allowed: bool
    scientific_generation_consumed: bool
    full_run_failure: bool
    relation_skipped: bool = False

    def __post_init__(self) -> None:
        _require_identifier(self.outcome, "retry outcome")
        _require_false(self.relation_skipped, "relation_skipped")


@dataclass(frozen=True)
class IndependentRetryPolicyV1:
    transport_retry_eligible: tuple[str, ...] = TRANSPORT_RETRY_ELIGIBLE
    not_transport_retry_eligible: tuple[str, ...] = NOT_TRANSPORT_RETRY
    maximum_transport_retries: int = MAXIMUM_TRANSPORT_RETRIES
    scientific_generation_retries: int = SCIENTIFIC_GENERATION_RETRIES
    exhaustion_outcome: str = "full_run_failure"
    relation_skipping_allowed: bool = False

    def __post_init__(self) -> None:
        if self.transport_retry_eligible != TRANSPORT_RETRY_ELIGIBLE:
            raise TASK039E2AuditPreparationError("transport retry categories differ")
        if self.not_transport_retry_eligible != NOT_TRANSPORT_RETRY:
            raise TASK039E2AuditPreparationError("non-retry categories differ")
        if (
            type(self.maximum_transport_retries) is not int
            or self.maximum_transport_retries != 2
        ):
            raise TASK039E2AuditPreparationError("transport retry maximum must be two")
        if (
            type(self.scientific_generation_retries) is not int
            or self.scientific_generation_retries != 0
        ):
            raise TASK039E2AuditPreparationError(
                "scientific generation retries must be zero"
            )
        if self.exhaustion_outcome != "full_run_failure":
            raise TASK039E2AuditPreparationError(
                "retry exhaustion must fail the full run"
            )
        _require_false(self.relation_skipping_allowed, "relation_skipping_allowed")

    def classify(
        self,
        *,
        outcome: str,
        model_response_obtained: bool,
        completed_transport_retries: int,
    ) -> IndependentRetryDecisionV1:
        if (
            isinstance(completed_transport_retries, bool)
            or not isinstance(completed_transport_retries, int)
            or completed_transport_retries < 0
        ):
            raise TASK039E2AuditPreparationError(
                "completed transport retry count is invalid"
            )
        if outcome == "success":
            if model_response_obtained is not True:
                raise TASK039E2AuditPreparationError(
                    "success requires a model response"
                )
            return IndependentRetryDecisionV1(
                outcome=outcome,
                transport_retry_allowed=False,
                scientific_generation_consumed=True,
                full_run_failure=False,
            )
        if outcome in self.transport_retry_eligible:
            if model_response_obtained is not False:
                raise TASK039E2AuditPreparationError(
                    "transport retry cannot disguise an obtained model response"
                )
            exhausted = completed_transport_retries >= self.maximum_transport_retries
            return IndependentRetryDecisionV1(
                outcome=outcome,
                transport_retry_allowed=not exhausted,
                scientific_generation_consumed=False,
                full_run_failure=exhausted,
            )
        if outcome in self.not_transport_retry_eligible:
            scientific_consumed = outcome in {
                "provider_refusal",
                "malformed_output",
                "verifier_rejection",
            }
            if scientific_consumed and model_response_obtained is not True:
                raise TASK039E2AuditPreparationError(
                    f"{outcome} requires an obtained model response"
                )
            return IndependentRetryDecisionV1(
                outcome=outcome,
                transport_retry_allowed=False,
                scientific_generation_consumed=scientific_consumed,
                full_run_failure=True,
            )
        raise TASK039E2AuditPreparationError("unregistered retry outcome")

    @property
    def artifact_hash(self) -> str:
        return independent_hash_v1(
            {
                "transport_retry_eligible": list(self.transport_retry_eligible),
                "not_transport_retry_eligible": list(
                    self.not_transport_retry_eligible
                ),
                "maximum_transport_retries": self.maximum_transport_retries,
                "scientific_generation_retries": self.scientific_generation_retries,
                "exhaustion_outcome": self.exhaustion_outcome,
                "relation_skipping_allowed": self.relation_skipping_allowed,
            }
        )


@dataclass(frozen=True)
class IndependentCapabilityReceiptV1:
    provider: str = EXPECTED_PROVIDER
    endpoint: str = EXPECTED_ENDPOINT
    exact_model_snapshot: str = EXPECTED_MODEL_SNAPSHOT
    structured_output_required: bool = True
    seed_policy: str = "deprecated_not_relied_upon"
    provider_contacted: bool = False
    live_capability_checked: bool = False
    account_availability_checked: bool = False
    seed_determinism_claimed: bool = False

    def __post_init__(self) -> None:
        if self.provider != EXPECTED_PROVIDER:
            raise TASK039E2AuditPreparationError("capability provider differs")
        if self.endpoint != EXPECTED_ENDPOINT:
            raise TASK039E2AuditPreparationError("capability endpoint differs")
        if self.exact_model_snapshot != EXPECTED_MODEL_SNAPSHOT:
            raise TASK039E2AuditPreparationError(
                "capability receipt requires the exact model snapshot"
            )
        _require_true(self.structured_output_required, "structured_output_required")
        if self.seed_policy != "deprecated_not_relied_upon":
            raise TASK039E2AuditPreparationError(
                "seed must be deprecated and not relied upon"
            )
        _require_false(self.provider_contacted, "provider_contacted")
        _require_false(self.live_capability_checked, "live_capability_checked")
        _require_false(
            self.account_availability_checked,
            "account_availability_checked",
        )
        _require_false(self.seed_determinism_claimed, "seed_determinism_claimed")

    def to_dict(self) -> dict[str, Any]:
        return _with_hash(
            {
                "schema_version": "task039e2_independent_capability_receipt_v1",
                "provider": self.provider,
                "endpoint": self.endpoint,
                "exact_model_snapshot": self.exact_model_snapshot,
                "structured_output_required": self.structured_output_required,
                "seed_policy": self.seed_policy,
                "provider_contacted": self.provider_contacted,
                "live_capability_checked": self.live_capability_checked,
                "account_availability_checked": self.account_availability_checked,
                "seed_determinism_claimed": self.seed_determinism_claimed,
            }
        )


@dataclass(frozen=True)
class IndependentE2AuditPreparationReceiptV1:
    status: str = PREPARATION_STATUS
    independent_standard_library_oracle_prepared: bool = True
    real_e2_result_accessed: bool = False
    real_e1_private_evidence_accessed: bool = False
    provider_contacted: bool = False
    model_called: bool = False
    api_key_accessed: bool = False
    real_t0_generated: bool = False
    rule_generated: bool = False
    runtime_authority: bool = False
    e3_authority: bool = False

    def __post_init__(self) -> None:
        if self.status != PREPARATION_STATUS:
            raise TASK039E2AuditPreparationError("preparation status differs")
        _require_true(
            self.independent_standard_library_oracle_prepared,
            "independent_standard_library_oracle_prepared",
        )
        for field_name in (
            "real_e2_result_accessed",
            "real_e1_private_evidence_accessed",
            "provider_contacted",
            "model_called",
            "api_key_accessed",
            "real_t0_generated",
            "rule_generated",
            "runtime_authority",
            "e3_authority",
        ):
            _require_false(getattr(self, field_name), field_name)

    def to_dict(self) -> dict[str, Any]:
        return _with_hash(
            {
                "schema_version": "task039e2_audit_preparation_receipt_v1",
                "status": self.status,
                "independent_standard_library_oracle_prepared": (
                    self.independent_standard_library_oracle_prepared
                ),
                "real_e2_result_accessed": self.real_e2_result_accessed,
                "real_e1_private_evidence_accessed": (
                    self.real_e1_private_evidence_accessed
                ),
                "provider_contacted": self.provider_contacted,
                "model_called": self.model_called,
                "api_key_accessed": self.api_key_accessed,
                "real_t0_generated": self.real_t0_generated,
                "rule_generated": self.rule_generated,
                "runtime_authority": self.runtime_authority,
                "e3_authority": self.e3_authority,
            }
        )


def assert_preparation_boundary_v1(
    *,
    real_e2_result_accessed: bool = False,
    real_e1_private_evidence_accessed: bool = False,
    provider_contacted: bool = False,
    model_called: bool = False,
    api_key_accessed: bool = False,
) -> str:
    boundary = {
        "real_e2_result_accessed": real_e2_result_accessed,
        "real_e1_private_evidence_accessed": real_e1_private_evidence_accessed,
        "provider_contacted": provider_contacted,
        "model_called": model_called,
        "api_key_accessed": api_key_accessed,
    }
    for field_name, value in boundary.items():
        _require_false(value, field_name)
    return PREPARATION_STATUS


def attempt_provider_interaction_v1(*_args: Any, **_kwargs: Any) -> None:
    """Fail before client construction, credential inspection, or network I/O."""

    raise TASK039E2AuditPreparationError(
        "provider interaction is impossible in TASK-039E2-AUDIT-PREP"
    )


__all__ = [
    "API_KEY_ACCESSED",
    "BASE_COMMIT",
    "BRANCH",
    "DIRECT_NUMBER_ALLOWED_SUPPLIED_ROLES",
    "DIRECT_NUMBER_HIDDEN_ROLES",
    "E3_AUTHORITY_GRANTED",
    "EXPECTED_CONCURRENCY",
    "EXPECTED_DIRECT_NUMBER_CALLS",
    "EXPECTED_ENDPOINT",
    "EXPECTED_MAX_COMPLETION_TOKENS",
    "EXPECTED_MODEL_FALLBACK",
    "EXPECTED_MODEL_SNAPSHOT",
    "EXPECTED_PROVIDER",
    "EXPECTED_REASONING",
    "EXPECTED_RELATION_COUNT",
    "EXPECTED_SEED",
    "EXPECTED_STORE",
    "EXPECTED_STREAM",
    "EXPECTED_T1B_CALLS",
    "EXPECTED_T1_CALLS",
    "EXPECTED_TEMPERATURE",
    "EXPECTED_TOP_P",
    "IndependentCapabilityReceiptV1",
    "IndependentDirectNumberAuditInputV1",
    "IndependentE2AuditPreparationReceiptV1",
    "IndependentExecutionConfigurationV1",
    "IndependentExecutionScheduleV1",
    "IndependentFreezeHashBindingsV1",
    "IndependentModelVisiblePromptV1",
    "IndependentRetrievalRecordV1",
    "IndependentRetryDecisionV1",
    "IndependentRetryPolicyV1",
    "IndependentSchemaFairnessAuditResultV1",
    "IndependentScheduleEntryV1",
    "IndependentT1BPolicyV1",
    "MAXIMUM_PROVIDER_SCIENTIFIC_CALLS",
    "MAXIMUM_T2_CALLS",
    "MAXIMUM_TRANSPORT_RETRIES",
    "LLM_CALLED",
    "MODEL_CALLED",
    "NOT_TRANSPORT_RETRY",
    "PREPARATION_STATUS",
    "PROMPT_HASH_FAMILIES",
    "PROMPT_REQUEST_ROLES",
    "PROVIDER_CONTACTED",
    "REAL_E1_PRIVATE_EVIDENCE_ACCESSED",
    "REAL_E2_RESULT_ACCESSED",
    "REAL_T0_GENERATED",
    "RULE_GENERATED",
    "RUNTIME_AUTHORITY_GRANTED",
    "SCIENTIFIC_GENERATION_RETRIES",
    "TASK039E2AuditPreparationError",
    "TASK_ID",
    "TRANSPORT_RETRY_ELIGIBLE",
    "assert_preparation_boundary_v1",
    "attempt_provider_interaction_v1",
    "audit_initial_prompt_fairness_v1",
    "audit_provider_facing_schema_v1",
    "audit_retrieval_sequence_v1",
    "build_synthetic_relation_major_schedule_v1",
    "independent_hash_v1",
]
