"""One-shot infrastructure-recovery authorization for the frozen D2 arm.

Only immutable public authorities and a process-local recovery-custody receipt
are consumed. Prediction artifacts are compared as opaque frozen bytes and are
never scientifically parsed here.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from hashlib import sha1, sha256
import json
from pathlib import Path
import subprocess
from typing import Any, Mapping, NoReturn
import weakref

from paperworks.v6.task039e3_r2r_d2_execution_recovery_custody_v1 import (
    D2RecoveryCustodyPreflightReceiptV1,
    PATH_REDACTION_AUDIT_IDENTITY,
    RECOVERY_CUSTODY_MODULE_IDENTITY,
    RECOVERY_CUSTODY_REMEDIATION_HASH,
    stable_hash_v1,
    validate_d2_recovery_custody_preflight_v1,
)


TASK_ID = "TASK-039E3-R2R-UTILITY-INNER-D2-EXECUTION-PRIVATE-CUSTODY-REMEDIATION-AND-RECOVERY-AUTHORIZATION-V1"
D2_EXECUTION_RECOVERY_AUTHORIZATION_VERSION = "TASK039E3_R2R_D2_EXECUTION_RECOVERY_AUTHORIZATION_V1"
D2_EXECUTION_RECOVERY_AUTHORIZATION_SCOPE = "HAI_23_05_P1_TEST1_D2_INFRASTRUCTURE_RECOVERY_AFTER_PRIVATE_CUSTODY_FAILURE_V1"
AUTHORIZATION_STATUS = "AUTHORIZED_INFRASTRUCTURE_RECOVERY_ATTEMPT"

D2_DESIGN_HASH = "eb559a91350fd046204d223d6820ef7f0590ad4beb7a2b17114a496859758e51"
ORIGINAL_D2_AUTHORIZATION_HASH = "b931d7bd89e923dc4d380e35ed2b3ff514679a701e0b94a75d426130a3c4427c"
ORIGINAL_D2_EXECUTION_IMPLEMENTATION_IDENTITY = "03d3d8c3a2586e1eeaadbbc367f756c973920c3b7e84afd384eb7f45684aa733"
ORIGINAL_D2_EXECUTION_SOURCE_SHA256 = "0bfcfc5aba2a53ad24d08da0c1d9861472e350d1fe64ba6dabf1ba1a8a6689cc"
D0_PREDICTION_HASH = "a4b58f1c78b9bb53125da1a009f3fd05b02e1c83a789772a341a7679fddca0f6"
D1_PREDICTION_HASH = "58c3c49f9657f68d35c830b12eeb493ce4bbf7669c90f04813fb80246c3c2682"
SOURCE_MAP_HASH = "f866176000c3d5a943053ac3125d2700b0b72f25b5a0539d8f4713435a959818"
BLOCKER_HASH = "b721ddc45f0e7c97646b520eab9384d74c6c12231cb744c0f493fbf661111580"

STATE_AUDIT_HASH = "8480d931df6cab7dff59ffd58a24be7a37751ce99d5685353acbefee120704db"
ROOT_CAUSE_AUDIT_HASH = "b936f646963be187cb96ab26c454e7ecfcac8fa01c445f548eae1f168bb2cd53"
PATH_EXPOSURE_AUDIT_HASH = "71ae3e1f3a327a5bb2b342d0c00f1f39254b15a0d957c1682212285f54e4475a"
RESIDUE_AUDIT_HASH = "81c7ac685596c0dc5eb2ca73140e278f1175127e85516aafaf90c482ff834c06"
RECOVERY_ELIGIBILITY_HASH = "b7a0137ac5b090fc51215044a1d8cd8a8d2c1518d96990e59656df4501ca3e8b"
BLOCKER_INDEPENDENT_AUDIT_HASH = "1132af241473c695e8b04924b31d6660d8a475f00c15ad9957e06219931b657f"
BLOCKER_READINESS_HASH = "0d63fb4be13583deef4c7fe6c013d89fdad06a2b3f25cfd016197b28aea2bee9"
BLOCKER_BUNDLE_HASH = "bb0d0f3a41194a86022f0097161ff7094e6fd217b09ef983532fe5e784a1dd56"
BLOCKER_RECEIPT_HASH = "45d3a318765e77ec15d68724aae72ec7b5d7aad6b15be78baa3ad39f6272e900"
BLOCKER_REPORT_BODY_HASH = "8993a5db909d2c89db6d16999a0f2180f4b523c0c13c99e9d24bc7229be437c6"

REQUIRED_DISTINCT_SOURCE_COUNT = 2
SAME_SECOND_POLICY = "EXACT_DECISION_PHYSICAL_ROW_INDEX_EQUALITY"
D0_PRESERVATION_POLICY = "EVERY_FROZEN_D0_ALARM_IS_A_D2_ALARM"

HISTORICAL_TOTAL_EXECUTION_ATTEMPTS = 1
HISTORICAL_ABORTED_INFRASTRUCTURE_ATTEMPTS = 1
HISTORICAL_COMPLETED_SCIENTIFIC_EXECUTIONS = 0
HISTORICAL_RESULT_DRIVEN_RETRIES = 0
AUTHORIZED_ADDITIONAL_RECOVERY_ATTEMPTS = 1
MAXIMUM_FUTURE_TOTAL_EXECUTION_ATTEMPTS = 2
MAXIMUM_FUTURE_COMPLETED_SCIENTIFIC_EXECUTIONS = 1
RESULT_DRIVEN_RETRIES_AUTHORIZED = 0

FUTURE_RECOVERY_EXECUTION_ORDER = (
    "REPLAY_ORIGINAL_D2_AUTHORIZATION",
    "REPLAY_RECOVERY_AUTHORIZATION",
    "VALIDATE_RECOVERY_CUSTODY_PLANE",
    "VALIDATE_D0_PREDICTION",
    "VALIDATE_D1_PREDICTION",
    "VALIDATE_SOURCE_MAP",
    "PARSE_D0_PREDICTION",
    "PARSE_D1_PREDICTION",
    "COMPUTE_EXACT_FROZEN_FUSION",
    "PERSIST_FUSION_EVIDENCE_WITH_RECOVERY_REDACTED_WRITER",
    "FREEZE_COMBINED_PREDICTION",
    "PARSE_LABELS_AFTER_COMBINED_PREDICTION_FREEZE",
    "COMPUTE_EXACT_FROZEN_METRICS",
    "FREEZE_RESULT",
    "STOP",
)

_REPORT_HASHES = {
    "TASK-039E3_R2R_UTILITY_INNER_D2_EXECUTION_PRIVATE_CUSTODY_BLOCKER_AUDIT_V1_STATE.json": STATE_AUDIT_HASH,
    "TASK-039E3_R2R_UTILITY_INNER_D2_EXECUTION_PRIVATE_CUSTODY_BLOCKER_AUDIT_V1_ROOT_CAUSE.json": ROOT_CAUSE_AUDIT_HASH,
    "TASK-039E3_R2R_UTILITY_INNER_D2_EXECUTION_PRIVATE_CUSTODY_BLOCKER_AUDIT_V1_PATH_EXPOSURE.json": PATH_EXPOSURE_AUDIT_HASH,
    "TASK-039E3_R2R_UTILITY_INNER_D2_EXECUTION_PRIVATE_CUSTODY_BLOCKER_AUDIT_V1_RESIDUE.json": RESIDUE_AUDIT_HASH,
    "TASK-039E3_R2R_UTILITY_INNER_D2_EXECUTION_PRIVATE_CUSTODY_BLOCKER_AUDIT_V1_RECOVERY_ELIGIBILITY.json": RECOVERY_ELIGIBILITY_HASH,
    "TASK-039E3_R2R_UTILITY_INNER_D2_EXECUTION_PRIVATE_CUSTODY_BLOCKER_AUDIT_V1_INDEPENDENT_AUDIT.json": BLOCKER_INDEPENDENT_AUDIT_HASH,
    "TASK-039E3_R2R_UTILITY_INNER_D2_EXECUTION_PRIVATE_CUSTODY_BLOCKER_AUDIT_V1_READINESS.json": BLOCKER_READINESS_HASH,
    "TASK-039E3_R2R_UTILITY_INNER_D2_EXECUTION_PRIVATE_CUSTODY_BLOCKER_AUDIT_V1_BUNDLE.json": BLOCKER_BUNDLE_HASH,
    "TASK-039E3_R2R_UTILITY_INNER_D2_EXECUTION_PRIVATE_CUSTODY_BLOCKER_AUDIT_V1_RECEIPT.json": BLOCKER_RECEIPT_HASH,
    "TASK-039E3_R2R_UTILITY_INNER_D2_EXECUTION_V1_BLOCKER.json": BLOCKER_HASH,
    "TASK-039E3_R2R_UTILITY_INNER_D2_EXECUTION_AUTHORIZATION_V1_AUTHORIZATION.json": ORIGINAL_D2_AUTHORIZATION_HASH,
    "TASK-039E3_R2R_UTILITY_INNER_D2_EXECUTION_AUTHORIZATION_V1_SOURCE_MAP.json": SOURCE_MAP_HASH,
}


class D2ExecutionRecoveryAuthorizationV1Error(ValueError):
    pass


def _fail(code: str) -> NoReturn:
    raise D2ExecutionRecoveryAuthorizationV1Error(code)


def _root_v1() -> Path:
    return Path(__file__).resolve().parents[3]


def _strict_json_object_v1(path: Path) -> dict[str, Any]:
    def pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
        out: dict[str, Any] = {}
        for key, value in items:
            if key in out:
                _fail("D2_RECOVERY_PUBLIC_AUTHORITY_REJECTED")
            out[key] = value
        return out
    try:
        value = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=pairs)
        if type(value) is not dict:
            _fail("D2_RECOVERY_PUBLIC_AUTHORITY_REJECTED")
        return value
    except D2ExecutionRecoveryAuthorizationV1Error:
        raise
    except BaseException:
        _fail("D2_RECOVERY_PUBLIC_AUTHORITY_REJECTED")


def _validate_self_hash_v1(document: Mapping[str, Any], expected: str) -> None:
    payload = dict(document)
    observed = payload.pop("artifact_hash", None)
    if observed != expected or stable_hash_v1(payload) != expected:
        _fail("D2_RECOVERY_PUBLIC_AUTHORITY_REJECTED")


def _git_blob_identity_v1(commit: str, relative: str) -> str:
    result = subprocess.run(
        ["git", "ls-tree", "-r", commit], cwd=_root_v1(),
        capture_output=True, check=False,
    )
    if result.returncode != 0:
        _fail("D2_RECOVERY_PUBLIC_AUTHORITY_REJECTED")
    suffix = ("\t" + relative).encode("utf-8")
    matches = [line for line in result.stdout.splitlines() if line.endswith(suffix)]
    if len(matches) != 1:
        _fail("D2_RECOVERY_PUBLIC_AUTHORITY_REJECTED")
    try:
        return matches[0].split(b" ", 2)[2].split(b"\t", 1)[0].decode("ascii")
    except BaseException:
        _fail("D2_RECOVERY_PUBLIC_AUTHORITY_REJECTED")


def _git_blob_hash_v1(content: bytes) -> str:
    header = f"blob {len(content)}\0".encode("ascii")
    return sha1(header + content).hexdigest()


@dataclass(frozen=True)
class D2RecoveryPublicAuthorityReplayV1:
    authority_set_hash: str
    d2_design_hash_match: bool
    original_authorization_hash_match: bool
    original_implementation_unchanged: bool
    d0_prediction_unchanged: bool
    d1_prediction_unchanged: bool
    source_map_unchanged: bool
    root_cause_audit_hash_match: bool
    recovery_eligibility_hash_match: bool


def replay_d2_recovery_public_authorities_v1() -> D2RecoveryPublicAuthorityReplayV1:
    reports = _root_v1() / "docs" / "task_reports"
    for name, expected in _REPORT_HASHES.items():
        _validate_self_hash_v1(_strict_json_object_v1(reports / name), expected)

    design = _strict_json_object_v1(reports / "TASK-039E3_R2R_UTILITY_INNER_D2_DESIGN_V1_DESIGN.json")
    if design.get("d2_design_hash") != D2_DESIGN_HASH:
        _fail("D2_RECOVERY_D2_DESIGN_REJECTED")
    authorization = _strict_json_object_v1(reports / "TASK-039E3_R2R_UTILITY_INNER_D2_EXECUTION_AUTHORIZATION_V1_AUTHORIZATION.json")
    exact = {
        "d2_design_hash": D2_DESIGN_HASH,
        "d0_prediction_hash": D0_PREDICTION_HASH,
        "d1_prediction_hash": D1_PREDICTION_HASH,
        "source_map_hash": SOURCE_MAP_HASH,
        "required_distinct_source_count": REQUIRED_DISTINCT_SOURCE_COUNT,
        "same_second_policy": SAME_SECOND_POLICY,
        "d0_preservation_policy": D0_PRESERVATION_POLICY,
    }
    if any(authorization.get(k) != v for k, v in exact.items()):
        _fail("D2_RECOVERY_ORIGINAL_AUTHORIZATION_REJECTED")
    source_map = _strict_json_object_v1(reports / "TASK-039E3_R2R_UTILITY_INNER_D2_EXECUTION_AUTHORIZATION_V1_SOURCE_MAP.json")
    if (source_map.get("entry_count") != 42 or source_map.get("unique_relation_count") != 42
            or source_map.get("d2_design_hash") != D2_DESIGN_HASH):
        _fail("D2_RECOVERY_SOURCE_MAP_REJECTED")
    eligibility = _strict_json_object_v1(reports / "TASK-039E3_R2R_UTILITY_INNER_D2_EXECUTION_PRIVATE_CUSTODY_BLOCKER_AUDIT_V1_RECOVERY_ELIGIBILITY.json")
    if (eligibility.get("recovery_eligible") is not True
            or eligibility.get("recovery_class") != "PATH_REDACTION_AND_CUSTODY_RECOVERY"):
        _fail("D2_RECOVERY_ELIGIBILITY_REJECTED")

    implementation_rel = "src/paperworks/v6/task039e3_r2r_d2_inner_execution_v1.py"
    implementation = (_root_v1() / implementation_rel).read_bytes()
    if sha256(implementation).hexdigest() != ORIGINAL_D2_EXECUTION_SOURCE_SHA256:
        _fail("D2_RECOVERY_ORIGINAL_IMPLEMENTATION_REJECTED")
    opaque = (
        ("78d758f50657413eed28dc838212be9a1edeffc7",
         "docs/task_reports/TASK-039E3_R2R_UTILITY_INNER_D0_DETECTOR_PREDICTION_ARTIFACT_V1.json"),
        ("9fe9192c6da4e2d1f3c7a42ecdd28006e8534449",
         "docs/task_reports/TASK-039E3_R2R_UTILITY_INNER_D1_RULE_PREDICTION_ARTIFACT_V1.json"),
    )
    for commit, relative in opaque:
        if _git_blob_hash_v1((_root_v1() / relative).read_bytes()) != _git_blob_identity_v1(commit, relative):
            _fail("D2_RECOVERY_PREDICTION_BYTES_REJECTED")
    report = (reports / "TASK-039E3_R2R_UTILITY_INNER_D2_EXECUTION_PRIVATE_CUSTODY_BLOCKER_AUDIT_V1_REPORT.md").read_bytes()
    marker = b"<!-- BEGIN D2 CUSTODY BLOCKER AUDIT REPORT PROVENANCE V1 -->"
    if report.count(marker) != 1 or sha256(report.split(marker, 1)[0]).hexdigest() != BLOCKER_REPORT_BODY_HASH:
        _fail("D2_RECOVERY_BLOCKER_REPORT_REJECTED")
    authority_set_hash = stable_hash_v1({
        "report_hashes": sorted(_REPORT_HASHES.items()),
        "design_hash": D2_DESIGN_HASH,
        "implementation_sha256": ORIGINAL_D2_EXECUTION_SOURCE_SHA256,
        "d0_prediction_hash": D0_PREDICTION_HASH,
        "d1_prediction_hash": D1_PREDICTION_HASH,
    })
    return D2RecoveryPublicAuthorityReplayV1(
        authority_set_hash, True, True, True, True, True, True, True, True,
    )


@dataclass(frozen=True, repr=False)
class D2ExecutionRecoveryAuthorizationV1:
    artifact_type: str
    schema_version: str
    task_id: str
    authorization_version: str
    authorization_scope: str
    authorization_status: str
    public_authority_set_hash: str
    custody_preflight_hash: str
    recovery_custody_module_identity: str
    recovery_custody_remediation_hash: str
    path_redaction_audit_identity: str
    original_d2_design_hash: str
    original_d2_authorization_hash: str
    original_d2_execution_implementation_identity: str
    d0_prediction_hash: str
    d1_prediction_hash: str
    source_map_hash: str
    historical_blocker_hash: str
    blocker_state_audit_hash: str
    blocker_root_cause_hash: str
    blocker_path_exposure_hash: str
    blocker_residue_hash: str
    recovery_eligibility_hash: str
    required_distinct_source_count: int
    same_second_policy: str
    d0_preservation_policy: str
    historical_total_execution_attempts: int
    historical_aborted_infrastructure_attempts: int
    historical_completed_scientific_executions: int
    historical_result_driven_retries: int
    authorized_additional_recovery_attempts: int
    maximum_future_total_execution_attempts: int
    maximum_future_completed_scientific_executions: int
    result_driven_retries_authorized: int
    future_execution_order: tuple[str, ...]
    d2_recovery_execution_authorized: bool
    d2_design_change_authorized: bool
    fusion_change_authorized: bool
    source_map_change_authorized: bool
    corroboration_count_change_authorized: bool
    temporal_policy_change_authorized: bool
    d0_prediction_change_authorized: bool
    d1_prediction_change_authorized: bool
    d0_rerun_authorized: bool
    d1_rerun_authorized: bool
    d0_score_access_authorized: bool
    rule_reevaluation_authorized: bool
    label_before_combined_prediction_authorized: bool
    test1_feature_access_authorized: bool
    test2_authorized: bool
    outer_authorized: bool
    result_driven_retry_authorized: bool
    authorization_hash: str
    _preflight: D2RecoveryCustodyPreflightReceiptV1 = field(repr=False, compare=False)
    _replay: D2RecoveryPublicAuthorityReplayV1 = field(repr=False, compare=False)

    def __repr__(self) -> str:
        return "<D2ExecutionRecoveryAuthorizationV1 validated=True private_path=REDACTED>"

    def __reduce__(self) -> object:
        _fail("D2_RECOVERY_AUTHORIZATION_FACTORY_CUSTODY_REJECTED")

    def _payload(self) -> dict[str, Any]:
        return {k: v for k, v in self.__dict__.items()
                if not k.startswith("_") and k != "authorization_hash"}

    def to_public_dict(self) -> dict[str, Any]:
        return {**self._payload(), "artifact_hash": self.authorization_hash}


_ISSUED_AUTHORIZATIONS: dict[int, tuple[weakref.ReferenceType[D2ExecutionRecoveryAuthorizationV1], str]] = {}
_REAL_AUTHORIZATION_ISSUED = False


def _build_authorization_v1(
    preflight: D2RecoveryCustodyPreflightReceiptV1,
    replay: D2RecoveryPublicAuthorityReplayV1,
) -> D2ExecutionRecoveryAuthorizationV1:
    provisional = D2ExecutionRecoveryAuthorizationV1(
        "D2ExecutionRecoveryAuthorizationV1", "1.0.0", TASK_ID,
        D2_EXECUTION_RECOVERY_AUTHORIZATION_VERSION,
        D2_EXECUTION_RECOVERY_AUTHORIZATION_SCOPE, AUTHORIZATION_STATUS,
        replay.authority_set_hash, preflight.artifact_hash,
        RECOVERY_CUSTODY_MODULE_IDENTITY, RECOVERY_CUSTODY_REMEDIATION_HASH,
        PATH_REDACTION_AUDIT_IDENTITY, D2_DESIGN_HASH,
        ORIGINAL_D2_AUTHORIZATION_HASH, ORIGINAL_D2_EXECUTION_IMPLEMENTATION_IDENTITY,
        D0_PREDICTION_HASH, D1_PREDICTION_HASH, SOURCE_MAP_HASH, BLOCKER_HASH,
        STATE_AUDIT_HASH, ROOT_CAUSE_AUDIT_HASH, PATH_EXPOSURE_AUDIT_HASH,
        RESIDUE_AUDIT_HASH, RECOVERY_ELIGIBILITY_HASH,
        REQUIRED_DISTINCT_SOURCE_COUNT, SAME_SECOND_POLICY, D0_PRESERVATION_POLICY,
        HISTORICAL_TOTAL_EXECUTION_ATTEMPTS, HISTORICAL_ABORTED_INFRASTRUCTURE_ATTEMPTS,
        HISTORICAL_COMPLETED_SCIENTIFIC_EXECUTIONS, HISTORICAL_RESULT_DRIVEN_RETRIES,
        AUTHORIZED_ADDITIONAL_RECOVERY_ATTEMPTS, MAXIMUM_FUTURE_TOTAL_EXECUTION_ATTEMPTS,
        MAXIMUM_FUTURE_COMPLETED_SCIENTIFIC_EXECUTIONS, RESULT_DRIVEN_RETRIES_AUTHORIZED,
        FUTURE_RECOVERY_EXECUTION_ORDER, True,
        False, False, False, False, False, False, False, False, False, False,
        False, False, False, False, False, False, "", preflight, replay,
    )
    return replace(provisional, authorization_hash=stable_hash_v1(provisional._payload()))


def issue_d2_execution_recovery_authorization_v1(
    preflight: D2RecoveryCustodyPreflightReceiptV1,
) -> D2ExecutionRecoveryAuthorizationV1:
    global _REAL_AUTHORIZATION_ISSUED
    validate_d2_recovery_custody_preflight_v1(preflight)
    if _REAL_AUTHORIZATION_ISSUED:
        _fail("D2_RECOVERY_AUTHORIZATION_ALREADY_ISSUED")
    _REAL_AUTHORIZATION_ISSUED = True
    replay = replay_d2_recovery_public_authorities_v1()
    value = _build_authorization_v1(preflight, replay)
    oid = id(value)
    _ISSUED_AUTHORIZATIONS[oid] = (
        weakref.ref(value, lambda _: _ISSUED_AUTHORIZATIONS.pop(oid, None)),
        value.authorization_hash,
    )
    return value


def validate_d2_execution_recovery_authorization_v1(
    value: D2ExecutionRecoveryAuthorizationV1,
    preflight: D2RecoveryCustodyPreflightReceiptV1,
) -> str:
    issued = _ISSUED_AUTHORIZATIONS.get(id(value))
    if (type(value) is not D2ExecutionRecoveryAuthorizationV1 or issued is None
            or issued[0]() is not value or issued[1] != value.authorization_hash
            or value._preflight is not preflight):
        _fail("D2_RECOVERY_AUTHORIZATION_FACTORY_CUSTODY_REJECTED")
    validate_d2_recovery_custody_preflight_v1(preflight)
    expected = _build_authorization_v1(preflight, value._replay)
    if value != expected or value.to_public_dict() != expected.to_public_dict():
        _fail("D2_RECOVERY_AUTHORIZATION_REPLAY_REJECTED")
    return value.authorization_hash


def _issue_synthetic_recovery_authorization_v1(
    preflight: D2RecoveryCustodyPreflightReceiptV1,
) -> D2ExecutionRecoveryAuthorizationV1:
    """Private test hook that does not consume the one real issuance."""
    validate_d2_recovery_custody_preflight_v1(preflight)
    replay = replay_d2_recovery_public_authorities_v1()
    value = _build_authorization_v1(preflight, replay)
    oid = id(value)
    _ISSUED_AUTHORIZATIONS[oid] = (
        weakref.ref(value, lambda _: _ISSUED_AUTHORIZATIONS.pop(oid, None)),
        value.authorization_hash,
    )
    return value


__all__ = [
    "D2ExecutionRecoveryAuthorizationV1",
    "D2ExecutionRecoveryAuthorizationV1Error",
    "D2_EXECUTION_RECOVERY_AUTHORIZATION_SCOPE",
    "D2_EXECUTION_RECOVERY_AUTHORIZATION_VERSION",
    "issue_d2_execution_recovery_authorization_v1",
    "replay_d2_recovery_public_authorities_v1",
    "validate_d2_execution_recovery_authorization_v1",
]
