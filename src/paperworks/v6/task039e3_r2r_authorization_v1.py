"""Closed future R2R scientific-execution authorization contract.

The module validates a document that a later governance task may create.  It
does not create that authority, read credentials, or contact a provider.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from paperworks.v6.common import require_sha256, stable_hash_v1


SCHEMA_VERSION = "1.0.0"
ARTIFACT_TYPE = "task039e3_r2r_execution_authorization_v1"
TASK_ID = "TASK-039E3-R2R-SCIENTIFIC-EXECUTION"
AUTHORIZATION_STATUS = "authorized_task039e3_r2r_scientific_execution"

PROTOCOL_COMMIT_A = "e55c01d679aa92ebf2cebd2c1929fd81c9e2f75f"
PROTOCOL_COMMIT_B = "8577e7cdf2893adb4ad6da588b2afb4d1896289d"
PROTOCOL_BUNDLE_HASH = "dbfab6817a8924b6c728c4a82405f5ffb030672c0057e6d25425fd5084e9e4a3"
PROTOCOL_RECEIPT_HASH = "2d65919dced159c2e584b4c5347dc2f4a3f8fd0d35323322d68014d2843f1168"
CAPABILITY_REUSE_BINDING_HASH = (
    "a26582efd20add0e639c40e7f3ed64428dc39923d284d0f0ad0d69d017b02f82"
)
CAPABILITY_RECEIPT_HASH = (
    "9ee4637da31b585a34eda4bad3b3be1dfa5597396ce1e78ef0564fa53da2b428"
)
CAPABILITY_PROVIDER_LEDGER_HEAD_HASH = (
    "e0b449ca96ffbf229954c059780baf8fb115aa79fc5d65802dd19e3a54120471"
)
CAPABILITY_PROVIDER_LEDGER_HASH = (
    "d6531d990bd70d89d114094f003dd9387e4df2db9cf9c2fc14bb5cf790818294"
)
FAILED_R2_TERMINAL_ARTIFACT_HASH = (
    "871afdea4753ae04594037ebaf973f2bf2963accb258df8b890076aa64cb837c"
)
FAILED_R2_SCIENTIFIC_LEDGER_HEAD_HASH = (
    "55bc62f047c085e3323fc28b1207afc3e5552a4ff05abad1b1fc05d055f79260"
)
FORENSIC_COMMIT_B = "12a974eb06999ec35266c73c8665852c072b1a41"
FORENSIC_BUNDLE_HASH = "8c01943ec1ac99ee2021a7e085eeffa45403590ca8f0857d71131ce20369a514"
FORENSIC_RECEIPT_HASH = "caa4a5b7537aaa62dd83f32253fa00aa9474c6472bdd48b23f16d80c89a15b46"
EXACT_MODEL = "gpt-5.4-2026-03-05"
EXACT_ENDPOINT = "https://api.openai.com/v1/chat/completions"
RECOVERY_SCHEMA_V2_HASH = "bcbc9debc32ec9e4b02d5781c7f8b512023752ccb90f60154648bb5d9de67aa1"
MAIN_PROMPT_HASH = "a251e4b9da31c33e72d14dd81da6b2b1d0d1437fdf37ca311330eccce226f1ba"
T2_FOLLOWUP_PROMPT_HASH = "a633067a7c9927be158f68ce714236f4c18c09433d49c903dac941a9774eeca5"
DIRECT_NUMBER_PROMPT_HASH = "fb01d8990ee3a7affe540dfdf3556b46d7bd744cd1e3a04d6fd9d79772dd2769"
DIRECT_NUMBER_SCHEMA_HASH = "b1b91bf27fd191da57984be625a2547e4e5ee96a0aca52535df071af92bfd6ca"
E1_COHORT_HASH = "4eb4da843a61a9c72aba59edcdf90e49766fc571af7eade14d500b3d04d363d4"
RELATION_SCHEDULE_HASH = "6db63485387924b28e9ce498aae46412a127ba69055a28e72880e1afffa4c4ca"

_COMMIT_FIELDS = {
    "protocol_commit_a": PROTOCOL_COMMIT_A,
    "protocol_commit_b": PROTOCOL_COMMIT_B,
    "implementation_commit_a": None,
    "implementation_commit_b": None,
    "independent_audit_commit_b": None,
    "forensic_commit_b": FORENSIC_COMMIT_B,
}
_HASH_FIELDS = {
    "protocol_bundle_hash": PROTOCOL_BUNDLE_HASH,
    "protocol_receipt_hash": PROTOCOL_RECEIPT_HASH,
    "capability_reuse_binding_hash": CAPABILITY_REUSE_BINDING_HASH,
    "capability_receipt_hash": CAPABILITY_RECEIPT_HASH,
    "capability_provider_ledger_head_hash": CAPABILITY_PROVIDER_LEDGER_HEAD_HASH,
    "capability_provider_ledger_hash": CAPABILITY_PROVIDER_LEDGER_HASH,
    "failed_r2_terminal_artifact_hash": FAILED_R2_TERMINAL_ARTIFACT_HASH,
    "failed_r2_scientific_provider_ledger_head_hash": FAILED_R2_SCIENTIFIC_LEDGER_HEAD_HASH,
    "forensic_bundle_hash": FORENSIC_BUNDLE_HASH,
    "forensic_receipt_hash": FORENSIC_RECEIPT_HASH,
    "implementation_source_manifest_hash": None,
    "independent_audit_bundle_hash": None,
    "independent_audit_receipt_hash": None,
    "recovery_main_provider_schema_v2_hash": RECOVERY_SCHEMA_V2_HASH,
    "main_prompt_hash": MAIN_PROMPT_HASH,
    "t2_followup_prompt_hash": T2_FOLLOWUP_PROMPT_HASH,
    "direct_number_prompt_hash": DIRECT_NUMBER_PROMPT_HASH,
    "direct_number_provider_schema_hash": DIRECT_NUMBER_SCHEMA_HASH,
    "e1_cohort_hash": E1_COHORT_HASH,
    "relation_schedule_hash": RELATION_SCHEDULE_HASH,
    "recovery_execution_configuration_hash": None,
}
_EXACT_FIELDS = {
    "schema_version": SCHEMA_VERSION,
    "artifact_type": ARTIFACT_TYPE,
    "task_id": TASK_ID,
    "authorization_status": AUTHORIZATION_STATUS,
    "recovery_execution_mode": "FRESH_FULL_COHORT_RESTART",
    "exact_model": EXACT_MODEL,
    "endpoint": EXACT_ENDPOINT,
    "urlopen_timeout_seconds": 30.0,
    "maximum_transport_attempts": 3,
    "maximum_transport_retries": 2,
    "scientific_concurrency": 1,
    "scientific_generation_retries": 0,
    "relations": 42,
    "t1_logical_calls": 42,
    "t1_b_logical_calls": 126,
    "t2_logical_calls_minimum": 42,
    "t2_logical_calls_maximum": 126,
    "direct_number_logical_calls": 42,
    "scientific_logical_calls_minimum": 252,
    "scientific_logical_calls_maximum": 336,
    "historical_aborted_r2_scientific_logical_calls": 1,
    "capability_reuse_authorized": True,
    "provider_contact_authorized": True,
    "scientific_execution_authorized": True,
    "capability_probe_authorized": False,
    "provider_diagnostic_call_authorized": False,
    "resume_authorized": False,
    "historical_partial_result_reuse_authorized": False,
    "rule_v2_authorized": False,
    "runtime_authority": False,
    "utility_evaluation_authorized": False,
    "winner_selected": False,
}
_AUTHORIZATION_KEYS = frozenset(
    {*_COMMIT_FIELDS, *_HASH_FIELDS, *_EXACT_FIELDS, "self_hash"}
)


class TASK039E3R2RAuthorizationError(ValueError):
    """A future R2R authorization is incomplete or has drifted."""


def _fail(message: str) -> None:
    raise TASK039E3R2RAuthorizationError(message)


@dataclass(frozen=True)
class ValidatedR2RAuthorizationV1:
    self_hash: str
    implementation_commit_a: str
    implementation_commit_b: str
    implementation_source_manifest_hash: str
    independent_audit_commit_b: str
    independent_audit_bundle_hash: str
    independent_audit_receipt_hash: str


def validate_r2r_authorization_v1(
    document: Mapping[str, Any],
) -> ValidatedR2RAuthorizationV1:
    """Validate a separately frozen future authorization; create nothing."""

    if not isinstance(document, Mapping):
        _fail("R2R authorization must be a mapping")
    if set(document) != _AUTHORIZATION_KEYS:
        _fail("R2R authorization fields differ from the closed contract")
    for key, expected in _EXACT_FIELDS.items():
        value = document.get(key)
        if type(value) is not type(expected) or value != expected:
            _fail(f"R2R authorization {key} differs")
    for key, expected in _COMMIT_FIELDS.items():
        value = document.get(key)
        if not isinstance(value, str) or len(value) != 40 or any(
            char not in "0123456789abcdef" for char in value
        ):
            _fail(f"R2R authorization {key} is not an exact Git commit")
        if expected is not None and value != expected:
            _fail(f"R2R authorization {key} differs")
    for key, expected in _HASH_FIELDS.items():
        try:
            value = require_sha256(document.get(key), key)  # type: ignore[arg-type]
        except (TypeError, ValueError) as exc:
            raise TASK039E3R2RAuthorizationError(
                f"R2R authorization {key} is not a lowercase SHA-256"
            ) from exc
        if expected is not None and value != expected:
            _fail(f"R2R authorization {key} differs")
    claimed = document.get("self_hash")
    try:
        self_hash = require_sha256(claimed, "self_hash")  # type: ignore[arg-type]
    except (TypeError, ValueError) as exc:
        raise TASK039E3R2RAuthorizationError(
            "R2R authorization self_hash is invalid"
        ) from exc
    payload = dict(document)
    payload.pop("self_hash")
    if stable_hash_v1(payload) != self_hash:
        _fail("R2R authorization self-hash differs")
    return ValidatedR2RAuthorizationV1(
        self_hash=self_hash,
        implementation_commit_a=str(document["implementation_commit_a"]),
        implementation_commit_b=str(document["implementation_commit_b"]),
        implementation_source_manifest_hash=str(
            document["implementation_source_manifest_hash"]
        ),
        independent_audit_commit_b=str(document["independent_audit_commit_b"]),
        independent_audit_bundle_hash=str(document["independent_audit_bundle_hash"]),
        independent_audit_receipt_hash=str(document["independent_audit_receipt_hash"]),
    )


__all__ = [
    "ARTIFACT_TYPE",
    "AUTHORIZATION_STATUS",
    "SCHEMA_VERSION",
    "TASK039E3R2RAuthorizationError",
    "TASK_ID",
    "ValidatedR2RAuthorizationV1",
    "validate_r2r_authorization_v1",
]
