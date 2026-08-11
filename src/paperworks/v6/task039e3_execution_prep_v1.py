"""Mock-only scientific execution machinery for TASK-039E3-PREP.

The module binds the public TASK-039E2 configuration and provides only an
injectable mock transport.  It contains no network client, credential reader,
real E1 loader, provider execution authority, or runtime authority path.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
import math
from types import MappingProxyType
from typing import Any, Mapping, Protocol, Sequence

from paperworks.v6.common import freeze_json, stable_hash_v1, thaw_json
from paperworks.v6.task039e0_rule_construction_prep_v1 import (
    ApprovedNumericEvidenceBundleV1,
    ConfirmedRelationPrimitiveV1,
)
from paperworks.v6.task039e2_execution_configuration_v1 import (
    API_BASE_URL,
    API_ENDPOINT,
    CALIBRATED_NUMERIC_ROLES,
    DIRECT_NUMBER_PROMPT_V1,
    DIRECT_NUMBER_PROVIDER_SCHEMA_V1,
    ENDPOINT_FAMILY,
    EXACT_MODEL,
    MAIN_INITIAL_PROMPT_V1,
    MAIN_PROVIDER_SCHEMA_V1,
    PROVIDER,
    T2_FOLLOWUP_PROMPT_V1,
    WINDOW_NUMERIC_ROLES,
    ProviderProposalCoreV1,
    build_chat_completions_request_body_v1,
    render_direct_number_model_content_v1,
    render_main_initial_model_content_v1,
    render_t2_followup_model_content_v1,
)


TASK_ID = "TASK-039E3-PREP"
BASE_COMMIT = "3c263277d5b30217058601bd0e12876d2cf58ba4"
BRANCH = "task-039e3-scientific-execution-prep"
STATUS = "passed_task039e3_scientific_execution_preparation"

E2_PROTOCOL_BUNDLE_HASH = (
    "2295f6e57aff47081419d70e942af02101de33fa545a758ea4a7e6476a46e6e8"
)
MAIN_PROMPT_HASH = (
    "a251e4b9da31c33e72d14dd81da6b2b1d0d1437fdf37ca311330eccce226f1ba"
)
T2_FOLLOWUP_PROMPT_HASH = (
    "a633067a7c9927be158f68ce714236f4c18c09433d49c903dac941a9774eeca5"
)
DIRECT_NUMBER_PROMPT_HASH = (
    "fb01d8990ee3a7affe540dfdf3556b46d7bd744cd1e3a04d6fd9d79772dd2769"
)
MAIN_SCHEMA_HASH = (
    "92c628faf78e5ebdcfc3ec2dbeb9daa42b6beff0875cbf226c87c2f2c43cc216"
)
DIRECT_NUMBER_SCHEMA_HASH = (
    "b1b91bf27fd191da57984be625a2547e4e5ee96a0aca52535df071af92bfd6ca"
)
EXECUTION_SCHEDULE_HASH = (
    "6db63485387924b28e9ce498aae46412a127ba69055a28e72880e1afffa4c4ca"
)
E0_BUDGET_POLICY_HASH = (
    "d36e297cb1de71d4a04f4ad99a31d7c75c076d1b2d6b2ccb74905bdcf4cc1c64"
)
E0_VALIDITY_POLICY_HASH = (
    "1bbeb53a091ecb43bcb7a121653efbef20d053ba3c34a409eef99550514d6a11"
)
E0_CONTROLLER_POLICY_HASH = (
    "6cc22fea19a636d590cb5e744d896e8f8588946049d2e0743674883c9eae15b4"
)
PROVIDER_MODEL_RECEIPT_HASH = (
    "c44c9b39d4e92d3ebac62a962ff967073411e55184cbcdd9d770cb7f2eeaf649"
)

LIVE_PROVIDER_TRANSPORT_ENABLED = False
REAL_E1_PRIVATE_EVIDENCE_ACCESSED = False
PROVIDER_CONTACTED = False
CREDENTIAL_ACCESSED = False
API_KEY_ACCESSED = False
CAPABILITY_PROBE_EXECUTED = False
LLM_CALLED = False
REAL_PROPOSAL_GENERATED = False
RULE_V2_AUTHORIZED = False
RUNTIME_AUTHORITY_GRANTED = False
INDIVIDUAL_PROPOSALS_PUBLIC = False
MAXIMUM_SCIENTIFIC_SLOTS = 336
MAXIMUM_TRANSPORT_RETRIES = 2
TRANSPORT_RETRY_DELAYS_SECONDS = (2, 4)

_ALL_NUMERIC_ROLES = CALIBRATED_NUMERIC_ROLES + WINDOW_NUMERIC_ROLES
_HASH_FIELDS = frozenset({"authorization", "authorization_header", "api_key"})
_PROHIBITED_VIEW_KEYS = frozenset(
    {
        "raw_hai",
        "hai_rows",
        "labels",
        "attacks",
        "test_data",
        "utility",
        "utility_outcomes",
        "candidate_method_performance",
        "candidate_method_results",
        "construction_arm",
        "call_index",
    }
)
_TRANSPORT_RETRYABLE = frozenset(
    {
        "connection_failure",
        "connection_reset",
        "timeout_before_response",
        "http_429",
        "http_5xx",
    }
)
_TERMINAL_SLOT_STATES = frozenset(
    {
        "completed_structured",
        "completed_refusal",
        "completed_invalid_response",
        "transport_exhausted",
    }
)


class TASK039E3PreparationError(ValueError):
    """Raised when mock preparation violates a frozen execution boundary."""


def _text_hash(value: str) -> str:
    return sha256(value.encode("utf-8")).hexdigest()


def _require_hash(value: object, field_name: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise TASK039E3PreparationError(f"{field_name} must be a SHA-256 hash")
    return value


def _require_synthetic(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value.startswith("SYNTHETIC_"):
        raise TASK039E3PreparationError(
            f"{field_name} must use a SYNTHETIC_ fixture identity"
        )
    return value


def _require_nonempty_string(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value:
        raise TASK039E3PreparationError(f"{field_name} must be a nonempty string")
    return value


def _canonical_json(value: Mapping[str, Any]) -> str:
    return json.dumps(
        thaw_json(value),
        ensure_ascii=True,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def _walk_prohibited_keys(
    value: Any, *, prohibited: frozenset[str], label: str, path: str = "$"
) -> None:
    if isinstance(value, Mapping):
        for key, nested in value.items():
            normalized = str(key).lower()
            if normalized in prohibited:
                raise TASK039E3PreparationError(
                    f"{label} contains prohibited field at {path}.{key}"
                )
            _walk_prohibited_keys(
                nested,
                prohibited=prohibited,
                label=label,
                path=f"{path}.{key}",
            )
    elif isinstance(value, (list, tuple)):
        for index, nested in enumerate(value):
            _walk_prohibited_keys(
                nested,
                prohibited=prohibited,
                label=label,
                path=f"{path}[{index}]",
            )


@dataclass(frozen=True)
class FrozenE2ExecutionBindingV1:
    protocol_bundle_hash: str = E2_PROTOCOL_BUNDLE_HASH
    provider: str = PROVIDER
    endpoint_family: str = ENDPOINT_FAMILY
    endpoint: str = f"{API_BASE_URL}{API_ENDPOINT}"
    exact_model: str = EXACT_MODEL
    reasoning_effort: str = "none"
    temperature: float = 0.7
    top_p: float = 1.0
    max_completion_tokens: int = 1024
    seed: None = None
    stream: bool = False
    store: bool = False
    fallback_allowed: bool = False
    main_prompt_hash: str = MAIN_PROMPT_HASH
    t2_followup_prompt_hash: str = T2_FOLLOWUP_PROMPT_HASH
    direct_number_prompt_hash: str = DIRECT_NUMBER_PROMPT_HASH
    main_schema_hash: str = MAIN_SCHEMA_HASH
    direct_number_schema_hash: str = DIRECT_NUMBER_SCHEMA_HASH
    schedule_hash: str = EXECUTION_SCHEDULE_HASH

    def __post_init__(self) -> None:
        expected = {
            "protocol_bundle_hash": E2_PROTOCOL_BUNDLE_HASH,
            "provider": "openai",
            "endpoint_family": "chat_completions",
            "endpoint": "https://api.openai.com/v1/chat/completions",
            "exact_model": "gpt-5.4-2026-03-05",
            "reasoning_effort": "none",
            "temperature": 0.7,
            "top_p": 1.0,
            "max_completion_tokens": 1024,
            "seed": None,
            "stream": False,
            "store": False,
            "fallback_allowed": False,
            "main_prompt_hash": MAIN_PROMPT_HASH,
            "t2_followup_prompt_hash": T2_FOLLOWUP_PROMPT_HASH,
            "direct_number_prompt_hash": DIRECT_NUMBER_PROMPT_HASH,
            "main_schema_hash": MAIN_SCHEMA_HASH,
            "direct_number_schema_hash": DIRECT_NUMBER_SCHEMA_HASH,
            "schedule_hash": EXECUTION_SCHEDULE_HASH,
        }
        if any(getattr(self, name) != value for name, value in expected.items()):
            raise TASK039E3PreparationError("frozen E2 execution binding differs")
        if type(self.temperature) is not float or type(self.top_p) is not float:
            raise TASK039E3PreparationError("sampling float types differ")
        for name in (
            "stream",
            "store",
            "fallback_allowed",
        ):
            if getattr(self, name) is not False:
                raise TASK039E3PreparationError(f"{name} must remain false")
        if _text_hash(MAIN_INITIAL_PROMPT_V1 + "\n") != self.main_prompt_hash:
            raise TASK039E3PreparationError("main prompt source hash differs")
        if _text_hash(T2_FOLLOWUP_PROMPT_V1 + "\n") != self.t2_followup_prompt_hash:
            raise TASK039E3PreparationError("T2 prompt source hash differs")
        if _text_hash(DIRECT_NUMBER_PROMPT_V1 + "\n") != self.direct_number_prompt_hash:
            raise TASK039E3PreparationError("direct-number prompt hash differs")
        if stable_hash_v1(MAIN_PROVIDER_SCHEMA_V1) != self.main_schema_hash:
            raise TASK039E3PreparationError("main provider schema hash differs")
        if (
            stable_hash_v1(DIRECT_NUMBER_PROVIDER_SCHEMA_V1)
            != self.direct_number_schema_hash
        ):
            raise TASK039E3PreparationError("direct-number schema hash differs")

    @property
    def artifact_hash(self) -> str:
        return stable_hash_v1(self.to_dict())

    def to_dict(self) -> dict[str, Any]:
        return {
            "artifact_type": "task039e3_frozen_e2_execution_binding_v1",
            "protocol_bundle_hash": self.protocol_bundle_hash,
            "provider": self.provider,
            "endpoint_family": self.endpoint_family,
            "endpoint": self.endpoint,
            "exact_model": self.exact_model,
            "reasoning_effort": self.reasoning_effort,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "max_completion_tokens": self.max_completion_tokens,
            "seed": self.seed,
            "stream": self.stream,
            "store": self.store,
            "fallback_allowed": self.fallback_allowed,
            "main_prompt_hash": self.main_prompt_hash,
            "t2_followup_prompt_hash": self.t2_followup_prompt_hash,
            "direct_number_prompt_hash": self.direct_number_prompt_hash,
            "main_schema_hash": self.main_schema_hash,
            "direct_number_schema_hash": self.direct_number_schema_hash,
            "schedule_hash": self.schedule_hash,
        }


FROZEN_E2_BINDING = FrozenE2ExecutionBindingV1()


@dataclass(frozen=True)
class ConstructionNumericBindingV1:
    numeric_role: str
    value: int | float
    reference: str
    evidence_identity: str

    def __post_init__(self) -> None:
        if self.numeric_role not in _ALL_NUMERIC_ROLES:
            raise TASK039E3PreparationError("synthetic numeric role is not approved")
        if (
            isinstance(self.value, bool)
            or not isinstance(self.value, (int, float))
            or not math.isfinite(float(self.value))
        ):
            raise TASK039E3PreparationError("synthetic numeric value must be finite")
        _require_hash(self.reference, "numeric reference")
        _require_nonempty_string(self.evidence_identity, "evidence identity")

    def to_dict(self) -> dict[str, Any]:
        return {
            "numeric_role": self.numeric_role,
            "value": self.value,
            "reference": self.reference,
            "evidence_identity": self.evidence_identity,
        }


SyntheticNumericBindingV1 = ConstructionNumericBindingV1


@dataclass(frozen=True)
class ConstructionInputViewV1:
    relation_identity: str
    source: str
    source_step_direction: str
    target: str
    target_response_direction: str
    selected_delay_horizon_seconds: int
    numeric_bindings: tuple[ConstructionNumericBindingV1, ...]
    approved_evidence_identities: tuple[str, ...]
    semantic_process_metadata: Mapping[str, Any]

    def __post_init__(self) -> None:
        for field_name in ("relation_identity", "source", "target"):
            _require_nonempty_string(getattr(self, field_name), field_name)
        if self.source_step_direction not in {"step_up", "step_down"}:
            raise TASK039E3PreparationError("source direction differs")
        if self.target_response_direction not in {"increase", "decrease"}:
            raise TASK039E3PreparationError("target direction differs")
        if self.selected_delay_horizon_seconds not in {1, 5, 10, 30, 60}:
            raise TASK039E3PreparationError("selected horizon differs")
        roles = tuple(item.numeric_role for item in self.numeric_bindings)
        if roles != _ALL_NUMERIC_ROLES:
            raise TASK039E3PreparationError("construction view numeric roles differ")
        if not self.approved_evidence_identities or len(
            set(self.approved_evidence_identities)
        ) != len(self.approved_evidence_identities):
            raise TASK039E3PreparationError("approved evidence identities differ")
        for identity in self.approved_evidence_identities:
            _require_nonempty_string(identity, "approved evidence identity")
        metadata = freeze_json(self.semantic_process_metadata)
        _walk_prohibited_keys(
            metadata,
            prohibited=_PROHIBITED_VIEW_KEYS,
            label="construction input",
        )
        object.__setattr__(self, "semantic_process_metadata", metadata)

    @property
    def numeric_references(self) -> dict[str, str]:
        return {item.numeric_role: item.reference for item in self.numeric_bindings}

    @property
    def evidence_hash(self) -> str:
        return stable_hash_v1(self.to_dict())

    def to_dict(self) -> dict[str, Any]:
        document = {
            "schema_version": "1.0.0",
            "artifact_type": "construction_input_view_v1",
            "relation_identity": self.relation_identity,
            "source": self.source,
            "source_step_direction": self.source_step_direction,
            "target": self.target,
            "target_response_direction": self.target_response_direction,
            "selected_delay_horizon_seconds": self.selected_delay_horizon_seconds,
            "numeric_bindings": [item.to_dict() for item in self.numeric_bindings],
            "numeric_references": self.numeric_references,
            "approved_evidence_identities": list(
                self.approved_evidence_identities
            ),
            "semantic_process_metadata": thaw_json(self.semantic_process_metadata),
            "raw_hai_included": False,
            "labels_included": False,
            "utility_included": False,
            "candidate_method_performance_included": False,
        }
        _walk_prohibited_keys(
            document["semantic_process_metadata"],
            prohibited=_PROHIBITED_VIEW_KEYS,
            label="construction input",
        )
        return document


@dataclass(frozen=True)
class SyntheticPrivateConstructionEvidenceV1:
    fixture_identity: str
    relation: ConfirmedRelationPrimitiveV1
    numeric_evidence: ApprovedNumericEvidenceBundleV1
    numeric_bindings: tuple[ConstructionNumericBindingV1, ...]
    approved_evidence_identities: tuple[str, ...]
    semantic_process_metadata: Mapping[str, Any]
    synthetic_fake_values_only: bool = True
    real_e1_ledger_source: bool = False

    def __post_init__(self) -> None:
        _require_synthetic(self.fixture_identity, "fixture identity")
        for field_name in ("relation_identity", "source", "target"):
            _require_synthetic(getattr(self.relation, field_name), field_name)
        self.numeric_evidence.assert_matches(self.relation)
        if tuple(item.numeric_role for item in self.numeric_bindings) != _ALL_NUMERIC_ROLES:
            raise TASK039E3PreparationError("synthetic private numeric roles differ")
        for binding in self.numeric_bindings:
            _require_synthetic(binding.evidence_identity, "synthetic evidence identity")
        for identity in self.approved_evidence_identities:
            _require_synthetic(identity, "synthetic approved evidence identity")
        references = {item.numeric_role: item.reference for item in self.numeric_bindings}
        expected = {
            "source_step_threshold": self.numeric_evidence.source_threshold_reference,
            "source_stability_tolerance": self.numeric_evidence.source_stability_reference,
            "target_noise_scale": self.numeric_evidence.target_scale_reference,
        }
        if any(references[role] != value for role, value in expected.items()):
            raise TASK039E3PreparationError("calibrated synthetic references differ")
        if tuple(references[role] for role in WINDOW_NUMERIC_ROLES) != (
            self.numeric_evidence.preregistered_window_constant_references
        ):
            raise TASK039E3PreparationError("window synthetic references differ")
        if self.synthetic_fake_values_only is not True:
            raise TASK039E3PreparationError("fixtures must contain fake values only")
        if self.real_e1_ledger_source is not False:
            raise TASK039E3PreparationError("real E1 ledger source is prohibited")

    def render_view(self) -> ConstructionInputViewV1:
        return ConstructionInputViewV1(
            relation_identity=self.relation.relation_identity,
            source=self.relation.source,
            source_step_direction=self.relation.source_step_direction,
            target=self.relation.target,
            target_response_direction=self.relation.target_response_direction,
            selected_delay_horizon_seconds=(
                self.relation.selected_delay_horizon_seconds
            ),
            numeric_bindings=self.numeric_bindings,
            approved_evidence_identities=self.approved_evidence_identities,
            semantic_process_metadata=self.semantic_process_metadata,
        )


class ConstructionEvidenceRenderingAdapterV1(Protocol):
    """Interface a separately authorized future E1 adapter must implement."""

    def render_view(self) -> ConstructionInputViewV1:
        """Return the bounded construction view without granting execution."""


class ConstructionEvidenceContextV1(ConstructionEvidenceRenderingAdapterV1, Protocol):
    """Future authorized E1 adapter shape used by deterministic orchestration."""

    relation: ConfirmedRelationPrimitiveV1
    numeric_evidence: ApprovedNumericEvidenceBundleV1


def render_main_construction_input_v1(view: ConstructionInputViewV1) -> str:
    return render_main_initial_model_content_v1(view.to_dict())


def render_direct_number_input_v1(view: ConstructionInputViewV1) -> str:
    rendered = render_direct_number_model_content_v1(view.to_dict())
    marker = "\n\nDIRECT_NUMBER_INPUT_JSON\n"
    if marker not in rendered:
        raise TASK039E3PreparationError("direct-number rendering marker differs")
    payload = json.loads(rendered.split(marker, 1)[1])
    bindings = payload.get("numeric_bindings", [])
    references = payload.get("numeric_references", {})
    if any(
        item.get("numeric_role") in CALIBRATED_NUMERIC_ROLES
        for item in bindings
        if isinstance(item, Mapping)
    ) or any(role in references for role in CALIBRATED_NUMERIC_ROLES):
        raise TASK039E3PreparationError("direct-number calibrated binding leaked")
    payload_text = _canonical_json(payload)
    for binding in view.numeric_bindings:
        if binding.numeric_role in CALIBRATED_NUMERIC_ROLES:
            if binding.reference in payload_text:
                raise TASK039E3PreparationError(
                    "direct-number calibrated reference leaked"
                )
    return rendered


@dataclass(frozen=True)
class FrozenProviderRequestV1:
    purpose: str
    request_body: Mapping[str, Any]
    model_visible_content_hash: str
    provider_schema_hash: str
    schema_name: str
    endpoint_family: str = ENDPOINT_FAMILY
    endpoint: str = f"{API_BASE_URL}{API_ENDPOINT}"
    e2_protocol_bundle_hash: str = E2_PROTOCOL_BUNDLE_HASH
    system_prompt: None = None
    developer_prompt: None = None
    authorization_header_included: bool = False
    api_key_included: bool = False

    def __post_init__(self) -> None:
        if self.purpose not in {
            "main_initial",
            "t2_followup",
            "direct_number",
            "capability_probe",
        }:
            raise TASK039E3PreparationError("request purpose differs")
        body = freeze_json(self.request_body)
        object.__setattr__(self, "request_body", body)
        _require_hash(self.model_visible_content_hash, "model content hash")
        _require_hash(self.provider_schema_hash, "provider schema hash")
        _require_hash(self.e2_protocol_bundle_hash, "E2 protocol bundle hash")
        if self.endpoint_family != "chat_completions" or self.endpoint != (
            "https://api.openai.com/v1/chat/completions"
        ):
            raise TASK039E3PreparationError("request endpoint differs")
        if self.system_prompt is not None or self.developer_prompt is not None:
            raise TASK039E3PreparationError(
                "E2 freezes the scientific instruction in the user content"
            )
        if self.authorization_header_included is not False or self.api_key_included is not False:
            raise TASK039E3PreparationError("request artifact contains credentials")
        _walk_prohibited_keys(
            body,
            prohibited=_HASH_FIELDS,
            label="canonical request",
        )
        expected = {
            "model": EXACT_MODEL,
            "reasoning_effort": "none",
            "temperature": 0.7,
            "top_p": 1.0,
            "max_completion_tokens": 1024,
            "stream": False,
            "store": False,
        }
        if any(body.get(name) != value for name, value in expected.items()):
            raise TASK039E3PreparationError("request sampling differs")
        if body.get("messages") != (
            MappingProxyType(
                {
                    "role": "user",
                    "content": body["messages"][0]["content"],
                }
            ),
        ):
            raise TASK039E3PreparationError("request message roles differ")
        response_format = body.get("response_format")
        if not isinstance(response_format, Mapping):
            raise TASK039E3PreparationError("strict response format is missing")
        schema_contract = response_format.get("json_schema")
        if (
            response_format.get("type") != "json_schema"
            or not isinstance(schema_contract, Mapping)
            or schema_contract.get("strict") is not True
        ):
            raise TASK039E3PreparationError("strict structured response differs")

    @property
    def request_hash(self) -> str:
        return stable_hash_v1(self.to_dict())

    def to_dict(self) -> dict[str, Any]:
        return {
            "artifact_type": "frozen_provider_request_v1",
            "purpose": self.purpose,
            "endpoint_family": self.endpoint_family,
            "endpoint": self.endpoint,
            "e2_protocol_bundle_hash": self.e2_protocol_bundle_hash,
            "system_prompt": self.system_prompt,
            "developer_prompt": self.developer_prompt,
            "request_body": thaw_json(self.request_body),
            "model_visible_content_hash": self.model_visible_content_hash,
            "provider_schema_hash": self.provider_schema_hash,
            "schema_name": self.schema_name,
        }


def _build_request(
    *, purpose: str, content: str, schema: Mapping[str, Any], schema_name: str
) -> FrozenProviderRequestV1:
    body = build_chat_completions_request_body_v1(
        model_visible_content=content,
        provider_schema=schema,
        schema_name=schema_name,
    )
    return FrozenProviderRequestV1(
        purpose=purpose,
        request_body=body,
        model_visible_content_hash=_text_hash(content),
        provider_schema_hash=stable_hash_v1(schema),
        schema_name=schema_name,
    )


def build_main_request_v1(view: ConstructionInputViewV1) -> FrozenProviderRequestV1:
    return _build_request(
        purpose="main_initial",
        content=render_main_construction_input_v1(view),
        schema=MAIN_PROVIDER_SCHEMA_V1,
        schema_name="provider_proposal_core_v1",
    )


def build_t2_followup_request_v1(
    *,
    view: ConstructionInputViewV1,
    verifier_issue_codes: Sequence[str],
    affected_fields: Sequence[str],
    previous_proposal_hash: str,
    retrieved_evidence: Mapping[str, Any] | None,
) -> FrozenProviderRequestV1:
    content = render_t2_followup_model_content_v1(
        original_view=view.to_dict(),
        verifier_issue_codes=verifier_issue_codes,
        affected_fields=affected_fields,
        previous_proposal_hash=previous_proposal_hash,
        retrieved_evidence=retrieved_evidence,
    )
    return _build_request(
        purpose="t2_followup",
        content=content,
        schema=MAIN_PROVIDER_SCHEMA_V1,
        schema_name="provider_proposal_core_v1",
    )


def build_direct_number_request_v1(
    view: ConstructionInputViewV1,
) -> FrozenProviderRequestV1:
    return _build_request(
        purpose="direct_number",
        content=render_direct_number_input_v1(view),
        schema=DIRECT_NUMBER_PROVIDER_SCHEMA_V1,
        schema_name="direct_number_response_v1",
    )


_CAPABILITY_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "additionalProperties": False,
    "required": ["model_snapshot", "structured_output_supported"],
    "properties": {
        "model_snapshot": {"type": "string"},
        "structured_output_supported": {"type": "boolean"},
    },
}


def build_capability_probe_request_v1() -> FrozenProviderRequestV1:
    content = (
        "SYNTHETIC_CAPABILITY_CHECK\nReturn the exact model snapshot and whether "
        "strict structured output was honored. No scientific evidence is supplied."
    )
    return _build_request(
        purpose="capability_probe",
        content=content,
        schema=_CAPABILITY_SCHEMA,
        schema_name="synthetic_capability_check_v1",
    )


@dataclass(frozen=True)
class MockProviderResponseV1:
    response_present: bool
    outcome: str
    status_code: int | None
    model: str | None
    content: str | None
    refusal: bool = False
    finish_reason: str | None = None
    response_id: str | None = None
    token_usage: Mapping[str, int] | None = None

    def __post_init__(self) -> None:
        if self.response_present:
            if self.status_code != 200:
                raise TASK039E3PreparationError("present mock response must be HTTP 200")
            if self.model is None or self.response_id is None:
                raise TASK039E3PreparationError("mock response metadata is incomplete")
        elif self.content is not None or self.refusal:
            raise TASK039E3PreparationError("absent response cannot carry content")
        if self.token_usage is not None:
            usage = freeze_json(self.token_usage)
            object.__setattr__(self, "token_usage", usage)

    @property
    def response_hash(self) -> str | None:
        if not self.response_present:
            return None
        return stable_hash_v1(
            {
                "outcome": self.outcome,
                "status_code": self.status_code,
                "model": self.model,
                "content": self.content,
                "refusal": self.refusal,
                "finish_reason": self.finish_reason,
                "response_id": self.response_id,
                "token_usage": thaw_json(self.token_usage),
            }
        )


@dataclass(frozen=True)
class MockProviderEventV1:
    scenario: str
    payload: Mapping[str, Any] | None = None

    def __post_init__(self) -> None:
        allowed = {
            "valid_proposal",
            "valid_direct_number",
            "schema_invalid_response",
            "provider_refusal",
            "incomplete_response",
            "http_429",
            "http_500",
            "no_response_timeout",
            "connection_failure",
            "http_400",
            "http_401",
            "http_403",
            "capability_supported",
            "snapshot_unavailable",
            "malformed_capability_response",
        }
        if self.scenario not in allowed:
            raise TASK039E3PreparationError("mock provider scenario is not frozen")
        if self.payload is not None:
            object.__setattr__(self, "payload", freeze_json(self.payload))

    def response(self, sequence_number: int) -> MockProviderResponseV1:
        response_id = f"SYNTHETIC_RESPONSE_{sequence_number:04d}"
        if self.scenario in {
            "valid_proposal",
            "valid_direct_number",
            "capability_supported",
            "snapshot_unavailable",
        }:
            if self.payload is None:
                raise TASK039E3PreparationError("mock success scenario requires payload")
            return MockProviderResponseV1(
                response_present=True,
                outcome=self.scenario,
                status_code=200,
                model=EXACT_MODEL,
                content=_canonical_json(self.payload),
                finish_reason="stop",
                response_id=response_id,
                token_usage=MappingProxyType(
                    {"prompt_tokens": 11, "completion_tokens": 7}
                ),
            )
        if self.scenario == "schema_invalid_response":
            return MockProviderResponseV1(
                True,
                self.scenario,
                200,
                EXACT_MODEL,
                '{"SYNTHETIC_WRONG_FIELD":true}',
                finish_reason="stop",
                response_id=response_id,
            )
        if self.scenario == "provider_refusal":
            return MockProviderResponseV1(
                True,
                self.scenario,
                200,
                EXACT_MODEL,
                None,
                refusal=True,
                finish_reason="stop",
                response_id=response_id,
            )
        if self.scenario == "incomplete_response":
            content = _canonical_json(self.payload) if self.payload else "{}"
            return MockProviderResponseV1(
                True,
                self.scenario,
                200,
                EXACT_MODEL,
                content,
                finish_reason="length",
                response_id=response_id,
            )
        if self.scenario == "malformed_capability_response":
            return MockProviderResponseV1(
                True,
                self.scenario,
                200,
                EXACT_MODEL,
                "{",
                finish_reason="stop",
                response_id=response_id,
            )
        absent = {
            "http_429": (429, "http_429"),
            "http_500": (500, "http_5xx"),
            "no_response_timeout": (None, "timeout_before_response"),
            "connection_failure": (None, "connection_failure"),
            "http_400": (400, "http_400"),
            "http_401": (401, "http_401"),
            "http_403": (403, "http_403"),
        }
        status_code, outcome = absent[self.scenario]
        return MockProviderResponseV1(
            response_present=False,
            outcome=outcome,
            status_code=status_code,
            model=None,
            content=None,
        )


class ProviderTransportV1(Protocol):
    def send(self, request: FrozenProviderRequestV1) -> MockProviderResponseV1:
        """Return one transport event for an immutable request."""


class MockProviderTransportV1:
    """Deterministic in-memory transport; it never opens a network resource."""

    def __init__(self, events: Sequence[MockProviderEventV1]) -> None:
        if not events:
            raise TASK039E3PreparationError("mock transport requires scripted events")
        self._events = tuple(events)
        self._cursor = 0
        self._request_hashes: list[str] = []

    @property
    def calls(self) -> int:
        return self._cursor

    @property
    def request_hashes(self) -> tuple[str, ...]:
        return tuple(self._request_hashes)

    def send(self, request: FrozenProviderRequestV1) -> MockProviderResponseV1:
        if not isinstance(request, FrozenProviderRequestV1):
            raise TASK039E3PreparationError("mock transport requires frozen request")
        if self._cursor >= len(self._events):
            raise TASK039E3PreparationError("mock transport script exhausted")
        event = self._events[self._cursor]
        self._cursor += 1
        self._request_hashes.append(request.request_hash)
        return event.response(self._cursor)


@dataclass(frozen=True)
class ParsedProviderProposalV1:
    parse_status: str
    proposal_core: ProviderProposalCoreV1 | None
    response_consumed_scientific_call: bool = True

    def __post_init__(self) -> None:
        if self.parse_status not in {
            "valid_structured",
            "provider_refusal",
            "incomplete_response",
            "schema_parse_failure",
        }:
            raise TASK039E3PreparationError("provider parse status differs")
        if (self.parse_status == "valid_structured") != (
            self.proposal_core is not None
        ):
            raise TASK039E3PreparationError("provider parse/core contract differs")
        if self.response_consumed_scientific_call is not True:
            raise TASK039E3PreparationError("received responses consume their call")


def parse_provider_proposal_response_v1(
    response: MockProviderResponseV1,
) -> ParsedProviderProposalV1:
    if not response.response_present:
        raise TASK039E3PreparationError("parser requires a received response")
    if response.refusal:
        return ParsedProviderProposalV1("provider_refusal", None)
    if response.finish_reason != "stop" or response.content is None:
        return ParsedProviderProposalV1("incomplete_response", None)
    try:
        document = json.loads(response.content)
        if not isinstance(document, dict) or set(document) != set(
            MAIN_PROVIDER_SCHEMA_V1["required"]
        ):
            raise ValueError("provider proposal closure differs")
        core = ProviderProposalCoreV1(
            dsl_family=document["dsl_family"],
            relation_identity=document["relation_identity"],
            source=document["source"],
            source_step_direction=document["source_step_direction"],
            target=document["target"],
            target_response_direction=document["target_response_direction"],
            selected_delay_horizon_seconds=document[
                "selected_delay_horizon_seconds"
            ],
            source_threshold_reference=document["source_threshold_reference"],
            source_stability_reference=document["source_stability_reference"],
            target_scale_reference=document["target_scale_reference"],
            window_constant_references=document["window_constant_references"],
            variables=tuple(document["variables"]),
            runtime_logic_family=document["runtime_logic_family"],
        )
    except (KeyError, TypeError, ValueError):
        return ParsedProviderProposalV1("schema_parse_failure", None)
    return ParsedProviderProposalV1("valid_structured", core)


@dataclass(frozen=True)
class ParsedDirectNumberV1:
    parse_status: str
    values: Mapping[str, float] | None

    def __post_init__(self) -> None:
        if self.parse_status not in {
            "valid_structured",
            "provider_refusal",
            "incomplete_response",
            "schema_parse_failure",
            "nonfinite_response",
        }:
            raise TASK039E3PreparationError("direct-number parse status differs")
        if (self.parse_status == "valid_structured") != (self.values is not None):
            raise TASK039E3PreparationError("direct-number value/status differs")
        if self.values is not None:
            object.__setattr__(self, "values", freeze_json(self.values))


def parse_direct_number_response_v1(
    response: MockProviderResponseV1,
) -> ParsedDirectNumberV1:
    if not response.response_present:
        raise TASK039E3PreparationError("direct parser requires a response")
    if response.refusal:
        return ParsedDirectNumberV1("provider_refusal", None)
    if response.finish_reason != "stop" or response.content is None:
        return ParsedDirectNumberV1("incomplete_response", None)
    try:
        document = json.loads(response.content)
    except (TypeError, json.JSONDecodeError):
        return ParsedDirectNumberV1("schema_parse_failure", None)
    if not isinstance(document, dict) or set(document) != set(CALIBRATED_NUMERIC_ROLES):
        return ParsedDirectNumberV1("schema_parse_failure", None)
    values: dict[str, float] = {}
    for role in CALIBRATED_NUMERIC_ROLES:
        value = document[role]
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return ParsedDirectNumberV1("schema_parse_failure", None)
        if not math.isfinite(float(value)):
            return ParsedDirectNumberV1("nonfinite_response", None)
        values[role] = float(value)
    return ParsedDirectNumberV1("valid_structured", values)


@dataclass(frozen=True)
class ParsedCapabilityProbeV1:
    status: str
    exact_snapshot_returned: bool
    structured_output_supported: bool

    def __post_init__(self) -> None:
        if self.status not in {"pass", "block_snapshot", "block_malformed"}:
            raise TASK039E3PreparationError("capability parse status differs")
        if self.status == "pass" and not (
            self.exact_snapshot_returned and self.structured_output_supported
        ):
            raise TASK039E3PreparationError("capability PASS contract differs")


def parse_capability_response_v1(
    response: MockProviderResponseV1,
) -> ParsedCapabilityProbeV1:
    if not response.response_present or response.refusal or response.content is None:
        return ParsedCapabilityProbeV1("block_malformed", False, False)
    try:
        document = json.loads(response.content)
    except (TypeError, json.JSONDecodeError):
        return ParsedCapabilityProbeV1("block_malformed", False, False)
    if not isinstance(document, dict) or set(document) != {
        "model_snapshot",
        "structured_output_supported",
    }:
        return ParsedCapabilityProbeV1("block_malformed", False, False)
    snapshot = document["model_snapshot"]
    structured = document["structured_output_supported"]
    if not isinstance(snapshot, str) or type(structured) is not bool:
        return ParsedCapabilityProbeV1("block_malformed", False, False)
    if snapshot != EXACT_MODEL or not structured:
        return ParsedCapabilityProbeV1(
            "block_snapshot", snapshot == EXACT_MODEL, structured
        )
    return ParsedCapabilityProbeV1("pass", True, True)


@dataclass(frozen=True)
class ProviderCallSlotV1:
    relation_schedule_index: int | None
    relation_binding_hash: str
    arm: str
    arm_local_call_number: int
    scientific: bool
    schedule_hash: str = EXECUTION_SCHEDULE_HASH

    def __post_init__(self) -> None:
        _require_hash(self.relation_binding_hash, "relation binding hash")
        _require_hash(self.schedule_hash, "schedule hash")
        if self.arm == "CAPABILITY":
            if (
                self.relation_schedule_index is not None
                or self.arm_local_call_number != 1
                or self.scientific is not False
            ):
                raise TASK039E3PreparationError("capability slot identity differs")
            return
        if self.arm not in {"T1", "T1-B", "T2", "T1-DIRECT-NUMBER"}:
            raise TASK039E3PreparationError("scientific slot arm differs")
        if (
            isinstance(self.relation_schedule_index, bool)
            or not isinstance(self.relation_schedule_index, int)
            or not 0 <= self.relation_schedule_index < 42
            or self.scientific is not True
        ):
            raise TASK039E3PreparationError("scientific slot relation differs")
        allowed_calls = {
            "T1": {1},
            "T1-B": {1, 2, 3},
            "T2": {1, 2, 3},
            "T1-DIRECT-NUMBER": {1},
        }
        if self.arm_local_call_number not in allowed_calls[self.arm]:
            raise TASK039E3PreparationError("scientific slot call differs")

    @property
    def slot_hash(self) -> str:
        return stable_hash_v1(self.to_dict())

    def to_dict(self) -> dict[str, Any]:
        return {
            "artifact_type": "scientific_provider_call_slot_v1",
            "relation_schedule_index": self.relation_schedule_index,
            "relation_binding_hash": self.relation_binding_hash,
            "arm": self.arm,
            "arm_local_call_number": self.arm_local_call_number,
            "scientific": self.scientific,
            "schedule_hash": self.schedule_hash,
        }


def build_mock_336_slot_schedule_v1(
    relation_binding_hashes: Sequence[str],
) -> tuple[ProviderCallSlotV1, ...]:
    if len(relation_binding_hashes) != 42 or len(set(relation_binding_hashes)) != 42:
        raise TASK039E3PreparationError("336-slot schedule requires 42 relations")
    pattern = (
        ("T1", 1),
        ("T1-B", 1),
        ("T1-B", 2),
        ("T1-B", 3),
        ("T2", 1),
        ("T2", 2),
        ("T2", 3),
        ("T1-DIRECT-NUMBER", 1),
    )
    slots = tuple(
        ProviderCallSlotV1(index, relation_hash, arm, call_number, True)
        for index, relation_hash in enumerate(relation_binding_hashes)
        for arm, call_number in pattern
    )
    if len(slots) != MAXIMUM_SCIENTIFIC_SLOTS or len(
        {slot.slot_hash for slot in slots}
    ) != MAXIMUM_SCIENTIFIC_SLOTS:
        raise TASK039E3PreparationError("scientific slot accounting differs")
    return slots


@dataclass(frozen=True)
class ProviderTransportAttemptV1:
    attempt_number: int
    outcome: str
    response_present: bool
    status_code: int | None
    retry_eligible: bool
    planned_retry_delay_seconds: int | None

    def __post_init__(self) -> None:
        if self.attempt_number not in {1, 2, 3}:
            raise TASK039E3PreparationError("transport attempt number differs")
        if self.retry_eligible != (
            not self.response_present and self.outcome in _TRANSPORT_RETRYABLE
        ):
            raise TASK039E3PreparationError("transport retry classification differs")
        expected_delay = (
            TRANSPORT_RETRY_DELAYS_SECONDS[self.attempt_number - 1]
            if self.retry_eligible
            and self.attempt_number <= MAXIMUM_TRANSPORT_RETRIES
            else None
        )
        if self.planned_retry_delay_seconds != expected_delay:
            raise TASK039E3PreparationError("transport retry delay differs")

    def to_dict(self) -> dict[str, Any]:
        return {
            "attempt_number": self.attempt_number,
            "outcome": self.outcome,
            "response_present": self.response_present,
            "status_code": self.status_code,
            "retry_eligible": self.retry_eligible,
            "planned_retry_delay_seconds": self.planned_retry_delay_seconds,
        }


@dataclass(frozen=True)
class ProviderCallRecordV1:
    sequence_index: int
    previous_record_hash: str | None
    slot: ProviderCallSlotV1
    request_hash: str
    response_present: bool
    provider_response_metadata: Mapping[str, Any]
    transport_attempts: tuple[ProviderTransportAttemptV1, ...]
    parse_status: str
    proposal_core_hash: str | None
    terminal_slot_state: str
    api_key_stored: bool = False
    authorization_header_stored: bool = False
    chain_of_thought_stored: bool = False

    def __post_init__(self) -> None:
        if self.sequence_index < 0:
            raise TASK039E3PreparationError("call record sequence differs")
        if self.previous_record_hash is not None:
            _require_hash(self.previous_record_hash, "previous record hash")
        _require_hash(self.request_hash, "request hash")
        if self.proposal_core_hash is not None:
            _require_hash(self.proposal_core_hash, "proposal core hash")
        if not self.transport_attempts or len(self.transport_attempts) > 3:
            raise TASK039E3PreparationError("transport attempt custody differs")
        if self.terminal_slot_state not in _TERMINAL_SLOT_STATES:
            raise TASK039E3PreparationError("terminal slot state differs")
        metadata = freeze_json(self.provider_response_metadata)
        _walk_prohibited_keys(metadata, prohibited=_HASH_FIELDS, label="call ledger")
        object.__setattr__(self, "provider_response_metadata", metadata)
        for field_name in (
            "api_key_stored",
            "authorization_header_stored",
            "chain_of_thought_stored",
        ):
            if getattr(self, field_name) is not False:
                raise TASK039E3PreparationError(f"{field_name} must remain false")

    def _content_dict(self) -> dict[str, Any]:
        return {
            "sequence_index": self.sequence_index,
            "previous_record_hash": self.previous_record_hash,
            "slot": self.slot.to_dict(),
            "slot_hash": self.slot.slot_hash,
            "request_hash": self.request_hash,
            "response_present": self.response_present,
            "provider_response_metadata": thaw_json(
                self.provider_response_metadata
            ),
            "transport_attempts": [item.to_dict() for item in self.transport_attempts],
            "parse_status": self.parse_status,
            "proposal_core_hash": self.proposal_core_hash,
            "terminal_slot_state": self.terminal_slot_state,
            "api_key_stored": self.api_key_stored,
            "authorization_header_stored": self.authorization_header_stored,
            "chain_of_thought_stored": self.chain_of_thought_stored,
        }

    @property
    def record_hash(self) -> str:
        return stable_hash_v1(self._content_dict())

    def to_dict(self) -> dict[str, Any]:
        document = self._content_dict()
        document["record_hash"] = self.record_hash
        return document


class ProviderCallLedgerV1:
    """Private in-memory append-only custody for provider slots."""

    def __init__(self) -> None:
        self._records: list[ProviderCallRecordV1] = []
        self._slot_hashes: set[str] = set()

    @property
    def records(self) -> tuple[ProviderCallRecordV1, ...]:
        return tuple(self._records)

    @property
    def ledger_hash(self) -> str:
        return stable_hash_v1(
            {
                "artifact_type": "provider_call_ledger_v1",
                "record_hashes": [item.record_hash for item in self._records],
            }
        )

    def append(
        self,
        *,
        slot: ProviderCallSlotV1,
        request_hash: str,
        response_present: bool,
        provider_response_metadata: Mapping[str, Any],
        transport_attempts: Sequence[ProviderTransportAttemptV1],
        parse_status: str,
        proposal_core_hash: str | None,
        terminal_slot_state: str,
    ) -> ProviderCallRecordV1:
        if slot.slot_hash in self._slot_hashes:
            raise TASK039E3PreparationError("provider slot was already recorded")
        record = ProviderCallRecordV1(
            sequence_index=len(self._records),
            previous_record_hash=(
                self._records[-1].record_hash if self._records else None
            ),
            slot=slot,
            request_hash=request_hash,
            response_present=response_present,
            provider_response_metadata=provider_response_metadata,
            transport_attempts=tuple(transport_attempts),
            parse_status=parse_status,
            proposal_core_hash=proposal_core_hash,
            terminal_slot_state=terminal_slot_state,
        )
        self._records.append(record)
        self._slot_hashes.add(slot.slot_hash)
        return record


@dataclass(frozen=True)
class ExecutionFailureReceiptV1:
    failure_reason: str
    failed_slot_hash: str
    completed_slot_record_hashes: tuple[str, ...]
    provider_call_ledger_hash: str
    status: str = "failed_closed"
    full_run_aborted: bool = True
    relation_skipping_allowed: bool = False
    automatic_resume_authority: bool = False
    automatic_rerun_policy: bool = False

    def __post_init__(self) -> None:
        _require_hash(self.failed_slot_hash, "failed slot hash")
        _require_hash(self.provider_call_ledger_hash, "provider ledger hash")
        for value in self.completed_slot_record_hashes:
            _require_hash(value, "completed slot record hash")
        if self.status != "failed_closed" or self.full_run_aborted is not True:
            raise TASK039E3PreparationError("failure receipt must fail closed")
        for field_name in (
            "relation_skipping_allowed",
            "automatic_resume_authority",
            "automatic_rerun_policy",
        ):
            if getattr(self, field_name) is not False:
                raise TASK039E3PreparationError(f"{field_name} must remain false")

    @property
    def artifact_hash(self) -> str:
        return stable_hash_v1(self._content_dict())

    def _content_dict(self) -> dict[str, Any]:
        return {
            "artifact_type": "execution_failure_receipt_v1",
            "failure_reason": self.failure_reason,
            "failed_slot_hash": self.failed_slot_hash,
            "completed_slot_record_hashes": list(
                self.completed_slot_record_hashes
            ),
            "provider_call_ledger_hash": self.provider_call_ledger_hash,
            "status": self.status,
            "full_run_aborted": self.full_run_aborted,
            "relation_skipping_allowed": self.relation_skipping_allowed,
            "automatic_resume_authority": self.automatic_resume_authority,
            "automatic_rerun_policy": self.automatic_rerun_policy,
        }

    def to_dict(self) -> dict[str, Any]:
        document = self._content_dict()
        document["artifact_hash"] = self.artifact_hash
        return document


class ScientificRunAbortV1(TASK039E3PreparationError):
    def __init__(self, receipt: ExecutionFailureReceiptV1) -> None:
        super().__init__(receipt.failure_reason)
        self.receipt = receipt


@dataclass(frozen=True)
class SlotExecutionResultV1:
    record: ProviderCallRecordV1
    parsed_proposal: ParsedProviderProposalV1 | None = None
    parsed_direct_number: ParsedDirectNumberV1 | None = None
    parsed_capability: ParsedCapabilityProbeV1 | None = None


def _failure_receipt(
    *, ledger: ProviderCallLedgerV1, slot: ProviderCallSlotV1, reason: str
) -> ExecutionFailureReceiptV1:
    return ExecutionFailureReceiptV1(
        failure_reason=reason,
        failed_slot_hash=slot.slot_hash,
        completed_slot_record_hashes=tuple(
            record.record_hash for record in ledger.records
        ),
        provider_call_ledger_hash=ledger.ledger_hash,
    )


def execute_mock_provider_slot_v1(
    *,
    slot: ProviderCallSlotV1,
    request: FrozenProviderRequestV1,
    transport: ProviderTransportV1,
    ledger: ProviderCallLedgerV1,
    parse_kind: str,
) -> SlotExecutionResultV1:
    if parse_kind not in {"proposal", "direct_number", "capability"}:
        raise TASK039E3PreparationError("slot parse kind differs")
    if not isinstance(transport, MockProviderTransportV1):
        raise TASK039E3PreparationError(
            "TASK-039E3-PREP accepts MockProviderTransportV1 only"
        )
    attempts: list[ProviderTransportAttemptV1] = []
    response: MockProviderResponseV1 | None = None
    for attempt_number in range(1, MAXIMUM_TRANSPORT_RETRIES + 2):
        response = transport.send(request)
        retry_eligible = (
            not response.response_present and response.outcome in _TRANSPORT_RETRYABLE
        )
        attempts.append(
            ProviderTransportAttemptV1(
                attempt_number=attempt_number,
                outcome=response.outcome,
                response_present=response.response_present,
                status_code=response.status_code,
                retry_eligible=retry_eligible,
                planned_retry_delay_seconds=(
                    TRANSPORT_RETRY_DELAYS_SECONDS[attempt_number - 1]
                    if retry_eligible
                    and attempt_number <= MAXIMUM_TRANSPORT_RETRIES
                    else None
                ),
            )
        )
        if response.response_present:
            break
        if retry_eligible and attempt_number <= MAXIMUM_TRANSPORT_RETRIES:
            continue
        ledger.append(
            slot=slot,
            request_hash=request.request_hash,
            response_present=False,
            provider_response_metadata={
                "outcome": response.outcome,
                "status_code": response.status_code,
                "response_hash": None,
            },
            transport_attempts=attempts,
            parse_status="transport_failure",
            proposal_core_hash=None,
            terminal_slot_state="transport_exhausted",
        )
        raise ScientificRunAbortV1(
            _failure_receipt(
                ledger=ledger,
                slot=slot,
                reason=(
                    "transport_exhausted_full_run_failure"
                    if retry_eligible
                    else "non_retryable_transport_failure_full_run_failure"
                ),
            )
        )
    if response is None or not response.response_present:
        raise TASK039E3PreparationError("mock transport loop ended without response")

    proposal: ParsedProviderProposalV1 | None = None
    direct: ParsedDirectNumberV1 | None = None
    capability: ParsedCapabilityProbeV1 | None = None
    core_hash: str | None = None
    if parse_kind == "proposal":
        proposal = parse_provider_proposal_response_v1(response)
        parse_status = proposal.parse_status
        if proposal.proposal_core is not None:
            core_hash = proposal.proposal_core.proposal_core_hash
    elif parse_kind == "direct_number":
        direct = parse_direct_number_response_v1(response)
        parse_status = direct.parse_status
    else:
        capability = parse_capability_response_v1(response)
        parse_status = capability.status
    terminal_state = (
        "completed_structured"
        if parse_status in {"valid_structured", "pass"}
        else "completed_refusal"
        if parse_status == "provider_refusal"
        else "completed_invalid_response"
    )
    record = ledger.append(
        slot=slot,
        request_hash=request.request_hash,
        response_present=True,
        provider_response_metadata={
            "outcome": response.outcome,
            "status_code": response.status_code,
            "model": response.model,
            "response_id": response.response_id,
            "finish_reason": response.finish_reason,
            "response_hash": response.response_hash,
            "token_usage": thaw_json(response.token_usage),
        },
        transport_attempts=attempts,
        parse_status=parse_status,
        proposal_core_hash=core_hash,
        terminal_slot_state=terminal_state,
    )
    return SlotExecutionResultV1(record, proposal, direct, capability)


@dataclass(frozen=True)
class CapabilityProbeResultV1:
    state: str
    slot_record_hash: str
    frozen_e2_binding_hash: str
    exact_snapshot_returned: bool
    structured_output_supported: bool
    mock_probe_executed: bool = True
    live_probe_executed: bool = False
    frozen_configuration_modified: bool = False
    provider_contacted: bool = False

    def __post_init__(self) -> None:
        if self.state not in {"PASS", "BLOCK"}:
            raise TASK039E3PreparationError("capability state differs")
        for value, name in (
            (self.slot_record_hash, "slot record hash"),
            (self.frozen_e2_binding_hash, "E2 binding hash"),
        ):
            _require_hash(value, name)
        if self.state == "PASS" and not (
            self.exact_snapshot_returned and self.structured_output_supported
        ):
            raise TASK039E3PreparationError("capability PASS differs")
        if self.mock_probe_executed is not True:
            raise TASK039E3PreparationError("mock capability probe must execute")
        for field_name in (
            "live_probe_executed",
            "frozen_configuration_modified",
            "provider_contacted",
        ):
            if getattr(self, field_name) is not False:
                raise TASK039E3PreparationError(f"{field_name} must remain false")


class CapabilityProbeRunnerV1:
    fixture_identity = "SYNTHETIC_CAPABILITY_CHECK"

    def run(
        self,
        *,
        transport: ProviderTransportV1,
        ledger: ProviderCallLedgerV1,
    ) -> CapabilityProbeResultV1:
        slot = ProviderCallSlotV1(
            relation_schedule_index=None,
            relation_binding_hash=stable_hash_v1(
                {"fixture_identity": self.fixture_identity}
            ),
            arm="CAPABILITY",
            arm_local_call_number=1,
            scientific=False,
        )
        try:
            result = execute_mock_provider_slot_v1(
                slot=slot,
                request=build_capability_probe_request_v1(),
                transport=transport,
                ledger=ledger,
                parse_kind="capability",
            )
        except ScientificRunAbortV1:
            return CapabilityProbeResultV1(
                state="BLOCK",
                slot_record_hash=ledger.records[-1].record_hash,
                frozen_e2_binding_hash=FROZEN_E2_BINDING.artifact_hash,
                exact_snapshot_returned=False,
                structured_output_supported=False,
            )
        parsed = result.parsed_capability
        if parsed is None:
            raise TASK039E3PreparationError("capability parser result missing")
        return CapabilityProbeResultV1(
            state="PASS" if parsed.status == "pass" else "BLOCK",
            slot_record_hash=result.record.record_hash,
            frozen_e2_binding_hash=FROZEN_E2_BINDING.artifact_hash,
            exact_snapshot_returned=parsed.exact_snapshot_returned,
            structured_output_supported=parsed.structured_output_supported,
        )


@dataclass(frozen=True)
class FutureLiveRunnerBoundaryV1:
    required_authorization_contract: str = "TASK039E3AuthorizationV1"
    clean_execution_code_commit_required: bool = True
    exact_e2_bundle_required: bool = True
    exact_e1_private_ledger_hash_required: bool = True
    capability_probe_pass_required: bool = True
    live_runner_present: bool = False
    execution_authorized: bool = False

    def __post_init__(self) -> None:
        if self.required_authorization_contract != "TASK039E3AuthorizationV1":
            raise TASK039E3PreparationError("future authorization contract differs")
        for field_name in (
            "clean_execution_code_commit_required",
            "exact_e2_bundle_required",
            "exact_e1_private_ledger_hash_required",
            "capability_probe_pass_required",
        ):
            if getattr(self, field_name) is not True:
                raise TASK039E3PreparationError(f"{field_name} must be true")
        for field_name in ("live_runner_present", "execution_authorized"):
            if getattr(self, field_name) is not False:
                raise TASK039E3PreparationError(f"{field_name} must remain false")


@dataclass(frozen=True)
class TASK039E3PreparationReceiptV1:
    status: str = STATUS
    frozen_e2_configuration_bound: bool = True
    mock_provider_prepared: bool = True
    live_provider_locked: bool = True
    capability_probe_harness_prepared: bool = True
    orchestration_harness_prepared: bool = True
    custody_and_metrics_prepared: bool = True
    real_e1_private_evidence_accessed: bool = False
    provider_contacted: bool = False
    credential_accessed: bool = False
    capability_probe_executed_live: bool = False
    llm_called: bool = False
    real_proposal_generated: bool = False
    rule_v2_authorized: bool = False
    runtime_authority: bool = False

    def __post_init__(self) -> None:
        if self.status != STATUS:
            raise TASK039E3PreparationError("preparation receipt status differs")
        for field_name in (
            "frozen_e2_configuration_bound",
            "mock_provider_prepared",
            "live_provider_locked",
            "capability_probe_harness_prepared",
            "orchestration_harness_prepared",
            "custody_and_metrics_prepared",
        ):
            if getattr(self, field_name) is not True:
                raise TASK039E3PreparationError(f"{field_name} must be true")
        for field_name in (
            "real_e1_private_evidence_accessed",
            "provider_contacted",
            "credential_accessed",
            "capability_probe_executed_live",
            "llm_called",
            "real_proposal_generated",
            "rule_v2_authorized",
            "runtime_authority",
        ):
            if getattr(self, field_name) is not False:
                raise TASK039E3PreparationError(f"{field_name} must remain false")

    def _content_dict(self) -> dict[str, Any]:
        return {
            "artifact_type": "task039e3_preparation_receipt_v1",
            "status": self.status,
            "frozen_e2_configuration_bound": self.frozen_e2_configuration_bound,
            "mock_provider_prepared": self.mock_provider_prepared,
            "live_provider_locked": self.live_provider_locked,
            "capability_probe_harness_prepared": (
                self.capability_probe_harness_prepared
            ),
            "orchestration_harness_prepared": self.orchestration_harness_prepared,
            "custody_and_metrics_prepared": self.custody_and_metrics_prepared,
            "real_e1_private_evidence_accessed": (
                self.real_e1_private_evidence_accessed
            ),
            "provider_contacted": self.provider_contacted,
            "credential_accessed": self.credential_accessed,
            "capability_probe_executed_live": self.capability_probe_executed_live,
            "llm_called": self.llm_called,
            "real_proposal_generated": self.real_proposal_generated,
            "rule_v2_authorized": self.rule_v2_authorized,
            "runtime_authority": self.runtime_authority,
        }

    @property
    def artifact_hash(self) -> str:
        return stable_hash_v1(self._content_dict())

    def to_dict(self) -> dict[str, Any]:
        document = self._content_dict()
        document["artifact_hash"] = self.artifact_hash
        return document


def open_live_provider_transport_v1(*_args: Any, **_kwargs: Any) -> None:
    raise TASK039E3PreparationError(
        "live provider transport is locked; an additive authorized runner is required"
    )


def read_openai_api_key_v1(*_args: Any, **_kwargs: Any) -> None:
    raise TASK039E3PreparationError(
        "credential access is impossible in TASK-039E3-PREP"
    )


def instantiate_live_provider_request_v1(*_args: Any, **_kwargs: Any) -> None:
    raise TASK039E3PreparationError(
        "live provider request instantiation is impossible in TASK-039E3-PREP"
    )


def assert_preparation_boundary_v1(
    *,
    real_e1_private_evidence_accessed: bool = False,
    provider_contacted: bool = False,
    credential_accessed: bool = False,
    capability_probe_executed_live: bool = False,
    llm_called: bool = False,
    real_proposal_generated: bool = False,
    rule_v2_authorized: bool = False,
    runtime_authority: bool = False,
) -> str:
    boundaries = {
        "real_e1_private_evidence_accessed": real_e1_private_evidence_accessed,
        "provider_contacted": provider_contacted,
        "credential_accessed": credential_accessed,
        "capability_probe_executed_live": capability_probe_executed_live,
        "llm_called": llm_called,
        "real_proposal_generated": real_proposal_generated,
        "rule_v2_authorized": rule_v2_authorized,
        "runtime_authority": runtime_authority,
    }
    for name, value in boundaries.items():
        if value is not False:
            raise TASK039E3PreparationError(f"{name} must remain false")
    return STATUS


__all__ = [
    "API_KEY_ACCESSED",
    "BASE_COMMIT",
    "BRANCH",
    "CAPABILITY_PROBE_EXECUTED",
    "CREDENTIAL_ACCESSED",
    "CapabilityProbeResultV1",
    "CapabilityProbeRunnerV1",
    "ConstructionInputViewV1",
    "ConstructionNumericBindingV1",
    "ConstructionEvidenceRenderingAdapterV1",
    "ConstructionEvidenceContextV1",
    "DIRECT_NUMBER_PROMPT_HASH",
    "DIRECT_NUMBER_SCHEMA_HASH",
    "E0_BUDGET_POLICY_HASH",
    "E0_CONTROLLER_POLICY_HASH",
    "E0_VALIDITY_POLICY_HASH",
    "E2_PROTOCOL_BUNDLE_HASH",
    "EXECUTION_SCHEDULE_HASH",
    "ExecutionFailureReceiptV1",
    "FROZEN_E2_BINDING",
    "FrozenE2ExecutionBindingV1",
    "FrozenProviderRequestV1",
    "FutureLiveRunnerBoundaryV1",
    "INDIVIDUAL_PROPOSALS_PUBLIC",
    "LIVE_PROVIDER_TRANSPORT_ENABLED",
    "LLM_CALLED",
    "MAIN_PROMPT_HASH",
    "MAIN_SCHEMA_HASH",
    "MAXIMUM_SCIENTIFIC_SLOTS",
    "MockProviderEventV1",
    "MockProviderResponseV1",
    "MockProviderTransportV1",
    "PROVIDER_CONTACTED",
    "ParsedCapabilityProbeV1",
    "ParsedDirectNumberV1",
    "ParsedProviderProposalV1",
    "ProviderCallLedgerV1",
    "ProviderCallRecordV1",
    "ProviderCallSlotV1",
    "ProviderTransportAttemptV1",
    "ProviderTransportV1",
    "REAL_E1_PRIVATE_EVIDENCE_ACCESSED",
    "REAL_PROPOSAL_GENERATED",
    "RULE_V2_AUTHORIZED",
    "RUNTIME_AUTHORITY_GRANTED",
    "STATUS",
    "ScientificRunAbortV1",
    "SlotExecutionResultV1",
    "SyntheticNumericBindingV1",
    "SyntheticPrivateConstructionEvidenceV1",
    "T2_FOLLOWUP_PROMPT_HASH",
    "TASK039E3PreparationReceiptV1",
    "TASK039E3PreparationError",
    "TASK_ID",
    "TRANSPORT_RETRY_DELAYS_SECONDS",
    "assert_preparation_boundary_v1",
    "build_capability_probe_request_v1",
    "build_direct_number_request_v1",
    "build_main_request_v1",
    "build_mock_336_slot_schedule_v1",
    "build_t2_followup_request_v1",
    "execute_mock_provider_slot_v1",
    "instantiate_live_provider_request_v1",
    "open_live_provider_transport_v1",
    "parse_capability_response_v1",
    "parse_direct_number_response_v1",
    "parse_provider_proposal_response_v1",
    "read_openai_api_key_v1",
    "render_direct_number_input_v1",
    "render_main_construction_input_v1",
]
