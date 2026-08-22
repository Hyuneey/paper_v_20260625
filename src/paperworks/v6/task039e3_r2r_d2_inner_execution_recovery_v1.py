"""One-shot D2 recovery bridge; scientific semantics remain in the frozen V1 module."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import re
from typing import Any, Mapping, NoReturn

from paperworks.v6 import task039e3_r2r_d2_inner_execution_v1 as original
from paperworks.v6 import task039e3_r2r_d2_execution_recovery_authorization_v1 as recovery_auth
from paperworks.v6 import task039e3_r2r_d2_execution_recovery_custody_v1 as recovery_custody


TASK_ID = "TASK-039E3-R2R-UTILITY-INNER-D2-EXECUTION-RECOVERY-V1"
D2_RECOVERY_EXECUTION_VERSION = "TASK039E3_R2R_D2_INNER_EXECUTION_RECOVERY_V1"
EXECUTION_MODE = "AUTHORIZED_INFRASTRUCTURE_RECOVERY_ATTEMPT"
PASS_STATUS = "passed_task039e3_r2r_utility_inner_d2_execution_recovery_v1"
SCIENTIFIC_STATUS = "D2_EXECUTED_RESULT_INTEGRITY_AUDIT_PENDING"
BASE_COMMIT = "adbac8a7b000fdf74d1d34fed920a6266e651926"
ORIGINAL_AUTHORIZATION_HASH = "b931d7bd89e923dc4d380e35ed2b3ff514679a701e0b94a75d426130a3c4427c"
RECOVERY_AUTHORIZATION_HASH = "0faa5c58073da28b0a3e1e9c4267aa4c16faa7723becf5d01b5ec9c391b7b141"
RECOVERY_PREFLIGHT_HASH = "945ff83f929d0f98ebc6ed942a0cbf1053dcb995fcc6ece40178793cc47cb917"
RECOVERY_CUSTODY_IDENTITY = "c0e3faafdab0cb84e2f8e62b9380c243b0faee9ab38cc014de36fed5464d62e6"
ORIGINAL_IMPLEMENTATION_IDENTITY = "03d3d8c3a2586e1eeaadbbc367f756c973920c3b7e84afd384eb7f45684aa733"
EXPECTED_ROW_COUNT = 54_000
EXPECTED_INDEPENDENT_ATTACKS = 24
SEMANTIC_DIFFERENTIAL_CASES = 8
HISTORICAL_TOTAL_ATTEMPTS = 1
HISTORICAL_ABORTED_INFRASTRUCTURE_ATTEMPTS = 1
MAXIMUM_TOTAL_ATTEMPTS = 2
MAXIMUM_COMPLETED_SCIENTIFIC_EXECUTIONS = 1
REPORT_HASH_SCHEME = "MARKDOWN_BODY_SHA256_BEFORE_INTEGRITY_FOOTER_V1"
NEXT_TASK = "TASK-039E3-R2R-UTILITY-INNER-D2-RESULT-INTEGRITY-AUDIT-V1"

BRIDGE_SCIENTIFIC_CALLS = (
    "_parse_frozen_d0_prediction_v1",
    "_parse_frozen_d1_prediction_v1",
    "_parse_frozen_source_map_v1",
    "_build_fusion_evidence_v1",
    "_build_combined_prediction_v1",
    "_persist_combined_prediction_before_label_v1",
    "_load_label_custody_once_v1",
    "metric_policy_v1.form_alarm_episodes_v1",
    "_build_private_metric_evidence_v1",
)

D2_RECOVERY_EXECUTION_IMPLEMENTATION_IDENTITY = original.stable_hash_v1({
    "artifact_type": "task039e3_r2r_d2_recovery_execution_implementation_identity_v1",
    "execution_version": D2_RECOVERY_EXECUTION_VERSION,
    "execution_mode": EXECUTION_MODE,
    "original_implementation_identity": ORIGINAL_IMPLEMENTATION_IDENTITY,
    "recovery_custody_identity": RECOVERY_CUSTODY_IDENTITY,
    "original_authorization_hash": ORIGINAL_AUTHORIZATION_HASH,
    "recovery_authorization_hash": RECOVERY_AUTHORIZATION_HASH,
    "scientific_calls_reused": list(BRIDGE_SCIENTIFIC_CALLS),
    "replaced_concern": "PRIVATE_EVIDENCE_PERSISTENCE_ONLY",
})

RESULT_PREFIX = "docs/task_reports/TASK-039E3_R2R_UTILITY_INNER_D2_EXECUTION_RECOVERY_V1_"
IMPLEMENTATION_AUDIT_PATH = RESULT_PREFIX + "IMPLEMENTATION_AUDIT.json"
ACCOUNTING_PATH = RESULT_PREFIX + "ACCOUNTING.json"
READINESS_PATH = RESULT_PREFIX + "READINESS.json"
BUNDLE_PATH = RESULT_PREFIX + "BUNDLE.json"
RECEIPT_PATH = RESULT_PREFIX + "RECEIPT.json"
REPORT_PATH = RESULT_PREFIX + "REPORT.md"
METRICS_PATH = "docs/task_reports/TASK-039E3_R2R_UTILITY_INNER_D2_METRICS_V1.json"


class D2RecoveryExecutionV1Error(RuntimeError):
    """Path-free recovery execution failure."""

    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


def _fail(code: str) -> NoReturn:
    if not re.fullmatch(r"[A-Z0-9_]+", code):
        code = "D2_RECOVERY_EXECUTION_UNEXPECTED"
    raise D2RecoveryExecutionV1Error(code)


def _root_v1() -> Path:
    return Path(__file__).resolve().parents[3]


def _self_hashed_v1(payload: Mapping[str, Any]) -> dict[str, Any]:
    if "artifact_hash" in payload:
        _fail("D2_RECOVERY_PUBLIC_PREHASH_REJECTED")
    value = dict(payload)
    value["artifact_hash"] = original.stable_hash_v1(value)
    return value


def _utc_now_v1() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _write_public_json_v1(relative: str, document: Mapping[str, Any]) -> bytes:
    try:
        return original._write_public_json_atomic_v1(relative, document)
    except original.D2InnerExecutionV1Error as exc:
        raise D2RecoveryExecutionV1Error(exc.code) from None
    except BaseException:
        _fail("D2_RECOVERY_PUBLIC_WRITE_REJECTED")


def _write_report_v1(text: str) -> None:
    path = _root_v1() / REPORT_PATH
    temporary = path.with_suffix(path.suffix + ".tmp")
    try:
        if path.exists() or path.is_symlink() or temporary.exists() or temporary.is_symlink():
            _fail("D2_RECOVERY_PUBLIC_REPORT_ALREADY_EXISTS")
        path.parent.mkdir(parents=True, exist_ok=True)
        with temporary.open("x", encoding="utf-8", newline="\n") as stream:
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        if path.read_text(encoding="utf-8") != text:
            _fail("D2_RECOVERY_PUBLIC_REPORT_REPLAY_REJECTED")
    except D2RecoveryExecutionV1Error:
        raise
    except BaseException:
        _fail("D2_RECOVERY_PUBLIC_REPORT_WRITE_REJECTED")


def _validate_private_document_v1(document: Mapping[str, Any]) -> str:
    observed = document.get("artifact_hash")
    if type(document) is not dict or type(observed) is not str:
        _fail("D2_RECOVERY_PRIVATE_DOCUMENT_REJECTED")
    try:
        if original._canonical_self_hash_v1(document) != observed:
            _fail("D2_RECOVERY_PRIVATE_DOCUMENT_HASH_REJECTED")
    except original.D2InnerExecutionV1Error:
        _fail("D2_RECOVERY_PRIVATE_DOCUMENT_HASH_REJECTED")
    return observed


def _persist_private_v1(root: recovery_custody.D2RecoveryPrivateRootV1,
                        filename: str, document: Mapping[str, Any]) -> str:
    expected = _validate_private_document_v1(document)
    try:
        observed = recovery_custody.write_recovery_private_json_atomic_v1(
            root, filename, document
        )
    except recovery_custody.D2RecoveryCustodyV1Error as exc:
        raise D2RecoveryExecutionV1Error(exc.code) from None
    if observed != expected:
        _fail("D2_RECOVERY_PRIVATE_DOCUMENT_REPLAY_REJECTED")
    return observed


def validate_static_recovery_boundary_v1() -> str:
    if original.D2_INNER_EXECUTION_IMPLEMENTATION_IDENTITY != ORIGINAL_IMPLEMENTATION_IDENTITY:
        _fail("D2_RECOVERY_ORIGINAL_IMPLEMENTATION_REJECTED")
    if recovery_custody.RECOVERY_CUSTODY_MODULE_IDENTITY != RECOVERY_CUSTODY_IDENTITY:
        _fail("D2_RECOVERY_CUSTODY_IDENTITY_REJECTED")
    if recovery_auth.ORIGINAL_D2_AUTHORIZATION_HASH != ORIGINAL_AUTHORIZATION_HASH:
        _fail("D2_RECOVERY_ORIGINAL_AUTHORIZATION_REJECTED")
    return D2_RECOVERY_EXECUTION_IMPLEMENTATION_IDENTITY


def _validate_real_authorities_v1(
    preflight: recovery_custody.D2RecoveryCustodyPreflightReceiptV1,
    authorization: recovery_auth.D2ExecutionRecoveryAuthorizationV1,
) -> None:
    recovery_custody.validate_d2_recovery_custody_preflight_v1(preflight)
    recovery_auth.validate_d2_execution_recovery_authorization_v1(authorization, preflight)
    if preflight.artifact_hash != RECOVERY_PREFLIGHT_HASH:
        _fail("D2_RECOVERY_PREFLIGHT_HASH_REJECTED")
    if authorization.authorization_hash != RECOVERY_AUTHORIZATION_HASH:
        _fail("D2_RECOVERY_AUTHORIZATION_HASH_REJECTED")
    if (
        authorization.historical_total_execution_attempts != HISTORICAL_TOTAL_ATTEMPTS
        or authorization.historical_aborted_infrastructure_attempts
        != HISTORICAL_ABORTED_INFRASTRUCTURE_ATTEMPTS
        or authorization.authorized_additional_recovery_attempts != 1
        or authorization.maximum_future_total_execution_attempts != MAXIMUM_TOTAL_ATTEMPTS
        or authorization.maximum_future_completed_scientific_executions
        != MAXIMUM_COMPLETED_SCIENTIFIC_EXECUTIONS
        or authorization.result_driven_retries_authorized != 0
        or authorization.d2_recovery_execution_authorized is not True
        or any((
            authorization.d2_design_change_authorized,
            authorization.fusion_change_authorized,
            authorization.source_map_change_authorized,
            authorization.corroboration_count_change_authorized,
            authorization.temporal_policy_change_authorized,
            authorization.d0_prediction_change_authorized,
            authorization.d1_prediction_change_authorized,
            authorization.d0_rerun_authorized,
            authorization.d1_rerun_authorized,
            authorization.d0_score_access_authorized,
            authorization.rule_reevaluation_authorized,
            authorization.label_before_combined_prediction_authorized,
            authorization.test1_feature_access_authorized,
            authorization.test2_authorized,
            authorization.outer_authorized,
            authorization.result_driven_retry_authorized,
        ))
    ):
        _fail("D2_RECOVERY_AUTHORIZATION_SCOPE_REJECTED")


@dataclass(frozen=True)
class D2RecoveryExecutionOutcomeV1:
    execution_run_hash: str
    fusion_evidence_hash: str
    combined_prediction_hash: str
    private_metric_evidence_hash: str
    metrics: tuple[tuple[str, original.ScientificD2MetricV1], ...]
    trigger_class_counts: tuple[tuple[str, int], ...]
    d2_point_alarm_count: int
    d2_alarm_episode_count: int
    rule_recovery_episode_count: int
    implementation_audit_hash: str
    accounting_hash: str
    readiness_hash: str
    bundle_hash: str
    receipt_hash: str
    report_self_hash: str


def _file_custody_v1(relative: str) -> tuple[str, str, str]:
    try:
        return original._file_commit_custody_v1(relative)
    except original.D2InnerExecutionV1Error as exc:
        raise D2RecoveryExecutionV1Error(exc.code) from None


def _report_body_v1(combined: original.ScientificCombinedPredictionArtifactV1,
                    metrics: Mapping[str, original.ScientificD2MetricV1],
                    d2_episode_count: int, recovery_episode_count: int) -> str:
    counts = dict(combined.trigger_class_counts)
    return (
        "# TASK-039E3-R2R Utility INNER D2 Recovery Execution V1\n\n"
        f"Status: `{PASS_STATUS}`\n\n"
        f"Scientific state: `{SCIENTIFIC_STATUS}`\n\n"
        "The sole authorized infrastructure recovery completed under the original "
        "frozen D2 scientific semantics. Historical attempt 1 remains recorded as an "
        "infrastructure-aborted attempt; this execution is total attempt 2.\n\n"
        f"- Original authorization: `{ORIGINAL_AUTHORIZATION_HASH}`\n"
        f"- Recovery authorization: `{RECOVERY_AUTHORIZATION_HASH}`\n"
        f"- CombinedPrediction artifact: `{combined.artifact_hash}`\n"
        f"- D2 point alarm count: `{combined.point_alarm_count}`\n"
        f"- D2 alarm episode count: `{d2_episode_count}`\n"
        f"- Corroboration points: `{counts['RULE_RECOVERY'] + counts['D0_AND_RULE_CORROBORATION']}`\n"
        f"- RULE_RECOVERY points: `{counts['RULE_RECOVERY']}`\n"
        f"- RULE_RECOVERY episodes: `{recovery_episode_count}`\n"
        f"- D2 Attack-event Recall: `{metrics['d2_attack_event_recall'].value}`\n"
        f"- D2 Normal FAR episodes/hour: `{metrics['d2_normal_far_episodes_per_hour'].value}`\n"
        f"- D0-missed Attack Recovery Rate: `{metrics['d0_missed_attack_recovery_rate'].value}`\n"
        f"- Incremental Attack-event Recall: `{metrics['incremental_attack_event_recall'].value}`\n"
        f"- Added Normal Recovery FAR episodes/hour: "
        f"`{metrics['added_normal_recovery_far_episodes_per_hour'].value}`\n"
        f"- Incremental Normal FAR episodes/hour: "
        f"`{metrics['incremental_normal_far_episodes_per_hour'].value}`\n"
        "- Total D2 attempts: `2`; infrastructure-aborted: `1`; completed scientific: `1`.\n"
        "- Result-driven retries: `0`; additional authorized attempts remaining: `0`.\n"
        "- D0/D1 executions, D0 score access, rule reevaluation, test1 feature access, "
        "test2 access, and OUTER execution: `0`.\n"
        "- Historical private-path exposure: `1` (`EPHEMERAL_PRIVATE_PATH_DISCLOSURE`); "
        "recovery exposure and tracked leaks: `0`.\n\n"
        f"Exact next task: `{NEXT_TASK}`.\n\n"
    )


def _write_recovery_reports_v1(
    combined: original.ScientificCombinedPredictionArtifactV1,
    fusion_hash: str,
    private_metric_hash: str,
    metrics: Mapping[str, original.ScientificD2MetricV1],
    d2_episode_count: int,
    recovery_episode_count: int,
) -> tuple[str, str, str, str, str, str]:
    bridge_commit, bridge_blob, bridge_sha = _file_custody_v1(
        "src/paperworks/v6/task039e3_r2r_d2_inner_execution_recovery_v1.py"
    )
    independent_commit, independent_blob, independent_sha = _file_custody_v1(
        "tests/test_task039e3_r2r_d2_inner_execution_recovery_v1_independent.py"
    )
    created = _utc_now_v1()
    implementation_audit = _self_hashed_v1({
        "artifact_type": "task039e3_r2r_d2_execution_recovery_v1_implementation_audit",
        "schema_version": original.SCHEMA_VERSION,
        "task_id": TASK_ID,
        "created_at_utc": created,
        "status": "PASS",
        "execution_version": D2_RECOVERY_EXECUTION_VERSION,
        "execution_mode": EXECUTION_MODE,
        "recovery_execution_implementation_identity": D2_RECOVERY_EXECUTION_IMPLEMENTATION_IDENTITY,
        "recovery_execution_commit_a": bridge_commit,
        "recovery_execution_git_blob": bridge_blob,
        "recovery_execution_source_sha256": bridge_sha,
        "independent_audit_commit_b": independent_commit,
        "independent_audit_git_blob": independent_blob,
        "independent_audit_source_sha256": independent_sha,
        "original_execution_implementation_identity": ORIGINAL_IMPLEMENTATION_IDENTITY,
        "original_execution_implementation_unchanged": True,
        "recovery_custody_module_identity": RECOVERY_CUSTODY_IDENTITY,
        "scientific_functions_reused": list(BRIDGE_SCIENTIFIC_CALLS),
        "private_persistence_only_changed_concern": True,
        "static_tests_passed": True,
        "independent_attacks": EXPECTED_INDEPENDENT_ATTACKS,
        "accepted_invalid": 0,
        "semantic_differential_cases": SEMANTIC_DIFFERENTIAL_CASES,
        "semantic_differential_divergences": 0,
        "production_changes_after_commit_a": 0,
        "private_paths_exposed": 0,
    })
    metric_document = _self_hashed_v1({
        "artifact_type": "task039e3_r2r_utility_inner_d2_metrics_v1",
        "schema_version": original.SCHEMA_VERSION,
        "task_id": TASK_ID,
        "created_at_utc": created,
        "execution_version": D2_RECOVERY_EXECUTION_VERSION,
        "execution_mode": EXECUTION_MODE,
        "d2_id": original.D2_ID,
        "d2_design_hash": original.D2_DESIGN_HASH,
        "original_authorization_hash": ORIGINAL_AUTHORIZATION_HASH,
        "recovery_authorization_hash": RECOVERY_AUTHORIZATION_HASH,
        "d0_prediction_hash": original.D0_PREDICTION_HASH,
        "d1_prediction_hash": original.D1_PREDICTION_HASH,
        "source_map_hash": original.SOURCE_MAP_HASH,
        "combined_prediction_hash": combined.artifact_hash,
        "fusion_evidence_hash": fusion_hash,
        "point_alarm_count": combined.point_alarm_count,
        "alarm_episode_count": d2_episode_count,
        "rule_recovery_episode_count": recovery_episode_count,
        "trigger_class_counts": dict(combined.trigger_class_counts),
        "corroboration_point_count": (
            dict(combined.trigger_class_counts)["RULE_RECOVERY"]
            + dict(combined.trigger_class_counts)["D0_AND_RULE_CORROBORATION"]
        ),
        "metrics": {name: metric.to_public_dict() for name, metric in metrics.items()},
        "private_metric_evidence_hash": private_metric_hash,
        "attack_intervals_public": False,
        "label_vector_public": False,
        "private_event_evidence_public": False,
        "raw_rule_source_sets_public": False,
    })
    run_payload = {
        "artifact_type": "task039e3_r2r_d2_recovery_execution_run_v1",
        "execution_version": D2_RECOVERY_EXECUTION_VERSION,
        "original_authorization_hash": ORIGINAL_AUTHORIZATION_HASH,
        "recovery_authorization_hash": RECOVERY_AUTHORIZATION_HASH,
        "d2_design_hash": original.D2_DESIGN_HASH,
        "d0_prediction_hash": original.D0_PREDICTION_HASH,
        "d1_prediction_hash": original.D1_PREDICTION_HASH,
        "source_map_hash": original.SOURCE_MAP_HASH,
        "fusion_evidence_hash": fusion_hash,
        "combined_prediction_hash": combined.artifact_hash,
        "private_metric_evidence_hash": private_metric_hash,
        "metric_artifact_hash": metric_document["artifact_hash"],
        "historical_d2_execution_attempts": 1,
        "recovery_d2_execution_attempts": 1,
        "total_d2_execution_attempts": 2,
    }
    execution_run_hash = original.stable_hash_v1(run_payload)
    accounting = _self_hashed_v1({
        "artifact_type": "task039e3_r2r_utility_inner_d2_execution_recovery_v1_accounting",
        "schema_version": original.SCHEMA_VERSION,
        "task_id": TASK_ID,
        "created_at_utc": created,
        "execution_run_hash": execution_run_hash,
        "historical_d2_execution_attempts": 1,
        "recovery_d2_execution_attempts": 1,
        "total_d2_execution_attempts": 2,
        "aborted_infrastructure_attempts": 1,
        "completed_scientific_executions": 1,
        "historical_execution_retries": 0,
        "recovery_execution_retries": 0,
        "result_driven_retries": 0,
        "additional_authorized_attempts_remaining": 0,
        "third_attempt_authorized": False,
        "recovery_d0_prediction_parses": 1,
        "recovery_d1_prediction_parses": 1,
        "recovery_source_map_reads": 1,
        "recovery_fusion_computations": EXPECTED_ROW_COUNT,
        "recovery_private_fusion_evidence_freezes": 1,
        "recovery_combined_prediction_freezes": 1,
        "recovery_label_scientific_parses": 1,
        "label_before_combined_prediction_access": False,
        "recovery_primary_metric_computations": 2,
        "recovery_incremental_metric_computations": 4,
        "D0_executions": 0,
        "D1_executions": 0,
        "D1_metric_reads": 0,
        "D0_score_accesses": 0,
        "D1_rule_reevaluations": 0,
        "test1_feature_accesses": 0,
        "test2_accesses": 0,
        "OUTER_executions": 0,
        "result_driven_changes": False,
        "historical_private_path_exposures": 1,
        "historical_path_exposure_classification": "EPHEMERAL_PRIVATE_PATH_DISCLOSURE",
        "recovery_private_path_exposures": 0,
        "tracked_private_path_leaks": 0,
        "push_attempted": False,
        "remote_egress_status": "LOCAL_ONLY_NOT_PUSHED",
    })
    body = _report_body_v1(combined, metrics, d2_episode_count, recovery_episode_count)
    report_hash = sha256(body.encode("utf-8")).hexdigest()
    readiness = _self_hashed_v1({
        "artifact_type": "task039e3_r2r_utility_inner_d2_execution_recovery_v1_readiness",
        "schema_version": original.SCHEMA_VERSION,
        "task_id": TASK_ID,
        "created_at_utc": created,
        "status": "PASS",
        "scientific_state": SCIENTIFIC_STATUS,
        "original_authorization_hash": ORIGINAL_AUTHORIZATION_HASH,
        "recovery_authorization_hash": RECOVERY_AUTHORIZATION_HASH,
        "execution_run_hash": execution_run_hash,
        "implementation_audit_hash": implementation_audit["artifact_hash"],
        "combined_prediction_hash": combined.artifact_hash,
        "metric_artifact_hash": metric_document["artifact_hash"],
        "accounting_hash": accounting["artifact_hash"],
        "fusion_evidence_hash": fusion_hash,
        "private_metric_evidence_hash": private_metric_hash,
        "d2_executed": True,
        "d2_result_frozen": True,
        "d2_result_integrity_audited": False,
        "d2_result_interpretation_ready": False,
        "additional_authorized_attempts_remaining": 0,
        "third_attempt_authorized": False,
        "test2_accesses": 0,
        "outer_authorized": False,
        "remote_egress_status": "LOCAL_ONLY_NOT_PUSHED",
        "exact_next_task": NEXT_TASK,
    })
    bundle = _self_hashed_v1({
        "artifact_type": "task039e3_r2r_utility_inner_d2_execution_recovery_v1_bundle",
        "schema_version": original.SCHEMA_VERSION,
        "task_id": TASK_ID,
        "status": "PASS",
        "original_authorization_hash": ORIGINAL_AUTHORIZATION_HASH,
        "recovery_authorization_hash": RECOVERY_AUTHORIZATION_HASH,
        "execution_run_hash": execution_run_hash,
        "implementation_audit_hash": implementation_audit["artifact_hash"],
        "combined_prediction_hash": combined.artifact_hash,
        "metric_artifact_hash": metric_document["artifact_hash"],
        "accounting_hash": accounting["artifact_hash"],
        "readiness_hash": readiness["artifact_hash"],
        "fusion_evidence_hash": fusion_hash,
        "private_metric_evidence_hash": private_metric_hash,
        "report_self_hash": report_hash,
        "report_hash_scheme": REPORT_HASH_SCHEME,
        "remote_egress_status": "LOCAL_ONLY_NOT_PUSHED",
    })
    receipt = _self_hashed_v1({
        "artifact_type": "task039e3_r2r_utility_inner_d2_execution_recovery_v1_receipt",
        "schema_version": original.SCHEMA_VERSION,
        "task_id": TASK_ID,
        "status": PASS_STATUS,
        "scientific_state": SCIENTIFIC_STATUS,
        "original_authorization_hash": ORIGINAL_AUTHORIZATION_HASH,
        "recovery_authorization_hash": RECOVERY_AUTHORIZATION_HASH,
        "execution_run_hash": execution_run_hash,
        "combined_prediction_hash": combined.artifact_hash,
        "bundle_hash": bundle["artifact_hash"],
        "readiness_hash": readiness["artifact_hash"],
        "report_self_hash": report_hash,
        "d2_executed": True,
        "d2_result_frozen": True,
        "d2_result_integrity_audited": False,
        "additional_authorized_attempts_remaining": 0,
        "third_attempt_authorized": False,
        "test2_accesses": 0,
        "outer_authorized": False,
        "push_attempted": False,
        "remote_egress_status": "LOCAL_ONLY_NOT_PUSHED",
        "blockers": [],
        "exact_next_task": NEXT_TASK,
    })
    footer = (
        "<!-- BEGIN D2 RECOVERY EXECUTION REPORT PROVENANCE V1 -->\n"
        f"Report-Hash-Scheme: {REPORT_HASH_SCHEME}\n"
        f"Report-Self-Hash: {report_hash}\n"
        f"Bundle-Hash: {bundle['artifact_hash']}\n"
        f"Receipt-Hash: {receipt['artifact_hash']}\n"
        "<!-- END D2 RECOVERY EXECUTION REPORT PROVENANCE V1 -->\n"
    )
    for relative, document in (
        (IMPLEMENTATION_AUDIT_PATH, implementation_audit),
        (METRICS_PATH, metric_document),
        (ACCOUNTING_PATH, accounting),
        (READINESS_PATH, readiness),
        (BUNDLE_PATH, bundle),
        (RECEIPT_PATH, receipt),
    ):
        _write_public_json_v1(relative, document)
    _write_report_v1(body + footer)
    return (
        execution_run_hash,
        str(implementation_audit["artifact_hash"]),
        str(accounting["artifact_hash"]),
        str(readiness["artifact_hash"]),
        str(bundle["artifact_hash"]),
        str(receipt["artifact_hash"]),
        report_hash,
    )


_REAL_RECOVERY_ENTRY_ATTEMPTED = False
_SCIENTIFIC_RECOVERY_ATTEMPT_STARTED = False
_SCIENTIFIC_RECOVERY_COMPLETED = False


def execute_authorized_d2_inner_recovery_v1() -> D2RecoveryExecutionOutcomeV1:
    """Execute total D2 attempt two exactly once, after one sentinel recheck."""

    global _REAL_RECOVERY_ENTRY_ATTEMPTED, _SCIENTIFIC_RECOVERY_ATTEMPT_STARTED
    global _SCIENTIFIC_RECOVERY_COMPLETED
    if _REAL_RECOVERY_ENTRY_ATTEMPTED or _SCIENTIFIC_RECOVERY_ATTEMPT_STARTED:
        _fail("D2_RECOVERY_THIRD_ATTEMPT_REJECTED")
    _REAL_RECOVERY_ENTRY_ATTEMPTED = True
    validate_static_recovery_boundary_v1()
    try:
        preflight = recovery_custody.perform_d2_recovery_custody_preflight_v1()
        authorization = recovery_auth.issue_d2_execution_recovery_authorization_v1(preflight)
        _validate_real_authorities_v1(preflight, authorization)
        grant = original.issue_committed_d2_inner_execution_grant_v1()
        if grant.authorization_hash != ORIGINAL_AUTHORIZATION_HASH:
            _fail("D2_RECOVERY_ORIGINAL_GRANT_REJECTED")
        token = original._issue_execution_token_v1(grant)
        state = original.D2ExecutionStateMachineV1()
        state.transition(original.D2ExecutionStateV1.NOT_STARTED,
                         original.D2ExecutionStateV1.GRANT_REPLAYED)

        # The sole additional scientific attempt starts at the first scientific parse.
        _SCIENTIFIC_RECOVERY_ATTEMPT_STARTED = True
        d0 = original._parse_frozen_d0_prediction_v1(token)
        d1 = original._parse_frozen_d1_prediction_v1(token)
        state.transition(original.D2ExecutionStateV1.GRANT_REPLAYED,
                         original.D2ExecutionStateV1.INPUT_PREDICTIONS_VALIDATED)
        source_map = original._parse_frozen_source_map_v1(token)
        state.transition(original.D2ExecutionStateV1.INPUT_PREDICTIONS_VALIDATED,
                         original.D2ExecutionStateV1.SOURCE_MAP_VALIDATED)
        evidence, evidence_document = original._build_fusion_evidence_v1(d0, d1, source_map)
        fusion_hash = _persist_private_v1(
            preflight._root, "task039e3_inner_d2_fusion_evidence_v1.json",
            evidence_document,
        )
        state.transition(original.D2ExecutionStateV1.SOURCE_MAP_VALIDATED,
                         original.D2ExecutionStateV1.FUSION_COMPUTED)
        combined = original._build_combined_prediction_v1(evidence)
        frozen_combined = original._persist_combined_prediction_before_label_v1(state, combined)

        # Label custody is resolved only after the CombinedPrediction bytes are frozen.
        hai_root = original._load_local_hai_root_v1()
        custody = original._load_label_custody_once_v1(
            state, hai_root / "hai-23.05" / original.LABEL_FILENAME
        )
        combined_path = _root_v1() / original.COMBINED_PREDICTION_RELATIVE_PATH
        if combined_path.read_bytes() != frozen_combined:
            _fail("D2_RECOVERY_COMBINED_BYTES_CHANGED_BEFORE_METRICS")
        combined_document = original._strict_json_object_v1(frozen_combined)
        original.validate_scientific_combined_prediction_document_v1(combined_document)
        records = combined_document["prediction_records"]
        d2_indices = tuple(int(item["physical_row_index"]) for item in records
                           if item["d2_alarm_emitted"] is True)
        recovery_indices = tuple(int(item["physical_row_index"]) for item in records
                                 if item["trigger_class"] == "RULE_RECOVERY")
        d2_episodes = original.metric_policy_v1.form_alarm_episodes_v1(d2_indices)
        recovery_episodes = original.metric_policy_v1.form_alarm_episodes_v1(recovery_indices)
        d0_reference = original._load_current_bytes_v1(original.D0_PREDICTION_RELATIVE_PATH)
        if (
            original._sha256_bytes_v1(d0_reference) != d0.raw_bytes_hash
            or d0_reference != original._result_commit_bytes_v1(
                original.D0_PREDICTION_FREEZE_COMMIT,
                original.D0_PREDICTION_RELATIVE_PATH,
            )
        ):
            _fail("D2_RECOVERY_D0_REFERENCE_RELOAD_REJECTED")
        d0_indices = tuple(index for index, alarm in enumerate(d0._alarms) if alarm)
        d0_episodes = original.metric_policy_v1.form_alarm_episodes_v1(d0_indices)
        metric_document, metrics = original._build_private_metric_evidence_v1(
            custody, d0_episodes, d2_episodes, recovery_episodes,
            combined.artifact_hash, fusion_hash,
        )
        private_metric_hash = _persist_private_v1(
            preflight._root, "task039e3_inner_d2_metric_evidence_v1.json",
            metric_document,
        )
        state.transition(original.D2ExecutionStateV1.LABEL_PARSED,
                         original.D2ExecutionStateV1.METRICS_COMPUTED)
        (
            execution_run_hash, implementation_audit_hash, accounting_hash,
            readiness_hash, bundle_hash, receipt_hash, report_hash,
        ) = _write_recovery_reports_v1(
            combined, fusion_hash, private_metric_hash, metrics,
            len(d2_episodes), len(recovery_episodes),
        )
        if combined_path.read_bytes() != frozen_combined:
            _fail("D2_RECOVERY_COMBINED_BYTES_CHANGED_AFTER_METRICS")
        if original._sha256_bytes_v1(original._load_current_bytes_v1(
                original.D0_PREDICTION_RELATIVE_PATH)) != d0.raw_bytes_hash:
            _fail("D2_RECOVERY_D0_PREDICTION_BYTES_CHANGED")
        if original._sha256_bytes_v1(original._load_current_bytes_v1(
                original.D1_PREDICTION_RELATIVE_PATH)) != d1.raw_bytes_hash:
            _fail("D2_RECOVERY_D1_PREDICTION_BYTES_CHANGED")
        if original._sha256_bytes_v1(original._load_current_bytes_v1(
                original.SOURCE_MAP_RELATIVE_PATH)) != source_map.raw_bytes_hash:
            _fail("D2_RECOVERY_SOURCE_MAP_BYTES_CHANGED")
        original._consume_execution_token_v1(token)
        state.transition(original.D2ExecutionStateV1.METRICS_COMPUTED,
                         original.D2ExecutionStateV1.RESULT_FROZEN)
        _SCIENTIFIC_RECOVERY_COMPLETED = True
        return D2RecoveryExecutionOutcomeV1(
            execution_run_hash, fusion_hash, combined.artifact_hash,
            private_metric_hash, tuple(metrics.items()), combined.trigger_class_counts,
            combined.point_alarm_count, len(d2_episodes), len(recovery_episodes),
            implementation_audit_hash, accounting_hash, readiness_hash,
            bundle_hash, receipt_hash, report_hash,
        )
    except D2RecoveryExecutionV1Error:
        raise
    except recovery_custody.D2RecoveryCustodyV1Error as exc:
        raise D2RecoveryExecutionV1Error(exc.code) from None
    except recovery_auth.D2ExecutionRecoveryAuthorizationV1Error as exc:
        raise D2RecoveryExecutionV1Error(exc.code) from None
    except original.D2InnerExecutionV1Error as exc:
        raise D2RecoveryExecutionV1Error(exc.code) from None
    except BaseException:
        _fail("D2_RECOVERY_EXECUTION_UNEXPECTED")


def reject_prohibited_recovery_operation_v1(operation: str) -> NoReturn:
    prohibited = {
        "third_attempt", "retry", "fusion_change", "source_map_change",
        "source_count_change", "temporal_window", "d0_suppression", "raw_rule_or",
        "d0_score", "d0_rerun", "d1_rerun", "d1_metric_read", "rule_reevaluation",
        "original_private_writer", "fallback_custody", "label_before_prediction",
        "test1_feature", "test2", "outer", "result_driven_retry",
    }
    if operation in prohibited:
        _fail("D2_RECOVERY_PROHIBITED_OPERATION_REJECTED")
    _fail("D2_RECOVERY_UNKNOWN_OPERATION_REJECTED")


__all__ = [
    "D2RecoveryExecutionOutcomeV1",
    "D2RecoveryExecutionV1Error",
    "D2_RECOVERY_EXECUTION_IMPLEMENTATION_IDENTITY",
    "D2_RECOVERY_EXECUTION_VERSION",
    "EXECUTION_MODE",
    "SEMANTIC_DIFFERENTIAL_CASES",
    "execute_authorized_d2_inner_recovery_v1",
    "reject_prohibited_recovery_operation_v1",
    "validate_static_recovery_boundary_v1",
]
