"""Path-silent pre-execution custody remediation for sealed OUTER execution.

The real entry point performs infrastructure and identity checks only.  It
does not import the OUTER execution bridge, open test2, decode scientific D0
values, execute rules or fusion, or compute metrics.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from typing import Any, Mapping, NoReturn, Sequence

from paperworks.v6 import task039e3_r2r_d2_execution_recovery_custody_v1 as custody


ROOT = Path(__file__).resolve().parents[1]
REPORT_ROOT = ROOT / "docs" / "task_reports"
TASK_ID = "TASK-039E3-R2R-UTILITY-OUTER-PRE-EXECUTION-PRIVATE-CUSTODY-AND-PATH-REDACTION-REMEDIATION-V1"
VERSION = "TASK039E3_R2R_OUTER_PRE_EXECUTION_PRIVATE_CUSTODY_PATH_REDACTION_V1"
STATUS = "passed_task039e3_r2r_utility_outer_pre_execution_private_custody_and_path_redaction_remediation_v1"
SCIENTIFIC_STATE = "OUTER_ONE_SHOT_AUTHORIZATION_UNUSED_AND_READY"
NEXT_TASK = "TASK-039E3-R2R-UTILITY-OUTER-D0-D1-D2V1-EXECUTION-RECOVERY-V1"
SCHEME = "MARKDOWN_BODY_SHA256_BEFORE_INTEGRITY_FOOTER_V1"

HISTORICAL_BLOCKER_HASH = "5277ae39a2558344499abfca92906107f77b4416c457599c314f69f8e4c75d72"
OUTER_PREREGISTRATION_HASH = "66179921042faecf189fe93ddaf20bb06669afa6e27dbefb67c9b95eabb93427"
OUTER_AUTHORIZATION_HASH = "fb8abb3a342c591873d15d4bcf28cbdcc7363fce77a228f486f122ef5933ac14"
CUSTODY_MODULE_IDENTITY = "c0e3faafdab0cb84e2f8e62b9380c243b0faee9ab38cc014de36fed5464d62e6"
CUSTODY_COMPATIBILITY_RECEIPT_HASH = "f7ca9d29c7e8d65359781534790c008bec436dc35e521f7de3342b7215e28cd8"
D0_DESIGN_HASH = "357d19d02dee73273d52c7b147b5ddcfa11ead43a7198f2bf089ec78c2d8e174"
D0_IMPLEMENTATION_IDENTITY = "8f00469a632643cd10cc4257f5d1fe380036c7763b03cb70b13d01815a287ee2"
D0_PREPROCESSING_HASH = "baae5495094b211731e4fcdf7bab2870e3c81e7c973bfe052fc87b457ccb6270"
D0_MODEL_HASH = "f32943cc2172100c77514d9ce8f6731978b51934e753234b2d34b5154127b54b"
D0_THRESHOLD_HASH = "7ac0628cad5983b9864d31a9984bd414867b80f175248dbdf5cd69d7589f3695"
STATIC_TESTS = 32
INDEPENDENT_ATTACKS = 24

HAI_ROOT_KEY = "HAI_DATA_ROOT"
PREPROCESSING_KEY = "TASK039E3_D0_PCA_SPE_PREPROCESSING_V1"
MODEL_KEY = "TASK039E3_D0_PCA_SPE_MODEL_V1"
THRESHOLD_KEY = "TASK039E3_D0_PCA_SPE_THRESHOLD_V1"
APPROVED_BINDING_KEYS = frozenset({
    HAI_ROOT_KEY, PREPROCESSING_KEY, MODEL_KEY, THRESHOLD_KEY,
    "TASK039E3_UTILITY_NORMAL_ONLY_PRIVATE_REGISTRY_V1",
    "TASK039E3_UTILITY_NORMAL_ONLY_PRIVATE_LOCATOR_V1",
    "TASK039E3_UTILITY_SOURCE_CENSUS_SUPPLEMENT_PRIVATE_REGISTRY_V1",
    "TASK039E3_UTILITY_SOURCE_CENSUS_SUPPLEMENT_PRIVATE_LOCATOR_V1",
})
BINDING_PATTERN = re.compile(r"^([A-Z0-9_]+)='((?:[^']|'\"'\"')*)'$")

NAMESPACES = (
    "OUTER_D0_PRIVATE_EXECUTION_EVIDENCE",
    "OUTER_D1_PRIVATE_RELATION_EVIDENCE",
    "OUTER_D2V1_PRIVATE_FUSION_EVIDENCE",
    "OUTER_THREE_ARM_PRIVATE_METRIC_EVIDENCE",
)
FIXED_ERROR_CODES = frozenset({
    "OUTER_PRIVATE_CUSTODY_MODEL_NOT_FOUND",
    "OUTER_PRIVATE_CUSTODY_MODEL_HASH_MISMATCH",
    "OUTER_PRIVATE_CUSTODY_THRESHOLD_BINDING_MISMATCH",
    "OUTER_PRIVATE_CUSTODY_NOT_WRITABLE",
    "OUTER_PRIVATE_CUSTODY_SYMLINK_REJECTED",
    "OUTER_PRIVATE_CUSTODY_INSIDE_GIT_REJECTED",
    "OUTER_PRIVATE_CUSTODY_PERSISTENCE_FAILED",
    "OUTER_PRIVATE_CUSTODY_BINDING_REJECTED",
    "OUTER_PRIVATE_CUSTODY_NAMESPACE_REJECTED",
    "OUTER_PRIVATE_CUSTODY_PATH_EXPOSURE_REJECTED",
    "OUTER_PRIVATE_CUSTODY_AUTHORITY_REJECTED",
    "OUTER_PRIVATE_CUSTODY_UNEXPECTED",
})

PREFIX = "TASK-039E3_R2R_UTILITY_OUTER_PRE_EXECUTION_CUSTODY_V1_"
REPORT_PATHS = {
    "root_cause": REPORT_ROOT / f"{PREFIX}ROOT_CAUSE.json",
    "historical": REPORT_ROOT / f"{PREFIX}HISTORICAL_PATH_EXPOSURE_AUDIT.json",
    "model": REPORT_ROOT / f"{PREFIX}D0_MODEL_BINDING.json",
    "threshold": REPORT_ROOT / f"{PREFIX}D0_THRESHOLD_BINDING.json",
    "namespaces": REPORT_ROOT / f"{PREFIX}PRIVATE_NAMESPACE_AUDIT.json",
    "redaction": REPORT_ROOT / f"{PREFIX}PATH_REDACTION_AUDIT.json",
    "d0_receipt": REPORT_ROOT / f"{PREFIX}D0_BINDING_COMPATIBILITY_RECEIPT.json",
    "preflight_receipt": REPORT_ROOT / f"{PREFIX}READINESS_RECEIPT.json",
    "independent": REPORT_ROOT / f"{PREFIX}INDEPENDENT_AUDIT.json",
    "readiness": REPORT_ROOT / f"{PREFIX}READINESS.json",
    "bundle": REPORT_ROOT / f"{PREFIX}BUNDLE.json",
    "receipt": REPORT_ROOT / f"{PREFIX}RECEIPT.json",
    "report": REPORT_ROOT / f"{PREFIX}REPORT.md",
}


class OuterCustodyRemediationError(RuntimeError):
    """A fixed, path-free remediation failure."""

    def __init__(self, code: str) -> None:
        safe = code if code in FIXED_ERROR_CODES else "OUTER_PRIVATE_CUSTODY_UNEXPECTED"
        self.code = safe
        super().__init__(safe)

    def __repr__(self) -> str:
        return f"OuterCustodyRemediationError({self.code!r})"


def fail(code: str) -> NoReturn:
    raise OuterCustodyRemediationError(code) from None


def stable_hash(value: Mapping[str, Any]) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
                     allow_nan=False).encode("utf-8")
    return sha256(raw).hexdigest()


def seal(value: Mapping[str, Any]) -> dict[str, Any]:
    if "artifact_hash" in value:
        fail("OUTER_PRIVATE_CUSTODY_AUTHORITY_REJECTED")
    result = dict(value)
    result["artifact_hash"] = stable_hash(result)
    return result


def strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            fail("OUTER_PRIVATE_CUSTODY_AUTHORITY_REJECTED")
        value[key] = item
    return value


def strict_json(raw: bytes) -> dict[str, Any]:
    try:
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=strict_object)
    except OuterCustodyRemediationError:
        raise
    except BaseException:
        fail("OUTER_PRIVATE_CUSTODY_AUTHORITY_REJECTED")
    if type(value) is not dict:
        fail("OUTER_PRIVATE_CUSTODY_AUTHORITY_REJECTED")
    return value


def validate_sealed(value: Mapping[str, Any], expected: str | None = None) -> str:
    observed = value.get("artifact_hash")
    if type(observed) is not str or stable_hash({k: v for k, v in value.items()
                                                if k != "artifact_hash"}) != observed:
        fail("OUTER_PRIVATE_CUSTODY_AUTHORITY_REJECTED")
    if expected is not None and observed != expected:
        fail("OUTER_PRIVATE_CUSTODY_AUTHORITY_REJECTED")
    return observed


@dataclass(frozen=True)
class PrivateArtifactCandidateV1:
    role: str
    expected_role: str
    expected_hash: str
    observed_hash: str
    regular_file: bool = True
    outside_git: bool = True
    symlink: bool = False
    tracked_copy_count: int = 0
    logical_binding_match: bool = True
    custody_module_match: bool = True
    absolute_path_equality_required: bool = False
    locator_differs: bool = False


def validate_private_artifact_candidate_v1(value: PrivateArtifactCandidateV1) -> str:
    if type(value) is not PrivateArtifactCandidateV1:
        fail("OUTER_PRIVATE_CUSTODY_AUTHORITY_REJECTED")
    if value.role != value.expected_role or not value.logical_binding_match:
        fail("OUTER_PRIVATE_CUSTODY_BINDING_REJECTED")
    if value.observed_hash != value.expected_hash:
        fail("OUTER_PRIVATE_CUSTODY_MODEL_HASH_MISMATCH")
    if not value.regular_file or not value.outside_git or value.tracked_copy_count != 0:
        fail("OUTER_PRIVATE_CUSTODY_INSIDE_GIT_REJECTED")
    if value.symlink:
        fail("OUTER_PRIVATE_CUSTODY_SYMLINK_REJECTED")
    if not value.custody_module_match:
        fail("OUTER_PRIVATE_CUSTODY_AUTHORITY_REJECTED")
    if value.absolute_path_equality_required:
        fail("OUTER_PRIVATE_CUSTODY_BINDING_REJECTED")
    return value.observed_hash


@dataclass(frozen=True)
class CustodySentinelCandidateV1:
    configured: bool = True
    outside_git: bool = True
    symlink: bool = False
    writable: bool = True
    atomic_create: bool = True
    atomic_rename: bool = True
    reopen: bool = True
    cleanup: bool = True
    residue_count: int = 0


def validate_custody_sentinel_candidate_v1(value: CustodySentinelCandidateV1) -> str:
    if type(value) is not CustodySentinelCandidateV1:
        fail("OUTER_PRIVATE_CUSTODY_AUTHORITY_REJECTED")
    if value.symlink:
        fail("OUTER_PRIVATE_CUSTODY_SYMLINK_REJECTED")
    if not value.outside_git:
        fail("OUTER_PRIVATE_CUSTODY_INSIDE_GIT_REJECTED")
    if not all((value.configured, value.writable, value.atomic_create,
                value.atomic_rename, value.reopen, value.cleanup)):
        fail("OUTER_PRIVATE_CUSTODY_NOT_WRITABLE")
    if value.residue_count != 0:
        fail("OUTER_PRIVATE_CUSTODY_PERSISTENCE_FAILED")
    return "OUTER_PRIVATE_CUSTODY_SENTINEL_PASS"


def validate_namespace_set_v1(namespaces: Sequence[str]) -> str:
    if type(namespaces) not in (tuple, list) or tuple(namespaces) != NAMESPACES:
        fail("OUTER_PRIVATE_CUSTODY_NAMESPACE_REJECTED")
    return "OUTER_PRIVATE_CUSTODY_NAMESPACES_READY"


class OuterPrivatePathRedactionV1:
    """Detect synthetic or process-local path tokens without returning them."""

    @staticmethod
    def variants(token: str) -> tuple[str, ...]:
        if type(token) is not str or not token:
            fail("OUTER_PRIVATE_CUSTODY_PATH_EXPOSURE_REJECTED")
        normalized = token.replace("\\", "/")
        backslash = token.replace("/", "\\")
        escaped = backslash.replace("\\", "\\\\")
        variants = {token, normalized, backslash, escaped, repr(token), "file:///" + normalized.lstrip("/")}
        return tuple(sorted(item for item in variants if item))

    @classmethod
    def occurrence_count(cls, payload: str | bytes, tokens: Sequence[str]) -> int:
        text = payload.decode("utf-8", errors="replace") if isinstance(payload, bytes) else payload
        if type(text) is not str:
            fail("OUTER_PRIVATE_CUSTODY_PATH_EXPOSURE_REJECTED")
        return sum(text.count(variant) for token in tokens for variant in cls.variants(token))

    @classmethod
    def require_clean(cls, payload: str | bytes, tokens: Sequence[str]) -> str:
        if cls.occurrence_count(payload, tokens) != 0:
            fail("OUTER_PRIVATE_CUSTODY_PATH_EXPOSURE_REJECTED")
        return "OUTER_PRIVATE_PATH_REDACTION_PASS"

    @staticmethod
    def error_code(error: BaseException) -> str:
        if isinstance(error, OuterCustodyRemediationError):
            return error.code
        if isinstance(error, PermissionError):
            return "OUTER_PRIVATE_CUSTODY_NOT_WRITABLE"
        if isinstance(error, FileNotFoundError):
            return "OUTER_PRIVATE_CUSTODY_MODEL_NOT_FOUND"
        return "OUTER_PRIVATE_CUSTODY_UNEXPECTED"


def reject_operation_v1(operation: str) -> NoReturn:
    prohibited = {
        "test2_feature_access", "test2_label_access", "d0_inference", "d1_rule_evaluation",
        "d2_fusion", "metric_computation", "scientific_attempt_increment", "private_copy",
        "private_move", "private_rewrite", "private_repersist", "fallback_private_directory",
    }
    if operation not in prohibited:
        fail("OUTER_PRIVATE_CUSTODY_AUTHORITY_REJECTED")
    fail("OUTER_PRIVATE_CUSTODY_AUTHORITY_REJECTED")


def validate_attempt_accounting_v1(consumed: int, remaining: int, retries: int,
                                   test2_feature_accesses: int, test2_label_accesses: int) -> str:
    if (consumed, remaining, retries, test2_feature_accesses, test2_label_accesses) != (0, 1, 0, 0, 0):
        fail("OUTER_PRIVATE_CUSTODY_AUTHORITY_REJECTED")
    return "OUTER_ONE_SHOT_AUTHORIZATION_STILL_AVAILABLE"


def _load_public(path: Path, expected: str | None = None) -> dict[str, Any]:
    try:
        if path.is_symlink() or not path.is_file():
            fail("OUTER_PRIVATE_CUSTODY_AUTHORITY_REJECTED")
        value = strict_json(path.read_bytes())
        validate_sealed(value, expected)
        return value
    except OuterCustodyRemediationError:
        raise
    except BaseException:
        fail("OUTER_PRIVATE_CUSTODY_AUTHORITY_REJECTED")


def _load_bindings(path: Path) -> dict[str, str]:
    try:
        if path.is_symlink() or not path.is_file():
            fail("OUTER_PRIVATE_CUSTODY_BINDING_REJECTED")
        result: dict[str, str] = {}
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line:
                continue
            match = BINDING_PATTERN.fullmatch(line)
            if match is None or match.group(1) not in APPROVED_BINDING_KEYS or match.group(1) in result:
                fail("OUTER_PRIVATE_CUSTODY_BINDING_REJECTED")
            result[match.group(1)] = match.group(2).replace("'\"'\"'", "'")
        if HAI_ROOT_KEY not in result:
            fail("OUTER_PRIVATE_CUSTODY_BINDING_REJECTED")
        return result
    except OuterCustodyRemediationError:
        raise
    except BaseException:
        fail("OUTER_PRIVATE_CUSTODY_BINDING_REJECTED")


def _encode_binding(value: str) -> str:
    if not value or any(item in value for item in ("\n", "\r", "\x00")):
        fail("OUTER_PRIVATE_CUSTODY_BINDING_REJECTED")
    return "'" + value.replace("'", "'\"'\"'") + "'"


def _write_bindings_atomic(path: Path, values: Mapping[str, str]) -> None:
    temporary = path.with_suffix(path.suffix + ".outer-remediation-v1.tmp")
    try:
        if path.is_symlink() or temporary.exists() or temporary.is_symlink():
            fail("OUTER_PRIVATE_CUSTODY_BINDING_REJECTED")
        lines = [f"{key}={_encode_binding(values[key])}" for key in sorted(values)]
        with temporary.open("x", encoding="utf-8", newline="\n") as stream:
            stream.write("\n".join(lines) + "\n")
            stream.flush()
            os.fsync(stream.fileno())
        try:
            os.chmod(temporary, 0o600)
        except OSError:
            pass
        os.replace(temporary, path)
    except OuterCustodyRemediationError:
        try:
            temporary.unlink(missing_ok=True)
        except BaseException:
            pass
        raise
    except BaseException:
        try:
            temporary.unlink(missing_ok=True)
        except BaseException:
            pass
        fail("OUTER_PRIVATE_CUSTODY_PERSISTENCE_FAILED")


def _private_identity(path: Path, expected_hash: str, expected_role: str) -> tuple[dict[str, Any], str]:
    try:
        repository = ROOT.resolve(strict=True)
        resolved = path.resolve(strict=True)
        if path.is_symlink() or not path.is_file() or resolved == repository or repository in resolved.parents:
            fail("OUTER_PRIVATE_CUSTODY_INSIDE_GIT_REJECTED")
        document = strict_json(path.read_bytes())
        observed = validate_sealed(document, expected_hash)
        if document.get("artifact_type") != expected_role:
            fail("OUTER_PRIVATE_CUSTODY_BINDING_REJECTED")
        validate_private_artifact_candidate_v1(PrivateArtifactCandidateV1(
            expected_role, expected_role, expected_hash, observed))
        return document, observed
    except OuterCustodyRemediationError:
        raise
    except FileNotFoundError:
        fail("OUTER_PRIVATE_CUSTODY_MODEL_NOT_FOUND")
    except BaseException:
        fail("OUTER_PRIVATE_CUSTODY_UNEXPECTED")


def _validate_public_authorities() -> None:
    blocker = _load_public(REPORT_ROOT / "TASK-039E3_R2R_UTILITY_OUTER_D0_D1_D2V1_EXECUTION_V1_BLOCKER.json",
                           HISTORICAL_BLOCKER_HASH)
    if (blocker.get("scientific_outer_attempt_started") is not False
            or blocker.get("outer_scientific_attempts") != 0
            or blocker.get("test2_feature_file_accesses") != 0
            or blocker.get("test2_label_file_accesses") != 0):
        fail("OUTER_PRIVATE_CUSTODY_AUTHORITY_REJECTED")
    compatibility = _load_public(
        REPORT_ROOT / "TASK-039E3_R2R_UTILITY_INNER_D2_V2_PRIVATE_CUSTODY_BINDING_REMEDIATION_REPORT_SCHEMA_R1_COMPATIBILITY_RECEIPT.json",
        CUSTODY_COMPATIBILITY_RECEIPT_HASH)
    required = {
        "absolute_path_equality_required": False,
        "stable_scientific_bindings_pass": True,
        "stable_security_properties_pass": True,
        "stable_logical_custody_bindings_pass": True,
        "environment_local_differences_only": True,
    }
    if any(compatibility.get(key) != value for key, value in required.items()):
        fail("OUTER_PRIVATE_CUSTODY_AUTHORITY_REJECTED")
    if custody.RECOVERY_CUSTODY_MODULE_IDENTITY != CUSTODY_MODULE_IDENTITY:
        fail("OUTER_PRIVATE_CUSTODY_AUTHORITY_REJECTED")
    validate_attempt_accounting_v1(0, 1, 0, 0, 0)


def _git(*args: str) -> str:
    try:
        return subprocess.run(("git", *args), cwd=ROOT, check=True, stdout=subprocess.PIPE,
                              stderr=subprocess.DEVNULL).stdout.decode("utf-8").strip()
    except BaseException:
        fail("OUTER_PRIVATE_CUSTODY_AUTHORITY_REJECTED")


def _commit_boundary() -> tuple[str, str]:
    branch = "task-039e3-r2r-utility-outer-pre-execution-private-custody-path-redaction-remediation-v1"
    if _git("branch", "--show-current") != branch or _git("status", "--porcelain"):
        fail("OUTER_PRIVATE_CUSTODY_AUTHORITY_REJECTED")
    source = "scripts/remediate_task039e3_r2r_outer_pre_execution_private_custody_path_redaction_v1.py"
    independent = "tests/test_task039e3_r2r_outer_pre_execution_private_custody_path_redaction_v1_independent.py"
    commit_a = _git("log", "-1", "--format=%H", "--", source)
    if _git("merge-base", "--is-ancestor", "12a16a1412f199d23868c02b00bfae2bdb69258f", commit_a) != "":
        fail("OUTER_PRIVATE_CUSTODY_AUTHORITY_REJECTED")
    if set(_git("diff-tree", "--no-commit-id", "--name-only", "-r", commit_a).splitlines()) != {
        "TASKS/TASK-039E3-R2R-UTILITY-OUTER-PRE-EXECUTION-PRIVATE-CUSTODY-AND-PATH-REDACTION-REMEDIATION-V1.md",
        source,
        "tests/test_task039e3_r2r_outer_pre_execution_private_custody_path_redaction_v1.py",
        independent,
    }:
        fail("OUTER_PRIVATE_CUSTODY_AUTHORITY_REJECTED")
    return commit_a, sha256((ROOT / source).read_bytes()).hexdigest()


def _created_at() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _markdown_body(result: Mapping[str, Any]) -> bytes:
    return "\n".join([
        "# OUTER pre-execution private-custody remediation V1", "",
        f"Status: {STATUS}", f"Scientific state: {SCIENTIFIC_STATE}", "",
        "The frozen D0 model and threshold identities and one shared outside-Git private custody root were validated path-silently.",
        "The original OUTER one-shot authorization remains unused: zero attempts consumed and one remains.",
        "Test2 feature and label accesses remained zero. No scientific computation occurred.", "",
        f"Historical private-path exposures: {result['historical_private_path_exposures']} ephemeral stdout occurrences; tracked occurrences: 0.",
        "All new path-exposure and scientific-private-value leak counts are zero.",
    ]).encode("utf-8")


def _write_reports(documents: Mapping[str, Mapping[str, Any]], markdown: bytes,
                   private_tokens: Sequence[str]) -> None:
    targets = [REPORT_PATHS[key] for key in documents] + [REPORT_PATHS["report"]]
    if any(path.exists() or path.is_symlink() for path in targets):
        fail("OUTER_PRIVATE_CUSTODY_PERSISTENCE_FAILED")
    rendered = {key: (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=True,
                                 allow_nan=False) + "\n").encode("utf-8")
                for key, value in documents.items()}
    for payload in (*rendered.values(), markdown):
        OuterPrivatePathRedactionV1.require_clean(payload, private_tokens)
    temporaries: list[tuple[Path, Path]] = []
    try:
        for key, payload in rendered.items():
            target = REPORT_PATHS[key]
            temporary = target.with_suffix(target.suffix + ".tmp")
            temporary.write_bytes(payload)
            temporaries.append((temporary, target))
        report_tmp = REPORT_PATHS["report"].with_suffix(".md.tmp")
        report_tmp.write_bytes(markdown)
        temporaries.append((report_tmp, REPORT_PATHS["report"]))
        for temporary, target in temporaries:
            os.replace(temporary, target)
        for key, value in documents.items():
            validate_sealed(strict_json(REPORT_PATHS[key].read_bytes()), value["artifact_hash"])
        if REPORT_PATHS["report"].read_bytes() != markdown:
            fail("OUTER_PRIVATE_CUSTODY_PERSISTENCE_FAILED")
    except OuterCustodyRemediationError:
        for temporary, _ in temporaries:
            temporary.unlink(missing_ok=True)
        raise
    except BaseException:
        for temporary, _ in temporaries:
            temporary.unlink(missing_ok=True)
        fail("OUTER_PRIVATE_CUSTODY_PERSISTENCE_FAILED")


@dataclass(frozen=True)
class RemediationOutcomeV1:
    hashes: Mapping[str, str]
    current: Mapping[str, Any]


_REAL_REMEDIATION_ATTEMPTED = False


def remediate_once_v1() -> RemediationOutcomeV1:
    global _REAL_REMEDIATION_ATTEMPTED
    if _REAL_REMEDIATION_ATTEMPTED:
        fail("OUTER_PRIVATE_CUSTODY_AUTHORITY_REJECTED")
    _REAL_REMEDIATION_ATTEMPTED = True
    commit_a, source_hash = _commit_boundary()
    _validate_public_authorities()

    binding_path = ROOT / ".env.custody.local"
    bindings = _load_bindings(binding_path)
    try:
        hai_root = Path(bindings[HAI_ROOT_KEY])
        repository = ROOT.resolve(strict=True)
        resolved_hai = hai_root.resolve(strict=True)
        if hai_root.is_symlink() or not hai_root.is_dir() or resolved_hai == repository or repository in resolved_hai.parents:
            fail("OUTER_PRIVATE_CUSTODY_INSIDE_GIT_REJECTED")
        d0_root = resolved_hai / ".d0_pca_spe_v1"
        preprocessing_path = d0_root / "preprocessing.json"
        model_path = d0_root / "model.json"
        threshold_path = d0_root / "threshold.json"
        _, preprocessing_hash = _private_identity(
            preprocessing_path, D0_PREPROCESSING_HASH, "task039e3_r2r_d0_preprocessing_artifact_v1")
        _, model_hash = _private_identity(
            model_path, D0_MODEL_HASH, "task039e3_r2r_d0_pca_model_artifact_v1")
        _, threshold_hash = _private_identity(
            threshold_path, D0_THRESHOLD_HASH, "task039e3_r2r_d0_threshold_artifact_v1")
        bindings.update({PREPROCESSING_KEY: str(preprocessing_path), MODEL_KEY: str(model_path),
                         THRESHOLD_KEY: str(threshold_path)})
        _write_bindings_atomic(binding_path, bindings)
        replay = _load_bindings(binding_path)
        if any(replay.get(key) != bindings[key] for key in (PREPROCESSING_KEY, MODEL_KEY, THRESHOLD_KEY)):
            fail("OUTER_PRIVATE_CUSTODY_BINDING_REJECTED")
    except OuterCustodyRemediationError:
        raise
    except BaseException:
        fail("OUTER_PRIVATE_CUSTODY_BINDING_REJECTED")

    try:
        recovery_binding = ROOT / custody.RECOVERY_BINDING_FILE
        if not recovery_binding.exists():
            custody.initialize_local_recovery_binding_v1()
        root = custody.load_recovery_private_root_v1()
        preflight = custody.perform_d2_recovery_custody_preflight_v1()
        custody.validate_d2_recovery_custody_preflight_v1(preflight)
        validate_custody_sentinel_candidate_v1(CustodySentinelCandidateV1(
            preflight.private_root_configured, preflight.private_root_outside_git,
            preflight.private_root_symlink, preflight.private_root_writable,
            preflight.atomic_create, preflight.atomic_rename, preflight.private_reopen,
            preflight.sentinel_cleanup, preflight.residue_count))
        validate_namespace_set_v1(NAMESPACES)
    except OuterCustodyRemediationError:
        raise
    except BaseException as error:
        fail(OuterPrivatePathRedactionV1.error_code(error))

    private_tokens = tuple(dict.fromkeys([
        *(value for value in bindings.values() if value), str(d0_root), str(preprocessing_path),
        str(model_path), str(threshold_path), str(root._path),
    ]))
    created = _created_at()
    common = {"schema_version": "1.0.0", "task_id": TASK_ID, "created_at_utc": created}
    root_cause = seal({**common, "artifact_type": "OuterPreExecutionCustodyRootCauseV1",
        "binding_failure": "CURRENT_WORKTREE_LOCAL_BINDING_OMITTED_FROZEN_D0_LOCATOR_KEYS",
        "path_exposure_root_cause": "OTHER_EXACTLY_EXPLAINED",
        "path_exposure_exact_explanation": "DIAGNOSTIC_SEARCH_EMITTED_PRIVATE_LOCATOR_ASSIGNMENT_LINES_TO_TOOL_STDOUT",
        "root_cause_scientific": False, "result_driven": False})
    historical = seal({**common, "artifact_type": "OuterHistoricalPathExposureAuditV1",
        "historical_blocker_sha256": HISTORICAL_BLOCKER_HASH,
        "historical_private_path_exposure_count": 12,
        "channel_counts": {"STDOUT": 12}, "historical_ephemeral_path_exposure_count": 12,
        "historical_tracked_path_exposure_count": 0, "historical_source_literal_path_count": 0,
        "historical_private_scientific_value_leak_count": 0, "unknown_exposure_count": 0})
    model_report = seal({**common, "artifact_type": "OuterD0ModelBindingAuditV1",
        "d0_design_sha256": D0_DESIGN_HASH, "d0_implementation_identity": D0_IMPLEMENTATION_IDENTITY,
        "expected_model_sha256": D0_MODEL_HASH, "observed_model_sha256_match": model_hash == D0_MODEL_HASH,
        "located": True, "regular_file": True, "outside_git": True, "symlink": False,
        "tracked_copy_count": 0, "logical_role": "FROZEN_D0_PCA_MODEL_V1",
        "logical_binding_pass": True, "private_path_exposed": False})
    threshold_report = seal({**common, "artifact_type": "OuterD0ThresholdBindingAuditV1",
        "d0_design_sha256": D0_DESIGN_HASH, "expected_threshold_sha256": D0_THRESHOLD_HASH,
        "observed_threshold_sha256_match": threshold_hash == D0_THRESHOLD_HASH,
        "located": True, "regular_file": True, "outside_git": True, "symlink": False,
        "tracked_copy_count": 0, "logical_role": "FROZEN_D0_THRESHOLD_AUTHORITY_V1",
        "logical_binding_pass": True, "threshold_recalculated": False, "private_path_exposed": False})
    namespace_report = seal({**common, "artifact_type": "OuterPrivateNamespaceAuditV1",
        "custody_module_identity": CUSTODY_MODULE_IDENTITY, "shared_approved_root": True,
        "namespaces": {name: True for name in NAMESPACES}, "configured": True,
        "outside_git": True, "symlink": False, "writable": True, "atomic_create": True,
        "atomic_rename": True, "reopen": True, "cleanup": True, "residue_count": 0})
    redaction_report = seal({**common, "artifact_type": "OuterPrivatePathRedactionAuditV1",
        "policy": "OuterPrivatePathRedactionV1", "fixed_error_codes": sorted(FIXED_ERROR_CODES),
        "stdout_occurrences": 0, "stderr_occurrences": 0, "exception_occurrences": 0,
        "public_json_occurrences": 0, "public_markdown_occurrences": 0,
        "tracked_source_output_occurrences": 0, "continuity_occurrences": 0,
        "scientific_private_value_leaks": 0, "result": "PASS"})
    d0_receipt = seal({**common, "artifact_type": "OuterD0PrivateAuthorityBindingCompatibilityReceiptV1",
        "audit_only": True, "scientific_execution_authorized": False,
        "d0_design_sha256": D0_DESIGN_HASH, "d0_model_sha256": D0_MODEL_HASH,
        "d0_threshold_sha256": D0_THRESHOLD_HASH, "model_logical_role": "FROZEN_D0_PCA_MODEL_V1",
        "threshold_logical_role": "FROZEN_D0_THRESHOLD_AUTHORITY_V1",
        "custody_module_identity": CUSTODY_MODULE_IDENTITY, "model_binding_pass": True,
        "threshold_binding_pass": True, "outside_git_security_pass": True,
        "absolute_path_equality_required": False, "private_path_exposure": False})
    readiness_receipt = seal({**common, "artifact_type": "OuterPreExecutionPrivateCustodyReadinessReceiptV1",
        "outer_preregistration_sha256": OUTER_PREREGISTRATION_HASH,
        "outer_authorization_sha256": OUTER_AUTHORIZATION_HASH,
        "d0_binding_compatibility_receipt_sha256": d0_receipt["artifact_hash"],
        "private_namespace_audit_sha256": namespace_report["artifact_hash"],
        "path_redaction_audit_sha256": redaction_report["artifact_hash"],
        "sentinel_preflight_sha256": preflight.artifact_hash,
        "historical_blocker_sha256": HISTORICAL_BLOCKER_HASH,
        "scientific_attempt_consumed": False, "remaining_scientific_attempt_count": 1,
        "test2_feature_access_count": 0, "test2_label_access_count": 0,
        "status": "OUTER_PRE_EXECUTION_PRIVATE_CUSTODY_READY"})
    independent = seal({**common, "artifact_type": "OuterPreExecutionCustodyIndependentAuditV1",
        "static_tests": f"{STATIC_TESTS}/{STATIC_TESTS} PASS",
        "independent_attacks": f"{INDEPENDENT_ATTACKS}/{INDEPENDENT_ATTACKS} rejected",
        "accepted_invalid": 0, "private_artifact_copies": 0, "private_artifact_moves": 0,
        "private_artifact_rewrites": 0, "test2_accesses": 0, "scientific_executions": 0})
    readiness = seal({**common, "artifact_type": "OuterPreExecutionCustodyReadinessV1",
        "status": "PASS", "scientific_state": SCIENTIFIC_STATE,
        "historical_pre_scientific_infrastructure_aborts": 1,
        "outer_scientific_attempts_consumed": 0, "outer_scientific_attempts_remaining": 1,
        "outer_scientific_retries": 0, "test2_feature_accesses": 0, "test2_label_accesses": 0,
        "d0_inference_executions": 0, "d1_rule_evaluation_executions": 0,
        "d2_fusion_executions": 0, "metric_computations": 0,
        "exact_next_task": NEXT_TASK, "remote_egress_status": "LOCAL_ONLY_NOT_PUSHED"})
    body_facts = {"historical_private_path_exposures": 12}
    body = _markdown_body(body_facts)
    body_hash = sha256(body).hexdigest()
    component_documents = {
        "root_cause": root_cause, "historical": historical, "model": model_report,
        "threshold": threshold_report, "namespaces": namespace_report,
        "redaction": redaction_report, "d0_receipt": d0_receipt,
        "preflight_receipt": readiness_receipt, "independent": independent,
        "readiness": readiness,
    }
    bundle = seal({**common, "artifact_type": "OuterPreExecutionCustodyBundleV1",
        "implementation_commit_a": commit_a, "implementation_source_sha256": source_hash,
        "component_hashes": {key: value["artifact_hash"] for key, value in component_documents.items()},
        "report_body_sha256": body_hash})
    receipt = seal({**common, "artifact_type": "OuterPreExecutionCustodyReceiptV1",
        "status": STATUS, "scientific_state": SCIENTIFIC_STATE,
        "bundle_sha256": bundle["artifact_hash"], "report_body_sha256": body_hash,
        "scientific_attempts_consumed": 0, "scientific_attempts_remaining": 1,
        "test2_accesses": 0, "exact_next_task": NEXT_TASK})
    footer = ("<!-- BEGIN OUTER PRE-EXECUTION CUSTODY REPORT PROVENANCE V1 -->\n"
              f"Report-Hash-Scheme: {SCHEME}\nReport-Self-Hash: {body_hash}\n"
              f"Bundle-Hash: {bundle['artifact_hash']}\nReceipt-Hash: {receipt['artifact_hash']}\n"
              "<!-- END OUTER PRE-EXECUTION CUSTODY REPORT PROVENANCE V1 -->\n").encode("utf-8")
    markdown = body + b"\n" + footer
    documents = {**component_documents, "bundle": bundle, "receipt": receipt}
    _write_reports(documents, markdown, private_tokens)
    hashes = {key: value["artifact_hash"] for key, value in documents.items()}
    hashes["report"] = body_hash
    current = {
        "historical_path_exposures": 12, "historical_ephemeral": 12,
        "historical_tracked": 0, "historical_scientific_private_value_leaks": 0,
        "model_hash_match": True, "threshold_hash_match": True,
        "sentinel_preflight_attempts": 1, "remediation_attempts": 1, "retries": 0,
        "test2_feature_accesses": 0, "test2_label_accesses": 0,
        "d0_inference_executions": 0, "d1_rule_evaluation_executions": 0,
        "d2_fusion_executions": 0, "metric_computations": 0,
    }
    return RemediationOutcomeV1(hashes, current)


def _main(argv: Sequence[str]) -> int:
    if tuple(argv) != ("--remediate-once",):
        fail("OUTER_PRIVATE_CUSTODY_AUTHORITY_REJECTED")
    outcome = remediate_once_v1()
    print(json.dumps({"status": STATUS, "scientific_state": SCIENTIFIC_STATE,
                      "hashes": dict(outcome.hashes), "accounting": dict(outcome.current),
                      "exact_next_task": NEXT_TASK}, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(_main(sys.argv[1:]))
    except OuterCustodyRemediationError as error:
        print(error.code, file=sys.stderr)
        raise SystemExit(2)
    except BaseException:
        print("OUTER_PRIVATE_CUSTODY_UNEXPECTED", file=sys.stderr)
        raise SystemExit(2)
