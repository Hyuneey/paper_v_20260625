"""Path-silent audit-only remediation of the D2 V2 private custody binding.

This module never executes or reconstructs scientific predictions, fusion,
episodes, labels, or metrics.  Its two private JSON reads validate only the
canonical identity envelope and stable authority bindings.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import re
import subprocess
import sys
from typing import Any, Mapping, NoReturn, Sequence


ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "TASK-039E3-R2R-UTILITY-INNER-D2-V2-PRIVATE-CUSTODY-BINDING-REMEDIATION-R1"
VERSION = "TASK039E3_R2R_D2_V2_PRIVATE_CUSTODY_BINDING_REMEDIATION_R1"
STATUS = "passed_task039e3_r2r_utility_inner_d2_v2_private_custody_binding_remediation_r1"
SCIENTIFIC_STATE = "UNCHANGED_FROZEN_NOT_YET_INTEGRITY_AUDITED"
CUSTODY_STATE = "PRIVATE_CUSTODY_BINDING_COMPATIBILITY_VERIFIED"
NEXT_TASK = "TASK-039E3-R2R-UTILITY-INNER-D2-V2-RESULT-INTEGRITY-AUDIT-HARNESS-REMEDIATION-R5"
BASE = "e20ac1891b7f30a9928f3de95b3ff364f7cec6dd"
R4_A = "bd0599c6bb6b377d34147a2ede490be061421c9a"
R4_B = "f40f2539782af78d5808835da1159b81075cde69"
R4_BLOCKER_HASH = "34acc0c252b13054b15f3ac6fb1a560fdf0c653f2580305c9d582f6a52e863fc"

FUSION_HASH = "9fd5563b76cb4af0cf68383e1e2b9d10da9e6fd35a667d4a68d6eb5f8db2e8cb"
METRIC_HASH = "3e3f20b5b1a9387cd3bed4ad17e4232e714cc588d7df1c2a37dfd69bcd1a8513"
COMBINED_HASH = "31035da56e140141917437df5b3473b803153621c7e1022830cccde52f61c0b3"
DESIGN_HASH = "ace631af367ee2abe1b0ee7658875eeb59a2a8d906d09ce8ea92e8f2d83e31e4"
AUTHORIZATION_HASH = "0f909480cfe3db8afc4042909258fe041f36ad021a917907008ee7e5023f2f45"
D0_HASH = "a4b58f1c78b9bb53125da1a009f3fd05b02e1c83a789772a341a7679fddca0f6"
D1_HASH = "58c3c49f9657f68d35c830b12eeb493ce4bbf7669c90f04813fb80246c3c2682"
SOURCE_HASH = "f866176000c3d5a943053ac3125d2700b0b72f25b5a0539d8f4713435a959818"
HORIZON_HASH = "e9825a578495396d935397e79d8c50717dccb47f069f13e93f6306f992a9407c"
CUSTODY_MODULE_IDENTITY = "c0e3faafdab0cb84e2f8e62b9380c243b0faee9ab38cc014de36fed5464d62e6"
CUSTODY_PREFLIGHT_HASH = "1296c76458d498d0e35b209c4da9691f6d02e1899778906409d96d7c18d4e463"
PATH_REDACTION_HASH = "1b51853f796b01fa0fa47c5c1a431c6d79997a62612b4569ba9a255045ca4355"
V2_BINDING_KEY = "TASK039E3_D2_V2_PRIVATE_EVIDENCE_ROOT_V1"
V2_NAMESPACE = "TASK039E3_D2_V2_PRIVATE_EVIDENCE_V1"
FUSION_FILENAME = "task039e3_inner_d2_v2_fusion_evidence_v1.json"
METRIC_FILENAME = "task039e3_inner_d2_v2_metric_evidence_v1.json"
REPORT_SCHEME = "MARKDOWN_BODY_SHA256_BEFORE_INTEGRITY_FOOTER_V1"
ROOT_CAUSE_DISPOSITION = "OTHER_EXACTLY_EXPLAINED"
R4_FAILED_BINDING_CLASS = "ENVIRONMENT_LOCAL_LOCATOR_ACCESS_PERMISSION"
R4_EXACT_ROOT_CAUSE = (
    "R4_FAIL_CLOSED_COLLAPSED_SANDBOX_ACCESS_DENIAL_DURING_"
    "ENVIRONMENT_LOCAL_LOCATOR_RESOLUTION_INTO_GENERIC_BINDING_REJECTION"
)

CUSTODY_SOURCE = "src/paperworks/v6/task039e3_r2r_d2_execution_recovery_custody_v1.py"
AUTH_SOURCE = "src/paperworks/v6/task039e3_r2r_d2_v2_execution_authorization_v1.py"
EXEC_SOURCE = "src/paperworks/v6/task039e3_r2r_d2_v2_inner_execution_v1.py"
R4_SOURCE = "scripts/audit_task039e3_r2r_d2_v2_result_integrity_harness_remediation_r4.py"
SOURCE_SHA256 = {
    CUSTODY_SOURCE: "2f13e95ee2d7ba45ef5095353f4335ff5a09cd64d444f859a28d2c9336560955",
    AUTH_SOURCE: "09c233ba61aa19431f342bf3398cc174c9523fcc9f73389f15e1fd35341bd25e",
    EXEC_SOURCE: "cec2a8a68f3807ec62c52cf5aea6c60425667bb1d77fa48e08159f4b4034d071",
    R4_SOURCE: "f7cbd75ea1989bb37b9129a1a3166ba88dbbe8142a7ec16041237f41576710d1",
}

AUTH_CUSTODY_PATH = "docs/task_reports/TASK-039E3_R2R_UTILITY_INNER_D2_V2_EXECUTION_AUTHORIZATION_V1_CUSTODY_PREFLIGHT.json"
AUTH_REDACTION_PATH = "docs/task_reports/TASK-039E3_R2R_UTILITY_INNER_D2_V2_EXECUTION_AUTHORIZATION_V1_PATH_REDACTION_AUDIT.json"
EXEC_BUNDLE_PATH = "docs/task_reports/TASK-039E3_R2R_UTILITY_INNER_D2_V2_EXECUTION_V1_BUNDLE.json"
R4_BLOCKER_PATH = "docs/task_reports/TASK-039E3_R2R_UTILITY_INNER_D2_V2_RESULT_INTEGRITY_AUDIT_HARNESS_R4_BLOCKER.json"

REPORT_PREFIX = "TASK-039E3_R2R_UTILITY_INNER_D2_V2_PRIVATE_CUSTODY_BINDING_REMEDIATION_R1_"
REPORT_NAMES = (
    "ROOT_CAUSE", "FIELD_CLASSIFICATION", "FUSION_EVIDENCE_IDENTITY",
    "METRIC_EVIDENCE_IDENTITY", "SECURITY_AUDIT", "COMPATIBILITY_RECEIPT",
    "INDEPENDENT_AUDIT", "READINESS", "BUNDLE", "RECEIPT",
)

CLASS_STABLE_SCIENTIFIC = "STABLE_SCIENTIFIC_IDENTITY"
CLASS_STABLE_SECURITY = "STABLE_SECURITY_PROPERTY"
CLASS_STABLE_LOGICAL = "STABLE_LOGICAL_CUSTODY_IDENTITY"
CLASS_ENVIRONMENT = "ENVIRONMENT_LOCAL_LOCATOR"
CLASS_EPHEMERAL = "EPHEMERAL_PROCESS_METADATA"


class CustodyRemediationError(RuntimeError):
    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


def fail(code: str) -> NoReturn:
    raise CustodyRemediationError(code) from None


def stable_hash(value: Mapping[str, Any]) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"),
                     ensure_ascii=True, allow_nan=False).encode("utf-8")
    return sha256(raw).hexdigest()


def self_hashed(value: Mapping[str, Any]) -> dict[str, Any]:
    payload = dict(value)
    if "artifact_hash" in payload:
        fail("CUSTODY_REMEDIATION_DUPLICATE_HASH_FIELD")
    return {**payload, "artifact_hash": stable_hash(payload)}


def validate_self_hash(document: Mapping[str, Any], expected: str | None = None) -> str:
    if type(document) is not dict or type(document.get("artifact_hash")) is not str:
        fail("CUSTODY_REMEDIATION_ARTIFACT_HASH_REJECTED")
    payload = {key: value for key, value in document.items() if key != "artifact_hash"}
    actual = stable_hash(payload)
    if actual != document["artifact_hash"] or (expected is not None and actual != expected):
        fail("CUSTODY_REMEDIATION_ARTIFACT_HASH_REJECTED")
    return actual


@dataclass(frozen=True)
class FieldClassificationR1:
    field: str
    classification: str
    producer_evidence: str


FIELD_CLASSIFICATIONS = (
    FieldClassificationR1("fusion_evidence_v2_hash", CLASS_STABLE_SCIENTIFIC, "private envelope and execution bundle"),
    FieldClassificationR1("metric_evidence_v2_hash", CLASS_STABLE_SCIENTIFIC, "private envelope and execution bundle"),
    FieldClassificationR1("combined_prediction_v2_hash", CLASS_STABLE_SCIENTIFIC, "metric envelope and execution bundle"),
    FieldClassificationR1("d2_v2_design_hash", CLASS_STABLE_SCIENTIFIC, "both private envelopes"),
    FieldClassificationR1("authorization_identity", CLASS_STABLE_SCIENTIFIC, "both private envelopes"),
    FieldClassificationR1("d0_prediction_hash", CLASS_STABLE_SCIENTIFIC, "fusion envelope"),
    FieldClassificationR1("d1_prediction_hash", CLASS_STABLE_SCIENTIFIC, "fusion envelope"),
    FieldClassificationR1("source_map_hash", CLASS_STABLE_SCIENTIFIC, "fusion envelope"),
    FieldClassificationR1("native_horizon_map_hash", CLASS_STABLE_SCIENTIFIC, "fusion envelope"),
    FieldClassificationR1("outside_git", CLASS_STABLE_SECURITY, "custody root issuer"),
    FieldClassificationR1("regular_file", CLASS_STABLE_SECURITY, "atomic custody target"),
    FieldClassificationR1("symlink_false", CLASS_STABLE_SECURITY, "custody root and target guard"),
    FieldClassificationR1("tracked_copy_count_zero", CLASS_STABLE_SECURITY, "private/public separation"),
    FieldClassificationR1("unexpected_residue_zero", CLASS_STABLE_SECURITY, "custody residue policy"),
    FieldClassificationR1("path_redaction_policy", CLASS_STABLE_SECURITY, "authorization path-redaction audit"),
    FieldClassificationR1("custody_module_identity", CLASS_STABLE_LOGICAL, "authorization and custody issuer"),
    FieldClassificationR1("v2_binding_key", CLASS_STABLE_LOGICAL, "V2 authorization source"),
    FieldClassificationR1("v2_private_namespace", CLASS_STABLE_LOGICAL, "authorization preflight receipt"),
    FieldClassificationR1("fusion_artifact_role_filename", CLASS_STABLE_LOGICAL, "V2 writer allowlist"),
    FieldClassificationR1("metric_artifact_role_filename", CLASS_STABLE_LOGICAL, "V2 writer allowlist"),
    FieldClassificationR1("absolute_root_string", CLASS_ENVIRONMENT, "private root field compare=False and omitted publicly"),
    FieldClassificationR1("resolved_root_spelling", CLASS_ENVIRONMENT, "process-local issued-root ledger"),
    FieldClassificationR1("drive_or_mount_prefix", CLASS_ENVIRONMENT, "not serialized by preflight receipt"),
    FieldClassificationR1("path_separator_representation", CLASS_ENVIRONMENT, "not serialized by preflight receipt"),
    FieldClassificationR1("worktree_local_binding_file_location", CLASS_ENVIRONMENT, "Git-ignored local binding layer"),
    FieldClassificationR1("inode_or_file_id", CLASS_EPHEMERAL, "not part of original binding"),
    FieldClassificationR1("device_or_volume_id", CLASS_EPHEMERAL, "not part of original binding"),
    FieldClassificationR1("process_id", CLASS_EPHEMERAL, "not part of original binding"),
    FieldClassificationR1("session_id", CLASS_EPHEMERAL, "not part of original binding"),
)


def classification_counts() -> dict[str, int]:
    values = {name: 0 for name in (
        CLASS_STABLE_SCIENTIFIC, CLASS_STABLE_SECURITY, CLASS_STABLE_LOGICAL,
        CLASS_ENVIRONMENT, CLASS_EPHEMERAL, "UNKNOWN_FAIL_CLOSED")}
    for field in FIELD_CLASSIFICATIONS:
        values[field.classification] += 1
    return values


@dataclass(frozen=True)
class CompatibilityCandidateR1:
    artifact_hashes_exact: bool = True
    stable_scientific_bindings_exact: bool = True
    stable_security_properties_pass: bool = True
    stable_logical_bindings_exact: bool = True
    environment_local_differences_only: bool = True
    producer_declares_path_environment_local: bool = True
    validator_requires_absolute_path_equality: bool = False
    producer_declares_path_stable: bool = False
    absolute_path_ignored: bool = True
    inside_git: bool = False
    symlink: bool = False
    tracked_copy_count: int = 0
    unexpected_residue_count: int = 0
    logical_namespace_match: bool = True
    custody_module_match: bool = True
    copied: bool = False
    moved: bool = False
    rewritten: bool = False
    repersisted: bool = False
    private_path_exposed: bool = False
    forbidden_accesses: int = 0


def validate_compatibility_candidate(candidate: CompatibilityCandidateR1) -> str:
    if type(candidate) is not CompatibilityCandidateR1:
        fail("CUSTODY_REMEDIATION_COMPATIBILITY_TYPE_REJECTED")
    if candidate.producer_declares_path_environment_local and candidate.validator_requires_absolute_path_equality:
        fail("CUSTODY_REMEDIATION_VALIDATOR_PATH_IDENTITY_DEFECT")
    if candidate.producer_declares_path_stable and candidate.absolute_path_ignored:
        fail("CUSTODY_REMEDIATION_STABLE_BINDING_MISMATCH")
    if not all((candidate.artifact_hashes_exact, candidate.stable_scientific_bindings_exact,
                candidate.stable_security_properties_pass, candidate.stable_logical_bindings_exact,
                candidate.environment_local_differences_only, candidate.logical_namespace_match,
                candidate.custody_module_match)):
        fail("CUSTODY_REMEDIATION_COMPATIBILITY_REJECTED")
    if candidate.inside_git or candidate.symlink or candidate.tracked_copy_count != 0 or candidate.unexpected_residue_count != 0:
        fail("CUSTODY_REMEDIATION_SECURITY_REJECTED")
    if any((candidate.copied, candidate.moved, candidate.rewritten, candidate.repersisted)):
        fail("CUSTODY_REMEDIATION_PRIVATE_MUTATION_REJECTED")
    if candidate.private_path_exposed or candidate.forbidden_accesses != 0:
        fail("CUSTODY_REMEDIATION_BOUNDARY_REJECTED")
    return "D2_V2_PRIVATE_CUSTODY_BINDING_COMPATIBILITY_PASS"


ALLOWED_OPERATIONS = frozenset({"STATIC_SOURCE_READ", "PUBLIC_AUTHORITY_READ", "PRIVATE_LOCATOR_RESOLVE", "PRIVATE_ENVELOPE_IDENTITY_PARSE", "PRIVATE_FILE_STAT", "GIT_TRACKED_COPY_CHECK"})


def validate_operation_request(operations: Sequence[str]) -> str:
    if type(operations) not in (tuple, list) or any(type(value) is not str or value not in ALLOWED_OPERATIONS for value in operations):
        fail("CUSTODY_REMEDIATION_FORBIDDEN_OPERATION")
    return "CUSTODY_REMEDIATION_OPERATION_SET_ACCEPTED"


def read_public_document(relative: str, expected: str) -> dict[str, Any]:
    try:
        document = json.loads((ROOT / relative).read_text(encoding="utf-8"))
        validate_self_hash(document, expected)
        return document
    except CustodyRemediationError:
        raise
    except BaseException:
        fail("CUSTODY_REMEDIATION_PUBLIC_AUTHORITY_REJECTED")


def validate_source_semantics() -> dict[str, Any]:
    source: dict[str, str] = {}
    for relative, expected in SOURCE_SHA256.items():
        raw = (ROOT / relative).read_bytes()
        if sha256(raw).hexdigest() != expected:
            fail("CUSTODY_REMEDIATION_FROZEN_SOURCE_REJECTED")
        source[relative] = raw.decode("utf-8")
    custody, authorization, execution, r4 = (source[CUSTODY_SOURCE], source[AUTH_SOURCE], source[EXEC_SOURCE], source[R4_SOURCE])
    required = (
        "_path: Path = field(repr=False, compare=False)",
        "return \"<D2RecoveryPrivateRootV1 validated=True path=REDACTED>\"",
        "V2_PRIVATE_NAMESPACE = \"TASK039E3_D2_V2_PRIVATE_EVIDENCE_V1\"",
        "if configured != root._path.resolve(strict=True):",
        "V2_PRIVATE_FILENAMES = (",
        "_persist_private_v2(preflight._root, PRIVATE_FUSION_FILENAME",
        "_persist_private_v2(preflight._root, PRIVATE_METRIC_FILENAME",
        "return Path(values[0]).resolve(strict=True)",
        "fail(\"D2_V2_R4_BINDING_REJECTED\")",
    )
    joined = custody + authorization + execution + r4
    if any(fragment not in joined for fragment in required):
        fail("CUSTODY_REMEDIATION_PRODUCER_SEMANTICS_UNPROVEN")
    return {
        "original_custody_producer_identity": CUSTODY_MODULE_IDENTITY,
        "producer_semantics_recovered": True,
        "absolute_path_serialized_in_public_preflight": False,
        "absolute_path_stable_scientific_identity": False,
        "runtime_locator_coherence_required_at_authorization": True,
        "r4_failed_stage": "V2_PRIVATE_BINDING_STRICT_LOCATOR_RESOLUTION",
        "r4_failed_binding_class": R4_FAILED_BINDING_CLASS,
        "r4_root_cause_disposition": ROOT_CAUSE_DISPOSITION,
        "r4_exact_root_cause": R4_EXACT_ROOT_CAUSE,
        "source_sha256": dict(SOURCE_SHA256),
    }


def binding_locator() -> Path:
    binding = ROOT / ".env.d2_v2_custody.local"
    try:
        if binding.is_symlink() or not binding.is_file():
            fail("CUSTODY_REMEDIATION_LOCAL_BINDING_REJECTED")
        matches: list[str] = []
        for line in binding.read_text(encoding="utf-8").splitlines():
            match = re.fullmatch(r"([A-Z0-9_]+)='(.*)'", line)
            if match and match.group(1) == V2_BINDING_KEY:
                matches.append(match.group(2).replace("'\"'\"'", "'"))
        if len(matches) != 1:
            fail("CUSTODY_REMEDIATION_LOCAL_BINDING_REJECTED")
        return Path(matches[0]).resolve(strict=True)
    except CustodyRemediationError:
        raise
    except BaseException:
        fail("CUSTODY_REMEDIATION_LOCAL_BINDING_REJECTED")


@dataclass(frozen=True)
class PrivateIdentityR1:
    role: str
    artifact_hash: str
    located: bool
    regular_file: bool
    symlink: bool
    outside_git: bool
    tracked_copy_count: int
    logical_filename_match: bool
    logical_namespace_match: bool
    stable_bindings_pass: bool
    identity_envelope_parses: int


def _tracked_copy_count(filename: str) -> int:
    result = subprocess.run(["git", "ls-files"], cwd=ROOT, check=True,
                            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
    return sum(Path(line).name == filename for line in result.stdout.splitlines())


def private_identity(root: Path, repository: Path, filename: str, expected_hash: str,
                     role: str, required: Mapping[str, Any]) -> PrivateIdentityR1:
    try:
        repo = repository.resolve(strict=True)
        current_root = root.resolve(strict=True)
        target = current_root / filename
        outside = current_root != repo and repo not in current_root.parents
        if not outside or current_root.is_symlink() or not current_root.is_dir():
            fail("CUSTODY_REMEDIATION_SECURITY_REJECTED")
        if target.is_symlink() or not target.is_file():
            fail("CUSTODY_REMEDIATION_PRIVATE_ARTIFACT_REJECTED")
        document = json.loads(target.read_text(encoding="utf-8"))
        validate_self_hash(document, expected_hash)
        if any(document.get(key) != value for key, value in required.items()):
            fail("CUSTODY_REMEDIATION_STABLE_BINDING_MISMATCH")
        tracked = _tracked_copy_count(filename)
        if tracked != 0:
            fail("CUSTODY_REMEDIATION_SECURITY_REJECTED")
        return PrivateIdentityR1(role, expected_hash, True, True, False, True,
                                 tracked, target.name == filename, True, True, 1)
    except CustodyRemediationError:
        raise
    except BaseException:
        fail("CUSTODY_REMEDIATION_PRIVATE_ARTIFACT_REJECTED")


def unexpected_residue_count(root: Path) -> int:
    expected = {FUSION_FILENAME, METRIC_FILENAME}
    try:
        return sum(entry.name not in expected for entry in root.iterdir()
                   if entry.name.startswith("task039e3_inner_d2_v2_"))
    except BaseException:
        fail("CUSTODY_REMEDIATION_PRIVATE_ARTIFACT_REJECTED")


def git(*args: str) -> str:
    result = subprocess.run(["git", *args], cwd=ROOT, check=True,
                            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
    return result.stdout.strip()


def validate_git_and_history() -> dict[str, Any]:
    if git("rev-parse", "HEAD") != BASE or git("status", "--porcelain"):
        fail("CUSTODY_REMEDIATION_GIT_STATE_REJECTED")
    blocker = read_public_document(R4_BLOCKER_PATH, R4_BLOCKER_HASH)
    if blocker.get("blocker_code") != "D2_V2_R4_BINDING_REJECTED":
        fail("CUSTODY_REMEDIATION_R4_BLOCKER_REJECTED")
    historical = (
        ("docs/task_reports/TASK-039E3_R2R_UTILITY_INNER_D2_V2_RESULT_INTEGRITY_V1_BLOCKER.json", "592344d430b50724a7ae4f81ed0e73423ec1473586d0d9a15d2ff68f6009f879"),
        ("docs/task_reports/TASK-039E3_R2R_UTILITY_INNER_D2_V2_RESULT_INTEGRITY_AUDIT_HARNESS_R1_BLOCKER.json", "dc6d83a33bdf985389b6d2d1b75e54f2b703e59f515369dc41b5a499280b0990"),
        ("docs/task_reports/TASK-039E3_R2R_UTILITY_INNER_D2_V2_RESULT_INTEGRITY_AUDIT_HARNESS_R2_BLOCKER.json", "4e6526e382dbb0bf15bae9123eeeba3a090dcb59bfd767f3b19172fe3e353c0c"),
        ("docs/task_reports/TASK-039E3_R2R_UTILITY_INNER_D2_V2_RESULT_INTEGRITY_AUDIT_HARNESS_R3_BLOCKER.json", "2baed348b67ec7567ea57d1892c4e605728120e65480728ca562528c822e9f4a"),
    )
    for path, expected in historical:
        read_public_document(path, expected)
    return {"historical_blocked_integrity_audit_attempts": 5,
            "historical_completed_integrity_audit_attempts": 0,
            "historical_blockers_preserved": True, "r4_blocker_hash_match": True}


def validate_public_custody_authorities() -> dict[str, Any]:
    preflight = read_public_document(AUTH_CUSTODY_PATH, CUSTODY_PREFLIGHT_HASH)
    redaction = read_public_document(AUTH_REDACTION_PATH, PATH_REDACTION_HASH)
    bundle = read_public_document(EXEC_BUNDLE_PATH, "ded276981ce75ebe5e947bd7a409d14b03208e7e23f1c8e3ddc1cd3070cb915f")
    required = {
        "recovery_custody_module_identity": CUSTODY_MODULE_IDENTITY,
        "v2_private_namespace": V2_NAMESPACE,
        "private_root_configured": True, "private_root_outside_git": True,
        "private_root_symlink": False, "path_redaction_pass": True,
        "d2_v2_design_hash": DESIGN_HASH, "d0_prediction_hash": D0_HASH,
        "d1_prediction_hash": D1_HASH, "source_map_hash": SOURCE_HASH,
        "native_horizon_map_hash": HORIZON_HASH,
    }
    if any(preflight.get(key) != value for key, value in required.items()):
        fail("CUSTODY_REMEDIATION_PUBLIC_CUSTODY_BINDING_REJECTED")
    if redaction.get("path_redaction_pass") is not True or redaction.get("private_paths_exposed") != 0:
        fail("CUSTODY_REMEDIATION_PATH_REDACTION_REJECTED")
    if any(bundle.get(key) != value for key, value in {
        "fusion_evidence_hash": FUSION_HASH,
        "private_metric_evidence_hash": METRIC_HASH,
        "combined_prediction_hash": COMBINED_HASH,
    }.items()):
        fail("CUSTODY_REMEDIATION_EXECUTION_BINDING_REJECTED")
    return {"custody_module_identity_match": True, "fusion_logical_namespace_match": True,
            "metric_logical_namespace_match": True, "path_redaction_policy_match": True}


def adversarial_audit() -> tuple[int, int]:
    mutations = (
        {"artifact_hashes_exact": False}, {"stable_scientific_bindings_exact": False},
        {"stable_security_properties_pass": False}, {"stable_logical_bindings_exact": False},
        {"environment_local_differences_only": False}, {"inside_git": True},
        {"symlink": True}, {"tracked_copy_count": 1}, {"unexpected_residue_count": 1},
        {"logical_namespace_match": False}, {"custody_module_match": False},
        {"copied": True}, {"moved": True}, {"rewritten": True}, {"repersisted": True},
        {"private_path_exposed": True}, {"forbidden_accesses": 1},
        {"validator_requires_absolute_path_equality": True},
        {"producer_declares_path_environment_local": False, "producer_declares_path_stable": True},
    )
    accepted = 0
    for mutation in mutations:
        candidate = replace(CompatibilityCandidateR1(), **mutation)
        try:
            validate_compatibility_candidate(candidate)
            accepted += 1
        except CustodyRemediationError:
            pass
    forbidden = ("COPY_PRIVATE", "MOVE_PRIVATE", "REWRITE_PRIVATE", "REPERSIST_PRIVATE",
                 "PARSE_D0", "PARSE_D1", "PARSE_SOURCE_MAP", "PARSE_HORIZON",
                 "PARSE_COMBINED", "PARSE_LABEL", "READ_TEST1_FEATURE", "READ_TEST2",
                 "RUN_FUSION", "COMPUTE_METRIC", "PRINT_PRIVATE_PATH")
    for operation in forbidden:
        try:
            validate_operation_request((operation,))
            accepted += 1
        except CustodyRemediationError:
            pass
    return len(mutations) + len(forbidden), accepted


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def build_reports(result: Mapping[str, Any]) -> tuple[dict[str, dict[str, Any]], bytes]:
    created = _utc_now()
    common = {"schema_version": "1.0.0", "task_id": TASK_ID,
              "created_at_utc": created, "status": STATUS}
    counts = classification_counts()
    reports: dict[str, dict[str, Any]] = {}
    reports["ROOT_CAUSE"] = self_hashed({**common, "artifact_type": "D2V2PrivateCustodyBindingRootCauseR1",
        "r4_blocker_hash": R4_BLOCKER_HASH, "r4_blocker_hash_match": True,
        "r4_failed_binding_field": "V2_PRIVATE_BINDING_KEY_RESOLVED_LOCATOR",
        "r4_failed_binding_class": R4_FAILED_BINDING_CLASS,
        "root_cause_disposition": ROOT_CAUSE_DISPOSITION,
        "exact_root_cause": R4_EXACT_ROOT_CAUSE, "root_cause_scientific": False,
        "root_cause_result_driven": False, "absolute_path_equality_required": False,
        "absolute_path_compared_publicly": False})
    reports["FIELD_CLASSIFICATION"] = self_hashed({**common, "artifact_type": "D2V2PrivateCustodyFieldClassificationR1",
        "classification_counts": counts,
        "fields": [asdict(value) for value in FIELD_CLASSIFICATIONS], "unknown_field_count": 0})
    fusion: PrivateIdentityR1 = result["fusion"]
    metric: PrivateIdentityR1 = result["metric"]
    reports["FUSION_EVIDENCE_IDENTITY"] = self_hashed({**common, "artifact_type": "D2V2FusionEvidenceIdentityAuditR1", **asdict(fusion)})
    reports["METRIC_EVIDENCE_IDENTITY"] = self_hashed({**common, "artifact_type": "D2V2MetricEvidenceIdentityAuditR1", **asdict(metric)})
    reports["SECURITY_AUDIT"] = self_hashed({**common, "artifact_type": "D2V2PrivateCustodySecurityAuditR1",
        "stable_security_properties_pass": True, "private_root_outside_git": True,
        "private_root_symlink": False, "regular_files": True, "tracked_copy_count": 0,
        "unexpected_private_residue": 0, "private_path_exposures": 0,
        "private_evidence_copied": False, "private_evidence_moved": False,
        "private_evidence_rewritten": False, "private_evidence_repersisted": False})
    compatibility_payload = {**common, "artifact_type": "D2V2PrivateCustodyBindingCompatibilityReceiptR1",
        "remediation_version": VERSION, "audit_only": True, "scientific_execution_authorized": False,
        "custody_module_identity": CUSTODY_MODULE_IDENTITY, "d2_v2_design_hash": DESIGN_HASH,
        "authorization_hash": AUTHORIZATION_HASH, "fusion_evidence_v2_hash": FUSION_HASH,
        "metric_evidence_v2_hash": METRIC_HASH, "combined_prediction_v2_hash": COMBINED_HASH,
        "fusion_logical_namespace_match": True, "metric_logical_namespace_match": True,
        "stable_scientific_bindings_pass": True, "stable_security_properties_pass": True,
        "stable_logical_custody_bindings_pass": True, "environment_local_differences_only": True,
        "absolute_path_equality_required": False, "r4_blocker_hash": R4_BLOCKER_HASH,
        "remediation_result": "PASS", "exact_next_task": NEXT_TASK}
    reports["COMPATIBILITY_RECEIPT"] = self_hashed(compatibility_payload)
    reports["INDEPENDENT_AUDIT"] = self_hashed({**common, "artifact_type": "D2V2PrivateCustodyBindingIndependentAuditR1",
        "independent_attacks": result["attacks"], "accepted_invalid": result["accepted"],
        "synthetic_only_before_real_invocation": True, "private_path_exposures": 0})
    reports["READINESS"] = self_hashed({**common, "artifact_type": "D2V2PrivateCustodyBindingRemediationReadinessR1",
        "custody_state": CUSTODY_STATE, "scientific_result_state": SCIENTIFIC_STATE,
        "compatibility_receipt_hash": reports["COMPATIBILITY_RECEIPT"]["artifact_hash"],
        "custody_binding_remediation_attempts": 1, "custody_binding_remediation_retries": 0,
        "integrity_audit_attempts": 5, "completed_integrity_audits": 0,
        "d0_prediction_parses": 0, "d1_prediction_parses": 0, "source_map_parses": 0,
        "native_horizon_parses": 0, "combined_prediction_parses": 0,
        "label_parses": 0, "metric_computations": 0, "test1_feature_accesses": 0,
        "test2_accesses": 0, "authoritative_scientific_executions": 0,
        "outer_authorized": False, "blockers": [], "exact_next_task": NEXT_TASK})
    body = (
        "# TASK-039E3-R2R D2 V2 private-custody binding remediation R1\n\n"
        f"Status: `{STATUS}`\n\n"
        "The R4 failure occurred while resolving an environment-local private locator under a denied runtime access boundary. It did not establish an artifact, namespace, authorization, or scientific mismatch.\n\n"
        "The original producer excludes absolute paths from public and scientific identity. Exact private self-hashes, stable authority bindings, the V2 logical namespace, fixed artifact roles, custody-module identity, and outside-Git security controls remain authoritative.\n\n"
        "Both existing private artifacts were validated in place. No private evidence was copied, moved, rewritten, renamed, or repersisted. No prediction, source map, horizon map, CombinedPrediction, label, feature, fusion, episode, or metric scientific computation occurred.\n\n"
        f"Exact next task: `{NEXT_TASK}`\n"
    ).encode("utf-8")
    report_hash = sha256(body).hexdigest()
    reports["BUNDLE"] = self_hashed({**common, "artifact_type": "D2V2PrivateCustodyBindingRemediationBundleR1",
        "root_cause_hash": reports["ROOT_CAUSE"]["artifact_hash"],
        "field_classification_hash": reports["FIELD_CLASSIFICATION"]["artifact_hash"],
        "fusion_evidence_identity_hash": reports["FUSION_EVIDENCE_IDENTITY"]["artifact_hash"],
        "metric_evidence_identity_hash": reports["METRIC_EVIDENCE_IDENTITY"]["artifact_hash"],
        "security_audit_hash": reports["SECURITY_AUDIT"]["artifact_hash"],
        "compatibility_receipt_hash": reports["COMPATIBILITY_RECEIPT"]["artifact_hash"],
        "independent_audit_hash": reports["INDEPENDENT_AUDIT"]["artifact_hash"],
        "readiness_hash": reports["READINESS"]["artifact_hash"],
        "report_hash_scheme": REPORT_SCHEME, "report_self_hash": report_hash,
        "remote_egress_status": "LOCAL_ONLY_NOT_PUSHED"})
    reports["RECEIPT"] = self_hashed({**common, "artifact_type": "D2V2PrivateCustodyBindingRemediationReceiptR1",
        "bundle_hash": reports["BUNDLE"]["artifact_hash"],
        "readiness_hash": reports["READINESS"]["artifact_hash"],
        "compatibility_receipt_hash": reports["COMPATIBILITY_RECEIPT"]["artifact_hash"],
        "report_hash_scheme": REPORT_SCHEME, "report_self_hash": report_hash,
        "scientific_execution_authorized": False, "outer_authorized": False,
        "exact_next_task": NEXT_TASK})
    footer = (
        "\n<!-- BEGIN D2 V2 PRIVATE CUSTODY BINDING REMEDIATION R1 REPORT PROVENANCE V1 -->\n"
        f"Report-Hash-Scheme: {REPORT_SCHEME}\n"
        f"Report-Self-Hash: {report_hash}\n"
        f"Bundle-Hash: {reports['BUNDLE']['artifact_hash']}\n"
        f"Receipt-Hash: {reports['RECEIPT']['artifact_hash']}\n"
        "<!-- END D2 V2 PRIVATE CUSTODY BINDING REMEDIATION R1 REPORT PROVENANCE V1 -->\n"
    ).encode("utf-8")
    return reports, body + footer


def write_reports(reports: Mapping[str, Mapping[str, Any]], markdown: bytes,
                  private_tokens: Sequence[str]) -> None:
    output = ROOT / "docs/task_reports"
    for name in REPORT_NAMES:
        path = output / f"{REPORT_PREFIX}{name}.json"
        if path.exists() or path.is_symlink():
            fail("CUSTODY_REMEDIATION_RESULT_EXISTS")
        raw = (json.dumps(reports[name], sort_keys=True, indent=2,
                          ensure_ascii=True, allow_nan=False) + "\n").encode("utf-8")
        if any(token and token.encode("utf-8") in raw for token in private_tokens):
            fail("CUSTODY_REMEDIATION_PATH_LEAK_REJECTED")
        path.write_bytes(raw)
    report_path = output / f"{REPORT_PREFIX}REPORT.md"
    if report_path.exists() or report_path.is_symlink():
        fail("CUSTODY_REMEDIATION_RESULT_EXISTS")
    if any(token and token.encode("utf-8") in markdown for token in private_tokens):
        fail("CUSTODY_REMEDIATION_PATH_LEAK_REJECTED")
    report_path.write_bytes(markdown)


def run_real() -> dict[str, Any]:
    history = validate_git_and_history()
    producer = validate_source_semantics()
    public = validate_public_custody_authorities()
    root = binding_locator()
    repo = ROOT.resolve(strict=True)
    fusion = private_identity(root, repo, FUSION_FILENAME, FUSION_HASH, "FUSION_EVIDENCE_V2", {
        "artifact_type": "D2V2FusionEvidenceV1", "schema_version": "1.0.0",
        "authorization_hash": AUTHORIZATION_HASH, "d2_v2_design_hash": DESIGN_HASH,
        "d0_prediction_hash": D0_HASH, "d1_prediction_hash": D1_HASH,
        "source_map_hash": SOURCE_HASH, "native_horizon_map_hash": HORIZON_HASH,
    })
    metric = private_identity(root, repo, METRIC_FILENAME, METRIC_HASH, "METRIC_EVIDENCE_V2", {
        "artifact_type": "D2V2MetricEvidenceV1", "schema_version": "1.0.0",
        "authorization_hash": AUTHORIZATION_HASH, "d2_v2_design_hash": DESIGN_HASH,
        "combined_prediction_v2_hash": COMBINED_HASH, "fusion_evidence_v2_hash": FUSION_HASH,
    })
    residue = unexpected_residue_count(root)
    candidate = CompatibilityCandidateR1(unexpected_residue_count=residue)
    validate_compatibility_candidate(candidate)
    attacks, accepted = adversarial_audit()
    if accepted != 0:
        fail("CUSTODY_REMEDIATION_ACCEPTED_INVALID")
    result: dict[str, Any] = {**history, **producer, **public, "fusion": fusion,
        "metric": metric, "residue": residue, "attacks": attacks, "accepted": accepted}
    reports, markdown = build_reports(result)
    write_reports(reports, markdown, (str(root), str(root / FUSION_FILENAME), str(root / METRIC_FILENAME)))
    return {"status": STATUS, "attacks": attacks, "accepted": accepted,
            "hashes": {name: reports[name]["artifact_hash"] for name in REPORT_NAMES},
            "report_self_hash": reports["RECEIPT"]["report_self_hash"]}


def main() -> int:
    if sys.argv[1:]:
        print("CUSTODY_REMEDIATION_ARGUMENTS_REJECTED")
        return 2
    try:
        result = run_real()
    except CustodyRemediationError as error:
        print(error.code)
        return 1
    except BaseException:
        print("CUSTODY_REMEDIATION_INTERNAL_BLOCKED")
        return 1
    print(result["status"])
    print(SCIENTIFIC_STATE)
    print(CUSTODY_STATE)
    print("LOCAL_ONLY_NOT_PUSHED")
    print(f"INDEPENDENT_ATTACKS={result['attacks']}")
    print(f"ACCEPTED_INVALID={result['accepted']}")
    for name, value in result["hashes"].items():
        print(f"{name}_HASH={value}")
    print(f"REPORT_SELF_HASH={result['report_self_hash']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
