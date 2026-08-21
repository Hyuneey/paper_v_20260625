"""Public-only provenance validator for the D0 audit-report hash remediation.

The module reads tracked public documents and local Git objects only.  It has
no scientific-data, label, private-model, detector, metric, D1, D2, test2, or
network execution path.
"""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import re
import subprocess
import sys
from typing import Any, Callable, Mapping, NoReturn, Sequence


REMEDIATION_TASK_ID = (
    "TASK-039E3-R2R-UTILITY-INNER-D0-RESULT-INTEGRITY-"
    "AUDIT-REPORT-HASH-REMEDIATION-R1"
)
HISTORICAL_TASK_ID = "TASK-039E3-R2R-UTILITY-INNER-D0-RESULT-INTEGRITY-AUDIT-V1"
PASS_STATUS = (
    "passed_task039e3_r2r_utility_inner_d0_result_integrity_"
    "audit_report_hash_remediation_r1"
)
SCHEMA_VERSION = "1.0.0"
REMOTE_STATE = "LOCAL_ONLY_NOT_PUSHED"
EXPECTED_BRANCH = (
    "task-039e3-r2r-utility-inner-d0-result-integrity-"
    "audit-report-hash-remediation-r1"
)

EXECUTION_COMMIT_A = "c117087ec43d6e58167e77087e13b6a8a9226d42"
EXECUTION_INDEPENDENT_COMMIT_B = "f45c71c9990984f6fa0c552060c8ab51e1e5c9a4"
RESULT_FREEZE_COMMIT_C = "78d758f50657413eed28dc838212be9a1edeffc7"
EXECUTION_CONTINUITY_COMMIT_D = "c96adab1ae6f474472f73cc2de0a7c5dab63e24d"
INTEGRITY_AUDIT_COMMIT_A = "346a9f1ec6d5b1d97a66da45fcff66f44353742e"
INTEGRITY_REPORT_COMMIT_B = "a1ff1929a86e95675431c2c32ace01efa2696a80"
HISTORICAL_BLOCKER_COMMIT = "69f902b380a2aa1b674ca70983bb131ad04f54ba"
CORRECTED_REMEDIATION_BASE = "eea8a0d76420ba058df2789b914a6347255c0db0"

HISTORICAL_BLOCKER_CODE = "D0_RESULT_INTEGRITY_BLOCKED_AUDIT_REPORT_SELF_HASH_MISSING"
HISTORICAL_BLOCKER_HASH = "b59c6e23e0a3bc5dfcf89a2a0b67f78f581958055efdfcf0a78200ad9299ae01"
PREVIOUS_REMEDIATION_ATTEMPT = "BLOCKED_BY_INCORRECT_TASK_LINEAGE_SPEC"
PREVIOUS_REMEDIATION_SCIENTIFIC_EFFECT = "NONE"

REPORT_HASH_SCHEME = "MARKDOWN_BODY_SHA256_BEFORE_INTEGRITY_FOOTER_V1"
REPORT_PATH = (
    "docs/task_reports/"
    "TASK-039E3_R2R_UTILITY_INNER_D0_RESULT_INTEGRITY_V1_REPORT.md"
)
FOOTER_BEGIN = "<!-- BEGIN D0 RESULT INTEGRITY REPORT PROVENANCE V1 -->"
FOOTER_END = "<!-- END D0 RESULT INTEGRITY REPORT PROVENANCE V1 -->"
EXPECTED_REPORT_SELF_HASH = "fadaa840aedb5d2be96ea3a44ecb757e586578e4d25de2d2a82c244e7e8bcc51"

DETECTOR_PREDICTION_HASH = "a4b58f1c78b9bb53125da1a009f3fd05b02e1c83a789772a341a7679fddca0f6"
SCORE_EVIDENCE_HASH = "ee9acb8de899fb8aa13fa70d1675ad61862982ef20ab8815702c7a3c620be91c"
PRIVATE_METRIC_EVIDENCE_HASH = (
    "628270f3413276d6d76c1ed3e1802679d37eae125898d250bb61524cba151176"
)
EXECUTION_RUN_IDENTITY = "0593d05790fef3b9264af587c451ece6186db438541a8b14edabbb2ee4bdeeb9"

HISTORICAL_READINESS_HASH = "b18ccca46ed84e09aedeb258f6089e07444da0c108a60f4da3160fb3a521282d"
HISTORICAL_BUNDLE_HASH = "9b74f9c56571526870f274e0928516ce642e1bc0d692ee3cdd8dce0cceddafc7"
HISTORICAL_RECEIPT_HASH = "15559141048efd729b3b4645b4f0baa4ac6d07ceedb2417cbd7915f49435da70"

SCIENTIFIC_AUDIT_ARTIFACTS: dict[str, tuple[str, str]] = {
    "freeze_audit": (
        "docs/task_reports/TASK-039E3_R2R_UTILITY_INNER_D0_RESULT_INTEGRITY_V1_FREEZE_AUDIT.json",
        "8e22cb39ba038d3492592f4a3f91cbb64d2640d146dc615b35aab1137635fdc5",
    ),
    "score_oracle": (
        "docs/task_reports/TASK-039E3_R2R_UTILITY_INNER_D0_RESULT_INTEGRITY_V1_SCORE_ORACLE.json",
        "6c6e80549b9bc8f4e047c5db222af3de1647d7c0cee8684497d06eaff701df6e",
    ),
    "prediction_audit": (
        "docs/task_reports/TASK-039E3_R2R_UTILITY_INNER_D0_RESULT_INTEGRITY_V1_PREDICTION_AUDIT.json",
        "d76903177a1595870c841086aa0aa6debd302f679b71163fa4b38686975b37bc",
    ),
    "label_independence_audit": (
        "docs/task_reports/TASK-039E3_R2R_UTILITY_INNER_D0_RESULT_INTEGRITY_V1_LABEL_INDEPENDENCE_AUDIT.json",
        "9b57b0b7b8f40f2384dc7ce8d612ad5f4d24d954372fdeac6b6d13722b79014e",
    ),
    "metric_oracle": (
        "docs/task_reports/TASK-039E3_R2R_UTILITY_INNER_D0_RESULT_INTEGRITY_V1_METRIC_ORACLE.json",
        "89f7b33e89d24cab74a589ec0efdaaf2c47acacc1693fff24729151a7a07bfaa",
    ),
    "accounting_audit": (
        "docs/task_reports/TASK-039E3_R2R_UTILITY_INNER_D0_RESULT_INTEGRITY_V1_ACCOUNTING_AUDIT.json",
        "563bdecde07c2bf4c6d4543b2fa4d3dc42b250d7ff7e5e6bdd05c588fb138a89",
    ),
    "leakage_audit": (
        "docs/task_reports/TASK-039E3_R2R_UTILITY_INNER_D0_RESULT_INTEGRITY_V1_LEAKAGE_AUDIT.json",
        "84221c711b1635f5c2f31f40c3eef11b39df2f05835cff657ac583b650abb645",
    ),
    "independent_audit": (
        "docs/task_reports/TASK-039E3_R2R_UTILITY_INNER_D0_RESULT_INTEGRITY_V1_INDEPENDENT_AUDIT.json",
        "d88148c61df8669a291d86e6f2bcd18838954f05b61d1f512ad05601db620361",
    ),
}

HISTORICAL_PROVENANCE_ARTIFACTS: dict[str, tuple[str, str]] = {
    "readiness": (
        "docs/task_reports/TASK-039E3_R2R_UTILITY_INNER_D0_RESULT_INTEGRITY_V1_READINESS.json",
        HISTORICAL_READINESS_HASH,
    ),
    "bundle": (
        "docs/task_reports/TASK-039E3_R2R_UTILITY_INNER_D0_RESULT_INTEGRITY_V1_BUNDLE.json",
        HISTORICAL_BUNDLE_HASH,
    ),
    "receipt": (
        "docs/task_reports/TASK-039E3_R2R_UTILITY_INNER_D0_RESULT_INTEGRITY_V1_RECEIPT.json",
        HISTORICAL_RECEIPT_HASH,
    ),
}

PREDICTION_PATH = (
    "docs/task_reports/"
    "TASK-039E3_R2R_UTILITY_INNER_D0_DETECTOR_PREDICTION_ARTIFACT_V1.json"
)
BLOCKER_PATH = (
    "docs/task_reports/"
    "TASK-039E3_R2R_UTILITY_INNER_D0_RESULT_INTEGRITY_V1_BLOCKER.json"
)
R1_READINESS_PATH = (
    "docs/task_reports/"
    "TASK-039E3_R2R_UTILITY_INNER_D0_RESULT_INTEGRITY_REPORT_HASH_R1_READINESS.json"
)
R1_BUNDLE_PATH = (
    "docs/task_reports/"
    "TASK-039E3_R2R_UTILITY_INNER_D0_RESULT_INTEGRITY_REPORT_HASH_R1_BUNDLE.json"
)
R1_RECEIPT_PATH = (
    "docs/task_reports/"
    "TASK-039E3_R2R_UTILITY_INNER_D0_RESULT_INTEGRITY_REPORT_HASH_R1_RECEIPT.json"
)
REMEDIATION_REPORT_PATH = (
    "docs/task_reports/"
    "TASK-039E3_R2R_UTILITY_INNER_D0_RESULT_INTEGRITY_REPORT_HASH_REMEDIATION_R1.json"
)

HEX64_RE = re.compile(r"^[0-9a-f]{64}$")
INDEPENDENT_ATTACK_COUNT = 27


class ReportHashRemediationError(ValueError):
    """A fixed public provenance invariant was rejected."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


def _fail(code: str) -> NoReturn:
    raise ReportHashRemediationError(code)


def repository_root_v1() -> Path:
    return Path(__file__).resolve().parents[1]


def canonical_json_v1(value: Mapping[str, Any]) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    )


def stable_hash_v1(value: Mapping[str, Any]) -> str:
    return sha256(canonical_json_v1(value).encode("utf-8")).hexdigest()


def self_hashed_v1(payload: Mapping[str, Any]) -> dict[str, Any]:
    if "artifact_hash" in payload:
        _fail("PREHASHED_PAYLOAD_REJECTED")
    document = dict(payload)
    document["artifact_hash"] = stable_hash_v1(document)
    return document


def rehash_v1(document: dict[str, Any]) -> None:
    document.pop("artifact_hash", None)
    document["artifact_hash"] = stable_hash_v1(document)


def validate_hash_v1(value: Any) -> str:
    if type(value) is not str or HEX64_RE.fullmatch(value) is None:
        _fail("MALFORMED_HASH_REJECTED")
    return value


def validate_self_hash_v1(document: Mapping[str, Any], expected: str | None = None) -> str:
    if type(document) is not dict or type(document.get("artifact_hash")) is not str:
        _fail("SELF_HASH_SCHEMA_REJECTED")
    observed = validate_hash_v1(document["artifact_hash"])
    payload = {key: value for key, value in document.items() if key != "artifact_hash"}
    if stable_hash_v1(payload) != observed:
        _fail("SELF_HASH_REJECTED")
    if expected is not None and observed != expected:
        _fail("EXPECTED_HASH_REJECTED")
    return observed


def strict_json_v1(content: bytes) -> dict[str, Any]:
    def pairs_hook(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                _fail("DUPLICATE_JSON_MEMBER_REJECTED")
            result[key] = value
        return result

    try:
        value = json.loads(content.decode("utf-8"), object_pairs_hook=pairs_hook)
    except ReportHashRemediationError:
        raise
    except BaseException:
        _fail("JSON_REJECTED")
    if type(value) is not dict:
        _fail("JSON_OBJECT_REQUIRED")
    return value


def git_result_v1(root: Path, arguments: Sequence[str]) -> subprocess.CompletedProcess[bytes]:
    try:
        return subprocess.run(
            ("git", *arguments),
            cwd=root,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            check=False,
        )
    except BaseException:
        _fail("LOCAL_GIT_UNAVAILABLE")


def git_bytes_v1(root: Path, arguments: Sequence[str]) -> bytes:
    completed = git_result_v1(root, arguments)
    if completed.returncode != 0:
        _fail("LOCAL_GIT_REJECTED")
    return completed.stdout


def git_text_v1(root: Path, arguments: Sequence[str]) -> str:
    try:
        return git_bytes_v1(root, arguments).decode("utf-8").strip()
    except ReportHashRemediationError:
        raise
    except BaseException:
        _fail("LOCAL_GIT_TEXT_REJECTED")


def git_blob_bytes_v1(root: Path, commit: str, relative: str) -> bytes:
    """Read a committed blob without Windows rev:path length limitations."""
    listing = git_bytes_v1(root, ("ls-tree", "-r", "--full-tree", commit))
    suffix = ("\t" + relative).encode("utf-8")
    matches = [line for line in listing.splitlines() if line.endswith(suffix)]
    if len(matches) != 1:
        _fail("COMMITTED_BLOB_PATH_REJECTED")
    try:
        metadata = matches[0].split(b"\t", 1)[0].decode("ascii").split()
        if len(metadata) != 3 or metadata[1] != "blob":
            _fail("COMMITTED_BLOB_TYPE_REJECTED")
        object_id = metadata[2]
    except ReportHashRemediationError:
        raise
    except BaseException:
        _fail("COMMITTED_BLOB_METADATA_REJECTED")
    return git_bytes_v1(root, ("cat-file", "blob", object_id))


def validate_corrected_lineage_values_v1(
    blocker_is_ancestor: bool,
    continuity_parent: str,
    remediation_base: str,
) -> None:
    if blocker_is_ancestor is not True:
        _fail("CORRECTED_LINEAGE_ANCESTOR_REJECTED")
    if continuity_parent != HISTORICAL_BLOCKER_COMMIT:
        _fail("CORRECTED_LINEAGE_DIRECT_PARENT_REJECTED")
    if remediation_base != CORRECTED_REMEDIATION_BASE:
        _fail("CORRECTED_REMEDIATION_BASE_REJECTED")


def validate_local_lineage_v1(root: Path) -> dict[str, bool]:
    commits = (
        EXECUTION_COMMIT_A,
        EXECUTION_INDEPENDENT_COMMIT_B,
        RESULT_FREEZE_COMMIT_C,
        EXECUTION_CONTINUITY_COMMIT_D,
        INTEGRITY_AUDIT_COMMIT_A,
        INTEGRITY_REPORT_COMMIT_B,
        HISTORICAL_BLOCKER_COMMIT,
        CORRECTED_REMEDIATION_BASE,
    )
    for commit in commits:
        if git_result_v1(root, ("cat-file", "-e", f"{commit}^{{commit}}")).returncode != 0:
            _fail("REQUIRED_LOCAL_COMMIT_MISSING")
    ancestor = git_result_v1(
        root,
        ("merge-base", "--is-ancestor", HISTORICAL_BLOCKER_COMMIT, CORRECTED_REMEDIATION_BASE),
    ).returncode == 0
    parent = git_text_v1(root, ("rev-parse", f"{CORRECTED_REMEDIATION_BASE}^"))
    validate_corrected_lineage_values_v1(ancestor, parent, CORRECTED_REMEDIATION_BASE)
    if git_text_v1(root, ("branch", "--show-current")) != EXPECTED_BRANCH:
        _fail("REMEDIATION_BRANCH_REJECTED")
    if git_result_v1(root, ("merge-base", "--is-ancestor", CORRECTED_REMEDIATION_BASE, "HEAD")).returncode != 0:
        _fail("REMEDIATION_HEAD_LINEAGE_REJECTED")
    upstream = git_result_v1(
        root, ("rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{upstream}")
    )
    remote_ref = git_result_v1(
        root, ("show-ref", "--verify", f"refs/remotes/origin/{EXPECTED_BRANCH}")
    )
    if upstream.returncode == 0 or remote_ref.returncode == 0:
        _fail("REMOTE_PUSH_STATE_REJECTED")
    return {
        "corrected_lineage_gate": True,
        "blocker_direct_parent_check": True,
        "historical_blocker_commit_resolvable": True,
        "remote_push": False,
    }


def historical_report_body_v1(root: Path) -> bytes:
    body = git_blob_bytes_v1(root, INTEGRITY_REPORT_COMMIT_B, REPORT_PATH)
    if sha256(body).hexdigest() != EXPECTED_REPORT_SELF_HASH:
        _fail("HISTORICAL_REPORT_BODY_HASH_REJECTED")
    if FOOTER_BEGIN.encode("ascii") in body or FOOTER_END.encode("ascii") in body:
        _fail("HISTORICAL_REPORT_ALREADY_PATCHED")
    return body


def frozen_scientific_hashes_v1() -> dict[str, str]:
    return {name: digest for name, (_, digest) in SCIENTIFIC_AUDIT_ARTIFACTS.items()}


def validate_frozen_public_artifacts_v1(root: Path) -> dict[str, Any]:
    for relative, expected in SCIENTIFIC_AUDIT_ARTIFACTS.values():
        current = (root / relative).read_bytes()
        frozen = git_blob_bytes_v1(root, INTEGRITY_REPORT_COMMIT_B, relative)
        if current != frozen:
            _fail("SCIENTIFIC_AUDIT_ARTIFACT_MUTATION_REJECTED")
        validate_self_hash_v1(strict_json_v1(current), expected)
    for relative, expected in HISTORICAL_PROVENANCE_ARTIFACTS.values():
        current = (root / relative).read_bytes()
        frozen = git_blob_bytes_v1(root, INTEGRITY_REPORT_COMMIT_B, relative)
        if current != frozen:
            _fail("HISTORICAL_PROVENANCE_MUTATION_REJECTED")
        validate_self_hash_v1(strict_json_v1(current), expected)

    prediction = (root / PREDICTION_PATH).read_bytes()
    frozen_prediction = git_blob_bytes_v1(root, RESULT_FREEZE_COMMIT_C, PREDICTION_PATH)
    if prediction != frozen_prediction:
        _fail("DETECTOR_PREDICTION_MUTATION_REJECTED")
    validate_self_hash_v1(strict_json_v1(prediction), DETECTOR_PREDICTION_HASH)

    blocker = (root / BLOCKER_PATH).read_bytes()
    frozen_blocker = git_blob_bytes_v1(root, HISTORICAL_BLOCKER_COMMIT, BLOCKER_PATH)
    if blocker != frozen_blocker:
        _fail("HISTORICAL_BLOCKER_MUTATION_REJECTED")
    blocker_document = strict_json_v1(blocker)
    validate_self_hash_v1(blocker_document, HISTORICAL_BLOCKER_HASH)
    if blocker_document.get("blocker_code") != HISTORICAL_BLOCKER_CODE:
        _fail("HISTORICAL_BLOCKER_CODE_REJECTED")

    historical_bundle = strict_json_v1(
        (root / HISTORICAL_PROVENANCE_ARTIFACTS["bundle"][0]).read_bytes()
    )
    if historical_bundle.get("detector_prediction_artifact_hash") != DETECTOR_PREDICTION_HASH:
        _fail("DETECTOR_PREDICTION_BINDING_REJECTED")
    if historical_bundle.get("score_evidence_hash") != SCORE_EVIDENCE_HASH:
        _fail("SCORE_EVIDENCE_BINDING_REJECTED")
    if historical_bundle.get("private_metric_evidence_hash") != PRIVATE_METRIC_EVIDENCE_HASH:
        _fail("METRIC_EVIDENCE_BINDING_REJECTED")
    return {
        "scientific_audit_artifacts_unchanged_count": len(SCIENTIFIC_AUDIT_ARTIFACTS),
        "scientific_audit_artifact_mutations": 0,
        "detector_prediction_unchanged": True,
        "score_evidence_identity_unchanged": True,
        "metric_evidence_identity_unchanged": True,
        "historical_blocker_artifact_hash_match": True,
    }


def reproduce_historical_blocker_v1(root: Path) -> dict[str, bool | str]:
    body = historical_report_body_v1(root)
    bundle = strict_json_v1(
        git_blob_bytes_v1(
            root, INTEGRITY_REPORT_COMMIT_B, HISTORICAL_PROVENANCE_ARTIFACTS["bundle"][0]
        )
    )
    receipt = strict_json_v1(
        git_blob_bytes_v1(
            root, INTEGRITY_REPORT_COMMIT_B, HISTORICAL_PROVENANCE_ARTIFACTS["receipt"][0]
        )
    )
    missing_report = FOOTER_BEGIN.encode("ascii") not in body
    missing_bundle = "report_self_hash" not in bundle
    missing_receipt = "report_self_hash" not in receipt
    if not (missing_report and missing_bundle and missing_receipt):
        _fail("HISTORICAL_BLOCKER_REPRODUCTION_REJECTED")
    return {
        "report_self_hash_missing": True,
        "bundle_binding_missing": True,
        "receipt_binding_missing": True,
        "blocker_code": HISTORICAL_BLOCKER_CODE,
    }


def build_readiness_v1(report_self_hash: str) -> dict[str, Any]:
    validate_hash_v1(report_self_hash)
    return self_hashed_v1({
        "artifact_type": "task039e3_r2r_utility_inner_d0_result_integrity_report_hash_r1_readiness",
        "schema_version": SCHEMA_VERSION,
        "remediation_task_id": REMEDIATION_TASK_ID,
        "historical_result_integrity_task_id": HISTORICAL_TASK_ID,
        "result_freeze_commit_c": RESULT_FREEZE_COMMIT_C,
        "integrity_audit_commit_a": INTEGRITY_AUDIT_COMMIT_A,
        "integrity_audit_report_commit_b": INTEGRITY_REPORT_COMMIT_B,
        "historical_blocker_commit": HISTORICAL_BLOCKER_COMMIT,
        "historical_blocker_artifact_hash": HISTORICAL_BLOCKER_HASH,
        "corrected_remediation_base": CORRECTED_REMEDIATION_BASE,
        "report_hash_scheme": REPORT_HASH_SCHEME,
        "report_self_hash": report_self_hash,
        "frozen_scientific_audit_hashes": frozen_scientific_hashes_v1(),
        "detector_prediction_artifact_hash": DETECTOR_PREDICTION_HASH,
        "score_evidence_hash": SCORE_EVIDENCE_HASH,
        "private_metric_evidence_hash": PRIVATE_METRIC_EVIDENCE_HASH,
        "scientific_result_changed": False,
        "scientific_recomputation_performed": False,
        "D0_rerun": False,
        "D1_content_read": False,
        "D2_execution": False,
        "test2_access": False,
        "remote_push": False,
        "blocker_resolved": True,
        "status": "PASS",
    })


def build_bundle_v1(report_self_hash: str, readiness_hash: str) -> dict[str, Any]:
    validate_hash_v1(report_self_hash)
    validate_hash_v1(readiness_hash)
    return self_hashed_v1({
        "artifact_type": "task039e3_r2r_utility_inner_d0_result_integrity_report_hash_r1_bundle",
        "schema_version": SCHEMA_VERSION,
        "remediation_task_id": REMEDIATION_TASK_ID,
        "corrected_remediation_base": CORRECTED_REMEDIATION_BASE,
        "report_self_hash": report_self_hash,
        "report_hash_scheme": REPORT_HASH_SCHEME,
        "r1_readiness_hash": readiness_hash,
        "frozen_scientific_audit_hashes": frozen_scientific_hashes_v1(),
        "historical_blocked_readiness_hash": HISTORICAL_READINESS_HASH,
        "historical_blocked_bundle_hash": HISTORICAL_BUNDLE_HASH,
        "historical_blocked_receipt_hash": HISTORICAL_RECEIPT_HASH,
        "historical_blocker_artifact_hash": HISTORICAL_BLOCKER_HASH,
        "detector_prediction_artifact_hash": DETECTOR_PREDICTION_HASH,
        "execution_run_identity": EXECUTION_RUN_IDENTITY,
        "remote_state": REMOTE_STATE,
    })


def build_receipt_v1(
    report_self_hash: str,
    readiness_hash: str,
    bundle_hash: str,
) -> dict[str, Any]:
    for digest in (report_self_hash, readiness_hash, bundle_hash):
        validate_hash_v1(digest)
    return self_hashed_v1({
        "artifact_type": "task039e3_r2r_utility_inner_d0_result_integrity_report_hash_r1_receipt",
        "schema_version": SCHEMA_VERSION,
        "remediation_task_id": REMEDIATION_TASK_ID,
        "corrected_remediation_base": CORRECTED_REMEDIATION_BASE,
        "report_self_hash": report_self_hash,
        "report_hash_scheme": REPORT_HASH_SCHEME,
        "r1_readiness_hash": readiness_hash,
        "r1_bundle_hash": bundle_hash,
        "historical_blocker_artifact_hash": HISTORICAL_BLOCKER_HASH,
        "scientific_result_changed": False,
        "scientific_recomputation_performed": False,
        "remote_egress": REMOTE_STATE,
        "final_status": "PASS",
    })


def build_remediation_report_v1(
    report_self_hash: str,
    readiness_hash: str,
    bundle_hash: str,
    receipt_hash: str,
) -> dict[str, Any]:
    for digest in (report_self_hash, readiness_hash, bundle_hash, receipt_hash):
        validate_hash_v1(digest)
    return self_hashed_v1({
        "artifact_type": "task039e3_r2r_utility_inner_d0_result_integrity_report_hash_remediation_r1",
        "schema_version": SCHEMA_VERSION,
        "remediation_task_id": REMEDIATION_TASK_ID,
        "status": PASS_STATUS,
        "previous_remediation_attempt": PREVIOUS_REMEDIATION_ATTEMPT,
        "previous_remediation_attempt_scientific_effect": PREVIOUS_REMEDIATION_SCIENTIFIC_EFFECT,
        "historical_scientific_blocker": HISTORICAL_BLOCKER_CODE,
        "historical_blocker_artifact_hash": HISTORICAL_BLOCKER_HASH,
        "corrected_lineage": "PASS",
        "report_body_unchanged": True,
        "report_hash_scheme": REPORT_HASH_SCHEME,
        "report_self_hash": report_self_hash,
        "r1_readiness_hash": readiness_hash,
        "r1_bundle_hash": bundle_hash,
        "r1_receipt_hash": receipt_hash,
        "frozen_scientific_audit_hashes": frozen_scientific_hashes_v1(),
        "detector_prediction_artifact_hash": DETECTOR_PREDICTION_HASH,
        "detector_prediction_unchanged": True,
        "score_evidence_hash": SCORE_EVIDENCE_HASH,
        "score_evidence_unchanged": True,
        "private_metric_evidence_hash": PRIVATE_METRIC_EVIDENCE_HASH,
        "private_metric_evidence_unchanged": True,
        "scientific_test1_feature_parses": 0,
        "scientific_score_recomputations": 0,
        "scientific_label_parses": 0,
        "scientific_attack_event_derivations": 0,
        "scientific_metric_recomputations": 0,
        "authoritative_D0_executions": 0,
        "model_fits": 0,
        "threshold_calibrations": 0,
        "D0_reruns": 0,
        "D1_content_reads": 0,
        "D2_executions": 0,
        "test2_accesses": 0,
        "independent_attacks": INDEPENDENT_ATTACK_COUNT,
        "accepted_invalid": 0,
        "private_paths_exposed": 0,
        "private_numeric_values_exposed": 0,
        "remote_push": False,
    })


def validate_exact_document_v1(
    document: Mapping[str, Any], expected: Mapping[str, Any], code: str
) -> str:
    validate_self_hash_v1(document)
    if document != expected:
        _fail(code)
    return str(document["artifact_hash"])


def footer_bytes_v1(report_self_hash: str, bundle_hash: str, receipt_hash: str) -> bytes:
    for digest in (report_self_hash, bundle_hash, receipt_hash):
        validate_hash_v1(digest)
    return (
        f"{FOOTER_BEGIN}\n"
        f"Report-Hash-Scheme: {REPORT_HASH_SCHEME}\n"
        f"Report-Self-Hash: {report_self_hash}\n"
        "Remediation-Status: PASS\n"
        f"R1-Bundle-Hash: {bundle_hash}\n"
        f"R1-Receipt-Hash: {receipt_hash}\n"
        f"Historical-Blocker-Hash: {HISTORICAL_BLOCKER_HASH}\n"
        f"{FOOTER_END}\n"
    ).encode("ascii")


def validate_provenance_v1(
    patched_report: bytes,
    historical_body: bytes,
    readiness: Mapping[str, Any],
    bundle: Mapping[str, Any],
    receipt: Mapping[str, Any],
    remediation_report: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    begin = FOOTER_BEGIN.encode("ascii")
    end = FOOTER_END.encode("ascii")
    if patched_report.count(begin) != 1 or patched_report.count(end) != 1:
        _fail("FOOTER_COUNT_REJECTED")
    marker_index = patched_report.find(begin)
    if marker_index != len(historical_body) or patched_report[:marker_index] != historical_body:
        _fail("MARKDOWN_BODY_MUTATION_REJECTED")
    report_self_hash = sha256(historical_body).hexdigest()
    validate_hash_v1(report_self_hash)

    expected_readiness = build_readiness_v1(report_self_hash)
    readiness_hash = validate_exact_document_v1(
        readiness, expected_readiness, "READINESS_BINDING_REJECTED"
    )
    expected_bundle = build_bundle_v1(report_self_hash, readiness_hash)
    bundle_hash = validate_exact_document_v1(bundle, expected_bundle, "BUNDLE_BINDING_REJECTED")
    expected_receipt = build_receipt_v1(report_self_hash, readiness_hash, bundle_hash)
    receipt_hash = validate_exact_document_v1(
        receipt, expected_receipt, "RECEIPT_BINDING_REJECTED"
    )
    if patched_report[marker_index:] != footer_bytes_v1(
        report_self_hash, bundle_hash, receipt_hash
    ):
        _fail("FOOTER_BINDING_REJECTED")
    if remediation_report is not None:
        expected_report = build_remediation_report_v1(
            report_self_hash, readiness_hash, bundle_hash, receipt_hash
        )
        validate_exact_document_v1(
            remediation_report, expected_report, "REMEDIATION_REPORT_BINDING_REJECTED"
        )
    return {
        "markdown_body_byte_identical": True,
        "report_hash_scheme": REPORT_HASH_SCHEME,
        "report_self_hash": report_self_hash,
        "report_self_hash_match": True,
        "integrity_footer_count": 1,
        "footer_bundle_binding_match": True,
        "footer_receipt_binding_match": True,
        "historical_blocker_binding_match": True,
        "r1_readiness_hash": readiness_hash,
        "r1_bundle_hash": bundle_hash,
        "r1_receipt_hash": receipt_hash,
    }


def load_r1_documents_v1(root: Path) -> tuple[dict[str, Any], ...]:
    return tuple(
        strict_json_v1((root / relative).read_bytes())
        for relative in (
            R1_READINESS_PATH,
            R1_BUNDLE_PATH,
            R1_RECEIPT_PATH,
            REMEDIATION_REPORT_PATH,
        )
    )


def _expect_rejected_v1(action: Callable[[], Any]) -> bool:
    try:
        action()
    except ReportHashRemediationError:
        return True
    return False


def run_adversarial_suite_v1() -> tuple[int, int]:
    historical = b"synthetic immutable report body\n"
    report_hash = sha256(historical).hexdigest()
    readiness = build_readiness_v1(report_hash)
    bundle = build_bundle_v1(report_hash, readiness["artifact_hash"])
    receipt = build_receipt_v1(
        report_hash, readiness["artifact_hash"], bundle["artifact_hash"]
    )
    report = build_remediation_report_v1(
        report_hash,
        readiness["artifact_hash"],
        bundle["artifact_hash"],
        receipt["artifact_hash"],
    )
    patched = historical + footer_bytes_v1(
        report_hash, bundle["artifact_hash"], receipt["artifact_hash"]
    )

    def provenance(
        patched_value: bytes = patched,
        historical_value: bytes = historical,
        readiness_value: Mapping[str, Any] = readiness,
        bundle_value: Mapping[str, Any] = bundle,
        receipt_value: Mapping[str, Any] = receipt,
        report_value: Mapping[str, Any] = report,
    ) -> None:
        validate_provenance_v1(
            patched_value,
            historical_value,
            readiness_value,
            bundle_value,
            receipt_value,
            report_value,
        )

    attacks: list[Callable[[], Any]] = [
        lambda: validate_corrected_lineage_values_v1(False, CORRECTED_REMEDIATION_BASE, CORRECTED_REMEDIATION_BASE),
        lambda: validate_corrected_lineage_values_v1(False, HISTORICAL_BLOCKER_COMMIT, CORRECTED_REMEDIATION_BASE),
        lambda: validate_corrected_lineage_values_v1(True, HISTORICAL_BLOCKER_COMMIT, "0" * 40),
        lambda: provenance(historical),
        lambda: provenance(patched + patched[len(historical):]),
        lambda: provenance(patched.replace(REPORT_HASH_SCHEME.encode(), b"WRONG_SCHEME", 1)),
        lambda: provenance(b"X" + historical[1:] + patched[len(historical):]),
        lambda: provenance(historical.replace(b" ", b"  ", 1) + patched[len(historical):]),
        lambda: provenance(patched.replace(report_hash.encode(), ("0" * 64).encode(), 1)),
        lambda: provenance(
            historical + footer_bytes_v1(
                sha256(patched).hexdigest(), bundle["artifact_hash"], receipt["artifact_hash"]
            )
        ),
    ]

    semantic_mutations = (
        (readiness, "score_evidence_hash", "0" * 64),
        (bundle, "remote_state", "PUSHED"),
        (receipt, "final_status", "FAIL"),
        (readiness, "historical_blocker_artifact_hash", "0" * 64),
        (readiness, "frozen_scientific_audit_hashes", {**frozen_scientific_hashes_v1(), "freeze_audit": "0" * 64}),
        (readiness, "detector_prediction_artifact_hash", "0" * 64),
        (readiness, "score_evidence_hash", "1" * 64),
        (readiness, "private_metric_evidence_hash", "2" * 64),
        (readiness, "scientific_result_changed", True),
        (readiness, "scientific_recomputation_performed", True),
        (readiness, "D0_rerun", True),
        (readiness, "D1_content_read", True),
        (readiness, "D2_execution", True),
        (readiness, "test2_access", True),
        (readiness, "remote_push", True),
    )
    for original, key, value in semantic_mutations:
        mutated = json.loads(json.dumps(original))
        mutated[key] = value
        rehash_v1(mutated)
        if original is readiness:
            attacks.append(lambda m=mutated: provenance(readiness_value=m))
        elif original is bundle:
            attacks.append(lambda m=mutated: provenance(bundle_value=m))
        else:
            attacks.append(lambda m=mutated: provenance(receipt_value=m))

    malformed = json.loads(json.dumps(readiness))
    malformed["report_self_hash"] = "bad"
    rehash_v1(malformed)
    attacks.append(lambda: provenance(readiness_value=malformed))

    cycle = json.loads(json.dumps(bundle))
    cycle["full_markdown_hash"] = sha256(patched).hexdigest()
    rehash_v1(cycle)
    attacks.append(lambda: provenance(bundle_value=cycle))

    if len(attacks) != INDEPENDENT_ATTACK_COUNT:
        _fail("ADVERSARIAL_COUNT_REJECTED")
    accepted_invalid = sum(not _expect_rejected_v1(attack) for attack in attacks)
    return len(attacks), accepted_invalid


def validate_live_remediation_v1(root: Path) -> dict[str, Any]:
    lineage = validate_local_lineage_v1(root)
    frozen = validate_frozen_public_artifacts_v1(root)
    historical = historical_report_body_v1(root)
    readiness, bundle, receipt, remediation_report = load_r1_documents_v1(root)
    provenance = validate_provenance_v1(
        (root / REPORT_PATH).read_bytes(),
        historical,
        readiness,
        bundle,
        receipt,
        remediation_report,
    )
    attacks, accepted = run_adversarial_suite_v1()
    if accepted != 0:
        _fail("ADVERSARIAL_ACCEPTED_INVALID")
    return {
        **lineage,
        **frozen,
        **provenance,
        "remediation_report_hash": remediation_report["artifact_hash"],
        "independent_attacks": attacks,
        "accepted_invalid": accepted,
        "scientific_test1_feature_parses": 0,
        "scientific_score_recomputations": 0,
        "scientific_label_parses": 0,
        "scientific_metric_recomputations": 0,
        "D0_reruns": 0,
        "D1_content_reads": 0,
        "D2_executions": 0,
        "test2_accesses": 0,
        "private_paths_exposed": 0,
        "private_numeric_values_exposed": 0,
        "remote_egress_status": REMOTE_STATE,
        "push_attempted": False,
    }


def main() -> int:
    root = repository_root_v1()
    try:
        if sys.argv[1:] == ["--historical-blocker"]:
            outcome = reproduce_historical_blocker_v1(root)
            print(outcome["blocker_code"])
            print("REPORT_SELF_HASH_MISSING=true")
            print("BUNDLE_BINDING_MISSING=true")
            print("RECEIPT_BINDING_MISSING=true")
            return 0
        if sys.argv[1:]:
            print("D0_REPORT_HASH_REMEDIATION_ARGUMENTS_REJECTED")
            return 2
        outcome = validate_live_remediation_v1(root)
    except ReportHashRemediationError as error:
        print(error.code)
        return 1
    except BaseException:
        print("D0_REPORT_HASH_REMEDIATION_INTERNAL_BLOCKED")
        return 1
    print(PASS_STATUS)
    print(REMOTE_STATE)
    print(f"REPORT_SELF_HASH={outcome['report_self_hash']}")
    print(f"R1_READINESS_HASH={outcome['r1_readiness_hash']}")
    print(f"R1_BUNDLE_HASH={outcome['r1_bundle_hash']}")
    print(f"R1_RECEIPT_HASH={outcome['r1_receipt_hash']}")
    print(f"REMEDIATION_REPORT_HASH={outcome['remediation_report_hash']}")
    print(f"INDEPENDENT_ATTACKS={outcome['independent_attacks']}")
    print(f"ACCEPTED_INVALID={outcome['accepted_invalid']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
