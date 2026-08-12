"""Offline-capable recovery gate for the TASK-039E3 capability amendment.

This module contains only deterministic request construction, response
validation, and logical-probe accounting.  It does not contain a credential
reader, network client, private-evidence loader, or scientific executor.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from types import MappingProxyType
from typing import Any, Mapping

from paperworks.v6.common import freeze_json, stable_hash_v1, thaw_json
from paperworks.v6.task039e2_execution_configuration_v1 import (
    EXACT_MODEL,
    build_chat_completions_request_body_v1,
)
from paperworks.v6.task039e3_execution_prep_v1 import (
    FrozenProviderRequestV1,
    MockProviderResponseV1,
)


RECOVERY_CAPABILITY_FIXTURE_ID = "SYNTHETIC_CAPABILITY_CHECK"
RECOVERY_CAPABILITY_TOKEN = "TASK039E3_STRICT_JSON_SCHEMA_V1"
RECOVERY_CAPABILITY_PROMPT_V1 = (
    "SYNTHETIC_CAPABILITY_CHECK\n"
    "Return exactly the frozen capability acknowledgement. "
    "No scientific evidence is supplied."
)
RECOVERY_CAPABILITY_PROMPT_SHA256 = (
    "b725da5aaf23913c5c5ad7c74aa8260304c27a53f004d588d34b386ecfe0372b"
)
RECOVERY_CAPABILITY_SCHEMA_SHA256 = (
    "7fb77614ef8df85ea6c03afe7b47ec6fda06c5b09d8f37722daae39de0f57e9a"
)
R0_CHECKER_SPEC_HASH = (
    "a2484b2a1327a48b2b02ee7d2dc3cb05909daed8724a736c806117253b4df783"
)
R0_REQUEST_BUILDER_CONTRACT_HASH = (
    "8bdd8612f57bef011a28f3c130953f0e2fbd05f0e0ba153a8c712688cec10864"
)
HISTORICAL_CAPABILITY_PROBE_COUNT = 1
MAXIMUM_ADDITIONAL_RECOVERY_PROBES = 1
MAXIMUM_CUMULATIVE_CAPABILITY_PROBES = 2

_RECOVERY_CAPABILITY_SCHEMA_MUTABLE: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "additionalProperties": False,
    "properties": {
        "capability_token": {
            "const": RECOVERY_CAPABILITY_TOKEN,
            "type": "string",
        },
        "fixture_id": {
            "const": RECOVERY_CAPABILITY_FIXTURE_ID,
            "type": "string",
        },
    },
    "required": ["fixture_id", "capability_token"],
    "type": "object",
}
RECOVERY_CAPABILITY_SCHEMA_V1: Mapping[str, Any] = freeze_json(
    _RECOVERY_CAPABILITY_SCHEMA_MUTABLE
)


class TASK039E3RecoveryCapabilityError(ValueError):
    """Raised when a frozen recovery-capability contract is violated."""


@dataclass(frozen=True)
class RecoveryProbeAccountingV1:
    """Cumulative logical-probe accounting; transport attempts are excluded."""

    historical_probe_count: int = HISTORICAL_CAPABILITY_PROBE_COUNT
    current_recovery_probe_count: int = 0
    maximum_additional_recovery_probes: int = MAXIMUM_ADDITIONAL_RECOVERY_PROBES
    maximum_cumulative_probe_count: int = MAXIMUM_CUMULATIVE_CAPABILITY_PROBES

    def __post_init__(self) -> None:
        if self.historical_probe_count != HISTORICAL_CAPABILITY_PROBE_COUNT:
            raise TASK039E3RecoveryCapabilityError(
                "historical capability-probe count differs"
            )
        if self.maximum_additional_recovery_probes != 1:
            raise TASK039E3RecoveryCapabilityError(
                "maximum additional recovery probes differs"
            )
        if self.maximum_cumulative_probe_count != 2:
            raise TASK039E3RecoveryCapabilityError(
                "maximum cumulative capability probes differs"
            )
        if self.current_recovery_probe_count not in {0, 1}:
            raise TASK039E3RecoveryCapabilityError(
                "third capability probe is prohibited"
            )
        if self.cumulative_probe_count > self.maximum_cumulative_probe_count:
            raise TASK039E3RecoveryCapabilityError(
                "cumulative capability-probe limit exceeded"
            )

    @property
    def cumulative_probe_count(self) -> int:
        return self.historical_probe_count + self.current_recovery_probe_count

    def after_logical_recovery_probe(self) -> "RecoveryProbeAccountingV1":
        """Count one logical probe regardless of its transport-attempt count."""

        if self.current_recovery_probe_count >= self.maximum_additional_recovery_probes:
            raise TASK039E3RecoveryCapabilityError(
                "third capability probe is prohibited"
            )
        return RecoveryProbeAccountingV1(current_recovery_probe_count=1)


@dataclass(frozen=True)
class RecoveryCapabilityGateResultV1:
    """Deterministic recovery gate result derived from provider observations."""

    gate_status: str
    failure_codes: tuple[str, ...]
    provider_model_identity_source: str
    structured_output_authority_source: str
    transport_response_succeeded: bool
    model_identity_match: bool
    refusal_absent: bool
    structured_parse_pass: bool
    schema_validation_pass: bool
    fixture_id_match: bool
    capability_token_match: bool
    parsed_payload: Mapping[str, Any] | None

    def __post_init__(self) -> None:
        if self.gate_status not in {"PASS", "BLOCK"}:
            raise TASK039E3RecoveryCapabilityError("capability gate status differs")
        if self.provider_model_identity_source != "provider_response_metadata_only":
            raise TASK039E3RecoveryCapabilityError("model identity authority differs")
        if (
            self.structured_output_authority_source
            != "observed_strict_schema_parse_and_validation"
        ):
            raise TASK039E3RecoveryCapabilityError(
                "structured-output authority differs"
            )
        passed = all(
            (
                self.transport_response_succeeded,
                self.model_identity_match,
                self.refusal_absent,
                self.structured_parse_pass,
                self.schema_validation_pass,
                self.fixture_id_match,
                self.capability_token_match,
            )
        )
        if (self.gate_status == "PASS") != passed:
            raise TASK039E3RecoveryCapabilityError("capability PASS decision differs")
        if (self.gate_status == "PASS") == bool(self.failure_codes):
            raise TASK039E3RecoveryCapabilityError("capability failure codes differ")
        if self.parsed_payload is not None:
            object.__setattr__(self, "parsed_payload", freeze_json(self.parsed_payload))

    def to_dict(self) -> dict[str, Any]:
        return {
            "gate_status": self.gate_status,
            "failure_codes": list(self.failure_codes),
            "provider_model_identity_source": self.provider_model_identity_source,
            "structured_output_authority_source": (
                self.structured_output_authority_source
            ),
            "transport_response_succeeded": self.transport_response_succeeded,
            "model_identity_match": self.model_identity_match,
            "refusal_absent": self.refusal_absent,
            "structured_parse_pass": self.structured_parse_pass,
            "schema_validation_pass": self.schema_validation_pass,
            "fixture_id_match": self.fixture_id_match,
            "capability_token_match": self.capability_token_match,
            "parsed_payload": (
                thaw_json(self.parsed_payload)
                if self.parsed_payload is not None
                else None
            ),
        }


def verify_recovery_capability_constants_v1() -> None:
    """Fail closed if the frozen prompt or schema bytes drift."""

    prompt_hash = sha256(RECOVERY_CAPABILITY_PROMPT_V1.encode("utf-8")).hexdigest()
    if prompt_hash != RECOVERY_CAPABILITY_PROMPT_SHA256:
        raise TASK039E3RecoveryCapabilityError("recovery capability prompt differs")
    if stable_hash_v1(RECOVERY_CAPABILITY_SCHEMA_V1) != RECOVERY_CAPABILITY_SCHEMA_SHA256:
        raise TASK039E3RecoveryCapabilityError("recovery capability schema differs")


def build_recovery_capability_request_v1() -> FrozenProviderRequestV1:
    """Build the frozen stateless strict-schema recovery request without I/O."""

    verify_recovery_capability_constants_v1()
    body = build_chat_completions_request_body_v1(
        model_visible_content=RECOVERY_CAPABILITY_PROMPT_V1,
        provider_schema=RECOVERY_CAPABILITY_SCHEMA_V1,
        schema_name="task039e3_recovery_capability_response_v1",
    )
    return FrozenProviderRequestV1(
        purpose="capability_probe",
        request_body=body,
        model_visible_content_hash=RECOVERY_CAPABILITY_PROMPT_SHA256,
        provider_schema_hash=RECOVERY_CAPABILITY_SCHEMA_SHA256,
        schema_name="task039e3_recovery_capability_response_v1",
    )


def _validate_payload_v1(value: object) -> tuple[bool, bool, bool]:
    """Validate the exact two-field closed schema without optional dependencies."""

    if not isinstance(value, Mapping):
        return False, False, False
    if set(value) != {"fixture_id", "capability_token"}:
        return False, False, False
    fixture = value.get("fixture_id")
    token = value.get("capability_token")
    if not isinstance(fixture, str) or not isinstance(token, str):
        return False, False, False
    fixture_match = fixture == RECOVERY_CAPABILITY_FIXTURE_ID
    token_match = token == RECOVERY_CAPABILITY_TOKEN
    return fixture_match and token_match, fixture_match, token_match


def evaluate_recovery_capability_response_v1(
    response: MockProviderResponseV1,
) -> RecoveryCapabilityGateResultV1:
    """Evaluate one completed logical probe using authoritative observations.

    ``response.model`` is the sole model-identity authority.  Structured-output
    support is established only by parsing and exact closed-schema validation;
    model-authored self-report fields have no role in the decision.
    """

    if not isinstance(response, MockProviderResponseV1):
        raise TASK039E3RecoveryCapabilityError(
            "capability evaluation requires mapped provider response"
        )
    verify_recovery_capability_constants_v1()
    transport_succeeded = response.response_present and response.status_code == 200
    model_match = transport_succeeded and response.model == EXACT_MODEL
    refusal_absent = transport_succeeded and not response.refusal
    parsed_payload: Mapping[str, Any] | None = None
    parse_pass = False
    schema_pass = False
    fixture_match = False
    token_match = False
    if transport_succeeded and refusal_absent and isinstance(response.content, str):
        try:
            parsed = json.loads(response.content)
        except (TypeError, ValueError, json.JSONDecodeError):
            parsed = None
        if isinstance(parsed, Mapping):
            parse_pass = True
            schema_pass, fixture_match, token_match = _validate_payload_v1(parsed)
            if schema_pass:
                parsed_payload = parsed

    checks = (
        (transport_succeeded, "transport_response_failed"),
        (model_match, "returned_model_mismatch"),
        (refusal_absent, "provider_refusal"),
        (parse_pass, "structured_parse_failed"),
        (schema_pass, "schema_validation_failed"),
        (fixture_match, "fixture_id_mismatch"),
        (token_match, "capability_token_mismatch"),
    )
    failure_codes = tuple(code for passed, code in checks if not passed)
    return RecoveryCapabilityGateResultV1(
        gate_status="PASS" if not failure_codes else "BLOCK",
        failure_codes=failure_codes,
        provider_model_identity_source="provider_response_metadata_only",
        structured_output_authority_source=(
            "observed_strict_schema_parse_and_validation"
        ),
        transport_response_succeeded=transport_succeeded,
        model_identity_match=model_match,
        refusal_absent=refusal_absent,
        structured_parse_pass=parse_pass,
        schema_validation_pass=schema_pass,
        fixture_id_match=fixture_match,
        capability_token_match=token_match,
        parsed_payload=parsed_payload,
    )


verify_recovery_capability_constants_v1()


__all__ = [
    "HISTORICAL_CAPABILITY_PROBE_COUNT",
    "MAXIMUM_ADDITIONAL_RECOVERY_PROBES",
    "MAXIMUM_CUMULATIVE_CAPABILITY_PROBES",
    "R0_CHECKER_SPEC_HASH",
    "R0_REQUEST_BUILDER_CONTRACT_HASH",
    "RECOVERY_CAPABILITY_FIXTURE_ID",
    "RECOVERY_CAPABILITY_PROMPT_SHA256",
    "RECOVERY_CAPABILITY_PROMPT_V1",
    "RECOVERY_CAPABILITY_SCHEMA_SHA256",
    "RECOVERY_CAPABILITY_SCHEMA_V1",
    "RECOVERY_CAPABILITY_TOKEN",
    "RecoveryCapabilityGateResultV1",
    "RecoveryProbeAccountingV1",
    "TASK039E3RecoveryCapabilityError",
    "build_recovery_capability_request_v1",
    "evaluate_recovery_capability_response_v1",
    "verify_recovery_capability_constants_v1",
]
