"""Fail-closed future R2 V2 authorization and pre-contact ordering.

This offline R1C module validates a separately supplied future authorization.
It contains no environment or provider access; credential lookup is an injected
operation reached only after every authority, Git, custody, root, and public
scientific-preflight guard has passed.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Any, Callable, Mapping, TypeVar

from paperworks.v6.common import require_sha256, stable_hash_v1
from paperworks.v6.task039e3_recovery_authorization_v1 import (
    RecoveryPrivateRootsV1,
    TASK039E3RecoveryAuthorizationError as _V1AuthorizationError,
    validate_recovery_private_roots_v1,
)


TASK_ID = "TASK-039E3-R2_RECOVERY_EXECUTION"
ARTIFACT_TYPE = "task039e3_recovery_execution_authorization_v2"
AUTHORIZATION_STATUS = "authorized_task039e3_r2_recovery_execution"
SCHEMA_VERSION = "2.0.0"

R0_COMMIT = "d5164aa93cc4c3efb6a343e0890b554f436a7e39"
R0_BUNDLE_HASH = "8c402cdea45f53a7bb49cfb8ba796d4b557a6fb70532c7ad22281f3b62c60ccc"
R1A_COMMIT = "260b91be463815bc5bb453ca2cc05cec741aacc3"
R1A_TIMEOUT_AUTHORITY_HASH = "d70f40d644405387681dfd2984b9fed2c4c8c0d6da13fbdd79a428b226b46865"
R1B_COMMIT_A = "93c2e8a6333829446c5353f1ca9b61c967f8a7a7"
R1B_COMMIT_B = "2b6e4964085b2405513680303e0586f7cca50c6d"
R1B_AUDIT_COMMIT_B = "1747ece15cac693b2ec84c7f780bd1a817a78469"
R1B_INDEPENDENT_AUDIT_BUNDLE_HASH = (
    "da87b16e0c8daa373303d716ef85203de58e7bfa6d21d42c3184fd4ef4e6ccf7"
)
R1B_AUDIT_RECEIPT_HASH = (
    "0d5e4b35cb62d08cfffb53c8b34f8e89f26db1329c83057c89a8eb749f0a83bc"
)
HISTORICAL_CAPABILITY_RECEIPT_HASH = (
    "e36098690f2c4c018b8ed5f339d46870fbbe0561f52c117cd2525a63d155c279"
)
HISTORICAL_PROVIDER_LEDGER_HEAD_HASH = (
    "656d81ded2f166175adf2717abc226c325cd4a9fcbcee5306f4ea35c7465d254"
)
EXACT_MODEL = "gpt-5.4-2026-03-05"
URLOPEN_TIMEOUT_SECONDS = 30.0
HISTORICAL_CAPABILITY_PROBE_COUNT = 1
MAXIMUM_ADDITIONAL_RECOVERY_PROBES = 1
MAXIMUM_CUMULATIVE_CAPABILITY_PROBES = 2

_COMMIT_RE = re.compile(r"^[a-f0-9]{40}$")
_AUTHORIZATION_KEYS = frozenset(
    {
        "schema_version",
        "artifact_type",
        "task_id",
        "authorization_status",
        "r0_commit",
        "r0_bundle_hash",
        "r1a_commit",
        "r1a_timeout_authority_hash",
        "r1b_commit_a",
        "r1b_commit_b",
        "r1b_audit_commit_b",
        "r1b_independent_audit_bundle_hash",
        "r1b_audit_receipt_hash",
        "r1c_commit_a",
        "r1c_source_manifest_hash",
        "historical_capability_receipt_hash",
        "historical_provider_ledger_head_hash",
        "exact_model",
        "urlopen_timeout_seconds",
        "historical_capability_probe_count",
        "maximum_additional_recovery_probes",
        "maximum_cumulative_capability_probes",
        "provider_contact_authorized",
        "recovery_probe_authorized",
        "scientific_execution_after_capability_pass_authorized",
        "rule_v2_authorized",
        "runtime_authority",
        "utility_evaluation_authorized",
        "winner_selected",
        "self_hash",
    }
)


class TASK039E3RecoveryAuthorizationV2Error(ValueError):
    """Raised before credential lookup when a future R2 V2 guard differs."""


def _fail(message: str) -> None:
    raise TASK039E3RecoveryAuthorizationV2Error(message)


def _require_commit(value: object, field_name: str) -> str:
    if not isinstance(value, str) or _COMMIT_RE.fullmatch(value) is None:
        _fail(f"{field_name} must be an exact 40-character Git commit")
    return value


def _require_exact(document: Mapping[str, Any], name: str, expected: object) -> None:
    observed = document.get(name)
    if type(observed) is not type(expected) or observed != expected:
        _fail(f"R2 V2 authorization {name} differs")


@dataclass(frozen=True)
class ValidatedR2AuthorizationV2:
    self_hash: str
    r1c_commit_a: str
    r1c_source_manifest_hash: str


@dataclass(frozen=True)
class PriorAuthorityStateV2:
    r0_commit: str
    r0_bundle_hash: str
    r1a_commit: str
    r1a_timeout_authority_hash: str
    r1b_commit_a: str
    r1b_commit_b: str
    r1b_audit_commit_b: str
    r1b_independent_audit_bundle_hash: str
    r1b_audit_receipt_hash: str


def validate_prior_authority_state_v2(state: PriorAuthorityStateV2) -> None:
    if not isinstance(state, PriorAuthorityStateV2):
        _fail("observed R0/R1A/R1B-AUDIT authority state is required")
    expected = PriorAuthorityStateV2(
        r0_commit=R0_COMMIT,
        r0_bundle_hash=R0_BUNDLE_HASH,
        r1a_commit=R1A_COMMIT,
        r1a_timeout_authority_hash=R1A_TIMEOUT_AUTHORITY_HASH,
        r1b_commit_a=R1B_COMMIT_A,
        r1b_commit_b=R1B_COMMIT_B,
        r1b_audit_commit_b=R1B_AUDIT_COMMIT_B,
        r1b_independent_audit_bundle_hash=R1B_INDEPENDENT_AUDIT_BUNDLE_HASH,
        r1b_audit_receipt_hash=R1B_AUDIT_RECEIPT_HASH,
    )
    if state != expected:
        _fail("observed R0/R1A/R1B-AUDIT authority binding differs")


def validate_r2_authorization_v2(
    document: Mapping[str, Any],
) -> ValidatedR2AuthorizationV2:
    """Validate the exact closed, self-hashed future R2 V2 authorization."""

    if not isinstance(document, Mapping):
        _fail("R2 V2 authorization must be an object")
    if frozenset(document) != _AUTHORIZATION_KEYS:
        _fail("R2 V2 authorization fields differ from the closed contract")
    supplied_hash = document.get("self_hash")
    try:
        require_sha256(supplied_hash, "self_hash")
    except (TypeError, ValueError) as exc:
        raise TASK039E3RecoveryAuthorizationV2Error(
            "R2 V2 authorization self_hash is invalid"
        ) from exc
    content = {key: value for key, value in document.items() if key != "self_hash"}
    if stable_hash_v1(content) != supplied_hash:
        _fail("R2 V2 authorization self-hash differs")

    exact_values = {
        "schema_version": SCHEMA_VERSION,
        "artifact_type": ARTIFACT_TYPE,
        "task_id": TASK_ID,
        "authorization_status": AUTHORIZATION_STATUS,
        "r0_commit": R0_COMMIT,
        "r0_bundle_hash": R0_BUNDLE_HASH,
        "r1a_commit": R1A_COMMIT,
        "r1a_timeout_authority_hash": R1A_TIMEOUT_AUTHORITY_HASH,
        "r1b_commit_a": R1B_COMMIT_A,
        "r1b_commit_b": R1B_COMMIT_B,
        "r1b_audit_commit_b": R1B_AUDIT_COMMIT_B,
        "r1b_independent_audit_bundle_hash": R1B_INDEPENDENT_AUDIT_BUNDLE_HASH,
        "r1b_audit_receipt_hash": R1B_AUDIT_RECEIPT_HASH,
        "historical_capability_receipt_hash": HISTORICAL_CAPABILITY_RECEIPT_HASH,
        "historical_provider_ledger_head_hash": HISTORICAL_PROVIDER_LEDGER_HEAD_HASH,
        "exact_model": EXACT_MODEL,
        "urlopen_timeout_seconds": URLOPEN_TIMEOUT_SECONDS,
        "historical_capability_probe_count": HISTORICAL_CAPABILITY_PROBE_COUNT,
        "maximum_additional_recovery_probes": MAXIMUM_ADDITIONAL_RECOVERY_PROBES,
        "maximum_cumulative_capability_probes": MAXIMUM_CUMULATIVE_CAPABILITY_PROBES,
        "provider_contact_authorized": True,
        "recovery_probe_authorized": True,
        "scientific_execution_after_capability_pass_authorized": True,
        "rule_v2_authorized": False,
        "runtime_authority": False,
        "utility_evaluation_authorized": False,
        "winner_selected": False,
    }
    for name, expected in exact_values.items():
        _require_exact(document, name, expected)
    commit = _require_commit(document.get("r1c_commit_a"), "r1c_commit_a")
    manifest_hash = document.get("r1c_source_manifest_hash")
    try:
        require_sha256(manifest_hash, "r1c_source_manifest_hash")
    except (TypeError, ValueError) as exc:
        raise TASK039E3RecoveryAuthorizationV2Error(
            "R2 V2 source-manifest hash is invalid"
        ) from exc
    return ValidatedR2AuthorizationV2(
        self_hash=supplied_hash,
        r1c_commit_a=commit,
        r1c_source_manifest_hash=manifest_hash,
    )


@dataclass(frozen=True)
class GitExecutionStateV2:
    head_commit: str
    worktree_clean: bool
    index_clean: bool
    source_manifest_hash: str
    source_blobs_match_manifest: bool


def validate_git_and_source_state_v2(
    state: GitExecutionStateV2,
    *,
    authorization: ValidatedR2AuthorizationV2,
) -> None:
    if not isinstance(state, GitExecutionStateV2):
        _fail("Git execution state V2 is required")
    if state.head_commit != authorization.r1c_commit_a:
        _fail("Git HEAD differs from authorized R1C Commit A")
    if state.worktree_clean is not True:
        _fail("recovery worktree must be clean")
    if state.index_clean is not True:
        _fail("recovery index must be clean")
    if state.source_manifest_hash != authorization.r1c_source_manifest_hash:
        _fail("R1C source-freeze manifest differs")
    if state.source_blobs_match_manifest is not True:
        _fail("R1C source blobs differ from the source-freeze manifest")


def validate_historical_bindings_v2(
    *, capability_receipt_hash: str, provider_ledger_head_hash: str
) -> None:
    if capability_receipt_hash != HISTORICAL_CAPABILITY_RECEIPT_HASH:
        _fail("historical capability receipt binding differs")
    if provider_ledger_head_hash != HISTORICAL_PROVIDER_LEDGER_HEAD_HASH:
        _fail("historical provider-ledger head binding differs")


def validate_recovery_private_roots_v2(
    *,
    repository_root: Path,
    e1_private_value: str,
    historical_e3_private_value: str,
    recovery_e3_private_value: str,
) -> RecoveryPrivateRootsV1:
    """Reuse the audited offline V1 root predicate, normalizing its error type."""

    try:
        return validate_recovery_private_roots_v1(
            repository_root=repository_root,
            e1_private_value=e1_private_value,
            historical_e3_private_value=historical_e3_private_value,
            recovery_e3_private_value=recovery_e3_private_value,
        )
    except _V1AuthorizationError as exc:
        raise TASK039E3RecoveryAuthorizationV2Error(str(exc)) from exc


@dataclass(frozen=True)
class RecoveryProbeAccountingV2:
    historical_probe_count: int = HISTORICAL_CAPABILITY_PROBE_COUNT
    current_recovery_probe_count: int = 0

    def __post_init__(self) -> None:
        if type(self.historical_probe_count) is not int or self.historical_probe_count != 1:
            _fail("historical capability probe count differs")
        if type(self.current_recovery_probe_count) is not int or self.current_recovery_probe_count not in (0, 1):
            _fail("at most one recovery capability probe is permitted")
        if self.cumulative_probe_count > MAXIMUM_CUMULATIVE_CAPABILITY_PROBES:
            _fail("cumulative capability probe limit exceeded")

    @property
    def cumulative_probe_count(self) -> int:
        return self.historical_probe_count + self.current_recovery_probe_count

    def allocate_recovery_probe(self) -> "RecoveryProbeAccountingV2":
        if self.current_recovery_probe_count != 0:
            _fail("third capability probe is prohibited")
        return RecoveryProbeAccountingV2(1, 1)

    def with_transport_attempts(self, attempts: int) -> "RecoveryProbeAccountingV2":
        if isinstance(attempts, bool) or not isinstance(attempts, int) or attempts not in (1, 2, 3):
            _fail("transport attempts for one logical probe must be between one and three")
        return self


_CredentialT = TypeVar("_CredentialT")


@dataclass(frozen=True)
class PrecontactBootstrapV2:
    authorization: ValidatedR2AuthorizationV2
    git_state: GitExecutionStateV2
    private_roots: RecoveryPrivateRootsV1
    scientific_preflight: Any
    credential: Any
    completed_guard_order: tuple[str, ...]


def run_ordered_precontact_guards_v2(
    *,
    authorization_document: Mapping[str, Any],
    prior_authority_state_loader: Callable[[], PriorAuthorityStateV2],
    git_state_loader: Callable[[], GitExecutionStateV2],
    repository_root: Path,
    e1_private_value: str,
    historical_e3_private_value: str,
    recovery_e3_private_value: str,
    historical_capability_receipt_hash: str,
    historical_provider_ledger_head_hash: str,
    scientific_preflight_loader: Callable[[], Any],
    credential_loader: Callable[[], _CredentialT],
    event_sink: Callable[[str], None] | None = None,
) -> PrecontactBootstrapV2:
    """Run every future R2 V2 guard before injected credential lookup."""

    completed: list[str] = []

    def mark(stage: str) -> None:
        completed.append(stage)
        if event_sink is not None:
            event_sink(stage)

    authorization = validate_r2_authorization_v2(authorization_document)
    mark("r2_authorization_v2_validated")
    prior = prior_authority_state_loader()
    validate_prior_authority_state_v2(prior)
    mark("r0_bindings_validated")
    mark("r1a_bindings_validated")
    mark("r1b_audit_bindings_validated")
    git_state = git_state_loader()
    validate_git_and_source_state_v2(git_state, authorization=authorization)
    mark("r1c_commit_a_validated")
    mark("git_worktree_and_index_validated")
    mark("r1c_source_manifest_validated")
    validate_historical_bindings_v2(
        capability_receipt_hash=historical_capability_receipt_hash,
        provider_ledger_head_hash=historical_provider_ledger_head_hash,
    )
    mark("historical_custody_bindings_validated")
    roots = validate_recovery_private_roots_v2(
        repository_root=repository_root,
        e1_private_value=e1_private_value,
        historical_e3_private_value=historical_e3_private_value,
        recovery_e3_private_value=recovery_e3_private_value,
    )
    mark("private_roots_validated")
    preflight = scientific_preflight_loader()
    mark("scientific_public_preflight_validated")
    credential = credential_loader()
    mark("credential_loaded")
    return PrecontactBootstrapV2(
        authorization=authorization,
        git_state=git_state,
        private_roots=roots,
        scientific_preflight=preflight,
        credential=credential,
        completed_guard_order=tuple(completed),
    )


__all__ = [
    "ARTIFACT_TYPE",
    "AUTHORIZATION_STATUS",
    "EXACT_MODEL",
    "GitExecutionStateV2",
    "HISTORICAL_CAPABILITY_PROBE_COUNT",
    "HISTORICAL_CAPABILITY_RECEIPT_HASH",
    "HISTORICAL_PROVIDER_LEDGER_HEAD_HASH",
    "MAXIMUM_ADDITIONAL_RECOVERY_PROBES",
    "MAXIMUM_CUMULATIVE_CAPABILITY_PROBES",
    "PrecontactBootstrapV2",
    "PriorAuthorityStateV2",
    "R0_BUNDLE_HASH",
    "R0_COMMIT",
    "R1A_COMMIT",
    "R1A_TIMEOUT_AUTHORITY_HASH",
    "R1B_AUDIT_COMMIT_B",
    "R1B_AUDIT_RECEIPT_HASH",
    "R1B_COMMIT_A",
    "R1B_COMMIT_B",
    "R1B_INDEPENDENT_AUDIT_BUNDLE_HASH",
    "RecoveryProbeAccountingV2",
    "TASK039E3RecoveryAuthorizationV2Error",
    "TASK_ID",
    "URLOPEN_TIMEOUT_SECONDS",
    "ValidatedR2AuthorizationV2",
    "run_ordered_precontact_guards_v2",
    "validate_git_and_source_state_v2",
    "validate_historical_bindings_v2",
    "validate_prior_authority_state_v2",
    "validate_r2_authorization_v2",
    "validate_recovery_private_roots_v2",
]
