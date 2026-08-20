"""Single-use real INNER execution bridge for frozen D0 PCA-SPE V1.

The real entry point accepts no scientific arguments.  It replays the complete
committed authorization set, validates the exact private preprocessing/model/
threshold custody, parses test1 features once, persists a label-blind detector
prediction before any label access, and then computes the two frozen metrics.
Private paths, numeric model values, scores, labels, and intervals never enter
the public artifact surface.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from enum import Enum
from hashlib import sha256
import json
import math
import os
from pathlib import Path
import platform
import re
import subprocess
from typing import Any, Mapping, NoReturn, Sequence
import weakref

from paperworks.v6.common import stable_hash_v1
from paperworks.v6 import task039e3_r2r_d0_detector_design_v1 as design_v1
from paperworks.v6 import task039e3_r2r_utility_evaluator_metrics_v1 as metric_policy_v1
from paperworks.v6 import task039e3_r2r_utility_protocol_v3 as protocol_v3


TASK_ID = "TASK-039E3-R2R-UTILITY-INNER-D0-EXECUTION-V1"
PASS_STATUS = "passed_task039e3_r2r_utility_inner_d0_execution_v1"
SCIENTIFIC_STATUS = "D0_EXECUTED_RESULT_INTEGRITY_AUDIT_PENDING"
D0_INNER_EXECUTION_VERSION = "TASK039E3_R2R_D0_INNER_EXECUTION_V1"
EXECUTION_MODE = "REAL_INNER_D0_PCA_SPE"
SCHEMA_VERSION = "1.0.0"

AUTHORIZATION_FREEZE_COMMIT = "01cd15831246f94b2111fd3d9c0589e639f2d254"
AUTHORIZATION_SCOPE = "HAI_23_05_P1_TEST1_D0_PCA_SPE_INNER_V1"
AUTHORIZATION_HASH = "a155fbb2659dc2a8b233db179706a13338a58ae41610f5c6db01f90f3b76a1ef"
PREFLIGHT_HASH = "033f1f9981bb5323e2830fa30d7e6613ce49b7a530e14a50ca2c4df75b848131"
RESTORATION_REPORT_HASH = "dc25f9aa51dc1a31d068110399dd29a7698f273d7cff9621f1634d7e16715ab9"
AUTHORIZATION_ACCOUNTING_HASH = "98493fe49d1c816c713ae2068276717137d6bd321b92e65dd0b23e0ff91b47fe"
AUTHORIZATION_READINESS_HASH = "3a105a529fc1adbb85fae1d2a1cfe2a5777e858059ef7cd6a51651b8bea5b93c"
AUTHORIZATION_BUNDLE_HASH = "618f5add4ad13f8c999414add7a294ee25946323baa775b54e4b90838c97e1a0"
AUTHORIZATION_RECEIPT_HASH = "10540956fe37ccd025d82d1e7a7c61eef26d869c1e9f97c7bda9b2415d4e12f2"

DETECTOR_ID = "D0_PCA_SPE_V1"
DETECTOR_FAMILY = "PCA_RECONSTRUCTION_SPE"
DESIGN_HASH = "357d19d02dee73273d52c7b147b5ddcfa11ead43a7198f2bf089ec78c2d8e174"
FEATURE_COUNT = 37
FEATURE_SET_HASH = "6dea06e82c0d99f35a0d11c5e97503e8bb3a0fc8c1d9963b997986021fd23515"
FEATURE_ORDER_HASH = "a612bdb9850ad0dd865dc62b23199bf2b696452c492e4aabe09fe554fa246d57"
PREPROCESSING_HASH = "baae5495094b211731e4fcdf7bab2870e3c81e7c973bfe052fc87b457ccb6270"
MODEL_HASH = "f32943cc2172100c77514d9ce8f6731978b51934e753234b2d34b5154127b54b"
THRESHOLD_HASH = "7ac0628cad5983b9864d31a9984bd414867b80f175248dbdf5cd69d7589f3695"
SELECTED_K = 10
RESIDUAL_DIMENSIONS = 27
PCA_EXPLAINED_VARIANCE_TARGET = 0.95
THRESHOLD_ALPHA = 0.001
THRESHOLD_Q_INDEX = 125_873
THRESHOLD_COMPARATOR = "score > threshold"

PYTHON_VERSION = "3.12.13"
PYTHON_RUNTIME_IDENTITY = "CPython-3.12"
NUMPY_VERSION = "2.3.5"
NUMERIC_BACKEND = "NUMPY_LINEAR_ALGEBRA"
SCIENTIFIC_FLOAT_DTYPE = "float64"

DATASET_MANIFEST_ID = "5b0c395169fea468f7afd52aceafc4e6dadf062a1bc557c5bbe5dd6b8a761aa2"
INNER_SPLIT_ID = "30a7c88d6e0af5c37493237cc83b9520cbcd6f43c2dee7bb50ec3cac2668e7d0"
TEST1_FEATURE_FILENAME = "hai-test1.csv"
TEST1_FEATURE_SHA256 = "78c7f1d4de1f2ab9ccc2f8c719f80f831033543adb0c81d0d78f84f40838d4be"
TEST1_FEATURE_BYTE_SIZE = 31_255_559
TEST1_LABEL_FILENAME = "label-test1.csv"
TEST1_LABEL_SHA256 = "eaf69edb9c5834bc393afd7bf658b5e408d34fd7bfc3261f80516765fb818fbc"
TEST1_LABEL_BYTE_SIZE = 1_242_017
EXPECTED_ROW_COUNT = 54_000

TRAIN1_SHA256 = "53007b0ba604fbf338e7ac2e08cd81d874b5d1388f3aecb213ddcba5bf2bec4a"
TRAIN2_SHA256 = "0e520e82bf78a661ab19ce4967f3c766bd809820f457a9c90c365102d4534c56"
TRAIN3_SHA256 = "bfcec2dc05adea103e7491546b0e28268faaa26d3cc717d10f4595c94b81e85d"
COMBINED_FIT_ROWS = 572_400
TRAIN3_ROWS = 126_000

ATTACK_EVENT_POLICY = "MAXIMAL_CONTIGUOUS_STRICT_LABEL_ONE_RUNS_FILE_LOCAL"
ALARM_EPISODE_POLICY = "MAXIMAL_CONTIGUOUS_UNIQUE_ONE_SECOND_DECISION_INDICES_FILE_LOCAL"
ATTACK_EVENT_RECALL_FORMULA = (
    "ATTACK_EVENTS_OVERLAPPED_BY_AT_LEAST_ONE_ALARM_EPISODE_DIVIDED_BY_ALL_ATTACK_EVENTS"
)
NORMAL_FAR_FORMULA = (
    "ALARM_EPISODES_WITH_NO_ATTACK_TIMESTAMP_DIVIDED_BY_NORMAL_LABELED_SECONDS_OVER_3600"
)

NUMERIC_DIFFERENTIAL_CASES = 5
EXPECTED_INDEPENDENT_ATTACKS = 34

PREDICTION_RELATIVE_PATH = (
    "docs/task_reports/"
    "TASK-039E3_R2R_UTILITY_INNER_D0_DETECTOR_PREDICTION_ARTIFACT_V1.json"
)

BRIDGE_SEMANTIC_POLICY = {
    "artifact_type": "task039e3_r2r_d0_inner_execution_bridge_semantics_v1",
    "execution_version": D0_INNER_EXECUTION_VERSION,
    "execution_mode": EXECUTION_MODE,
    "authorization_scope": AUTHORIZATION_SCOPE,
    "detector_id": DETECTOR_ID,
    "design_hash": DESIGN_HASH,
    "feature_order_hash": FEATURE_ORDER_HASH,
    "preprocessing_hash": PREPROCESSING_HASH,
    "model_hash": MODEL_HASH,
    "threshold_hash": THRESHOLD_HASH,
    "selected_k": SELECTED_K,
    "score": "STANDARDIZE_PROJECT_RESIDUAL_SUM_OF_SQUARES",
    "comparator": THRESHOLD_COMPARATOR,
    "prediction_first": True,
    "label_before_prediction": False,
    "attack_event_policy": ATTACK_EVENT_POLICY,
    "alarm_episode_policy": ALARM_EPISODE_POLICY,
    "attack_event_recall_formula": ATTACK_EVENT_RECALL_FORMULA,
    "normal_far_formula": NORMAL_FAR_FORMULA,
    "test2_authorized": False,
    "d1_execution_authorized": False,
    "d2_authorized": False,
    "retries": 0,
}
D0_INNER_EXECUTION_IMPLEMENTATION_IDENTITY = stable_hash_v1(BRIDGE_SEMANTIC_POLICY)


class InnerD0ExecutionV1Error(ValueError):
    """A fixed authorization, custody, state, or numeric invariant differs."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


def _fail(code: str) -> NoReturn:
    raise InnerD0ExecutionV1Error(code)


def _repository_root_v1() -> Path:
    return Path(__file__).resolve().parents[3]


def _strict_sha256_v1(value: object, code: str) -> str:
    if type(value) is not str or re.fullmatch(r"[a-f0-9]{64}", value) is None:
        _fail(code)
    return value


def _canonical_self_hash_v1(document: Mapping[str, Any]) -> str:
    observed = _strict_sha256_v1(document.get("artifact_hash"), "ARTIFACT_HASH_INVALID")
    payload = {key: value for key, value in document.items() if key != "artifact_hash"}
    if stable_hash_v1(payload) != observed:
        _fail("ARTIFACT_SELF_HASH_INVALID")
    return observed


def _strict_json_object_v1(content: bytes) -> dict[str, Any]:
    def reject_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                _fail("DUPLICATE_JSON_MEMBER_REJECTED")
            result[key] = value
        return result

    try:
        value = json.loads(content.decode("utf-8"), object_pairs_hook=reject_duplicates)
    except InnerD0ExecutionV1Error:
        raise
    except BaseException:
        _fail("JSON_DOCUMENT_REJECTED")
    if type(value) is not dict:
        _fail("JSON_OBJECT_REQUIRED")
    return value


def _git_output_v1(arguments: Sequence[str]) -> bytes:
    try:
        completed = subprocess.run(
            ("git", *arguments),
            cwd=_repository_root_v1(),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            check=False,
        )
    except BaseException:
        _fail("COMMITTED_GIT_REPLAY_UNAVAILABLE")
    if completed.returncode != 0:
        _fail("COMMITTED_GIT_REPLAY_REJECTED")
    return completed.stdout


_COMMITTED_ARTIFACT_PATHS = {
    "restoration": (
        "docs/task_reports/"
        "TASK-039E3_R2R_UTILITY_INNER_D0_EXECUTION_AUTHORIZATION_TEST1_CUSTODY_RESTORATION_V1.json"
    ),
    "preflight": (
        "docs/task_reports/"
        "TASK-039E3_R2R_UTILITY_INNER_D0_EXECUTION_AUTHORIZATION_RESTORATION_V1_PREFLIGHT.json"
    ),
    "authorization": (
        "docs/task_reports/"
        "TASK-039E3_R2R_UTILITY_INNER_D0_EXECUTION_AUTHORIZATION_RESTORATION_V1_AUTHORIZATION.json"
    ),
    "accounting": (
        "docs/task_reports/"
        "TASK-039E3_R2R_UTILITY_INNER_D0_EXECUTION_AUTHORIZATION_RESTORATION_V1_ACCOUNTING.json"
    ),
    "readiness": (
        "docs/task_reports/"
        "TASK-039E3_R2R_UTILITY_INNER_D0_EXECUTION_AUTHORIZATION_RESTORATION_V1_READINESS.json"
    ),
    "bundle": (
        "docs/task_reports/"
        "TASK-039E3_R2R_UTILITY_INNER_D0_EXECUTION_AUTHORIZATION_RESTORATION_V1_BUNDLE.json"
    ),
    "receipt": (
        "docs/task_reports/"
        "TASK-039E3_R2R_UTILITY_INNER_D0_EXECUTION_AUTHORIZATION_RESTORATION_V1_RECEIPT.json"
    ),
}
_COMMITTED_ARTIFACT_HASHES = {
    "restoration": RESTORATION_REPORT_HASH,
    "preflight": PREFLIGHT_HASH,
    "authorization": AUTHORIZATION_HASH,
    "accounting": AUTHORIZATION_ACCOUNTING_HASH,
    "readiness": AUTHORIZATION_READINESS_HASH,
    "bundle": AUTHORIZATION_BUNDLE_HASH,
    "receipt": AUTHORIZATION_RECEIPT_HASH,
}


def _load_committed_artifact_set_v1() -> dict[str, dict[str, Any]]:
    root = _repository_root_v1()
    if root.is_symlink() or not root.is_dir():
        _fail("COMMITTED_REPOSITORY_ROOT_REJECTED")
    _git_output_v1(("merge-base", "--is-ancestor", AUTHORIZATION_FREEZE_COMMIT, "HEAD"))
    documents: dict[str, dict[str, Any]] = {}
    for name, relative in _COMMITTED_ARTIFACT_PATHS.items():
        path = root / relative
        try:
            if path.is_symlink() or not path.is_file():
                _fail("COMMITTED_ARTIFACT_FILE_REJECTED")
            current = path.read_bytes()
        except InnerD0ExecutionV1Error:
            raise
        except BaseException:
            _fail("COMMITTED_ARTIFACT_READ_REJECTED")
        frozen = _git_output_v1(("show", f"{AUTHORIZATION_FREEZE_COMMIT}:{relative}"))
        if current != frozen:
            _fail("COMMITTED_ARTIFACT_BYTES_DIFFER")
        documents[name] = _strict_json_object_v1(current)
    return documents


def _validate_committed_artifact_set_v1(
    documents: Mapping[str, Mapping[str, Any]],
) -> None:
    if type(documents) is not dict or set(documents) != set(_COMMITTED_ARTIFACT_PATHS):
        _fail("COMMITTED_ARTIFACT_SET_CLOSURE_REJECTED")
    for name, expected in _COMMITTED_ARTIFACT_HASHES.items():
        document = documents[name]
        if type(document) is not dict or _canonical_self_hash_v1(document) != expected:
            _fail("COMMITTED_ARTIFACT_IDENTITY_REJECTED")

    restoration = documents["restoration"]
    preflight = documents["preflight"]
    authorization = documents["authorization"]
    accounting = documents["accounting"]
    readiness = documents["readiness"]
    bundle = documents["bundle"]
    receipt = documents["receipt"]

    required_authorization = {
        "authorization_scope": AUTHORIZATION_SCOPE,
        "custody_preflight_hash": PREFLIGHT_HASH,
        "detector_id": DETECTOR_ID,
        "detector_family": DETECTOR_FAMILY,
        "design_hash": DESIGN_HASH,
        "feature_count": FEATURE_COUNT,
        "feature_set_hash": FEATURE_SET_HASH,
        "feature_order_hash": FEATURE_ORDER_HASH,
        "preprocessing_content_hash": PREPROCESSING_HASH,
        "model_content_hash": MODEL_HASH,
        "threshold_content_hash": THRESHOLD_HASH,
        "selected_k": SELECTED_K,
        "residual_dimensions": RESIDUAL_DIMENSIONS,
        "threshold_alpha": THRESHOLD_ALPHA,
        "threshold_q_index": THRESHOLD_Q_INDEX,
        "threshold_comparison_operator": THRESHOLD_COMPARATOR,
        "python_version": PYTHON_VERSION,
        "python_runtime_identity": PYTHON_RUNTIME_IDENTITY,
        "numpy_version": NUMPY_VERSION,
        "numeric_backend": NUMERIC_BACKEND,
        "dataset_manifest_id": DATASET_MANIFEST_ID,
        "inner_split_id": INNER_SPLIT_ID,
        "test1_feature_sha256": TEST1_FEATURE_SHA256,
        "test1_label_sha256": TEST1_LABEL_SHA256,
        "expected_test1_rows": EXPECTED_ROW_COUNT,
        "d0_inner_execution_authorized": True,
        "d0_detector_prediction_authorized": True,
        "test1_feature_scientific_parsing_authorized": True,
        "label_metric_evaluation_authorized": True,
        "label_access_before_prediction_freeze_authorized": False,
        "d1_execution_authorized": False,
        "d1_rerun_authorized": False,
        "d2_authorized": False,
        "fusion_authorized": False,
        "outer_authorized": False,
        "test2_authorized": False,
        "retraining_authorized": False,
        "recalibration_authorized": False,
        "feature_change_authorized": False,
        "model_change_authorized": False,
        "threshold_change_authorized": False,
        "d0_executed": False,
    }
    if any(authorization.get(key) != value for key, value in required_authorization.items()):
        _fail("COMMITTED_AUTHORIZATION_SEMANTICS_REJECTED")
    required_preflight = {
        "authorization_scope": AUTHORIZATION_SCOPE,
        "custody_mode": "REAL_CUSTODY_PREFLIGHT",
        "design_hash": DESIGN_HASH,
        "preprocessing_expected_hash": PREPROCESSING_HASH,
        "preprocessing_observed_match": True,
        "model_expected_hash": MODEL_HASH,
        "model_observed_match": True,
        "threshold_expected_hash": THRESHOLD_HASH,
        "threshold_observed_match": True,
        "test1_feature_expected_hash": TEST1_FEATURE_SHA256,
        "test1_feature_observed_match": True,
        "test1_label_expected_hash": TEST1_LABEL_SHA256,
        "test1_label_observed_match": True,
        "test2_touched": False,
        "scientific_feature_parsing_performed": False,
        "scientific_label_parsing_performed": False,
        "detector_execution_count": 0,
        "metric_computation_count": 0,
        "real_preflight_attempts": 1,
        "real_preflight_retries": 0,
        "private_paths_exposed": 0,
        "private_model_values_exposed": 0,
        "private_threshold_values_exposed": 0,
    }
    if any(preflight.get(key) != value for key, value in required_preflight.items()):
        _fail("COMMITTED_PREFLIGHT_SEMANTICS_REJECTED")
    if (
        restoration.get("artifact_hash") != RESTORATION_REPORT_HASH
        or restoration.get("test1_feature_hash_match") is not True
        or restoration.get("test1_label_hash_match") is not True
        or restoration.get("scientific_feature_parses") != 0
        or restoration.get("scientific_label_parses") != 0
        or restoration.get("test2_file_opens") != 0
        or restoration.get("private_paths_exposed") != 0
        or restoration.get("private_numeric_values_exposed") != 0
    ):
        _fail("COMMITTED_RESTORATION_SEMANTICS_REJECTED")
    if (
        accounting.get("authorization_issuances") != 1
        or accounting.get("authorization_preflight_attempts_new_process") != 1
        or accounting.get("authorization_preflight_retries") != 0
        or accounting.get("test1_feature_scientific_parses") != 0
        or accounting.get("test1_label_scientific_parses") != 0
        or accounting.get("detector_executions") != 0
        or accounting.get("metric_computations") != 0
        or accounting.get("d1_executions") != 0
        or accounting.get("d2_executions") != 0
        or accounting.get("outer_executions") != 0
        or accounting.get("test2_accesses") != 0
    ):
        _fail("COMMITTED_AUTHORIZATION_ACCOUNTING_REJECTED")
    if (
        readiness.get("authorization_hash") != AUTHORIZATION_HASH
        or readiness.get("preflight_hash") != PREFLIGHT_HASH
        or readiness.get("d0_authorized") is not True
        or readiness.get("d0_executed") is not False
        or readiness.get("d2_authorized") is not False
        or readiness.get("outer_authorized") is not False
        or readiness.get("label_before_prediction_authorized") is not False
        or readiness.get("test2_accesses") != 0
        or readiness.get("exact_next_task") != TASK_ID
    ):
        _fail("COMMITTED_AUTHORIZATION_READINESS_REJECTED")
    if (
        bundle.get("authorization_hash") != AUTHORIZATION_HASH
        or bundle.get("preflight_hash") != PREFLIGHT_HASH
        or bundle.get("accounting_hash") != AUTHORIZATION_ACCOUNTING_HASH
        or bundle.get("readiness_hash") != AUTHORIZATION_READINESS_HASH
        or bundle.get("restoration_report_hash") != RESTORATION_REPORT_HASH
        or bundle.get("model_hash") != MODEL_HASH
        or bundle.get("threshold_hash") != THRESHOLD_HASH
        or bundle.get("test2_accesses") != 0
    ):
        _fail("COMMITTED_AUTHORIZATION_BUNDLE_REJECTED")
    if (
        receipt.get("authorization_hash") != AUTHORIZATION_HASH
        or receipt.get("preflight_hash") != PREFLIGHT_HASH
        or receipt.get("accounting_hash") != AUTHORIZATION_ACCOUNTING_HASH
        or receipt.get("readiness_hash") != AUTHORIZATION_READINESS_HASH
        or receipt.get("bundle_hash") != AUTHORIZATION_BUNDLE_HASH
        or receipt.get("restoration_report_hash") != RESTORATION_REPORT_HASH
        or receipt.get("d0_authorized") is not True
        or receipt.get("d0_executed") is not False
        or receipt.get("d2_authorized") is not False
        or receipt.get("outer_authorized") is not False
        or receipt.get("test2_accesses") != 0
        or receipt.get("exact_next_task") != TASK_ID
    ):
        _fail("COMMITTED_AUTHORIZATION_RECEIPT_REJECTED")


@dataclass(frozen=True)
class CommittedD0InnerExecutionGrantV1:
    execution_version: str
    authorization_freeze_commit: str
    restoration_report_hash: str
    preflight_hash: str
    authorization_hash: str
    authorization_accounting_hash: str
    authorization_readiness_hash: str
    authorization_bundle_hash: str
    authorization_receipt_hash: str
    authorization_scope: str
    detector_id: str
    design_hash: str
    preprocessing_hash: str
    model_hash: str
    threshold_hash: str
    feature_order_hash: str
    d0_inner_execution_authorized: bool
    d0_detector_prediction_authorized: bool
    test1_feature_scientific_parsing_authorized: bool
    label_metric_evaluation_authorized: bool
    label_access_before_prediction_freeze_authorized: bool
    d1_execution_authorized: bool
    d1_rerun_authorized: bool
    d2_authorized: bool
    fusion_authorized: bool
    outer_authorized: bool
    test2_authorized: bool
    retraining_authorized: bool
    recalibration_authorized: bool
    feature_change_authorized: bool
    model_change_authorized: bool
    threshold_change_authorized: bool
    grant_hash: str

    def _payload(self) -> dict[str, Any]:
        return {key: value for key, value in self.__dict__.items() if key != "grant_hash"}

    def to_public_dict(self) -> dict[str, Any]:
        return {**self._payload(), "artifact_hash": self.grant_hash}


def _expected_committed_grant_v1() -> CommittedD0InnerExecutionGrantV1:
    provisional = CommittedD0InnerExecutionGrantV1(
        D0_INNER_EXECUTION_VERSION,
        AUTHORIZATION_FREEZE_COMMIT,
        RESTORATION_REPORT_HASH,
        PREFLIGHT_HASH,
        AUTHORIZATION_HASH,
        AUTHORIZATION_ACCOUNTING_HASH,
        AUTHORIZATION_READINESS_HASH,
        AUTHORIZATION_BUNDLE_HASH,
        AUTHORIZATION_RECEIPT_HASH,
        AUTHORIZATION_SCOPE,
        DETECTOR_ID,
        DESIGN_HASH,
        PREPROCESSING_HASH,
        MODEL_HASH,
        THRESHOLD_HASH,
        FEATURE_ORDER_HASH,
        True,
        True,
        True,
        True,
        False,
        False,
        False,
        False,
        False,
        False,
        False,
        False,
        False,
        False,
        False,
        False,
        "",
    )
    return replace(provisional, grant_hash=stable_hash_v1(provisional._payload()))


_ISSUED_GRANTS: dict[
    int, tuple[weakref.ReferenceType[CommittedD0InnerExecutionGrantV1], str]
] = {}


def issue_committed_d0_inner_execution_grant_v1() -> CommittedD0InnerExecutionGrantV1:
    """Replay all exact Commit-B artifacts and issue one process-local grant."""

    documents = _load_committed_artifact_set_v1()
    _validate_committed_artifact_set_v1(documents)
    grant = _expected_committed_grant_v1()
    object_id = id(grant)

    def cleanup(dead: object, *, key: int = object_id) -> None:
        issued = _ISSUED_GRANTS.get(key)
        if issued is not None and issued[0] is dead:
            _ISSUED_GRANTS.pop(key, None)

    _ISSUED_GRANTS[object_id] = (weakref.ref(grant, cleanup), grant.grant_hash)
    return grant


def validate_committed_d0_inner_execution_grant_v1(
    grant: CommittedD0InnerExecutionGrantV1,
) -> str:
    if type(grant) is not CommittedD0InnerExecutionGrantV1:
        _fail("COMMITTED_GRANT_TYPE_REJECTED")
    issued = _ISSUED_GRANTS.get(id(grant))
    if issued is None or issued[0]() is not grant or issued[1] != grant.grant_hash:
        _fail("COMMITTED_GRANT_FACTORY_CUSTODY_REJECTED")
    documents = _load_committed_artifact_set_v1()
    _validate_committed_artifact_set_v1(documents)
    expected = _expected_committed_grant_v1()
    if grant != expected or stable_hash_v1(grant._payload()) != grant.grant_hash:
        _fail("COMMITTED_GRANT_REPLAY_REJECTED")
    return grant.grant_hash


class _D0InnerExecutionTokenV1:
    __slots__ = ("grant", "token_hash", "__weakref__")

    def __init__(self, grant: CommittedD0InnerExecutionGrantV1, token_hash: str) -> None:
        self.grant = grant
        self.token_hash = token_hash

    def __repr__(self) -> str:
        return "<_D0InnerExecutionTokenV1 validated=True>"


_ISSUED_TOKENS: dict[
    int, tuple[weakref.ReferenceType[_D0InnerExecutionTokenV1], str, int]
] = {}
_REAL_TOKEN_ISSUED = False


def _issue_execution_token_v1(
    grant: CommittedD0InnerExecutionGrantV1,
) -> _D0InnerExecutionTokenV1:
    global _REAL_TOKEN_ISSUED
    validate_committed_d0_inner_execution_grant_v1(grant)
    if _REAL_TOKEN_ISSUED:
        _fail("EXECUTION_TOKEN_ALREADY_ISSUED")
    token_hash = stable_hash_v1(
        {
            "artifact_type": "task039e3_r2r_d0_inner_execution_token_v1",
            "grant_hash": grant.grant_hash,
            "implementation_identity": D0_INNER_EXECUTION_IMPLEMENTATION_IDENTITY,
            "single_use": True,
        }
    )
    token = _D0InnerExecutionTokenV1(grant, token_hash)
    object_id = id(token)

    def cleanup(dead: object, *, key: int = object_id) -> None:
        issued = _ISSUED_TOKENS.get(key)
        if issued is not None and issued[0] is dead:
            _ISSUED_TOKENS.pop(key, None)

    _ISSUED_TOKENS[object_id] = (weakref.ref(token, cleanup), token_hash, id(grant))
    _REAL_TOKEN_ISSUED = True
    return token


def _validate_execution_token_v1(token: _D0InnerExecutionTokenV1) -> str:
    if type(token) is not _D0InnerExecutionTokenV1:
        _fail("EXECUTION_TOKEN_TYPE_REJECTED")
    issued = _ISSUED_TOKENS.get(id(token))
    if (
        issued is None
        or issued[0]() is not token
        or issued[1] != token.token_hash
        or issued[2] != id(token.grant)
    ):
        _fail("EXECUTION_TOKEN_FACTORY_CUSTODY_REJECTED")
    validate_committed_d0_inner_execution_grant_v1(token.grant)
    return token.token_hash


class D0ExecutionStateV1(str, Enum):
    NOT_STARTED = "NOT_STARTED"
    GRANT_REPLAYED = "GRANT_REPLAYED"
    PRIVATE_AUTHORITY_VALIDATED = "PRIVATE_AUTHORITY_VALIDATED"
    FEATURE_PARSED = "FEATURE_PARSED"
    SCORES_COMPUTED = "SCORES_COMPUTED"
    PREDICTION_FROZEN = "PREDICTION_FROZEN"
    LABEL_PARSED = "LABEL_PARSED"
    METRICS_COMPUTED = "METRICS_COMPUTED"
    RESULT_FROZEN = "RESULT_FROZEN"


class D0ExecutionStateMachineV1:
    """Explicit prediction-before-label state gate."""

    def __init__(self) -> None:
        self.state = D0ExecutionStateV1.NOT_STARTED

    def transition(self, expected: D0ExecutionStateV1, target: D0ExecutionStateV1) -> None:
        if self.state is not expected:
            _fail("EXECUTION_STATE_TRANSITION_REJECTED")
        self.state = target

    def require_label_access(self) -> None:
        if self.state is not D0ExecutionStateV1.PREDICTION_FROZEN:
            _fail("LABEL_ACCESS_BEFORE_PREDICTION_FREEZE_REJECTED")


def _np_v1() -> Any:
    try:
        import numpy as np
    except BaseException:
        _fail("NUMPY_BACKEND_UNAVAILABLE")
    return np


def validate_numeric_backend_v1() -> tuple[str, str]:
    np = _np_v1()
    if (
        platform.python_implementation() != "CPython"
        or platform.python_version() != PYTHON_VERSION
        or str(np.__version__) != NUMPY_VERSION
    ):
        _fail("NUMERIC_BACKEND_MISMATCH")
    return platform.python_version(), str(np.__version__)


@dataclass(frozen=True, repr=False)
class FrozenD0PrivateModelBundleV1:
    execution_mode: str
    detector_id: str
    design_hash: str
    preprocessing_hash: str
    model_hash: str
    threshold_hash: str
    feature_order_hash: str
    selected_k: int
    residual_dimensions: int
    python_version: str
    numpy_version: str
    bundle_hash: str
    _means: Any = field(repr=False, compare=False)
    _scales: Any = field(repr=False, compare=False)
    _retained_loadings: Any = field(repr=False, compare=False)
    _threshold: float = field(repr=False, compare=False)
    _mean_value_hash: str = field(repr=False, compare=False)
    _scale_value_hash: str = field(repr=False, compare=False)
    _loading_value_hash: str = field(repr=False, compare=False)
    _threshold_value_hash: str = field(repr=False, compare=False)

    def __repr__(self) -> str:
        return "<FrozenD0PrivateModelBundleV1 validated=True values=REDACTED>"

    def __reduce__(self) -> object:
        _fail("PRIVATE_MODEL_SERIALIZATION_PROHIBITED")


_ISSUED_PRIVATE_BUNDLES: dict[
    int, tuple[weakref.ReferenceType[FrozenD0PrivateModelBundleV1], str]
] = {}

HAI_DATA_ROOT_BINDING = "HAI_DATA_ROOT"
PREPROCESSING_BINDING = "TASK039E3_D0_PCA_SPE_PREPROCESSING_V1"
MODEL_BINDING = "TASK039E3_D0_PCA_SPE_MODEL_V1"
THRESHOLD_BINDING = "TASK039E3_D0_PCA_SPE_THRESHOLD_V1"
_APPROVED_BINDING_KEYS = frozenset(
    {
        HAI_DATA_ROOT_BINDING,
        PREPROCESSING_BINDING,
        MODEL_BINDING,
        THRESHOLD_BINDING,
        "TASK039E3_UTILITY_NORMAL_ONLY_PRIVATE_REGISTRY_V1",
        "TASK039E3_UTILITY_NORMAL_ONLY_PRIVATE_LOCATOR_V1",
        "TASK039E3_UTILITY_SOURCE_CENSUS_SUPPLEMENT_PRIVATE_REGISTRY_V1",
        "TASK039E3_UTILITY_SOURCE_CENSUS_SUPPLEMENT_PRIVATE_LOCATOR_V1",
    }
)
_BINDING_PATTERN = re.compile(r"^([A-Z0-9_]+)='((?:[^']|'\"'\"')*)'$")


def _load_local_bindings_v1() -> dict[str, str]:
    path = _repository_root_v1() / ".env.custody.local"
    try:
        if path.is_symlink() or not path.is_file():
            _fail("PRIVATE_BINDINGS_UNAVAILABLE")
        values: dict[str, str] = {}
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line:
                continue
            match = _BINDING_PATTERN.fullmatch(line)
            if (
                match is None
                or match.group(1) not in _APPROVED_BINDING_KEYS
                or match.group(1) in values
            ):
                _fail("PRIVATE_BINDINGS_REJECTED")
            values[match.group(1)] = match.group(2).replace("'\"'\"'", "'")
        required = {
            HAI_DATA_ROOT_BINDING,
            PREPROCESSING_BINDING,
            MODEL_BINDING,
            THRESHOLD_BINDING,
        }
        if not required.issubset(values):
            _fail("PRIVATE_BINDING_MISSING")
        return values
    except InnerD0ExecutionV1Error:
        raise
    except BaseException:
        _fail("PRIVATE_BINDINGS_REJECTED")


def _private_regular_file_v1(value: str) -> Path:
    try:
        path = Path(value)
        resolved = path.resolve(strict=True)
        repository = _repository_root_v1().resolve()
        if (
            not path.is_absolute()
            or path.is_symlink()
            or not path.is_file()
            or resolved == repository
            or repository in resolved.parents
        ):
            _fail("PRIVATE_FILE_CUSTODY_REJECTED")
        return path
    except InnerD0ExecutionV1Error:
        raise
    except BaseException:
        _fail("PRIVATE_FILE_CUSTODY_REJECTED")


def _private_hai_root_v1(value: str) -> Path:
    try:
        path = Path(value)
        resolved = path.resolve(strict=True)
        repository = _repository_root_v1().resolve()
        if (
            not path.is_absolute()
            or path.is_symlink()
            or not path.is_dir()
            or resolved == repository
            or repository in resolved.parents
        ):
            _fail("PRIVATE_HAI_CUSTODY_REJECTED")
        return path
    except InnerD0ExecutionV1Error:
        raise
    except BaseException:
        _fail("PRIVATE_HAI_CUSTODY_REJECTED")


def _load_private_json_once_v1(value: str, expected_hash: str) -> dict[str, Any]:
    path = _private_regular_file_v1(value)
    try:
        document = _strict_json_object_v1(path.read_bytes())
        if _canonical_self_hash_v1(document) != expected_hash:
            _fail("PRIVATE_ARTIFACT_IDENTITY_REJECTED")
        return document
    except InnerD0ExecutionV1Error:
        raise
    except BaseException:
        _fail("PRIVATE_ARTIFACT_READ_REJECTED")


def _canonical_float_hex_v1(value: object) -> bool:
    if type(value) is not str:
        return False
    try:
        decoded = float.fromhex(value)
        return math.isfinite(decoded) and decoded.hex() == value
    except BaseException:
        return False


def _validate_and_decode_private_documents_v1(
    preprocessing: Mapping[str, Any],
    model: Mapping[str, Any],
    threshold: Mapping[str, Any],
) -> tuple[Any, Any, Any, float]:
    np = _np_v1()
    if (
        type(preprocessing) is not dict
        or _canonical_self_hash_v1(preprocessing) != PREPROCESSING_HASH
        or set(preprocessing)
        != {
            "artifact_type",
            "schema_version",
            "detector_id",
            "design_hash",
            "feature_order_hash",
            "train1_sha256",
            "train2_sha256",
            "combined_row_count",
            "python_version",
            "numpy_version",
            "means_float_hex",
            "scales_float_hex",
            "artifact_hash",
        }
        or preprocessing.get("artifact_type")
        != "task039e3_r2r_d0_preprocessing_artifact_v1"
        or preprocessing.get("detector_id") != DETECTOR_ID
        or preprocessing.get("design_hash") != DESIGN_HASH
        or preprocessing.get("feature_order_hash") != FEATURE_ORDER_HASH
        or preprocessing.get("train1_sha256") != TRAIN1_SHA256
        or preprocessing.get("train2_sha256") != TRAIN2_SHA256
        or preprocessing.get("combined_row_count") != COMBINED_FIT_ROWS
        or preprocessing.get("python_version") != PYTHON_VERSION
        or preprocessing.get("numpy_version") != NUMPY_VERSION
    ):
        _fail("PRIVATE_PREPROCESSING_REJECTED")
    means_hex = preprocessing.get("means_float_hex")
    scales_hex = preprocessing.get("scales_float_hex")
    if (
        type(means_hex) is not list
        or type(scales_hex) is not list
        or len(means_hex) != FEATURE_COUNT
        or len(scales_hex) != FEATURE_COUNT
        or not all(_canonical_float_hex_v1(value) for value in (*means_hex, *scales_hex))
    ):
        _fail("PRIVATE_PREPROCESSING_REPRESENTATION_REJECTED")

    if (
        type(model) is not dict
        or _canonical_self_hash_v1(model) != MODEL_HASH
        or set(model)
        != {
            "artifact_type",
            "schema_version",
            "detector_id",
            "design_hash",
            "preprocessing_hash",
            "feature_order_hash",
            "train1_sha256",
            "train2_sha256",
            "fit_row_count",
            "python_version",
            "numpy_version",
            "selected_k",
            "explained_variance_target",
            "eigenvalues_float_hex",
            "retained_loadings_float_hex",
            "labels_used",
            "test_accessed",
            "artifact_hash",
        }
        or model.get("artifact_type") != "task039e3_r2r_d0_pca_model_artifact_v1"
        or model.get("detector_id") != DETECTOR_ID
        or model.get("design_hash") != DESIGN_HASH
        or model.get("preprocessing_hash") != PREPROCESSING_HASH
        or model.get("feature_order_hash") != FEATURE_ORDER_HASH
        or model.get("train1_sha256") != TRAIN1_SHA256
        or model.get("train2_sha256") != TRAIN2_SHA256
        or model.get("fit_row_count") != COMBINED_FIT_ROWS
        or model.get("python_version") != PYTHON_VERSION
        or model.get("numpy_version") != NUMPY_VERSION
        or model.get("selected_k") != SELECTED_K
        or model.get("explained_variance_target") != PCA_EXPLAINED_VARIANCE_TARGET
        or model.get("labels_used") is not False
        or model.get("test_accessed") is not False
    ):
        _fail("PRIVATE_MODEL_REJECTED")
    eigenvalues = model.get("eigenvalues_float_hex")
    loadings_hex = model.get("retained_loadings_float_hex")
    if (
        type(eigenvalues) is not list
        or len(eigenvalues) != FEATURE_COUNT
        or not all(_canonical_float_hex_v1(value) for value in eigenvalues)
        or type(loadings_hex) is not list
        or len(loadings_hex) != FEATURE_COUNT
        or any(type(row) is not list or len(row) != SELECTED_K for row in loadings_hex)
        or not all(_canonical_float_hex_v1(value) for row in loadings_hex for value in row)
    ):
        _fail("PRIVATE_MODEL_REPRESENTATION_REJECTED")

    if (
        type(threshold) is not dict
        or _canonical_self_hash_v1(threshold) != THRESHOLD_HASH
        or set(threshold)
        != {
            "artifact_type",
            "schema_version",
            "detector_id",
            "design_hash",
            "model_hash",
            "train3_sha256",
            "calibration_row_count",
            "alpha",
            "upper_quantile",
            "q_index",
            "order_statistic_policy",
            "threshold_float_hex",
            "comparison_operator",
            "labels_used",
            "test_used",
            "artifact_hash",
        }
        or threshold.get("artifact_type") != "task039e3_r2r_d0_threshold_artifact_v1"
        or threshold.get("detector_id") != DETECTOR_ID
        or threshold.get("design_hash") != DESIGN_HASH
        or threshold.get("model_hash") != MODEL_HASH
        or threshold.get("train3_sha256") != TRAIN3_SHA256
        or threshold.get("calibration_row_count") != TRAIN3_ROWS
        or threshold.get("alpha") != THRESHOLD_ALPHA
        or threshold.get("upper_quantile") != 0.999
        or threshold.get("q_index") != THRESHOLD_Q_INDEX
        or threshold.get("order_statistic_policy")
        != "ceil(0.999*n)-1_zero_based_after_ascending_sort_no_interpolation"
        or threshold.get("comparison_operator") != THRESHOLD_COMPARATOR
        or threshold.get("labels_used") is not False
        or threshold.get("test_used") is not False
        or not _canonical_float_hex_v1(threshold.get("threshold_float_hex"))
    ):
        _fail("PRIVATE_THRESHOLD_REJECTED")

    means = np.asarray([float.fromhex(value) for value in means_hex], dtype=np.float64)
    scales = np.asarray([float.fromhex(value) for value in scales_hex], dtype=np.float64)
    loadings = np.asarray(
        [[float.fromhex(value) for value in row] for row in loadings_hex],
        dtype=np.float64,
    )
    threshold_value = float.fromhex(threshold["threshold_float_hex"])
    if (
        means.shape != (FEATURE_COUNT,)
        or scales.shape != (FEATURE_COUNT,)
        or loadings.shape != (FEATURE_COUNT, SELECTED_K)
        or means.dtype != np.float64
        or scales.dtype != np.float64
        or loadings.dtype != np.float64
        or not bool(np.isfinite(means).all())
        or not bool(np.isfinite(scales).all())
        or not bool(np.isfinite(loadings).all())
        or bool((scales <= 0.0).any())
        or not math.isfinite(threshold_value)
    ):
        _fail("PRIVATE_NUMERIC_REPRESENTATION_REJECTED")
    return means, scales, loadings, threshold_value


def _private_value_hash_v1(kind: str, values: Any) -> str:
    np = _np_v1()
    array = np.asarray(values, dtype=np.float64)
    return stable_hash_v1(
        {
            "artifact_type": f"task039e3_r2r_private_{kind}_float_hex_v1",
            "shape": list(array.shape),
            "values_float_hex": [float(value).hex() for value in array.ravel(order="C")],
        }
    )


def _load_frozen_private_model_bundle_v1(
    token: _D0InnerExecutionTokenV1,
    bindings: Mapping[str, str],
) -> FrozenD0PrivateModelBundleV1:
    _validate_execution_token_v1(token)
    preprocessing = _load_private_json_once_v1(
        bindings[PREPROCESSING_BINDING], PREPROCESSING_HASH
    )
    model = _load_private_json_once_v1(bindings[MODEL_BINDING], MODEL_HASH)
    threshold = _load_private_json_once_v1(bindings[THRESHOLD_BINDING], THRESHOLD_HASH)
    means, scales, loadings, threshold_value = _validate_and_decode_private_documents_v1(
        preprocessing, model, threshold
    )
    means.setflags(write=False)
    scales.setflags(write=False)
    loadings.setflags(write=False)
    public_payload = {
        "artifact_type": "task039e3_r2r_frozen_d0_private_model_bundle_v1",
        "execution_mode": EXECUTION_MODE,
        "detector_id": DETECTOR_ID,
        "design_hash": DESIGN_HASH,
        "preprocessing_hash": PREPROCESSING_HASH,
        "model_hash": MODEL_HASH,
        "threshold_hash": THRESHOLD_HASH,
        "feature_order_hash": FEATURE_ORDER_HASH,
        "selected_k": SELECTED_K,
        "residual_dimensions": RESIDUAL_DIMENSIONS,
        "python_version": PYTHON_VERSION,
        "numpy_version": NUMPY_VERSION,
        "private_values_exposed": 0,
    }
    bundle = FrozenD0PrivateModelBundleV1(
        EXECUTION_MODE,
        DETECTOR_ID,
        DESIGN_HASH,
        PREPROCESSING_HASH,
        MODEL_HASH,
        THRESHOLD_HASH,
        FEATURE_ORDER_HASH,
        SELECTED_K,
        RESIDUAL_DIMENSIONS,
        PYTHON_VERSION,
        NUMPY_VERSION,
        stable_hash_v1(public_payload),
        means,
        scales,
        loadings,
        threshold_value,
        _private_value_hash_v1("preprocessing_mean", means),
        _private_value_hash_v1("preprocessing_scale", scales),
        _private_value_hash_v1("retained_loadings", loadings),
        stable_hash_v1(
            {
                "artifact_type": "task039e3_r2r_private_threshold_float_hex_v1",
                "threshold_float_hex": threshold_value.hex(),
            }
        ),
    )
    object_id = id(bundle)

    def cleanup(dead: object, *, key: int = object_id) -> None:
        issued = _ISSUED_PRIVATE_BUNDLES.get(key)
        if issued is not None and issued[0] is dead:
            _ISSUED_PRIVATE_BUNDLES.pop(key, None)

    _ISSUED_PRIVATE_BUNDLES[object_id] = (
        weakref.ref(bundle, cleanup),
        bundle.bundle_hash,
    )
    validate_frozen_d0_private_model_bundle_v1(bundle)
    return bundle


def validate_frozen_d0_private_model_bundle_v1(
    bundle: FrozenD0PrivateModelBundleV1,
) -> str:
    if type(bundle) is not FrozenD0PrivateModelBundleV1:
        _fail("PRIVATE_MODEL_BUNDLE_TYPE_REJECTED")
    issued = _ISSUED_PRIVATE_BUNDLES.get(id(bundle))
    if issued is None or issued[0]() is not bundle or issued[1] != bundle.bundle_hash:
        _fail("PRIVATE_MODEL_BUNDLE_FACTORY_CUSTODY_REJECTED")
    if (
        bundle.execution_mode != EXECUTION_MODE
        or bundle.detector_id != DETECTOR_ID
        or bundle.design_hash != DESIGN_HASH
        or bundle.preprocessing_hash != PREPROCESSING_HASH
        or bundle.model_hash != MODEL_HASH
        or bundle.threshold_hash != THRESHOLD_HASH
        or bundle.feature_order_hash != FEATURE_ORDER_HASH
        or bundle.selected_k != SELECTED_K
        or bundle.residual_dimensions != RESIDUAL_DIMENSIONS
        or bundle.python_version != PYTHON_VERSION
        or bundle.numpy_version != NUMPY_VERSION
        or bundle._mean_value_hash != _private_value_hash_v1("preprocessing_mean", bundle._means)
        or bundle._scale_value_hash != _private_value_hash_v1("preprocessing_scale", bundle._scales)
        or bundle._loading_value_hash
        != _private_value_hash_v1("retained_loadings", bundle._retained_loadings)
        or bundle._threshold_value_hash
        != stable_hash_v1(
            {
                "artifact_type": "task039e3_r2r_private_threshold_float_hex_v1",
                "threshold_float_hex": bundle._threshold.hex(),
            }
        )
    ):
        _fail("PRIVATE_MODEL_BUNDLE_REPLAY_REJECTED")
    return bundle.bundle_hash


@dataclass(frozen=True, repr=False)
class RealD0FeatureFrameV1:
    execution_mode: str
    dataset_manifest_id: str
    split_id: str
    source_file_identity: str
    source_file_sha256: str
    feature_set_hash: str
    feature_order_hash: str
    ordered_features: tuple[str, ...]
    row_count: int
    dtype: str
    frame_hash: str
    _matrix: Any = field(repr=False, compare=False)
    _timestamps: tuple[str, ...] = field(repr=False, compare=False)

    def __repr__(self) -> str:
        return "<RealD0FeatureFrameV1 validated=True values=REDACTED>"

    def __reduce__(self) -> object:
        _fail("REAL_FEATURE_FRAME_SERIALIZATION_PROHIBITED")


_ISSUED_FEATURE_FRAMES: dict[
    int, tuple[weakref.ReferenceType[RealD0FeatureFrameV1], str]
] = {}


def _feature_frame_payload_v1(frame: RealD0FeatureFrameV1) -> dict[str, Any]:
    return {
        "artifact_type": "task039e3_r2r_real_d0_feature_frame_v1",
        "execution_mode": frame.execution_mode,
        "dataset_manifest_id": frame.dataset_manifest_id,
        "split_id": frame.split_id,
        "source_file_identity": frame.source_file_identity,
        "source_file_sha256": frame.source_file_sha256,
        "feature_set_hash": frame.feature_set_hash,
        "feature_order_hash": frame.feature_order_hash,
        "ordered_features": list(frame.ordered_features),
        "row_count": frame.row_count,
        "dtype": frame.dtype,
        "private_feature_values_exposed": 0,
    }


def _issue_feature_frame_v1(
    matrix: Any, timestamps: tuple[str, ...]
) -> RealD0FeatureFrameV1:
    provisional = RealD0FeatureFrameV1(
        EXECUTION_MODE,
        DATASET_MANIFEST_ID,
        INNER_SPLIT_ID,
        TEST1_FEATURE_FILENAME,
        TEST1_FEATURE_SHA256,
        FEATURE_SET_HASH,
        FEATURE_ORDER_HASH,
        design_v1.P1_FEATURE_ORDER,
        EXPECTED_ROW_COUNT,
        SCIENTIFIC_FLOAT_DTYPE,
        "",
        matrix,
        timestamps,
    )
    frame = replace(
        provisional, frame_hash=stable_hash_v1(_feature_frame_payload_v1(provisional))
    )
    object_id = id(frame)

    def cleanup(dead: object, *, key: int = object_id) -> None:
        issued = _ISSUED_FEATURE_FRAMES.get(key)
        if issued is not None and issued[0] is dead:
            _ISSUED_FEATURE_FRAMES.pop(key, None)

    _ISSUED_FEATURE_FRAMES[object_id] = (weakref.ref(frame, cleanup), frame.frame_hash)
    validate_real_d0_feature_frame_v1(frame)
    return frame


def validate_real_d0_feature_frame_v1(frame: RealD0FeatureFrameV1) -> str:
    np = _np_v1()
    if type(frame) is not RealD0FeatureFrameV1:
        _fail("REAL_FEATURE_FRAME_TYPE_REJECTED")
    issued = _ISSUED_FEATURE_FRAMES.get(id(frame))
    if issued is None or issued[0]() is not frame or issued[1] != frame.frame_hash:
        _fail("REAL_FEATURE_FRAME_FACTORY_CUSTODY_REJECTED")
    if (
        frame.execution_mode != EXECUTION_MODE
        or frame.dataset_manifest_id != DATASET_MANIFEST_ID
        or frame.split_id != INNER_SPLIT_ID
        or frame.source_file_identity != TEST1_FEATURE_FILENAME
        or frame.source_file_sha256 != TEST1_FEATURE_SHA256
        or frame.feature_set_hash != FEATURE_SET_HASH
        or frame.feature_order_hash != FEATURE_ORDER_HASH
        or frame.ordered_features != design_v1.P1_FEATURE_ORDER
        or frame.row_count != EXPECTED_ROW_COUNT
        or frame.dtype != SCIENTIFIC_FLOAT_DTYPE
        or type(frame._matrix) is not np.ndarray
        or frame._matrix.shape != (EXPECTED_ROW_COUNT, FEATURE_COUNT)
        or frame._matrix.dtype != np.float64
        or not bool(np.isfinite(frame._matrix).all())
        or len(frame._timestamps) != EXPECTED_ROW_COUNT
        or frame.frame_hash != stable_hash_v1(_feature_frame_payload_v1(frame))
    ):
        _fail("REAL_FEATURE_FRAME_REPLAY_REJECTED")
    return frame.frame_hash


def validate_test1_feature_raw_identity_v1(observed_hash: str, observed_size: int) -> None:
    if observed_hash != TEST1_FEATURE_SHA256 or observed_size != TEST1_FEATURE_BYTE_SIZE:
        _fail("TEST1_FEATURE_RAW_IDENTITY_REJECTED")


def _raw_sha256_once_v1(path: Path, expected_size: int, failure_code: str) -> str:
    try:
        if path.is_symlink() or not path.is_file() or path.stat().st_size != expected_size:
            _fail(failure_code)
        digest = sha256()
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()
    except InnerD0ExecutionV1Error:
        raise
    except BaseException:
        _fail(failure_code)


def _parse_test1_feature_frame_once_v1(
    token: _D0InnerExecutionTokenV1, path: Path
) -> RealD0FeatureFrameV1:
    _validate_execution_token_v1(token)
    np = _np_v1()
    matrix = np.empty((EXPECTED_ROW_COUNT, FEATURE_COUNT), dtype=np.float64)
    timestamps: list[str] = []
    try:
        with path.open("r", encoding="utf-8", newline="") as stream:
            reader = csv.reader(stream)
            header = next(reader)
            if len(header) != len(set(header)) or "timestamp" not in header:
                _fail("TEST1_FEATURE_HEADER_REJECTED")
            observed_p1_order = tuple(name for name in header if name.startswith("P1_"))
            if observed_p1_order != design_v1.P1_FEATURE_ORDER:
                _fail("TEST1_FEATURE_ORDER_REJECTED")
            timestamp_index = header.index("timestamp")
            feature_indices = tuple(header.index(name) for name in design_v1.P1_FEATURE_ORDER)
            row_count = 0
            for row_count, row in enumerate(reader, start=1):
                if row_count > EXPECTED_ROW_COUNT or len(row) != len(header):
                    _fail("TEST1_FEATURE_ROW_CLOSURE_REJECTED")
                timestamps.append(row[timestamp_index])
                target = row_count - 1
                for column, source in enumerate(feature_indices):
                    matrix[target, column] = float(row[source])
    except InnerD0ExecutionV1Error:
        raise
    except BaseException:
        _fail("TEST1_FEATURE_PARSE_REJECTED")
    if (
        len(timestamps) != EXPECTED_ROW_COUNT
        or len(set(timestamps)) != EXPECTED_ROW_COUNT
        or matrix.shape != (EXPECTED_ROW_COUNT, FEATURE_COUNT)
        or matrix.dtype != np.float64
        or not bool(np.isfinite(matrix).all())
    ):
        _fail("TEST1_FEATURE_FRAME_REJECTED")
    matrix.setflags(write=False)
    return _issue_feature_frame_v1(matrix, tuple(timestamps))


def compute_spe_float64_v1(
    values: Any,
    mean: Any,
    scale: Any,
    retained_loadings: Any,
) -> Any:
    """Frozen float64 standardize/project/residual/SPE arithmetic."""

    np = _np_v1()
    if (
        type(values) is not np.ndarray
        or values.dtype != np.float64
        or values.ndim != 2
        or values.shape[1] != FEATURE_COUNT
        or type(mean) is not np.ndarray
        or mean.dtype != np.float64
        or mean.shape != (FEATURE_COUNT,)
        or type(scale) is not np.ndarray
        or scale.dtype != np.float64
        or scale.shape != (FEATURE_COUNT,)
        or type(retained_loadings) is not np.ndarray
        or retained_loadings.dtype != np.float64
        or retained_loadings.shape != (FEATURE_COUNT, SELECTED_K)
        or not bool(np.isfinite(values).all())
        or not bool(np.isfinite(mean).all())
        or not bool(np.isfinite(scale).all())
        or not bool(np.isfinite(retained_loadings).all())
        or bool((scale <= 0.0).any())
    ):
        _fail("SPE_NUMERIC_CONTRACT_REJECTED")
    standardized = (values - mean) / scale
    projection = (standardized @ retained_loadings) @ retained_loadings.T
    residual = standardized - projection
    scores = np.sum(residual * residual, axis=1, dtype=np.float64)
    if scores.dtype != np.float64 or not bool(np.isfinite(scores).all()) or bool((scores < 0.0).any()):
        _fail("SPE_RESULT_REJECTED")
    return scores


def strict_alarm_mask_v1(scores: Any, threshold: float) -> Any:
    np = _np_v1()
    if (
        type(scores) is not np.ndarray
        or scores.dtype != np.float64
        or scores.ndim != 1
        or not bool(np.isfinite(scores).all())
        or type(threshold) is not float
        or not math.isfinite(threshold)
    ):
        _fail("STRICT_THRESHOLD_CONTRACT_REJECTED")
    return scores > np.float64(threshold)


def _score_vector_content_v1(scores: Any) -> tuple[list[str], str]:
    np = _np_v1()
    if (
        type(scores) is not np.ndarray
        or scores.dtype != np.float64
        or scores.shape != (EXPECTED_ROW_COUNT,)
        or not bool(np.isfinite(scores).all())
    ):
        _fail("SCORE_VECTOR_CLOSURE_REJECTED")
    values = [float(value).hex() for value in scores]
    content_hash = stable_hash_v1(
        {
            "artifact_type": "task039e3_r2r_d0_test1_score_vector_v1",
            "canonical_representation": "PYTHON_FLOAT_HEX_ROW_ORDER",
            "row_count": EXPECTED_ROW_COUNT,
            "scores_float_hex": values,
        }
    )
    return values, content_hash


def _private_evidence_directory_v1(hai_root: Path) -> Path:
    repository = _repository_root_v1().resolve()
    try:
        directory = hai_root.resolve(strict=True).parent / ".paper_v_20260625_private_evidence"
        if directory == repository or repository in directory.parents:
            _fail("PRIVATE_EVIDENCE_INSIDE_REPOSITORY_REJECTED")
        directory.mkdir(mode=0o700, parents=True, exist_ok=True)
        if directory.is_symlink() or not directory.is_dir():
            _fail("PRIVATE_EVIDENCE_DIRECTORY_REJECTED")
        return directory
    except InnerD0ExecutionV1Error:
        raise
    except BaseException:
        _fail("PRIVATE_EVIDENCE_DIRECTORY_REJECTED")


def _write_private_json_atomic_v1(
    directory: Path, filename: str, document: Mapping[str, Any]
) -> str:
    path = directory / filename
    temporary = directory / f"{filename}.tmp"
    try:
        if path.exists() or path.is_symlink() or temporary.exists() or temporary.is_symlink():
            _fail("PRIVATE_EVIDENCE_ALREADY_EXISTS")
        content = (
            json.dumps(
                document,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=True,
                allow_nan=False,
            )
            + "\n"
        ).encode("utf-8")
        with temporary.open("xb") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        try:
            os.chmod(temporary, 0o600)
        except OSError:
            pass
        os.replace(temporary, path)
        replay = _strict_json_object_v1(path.read_bytes())
        if replay != document or _canonical_self_hash_v1(replay) != document["artifact_hash"]:
            _fail("PRIVATE_EVIDENCE_REPLAY_REJECTED")
        return str(document["artifact_hash"])
    except InnerD0ExecutionV1Error:
        raise
    except BaseException:
        _fail("PRIVATE_EVIDENCE_WRITE_REJECTED")


def _freeze_private_score_evidence_v1(
    hai_root: Path, scores: Any
) -> tuple[str, str]:
    values, content_hash = _score_vector_content_v1(scores)
    payload = {
        "artifact_type": "D0Test1ScoreEvidenceV1",
        "schema_version": SCHEMA_VERSION,
        "authorization_hash": AUTHORIZATION_HASH,
        "design_hash": DESIGN_HASH,
        "preprocessing_hash": PREPROCESSING_HASH,
        "model_hash": MODEL_HASH,
        "threshold_hash": THRESHOLD_HASH,
        "test1_feature_sha256": TEST1_FEATURE_SHA256,
        "feature_order_hash": FEATURE_ORDER_HASH,
        "row_count": EXPECTED_ROW_COUNT,
        "canonical_score_representation": "PYTHON_FLOAT_HEX_ROW_ORDER",
        "scores_float_hex": values,
        "score_vector_content_hash": content_hash,
    }
    document = {**payload, "artifact_hash": stable_hash_v1(payload)}
    evidence_hash = _write_private_json_atomic_v1(
        _private_evidence_directory_v1(hai_root),
        "task039e3_inner_d0_score_evidence_v1.json",
        document,
    )
    return evidence_hash, content_hash


@dataclass(frozen=True)
class ScientificDetectorPredictionRecordV1:
    physical_row_index: int
    alarm_emitted: bool
    detector_decision_identity: str

    def to_public_dict(self) -> dict[str, object]:
        return {
            "physical_row_index": self.physical_row_index,
            "alarm_emitted": self.alarm_emitted,
            "detector_decision_identity": self.detector_decision_identity,
        }


def _decision_identity_v1(index: int, alarm: bool, score_vector_content_hash: str) -> str:
    return stable_hash_v1(
        {
            "artifact_type": "task039e3_r2r_d0_detector_decision_identity_v1",
            "execution_implementation_identity": D0_INNER_EXECUTION_IMPLEMENTATION_IDENTITY,
            "detector_id": DETECTOR_ID,
            "score_vector_content_hash": score_vector_content_hash,
            "physical_row_index": index,
            "alarm_emitted": alarm,
        }
    )


def _validate_prediction_record_closure_v1(
    records: Sequence[ScientificDetectorPredictionRecordV1],
    score_vector_content_hash: str,
    *,
    expected_count: int = EXPECTED_ROW_COUNT,
) -> None:
    if type(records) not in {tuple, list} or len(records) != expected_count:
        _fail("PREDICTION_RECORD_COUNT_REJECTED")
    for expected_index, record in enumerate(records):
        if (
            type(record) is not ScientificDetectorPredictionRecordV1
            or type(record.physical_row_index) is not int
            or record.physical_row_index != expected_index
            or type(record.alarm_emitted) is not bool
            or record.detector_decision_identity
            != _decision_identity_v1(
                expected_index, record.alarm_emitted, score_vector_content_hash
            )
        ):
            _fail("PREDICTION_RECORD_CLOSURE_REJECTED")


@dataclass(frozen=True)
class ScientificDetectorPredictionArtifactV1:
    execution_mode: str
    authorization_hash: str
    execution_version: str
    execution_implementation_identity: str
    execution_implementation_commit: str
    execution_implementation_source_sha256: str
    detector_id: str
    detector_family: str
    design_hash: str
    preprocessing_hash: str
    model_hash: str
    threshold_hash: str
    feature_set_hash: str
    feature_order_hash: str
    test1_feature_sha256: str
    dataset_manifest_id: str
    split_id: str
    row_count: int
    score_vector_content_hash: str
    prediction_records: tuple[ScientificDetectorPredictionRecordV1, ...]
    point_alarm_count: int
    artifact_hash: str

    def to_public_dict(self) -> dict[str, object]:
        payload = _prediction_payload_v1(self)
        return {**payload, "artifact_hash": self.artifact_hash}


_ISSUED_PREDICTIONS: dict[
    int, tuple[weakref.ReferenceType[ScientificDetectorPredictionArtifactV1], str]
] = {}


def _prediction_payload_v1(
    artifact: ScientificDetectorPredictionArtifactV1,
) -> dict[str, object]:
    return {
        "artifact_type": "ScientificDetectorPredictionArtifactV1",
        "schema_version": SCHEMA_VERSION,
        "execution_mode": artifact.execution_mode,
        "authorization_hash": artifact.authorization_hash,
        "execution_version": artifact.execution_version,
        "execution_implementation_identity": artifact.execution_implementation_identity,
        "execution_implementation_commit": artifact.execution_implementation_commit,
        "execution_implementation_source_sha256": artifact.execution_implementation_source_sha256,
        "detector_id": artifact.detector_id,
        "detector_family": artifact.detector_family,
        "design_hash": artifact.design_hash,
        "preprocessing_hash": artifact.preprocessing_hash,
        "model_hash": artifact.model_hash,
        "threshold_hash": artifact.threshold_hash,
        "feature_set_hash": artifact.feature_set_hash,
        "feature_order_hash": artifact.feature_order_hash,
        "test1_feature_sha256": artifact.test1_feature_sha256,
        "dataset_manifest_id": artifact.dataset_manifest_id,
        "split_id": artifact.split_id,
        "row_count": artifact.row_count,
        "unique_row_count": artifact.row_count,
        "score_vector_content_hash": artifact.score_vector_content_hash,
        "prediction_records": [record.to_public_dict() for record in artifact.prediction_records],
        "point_alarm_count": artifact.point_alarm_count,
        "label_blind": True,
        "labels_accessed_before_prediction_freeze": False,
        "private_score_values_exposed": 0,
        "private_threshold_value_exposed": 0,
        "private_paths_exposed": 0,
    }


def _file_commit_custody_v1(relative: str) -> tuple[str, str]:
    path = _repository_root_v1() / relative
    try:
        if path.is_symlink() or not path.is_file():
            _fail("FROZEN_FILE_CUSTODY_REJECTED")
        commit = _git_output_v1(("log", "-1", "--format=%H", "--", relative)).decode(
            "ascii"
        ).strip()
        if re.fullmatch(r"[a-f0-9]{40}", commit) is None:
            _fail("FROZEN_FILE_COMMIT_REJECTED")
        current = path.read_bytes()
        frozen = _git_output_v1(("show", f"{commit}:{relative}"))
        if current != frozen:
            _fail("FROZEN_FILE_BYTES_REJECTED")
        return commit, sha256(current).hexdigest()
    except InnerD0ExecutionV1Error:
        raise
    except BaseException:
        _fail("FROZEN_FILE_CUSTODY_REJECTED")


def _build_scientific_prediction_v1(
    token: _D0InnerExecutionTokenV1,
    alarm_mask: Any,
    score_vector_content_hash: str,
) -> ScientificDetectorPredictionArtifactV1:
    np = _np_v1()
    _validate_execution_token_v1(token)
    if (
        type(alarm_mask) is not np.ndarray
        or alarm_mask.dtype != np.bool_
        or alarm_mask.shape != (EXPECTED_ROW_COUNT,)
    ):
        _fail("PREDICTION_ALARM_MASK_REJECTED")
    _strict_sha256_v1(score_vector_content_hash, "SCORE_VECTOR_HASH_REJECTED")
    records = tuple(
        ScientificDetectorPredictionRecordV1(
            index,
            bool(alarm_mask[index]),
            _decision_identity_v1(index, bool(alarm_mask[index]), score_vector_content_hash),
        )
        for index in range(EXPECTED_ROW_COUNT)
    )
    _validate_prediction_record_closure_v1(records, score_vector_content_hash)
    implementation_commit, implementation_source_sha = _file_commit_custody_v1(
        "src/paperworks/v6/task039e3_r2r_d0_inner_execution_v1.py"
    )
    provisional = ScientificDetectorPredictionArtifactV1(
        EXECUTION_MODE,
        AUTHORIZATION_HASH,
        D0_INNER_EXECUTION_VERSION,
        D0_INNER_EXECUTION_IMPLEMENTATION_IDENTITY,
        implementation_commit,
        implementation_source_sha,
        DETECTOR_ID,
        DETECTOR_FAMILY,
        DESIGN_HASH,
        PREPROCESSING_HASH,
        MODEL_HASH,
        THRESHOLD_HASH,
        FEATURE_SET_HASH,
        FEATURE_ORDER_HASH,
        TEST1_FEATURE_SHA256,
        DATASET_MANIFEST_ID,
        INNER_SPLIT_ID,
        EXPECTED_ROW_COUNT,
        score_vector_content_hash,
        records,
        int(np.count_nonzero(alarm_mask)),
        "",
    )
    artifact = replace(
        provisional, artifact_hash=stable_hash_v1(_prediction_payload_v1(provisional))
    )
    object_id = id(artifact)

    def cleanup(dead: object, *, key: int = object_id) -> None:
        issued = _ISSUED_PREDICTIONS.get(key)
        if issued is not None and issued[0] is dead:
            _ISSUED_PREDICTIONS.pop(key, None)

    _ISSUED_PREDICTIONS[object_id] = (
        weakref.ref(artifact, cleanup),
        artifact.artifact_hash,
    )
    validate_scientific_detector_prediction_artifact_v1(artifact)
    return artifact


def validate_scientific_detector_prediction_artifact_v1(
    artifact: ScientificDetectorPredictionArtifactV1,
) -> str:
    if type(artifact) is not ScientificDetectorPredictionArtifactV1:
        _fail("PREDICTION_ARTIFACT_TYPE_REJECTED")
    issued = _ISSUED_PREDICTIONS.get(id(artifact))
    if issued is None or issued[0]() is not artifact or issued[1] != artifact.artifact_hash:
        _fail("PREDICTION_ARTIFACT_FACTORY_CUSTODY_REJECTED")
    _validate_prediction_record_closure_v1(
        artifact.prediction_records, artifact.score_vector_content_hash
    )
    if (
        artifact.execution_mode != EXECUTION_MODE
        or artifact.authorization_hash != AUTHORIZATION_HASH
        or artifact.execution_version != D0_INNER_EXECUTION_VERSION
        or artifact.execution_implementation_identity
        != D0_INNER_EXECUTION_IMPLEMENTATION_IDENTITY
        or re.fullmatch(r"[a-f0-9]{40}", artifact.execution_implementation_commit) is None
        or re.fullmatch(
            r"[a-f0-9]{64}", artifact.execution_implementation_source_sha256
        )
        is None
        or artifact.detector_id != DETECTOR_ID
        or artifact.detector_family != DETECTOR_FAMILY
        or artifact.design_hash != DESIGN_HASH
        or artifact.preprocessing_hash != PREPROCESSING_HASH
        or artifact.model_hash != MODEL_HASH
        or artifact.threshold_hash != THRESHOLD_HASH
        or artifact.feature_set_hash != FEATURE_SET_HASH
        or artifact.feature_order_hash != FEATURE_ORDER_HASH
        or artifact.test1_feature_sha256 != TEST1_FEATURE_SHA256
        or artifact.dataset_manifest_id != DATASET_MANIFEST_ID
        or artifact.split_id != INNER_SPLIT_ID
        or artifact.row_count != EXPECTED_ROW_COUNT
        or artifact.point_alarm_count
        != sum(record.alarm_emitted for record in artifact.prediction_records)
        or artifact.artifact_hash != stable_hash_v1(_prediction_payload_v1(artifact))
    ):
        _fail("PREDICTION_ARTIFACT_REPLAY_REJECTED")
    return artifact.artifact_hash


_PREDICTION_DOCUMENT_KEYS = {
    "artifact_type",
    "schema_version",
    "execution_mode",
    "authorization_hash",
    "execution_version",
    "execution_implementation_identity",
    "execution_implementation_commit",
    "execution_implementation_source_sha256",
    "detector_id",
    "detector_family",
    "design_hash",
    "preprocessing_hash",
    "model_hash",
    "threshold_hash",
    "feature_set_hash",
    "feature_order_hash",
    "test1_feature_sha256",
    "dataset_manifest_id",
    "split_id",
    "row_count",
    "unique_row_count",
    "score_vector_content_hash",
    "prediction_records",
    "point_alarm_count",
    "label_blind",
    "labels_accessed_before_prediction_freeze",
    "private_score_values_exposed",
    "private_threshold_value_exposed",
    "private_paths_exposed",
    "artifact_hash",
}
_PREDICTION_RECORD_KEYS = {
    "physical_row_index",
    "alarm_emitted",
    "detector_decision_identity",
}


def validate_scientific_detector_prediction_document_v1(
    document: Mapping[str, Any],
) -> str:
    if type(document) is not dict or set(document) != _PREDICTION_DOCUMENT_KEYS:
        _fail("PREDICTION_DOCUMENT_SCHEMA_REJECTED")
    if _canonical_self_hash_v1(document) != document.get("artifact_hash"):
        _fail("PREDICTION_DOCUMENT_HASH_REJECTED")
    records = document.get("prediction_records")
    score_hash = document.get("score_vector_content_hash")
    _strict_sha256_v1(score_hash, "PREDICTION_SCORE_HASH_REJECTED")
    if type(records) is not list or len(records) != EXPECTED_ROW_COUNT:
        _fail("PREDICTION_DOCUMENT_RECORD_COUNT_REJECTED")
    alarm_count = 0
    for expected_index, record in enumerate(records):
        if (
            type(record) is not dict
            or set(record) != _PREDICTION_RECORD_KEYS
            or type(record.get("physical_row_index")) is not int
            or record.get("physical_row_index") != expected_index
            or type(record.get("alarm_emitted")) is not bool
            or record.get("detector_decision_identity")
            != _decision_identity_v1(expected_index, record["alarm_emitted"], score_hash)
        ):
            _fail("PREDICTION_DOCUMENT_RECORD_CLOSURE_REJECTED")
        alarm_count += int(record["alarm_emitted"])
    required = {
        "artifact_type": "ScientificDetectorPredictionArtifactV1",
        "schema_version": SCHEMA_VERSION,
        "execution_mode": EXECUTION_MODE,
        "authorization_hash": AUTHORIZATION_HASH,
        "execution_version": D0_INNER_EXECUTION_VERSION,
        "execution_implementation_identity": D0_INNER_EXECUTION_IMPLEMENTATION_IDENTITY,
        "detector_id": DETECTOR_ID,
        "detector_family": DETECTOR_FAMILY,
        "design_hash": DESIGN_HASH,
        "preprocessing_hash": PREPROCESSING_HASH,
        "model_hash": MODEL_HASH,
        "threshold_hash": THRESHOLD_HASH,
        "feature_set_hash": FEATURE_SET_HASH,
        "feature_order_hash": FEATURE_ORDER_HASH,
        "test1_feature_sha256": TEST1_FEATURE_SHA256,
        "dataset_manifest_id": DATASET_MANIFEST_ID,
        "split_id": INNER_SPLIT_ID,
        "row_count": EXPECTED_ROW_COUNT,
        "unique_row_count": EXPECTED_ROW_COUNT,
        "point_alarm_count": alarm_count,
        "label_blind": True,
        "labels_accessed_before_prediction_freeze": False,
        "private_score_values_exposed": 0,
        "private_threshold_value_exposed": 0,
        "private_paths_exposed": 0,
    }
    if any(document.get(key) != value for key, value in required.items()):
        _fail("PREDICTION_DOCUMENT_SEMANTICS_REJECTED")
    return str(document["artifact_hash"])


def _public_json_bytes_v1(document: Mapping[str, Any]) -> bytes:
    return (
        json.dumps(
            document,
            sort_keys=True,
            indent=2,
            ensure_ascii=True,
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def _write_public_json_atomic_v1(relative: str, document: Mapping[str, Any]) -> bytes:
    root = _repository_root_v1().resolve()
    path = root / relative
    temporary = path.with_suffix(path.suffix + ".tmp")
    try:
        parent = path.parent.resolve()
        if root not in parent.parents and parent != root:
            _fail("PUBLIC_ARTIFACT_PATH_REJECTED")
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists() or path.is_symlink() or temporary.exists() or temporary.is_symlink():
            _fail("PUBLIC_ARTIFACT_ALREADY_EXISTS")
        content = _public_json_bytes_v1(document)
        with temporary.open("xb") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        replay_bytes = path.read_bytes()
        if replay_bytes != content:
            _fail("PUBLIC_ARTIFACT_BYTES_REJECTED")
        replay = _strict_json_object_v1(replay_bytes)
        if replay != document or _canonical_self_hash_v1(replay) != document["artifact_hash"]:
            _fail("PUBLIC_ARTIFACT_REPLAY_REJECTED")
        return replay_bytes
    except InnerD0ExecutionV1Error:
        raise
    except BaseException:
        _fail("PUBLIC_ARTIFACT_WRITE_REJECTED")


def _persist_prediction_before_label_v1(
    state: D0ExecutionStateMachineV1,
    artifact: ScientificDetectorPredictionArtifactV1,
) -> bytes:
    if state.state is not D0ExecutionStateV1.SCORES_COMPUTED:
        _fail("PREDICTION_PERSISTENCE_ORDER_REJECTED")
    validate_scientific_detector_prediction_artifact_v1(artifact)
    frozen = _write_public_json_atomic_v1(PREDICTION_RELATIVE_PATH, artifact.to_public_dict())
    replay = _strict_json_object_v1(frozen)
    validate_scientific_detector_prediction_document_v1(replay)
    state.transition(D0ExecutionStateV1.SCORES_COMPUTED, D0ExecutionStateV1.PREDICTION_FROZEN)
    return frozen


@dataclass(frozen=True, repr=False)
class RealD0LabelEventCustodyV1:
    label_file_sha256: str
    row_count: int
    strict_label_vector_hash: str
    attack_event_set_hash: str
    attack_event_count: int
    attack_labeled_seconds: int
    normal_labeled_seconds: int
    custody_hash: str
    _labels: tuple[int, ...] = field(repr=False, compare=False)
    _attack_events: tuple[metric_policy_v1.IntervalV1, ...] = field(
        repr=False, compare=False
    )

    def __repr__(self) -> str:
        return "<RealD0LabelEventCustodyV1 validated=True labels=REDACTED intervals=REDACTED>"

    def __reduce__(self) -> object:
        _fail("REAL_LABEL_CUSTODY_SERIALIZATION_PROHIBITED")


_ISSUED_LABEL_CUSTODIES: dict[
    int, tuple[weakref.ReferenceType[RealD0LabelEventCustodyV1], str]
] = {}


def _private_interval_set_hash_v1(
    kind: str, intervals: tuple[metric_policy_v1.IntervalV1, ...]
) -> str:
    return stable_hash_v1(
        {
            "artifact_type": f"task039e3_r2r_private_d0_{kind}_interval_set_v1",
            "interval_semantics": "HALF_OPEN_FILE_LOCAL_ONE_SECOND",
            "intervals": [
                {"start": interval.start, "end": interval.end} for interval in intervals
            ],
        }
    )


def _load_label_custody_once_v1(
    token: _D0InnerExecutionTokenV1,
    state: D0ExecutionStateMachineV1,
    feature_timestamps: tuple[str, ...],
    label_path: Path,
) -> RealD0LabelEventCustodyV1:
    _validate_execution_token_v1(token)
    state.require_label_access()
    observed_hash = _raw_sha256_once_v1(
        label_path, TEST1_LABEL_BYTE_SIZE, "TEST1_LABEL_RAW_IDENTITY_REJECTED"
    )
    if observed_hash != TEST1_LABEL_SHA256:
        _fail("TEST1_LABEL_HASH_REJECTED")
    timestamp_tokens: list[str] = []
    label_tokens: list[str] = []
    try:
        with label_path.open("r", encoding="utf-8", newline="") as stream:
            reader = csv.reader(stream)
            header = next(reader)
            if header != ["timestamp", "label"]:
                _fail("TEST1_LABEL_HEADER_REJECTED")
            for row in reader:
                if len(row) != 2:
                    _fail("TEST1_LABEL_ROW_WIDTH_REJECTED")
                timestamp_tokens.append(row[0])
                label_tokens.append(row[1])
    except InnerD0ExecutionV1Error:
        raise
    except BaseException:
        _fail("TEST1_LABEL_PARSE_REJECTED")
    if tuple(timestamp_tokens) != feature_timestamps or len(label_tokens) != EXPECTED_ROW_COUNT:
        _fail("TEST1_LABEL_ALIGNMENT_REJECTED")
    try:
        labels = protocol_v3.parse_raw_label_tokens_v3(tuple(label_tokens))
        attacks = metric_policy_v1.derive_attack_events_v1(labels)
    except BaseException:
        _fail("TEST1_LABEL_VALUE_REJECTED")
    label_hash = stable_hash_v1(
        {
            "artifact_type": "task039e3_r2r_private_d0_strict_label_vector_v1",
            "label_file_sha256": TEST1_LABEL_SHA256,
            "labels": list(labels),
        }
    )
    attack_hash = _private_interval_set_hash_v1("attack", attacks)
    payload = {
        "artifact_type": "task039e3_r2r_real_d0_label_event_custody_v1",
        "label_file_sha256": TEST1_LABEL_SHA256,
        "row_count": EXPECTED_ROW_COUNT,
        "strict_label_vector_hash": label_hash,
        "attack_event_set_hash": attack_hash,
        "attack_event_count": len(attacks),
        "attack_event_policy": ATTACK_EVENT_POLICY,
    }
    custody = RealD0LabelEventCustodyV1(
        TEST1_LABEL_SHA256,
        EXPECTED_ROW_COUNT,
        label_hash,
        attack_hash,
        len(attacks),
        sum(labels),
        EXPECTED_ROW_COUNT - sum(labels),
        stable_hash_v1(payload),
        labels,
        attacks,
    )
    object_id = id(custody)

    def cleanup(dead: object, *, key: int = object_id) -> None:
        issued = _ISSUED_LABEL_CUSTODIES.get(key)
        if issued is not None and issued[0] is dead:
            _ISSUED_LABEL_CUSTODIES.pop(key, None)

    _ISSUED_LABEL_CUSTODIES[object_id] = (
        weakref.ref(custody, cleanup),
        custody.custody_hash,
    )
    state.transition(D0ExecutionStateV1.PREDICTION_FROZEN, D0ExecutionStateV1.LABEL_PARSED)
    return custody


def _interval_overlap_v1(
    left: metric_policy_v1.IntervalV1, right: metric_policy_v1.IntervalV1
) -> bool:
    return left.start < right.end and right.start < left.end


@dataclass(frozen=True)
class ScientificD0MetricV1:
    metric_name: str
    formula_identity: str
    value: float | None
    defined: bool
    undefined_reason: str | None
    private_evidence_hash: str
    metric_hash: str

    def to_public_dict(self) -> dict[str, object]:
        return {
            "metric_name": self.metric_name,
            "formula_identity": self.formula_identity,
            "value": self.value,
            "defined": self.defined,
            "undefined_reason": self.undefined_reason,
            "private_evidence_hash": self.private_evidence_hash,
            "artifact_hash": self.metric_hash,
        }


def _scientific_metric_v1(
    name: str,
    formula: str,
    numerator: int,
    denominator: float,
    undefined_reason: str,
    private_evidence_hash: str,
) -> ScientificD0MetricV1:
    defined = denominator != 0.0
    value = float(numerator / denominator) if defined else None
    payload = {
        "artifact_type": "ScientificD0MetricV1",
        "metric_name": name,
        "formula_identity": formula,
        "value": value,
        "defined": defined,
        "undefined_reason": None if defined else undefined_reason,
        "private_evidence_hash": private_evidence_hash,
    }
    return ScientificD0MetricV1(
        name,
        formula,
        value,
        defined,
        None if defined else undefined_reason,
        private_evidence_hash,
        stable_hash_v1(payload),
    )


def metric_arithmetic_v1(
    attack_events: tuple[metric_policy_v1.IntervalV1, ...],
    alarm_episodes: tuple[metric_policy_v1.IntervalV1, ...],
    normal_seconds: int,
) -> tuple[int, int, int, float]:
    if (
        type(attack_events) is not tuple
        or type(alarm_episodes) is not tuple
        or any(type(item) is not metric_policy_v1.IntervalV1 for item in attack_events)
        or any(type(item) is not metric_policy_v1.IntervalV1 for item in alarm_episodes)
        or type(normal_seconds) is not int
        or normal_seconds < 0
    ):
        _fail("METRIC_ARITHMETIC_INPUT_REJECTED")
    recall_numerator = sum(
        any(_interval_overlap_v1(attack, alarm) for alarm in alarm_episodes)
        for attack in attack_events
    )
    far_numerator = sum(
        not any(_interval_overlap_v1(alarm, attack) for attack in attack_events)
        for alarm in alarm_episodes
    )
    return recall_numerator, len(attack_events), far_numerator, normal_seconds / 3600.0


def _build_private_metric_evidence_v1(
    custody: RealD0LabelEventCustodyV1,
    alarm_episodes: tuple[metric_policy_v1.IntervalV1, ...],
    score_evidence_hash: str,
    score_vector_content_hash: str,
    prediction_hash: str,
) -> tuple[dict[str, Any], ScientificD0MetricV1, ScientificD0MetricV1]:
    issued = _ISSUED_LABEL_CUSTODIES.get(id(custody))
    if issued is None or issued[0]() is not custody or issued[1] != custody.custody_hash:
        _fail("LABEL_CUSTODY_FACTORY_REJECTED")
    recall_numerator, recall_denominator, far_numerator, far_denominator = (
        metric_arithmetic_v1(
            custody._attack_events, alarm_episodes, custody.normal_labeled_seconds
        )
    )
    alarm_hash = _private_interval_set_hash_v1("alarm", alarm_episodes)
    payload = {
        "artifact_type": "task039e3_r2r_utility_inner_d0_private_metric_evidence_v1",
        "schema_version": SCHEMA_VERSION,
        "authorization_hash": AUTHORIZATION_HASH,
        "strict_label_vector_hash": custody.strict_label_vector_hash,
        "attack_event_set_hash": custody.attack_event_set_hash,
        "detector_alarm_episode_set_hash": alarm_hash,
        "attack_event_recall": {
            "numerator": recall_numerator,
            "denominator": recall_denominator,
        },
        "normal_far_episodes_per_hour": {
            "numerator": far_numerator,
            "normal_second_denominator": custody.normal_labeled_seconds,
            "normal_hour_denominator": far_denominator,
        },
        "strict_label_vector": list(custody._labels),
        "attack_events": [
            {"start": item.start, "end": item.end} for item in custody._attack_events
        ],
        "alarm_episodes": [
            {"start": item.start, "end": item.end} for item in alarm_episodes
        ],
        "score_evidence_hash": score_evidence_hash,
        "score_vector_content_hash": score_vector_content_hash,
        "detector_prediction_artifact_hash": prediction_hash,
    }
    evidence_hash = stable_hash_v1(payload)
    document = {**payload, "artifact_hash": evidence_hash}
    recall = _scientific_metric_v1(
        "attack_event_recall",
        ATTACK_EVENT_RECALL_FORMULA,
        recall_numerator,
        float(recall_denominator),
        "no_attack_events",
        evidence_hash,
    )
    far = _scientific_metric_v1(
        "normal_far_episodes_per_hour",
        NORMAL_FAR_FORMULA,
        far_numerator,
        far_denominator,
        "no_normal_exposure",
        evidence_hash,
    )
    return document, recall, far


@dataclass(frozen=True)
class D0InnerExecutionRunV1:
    committed_execution_grant_hash: str
    authorization_hash: str
    execution_implementation_identity: str
    design_hash: str
    preprocessing_hash: str
    model_hash: str
    threshold_hash: str
    test1_feature_sha256: str
    detector_prediction_artifact_hash: str
    score_evidence_hash: str
    score_vector_content_hash: str
    private_metric_evidence_hash: str
    point_alarm_count: int
    alarm_episode_count: int
    metric_receipt_hashes: tuple[str, str]
    scientific_execution_attempts: int
    scientific_execution_retries: int
    test2_accesses: int
    run_hash: str

    def _payload(self) -> dict[str, Any]:
        return {key: value for key, value in self.__dict__.items() if key != "run_hash"}


@dataclass(frozen=True)
class D0InnerExecutionOutcomeV1:
    run: D0InnerExecutionRunV1
    prediction: ScientificDetectorPredictionArtifactV1
    attack_event_recall: ScientificD0MetricV1
    normal_far_episodes_per_hour: ScientificD0MetricV1
    score_evidence_hash: str
    private_metric_evidence_hash: str
    implementation_audit_hash: str
    accounting_hash: str
    readiness_hash: str
    bundle_hash: str
    receipt_hash: str


def reject_prohibited_operation_v1(operation: str) -> NoReturn:
    prohibited = {
        "d1_content_read",
        "d1_execution",
        "d2",
        "fusion",
        "test2",
        "outer",
        "retry",
        "retraining",
        "recalibration",
        "result_driven_change",
        "score_smoothing",
    }
    if operation in prohibited:
        _fail("PROHIBITED_D0_EXECUTION_OPERATION_REJECTED")
    _fail("UNKNOWN_D0_EXECUTION_OPERATION_REJECTED")


def _self_hashed_document_v1(payload: Mapping[str, Any]) -> dict[str, Any]:
    if "artifact_hash" in payload:
        _fail("PREHASHED_PUBLIC_PAYLOAD_REJECTED")
    document = dict(payload)
    document["artifact_hash"] = stable_hash_v1(document)
    return document


def _utc_now_v1() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _report_text_and_hash_v1(
    prediction: ScientificDetectorPredictionArtifactV1,
    recall: ScientificD0MetricV1,
    far: ScientificD0MetricV1,
    alarm_episode_count: int,
) -> tuple[str, str]:
    body = (
        "# TASK-039E3-R2R Utility INNER D0 Execution V1\n\n"
        f"Status: `{PASS_STATUS}`\n\n"
        f"Scientific status: `{SCIENTIFIC_STATUS}`\n\n"
        "The first and only authorized real INNER D0 PCA-SPE execution completed exactly once. "
        "The result is frozen without scientific interpretation, tuning, or comparison.\n\n"
        f"- Authorization: `{AUTHORIZATION_HASH}`\n"
        f"- DetectorPrediction artifact: `{prediction.artifact_hash}`\n"
        f"- Point alarm count: `{prediction.point_alarm_count}`\n"
        f"- Alarm episode count: `{alarm_episode_count}`\n"
        f"- Attack-event Recall: `{recall.value}` (defined: `{str(recall.defined).lower()}`)\n"
        f"- Normal FAR episodes/hour: `{far.value}` (defined: `{str(far.defined).lower()}`)\n"
        "- Test2 accesses: `0`\n"
        "- D1 content reads: `0`\n"
        "- D2 executions: `0`\n"
        "- Private paths and private numeric values exposed: `0`\n\n"
        "Exact next task: `TASK-039E3-R2R-UTILITY-INNER-D0-RESULT-INTEGRITY-AUDIT-V1`.\n"
    )
    report_hash = stable_hash_v1(
        {
            "artifact_type": "task039e3_r2r_utility_inner_d0_execution_v1_report",
            "body": body,
        }
    )
    return body + f"\nReport artifact hash: `{report_hash}`\n", report_hash


def _write_report_atomic_v1(text: str) -> None:
    relative = "docs/task_reports/TASK-039E3_R2R_UTILITY_INNER_D0_EXECUTION_V1_REPORT.md"
    root = _repository_root_v1().resolve()
    path = root / relative
    temporary = path.with_suffix(path.suffix + ".tmp")
    try:
        if path.exists() or path.is_symlink() or temporary.exists() or temporary.is_symlink():
            _fail("PUBLIC_REPORT_ALREADY_EXISTS")
        with temporary.open("x", encoding="utf-8", newline="\n") as stream:
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        if path.read_text(encoding="utf-8") != text:
            _fail("PUBLIC_REPORT_REPLAY_REJECTED")
    except InnerD0ExecutionV1Error:
        raise
    except BaseException:
        _fail("PUBLIC_REPORT_WRITE_REJECTED")


def _public_result_reports_v1(
    *,
    grant: CommittedD0InnerExecutionGrantV1,
    prediction: ScientificDetectorPredictionArtifactV1,
    score_evidence_hash: str,
    private_metric_evidence_hash: str,
    recall: ScientificD0MetricV1,
    far: ScientificD0MetricV1,
    alarm_episode_count: int,
    run: D0InnerExecutionRunV1,
) -> tuple[str, str, str, str, str]:
    implementation_commit, implementation_source_sha = _file_commit_custody_v1(
        "src/paperworks/v6/task039e3_r2r_d0_inner_execution_v1.py"
    )
    independent_commit, independent_source_sha = _file_commit_custody_v1(
        "tests/test_task039e3_r2r_d0_inner_execution_v1_independent.py"
    )
    created = _utc_now_v1()
    implementation_audit = _self_hashed_document_v1(
        {
            "artifact_type": "task039e3_r2r_utility_inner_d0_execution_v1_implementation_audit",
            "schema_version": SCHEMA_VERSION,
            "task_id": TASK_ID,
            "created_at_utc": created,
            "status": "PASS",
            "execution_implementation_identity": D0_INNER_EXECUTION_IMPLEMENTATION_IDENTITY,
            "execution_implementation_commit_a": implementation_commit,
            "execution_implementation_source_sha256": implementation_source_sha,
            "independent_audit_commit_b": independent_commit,
            "independent_audit_source_sha256": independent_source_sha,
            "static_suite_passed": True,
            "independent_suite_passed": True,
            "independent_attacks": EXPECTED_INDEPENDENT_ATTACKS,
            "accepted_invalid": 0,
            "numeric_differential_cases": NUMERIC_DIFFERENTIAL_CASES,
            "numeric_differential_divergences": 0,
            "production_changes_after_commit_a": 0,
            "python_version": PYTHON_VERSION,
            "numpy_version": NUMPY_VERSION,
            "numeric_backend": NUMERIC_BACKEND,
            "private_paths_exposed": 0,
            "private_preprocessing_values_exposed": 0,
            "private_model_values_exposed": 0,
            "private_threshold_values_exposed": 0,
            "private_score_values_exposed": 0,
        }
    )
    metrics = _self_hashed_document_v1(
        {
            "artifact_type": "task039e3_r2r_utility_inner_d0_metrics_v1",
            "schema_version": SCHEMA_VERSION,
            "task_id": TASK_ID,
            "created_at_utc": created,
            "execution_mode": EXECUTION_MODE,
            "detector_id": DETECTOR_ID,
            "authorization_hash": AUTHORIZATION_HASH,
            "detector_prediction_artifact_hash": prediction.artifact_hash,
            "point_alarm_count": prediction.point_alarm_count,
            "alarm_episode_count": alarm_episode_count,
            "attack_event_recall": recall.to_public_dict(),
            "normal_far_episodes_per_hour": far.to_public_dict(),
            "private_metric_evidence_hash": private_metric_evidence_hash,
            "raw_scores_public": False,
            "threshold_value_public": False,
            "label_vector_public": False,
            "attack_intervals_public": False,
            "private_metric_denominators_public": False,
        }
    )
    accounting = _self_hashed_document_v1(
        {
            "artifact_type": "task039e3_r2r_utility_inner_d0_execution_v1_accounting",
            "schema_version": SCHEMA_VERSION,
            "task_id": TASK_ID,
            "created_at_utc": created,
            "scientific_execution_attempts": 1,
            "scientific_execution_retries": 0,
            "preprocessing_reads": 1,
            "model_reads": 1,
            "threshold_reads": 1,
            "test1_feature_hash_reads": 1,
            "test1_feature_scientific_parses": 1,
            "score_computations": EXPECTED_ROW_COUNT,
            "detector_prediction_freezes": 1,
            "label_hash_reads": 1,
            "label_scientific_parses": 1,
            "label_before_prediction_access": False,
            "attack_event_derivations": 1,
            "metric_computations": 2,
            "D1_content_reads": 0,
            "D1_executions": 0,
            "D2_executions": 0,
            "OUTER_executions": 0,
            "test2_accesses": 0,
            "hai_test2_opens": 0,
            "hai_test2_hashes": 0,
            "label_test2_opens": 0,
            "summary_label_accesses": 0,
            "result_driven_changes": False,
            "private_paths_exposed": 0,
            "private_preprocessing_values_exposed": 0,
            "private_model_values_exposed": 0,
            "private_pca_values_exposed": 0,
            "private_threshold_values_exposed": 0,
            "private_score_values_exposed": 0,
            "execution_run_hash": run.run_hash,
        }
    )
    readiness = _self_hashed_document_v1(
        {
            "artifact_type": "task039e3_r2r_utility_inner_d0_execution_v1_readiness",
            "schema_version": SCHEMA_VERSION,
            "task_id": TASK_ID,
            "created_at_utc": created,
            "status": PASS_STATUS,
            "scientific_status": SCIENTIFIC_STATUS,
            "authorization_hash": AUTHORIZATION_HASH,
            "committed_execution_grant_hash": grant.grant_hash,
            "detector_prediction_artifact_hash": prediction.artifact_hash,
            "metrics_hash": metrics["artifact_hash"],
            "implementation_audit_hash": implementation_audit["artifact_hash"],
            "accounting_hash": accounting["artifact_hash"],
            "execution_run_hash": run.run_hash,
            "preprocessing_hash_match": True,
            "model_hash_match": True,
            "threshold_hash_match": True,
            "test1_feature_hash_match": True,
            "test1_label_hash_match": True,
            "test1_feature_rows": EXPECTED_ROW_COUNT,
            "feature_count": FEATURE_COUNT,
            "score_computations": EXPECTED_ROW_COUNT,
            "UTILITY_INNER_D0_MODEL_THRESHOLD_INTEGRITY_AUDITED": True,
            "UTILITY_INNER_D0_EXECUTION_AUTHORIZATION_ISSUED": True,
            "UTILITY_INNER_D0_AUTHORIZED": True,
            "UTILITY_INNER_D0_EXECUTED": True,
            "UTILITY_INNER_D0_RESULT_FROZEN": True,
            "UTILITY_INNER_D0_RESULT_INTEGRITY_AUDITED": False,
            "UTILITY_INNER_D0_RESULT_INTERPRETATION_READY": False,
            "UTILITY_INNER_D2_AUTHORIZED": False,
            "UTILITY_OUTER_EXECUTION_AUTHORIZED": False,
            "exact_next_task": (
                "TASK-039E3-R2R-UTILITY-INNER-D0-RESULT-INTEGRITY-AUDIT-V1"
            ),
        }
    )
    report_text, report_hash = _report_text_and_hash_v1(
        prediction, recall, far, alarm_episode_count
    )
    bundle = _self_hashed_document_v1(
        {
            "artifact_type": "task039e3_r2r_utility_inner_d0_execution_v1_bundle",
            "schema_version": SCHEMA_VERSION,
            "task_id": TASK_ID,
            "created_at_utc": created,
            "authorization_hash": AUTHORIZATION_HASH,
            "committed_preflight_hash": PREFLIGHT_HASH,
            "committed_authorization_receipt_hash": AUTHORIZATION_RECEIPT_HASH,
            "committed_execution_grant_hash": grant.grant_hash,
            "implementation_audit_hash": implementation_audit["artifact_hash"],
            "detector_prediction_artifact_hash": prediction.artifact_hash,
            "score_evidence_hash": score_evidence_hash,
            "score_vector_content_hash": prediction.score_vector_content_hash,
            "private_metric_evidence_hash": private_metric_evidence_hash,
            "metrics_hash": metrics["artifact_hash"],
            "accounting_hash": accounting["artifact_hash"],
            "readiness_hash": readiness["artifact_hash"],
            "execution_run_hash": run.run_hash,
            "report_hash": report_hash,
        }
    )
    receipt = _self_hashed_document_v1(
        {
            "artifact_type": "task039e3_r2r_utility_inner_d0_execution_v1_receipt",
            "schema_version": SCHEMA_VERSION,
            "task_id": TASK_ID,
            "created_at_utc": created,
            "status": PASS_STATUS,
            "scientific_status": SCIENTIFIC_STATUS,
            "authorization_hash": AUTHORIZATION_HASH,
            "preflight_hash": PREFLIGHT_HASH,
            "authorization_receipt_hash": AUTHORIZATION_RECEIPT_HASH,
            "detector_prediction_artifact_hash": prediction.artifact_hash,
            "implementation_audit_hash": implementation_audit["artifact_hash"],
            "accounting_hash": accounting["artifact_hash"],
            "readiness_hash": readiness["artifact_hash"],
            "bundle_hash": bundle["artifact_hash"],
            "execution_run_hash": run.run_hash,
            "scientific_execution_attempts": 1,
            "scientific_execution_retries": 0,
            "test2_accesses": 0,
            "D1_content_reads": 0,
            "D1_executions": 0,
            "D2_executions": 0,
            "OUTER_executions": 0,
            "result_driven_changes": False,
            "private_paths_exposed": 0,
            "private_preprocessing_values_exposed": 0,
            "private_model_values_exposed": 0,
            "private_pca_values_exposed": 0,
            "private_threshold_values_exposed": 0,
            "private_score_values_exposed": 0,
            "exact_next_task": (
                "TASK-039E3-R2R-UTILITY-INNER-D0-RESULT-INTEGRITY-AUDIT-V1"
            ),
        }
    )
    outputs = (
        (
            "docs/task_reports/"
            "TASK-039E3_R2R_UTILITY_INNER_D0_EXECUTION_V1_IMPLEMENTATION_AUDIT.json",
            implementation_audit,
        ),
        (
            "docs/task_reports/TASK-039E3_R2R_UTILITY_INNER_D0_METRICS_V1.json",
            metrics,
        ),
        (
            "docs/task_reports/"
            "TASK-039E3_R2R_UTILITY_INNER_D0_EXECUTION_V1_ACCOUNTING.json",
            accounting,
        ),
        (
            "docs/task_reports/"
            "TASK-039E3_R2R_UTILITY_INNER_D0_EXECUTION_V1_READINESS.json",
            readiness,
        ),
        (
            "docs/task_reports/"
            "TASK-039E3_R2R_UTILITY_INNER_D0_EXECUTION_V1_BUNDLE.json",
            bundle,
        ),
        (
            "docs/task_reports/"
            "TASK-039E3_R2R_UTILITY_INNER_D0_EXECUTION_V1_RECEIPT.json",
            receipt,
        ),
    )
    for relative, document in outputs:
        _write_public_json_atomic_v1(relative, document)
    _write_report_atomic_v1(report_text)
    return (
        str(implementation_audit["artifact_hash"]),
        str(accounting["artifact_hash"]),
        str(readiness["artifact_hash"]),
        str(bundle["artifact_hash"]),
        str(receipt["artifact_hash"]),
    )


_REAL_ENTRY_ATTEMPTED = False
_SCIENTIFIC_EXECUTION_ATTEMPTS = 0
_SCIENTIFIC_EXECUTION_COMPLETED = False


def execute_authorized_d0_inner_v1() -> D0InnerExecutionOutcomeV1:
    """Execute the exact authorized D0 INNER experiment once, with no knobs."""

    global _REAL_ENTRY_ATTEMPTED, _SCIENTIFIC_EXECUTION_ATTEMPTS
    global _SCIENTIFIC_EXECUTION_COMPLETED
    if _REAL_ENTRY_ATTEMPTED or _SCIENTIFIC_EXECUTION_COMPLETED:
        _fail("REAL_D0_EXECUTION_ALREADY_ATTEMPTED")
    _REAL_ENTRY_ATTEMPTED = True
    state = D0ExecutionStateMachineV1()
    grant = issue_committed_d0_inner_execution_grant_v1()
    token = _issue_execution_token_v1(grant)
    state.transition(D0ExecutionStateV1.NOT_STARTED, D0ExecutionStateV1.GRANT_REPLAYED)
    validate_numeric_backend_v1()
    bindings = _load_local_bindings_v1()
    hai_root = _private_hai_root_v1(bindings[HAI_DATA_ROOT_BINDING])
    private_bundle = _load_frozen_private_model_bundle_v1(token, bindings)
    validate_frozen_d0_private_model_bundle_v1(private_bundle)
    state.transition(
        D0ExecutionStateV1.GRANT_REPLAYED,
        D0ExecutionStateV1.PRIVATE_AUTHORITY_VALIDATED,
    )

    feature_path = hai_root / "hai-23.05" / TEST1_FEATURE_FILENAME
    observed_feature_hash = _raw_sha256_once_v1(
        feature_path,
        TEST1_FEATURE_BYTE_SIZE,
        "TEST1_FEATURE_RAW_IDENTITY_REJECTED",
    )
    validate_test1_feature_raw_identity_v1(
        observed_feature_hash, TEST1_FEATURE_BYTE_SIZE
    )
    _SCIENTIFIC_EXECUTION_ATTEMPTS = 1
    frame = _parse_test1_feature_frame_once_v1(token, feature_path)
    validate_real_d0_feature_frame_v1(frame)
    state.transition(
        D0ExecutionStateV1.PRIVATE_AUTHORITY_VALIDATED,
        D0ExecutionStateV1.FEATURE_PARSED,
    )
    scores = compute_spe_float64_v1(
        frame._matrix,
        private_bundle._means,
        private_bundle._scales,
        private_bundle._retained_loadings,
    )
    if scores.shape != (EXPECTED_ROW_COUNT,):
        _fail("REAL_SCORE_COUNT_REJECTED")
    score_evidence_hash, score_vector_content_hash = _freeze_private_score_evidence_v1(
        hai_root, scores
    )
    alarm_mask = strict_alarm_mask_v1(scores, private_bundle._threshold)
    state.transition(
        D0ExecutionStateV1.FEATURE_PARSED, D0ExecutionStateV1.SCORES_COMPUTED
    )
    prediction = _build_scientific_prediction_v1(
        token, alarm_mask, score_vector_content_hash
    )
    frozen_prediction_bytes = _persist_prediction_before_label_v1(state, prediction)

    label_path = hai_root / "hai-23.05" / TEST1_LABEL_FILENAME
    label_custody = _load_label_custody_once_v1(
        token, state, frame._timestamps, label_path
    )
    prediction_path = _repository_root_v1() / PREDICTION_RELATIVE_PATH
    metric_prediction_bytes = prediction_path.read_bytes()
    if metric_prediction_bytes != frozen_prediction_bytes:
        _fail("PREDICTION_BYTES_CHANGED_BEFORE_METRICS")
    prediction_document = _strict_json_object_v1(metric_prediction_bytes)
    validate_scientific_detector_prediction_document_v1(prediction_document)
    alarm_indices = tuple(
        int(record["physical_row_index"])
        for record in prediction_document["prediction_records"]
        if record["alarm_emitted"] is True
    )
    alarm_episodes = metric_policy_v1.form_alarm_episodes_v1(alarm_indices)
    private_metric_document, recall, far = _build_private_metric_evidence_v1(
        label_custody,
        alarm_episodes,
        score_evidence_hash,
        score_vector_content_hash,
        prediction.artifact_hash,
    )
    private_metric_evidence_hash = _write_private_json_atomic_v1(
        _private_evidence_directory_v1(hai_root),
        "task039e3_inner_d0_metric_evidence_v1.json",
        private_metric_document,
    )
    state.transition(
        D0ExecutionStateV1.LABEL_PARSED, D0ExecutionStateV1.METRICS_COMPUTED
    )
    provisional_run = D0InnerExecutionRunV1(
        grant.grant_hash,
        AUTHORIZATION_HASH,
        D0_INNER_EXECUTION_IMPLEMENTATION_IDENTITY,
        DESIGN_HASH,
        PREPROCESSING_HASH,
        MODEL_HASH,
        THRESHOLD_HASH,
        TEST1_FEATURE_SHA256,
        prediction.artifact_hash,
        score_evidence_hash,
        score_vector_content_hash,
        private_metric_evidence_hash,
        prediction.point_alarm_count,
        len(alarm_episodes),
        (recall.metric_hash, far.metric_hash),
        1,
        0,
        0,
        "",
    )
    run = replace(
        provisional_run, run_hash=stable_hash_v1(provisional_run._payload())
    )
    (
        implementation_audit_hash,
        accounting_hash,
        readiness_hash,
        bundle_hash,
        receipt_hash,
    ) = _public_result_reports_v1(
        grant=grant,
        prediction=prediction,
        score_evidence_hash=score_evidence_hash,
        private_metric_evidence_hash=private_metric_evidence_hash,
        recall=recall,
        far=far,
        alarm_episode_count=len(alarm_episodes),
        run=run,
    )
    if prediction_path.read_bytes() != frozen_prediction_bytes:
        _fail("PREDICTION_BYTES_CHANGED_AFTER_METRICS")
    state.transition(
        D0ExecutionStateV1.METRICS_COMPUTED, D0ExecutionStateV1.RESULT_FROZEN
    )
    _SCIENTIFIC_EXECUTION_COMPLETED = True
    return D0InnerExecutionOutcomeV1(
        run,
        prediction,
        recall,
        far,
        score_evidence_hash,
        private_metric_evidence_hash,
        implementation_audit_hash,
        accounting_hash,
        readiness_hash,
        bundle_hash,
        receipt_hash,
    )


__all__ = [
    "CommittedD0InnerExecutionGrantV1",
    "D0ExecutionStateMachineV1",
    "D0ExecutionStateV1",
    "D0InnerExecutionOutcomeV1",
    "D0InnerExecutionRunV1",
    "D0_INNER_EXECUTION_IMPLEMENTATION_IDENTITY",
    "D0_INNER_EXECUTION_VERSION",
    "EXPECTED_INDEPENDENT_ATTACKS",
    "FrozenD0PrivateModelBundleV1",
    "InnerD0ExecutionV1Error",
    "NUMERIC_DIFFERENTIAL_CASES",
    "RealD0FeatureFrameV1",
    "RealD0LabelEventCustodyV1",
    "ScientificD0MetricV1",
    "ScientificDetectorPredictionArtifactV1",
    "ScientificDetectorPredictionRecordV1",
    "compute_spe_float64_v1",
    "execute_authorized_d0_inner_v1",
    "issue_committed_d0_inner_execution_grant_v1",
    "metric_arithmetic_v1",
    "reject_prohibited_operation_v1",
    "strict_alarm_mask_v1",
    "validate_committed_d0_inner_execution_grant_v1",
    "validate_numeric_backend_v1",
    "validate_scientific_detector_prediction_artifact_v1",
    "validate_scientific_detector_prediction_document_v1",
    "validate_test1_feature_raw_identity_v1",
]
