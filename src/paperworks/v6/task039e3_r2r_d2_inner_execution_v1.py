"""Single-use real INNER D2 fusion of immutable D0/D1 predictions.

The public entry point has no scientific arguments. It replays the complete
committed D2 authorization set, validates and parses only the exact frozen D0
and D1 prediction artifacts, freezes a label-blind CombinedPrediction, and
only then opens label-test1 for the frozen metric calculations. Raw source
sets, labels, intervals, numerators, denominators, and private paths stay
outside Git.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from enum import Enum
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import subprocess
from typing import Any, Mapping, NoReturn, Sequence
import weakref

from paperworks.v6.common import stable_hash_v1
from paperworks.v6 import task039e3_r2r_utility_evaluator_metrics_v1 as metric_policy_v1
from paperworks.v6 import task039e3_r2r_utility_protocol_v3 as protocol_v3


TASK_ID = "TASK-039E3-R2R-UTILITY-INNER-D2-EXECUTION-V1"
PASS_STATUS = "passed_task039e3_r2r_utility_inner_d2_execution_v1"
SCIENTIFIC_STATUS = "D2_EXECUTED_RESULT_INTEGRITY_AUDIT_PENDING"
D2_INNER_EXECUTION_VERSION = "TASK039E3_R2R_D2_INNER_EXECUTION_V1"
EXECUTION_MODE = "REAL_INNER_D2_FROZEN_PREDICTION_FUSION"
SCHEMA_VERSION = "1.0.0"

AUTHORIZATION_FREEZE_COMMIT = "a412a0e7e893d23e7806e18831142f75cd5c0828"
AUTHORIZATION_VERSION = "TASK039E3_R2R_D2_INNER_EXECUTION_AUTHORIZATION_V1"
AUTHORIZATION_SCOPE = (
    "HAI_23_05_P1_TEST1_D2_D0_PLUS_VERIFIED_RULE_CORROBORATION_INNER_V1"
)
AUTHORIZATION_HASH = "b931d7bd89e923dc4d380e35ed2b3ff514679a701e0b94a75d426130a3c4427c"
AUTHORIZATION_CONTRACT_HASH = "9abe31f8163c2709275e25ca7e9516f8d3e108b7bf2a4e7a0a9d15ad645e4638"
AUTHORIZATION_INDEPENDENT_AUDIT_HASH = "a1f9c270bc36e8c4b64bc6aae2510a1c83034fc3b4abd805896e4dab98803e33"
AUTHORIZATION_PREFLIGHT_HASH = "5ec6ce95c38cfe313034882e3a9020c3846f71b9e368676627ded9094a41ad8e"
AUTHORIZATION_ACCOUNTING_HASH = "856082f8f08a3c79cfbcb2b8d1332e047d2f4087a408f435fd4be456efcc5d19"
AUTHORIZATION_READINESS_HASH = "72fe36cd9e5df8117c7db511c1ecd3c70c7d6dc0ec9db16f8c854baef0b05f65"
AUTHORIZATION_BUNDLE_HASH = "61c33e2652734726fe408d7254068121ce1af5ef5de9372242a9b041276ad00d"
AUTHORIZATION_RECEIPT_HASH = "7d372987043e65d3038d06f318f5426cefd9a3bfee55fb27851aded0c52e6137"
AUTHORIZATION_REPORT_BODY_HASH = "5db2f0ff315d5578c32540df6044f19389fa3a784291d7df2317c3dff6446251"

D2_ID = "D2_D0_PLUS_VERIFIED_RULE_CORROBORATION_V1"
D2_DESIGN_HASH = "eb559a91350fd046204d223d6820ef7f0590ad4beb7a2b17114a496859758e51"
PROVENANCE_CLARIFICATION_HASH = "f0fbea249e11b6a3ae27a43b4b705d8537983511e2659d88f49b9c64dcf59e10"
D0_PREDICTION_HASH = "a4b58f1c78b9bb53125da1a009f3fd05b02e1c83a789772a341a7679fddca0f6"
D1_PREDICTION_HASH = "58c3c49f9657f68d35c830b12eeb493ce4bbf7669c90f04813fb80246c3c2682"
D0_PREDICTION_FREEZE_COMMIT = "78d758f50657413eed28dc838212be9a1edeffc7"
D1_PREDICTION_FREEZE_COMMIT = "9fe9192c6da4e2d1f3c7a42ecdd28006e8534449"
SOURCE_MAP_HASH = "f866176000c3d5a943053ac3125d2700b0b72f25b5a0539d8f4713435a959818"
SOURCE_RESOLUTION_POLICY = (
    "D1_RELATION_BINDING_HASH_TO_CANONICAL_V4_RULE_DESCRIPTOR_SOURCE_V1"
)
REQUIRED_DISTINCT_SOURCE_COUNT = 2
SAME_SECOND_POLICY = "EXACT_DECISION_PHYSICAL_ROW_INDEX_EQUALITY"
D0_PRESERVATION_POLICY = "EVERY_FROZEN_D0_ALARM_IS_A_D2_ALARM"
EXPECTED_ROW_COUNT = 54_000
EXPECTED_D1_RECORD_COUNT = 6_031
LABEL_SHA256 = "eaf69edb9c5834bc393afd7bf658b5e408d34fd7bfc3261f80516765fb818fbc"
LABEL_BYTE_SIZE = 1_242_017
LABEL_FILENAME = "label-test1.csv"
DATASET_MANIFEST_ID = "5b0c395169fea468f7afd52aceafc4e6dadf062a1bc557c5bbe5dd6b8a761aa2"
INNER_SPLIT_ID = "30a7c88d6e0af5c37493237cc83b9520cbcd6f43c2dee7bb50ec3cac2668e7d0"

TRIGGER_CLASSES = (
    "NONE",
    "D0_ONLY",
    "RULE_RECOVERY",
    "D0_AND_RULE_CORROBORATION",
)
ATTACK_EVENT_POLICY = "MAXIMAL_CONTIGUOUS_STRICT_LABEL_ONE_RUNS_FILE_LOCAL"
ALARM_EPISODE_POLICY = (
    "MAXIMAL_CONTIGUOUS_UNIQUE_ONE_SECOND_DECISION_INDICES_FILE_LOCAL"
)
ATTACK_EVENT_RECALL_FORMULA = (
    "ATTACK_EVENTS_OVERLAPPED_BY_AT_LEAST_ONE_ALARM_EPISODE_DIVIDED_BY_ALL_ATTACK_EVENTS"
)
NORMAL_FAR_FORMULA = (
    "ALARM_EPISODES_WITH_NO_ATTACK_TIMESTAMP_DIVIDED_BY_NORMAL_LABELED_SECONDS_OVER_3600"
)
D0_MISSED_ATTACK_RECOVERY_FORMULA = (
    "D0_MISSED_ATTACK_EVENTS_RECOVERED_BY_RULE_RECOVERY_DIVIDED_BY_ALL_D0_MISSED_ATTACK_EVENTS"
)
INCREMENTAL_ATTACK_RECALL_FORMULA = (
    "D2_ATTACK_EVENT_RECALL_MINUS_D0_ATTACK_EVENT_RECALL"
)
ADDED_NORMAL_RECOVERY_FAR_FORMULA = (
    "RULE_RECOVERY_ALARM_EPISODES_WITH_ZERO_ATTACK_EVENT_OVERLAP_DIVIDED_BY_NORMAL_LABELED_SECONDS_OVER_3600"
)
INCREMENTAL_NORMAL_FAR_FORMULA = (
    "D2_NORMAL_FAR_EPISODES_PER_HOUR_MINUS_D0_NORMAL_FAR_EPISODES_PER_HOUR"
)

DIFFERENTIAL_CASES = 6
EXPECTED_INDEPENDENT_ATTACKS = 32

D0_PREDICTION_RELATIVE_PATH = (
    "docs/task_reports/"
    "TASK-039E3_R2R_UTILITY_INNER_D0_DETECTOR_PREDICTION_ARTIFACT_V1.json"
)
D1_PREDICTION_RELATIVE_PATH = (
    "docs/task_reports/"
    "TASK-039E3_R2R_UTILITY_INNER_D1_RULE_PREDICTION_ARTIFACT_V1.json"
)
SOURCE_MAP_RELATIVE_PATH = (
    "docs/task_reports/"
    "TASK-039E3_R2R_UTILITY_INNER_D2_EXECUTION_AUTHORIZATION_V1_SOURCE_MAP.json"
)
COMBINED_PREDICTION_RELATIVE_PATH = (
    "docs/task_reports/"
    "TASK-039E3_R2R_UTILITY_INNER_D2_COMBINED_PREDICTION_ARTIFACT_V1.json"
)

AUTHORIZATION_ARTIFACTS = {
    "TASK-039E3_R2R_UTILITY_INNER_D2_EXECUTION_AUTHORIZATION_V1_SOURCE_MAP.json": SOURCE_MAP_HASH,
    "TASK-039E3_R2R_UTILITY_INNER_D2_EXECUTION_AUTHORIZATION_V1_CONTRACT.json": AUTHORIZATION_CONTRACT_HASH,
    "TASK-039E3_R2R_UTILITY_INNER_D2_EXECUTION_AUTHORIZATION_V1_INDEPENDENT_AUDIT.json": AUTHORIZATION_INDEPENDENT_AUDIT_HASH,
    "TASK-039E3_R2R_UTILITY_INNER_D2_EXECUTION_AUTHORIZATION_V1_PREFLIGHT.json": AUTHORIZATION_PREFLIGHT_HASH,
    "TASK-039E3_R2R_UTILITY_INNER_D2_EXECUTION_AUTHORIZATION_V1_AUTHORIZATION.json": AUTHORIZATION_HASH,
    "TASK-039E3_R2R_UTILITY_INNER_D2_EXECUTION_AUTHORIZATION_V1_ACCOUNTING.json": AUTHORIZATION_ACCOUNTING_HASH,
    "TASK-039E3_R2R_UTILITY_INNER_D2_EXECUTION_AUTHORIZATION_V1_READINESS.json": AUTHORIZATION_READINESS_HASH,
    "TASK-039E3_R2R_UTILITY_INNER_D2_EXECUTION_AUTHORIZATION_V1_BUNDLE.json": AUTHORIZATION_BUNDLE_HASH,
    "TASK-039E3_R2R_UTILITY_INNER_D2_EXECUTION_AUTHORIZATION_V1_RECEIPT.json": AUTHORIZATION_RECEIPT_HASH,
}

D0_ROOT_KEYS = frozenset(
    {
        "artifact_hash", "artifact_type", "authorization_hash", "dataset_manifest_id",
        "design_hash", "detector_family", "detector_id", "execution_implementation_commit",
        "execution_implementation_identity", "execution_implementation_source_sha256",
        "execution_mode", "execution_version", "feature_order_hash", "feature_set_hash",
        "label_blind", "labels_accessed_before_prediction_freeze", "model_hash",
        "point_alarm_count", "prediction_records", "preprocessing_hash",
        "private_paths_exposed", "private_score_values_exposed",
        "private_threshold_value_exposed", "row_count", "schema_version",
        "score_vector_content_hash", "split_id", "test1_feature_sha256",
        "threshold_hash", "unique_row_count",
    }
)
D0_RECORD_KEYS = frozenset(
    {"physical_row_index", "alarm_emitted", "detector_decision_identity"}
)
D1_ROOT_KEYS = frozenset(
    {
        "artifact_hash", "artifact_type", "artifact_version", "authorization_hash",
        "authorization_report_commit", "bridge_identity", "common_portfolio",
        "common_relation_count", "counts", "dataset_manifest_identity",
        "denominator_policy", "evaluator_authority_bundle_hash", "execution_bridge_commit",
        "execution_bridge_source_sha256", "execution_mode", "feature_sha256",
        "full_census_identity", "label_blind", "labels_accessed_before_prediction_freeze",
        "main_descriptor_hash", "main_private_registry_hash", "prediction_records",
        "private_numeric_values_exposed", "private_paths_exposed",
        "r3_implementation_identity", "scientific_eligible", "split_identity",
        "supplement_descriptor_hash", "supplement_private_registry_hash",
        "v4_authority_hash",
    }
)
D1_RECORD_KEYS = frozenset(
    {
        "alarm_emitted", "computation_identity", "decision_physical_row_index",
        "final_state", "numeric_reference_identities", "opportunity_id",
        "relation_binding_hash", "source_event_identity_hash", "trace_hash",
    }
)
COMBINED_RECORD_KEYS = frozenset(
    {"physical_row_index", "d2_alarm_emitted", "trigger_class", "combined_decision_identity"}
)

EXECUTION_SEMANTIC_POLICY = {
    "artifact_type": "task039e3_r2r_d2_inner_execution_semantics_v1",
    "version": D2_INNER_EXECUTION_VERSION,
    "mode": EXECUTION_MODE,
    "authorization_scope": AUTHORIZATION_SCOPE,
    "d2_id": D2_ID,
    "d2_design_hash": D2_DESIGN_HASH,
    "d0_prediction_hash": D0_PREDICTION_HASH,
    "d1_prediction_hash": D1_PREDICTION_HASH,
    "source_map_hash": SOURCE_MAP_HASH,
    "source_resolution_policy": SOURCE_RESOLUTION_POLICY,
    "required_distinct_source_count": REQUIRED_DISTINCT_SOURCE_COUNT,
    "same_second_policy": SAME_SECOND_POLICY,
    "d0_preservation_policy": D0_PRESERVATION_POLICY,
    "trigger_classes": TRIGGER_CLASSES,
    "combined_prediction_first": True,
    "label_before_combined_prediction": False,
    "attack_event_policy": ATTACK_EVENT_POLICY,
    "alarm_episode_policy": ALARM_EPISODE_POLICY,
    "primary_metric_formulas": (ATTACK_EVENT_RECALL_FORMULA, NORMAL_FAR_FORMULA),
    "incremental_metric_formulas": (
        D0_MISSED_ATTACK_RECOVERY_FORMULA,
        INCREMENTAL_ATTACK_RECALL_FORMULA,
        ADDED_NORMAL_RECOVERY_FAR_FORMULA,
        INCREMENTAL_NORMAL_FAR_FORMULA,
    ),
    "d0_rerun": False,
    "d1_rerun": False,
    "d0_score_access": False,
    "d1_metric_read": False,
    "test1_feature_access": False,
    "test2": False,
    "retries": 0,
}
D2_INNER_EXECUTION_IMPLEMENTATION_IDENTITY = stable_hash_v1(EXECUTION_SEMANTIC_POLICY)


class D2InnerExecutionV1Error(ValueError):
    """A frozen authorization, input, fusion, state, or privacy invariant differs."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


def _fail(code: str) -> NoReturn:
    raise D2InnerExecutionV1Error(code)


def _repository_root_v1() -> Path:
    return Path(__file__).resolve().parents[3]


def _strict_json_object_v1(content: bytes) -> dict[str, Any]:
    try:
        text = content.decode("utf-8")
        def pairs(values: list[tuple[str, Any]]) -> dict[str, Any]:
            result: dict[str, Any] = {}
            for key, value in values:
                if key in result:
                    _fail("DUPLICATE_JSON_KEY_REJECTED")
                result[key] = value
            return result
        value = json.loads(text, object_pairs_hook=pairs)
    except D2InnerExecutionV1Error:
        raise
    except BaseException:
        _fail("STRICT_JSON_REJECTED")
    if type(value) is not dict:
        _fail("JSON_OBJECT_REQUIRED")
    return value


def _canonical_self_hash_v1(document: Mapping[str, Any]) -> str:
    payload = dict(document)
    observed = payload.pop("artifact_hash", None)
    if type(observed) is not str or not re.fullmatch(r"[0-9a-f]{64}", observed):
        _fail("ARTIFACT_SELF_HASH_REJECTED")
    expected = stable_hash_v1(payload)
    if observed != expected:
        _fail("ARTIFACT_SELF_HASH_REJECTED")
    return expected


def _git_output_v1(arguments: Sequence[str]) -> bytes:
    try:
        result = subprocess.run(
            ["git", *arguments], cwd=_repository_root_v1(), check=True,
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
        )
        return result.stdout
    except BaseException:
        _fail("GIT_CUSTODY_REPLAY_REJECTED")


def _committed_bytes_v1(relative: str) -> bytes:
    return _git_output_v1(["show", f"{AUTHORIZATION_FREEZE_COMMIT}:{relative}"])


def _result_commit_bytes_v1(commit: str, relative: str) -> bytes:
    if commit not in {D0_PREDICTION_FREEZE_COMMIT, D1_PREDICTION_FREEZE_COMMIT}:
        _fail("FROZEN_RESULT_COMMIT_REJECTED")
    return _git_output_v1(["show", f"{commit}:{relative}"])


def _load_current_bytes_v1(relative: str) -> bytes:
    path = _repository_root_v1() / relative
    try:
        if path.is_symlink() or not path.is_file():
            _fail("TRACKED_AUTHORITY_FILE_REJECTED")
        return path.read_bytes()
    except D2InnerExecutionV1Error:
        raise
    except BaseException:
        _fail("TRACKED_AUTHORITY_FILE_REJECTED")


def _authorization_report_provenance_v1(content: bytes) -> str:
    try:
        marker = b"<!-- BEGIN D2 AUTHORIZATION REPORT PROVENANCE V1 -->"
        if content.count(marker) != 1:
            _fail("AUTHORIZATION_REPORT_PROVENANCE_REJECTED")
        body, footer = content.split(marker, 1)
        observed = re.search(rb"Report-Self-Hash: ([0-9a-f]{64})", footer)
        bundle = re.search(rb"Bundle-Hash: ([0-9a-f]{64})", footer)
        receipt = re.search(rb"Receipt-Hash: ([0-9a-f]{64})", footer)
        body_hash = sha256(body).hexdigest()
        if (
            observed is None or observed.group(1).decode() != AUTHORIZATION_REPORT_BODY_HASH
            or body_hash != AUTHORIZATION_REPORT_BODY_HASH
            or bundle is None or bundle.group(1).decode() != AUTHORIZATION_BUNDLE_HASH
            or receipt is None or receipt.group(1).decode() != AUTHORIZATION_RECEIPT_HASH
        ):
            _fail("AUTHORIZATION_REPORT_PROVENANCE_REJECTED")
        return body_hash
    except D2InnerExecutionV1Error:
        raise
    except BaseException:
        _fail("AUTHORIZATION_REPORT_PROVENANCE_REJECTED")


@dataclass(frozen=True)
class CommittedD2InnerExecutionGrantV1:
    authorization_freeze_commit: str
    authorization_version: str
    authorization_scope: str
    authorization_hash: str
    authorization_contract_hash: str
    authorization_independent_audit_hash: str
    authorization_preflight_hash: str
    authorization_accounting_hash: str
    authorization_readiness_hash: str
    authorization_bundle_hash: str
    authorization_receipt_hash: str
    authorization_report_body_hash: str
    d2_design_hash: str
    provenance_clarification_hash: str
    d0_prediction_hash: str
    d1_prediction_hash: str
    source_map_hash: str
    required_distinct_source_count: int
    same_second_policy: str
    d0_preservation_policy: str
    d0_rerun_authorized: bool
    d1_rerun_authorized: bool
    d0_score_access_authorized: bool
    d1_metric_read_authorized: bool
    test1_feature_access_authorized: bool
    test2_authorized: bool
    outer_authorized: bool
    grant_hash: str

    def _payload(self) -> dict[str, Any]:
        return {k: v for k, v in self.__dict__.items() if k != "grant_hash"}

    def __reduce__(self) -> object:
        _fail("COMMITTED_GRANT_SERIALIZATION_PROHIBITED")


_ISSUED_GRANTS: dict[int, tuple[weakref.ReferenceType[CommittedD2InnerExecutionGrantV1], str]] = {}


def _expected_grant_v1() -> CommittedD2InnerExecutionGrantV1:
    provisional = CommittedD2InnerExecutionGrantV1(
        AUTHORIZATION_FREEZE_COMMIT, AUTHORIZATION_VERSION, AUTHORIZATION_SCOPE,
        AUTHORIZATION_HASH, AUTHORIZATION_CONTRACT_HASH,
        AUTHORIZATION_INDEPENDENT_AUDIT_HASH, AUTHORIZATION_PREFLIGHT_HASH,
        AUTHORIZATION_ACCOUNTING_HASH, AUTHORIZATION_READINESS_HASH,
        AUTHORIZATION_BUNDLE_HASH, AUTHORIZATION_RECEIPT_HASH,
        AUTHORIZATION_REPORT_BODY_HASH, D2_DESIGN_HASH,
        PROVENANCE_CLARIFICATION_HASH, D0_PREDICTION_HASH, D1_PREDICTION_HASH,
        SOURCE_MAP_HASH, REQUIRED_DISTINCT_SOURCE_COUNT, SAME_SECOND_POLICY,
        D0_PRESERVATION_POLICY, False, False, False, False, False, False, False, "",
    )
    return replace(provisional, grant_hash=stable_hash_v1(provisional._payload()))


def _replay_committed_authorization_v1() -> None:
    reports = "docs/task_reports/"
    loaded: dict[str, dict[str, Any]] = {}
    for filename, expected_hash in AUTHORIZATION_ARTIFACTS.items():
        relative = reports + filename
        current = _load_current_bytes_v1(relative)
        if current != _committed_bytes_v1(relative):
            _fail("COMMITTED_AUTHORIZATION_BYTES_REJECTED")
        document = _strict_json_object_v1(current)
        if _canonical_self_hash_v1(document) != expected_hash:
            _fail("COMMITTED_AUTHORIZATION_HASH_REJECTED")
        loaded[filename] = document
    report_relative = reports + "TASK-039E3_R2R_UTILITY_INNER_D2_EXECUTION_AUTHORIZATION_V1_REPORT.md"
    report = _load_current_bytes_v1(report_relative)
    if report != _committed_bytes_v1(report_relative):
        _fail("COMMITTED_AUTHORIZATION_REPORT_BYTES_REJECTED")
    _authorization_report_provenance_v1(report)
    auth = loaded["TASK-039E3_R2R_UTILITY_INNER_D2_EXECUTION_AUTHORIZATION_V1_AUTHORIZATION.json"]
    receipt = loaded["TASK-039E3_R2R_UTILITY_INNER_D2_EXECUTION_AUTHORIZATION_V1_RECEIPT.json"]
    bundle = loaded["TASK-039E3_R2R_UTILITY_INNER_D2_EXECUTION_AUTHORIZATION_V1_BUNDLE.json"]
    readiness = loaded["TASK-039E3_R2R_UTILITY_INNER_D2_EXECUTION_AUTHORIZATION_V1_READINESS.json"]
    if (
        auth.get("authorization_version") != AUTHORIZATION_VERSION
        or auth.get("authorization_scope") != AUTHORIZATION_SCOPE
        or auth.get("d2_design_hash") != D2_DESIGN_HASH
        or auth.get("provenance_clarification_hash") != PROVENANCE_CLARIFICATION_HASH
        or auth.get("d0_prediction_hash") != D0_PREDICTION_HASH
        or auth.get("d1_prediction_hash") != D1_PREDICTION_HASH
        or auth.get("source_map_hash") != SOURCE_MAP_HASH
        or auth.get("required_distinct_source_count") != 2
        or auth.get("same_second_policy") != SAME_SECOND_POLICY
        or auth.get("d0_preservation_policy") != D0_PRESERVATION_POLICY
        or auth.get("d2_inner_execution_authorized") is not True
        or auth.get("d2_combined_prediction_authorized") is not True
        or auth.get("label_access_before_combined_prediction_freeze_authorized") is not False
        or auth.get("test1_feature_access_authorized") is not False
        or auth.get("d0_rerun_authorized") is not False
        or auth.get("d1_rerun_authorized") is not False
        or auth.get("d0_score_access_authorized") is not False
        or auth.get("rule_reevaluation_authorized") is not False
        or auth.get("fusion_change_authorized") is not False
        or auth.get("test2_authorized") is not False
        or auth.get("outer_authorized") is not False
    ):
        _fail("COMMITTED_AUTHORIZATION_SEMANTICS_REJECTED")
    if (
        receipt.get("bundle_hash") != AUTHORIZATION_BUNDLE_HASH
        or receipt.get("readiness_hash") != AUTHORIZATION_READINESS_HASH
        or receipt.get("authorization_hash") != AUTHORIZATION_HASH
        or receipt.get("d2_authorized") is not True
        or receipt.get("d2_executed") is not False
        or receipt.get("test2_authorized") is not False
        or receipt.get("outer_authorized") is not False
        or bundle.get("authorization_hash") != AUTHORIZATION_HASH
        or bundle.get("readiness_hash") != AUTHORIZATION_READINESS_HASH
        or readiness.get("authorization_hash") != AUTHORIZATION_HASH
        or readiness.get("d2_authorized") is not True
        or readiness.get("d2_executed") is not False
    ):
        _fail("COMMITTED_AUTHORIZATION_CROSS_BINDING_REJECTED")


def issue_committed_d2_inner_execution_grant_v1() -> CommittedD2InnerExecutionGrantV1:
    _replay_committed_authorization_v1()
    value = _expected_grant_v1()
    oid = id(value)
    _ISSUED_GRANTS[oid] = (
        weakref.ref(value, lambda _: _ISSUED_GRANTS.pop(oid, None)), value.grant_hash
    )
    return value


def validate_committed_d2_inner_execution_grant_v1(
    value: CommittedD2InnerExecutionGrantV1,
) -> str:
    issued = _ISSUED_GRANTS.get(id(value))
    if (
        type(value) is not CommittedD2InnerExecutionGrantV1
        or issued is None or issued[0]() is not value or issued[1] != value.grant_hash
        or value != _expected_grant_v1()
        or value.grant_hash != stable_hash_v1(value._payload())
    ):
        _fail("COMMITTED_D2_EXECUTION_GRANT_CUSTODY_REJECTED")
    _replay_committed_authorization_v1()
    return value.grant_hash


@dataclass(frozen=True, repr=False)
class _D2ExecutionTokenV1:
    grant_hash: str
    token_hash: str
    consumed: bool = field(default=False, compare=False)

    def __repr__(self) -> str:
        return "<_D2ExecutionTokenV1 REDACTED>"

    def __reduce__(self) -> object:
        _fail("D2_EXECUTION_TOKEN_SERIALIZATION_PROHIBITED")


_ISSUED_TOKENS: dict[int, tuple[weakref.ReferenceType[_D2ExecutionTokenV1], str, bool]] = {}
_TOKEN_ISSUED = False


def _issue_execution_token_v1(grant: CommittedD2InnerExecutionGrantV1) -> _D2ExecutionTokenV1:
    global _TOKEN_ISSUED
    validate_committed_d2_inner_execution_grant_v1(grant)
    if _TOKEN_ISSUED:
        _fail("D2_EXECUTION_TOKEN_ALREADY_ISSUED")
    _TOKEN_ISSUED = True
    token_hash = stable_hash_v1(
        {"artifact_type": "D2InnerExecutionTokenV1", "grant_hash": grant.grant_hash}
    )
    token = _D2ExecutionTokenV1(grant.grant_hash, token_hash)
    oid = id(token)
    _ISSUED_TOKENS[oid] = (
        weakref.ref(token, lambda _: _ISSUED_TOKENS.pop(oid, None)), token_hash, False
    )
    return token


def _validate_execution_token_v1(token: _D2ExecutionTokenV1) -> str:
    issued = _ISSUED_TOKENS.get(id(token))
    if (
        type(token) is not _D2ExecutionTokenV1 or issued is None
        or issued[0]() is not token or issued[1] != token.token_hash or issued[2]
    ):
        _fail("D2_EXECUTION_TOKEN_CUSTODY_REJECTED")
    return token.token_hash


def _consume_execution_token_v1(token: _D2ExecutionTokenV1) -> None:
    _validate_execution_token_v1(token)
    issued = _ISSUED_TOKENS[id(token)]
    _ISSUED_TOKENS[id(token)] = (issued[0], issued[1], True)


class D2ExecutionStateV1(str, Enum):
    NOT_STARTED = "NOT_STARTED"
    GRANT_REPLAYED = "GRANT_REPLAYED"
    INPUT_PREDICTIONS_VALIDATED = "INPUT_PREDICTIONS_VALIDATED"
    SOURCE_MAP_VALIDATED = "SOURCE_MAP_VALIDATED"
    FUSION_COMPUTED = "FUSION_COMPUTED"
    COMBINED_PREDICTION_FROZEN = "COMBINED_PREDICTION_FROZEN"
    LABEL_PARSED = "LABEL_PARSED"
    METRICS_COMPUTED = "METRICS_COMPUTED"
    RESULT_FROZEN = "RESULT_FROZEN"


@dataclass
class D2ExecutionStateMachineV1:
    state: D2ExecutionStateV1 = D2ExecutionStateV1.NOT_STARTED

    def transition(self, expected: D2ExecutionStateV1, target: D2ExecutionStateV1) -> None:
        if self.state is not expected:
            _fail("D2_EXECUTION_STATE_TRANSITION_REJECTED")
        self.state = target

    def require_label_access(self) -> None:
        if self.state is not D2ExecutionStateV1.COMBINED_PREDICTION_FROZEN:
            _fail("LABEL_BEFORE_COMBINED_PREDICTION_FREEZE_REJECTED")


@dataclass(frozen=True, repr=False)
class FrozenD0PredictionInputV1:
    artifact_hash: str
    raw_bytes_hash: str
    row_count: int
    point_alarm_count: int
    _alarms: tuple[bool, ...] = field(repr=False, compare=False)

    def __repr__(self) -> str:
        return "<FrozenD0PredictionInputV1 validated=True records=REDACTED>"


@dataclass(frozen=True)
class _FrozenD1AlarmRecordV1:
    decision_physical_row_index: int
    alarm_emitted: bool
    relation_binding_hash: str
    opportunity_id: str


@dataclass(frozen=True, repr=False)
class FrozenD1PredictionInputV1:
    artifact_hash: str
    raw_bytes_hash: str
    record_count: int
    _records: tuple[_FrozenD1AlarmRecordV1, ...] = field(repr=False, compare=False)

    def __repr__(self) -> str:
        return "<FrozenD1PredictionInputV1 validated=True records=REDACTED>"


@dataclass(frozen=True, repr=False)
class FrozenD2SourceMapV1:
    artifact_hash: str
    raw_bytes_hash: str
    entry_count: int
    unique_relation_count: int
    distinct_source_count: int
    _entries: tuple[tuple[str, str], ...] = field(repr=False, compare=False)

    def __repr__(self) -> str:
        return "<FrozenD2SourceMapV1 validated=True entries=REDACTED>"


def _sha256_bytes_v1(content: bytes) -> str:
    return sha256(content).hexdigest()


def _parse_frozen_d0_prediction_v1(token: _D2ExecutionTokenV1) -> FrozenD0PredictionInputV1:
    _validate_execution_token_v1(token)
    content = _load_current_bytes_v1(D0_PREDICTION_RELATIVE_PATH)
    if content != _result_commit_bytes_v1(
        D0_PREDICTION_FREEZE_COMMIT, D0_PREDICTION_RELATIVE_PATH
    ):
        _fail("D0_PREDICTION_COMMITTED_BYTES_REJECTED")
    document = _strict_json_object_v1(content)
    if set(document) != D0_ROOT_KEYS or _canonical_self_hash_v1(document) != D0_PREDICTION_HASH:
        _fail("D0_PREDICTION_DOCUMENT_REJECTED")
    records = document.get("prediction_records")
    if type(records) is not list or len(records) != EXPECTED_ROW_COUNT:
        _fail("D0_PREDICTION_CLOSURE_REJECTED")
    alarms: list[bool] = []
    for expected_index, record in enumerate(records):
        if type(record) is not dict or set(record) != D0_RECORD_KEYS:
            _fail("D0_PREDICTION_RECORD_SCHEMA_REJECTED")
        if type(record["physical_row_index"]) is not int or record["physical_row_index"] != expected_index:
            _fail("D0_PREDICTION_ROW_ORDER_REJECTED")
        if type(record["alarm_emitted"]) is not bool:
            _fail("D0_PREDICTION_ALARM_TYPE_REJECTED")
        if type(record["detector_decision_identity"]) is not str or not re.fullmatch(
            r"[0-9a-f]{64}", record["detector_decision_identity"]
        ):
            _fail("D0_PREDICTION_DECISION_IDENTITY_REJECTED")
        alarms.append(record["alarm_emitted"])
    if (
        document.get("artifact_type") != "ScientificDetectorPredictionArtifactV1"
        or document.get("label_blind") is not True
        or document.get("labels_accessed_before_prediction_freeze") is not False
        or document.get("row_count") != EXPECTED_ROW_COUNT
        or document.get("unique_row_count") != EXPECTED_ROW_COUNT
        or document.get("point_alarm_count") != sum(alarms)
    ):
        _fail("D0_PREDICTION_AUTHORITY_REJECTED")
    return FrozenD0PredictionInputV1(
        D0_PREDICTION_HASH, _sha256_bytes_v1(content), EXPECTED_ROW_COUNT,
        sum(alarms), tuple(alarms),
    )


def _parse_frozen_d1_prediction_v1(token: _D2ExecutionTokenV1) -> FrozenD1PredictionInputV1:
    _validate_execution_token_v1(token)
    content = _load_current_bytes_v1(D1_PREDICTION_RELATIVE_PATH)
    if content != _result_commit_bytes_v1(
        D1_PREDICTION_FREEZE_COMMIT, D1_PREDICTION_RELATIVE_PATH
    ):
        _fail("D1_PREDICTION_COMMITTED_BYTES_REJECTED")
    document = _strict_json_object_v1(content)
    if set(document) != D1_ROOT_KEYS or _canonical_self_hash_v1(document) != D1_PREDICTION_HASH:
        _fail("D1_PREDICTION_DOCUMENT_REJECTED")
    records = document.get("prediction_records")
    if type(records) is not list or len(records) != EXPECTED_D1_RECORD_COUNT:
        _fail("D1_PREDICTION_CLOSURE_REJECTED")
    parsed: list[_FrozenD1AlarmRecordV1] = []
    opportunity_ids: set[str] = set()
    for record in records:
        if type(record) is not dict or set(record) != D1_RECORD_KEYS:
            _fail("D1_PREDICTION_RECORD_SCHEMA_REJECTED")
        index = record["decision_physical_row_index"]
        alarm = record["alarm_emitted"]
        relation = record["relation_binding_hash"]
        opportunity = record["opportunity_id"]
        if type(index) is not int or not 0 <= index < EXPECTED_ROW_COUNT:
            _fail("D1_PREDICTION_PHYSICAL_INDEX_REJECTED")
        if type(alarm) is not bool:
            _fail("D1_PREDICTION_ALARM_TYPE_REJECTED")
        if type(relation) is not str or not re.fullmatch(r"[0-9a-f]{64}", relation):
            _fail("D1_PREDICTION_RELATION_BINDING_REJECTED")
        if type(opportunity) is not str or not re.fullmatch(r"[0-9a-f]{64}", opportunity):
            _fail("D1_PREDICTION_OPPORTUNITY_IDENTITY_REJECTED")
        if opportunity in opportunity_ids:
            _fail("D1_PREDICTION_DUPLICATE_OPPORTUNITY_REJECTED")
        opportunity_ids.add(opportunity)
        parsed.append(_FrozenD1AlarmRecordV1(index, alarm, relation, opportunity))
    if (
        document.get("artifact_type") != "task039e3_r2r_scientific_rule_prediction_artifact_v1"
        or document.get("label_blind") is not True
        or document.get("labels_accessed_before_prediction_freeze") is not False
        or document.get("common_portfolio") != "COMMON-42"
        or document.get("common_relation_count") != 42
        or document.get("scientific_eligible") is not True
    ):
        _fail("D1_PREDICTION_AUTHORITY_REJECTED")
    return FrozenD1PredictionInputV1(
        D1_PREDICTION_HASH, _sha256_bytes_v1(content), len(parsed), tuple(parsed)
    )


def _parse_frozen_source_map_v1(token: _D2ExecutionTokenV1) -> FrozenD2SourceMapV1:
    _validate_execution_token_v1(token)
    content = _load_current_bytes_v1(SOURCE_MAP_RELATIVE_PATH)
    document = _strict_json_object_v1(content)
    if _canonical_self_hash_v1(document) != SOURCE_MAP_HASH:
        _fail("SOURCE_MAP_HASH_REJECTED")
    records = document.get("entries")
    if type(records) is not list or len(records) != 42:
        _fail("SOURCE_MAP_CLOSURE_REJECTED")
    entries: list[tuple[str, str]] = []
    for record in records:
        if type(record) is not dict or set(record) != {
            "relation_binding_hash", "source_variable_identity"
        }:
            _fail("SOURCE_MAP_ENTRY_SCHEMA_REJECTED")
        relation = record["relation_binding_hash"]
        source = record["source_variable_identity"]
        if type(relation) is not str or not re.fullmatch(r"[0-9a-f]{64}", relation):
            _fail("SOURCE_MAP_RELATION_REJECTED")
        if type(source) is not str or not re.fullmatch(r"P1_[A-Z0-9]+", source):
            _fail("SOURCE_MAP_SOURCE_REJECTED")
        entries.append((relation, source))
    if (
        document.get("artifact_type") != "D2SourceResolutionMapV1"
        or document.get("d2_design_hash") != D2_DESIGN_HASH
        or document.get("source_resolution_policy") != SOURCE_RESOLUTION_POLICY
        or document.get("entry_count") != 42
        or document.get("unique_relation_count") != 42
        or document.get("distinct_source_count") != 9
        or len({relation for relation, _ in entries}) != 42
        or len({source for _, source in entries}) != 9
    ):
        _fail("SOURCE_MAP_AUTHORITY_REJECTED")
    return FrozenD2SourceMapV1(
        SOURCE_MAP_HASH, _sha256_bytes_v1(content), 42, 42, 9, tuple(entries)
    )


def fuse_point_v1(d0_alarm: bool, distinct_sources: frozenset[str]) -> tuple[bool, bool, str]:
    if type(d0_alarm) is not bool or type(distinct_sources) is not frozenset:
        _fail("FUSION_POINT_INPUT_REJECTED")
    if any(type(source) is not str or not source for source in distinct_sources):
        _fail("FUSION_SOURCE_IDENTITY_REJECTED")
    corroborated = len(distinct_sources) >= REQUIRED_DISTINCT_SOURCE_COUNT
    d2_alarm = d0_alarm or corroborated
    if not d0_alarm and not corroborated:
        trigger = "NONE"
    elif d0_alarm and not corroborated:
        trigger = "D0_ONLY"
    elif not d0_alarm and corroborated:
        trigger = "RULE_RECOVERY"
    else:
        trigger = "D0_AND_RULE_CORROBORATION"
    return corroborated, d2_alarm, trigger


def fuse_synthetic_timeline_v1(
    d0_alarms: tuple[bool, ...],
    d1_alarm_records: tuple[tuple[int, bool, str], ...],
    source_map: Mapping[str, str],
) -> tuple[tuple[bool, str, tuple[str, ...]], ...]:
    if type(d0_alarms) is not tuple or any(type(value) is not bool for value in d0_alarms):
        _fail("SYNTHETIC_D0_INPUT_REJECTED")
    if type(d1_alarm_records) is not tuple or type(source_map) is not dict:
        _fail("SYNTHETIC_D1_INPUT_REJECTED")
    per_row: list[set[str]] = [set() for _ in d0_alarms]
    for record in d1_alarm_records:
        if type(record) is not tuple or len(record) != 3:
            _fail("SYNTHETIC_D1_RECORD_REJECTED")
        index, alarm, relation = record
        if type(index) is not int or not 0 <= index < len(d0_alarms) or type(alarm) is not bool:
            _fail("SYNTHETIC_D1_RECORD_REJECTED")
        if relation not in source_map:
            _fail("UNRESOLVED_RELATION_BINDING_REJECTED")
        if alarm:
            per_row[index].add(source_map[relation])
    result = []
    for d0_alarm, sources in zip(d0_alarms, per_row):
        _, d2_alarm, trigger = fuse_point_v1(d0_alarm, frozenset(sources))
        result.append((d2_alarm, trigger, tuple(sorted(sources))))
    return tuple(result)


@dataclass(frozen=True, repr=False)
class D2FusionEvidenceV1:
    authorization_hash: str
    d2_design_hash: str
    d0_prediction_hash: str
    d1_prediction_hash: str
    source_map_hash: str
    physical_row_count: int
    corroboration_point_count: int
    rule_recovery_point_count: int
    fusion_evidence_hash: str
    _distinct_sources_by_row: tuple[tuple[str, ...], ...] = field(repr=False, compare=False)
    _corroboration: tuple[bool, ...] = field(repr=False, compare=False)
    _trigger_classes: tuple[str, ...] = field(repr=False, compare=False)
    _d2_alarms: tuple[bool, ...] = field(repr=False, compare=False)

    def __repr__(self) -> str:
        return "<D2FusionEvidenceV1 validated=True private_rows=REDACTED>"

    def __reduce__(self) -> object:
        _fail("D2_FUSION_EVIDENCE_SERIALIZATION_PROHIBITED")


def _build_fusion_evidence_v1(
    d0: FrozenD0PredictionInputV1,
    d1: FrozenD1PredictionInputV1,
    source_map: FrozenD2SourceMapV1,
) -> tuple[D2FusionEvidenceV1, dict[str, Any]]:
    mapping = dict(source_map._entries)
    per_row: list[set[str]] = [set() for _ in range(EXPECTED_ROW_COUNT)]
    for record in d1._records:
        source = mapping.get(record.relation_binding_hash)
        if source is None:
            _fail("UNRESOLVED_RELATION_BINDING_REJECTED")
        if record.alarm_emitted:
            per_row[record.decision_physical_row_index].add(source)
    source_rows = tuple(tuple(sorted(values)) for values in per_row)
    corroboration: list[bool] = []
    d2_alarms: list[bool] = []
    triggers: list[str] = []
    for d0_alarm, sources in zip(d0._alarms, source_rows):
        corroborated, d2_alarm, trigger = fuse_point_v1(d0_alarm, frozenset(sources))
        if d0_alarm and not d2_alarm:
            _fail("D0_PRESERVATION_REJECTED")
        corroboration.append(corroborated)
        d2_alarms.append(d2_alarm)
        triggers.append(trigger)
    payload = {
        "artifact_type": "D2FusionEvidenceV1",
        "schema_version": SCHEMA_VERSION,
        "authorization_hash": AUTHORIZATION_HASH,
        "d2_design_hash": D2_DESIGN_HASH,
        "d0_prediction_hash": D0_PREDICTION_HASH,
        "d1_prediction_hash": D1_PREDICTION_HASH,
        "source_map_hash": SOURCE_MAP_HASH,
        "physical_row_count": EXPECTED_ROW_COUNT,
        "distinct_sources_by_row": [list(values) for values in source_rows],
        "corroboration_by_row": corroboration,
        "trigger_classes_by_row": triggers,
        "d2_alarm_vector": d2_alarms,
    }
    document = {**payload, "artifact_hash": stable_hash_v1(payload)}
    evidence = D2FusionEvidenceV1(
        AUTHORIZATION_HASH, D2_DESIGN_HASH, D0_PREDICTION_HASH,
        D1_PREDICTION_HASH, SOURCE_MAP_HASH, EXPECTED_ROW_COUNT,
        sum(corroboration), sum(trigger == "RULE_RECOVERY" for trigger in triggers),
        document["artifact_hash"], source_rows, tuple(corroboration),
        tuple(triggers), tuple(d2_alarms),
    )
    return evidence, document


@dataclass(frozen=True)
class ScientificCombinedPredictionRecordV1:
    physical_row_index: int
    d2_alarm_emitted: bool
    trigger_class: str
    combined_decision_identity: str

    def to_public_dict(self) -> dict[str, Any]:
        return {
            "physical_row_index": self.physical_row_index,
            "d2_alarm_emitted": self.d2_alarm_emitted,
            "trigger_class": self.trigger_class,
            "combined_decision_identity": self.combined_decision_identity,
        }


def _combined_decision_identity_v1(index: int, alarm: bool, trigger: str) -> str:
    return stable_hash_v1(
        {
            "artifact_type": "task039e3_r2r_d2_combined_decision_identity_v1",
            "execution_implementation_identity": D2_INNER_EXECUTION_IMPLEMENTATION_IDENTITY,
            "authorization_hash": AUTHORIZATION_HASH,
            "d2_design_hash": D2_DESIGN_HASH,
            "d0_prediction_hash": D0_PREDICTION_HASH,
            "d1_prediction_hash": D1_PREDICTION_HASH,
            "source_map_hash": SOURCE_MAP_HASH,
            "physical_row_index": index,
            "d2_alarm_emitted": alarm,
            "trigger_class": trigger,
        }
    )


@dataclass(frozen=True)
class ScientificCombinedPredictionArtifactV1:
    artifact_type: str
    schema_version: str
    execution_version: str
    execution_mode: str
    execution_implementation_identity: str
    authorization_hash: str
    d2_id: str
    d2_design_hash: str
    provenance_clarification_hash: str
    d0_prediction_hash: str
    d1_prediction_hash: str
    source_map_hash: str
    fusion_evidence_hash: str
    dataset_manifest_id: str
    split_id: str
    row_count: int
    unique_row_count: int
    label_blind: bool
    labels_accessed_before_prediction_freeze: bool
    d0_preservation_validated: bool
    trigger_class_counts: tuple[tuple[str, int], ...]
    point_alarm_count: int
    records: tuple[ScientificCombinedPredictionRecordV1, ...]
    artifact_hash: str

    def _payload(self) -> dict[str, Any]:
        return {
            "artifact_type": self.artifact_type,
            "schema_version": self.schema_version,
            "execution_version": self.execution_version,
            "execution_mode": self.execution_mode,
            "execution_implementation_identity": self.execution_implementation_identity,
            "authorization_hash": self.authorization_hash,
            "d2_id": self.d2_id,
            "d2_design_hash": self.d2_design_hash,
            "provenance_clarification_hash": self.provenance_clarification_hash,
            "d0_prediction_hash": self.d0_prediction_hash,
            "d1_prediction_hash": self.d1_prediction_hash,
            "source_map_hash": self.source_map_hash,
            "fusion_evidence_hash": self.fusion_evidence_hash,
            "dataset_manifest_id": self.dataset_manifest_id,
            "split_id": self.split_id,
            "row_count": self.row_count,
            "unique_row_count": self.unique_row_count,
            "label_blind": self.label_blind,
            "labels_accessed_before_prediction_freeze": self.labels_accessed_before_prediction_freeze,
            "d0_preservation_validated": self.d0_preservation_validated,
            "trigger_class_counts": dict(self.trigger_class_counts),
            "point_alarm_count": self.point_alarm_count,
            "prediction_records": [record.to_public_dict() for record in self.records],
        }

    def to_public_dict(self) -> dict[str, Any]:
        return {**self._payload(), "artifact_hash": self.artifact_hash}


def _build_combined_prediction_v1(
    evidence: D2FusionEvidenceV1,
) -> ScientificCombinedPredictionArtifactV1:
    records = tuple(
        ScientificCombinedPredictionRecordV1(
            index, alarm, trigger,
            _combined_decision_identity_v1(index, alarm, trigger),
        )
        for index, (alarm, trigger) in enumerate(
            zip(evidence._d2_alarms, evidence._trigger_classes)
        )
    )
    counts = tuple((name, sum(item.trigger_class == name for item in records)) for name in TRIGGER_CLASSES)
    provisional = ScientificCombinedPredictionArtifactV1(
        "ScientificCombinedPredictionArtifactV1", SCHEMA_VERSION,
        D2_INNER_EXECUTION_VERSION, EXECUTION_MODE,
        D2_INNER_EXECUTION_IMPLEMENTATION_IDENTITY, AUTHORIZATION_HASH, D2_ID,
        D2_DESIGN_HASH, PROVENANCE_CLARIFICATION_HASH, D0_PREDICTION_HASH,
        D1_PREDICTION_HASH, SOURCE_MAP_HASH, evidence.fusion_evidence_hash,
        DATASET_MANIFEST_ID, INNER_SPLIT_ID, EXPECTED_ROW_COUNT,
        EXPECTED_ROW_COUNT, True, False, True, counts,
        sum(item.d2_alarm_emitted for item in records), records, "",
    )
    return replace(provisional, artifact_hash=stable_hash_v1(provisional._payload()))


def validate_combined_prediction_records_v1(
    records: tuple[ScientificCombinedPredictionRecordV1, ...], expected_count: int,
) -> None:
    if type(records) is not tuple or type(expected_count) is not int or expected_count < 0:
        _fail("COMBINED_PREDICTION_RECORDS_REJECTED")
    if len(records) != expected_count:
        _fail("COMBINED_PREDICTION_CLOSURE_REJECTED")
    for expected_index, record in enumerate(records):
        if type(record) is not ScientificCombinedPredictionRecordV1:
            _fail("COMBINED_PREDICTION_RECORD_TYPE_REJECTED")
        if record.physical_row_index != expected_index or type(record.physical_row_index) is not int:
            _fail("COMBINED_PREDICTION_ROW_ORDER_REJECTED")
        if type(record.d2_alarm_emitted) is not bool or record.trigger_class not in TRIGGER_CLASSES:
            _fail("COMBINED_PREDICTION_STATE_REJECTED")
        expected_alarm = record.trigger_class != "NONE"
        if record.d2_alarm_emitted is not expected_alarm:
            _fail("COMBINED_PREDICTION_TRIGGER_CONTRADICTION_REJECTED")
        if type(record.combined_decision_identity) is not str or not re.fullmatch(
            r"[0-9a-f]{64}", record.combined_decision_identity
        ):
            _fail("COMBINED_PREDICTION_DECISION_IDENTITY_REJECTED")
        if record.combined_decision_identity != _combined_decision_identity_v1(
            expected_index, record.d2_alarm_emitted, record.trigger_class
        ):
            _fail("COMBINED_PREDICTION_DECISION_IDENTITY_REJECTED")


def validate_scientific_combined_prediction_artifact_v1(
    artifact: ScientificCombinedPredictionArtifactV1,
) -> str:
    if type(artifact) is not ScientificCombinedPredictionArtifactV1:
        _fail("COMBINED_PREDICTION_TYPE_REJECTED")
    validate_combined_prediction_records_v1(artifact.records, EXPECTED_ROW_COUNT)
    if (
        artifact.artifact_type != "ScientificCombinedPredictionArtifactV1"
        or artifact.execution_version != D2_INNER_EXECUTION_VERSION
        or artifact.execution_mode != EXECUTION_MODE
        or artifact.authorization_hash != AUTHORIZATION_HASH
        or artifact.d2_design_hash != D2_DESIGN_HASH
        or artifact.d0_prediction_hash != D0_PREDICTION_HASH
        or artifact.d1_prediction_hash != D1_PREDICTION_HASH
        or artifact.source_map_hash != SOURCE_MAP_HASH
        or artifact.row_count != EXPECTED_ROW_COUNT
        or artifact.unique_row_count != EXPECTED_ROW_COUNT
        or artifact.label_blind is not True
        or artifact.labels_accessed_before_prediction_freeze is not False
        or artifact.d0_preservation_validated is not True
        or dict(artifact.trigger_class_counts) != {
            name: sum(record.trigger_class == name for record in artifact.records)
            for name in TRIGGER_CLASSES
        }
        or artifact.point_alarm_count != sum(record.d2_alarm_emitted for record in artifact.records)
        or artifact.artifact_hash != stable_hash_v1(artifact._payload())
    ):
        _fail("COMBINED_PREDICTION_ARTIFACT_REJECTED")
    return artifact.artifact_hash


def validate_scientific_combined_prediction_document_v1(document: Mapping[str, Any]) -> str:
    allowed_root = set(ScientificCombinedPredictionArtifactV1.__dataclass_fields__) - {"records"}
    allowed_root.add("prediction_records")
    if type(document) is not dict or set(document) != allowed_root:
        _fail("COMBINED_PREDICTION_DOCUMENT_SCHEMA_REJECTED")
    if _canonical_self_hash_v1(document) != document.get("artifact_hash"):
        _fail("COMBINED_PREDICTION_DOCUMENT_HASH_REJECTED")
    records = document.get("prediction_records")
    if type(records) is not list or len(records) != EXPECTED_ROW_COUNT:
        _fail("COMBINED_PREDICTION_DOCUMENT_CLOSURE_REJECTED")
    for index, record in enumerate(records):
        if type(record) is not dict or set(record) != COMBINED_RECORD_KEYS:
            _fail("COMBINED_PREDICTION_DOCUMENT_RECORD_SCHEMA_REJECTED")
        if record.get("physical_row_index") != index or type(record.get("physical_row_index")) is not int:
            _fail("COMBINED_PREDICTION_DOCUMENT_ROW_REJECTED")
        alarm = record.get("d2_alarm_emitted")
        trigger = record.get("trigger_class")
        if type(alarm) is not bool or trigger not in TRIGGER_CLASSES or alarm is (trigger == "NONE"):
            _fail("COMBINED_PREDICTION_DOCUMENT_STATE_REJECTED")
        if type(record.get("combined_decision_identity")) is not str or not re.fullmatch(
            r"[0-9a-f]{64}", record["combined_decision_identity"]
        ):
            _fail("COMBINED_PREDICTION_DOCUMENT_IDENTITY_REJECTED")
        if record["combined_decision_identity"] != _combined_decision_identity_v1(
            index, alarm, trigger
        ):
            _fail("COMBINED_PREDICTION_DOCUMENT_IDENTITY_REJECTED")
    expected_trigger_counts = {
        name: sum(record["trigger_class"] == name for record in records)
        for name in TRIGGER_CLASSES
    }
    if (
        document.get("artifact_type") != "ScientificCombinedPredictionArtifactV1"
        or document.get("schema_version") != SCHEMA_VERSION
        or document.get("execution_version") != D2_INNER_EXECUTION_VERSION
        or document.get("execution_mode") != EXECUTION_MODE
        or document.get("execution_implementation_identity")
        != D2_INNER_EXECUTION_IMPLEMENTATION_IDENTITY
        or document.get("authorization_hash") != AUTHORIZATION_HASH
        or document.get("d2_id") != D2_ID
        or document.get("d2_design_hash") != D2_DESIGN_HASH
        or document.get("provenance_clarification_hash")
        != PROVENANCE_CLARIFICATION_HASH
        or document.get("d0_prediction_hash") != D0_PREDICTION_HASH
        or document.get("d1_prediction_hash") != D1_PREDICTION_HASH
        or document.get("source_map_hash") != SOURCE_MAP_HASH
        or type(document.get("fusion_evidence_hash")) is not str
        or not re.fullmatch(r"[0-9a-f]{64}", document["fusion_evidence_hash"])
        or document.get("dataset_manifest_id") != DATASET_MANIFEST_ID
        or document.get("split_id") != INNER_SPLIT_ID
        or document.get("label_blind") is not True
        or document.get("labels_accessed_before_prediction_freeze") is not False
        or document.get("d0_preservation_validated") is not True
        or document.get("row_count") != EXPECTED_ROW_COUNT
        or document.get("unique_row_count") != EXPECTED_ROW_COUNT
        or document.get("trigger_class_counts") != expected_trigger_counts
        or document.get("point_alarm_count") != sum(record["d2_alarm_emitted"] for record in records)
    ):
        _fail("COMBINED_PREDICTION_DOCUMENT_AUTHORITY_REJECTED")
    return str(document["artifact_hash"])


def _public_json_bytes_v1(document: Mapping[str, Any]) -> bytes:
    return (
        json.dumps(document, sort_keys=True, indent=2, ensure_ascii=True, allow_nan=False)
        + "\n"
    ).encode("utf-8")


def _write_public_json_atomic_v1(relative: str, document: Mapping[str, Any]) -> bytes:
    root = _repository_root_v1().resolve()
    path = root / relative
    temporary = path.with_suffix(path.suffix + ".tmp")
    try:
        if path.exists() or path.is_symlink() or temporary.exists() or temporary.is_symlink():
            _fail("PUBLIC_ARTIFACT_ALREADY_EXISTS")
        content = _public_json_bytes_v1(document)
        path.parent.mkdir(parents=True, exist_ok=True)
        with temporary.open("xb") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        replay = path.read_bytes()
        if replay != content or _strict_json_object_v1(replay) != document:
            _fail("PUBLIC_ARTIFACT_REPLAY_REJECTED")
        _canonical_self_hash_v1(document)
        return replay
    except D2InnerExecutionV1Error:
        raise
    except BaseException:
        _fail("PUBLIC_ARTIFACT_WRITE_REJECTED")


def _persist_combined_prediction_before_label_v1(
    state: D2ExecutionStateMachineV1,
    artifact: ScientificCombinedPredictionArtifactV1,
) -> bytes:
    if state.state is not D2ExecutionStateV1.FUSION_COMPUTED:
        _fail("COMBINED_PREDICTION_PERSISTENCE_ORDER_REJECTED")
    validate_scientific_combined_prediction_artifact_v1(artifact)
    frozen = _write_public_json_atomic_v1(
        COMBINED_PREDICTION_RELATIVE_PATH, artifact.to_public_dict()
    )
    validate_scientific_combined_prediction_document_v1(_strict_json_object_v1(frozen))
    state.transition(
        D2ExecutionStateV1.FUSION_COMPUTED,
        D2ExecutionStateV1.COMBINED_PREDICTION_FROZEN,
    )
    return frozen


def _load_local_hai_root_v1() -> Path:
    binding = _repository_root_v1() / ".env.custody.local"
    try:
        if binding.is_symlink() or not binding.is_file():
            _fail("D2_LABEL_CUSTODY_UNAVAILABLE")
        values: dict[str, str] = {}
        for line in binding.read_text(encoding="utf-8").splitlines():
            match = re.fullmatch(r"([A-Z0-9_]+)='(.*)'", line)
            if match:
                values[match.group(1)] = match.group(2).replace("'\"'\"'", "'")
        root = Path(values["HAI_DATA_ROOT"])
        if root.is_symlink() or not root.is_dir():
            _fail("D2_LABEL_CUSTODY_UNAVAILABLE")
        return root
    except D2InnerExecutionV1Error:
        raise
    except BaseException:
        _fail("D2_LABEL_CUSTODY_UNAVAILABLE")


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
    except D2InnerExecutionV1Error:
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
            json.dumps(document, sort_keys=True, separators=(",", ":"),
                       ensure_ascii=True, allow_nan=False) + "\n"
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
    except D2InnerExecutionV1Error:
        raise
    except BaseException:
        _fail("PRIVATE_EVIDENCE_WRITE_REJECTED")


@dataclass(frozen=True, repr=False)
class D2LabelEventCustodyV1:
    label_file_sha256: str
    row_count: int
    strict_label_vector_hash: str
    attack_event_set_hash: str
    attack_event_count: int
    attack_labeled_seconds: int
    normal_labeled_seconds: int
    custody_hash: str
    _labels: tuple[int, ...] = field(repr=False, compare=False)
    _attack_events: tuple[metric_policy_v1.IntervalV1, ...] = field(repr=False, compare=False)

    def __repr__(self) -> str:
        return "<D2LabelEventCustodyV1 validated=True labels=REDACTED intervals=REDACTED>"

    def __reduce__(self) -> object:
        _fail("D2_LABEL_CUSTODY_SERIALIZATION_PROHIBITED")


def _interval_set_hash_v1(kind: str, intervals: tuple[metric_policy_v1.IntervalV1, ...]) -> str:
    return stable_hash_v1(
        {
            "artifact_type": f"task039e3_r2r_private_d2_{kind}_interval_set_v1",
            "interval_semantics": "HALF_OPEN_FILE_LOCAL_ONE_SECOND",
            "intervals": [{"start": item.start, "end": item.end} for item in intervals],
        }
    )


def _raw_sha256_once_v1(path: Path, expected_size: int) -> str:
    try:
        if path.is_symlink() or not path.is_file() or path.stat().st_size != expected_size:
            _fail("LABEL_RAW_IDENTITY_REJECTED")
        digest = sha256()
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()
    except D2InnerExecutionV1Error:
        raise
    except BaseException:
        _fail("LABEL_RAW_IDENTITY_REJECTED")


def _load_label_custody_once_v1(
    state: D2ExecutionStateMachineV1, label_path: Path,
) -> D2LabelEventCustodyV1:
    state.require_label_access()
    if _raw_sha256_once_v1(label_path, LABEL_BYTE_SIZE) != LABEL_SHA256:
        _fail("LABEL_HASH_REJECTED")
    label_tokens: list[str] = []
    try:
        with label_path.open("r", encoding="utf-8", newline="") as stream:
            reader = csv.reader(stream)
            if next(reader) != ["timestamp", "label"]:
                _fail("LABEL_HEADER_REJECTED")
            for row in reader:
                if len(row) != 2 or type(row[0]) is not str or not row[0]:
                    _fail("LABEL_ROW_REJECTED")
                label_tokens.append(row[1])
    except D2InnerExecutionV1Error:
        raise
    except BaseException:
        _fail("LABEL_PARSE_REJECTED")
    if len(label_tokens) != EXPECTED_ROW_COUNT:
        _fail("LABEL_ROW_COUNT_REJECTED")
    try:
        labels = protocol_v3.parse_raw_label_tokens_v3(tuple(label_tokens))
        attacks = metric_policy_v1.derive_attack_events_v1(labels)
    except BaseException:
        _fail("LABEL_VALUE_REJECTED")
    label_hash = stable_hash_v1(
        {
            "artifact_type": "task039e3_r2r_private_d2_strict_label_vector_v1",
            "label_file_sha256": LABEL_SHA256,
            "labels": list(labels),
        }
    )
    attack_hash = _interval_set_hash_v1("attack", attacks)
    payload = {
        "artifact_type": "D2LabelEventCustodyV1",
        "label_file_sha256": LABEL_SHA256,
        "row_count": EXPECTED_ROW_COUNT,
        "strict_label_vector_hash": label_hash,
        "attack_event_set_hash": attack_hash,
        "attack_event_count": len(attacks),
        "attack_event_policy": ATTACK_EVENT_POLICY,
    }
    custody = D2LabelEventCustodyV1(
        LABEL_SHA256, EXPECTED_ROW_COUNT, label_hash, attack_hash, len(attacks),
        sum(labels), EXPECTED_ROW_COUNT - sum(labels), stable_hash_v1(payload),
        labels, attacks,
    )
    state.transition(
        D2ExecutionStateV1.COMBINED_PREDICTION_FROZEN,
        D2ExecutionStateV1.LABEL_PARSED,
    )
    return custody


def _overlap_v1(left: metric_policy_v1.IntervalV1, right: metric_policy_v1.IntervalV1) -> bool:
    return left.start < right.end and right.start < left.end


def metric_counts_v1(
    attack_events: tuple[metric_policy_v1.IntervalV1, ...],
    episodes: tuple[metric_policy_v1.IntervalV1, ...],
) -> tuple[int, int]:
    if type(attack_events) is not tuple or type(episodes) is not tuple:
        _fail("METRIC_INPUT_TYPE_REJECTED")
    attacked = sum(any(_overlap_v1(event, alarm) for alarm in episodes) for event in attack_events)
    false_episodes = sum(not any(_overlap_v1(event, alarm) for event in attack_events) for alarm in episodes)
    return attacked, false_episodes


@dataclass(frozen=True)
class ScientificD2MetricV1:
    metric_name: str
    formula_identity: str
    value: float | None
    defined: bool
    undefined_reason: str | None
    private_evidence_hash: str
    metric_hash: str

    def to_public_dict(self) -> dict[str, Any]:
        return {
            "metric_name": self.metric_name,
            "formula_identity": self.formula_identity,
            "value": self.value,
            "defined": self.defined,
            "undefined_reason": self.undefined_reason,
            "private_evidence_hash": self.private_evidence_hash,
            "artifact_hash": self.metric_hash,
        }


def _metric_v1(
    name: str, formula: str, value: float | None, undefined_reason: str | None,
    private_evidence_hash: str,
) -> ScientificD2MetricV1:
    defined = value is not None
    payload = {
        "artifact_type": "ScientificD2MetricV1",
        "metric_name": name,
        "formula_identity": formula,
        "value": value,
        "defined": defined,
        "undefined_reason": None if defined else undefined_reason,
        "private_evidence_hash": private_evidence_hash,
    }
    return ScientificD2MetricV1(
        name, formula, value, defined, None if defined else undefined_reason,
        private_evidence_hash, stable_hash_v1(payload),
    )


def compute_metric_values_v1(
    attack_events: tuple[metric_policy_v1.IntervalV1, ...],
    d0_episodes: tuple[metric_policy_v1.IntervalV1, ...],
    d2_episodes: tuple[metric_policy_v1.IntervalV1, ...],
    recovery_episodes: tuple[metric_policy_v1.IntervalV1, ...],
    normal_seconds: int,
) -> dict[str, float | None]:
    if type(normal_seconds) is not int or normal_seconds < 0:
        _fail("NORMAL_EXPOSURE_REJECTED")
    d0_attacked, d0_false = metric_counts_v1(attack_events, d0_episodes)
    d2_attacked, d2_false = metric_counts_v1(attack_events, d2_episodes)
    recovery_attacked, recovery_false = metric_counts_v1(attack_events, recovery_episodes)
    del recovery_attacked
    missed = tuple(
        event for event in attack_events
        if not any(_overlap_v1(event, episode) for episode in d0_episodes)
    )
    recovered_missed = sum(
        any(_overlap_v1(event, episode) for episode in recovery_episodes)
        for event in missed
    )
    normal_hours = normal_seconds / 3600.0
    d0_recall = d0_attacked / len(attack_events) if attack_events else None
    d2_recall = d2_attacked / len(attack_events) if attack_events else None
    d0_far = d0_false / normal_hours if normal_hours else None
    d2_far = d2_false / normal_hours if normal_hours else None
    added_far = recovery_false / normal_hours if normal_hours else None
    return {
        "d2_recall": d2_recall,
        "d2_far": d2_far,
        "d0_missed_recovery": recovered_missed / len(missed) if missed else None,
        "incremental_recall": (
            d2_recall - d0_recall if d2_recall is not None and d0_recall is not None else None
        ),
        "added_recovery_far": added_far,
        "incremental_far": (
            d2_far - d0_far if d2_far is not None and d0_far is not None else None
        ),
    }


def _build_private_metric_evidence_v1(
    custody: D2LabelEventCustodyV1,
    d0_episodes: tuple[metric_policy_v1.IntervalV1, ...],
    d2_episodes: tuple[metric_policy_v1.IntervalV1, ...],
    recovery_episodes: tuple[metric_policy_v1.IntervalV1, ...],
    combined_hash: str,
    fusion_hash: str,
) -> tuple[dict[str, Any], dict[str, ScientificD2MetricV1]]:
    values = compute_metric_values_v1(
        custody._attack_events, d0_episodes, d2_episodes, recovery_episodes,
        custody.normal_labeled_seconds,
    )
    d0_attacked, d0_false = metric_counts_v1(custody._attack_events, d0_episodes)
    d2_attacked, d2_false = metric_counts_v1(custody._attack_events, d2_episodes)
    _, recovery_false = metric_counts_v1(custody._attack_events, recovery_episodes)
    missed = tuple(
        event for event in custody._attack_events
        if not any(_overlap_v1(event, episode) for episode in d0_episodes)
    )
    recovered_missed = sum(
        any(_overlap_v1(event, episode) for episode in recovery_episodes)
        for event in missed
    )
    payload = {
        "artifact_type": "D2MetricEvidenceV1",
        "schema_version": SCHEMA_VERSION,
        "authorization_hash": AUTHORIZATION_HASH,
        "d2_design_hash": D2_DESIGN_HASH,
        "combined_prediction_hash": combined_hash,
        "fusion_evidence_hash": fusion_hash,
        "label_vector_hash": custody.strict_label_vector_hash,
        "attack_event_set_hash": custody.attack_event_set_hash,
        "d0_alarm_episode_set_hash": _interval_set_hash_v1("d0_alarm", d0_episodes),
        "d2_alarm_episode_set_hash": _interval_set_hash_v1("d2_alarm", d2_episodes),
        "rule_recovery_episode_set_hash": _interval_set_hash_v1("rule_recovery", recovery_episodes),
        "private_counts": {
            "attack_event_count": len(custody._attack_events),
            "normal_labeled_seconds": custody.normal_labeled_seconds,
            "d0_attack_events_overlapped": d0_attacked,
            "d2_attack_events_overlapped": d2_attacked,
            "d0_false_alarm_episodes": d0_false,
            "d2_false_alarm_episodes": d2_false,
            "d0_missed_attack_events": len(missed),
            "d0_missed_recovered": recovered_missed,
            "rule_recovery_false_alarm_episodes": recovery_false,
        },
        "metric_values": values,
    }
    evidence = {**payload, "artifact_hash": stable_hash_v1(payload)}
    evidence_hash = str(evidence["artifact_hash"])
    metrics = {
        "d2_attack_event_recall": _metric_v1(
            "D2 Attack-event Recall", ATTACK_EVENT_RECALL_FORMULA,
            values["d2_recall"], "NO_ATTACK_EVENTS", evidence_hash,
        ),
        "d2_normal_far_episodes_per_hour": _metric_v1(
            "D2 Normal FAR episodes/hour", NORMAL_FAR_FORMULA,
            values["d2_far"], "NO_NORMAL_EXPOSURE", evidence_hash,
        ),
        "d0_missed_attack_recovery_rate": _metric_v1(
            "D0-missed Attack Recovery Rate", D0_MISSED_ATTACK_RECOVERY_FORMULA,
            values["d0_missed_recovery"], "NO_D0_MISSED_ATTACK_EVENTS", evidence_hash,
        ),
        "incremental_attack_event_recall": _metric_v1(
            "Incremental Attack-event Recall", INCREMENTAL_ATTACK_RECALL_FORMULA,
            values["incremental_recall"], "NO_ATTACK_EVENTS", evidence_hash,
        ),
        "added_normal_recovery_far_episodes_per_hour": _metric_v1(
            "Added Normal Recovery FAR episodes/hour", ADDED_NORMAL_RECOVERY_FAR_FORMULA,
            values["added_recovery_far"], "NO_NORMAL_EXPOSURE", evidence_hash,
        ),
        "incremental_normal_far_episodes_per_hour": _metric_v1(
            "Incremental Normal FAR episodes/hour", INCREMENTAL_NORMAL_FAR_FORMULA,
            values["incremental_far"], "NO_NORMAL_EXPOSURE", evidence_hash,
        ),
    }
    return evidence, metrics


@dataclass(frozen=True)
class D2InnerExecutionRunV1:
    committed_grant_hash: str
    authorization_hash: str
    execution_implementation_identity: str
    d2_design_hash: str
    provenance_clarification_hash: str
    d0_prediction_hash: str
    d1_prediction_hash: str
    source_map_hash: str
    fusion_evidence_hash: str
    combined_prediction_hash: str
    private_metric_evidence_hash: str
    metric_artifact_hash: str
    accounting_identity: str
    scientific_execution_attempts: int
    scientific_execution_retries: int
    test2_accesses: int
    run_hash: str

    def _payload(self) -> dict[str, Any]:
        return {k: v for k, v in self.__dict__.items() if k != "run_hash"}


@dataclass(frozen=True)
class D2InnerExecutionOutcomeV1:
    run: D2InnerExecutionRunV1
    combined_prediction: ScientificCombinedPredictionArtifactV1
    metrics: tuple[tuple[str, ScientificD2MetricV1], ...]
    fusion_evidence_hash: str
    private_metric_evidence_hash: str
    implementation_audit_hash: str
    accounting_hash: str
    readiness_hash: str
    bundle_hash: str
    receipt_hash: str


def _self_hashed_document_v1(payload: Mapping[str, Any]) -> dict[str, Any]:
    if "artifact_hash" in payload:
        _fail("PREHASHED_PUBLIC_PAYLOAD_REJECTED")
    document = dict(payload)
    document["artifact_hash"] = stable_hash_v1(document)
    return document


def _utc_now_v1() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _file_commit_custody_v1(relative: str) -> tuple[str, str, str]:
    content = _load_current_bytes_v1(relative)
    commit = _git_output_v1(["log", "-1", "--format=%H", "--", relative]).decode().strip()
    blob = _git_output_v1(["rev-parse", f"HEAD:{relative}"]).decode().strip()
    if not re.fullmatch(r"[0-9a-f]{40}", commit) or not re.fullmatch(r"[0-9a-f]{40}", blob):
        _fail("IMPLEMENTATION_CUSTODY_REJECTED")
    return commit, blob, _sha256_bytes_v1(content)


def _report_body_v1(
    combined: ScientificCombinedPredictionArtifactV1,
    metrics: Mapping[str, ScientificD2MetricV1],
    d2_episode_count: int,
    recovery_episode_count: int,
) -> str:
    counts = dict(combined.trigger_class_counts)
    return (
        "# TASK-039E3-R2R Utility INNER D2 Execution V1\n\n"
        f"Status: `{PASS_STATUS}`\n\n"
        f"Scientific status: `{SCIENTIFIC_STATUS}`\n\n"
        "The first and only authorized real INNER D2 frozen-prediction fusion completed "
        "exactly once. The result is frozen without interpretation, tuning, comparison, "
        "or remote egress.\n\n"
        f"- Authorization: `{AUTHORIZATION_HASH}`\n"
        f"- CombinedPrediction artifact: `{combined.artifact_hash}`\n"
        f"- D2 point alarm count: `{combined.point_alarm_count}`\n"
        f"- D2 alarm episode count: `{d2_episode_count}`\n"
        f"- RULE_RECOVERY point count: `{counts['RULE_RECOVERY']}`\n"
        f"- RULE_RECOVERY episode count: `{recovery_episode_count}`\n"
        f"- D2 Attack-event Recall: `{metrics['d2_attack_event_recall'].value}` "
        f"(defined: `{str(metrics['d2_attack_event_recall'].defined).lower()}`)\n"
        f"- D2 Normal FAR episodes/hour: `{metrics['d2_normal_far_episodes_per_hour'].value}` "
        f"(defined: `{str(metrics['d2_normal_far_episodes_per_hour'].defined).lower()}`)\n"
        f"- D0-missed Attack Recovery Rate: `{metrics['d0_missed_attack_recovery_rate'].value}` "
        f"(defined: `{str(metrics['d0_missed_attack_recovery_rate'].defined).lower()}`)\n"
        f"- Incremental Attack-event Recall: `{metrics['incremental_attack_event_recall'].value}`\n"
        f"- Added Normal Recovery FAR episodes/hour: "
        f"`{metrics['added_normal_recovery_far_episodes_per_hour'].value}`\n"
        f"- Incremental Normal FAR episodes/hour: "
        f"`{metrics['incremental_normal_far_episodes_per_hour'].value}`\n"
        "- D0 executions: `0`; D1 executions: `0`; test1 feature accesses: `0`; "
        "test2 accesses: `0`; OUTER executions: `0`.\n"
        "- Private paths, source sets, and label values exposed: `0`.\n\n"
        "Exact next task: "
        "`TASK-039E3-R2R-UTILITY-INNER-D2-RESULT-INTEGRITY-AUDIT-V1`.\n\n"
    )


def _write_report_atomic_v1(text: str) -> None:
    relative = "docs/task_reports/TASK-039E3_R2R_UTILITY_INNER_D2_EXECUTION_V1_REPORT.md"
    root = _repository_root_v1()
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
    except D2InnerExecutionV1Error:
        raise
    except BaseException:
        _fail("PUBLIC_REPORT_WRITE_REJECTED")


def _public_result_reports_v1(
    grant: CommittedD2InnerExecutionGrantV1,
    combined: ScientificCombinedPredictionArtifactV1,
    fusion_evidence_hash: str,
    private_metric_evidence_hash: str,
    metrics: Mapping[str, ScientificD2MetricV1],
    d2_episode_count: int,
    recovery_episode_count: int,
    provisional_run: D2InnerExecutionRunV1,
) -> tuple[D2InnerExecutionRunV1, str, str, str, str, str, str]:
    implementation_commit, implementation_blob, implementation_sha = _file_commit_custody_v1(
        "src/paperworks/v6/task039e3_r2r_d2_inner_execution_v1.py"
    )
    independent_commit, independent_blob, independent_sha = _file_commit_custody_v1(
        "tests/test_task039e3_r2r_d2_inner_execution_v1_independent.py"
    )
    created = _utc_now_v1()
    implementation_audit = _self_hashed_document_v1(
        {
            "artifact_type": "task039e3_r2r_d2_execution_v1_implementation_audit",
            "schema_version": SCHEMA_VERSION,
            "task_id": TASK_ID,
            "created_at_utc": created,
            "status": "PASS",
            "execution_implementation_identity": D2_INNER_EXECUTION_IMPLEMENTATION_IDENTITY,
            "execution_implementation_commit_a": implementation_commit,
            "execution_implementation_git_blob": implementation_blob,
            "execution_implementation_source_sha256": implementation_sha,
            "independent_audit_commit_b": independent_commit,
            "independent_audit_git_blob": independent_blob,
            "independent_audit_source_sha256": independent_sha,
            "static_suite_passed": True,
            "independent_suite_passed": True,
            "independent_attacks": EXPECTED_INDEPENDENT_ATTACKS,
            "accepted_invalid": 0,
            "differential_cases": DIFFERENTIAL_CASES,
            "differential_divergences": 0,
            "production_changes_after_commit_a": 0,
            "private_paths_exposed": 0,
            "private_source_sets_exposed": 0,
            "private_label_values_exposed": 0,
        }
    )
    metric_document = _self_hashed_document_v1(
        {
            "artifact_type": "task039e3_r2r_utility_inner_d2_metrics_v1",
            "schema_version": SCHEMA_VERSION,
            "task_id": TASK_ID,
            "created_at_utc": created,
            "execution_mode": EXECUTION_MODE,
            "d2_id": D2_ID,
            "d2_design_hash": D2_DESIGN_HASH,
            "authorization_hash": AUTHORIZATION_HASH,
            "d0_prediction_hash": D0_PREDICTION_HASH,
            "d1_prediction_hash": D1_PREDICTION_HASH,
            "combined_prediction_hash": combined.artifact_hash,
            "fusion_evidence_hash": fusion_evidence_hash,
            "point_alarm_count": combined.point_alarm_count,
            "alarm_episode_count": d2_episode_count,
            "rule_recovery_episode_count": recovery_episode_count,
            "trigger_class_counts": dict(combined.trigger_class_counts),
            "corroboration_point_count": (
                dict(combined.trigger_class_counts)["RULE_RECOVERY"]
                + dict(combined.trigger_class_counts)["D0_AND_RULE_CORROBORATION"]
            ),
            "metrics": {name: metric.to_public_dict() for name, metric in metrics.items()},
            "private_metric_evidence_hash": private_metric_evidence_hash,
            "attack_intervals_public": False,
            "label_vector_public": False,
            "private_event_evidence_public": False,
            "raw_rule_source_sets_public": False,
        }
    )
    accounting_identity = stable_hash_v1(
        {
            "artifact_type": "task039e3_r2r_d2_execution_v1_accounting_identity",
            "authorization_hash": AUTHORIZATION_HASH,
            "combined_prediction_hash": combined.artifact_hash,
            "scientific_execution_attempts": 1,
            "scientific_execution_retries": 0,
        }
    )
    run = replace(
        provisional_run,
        metric_artifact_hash=str(metric_document["artifact_hash"]),
        accounting_identity=accounting_identity,
    )
    run = replace(run, run_hash=stable_hash_v1(run._payload()))
    accounting = _self_hashed_document_v1(
        {
            "artifact_type": "task039e3_r2r_utility_inner_d2_execution_v1_accounting",
            "schema_version": SCHEMA_VERSION,
            "task_id": TASK_ID,
            "created_at_utc": created,
            "accounting_identity": accounting_identity,
            "execution_run_hash": run.run_hash,
            "scientific_execution_attempts": 1,
            "scientific_execution_retries": 0,
            "d0_prediction_parses": 1,
            "d1_prediction_parses": 1,
            "source_map_reads": 1,
            "fusion_computations": EXPECTED_ROW_COUNT,
            "combined_prediction_freezes": 1,
            "label_hash_reads": 1,
            "label_scientific_parses": 1,
            "label_before_combined_prediction_access": False,
            "attack_event_derivations": 1,
            "d2_alarm_episode_derivations": 1,
            "d0_reference_episode_derivations": 1,
            "rule_recovery_episode_derivations": 1,
            "primary_metric_computations": 2,
            "incremental_metric_computations": 4,
            "D0_executions": 0,
            "D1_executions": 0,
            "D1_metric_artifact_reads": 0,
            "D0_model_accesses": 0,
            "D0_score_accesses": 0,
            "D1_rule_reevaluations": 0,
            "D1_numeric_rule_authority_execution_accesses": 0,
            "test1_feature_accesses": 0,
            "test1_feature_parses": 0,
            "test2_accesses": 0,
            "OUTER_executions": 0,
            "result_driven_changes": False,
            "private_paths_exposed": 0,
            "private_source_sets_exposed": 0,
            "private_label_values_exposed": 0,
        }
    )
    body = _report_body_v1(combined, metrics, d2_episode_count, recovery_episode_count)
    report_body_hash = sha256(body.encode("utf-8")).hexdigest()
    readiness = _self_hashed_document_v1(
        {
            "artifact_type": "task039e3_r2r_utility_inner_d2_execution_v1_readiness",
            "schema_version": SCHEMA_VERSION,
            "task_id": TASK_ID,
            "created_at_utc": created,
            "status": "PASS",
            "scientific_state": SCIENTIFIC_STATUS,
            "authorization_hash": AUTHORIZATION_HASH,
            "committed_execution_grant_hash": grant.grant_hash,
            "execution_run_hash": run.run_hash,
            "implementation_audit_hash": implementation_audit["artifact_hash"],
            "combined_prediction_hash": combined.artifact_hash,
            "metric_artifact_hash": metric_document["artifact_hash"],
            "accounting_hash": accounting["artifact_hash"],
            "fusion_evidence_hash": fusion_evidence_hash,
            "private_metric_evidence_hash": private_metric_evidence_hash,
            "d2_executed": True,
            "d2_result_frozen": True,
            "d2_result_integrity_audited": False,
            "test2_accesses": 0,
            "outer_authorized": False,
            "remote_egress_status": "LOCAL_ONLY_NOT_PUSHED",
            "exact_next_task": "TASK-039E3-R2R-UTILITY-INNER-D2-RESULT-INTEGRITY-AUDIT-V1",
        }
    )
    bundle = _self_hashed_document_v1(
        {
            "artifact_type": "task039e3_r2r_utility_inner_d2_execution_v1_bundle",
            "schema_version": SCHEMA_VERSION,
            "task_id": TASK_ID,
            "status": "PASS",
            "authorization_hash": AUTHORIZATION_HASH,
            "committed_execution_grant_hash": grant.grant_hash,
            "execution_run_hash": run.run_hash,
            "implementation_audit_hash": implementation_audit["artifact_hash"],
            "combined_prediction_hash": combined.artifact_hash,
            "metric_artifact_hash": metric_document["artifact_hash"],
            "accounting_hash": accounting["artifact_hash"],
            "readiness_hash": readiness["artifact_hash"],
            "fusion_evidence_hash": fusion_evidence_hash,
            "private_metric_evidence_hash": private_metric_evidence_hash,
            "report_body_hash": report_body_hash,
            "report_hash_scheme": "MARKDOWN_BODY_SHA256_BEFORE_INTEGRITY_FOOTER_V1",
            "remote_egress_status": "LOCAL_ONLY_NOT_PUSHED",
        }
    )
    receipt = _self_hashed_document_v1(
        {
            "artifact_type": "task039e3_r2r_utility_inner_d2_execution_v1_receipt",
            "schema_version": SCHEMA_VERSION,
            "task_id": TASK_ID,
            "status": PASS_STATUS,
            "scientific_state": SCIENTIFIC_STATUS,
            "authorization_hash": AUTHORIZATION_HASH,
            "execution_run_hash": run.run_hash,
            "combined_prediction_hash": combined.artifact_hash,
            "bundle_hash": bundle["artifact_hash"],
            "readiness_hash": readiness["artifact_hash"],
            "report_body_hash": report_body_hash,
            "d2_executed": True,
            "d2_result_frozen": True,
            "d2_result_integrity_audited": False,
            "test2_accesses": 0,
            "outer_authorized": False,
            "push_attempted": False,
            "remote_egress_status": "LOCAL_ONLY_NOT_PUSHED",
            "blockers": [],
            "exact_next_task": "TASK-039E3-R2R-UTILITY-INNER-D2-RESULT-INTEGRITY-AUDIT-V1",
        }
    )
    footer = (
        "<!-- BEGIN D2 EXECUTION REPORT PROVENANCE V1 -->\n"
        "Report-Hash-Scheme: MARKDOWN_BODY_SHA256_BEFORE_INTEGRITY_FOOTER_V1\n"
        f"Report-Self-Hash: {report_body_hash}\n"
        f"Bundle-Hash: {bundle['artifact_hash']}\n"
        f"Receipt-Hash: {receipt['artifact_hash']}\n"
        "<!-- END D2 EXECUTION REPORT PROVENANCE V1 -->\n"
    )
    outputs = (
        ("docs/task_reports/TASK-039E3_R2R_UTILITY_INNER_D2_EXECUTION_V1_IMPLEMENTATION_AUDIT.json", implementation_audit),
        ("docs/task_reports/TASK-039E3_R2R_UTILITY_INNER_D2_METRICS_V1.json", metric_document),
        ("docs/task_reports/TASK-039E3_R2R_UTILITY_INNER_D2_EXECUTION_V1_ACCOUNTING.json", accounting),
        ("docs/task_reports/TASK-039E3_R2R_UTILITY_INNER_D2_EXECUTION_V1_READINESS.json", readiness),
        ("docs/task_reports/TASK-039E3_R2R_UTILITY_INNER_D2_EXECUTION_V1_BUNDLE.json", bundle),
        ("docs/task_reports/TASK-039E3_R2R_UTILITY_INNER_D2_EXECUTION_V1_RECEIPT.json", receipt),
    )
    for relative, document in outputs:
        _write_public_json_atomic_v1(relative, document)
    _write_report_atomic_v1(body + footer)
    return (
        run, str(implementation_audit["artifact_hash"]),
        str(accounting["artifact_hash"]), str(readiness["artifact_hash"]),
        str(bundle["artifact_hash"]), str(receipt["artifact_hash"]), report_body_hash,
    )


def reject_prohibited_operation_v1(operation: str) -> NoReturn:
    prohibited = {
        "d0_rerun", "d1_rerun", "d0_score_access", "d1_rule_reevaluation",
        "d1_metric_read", "test1_feature_access", "test2", "outer", "retry",
        "fusion_change", "fusion_candidate_search", "result_driven_change",
    }
    if operation in prohibited:
        _fail("PROHIBITED_D2_EXECUTION_OPERATION_REJECTED")
    _fail("UNKNOWN_D2_EXECUTION_OPERATION_REJECTED")


_REAL_ENTRY_ATTEMPTED = False
_SCIENTIFIC_EXECUTION_ATTEMPTS = 0
_SCIENTIFIC_EXECUTION_COMPLETED = False


def execute_authorized_d2_inner_v1() -> D2InnerExecutionOutcomeV1:
    """Execute the exact authorized D2 INNER fusion once, with no knobs."""

    global _REAL_ENTRY_ATTEMPTED, _SCIENTIFIC_EXECUTION_ATTEMPTS
    global _SCIENTIFIC_EXECUTION_COMPLETED
    if _REAL_ENTRY_ATTEMPTED or _SCIENTIFIC_EXECUTION_COMPLETED:
        _fail("REAL_D2_EXECUTION_ALREADY_ATTEMPTED")
    _REAL_ENTRY_ATTEMPTED = True
    state = D2ExecutionStateMachineV1()
    grant = issue_committed_d2_inner_execution_grant_v1()
    token = _issue_execution_token_v1(grant)
    state.transition(D2ExecutionStateV1.NOT_STARTED, D2ExecutionStateV1.GRANT_REPLAYED)

    _SCIENTIFIC_EXECUTION_ATTEMPTS = 1
    d0 = _parse_frozen_d0_prediction_v1(token)
    d1 = _parse_frozen_d1_prediction_v1(token)
    state.transition(
        D2ExecutionStateV1.GRANT_REPLAYED,
        D2ExecutionStateV1.INPUT_PREDICTIONS_VALIDATED,
    )
    source_map = _parse_frozen_source_map_v1(token)
    state.transition(
        D2ExecutionStateV1.INPUT_PREDICTIONS_VALIDATED,
        D2ExecutionStateV1.SOURCE_MAP_VALIDATED,
    )
    evidence, evidence_document = _build_fusion_evidence_v1(d0, d1, source_map)
    hai_root = _load_local_hai_root_v1()
    private_directory = _private_evidence_directory_v1(hai_root)
    fusion_evidence_hash = _write_private_json_atomic_v1(
        private_directory, "task039e3_inner_d2_fusion_evidence_v1.json", evidence_document
    )
    state.transition(
        D2ExecutionStateV1.SOURCE_MAP_VALIDATED,
        D2ExecutionStateV1.FUSION_COMPUTED,
    )
    combined = _build_combined_prediction_v1(evidence)
    frozen_combined_bytes = _persist_combined_prediction_before_label_v1(state, combined)

    label_path = hai_root / "hai-23.05" / LABEL_FILENAME
    custody = _load_label_custody_once_v1(state, label_path)
    combined_path = _repository_root_v1() / COMBINED_PREDICTION_RELATIVE_PATH
    metric_combined_bytes = combined_path.read_bytes()
    if metric_combined_bytes != frozen_combined_bytes:
        _fail("COMBINED_PREDICTION_BYTES_CHANGED_BEFORE_METRICS")
    combined_document = _strict_json_object_v1(metric_combined_bytes)
    validate_scientific_combined_prediction_document_v1(combined_document)
    d2_indices = tuple(
        int(record["physical_row_index"])
        for record in combined_document["prediction_records"]
        if record["d2_alarm_emitted"] is True
    )
    recovery_indices = tuple(
        int(record["physical_row_index"])
        for record in combined_document["prediction_records"]
        if record["trigger_class"] == "RULE_RECOVERY"
    )
    d2_episodes = metric_policy_v1.form_alarm_episodes_v1(d2_indices)
    recovery_episodes = metric_policy_v1.form_alarm_episodes_v1(recovery_indices)

    d0_reference_bytes = _load_current_bytes_v1(D0_PREDICTION_RELATIVE_PATH)
    if (
        _sha256_bytes_v1(d0_reference_bytes) != d0.raw_bytes_hash
        or d0_reference_bytes != _result_commit_bytes_v1(
            D0_PREDICTION_FREEZE_COMMIT, D0_PREDICTION_RELATIVE_PATH
        )
    ):
        _fail("D0_REFERENCE_PREDICTION_RELOAD_REJECTED")
    d0_indices = tuple(
        index for index, alarm in enumerate(d0._alarms) if alarm is True
    )
    d0_episodes = metric_policy_v1.form_alarm_episodes_v1(d0_indices)
    metric_evidence_document, metrics = _build_private_metric_evidence_v1(
        custody, d0_episodes, d2_episodes, recovery_episodes,
        combined.artifact_hash, fusion_evidence_hash,
    )
    private_metric_evidence_hash = _write_private_json_atomic_v1(
        private_directory, "task039e3_inner_d2_metric_evidence_v1.json",
        metric_evidence_document,
    )
    state.transition(D2ExecutionStateV1.LABEL_PARSED, D2ExecutionStateV1.METRICS_COMPUTED)
    provisional_run = D2InnerExecutionRunV1(
        grant.grant_hash, AUTHORIZATION_HASH, D2_INNER_EXECUTION_IMPLEMENTATION_IDENTITY,
        D2_DESIGN_HASH, PROVENANCE_CLARIFICATION_HASH, D0_PREDICTION_HASH,
        D1_PREDICTION_HASH, SOURCE_MAP_HASH, fusion_evidence_hash,
        combined.artifact_hash, private_metric_evidence_hash, "", "", 1, 0, 0, "",
    )
    (
        run, implementation_audit_hash, accounting_hash, readiness_hash,
        bundle_hash, receipt_hash, _report_hash,
    ) = _public_result_reports_v1(
        grant, combined, fusion_evidence_hash, private_metric_evidence_hash,
        metrics, len(d2_episodes), len(recovery_episodes), provisional_run,
    )
    if combined_path.read_bytes() != frozen_combined_bytes:
        _fail("COMBINED_PREDICTION_BYTES_CHANGED_AFTER_METRICS")
    if _sha256_bytes_v1(_load_current_bytes_v1(D0_PREDICTION_RELATIVE_PATH)) != d0.raw_bytes_hash:
        _fail("D0_PREDICTION_BYTES_CHANGED")
    if _sha256_bytes_v1(_load_current_bytes_v1(D1_PREDICTION_RELATIVE_PATH)) != d1.raw_bytes_hash:
        _fail("D1_PREDICTION_BYTES_CHANGED")
    if _sha256_bytes_v1(_load_current_bytes_v1(SOURCE_MAP_RELATIVE_PATH)) != source_map.raw_bytes_hash:
        _fail("SOURCE_MAP_BYTES_CHANGED")
    _consume_execution_token_v1(token)
    state.transition(D2ExecutionStateV1.METRICS_COMPUTED, D2ExecutionStateV1.RESULT_FROZEN)
    _SCIENTIFIC_EXECUTION_COMPLETED = True
    return D2InnerExecutionOutcomeV1(
        run, combined, tuple(metrics.items()), fusion_evidence_hash,
        private_metric_evidence_hash, implementation_audit_hash, accounting_hash,
        readiness_hash, bundle_hash, receipt_hash,
    )


__all__ = [
    "CommittedD2InnerExecutionGrantV1",
    "D2ExecutionStateMachineV1",
    "D2ExecutionStateV1",
    "D2FusionEvidenceV1",
    "D2InnerExecutionOutcomeV1",
    "D2InnerExecutionRunV1",
    "D2InnerExecutionV1Error",
    "D2LabelEventCustodyV1",
    "D2_INNER_EXECUTION_IMPLEMENTATION_IDENTITY",
    "D2_INNER_EXECUTION_VERSION",
    "DIFFERENTIAL_CASES",
    "EXPECTED_INDEPENDENT_ATTACKS",
    "FrozenD0PredictionInputV1",
    "FrozenD1PredictionInputV1",
    "FrozenD2SourceMapV1",
    "ScientificCombinedPredictionArtifactV1",
    "ScientificCombinedPredictionRecordV1",
    "ScientificD2MetricV1",
    "compute_metric_values_v1",
    "execute_authorized_d2_inner_v1",
    "fuse_point_v1",
    "fuse_synthetic_timeline_v1",
    "issue_committed_d2_inner_execution_grant_v1",
    "metric_counts_v1",
    "reject_prohibited_operation_v1",
    "validate_combined_prediction_records_v1",
    "validate_committed_d2_inner_execution_grant_v1",
    "validate_scientific_combined_prediction_artifact_v1",
    "validate_scientific_combined_prediction_document_v1",
]
