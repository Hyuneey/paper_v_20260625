"""Final-audit-capable future R2 authorization for TASK-039E3 R1D2.

This additive, offline module closes the R1C-AUDIT provenance gap.  It
validates a future R2 V3 authorization, an externally supplied R1D2-AUDIT
PASS receipt, and the identical receipt read from the authorized audit Git
commit before an injected credential loader can be reached.

R1D2 is the task name used by the authority fields.  It is the corrected
successor to the historically blocked R1D preflight; no R1D/R1D2 alias is
accepted.  This module neither reads process environment nor contacts a
provider and does not create an authorized R2 artifact.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import re
import subprocess
from typing import Any, Callable, Mapping, TypeVar

from paperworks.v6.common import require_sha256, stable_hash_v1


TASK_ID = "TASK-039E3-R2_RECOVERY_EXECUTION"
ARTIFACT_TYPE = "task039e3_recovery_execution_authorization_v3"
AUTHORIZATION_STATUS = "authorized_task039e3_r2_recovery_execution"
SCHEMA_VERSION = "3.0.0"

FINAL_AUDIT_TASK_ID = "TASK-039E3-R1D2-AUDIT"
FINAL_AUDIT_ARTIFACT_TYPE = "task039e3_r1d2_audit_receipt_v1"
FINAL_AUDIT_PASS_STATUS = "passed_task039e3_r1d2_independent_audit"
FINAL_AUDIT_RECEIPT_PATH = (
    "docs/task_reports/TASK-039E3_R1D2_AUDIT_RECEIPT.json"
)

R0_COMMIT = "d5164aa93cc4c3efb6a343e0890b554f436a7e39"
R0_BUNDLE_HASH = "8c402cdea45f53a7bb49cfb8ba796d4b557a6fb70532c7ad22281f3b62c60ccc"
R1A_COMMIT = "260b91be463815bc5bb453ca2cc05cec741aacc3"
R1A_TIMEOUT_AUTHORITY_HASH = (
    "d70f40d644405387681dfd2984b9fed2c4c8c0d6da13fbdd79a428b226b46865"
)
R1B_COMMIT_A = "93c2e8a6333829446c5353f1ca9b61c967f8a7a7"
R1B_COMMIT_B = "2b6e4964085b2405513680303e0586f7cca50c6d"
R1C_COMMIT_A = "42f51cba0168f8050803139ec3333156ed2fa403"
R1C_COMMIT_B = "a1a802eb814937e2f024b6caa429943690bc6976"
R1C_SOURCE_MANIFEST_HASH = (
    "e494c727d03b75cbec7123c7bb92da61ead345673f678078d32a217dfe6350d0"
)
R1C_IMPLEMENTATION_RECEIPT_HASH = (
    "01b4d987c490ff4255d5cd992a2846f86d9a7249717c807e097747fd4d6b698e"
)
R1C_REMEDIATION_BUNDLE_HASH = (
    "6a4ed90c1e96006f81ea414519ef7c842b0a2b3e4d0062c16d4d420010cd4a56"
)
R1C_AUDIT_COMMIT_B = "8bd34c6af42f97835588f6b0ffba34660a5d51cc"
R1C_INDEPENDENT_AUDIT_BUNDLE_HASH = (
    "cd5c905fb356982947f0367ab7d44f8c9a6c694130fa7d02d936e26389713384"
)
R1C_AUDIT_RECEIPT_HASH = (
    "2abff5c79cfad02bccc963043c13def1e4223676b89b58773216000aeeb3049f"
)
CORRECTED_CUSTODY_ACCOUNTING_HASH = (
    "ac5dd3d8b060ef353b18a124ea9344ab679cbd6ac82bbcfb5d9f94ce5fbeb616"
)

HISTORICAL_BLOCKED_R1D_COMMIT = "66e15fcdae2e932bebf09b569fefbe6028443d79"
HISTORICAL_BLOCKED_R1D_PREFLIGHT_HASH = (
    "ad2cc1493c97e91c3775a1b13c1ba88a5b06c774d2df043e0ace806559532870"
)
HISTORICAL_BLOCKED_R1D_IMPLEMENTATION_RECEIPT_HASH = (
    "2f5aaf68462be6dce7de063f595dce753b2b1bd4dfab13713c41517b2408ca57"
)
HISTORICAL_BLOCKED_R1D_DATA_ACCESS_AUDIT_HASH = (
    "ed2025cf7ec81b56860052b157bec44be5336bca30b924194a7f8f584078838e"
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
        "r1c_commit_a",
        "r1c_commit_b",
        "r1c_source_manifest_hash",
        "r1c_implementation_receipt_hash",
        "r1c_remediation_bundle_hash",
        "r1c_audit_commit_b",
        "r1c_independent_audit_bundle_hash",
        "r1c_audit_receipt_hash",
        "corrected_custody_accounting_hash",
        "historical_blocked_r1d_commit",
        "historical_blocked_r1d_preflight_hash",
        "historical_blocked_r1d_implementation_receipt_hash",
        "historical_blocked_r1d_data_access_audit_hash",
        "r1d2_commit_a",
        "r1d2_commit_b",
        "r1d2_source_manifest_hash",
        "r1d2_audit_commit_b",
        "r1d2_independent_audit_bundle_hash",
        "r1d2_audit_receipt_hash",
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


class TASK039E3RecoveryAuthorizationV3Error(ValueError):
    """Raised before credential lookup when a V3 authority guard differs."""


def _fail(message: str) -> None:
    raise TASK039E3RecoveryAuthorizationV3Error(message)


def _require_commit(value: object, field_name: str) -> str:
    if not isinstance(value, str) or _COMMIT_RE.fullmatch(value) is None:
        _fail(f"{field_name} must be an exact 40-character Git commit")
    return value


def _require_hash(value: object, field_name: str) -> str:
    try:
        validated = require_sha256(value, field_name)  # type: ignore[arg-type]
    except (TypeError, ValueError) as exc:
        raise TASK039E3RecoveryAuthorizationV3Error(
            f"{field_name} must be a lowercase SHA-256"
        ) from exc
    return validated


def _require_exact(document: Mapping[str, Any], name: str, expected: object) -> None:
    observed = document.get(name)
    if type(observed) is not type(expected) or observed != expected:
        _fail(f"R2 V3 authorization {name} differs")


@dataclass(frozen=True)
class ValidatedR2AuthorizationV3:
    self_hash: str
    r1d2_commit_a: str
    r1d2_commit_b: str
    r1d2_source_manifest_hash: str
    r1d2_audit_commit_b: str
    r1d2_independent_audit_bundle_hash: str
    r1d2_audit_receipt_hash: str


@dataclass(frozen=True)
class PriorAuthorityStateV3:
    r0_commit: str
    r0_bundle_hash: str
    r1a_commit: str
    r1a_timeout_authority_hash: str
    r1b_commit_a: str
    r1b_commit_b: str
    r1c_commit_a: str
    r1c_commit_b: str
    r1c_source_manifest_hash: str
    r1c_implementation_receipt_hash: str
    r1c_remediation_bundle_hash: str
    r1c_audit_commit_b: str
    r1c_independent_audit_bundle_hash: str
    r1c_audit_receipt_hash: str
    corrected_custody_accounting_hash: str
    historical_blocked_r1d_commit: str
    historical_blocked_r1d_preflight_hash: str
    historical_blocked_r1d_implementation_receipt_hash: str
    historical_blocked_r1d_data_access_audit_hash: str


_EXPECTED_PRIOR_AUTHORITY = PriorAuthorityStateV3(
    r0_commit=R0_COMMIT,
    r0_bundle_hash=R0_BUNDLE_HASH,
    r1a_commit=R1A_COMMIT,
    r1a_timeout_authority_hash=R1A_TIMEOUT_AUTHORITY_HASH,
    r1b_commit_a=R1B_COMMIT_A,
    r1b_commit_b=R1B_COMMIT_B,
    r1c_commit_a=R1C_COMMIT_A,
    r1c_commit_b=R1C_COMMIT_B,
    r1c_source_manifest_hash=R1C_SOURCE_MANIFEST_HASH,
    r1c_implementation_receipt_hash=R1C_IMPLEMENTATION_RECEIPT_HASH,
    r1c_remediation_bundle_hash=R1C_REMEDIATION_BUNDLE_HASH,
    r1c_audit_commit_b=R1C_AUDIT_COMMIT_B,
    r1c_independent_audit_bundle_hash=R1C_INDEPENDENT_AUDIT_BUNDLE_HASH,
    r1c_audit_receipt_hash=R1C_AUDIT_RECEIPT_HASH,
    corrected_custody_accounting_hash=CORRECTED_CUSTODY_ACCOUNTING_HASH,
    historical_blocked_r1d_commit=HISTORICAL_BLOCKED_R1D_COMMIT,
    historical_blocked_r1d_preflight_hash=HISTORICAL_BLOCKED_R1D_PREFLIGHT_HASH,
    historical_blocked_r1d_implementation_receipt_hash=(
        HISTORICAL_BLOCKED_R1D_IMPLEMENTATION_RECEIPT_HASH
    ),
    historical_blocked_r1d_data_access_audit_hash=(
        HISTORICAL_BLOCKED_R1D_DATA_ACCESS_AUDIT_HASH
    ),
)


def validate_prior_authority_state_v3(state: PriorAuthorityStateV3) -> None:
    if not isinstance(state, PriorAuthorityStateV3):
        _fail("observed R0/R1A/R1B/R1C/R1D authority state is required")
    if state != _EXPECTED_PRIOR_AUTHORITY:
        _fail("observed prior authority binding differs")


def validate_r2_authorization_v3(
    document: Mapping[str, Any],
) -> ValidatedR2AuthorizationV3:
    """Validate the exact closed, self-hashed future R2 V3 authorization."""

    if not isinstance(document, Mapping):
        _fail("R2 V3 authorization must be an object")
    if frozenset(document) != _AUTHORIZATION_KEYS:
        _fail("R2 V3 authorization fields differ from the closed contract")
    supplied_hash = _require_hash(document.get("self_hash"), "self_hash")
    content = {key: value for key, value in document.items() if key != "self_hash"}
    if stable_hash_v1(content) != supplied_hash:
        _fail("R2 V3 authorization self-hash differs")

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
        "r1c_commit_a": R1C_COMMIT_A,
        "r1c_commit_b": R1C_COMMIT_B,
        "r1c_source_manifest_hash": R1C_SOURCE_MANIFEST_HASH,
        "r1c_implementation_receipt_hash": R1C_IMPLEMENTATION_RECEIPT_HASH,
        "r1c_remediation_bundle_hash": R1C_REMEDIATION_BUNDLE_HASH,
        "r1c_audit_commit_b": R1C_AUDIT_COMMIT_B,
        "r1c_independent_audit_bundle_hash": R1C_INDEPENDENT_AUDIT_BUNDLE_HASH,
        "r1c_audit_receipt_hash": R1C_AUDIT_RECEIPT_HASH,
        "corrected_custody_accounting_hash": CORRECTED_CUSTODY_ACCOUNTING_HASH,
        "historical_blocked_r1d_commit": HISTORICAL_BLOCKED_R1D_COMMIT,
        "historical_blocked_r1d_preflight_hash": HISTORICAL_BLOCKED_R1D_PREFLIGHT_HASH,
        "historical_blocked_r1d_implementation_receipt_hash": (
            HISTORICAL_BLOCKED_R1D_IMPLEMENTATION_RECEIPT_HASH
        ),
        "historical_blocked_r1d_data_access_audit_hash": (
            HISTORICAL_BLOCKED_R1D_DATA_ACCESS_AUDIT_HASH
        ),
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

    commit_a = _require_commit(document.get("r1d2_commit_a"), "r1d2_commit_a")
    commit_b = _require_commit(document.get("r1d2_commit_b"), "r1d2_commit_b")
    manifest_hash = _require_hash(
        document.get("r1d2_source_manifest_hash"), "r1d2_source_manifest_hash"
    )
    audit_commit = _require_commit(
        document.get("r1d2_audit_commit_b"), "r1d2_audit_commit_b"
    )
    audit_bundle = _require_hash(
        document.get("r1d2_independent_audit_bundle_hash"),
        "r1d2_independent_audit_bundle_hash",
    )
    audit_receipt = _require_hash(
        document.get("r1d2_audit_receipt_hash"), "r1d2_audit_receipt_hash"
    )
    return ValidatedR2AuthorizationV3(
        self_hash=supplied_hash,
        r1d2_commit_a=commit_a,
        r1d2_commit_b=commit_b,
        r1d2_source_manifest_hash=manifest_hash,
        r1d2_audit_commit_b=audit_commit,
        r1d2_independent_audit_bundle_hash=audit_bundle,
        r1d2_audit_receipt_hash=audit_receipt,
    )


@dataclass(frozen=True)
class GitExecutionStateV3:
    head_commit: str
    worktree_clean: bool
    index_clean: bool
    source_manifest_hash: str
    source_blobs_match_manifest: bool


def validate_git_and_source_state_v3(
    state: GitExecutionStateV3,
    *,
    authorization: ValidatedR2AuthorizationV3,
) -> None:
    if not isinstance(state, GitExecutionStateV3):
        _fail("Git execution state V3 is required")
    if state.head_commit != authorization.r1d2_commit_a:
        _fail("Git HEAD differs from authorized R1D2 Commit A")
    if state.worktree_clean is not True:
        _fail("recovery worktree must be clean")
    if state.index_clean is not True:
        _fail("recovery index must be clean")
    if state.source_manifest_hash != authorization.r1d2_source_manifest_hash:
        _fail("R1D2 source-freeze manifest differs")
    if state.source_blobs_match_manifest is not True:
        _fail("R1D2 source blobs differ from the source-freeze manifest")


@dataclass(frozen=True)
class ValidatedFinalAuditProvenanceV3:
    receipt_hash: str
    audit_commit_b: str
    audit_bundle_hash: str
    receipt_path: str


def _validate_audit_receipt_document(
    document: Mapping[str, Any],
    *,
    authorization: ValidatedR2AuthorizationV3,
) -> str:
    if not isinstance(document, Mapping):
        _fail("R1D2-AUDIT receipt must be an object")
    supplied_hash = _require_hash(document.get("artifact_hash"), "audit receipt artifact_hash")
    content = {key: value for key, value in document.items() if key != "artifact_hash"}
    if stable_hash_v1(content) != supplied_hash:
        _fail("R1D2-AUDIT receipt self-hash differs")
    required_values = {
        "artifact_type": FINAL_AUDIT_ARTIFACT_TYPE,
        "task_id": FINAL_AUDIT_TASK_ID,
        "status": FINAL_AUDIT_PASS_STATUS,
        "r1d2_commit_a": authorization.r1d2_commit_a,
        "r1d2_commit_b": authorization.r1d2_commit_b,
        "r1d2_source_manifest_hash": authorization.r1d2_source_manifest_hash,
        "audit_bundle_hash": authorization.r1d2_independent_audit_bundle_hash,
    }
    for name, expected in required_values.items():
        observed = document.get(name)
        if type(observed) is not type(expected) or observed != expected:
            _fail(f"R1D2-AUDIT receipt {name} differs")
    if supplied_hash != authorization.r1d2_audit_receipt_hash:
        _fail("R1D2-AUDIT receipt hash differs from R2 authorization")
    return supplied_hash


GitReceiptBlobLoaderV3 = Callable[[str, str], bytes]


def load_audit_receipt_git_blob_v3(
    repository_root: Path,
    audit_commit_b: str,
    receipt_path: str = FINAL_AUDIT_RECEIPT_PATH,
) -> bytes:
    """Read the exact audit receipt blob from Git without network access.

    The active runner should bind this function to its already validated
    repository root and pass the resulting callable into the ordered guards.
    ``shell=False`` and a fixed repository-relative receipt path avoid shell
    interpretation and worktree-file substitution.
    """

    commit = _require_commit(audit_commit_b, "r1d2_audit_commit_b")
    if not isinstance(repository_root, Path) or not repository_root.is_absolute():
        _fail("repository root for Git audit receipt must be absolute")
    if receipt_path != FINAL_AUDIT_RECEIPT_PATH:
        _fail("R1D2-AUDIT Git receipt path differs")
    try:
        resolved_repository = repository_root.resolve(strict=True)
    except OSError as exc:
        raise TASK039E3RecoveryAuthorizationV3Error(
            "repository root for Git audit receipt is unavailable"
        ) from exc
    try:
        completed = subprocess.run(
            [
                "git",
                "-C",
                str(resolved_repository),
                "cat-file",
                "blob",
                f"{commit}:{receipt_path}",
            ],
            check=False,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            shell=False,
        )
    except OSError as exc:
        raise TASK039E3RecoveryAuthorizationV3Error(
            "Git object inspection for R1D2-AUDIT receipt failed"
        ) from exc
    if completed.returncode != 0:
        _fail("authorized R1D2-AUDIT receipt Git object is unavailable")
    return bytes(completed.stdout)


def validate_final_audit_provenance_v3(
    *,
    authorization: ValidatedR2AuthorizationV3,
    external_audit_receipt: Mapping[str, Any],
    git_receipt_blob_loader: GitReceiptBlobLoaderV3,
) -> ValidatedFinalAuditProvenanceV3:
    """Verify the external PASS receipt and its exact authorized Git object."""

    external_hash = _validate_audit_receipt_document(
        external_audit_receipt, authorization=authorization
    )
    try:
        blob = git_receipt_blob_loader(
            authorization.r1d2_audit_commit_b, FINAL_AUDIT_RECEIPT_PATH
        )
    except Exception as exc:
        raise TASK039E3RecoveryAuthorizationV3Error(
            "authorized R1D2-AUDIT Git receipt is unavailable"
        ) from exc
    if not isinstance(blob, bytes):
        _fail("authorized R1D2-AUDIT Git receipt loader must return bytes")
    try:
        git_document = json.loads(blob.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise TASK039E3RecoveryAuthorizationV3Error(
            "authorized R1D2-AUDIT Git receipt is not valid UTF-8 JSON"
        ) from exc
    if not isinstance(git_document, Mapping):
        _fail("authorized R1D2-AUDIT Git receipt must be a JSON object")
    git_hash = _validate_audit_receipt_document(
        git_document, authorization=authorization
    )
    if dict(git_document) != dict(external_audit_receipt):
        _fail("external R1D2-AUDIT receipt differs from authorized Git object")
    if git_hash != external_hash:
        _fail("authorized Git and external audit receipt hashes differ")
    return ValidatedFinalAuditProvenanceV3(
        receipt_hash=external_hash,
        audit_commit_b=authorization.r1d2_audit_commit_b,
        audit_bundle_hash=authorization.r1d2_independent_audit_bundle_hash,
        receipt_path=FINAL_AUDIT_RECEIPT_PATH,
    )


def validate_historical_bindings_v3(
    *, capability_receipt_hash: str, provider_ledger_head_hash: str
) -> None:
    if capability_receipt_hash != HISTORICAL_CAPABILITY_RECEIPT_HASH:
        _fail("historical capability receipt binding differs")
    if provider_ledger_head_hash != HISTORICAL_PROVIDER_LEDGER_HEAD_HASH:
        _fail("historical provider-ledger head binding differs")


_CredentialT = TypeVar("_CredentialT")


@dataclass(frozen=True)
class PrecontactBootstrapV3:
    authorization: ValidatedR2AuthorizationV3
    git_state: GitExecutionStateV3
    final_audit: ValidatedFinalAuditProvenanceV3
    guarded_roots: Any
    scientific_preflight: Any
    credential: Any
    completed_guard_order: tuple[str, ...]


def run_ordered_precontact_guards_v3(
    *,
    authorization_document: Mapping[str, Any],
    prior_authority_state_loader: Callable[[], PriorAuthorityStateV3],
    git_state_loader: Callable[[], GitExecutionStateV3],
    external_audit_receipt: Mapping[str, Any],
    git_receipt_blob_loader: GitReceiptBlobLoaderV3,
    historical_capability_receipt_hash: str,
    historical_provider_ledger_head_hash: str,
    root_guard_loader: Callable[[], Any],
    scientific_preflight_loader: Callable[[], Any],
    credential_loader: Callable[[], _CredentialT],
    event_sink: Callable[[str], None] | None = None,
) -> PrecontactBootstrapV3:
    """Run every future V3 authority/audit guard before credential lookup.

    ``root_guard_loader`` is coordinator-supplied so the active runner can
    validate all private roots and the external public-output root as one
    indivisible pre-contact stage.
    """

    completed: list[str] = []

    def mark(stage: str) -> None:
        completed.append(stage)
        if event_sink is not None:
            event_sink(stage)

    authorization = validate_r2_authorization_v3(authorization_document)
    mark("r2_authorization_v3_validated")
    prior = prior_authority_state_loader()
    validate_prior_authority_state_v3(prior)
    mark("prior_authority_bindings_validated")
    git_state = git_state_loader()
    validate_git_and_source_state_v3(git_state, authorization=authorization)
    mark("r1d2_commit_a_and_source_manifest_validated")
    final_audit = validate_final_audit_provenance_v3(
        authorization=authorization,
        external_audit_receipt=external_audit_receipt,
        git_receipt_blob_loader=git_receipt_blob_loader,
    )
    mark("r1d2_audit_pass_and_git_provenance_validated")
    validate_historical_bindings_v3(
        capability_receipt_hash=historical_capability_receipt_hash,
        provider_ledger_head_hash=historical_provider_ledger_head_hash,
    )
    mark("historical_custody_bindings_validated")
    guarded_roots = root_guard_loader()
    mark("private_and_public_roots_validated")
    scientific_preflight = scientific_preflight_loader()
    mark("scientific_public_preflight_validated")
    credential = credential_loader()
    mark("credential_loaded")
    return PrecontactBootstrapV3(
        authorization=authorization,
        git_state=git_state,
        final_audit=final_audit,
        guarded_roots=guarded_roots,
        scientific_preflight=scientific_preflight,
        credential=credential,
        completed_guard_order=tuple(completed),
    )


__all__ = [
    "ARTIFACT_TYPE",
    "AUTHORIZATION_STATUS",
    "CORRECTED_CUSTODY_ACCOUNTING_HASH",
    "EXACT_MODEL",
    "FINAL_AUDIT_ARTIFACT_TYPE",
    "FINAL_AUDIT_PASS_STATUS",
    "FINAL_AUDIT_RECEIPT_PATH",
    "FINAL_AUDIT_TASK_ID",
    "GitExecutionStateV3",
    "HISTORICAL_CAPABILITY_PROBE_COUNT",
    "HISTORICAL_CAPABILITY_RECEIPT_HASH",
    "HISTORICAL_PROVIDER_LEDGER_HEAD_HASH",
    "MAXIMUM_ADDITIONAL_RECOVERY_PROBES",
    "MAXIMUM_CUMULATIVE_CAPABILITY_PROBES",
    "PrecontactBootstrapV3",
    "PriorAuthorityStateV3",
    "SCHEMA_VERSION",
    "TASK039E3RecoveryAuthorizationV3Error",
    "TASK_ID",
    "URLOPEN_TIMEOUT_SECONDS",
    "ValidatedFinalAuditProvenanceV3",
    "ValidatedR2AuthorizationV3",
    "run_ordered_precontact_guards_v3",
    "load_audit_receipt_git_blob_v3",
    "validate_final_audit_provenance_v3",
    "validate_git_and_source_state_v3",
    "validate_historical_bindings_v3",
    "validate_prior_authority_state_v3",
    "validate_r2_authorization_v3",
]
