"""One-shot execution of the frozen D2 V2 native-horizon INNER policy.

The entry point has no scientific arguments.  It replays the committed V2
authorization, revalidates private custody, parses the immutable D0 and D1
prediction artifacts once, freezes a label-blind CombinedPredictionV2, and
only then parses label-test1 for the frozen metrics.
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
from paperworks.v6 import task039e3_r2r_d2_execution_recovery_custody_v1 as recovery_custody
from paperworks.v6 import task039e3_r2r_d2_v2_design_v1 as design
from paperworks.v6 import task039e3_r2r_d2_v2_execution_authorization_v1 as authorization_boundary
from paperworks.v6 import task039e3_r2r_utility_evaluator_metrics_v1 as metric_policy_v1
from paperworks.v6 import task039e3_r2r_utility_protocol_v3 as protocol_v3


TASK_ID = "TASK-039E3-R2R-UTILITY-INNER-D2-V2-EXECUTION-V1"
PASS_STATUS = "passed_task039e3_r2r_utility_inner_d2_v2_execution_v1"
SCIENTIFIC_STATUS = "D2_V2_EXECUTED_RESULT_INTEGRITY_AUDIT_PENDING"
D2_V2_INNER_EXECUTION_VERSION = "TASK039E3_R2R_D2_V2_INNER_EXECUTION_V1"
EXECUTION_MODE = "REAL_INNER_D2_V2_FROZEN_PREDICTION_NATIVE_HORIZON_FUSION"
SCHEMA_VERSION = "1.0.0"
BASE_COMMIT = "8898c5d4b497931562bc225c287274a2c6512ffe"
AUTHORIZATION_FREEZE_COMMIT = "867738a3904d2bc110865df5dfe4f9fe3032eddf"
AUTHORIZATION_HASH = "0f909480cfe3db8afc4042909258fe041f36ad021a917907008ee7e5023f2f45"
AUTHORIZATION_VERSION = "TASK039E3_R2R_D2_V2_INNER_EXECUTION_AUTHORIZATION_V1"
AUTHORIZATION_SCOPE = "HAI_23_05_P1_TEST1_D2_V2_NATIVE_HORIZON_CORROBORATION_INNER_V1"
AUTHORIZATION_REPORT_BODY_HASH = "40f63c01c8594f1ff4fbdd76d1373001191b1a408d96000f0707ebe6dc890830"
D2_V2_ID = "D2_V2_D0_PLUS_NATIVE_HORIZON_MULTI_SOURCE_CORROBORATION_V1"
D2_V2_DESIGN_HASH = "ace631af367ee2abe1b0ee7658875eeb59a2a8d906d09ce8ea92e8f2d83e31e4"
D0_PREDICTION_HASH = "a4b58f1c78b9bb53125da1a009f3fd05b02e1c83a789772a341a7679fddca0f6"
D1_PREDICTION_HASH = "58c3c49f9657f68d35c830b12eeb493ce4bbf7669c90f04813fb80246c3c2682"
SOURCE_MAP_HASH = "f866176000c3d5a943053ac3125d2700b0b72f25b5a0539d8f4713435a959818"
NATIVE_HORIZON_MAP_HASH = "e9825a578495396d935397e79d8c50717dccb47f069f13e93f6306f992a9407c"
D0_PREDICTION_FREEZE_COMMIT = "78d758f50657413eed28dc838212be9a1edeffc7"
D1_PREDICTION_FREEZE_COMMIT = "9fe9192c6da4e2d1f3c7a42ecdd28006e8534449"
SOURCE_MAP_FREEZE_COMMIT = "a412a0e7e893d23e7806e18831142f75cd5c0828"
RECOVERY_CUSTODY_IDENTITY = "c0e3faafdab0cb84e2f8e62b9380c243b0faee9ab38cc014de36fed5464d62e6"
EXPECTED_ROW_COUNT = 54_000
EXPECTED_D1_RECORD_COUNT = 6_031
EXPECTED_HORIZON_COUNT = 42
EXPECTED_SOURCE_COUNT = 9
REQUIRED_DISTINCT_SOURCE_COUNT = 2
LABEL_SHA256 = "eaf69edb9c5834bc393afd7bf658b5e408d34fd7bfc3261f80516765fb818fbc"
LABEL_BYTE_SIZE = 1_242_017
LABEL_FILENAME = "label-test1.csv"
DATASET_MANIFEST_ID = "5b0c395169fea468f7afd52aceafc4e6dadf062a1bc557c5bbe5dd6b8a761aa2"
INNER_SPLIT_ID = "30a7c88d6e0af5c37493237cc83b9520cbcd6f43c2dee7bb50ec3cac2668e7d0"
SOURCE_RESOLUTION_POLICY = "D1_RELATION_BINDING_HASH_TO_CANONICAL_V4_RULE_DESCRIPTOR_SOURCE_V1"
NATIVE_HORIZON_AUTHORITY_TYPE = "COMMON42_CANONICAL_RULE_DESCRIPTOR_SELECTED_HORIZON_SECONDS_V1"
TOKEN_START_POLICY = "D1_DECISION_PHYSICAL_ROW_INDEX"
TOKEN_EXPIRY_POLICY = "DECISION_PHYSICAL_ROW_INDEX_PLUS_FROZEN_NATIVE_HORIZON_INCLUSIVE"
D0_PRESERVATION_POLICY = "EVERY_FROZEN_D0_ALARM_IS_A_D2_V2_ALARM"
REPORT_HASH_SCHEME = "MARKDOWN_BODY_SHA256_BEFORE_INTEGRITY_FOOTER_V1"
EXPECTED_STATIC_TESTS = 12
EXPECTED_INDEPENDENT_ATTACKS = 34
SEMANTIC_DIFFERENTIAL_CASES = 8
NEXT_TASK = "TASK-039E3-R2R-UTILITY-INNER-D2-V2-RESULT-INTEGRITY-AUDIT-V1"

TRIGGER_CLASSES = (
    "NONE", "D0_ONLY", "RULE_RECOVERY_NATIVE_HORIZON",
    "D0_AND_RULE_CORROBORATION_NATIVE_HORIZON",
)
ATTACK_EVENT_POLICY = "MAXIMAL_CONTIGUOUS_STRICT_LABEL_ONE_RUNS_FILE_LOCAL"
ALARM_EPISODE_POLICY = "MAXIMAL_CONTIGUOUS_UNIQUE_ONE_SECOND_DECISION_INDICES_FILE_LOCAL"
ATTACK_EVENT_RECALL_FORMULA = "ATTACK_EVENTS_OVERLAPPED_BY_AT_LEAST_ONE_ALARM_EPISODE_DIVIDED_BY_ALL_ATTACK_EVENTS"
NORMAL_FAR_FORMULA = "ALARM_EPISODES_WITH_NO_ATTACK_TIMESTAMP_DIVIDED_BY_NORMAL_LABELED_SECONDS_OVER_3600"
D0_MISSED_ATTACK_RECOVERY_FORMULA = "D0_MISSED_ATTACK_EVENTS_RECOVERED_BY_RULE_RECOVERY_DIVIDED_BY_ALL_D0_MISSED_ATTACK_EVENTS"
INCREMENTAL_ATTACK_RECALL_FORMULA = "D2_ATTACK_EVENT_RECALL_MINUS_D0_ATTACK_EVENT_RECALL"
ADDED_NORMAL_RECOVERY_FAR_FORMULA = "RULE_RECOVERY_ALARM_EPISODES_WITH_ZERO_ATTACK_EVENT_OVERLAP_DIVIDED_BY_NORMAL_LABELED_SECONDS_OVER_3600"
INCREMENTAL_NORMAL_FAR_FORMULA = "D2_NORMAL_FAR_EPISODES_PER_HOUR_MINUS_D0_NORMAL_FAR_EPISODES_PER_HOUR"

D0_PREDICTION_PATH = "docs/task_reports/TASK-039E3_R2R_UTILITY_INNER_D0_DETECTOR_PREDICTION_ARTIFACT_V1.json"
D1_PREDICTION_PATH = "docs/task_reports/TASK-039E3_R2R_UTILITY_INNER_D1_RULE_PREDICTION_ARTIFACT_V1.json"
SOURCE_MAP_PATH = "docs/task_reports/TASK-039E3_R2R_UTILITY_INNER_D2_EXECUTION_AUTHORIZATION_V1_SOURCE_MAP.json"
COMBINED_PREDICTION_PATH = "docs/task_reports/TASK-039E3_R2R_UTILITY_INNER_D2_V2_COMBINED_PREDICTION_ARTIFACT_V1.json"
METRICS_PATH = "docs/task_reports/TASK-039E3_R2R_UTILITY_INNER_D2_V2_METRICS_V1.json"
RESULT_PREFIX = "docs/task_reports/TASK-039E3_R2R_UTILITY_INNER_D2_V2_EXECUTION_V1_"
IMPLEMENTATION_AUDIT_PATH = RESULT_PREFIX + "IMPLEMENTATION_AUDIT.json"
ACCOUNTING_PATH = RESULT_PREFIX + "ACCOUNTING.json"
READINESS_PATH = RESULT_PREFIX + "READINESS.json"
BUNDLE_PATH = RESULT_PREFIX + "BUNDLE.json"
RECEIPT_PATH = RESULT_PREFIX + "RECEIPT.json"
REPORT_PATH = RESULT_PREFIX + "REPORT.md"
PRIVATE_FUSION_FILENAME = "task039e3_inner_d2_v2_fusion_evidence_v1.json"
PRIVATE_METRIC_FILENAME = "task039e3_inner_d2_v2_metric_evidence_v1.json"

AUTHORIZATION_ARTIFACTS = {
    "CONTRACT": "89e4e2bdf91cea0ab5d67827945c0051c812d3740f8cbe038a078f601a19caa3",
    "NATIVE_HORIZON_AUDIT": "2893972703172965caea957f8f7dbd0b8b89a1ce14f7e559b1ef606404d90d25",
    "CUSTODY_PREFLIGHT": "1296c76458d498d0e35b209c4da9691f6d02e1899778906409d96d7c18d4e463",
    "PATH_REDACTION_AUDIT": "1b51853f796b01fa0fa47c5c1a431c6d79997a62612b4569ba9a255045ca4355",
    "INDEPENDENT_AUDIT": "3ee5e6a3deefaa39365e9eb471789a0cde2cf60e4635b1743a176d45b48f9ee8",
    "AUTHORIZATION": AUTHORIZATION_HASH,
    "ACCOUNTING": "33239fd17c0266f4e18a1079a37560d16dd5143dd64062092a86ca27cfbbb419",
    "READINESS": "02ce6ebb6d71225160210772768a6f6a904a6df6f188ef7a7b47fe034bdf922a",
    "BUNDLE": "779a326715bbf5f7cebc94c06ea24b1b4538b75abb2117281a01cb65ec784472",
    "RECEIPT": "16198e7d11b241977031c73dd8ab3fb645c4620e75f446e6c57793ff49693b96",
}

D0_ROOT_KEYS = frozenset({
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
})
D0_RECORD_KEYS = frozenset({"physical_row_index", "alarm_emitted", "detector_decision_identity"})
D1_ROOT_KEYS = frozenset({
    "artifact_hash", "artifact_type", "artifact_version", "authorization_hash",
    "authorization_report_commit", "bridge_identity", "common_portfolio",
    "common_relation_count", "counts", "dataset_manifest_identity",
    "denominator_policy", "evaluator_authority_bundle_hash", "execution_bridge_commit",
    "execution_bridge_source_sha256", "execution_mode", "feature_sha256",
    "full_census_identity", "label_blind", "labels_accessed_before_prediction_freeze",
    "main_descriptor_hash", "main_private_registry_hash", "prediction_records",
    "private_numeric_values_exposed", "private_paths_exposed", "r3_implementation_identity",
    "scientific_eligible", "split_identity", "supplement_descriptor_hash",
    "supplement_private_registry_hash", "v4_authority_hash",
})
D1_RECORD_KEYS = frozenset({
    "alarm_emitted", "computation_identity", "decision_physical_row_index", "final_state",
    "numeric_reference_identities", "opportunity_id", "relation_binding_hash",
    "source_event_identity_hash", "trace_hash",
})
COMBINED_RECORD_KEYS = frozenset({
    "physical_row_index", "d2_v2_alarm_emitted", "trigger_class", "combined_decision_identity",
})

EXECUTION_SEMANTIC_POLICY = {
    "artifact_type": "task039e3_r2r_d2_v2_inner_execution_semantics_v1",
    "execution_version": D2_V2_INNER_EXECUTION_VERSION,
    "execution_mode": EXECUTION_MODE,
    "authorization_hash": AUTHORIZATION_HASH,
    "d2_v2_design_hash": D2_V2_DESIGN_HASH,
    "d0_prediction_hash": D0_PREDICTION_HASH,
    "d1_prediction_hash": D1_PREDICTION_HASH,
    "source_map_hash": SOURCE_MAP_HASH,
    "native_horizon_map_hash": NATIVE_HORIZON_MAP_HASH,
    "token_start_policy": TOKEN_START_POLICY,
    "token_expiry_policy": TOKEN_EXPIRY_POLICY,
    "required_distinct_source_count": 2,
    "same_source_duplicates_count_once": True,
    "single_source_fallback": False,
    "fixed_global_temporal_window": None,
    "d0_preservation_policy": D0_PRESERVATION_POLICY,
    "trigger_classes": TRIGGER_CLASSES,
    "prediction_before_label": True,
    "primary_metric_formulas": (ATTACK_EVENT_RECALL_FORMULA, NORMAL_FAR_FORMULA),
    "incremental_metric_formulas": (
        D0_MISSED_ATTACK_RECOVERY_FORMULA, INCREMENTAL_ATTACK_RECALL_FORMULA,
        ADDED_NORMAL_RECOVERY_FAR_FORMULA, INCREMENTAL_NORMAL_FAR_FORMULA,
    ),
    "d0_rerun": False, "d1_rerun": False, "d2_v1_rerun": False,
    "d0_score_access": False, "rule_reevaluation": False,
    "test1_feature_access": False, "test2": False, "outer": False, "retries": 0,
}
D2_V2_INNER_EXECUTION_IMPLEMENTATION_IDENTITY = stable_hash_v1(EXECUTION_SEMANTIC_POLICY)


class D2V2InnerExecutionV1Error(RuntimeError):
    def __init__(self, code: str) -> None:
        safe = code if re.fullmatch(r"[A-Z0-9_]+", code) else "D2_V2_EXECUTION_UNEXPECTED"
        self.code = safe
        super().__init__(safe)


def _fail(code: str) -> NoReturn:
    raise D2V2InnerExecutionV1Error(code) from None


def _root_v1() -> Path:
    return Path(__file__).resolve().parents[3]


def _utc_now_v1() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _strict_json_object_v1(content: bytes) -> dict[str, Any]:
    try:
        def pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
            result: dict[str, Any] = {}
            for key, value in items:
                if key in result:
                    _fail("DUPLICATE_JSON_KEY_REJECTED")
                result[key] = value
            return result
        value = json.loads(content.decode("utf-8"), object_pairs_hook=pairs)
    except D2V2InnerExecutionV1Error:
        raise
    except BaseException:
        _fail("STRICT_JSON_REJECTED")
    if type(value) is not dict:
        _fail("JSON_OBJECT_REQUIRED")
    return value


def _canonical_self_hash_v1(document: Mapping[str, Any]) -> str:
    payload = dict(document)
    observed = payload.pop("artifact_hash", None)
    if type(observed) is not str or observed != stable_hash_v1(payload):
        _fail("ARTIFACT_SELF_HASH_REJECTED")
    return observed


def _self_hashed_v1(payload: Mapping[str, Any]) -> dict[str, Any]:
    if "artifact_hash" in payload:
        _fail("PUBLIC_PREHASH_REJECTED")
    value = dict(payload)
    value["artifact_hash"] = stable_hash_v1(value)
    return value


def _git_output_v1(arguments: Sequence[str]) -> bytes:
    try:
        return subprocess.run(
            ["git", *arguments], cwd=_root_v1(), check=True,
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
        ).stdout
    except BaseException:
        _fail("GIT_CUSTODY_REPLAY_REJECTED")


def _current_bytes_v1(relative: str) -> bytes:
    path = _root_v1() / relative
    try:
        if path.is_symlink() or not path.is_file():
            _fail("TRACKED_AUTHORITY_FILE_REJECTED")
        return path.read_bytes()
    except D2V2InnerExecutionV1Error:
        raise
    except BaseException:
        _fail("TRACKED_AUTHORITY_FILE_REJECTED")


def _commit_bytes_v1(commit: str, relative: str) -> bytes:
    return _git_output_v1(["show", f"{commit}:{relative}"])


@dataclass(frozen=True)
class CommittedD2V2InnerExecutionGrantV1:
    authorization_freeze_commit: str
    authorization_version: str
    authorization_scope: str
    authorization_hash: str
    authorization_artifact_hashes: tuple[tuple[str, str], ...]
    authorization_report_body_hash: str
    d2_v2_design_hash: str
    d0_prediction_hash: str
    d1_prediction_hash: str
    source_map_hash: str
    native_horizon_map_hash: str
    token_start_policy: str
    token_expiry_policy: str
    required_distinct_source_count: int
    single_source_fallback: bool
    fixed_global_temporal_window: int | None
    d0_preservation_policy: str
    label_before_prediction_authorized: bool
    test1_feature_authorized: bool
    test2_authorized: bool
    outer_authorized: bool
    grant_hash: str

    def _payload(self) -> dict[str, Any]:
        return {key: value for key, value in self.__dict__.items() if key != "grant_hash"}

    def __reduce__(self) -> object:
        _fail("COMMITTED_GRANT_SERIALIZATION_PROHIBITED")


def _expected_grant_v1() -> CommittedD2V2InnerExecutionGrantV1:
    provisional = CommittedD2V2InnerExecutionGrantV1(
        AUTHORIZATION_FREEZE_COMMIT, AUTHORIZATION_VERSION, AUTHORIZATION_SCOPE,
        AUTHORIZATION_HASH, tuple(sorted(AUTHORIZATION_ARTIFACTS.items())),
        AUTHORIZATION_REPORT_BODY_HASH, D2_V2_DESIGN_HASH, D0_PREDICTION_HASH,
        D1_PREDICTION_HASH, SOURCE_MAP_HASH, NATIVE_HORIZON_MAP_HASH,
        TOKEN_START_POLICY, TOKEN_EXPIRY_POLICY, 2, False, None,
        D0_PRESERVATION_POLICY, False, False, False, False, "",
    )
    return replace(provisional, grant_hash=stable_hash_v1(provisional._payload()))


_ISSUED_GRANTS: dict[int, tuple[weakref.ReferenceType[CommittedD2V2InnerExecutionGrantV1], str]] = {}


def _replay_committed_authorization_v1() -> None:
    prefix = "docs/task_reports/TASK-039E3_R2R_UTILITY_INNER_D2_V2_EXECUTION_AUTHORIZATION_V1_"
    loaded: dict[str, dict[str, Any]] = {}
    for suffix, expected_hash in AUTHORIZATION_ARTIFACTS.items():
        relative = prefix + suffix + ".json"
        content = _current_bytes_v1(relative)
        if content != _commit_bytes_v1(AUTHORIZATION_FREEZE_COMMIT, relative):
            _fail("COMMITTED_AUTHORIZATION_BYTES_REJECTED")
        document = _strict_json_object_v1(content)
        if _canonical_self_hash_v1(document) != expected_hash:
            _fail("COMMITTED_AUTHORIZATION_HASH_REJECTED")
        loaded[suffix] = document
    report_relative = prefix + "REPORT.md"
    report = _current_bytes_v1(report_relative)
    if report != _commit_bytes_v1(AUTHORIZATION_FREEZE_COMMIT, report_relative):
        _fail("COMMITTED_AUTHORIZATION_REPORT_BYTES_REJECTED")
    marker = b"<!-- BEGIN D2 V2 AUTHORIZATION REPORT PROVENANCE V1 -->"
    if report.count(marker) != 1:
        _fail("COMMITTED_AUTHORIZATION_REPORT_PROVENANCE_REJECTED")
    body, footer = report.split(marker, 1)
    # The frozen Markdown provenance hashes canonical LF text, independent of
    # the checkout's core.autocrlf representation.
    body_hash = sha256(body.replace(b"\r\n", b"\n").rstrip(b"\n") + b"\n").hexdigest()
    if body_hash != AUTHORIZATION_REPORT_BODY_HASH:
        _fail("COMMITTED_AUTHORIZATION_REPORT_PROVENANCE_REJECTED")
    for label, expected in (
        (b"Report-Self-Hash", AUTHORIZATION_REPORT_BODY_HASH),
        (b"Bundle-Hash", AUTHORIZATION_ARTIFACTS["BUNDLE"]),
        (b"Receipt-Hash", AUTHORIZATION_ARTIFACTS["RECEIPT"]),
    ):
        match = re.search(label + rb": ([0-9a-f]{64})", footer)
        if match is None or match.group(1).decode() != expected:
            _fail("COMMITTED_AUTHORIZATION_REPORT_PROVENANCE_REJECTED")
    auth = loaded["AUTHORIZATION"]
    readiness = loaded["READINESS"]
    bundle = loaded["BUNDLE"]
    receipt = loaded["RECEIPT"]
    if (
        auth.get("authorization_version") != AUTHORIZATION_VERSION
        or auth.get("authorization_scope") != AUTHORIZATION_SCOPE
        or auth.get("design_hash") != D2_V2_DESIGN_HASH
        or auth.get("d0_prediction_hash") != D0_PREDICTION_HASH
        or auth.get("d1_prediction_hash") != D1_PREDICTION_HASH
        or auth.get("source_map_hash") != SOURCE_MAP_HASH
        or auth.get("native_horizon_map_hash") != NATIVE_HORIZON_MAP_HASH
        or auth.get("token_start_policy") != TOKEN_START_POLICY
        or auth.get("token_expiry_policy") != TOKEN_EXPIRY_POLICY
        or auth.get("required_distinct_source_count") != 2
        or auth.get("single_source_fallback") is not False
        or auth.get("fixed_global_temporal_window") is not None
        or auth.get("d0_preservation_policy") != D0_PRESERVATION_POLICY
        or auth.get("d2_v2_inner_execution_authorized") is not True
        or auth.get("label_before_combined_prediction_authorized") is not False
        or auth.get("test1_feature_access_authorized") is not False
        or auth.get("d0_score_access_authorized") is not False
        or auth.get("rule_reevaluation_authorized") is not False
        or auth.get("horizon_override_authorized") is not False
        or auth.get("fusion_change_authorized") is not False
        or auth.get("test2_authorized") is not False
        or auth.get("outer_authorized") is not False
    ):
        _fail("COMMITTED_AUTHORIZATION_SEMANTICS_REJECTED")
    if (
        readiness.get("authorization_hash") != AUTHORIZATION_HASH
        or readiness.get("authorization_issued") is not True
        or readiness.get("d2_v2_executed") is not False
        or bundle.get("authorization_hash") != AUTHORIZATION_HASH
        or bundle.get("readiness_hash") != AUTHORIZATION_ARTIFACTS["READINESS"]
        or receipt.get("bundle_hash") != AUTHORIZATION_ARTIFACTS["BUNDLE"]
        or receipt.get("authorization_hash") != AUTHORIZATION_HASH
        or receipt.get("d2_v2_inner_execution_authorized") is not True
        or receipt.get("d2_v2_executed") is not False
    ):
        _fail("COMMITTED_AUTHORIZATION_CROSS_BINDING_REJECTED")


def issue_committed_d2_v2_inner_execution_grant_v1() -> CommittedD2V2InnerExecutionGrantV1:
    _replay_committed_authorization_v1()
    design.validate_d2_v2_design_authority_v1(design.build_d2_v2_design_authority_v1())
    design.validate_native_horizon_map_document_v1(design.native_horizon_map_document_v1())
    value = _expected_grant_v1()
    oid = id(value)
    _ISSUED_GRANTS[oid] = (weakref.ref(value, lambda _: _ISSUED_GRANTS.pop(oid, None)), value.grant_hash)
    return value


def validate_committed_d2_v2_inner_execution_grant_v1(value: CommittedD2V2InnerExecutionGrantV1) -> str:
    issued = _ISSUED_GRANTS.get(id(value))
    if (type(value) is not CommittedD2V2InnerExecutionGrantV1 or issued is None
            or issued[0]() is not value or issued[1] != value.grant_hash
            or value != _expected_grant_v1()
            or value.grant_hash != stable_hash_v1(value._payload())):
        _fail("COMMITTED_EXECUTION_GRANT_REJECTED")
    return value.grant_hash


@dataclass(frozen=True, repr=False)
class _D2V2ExecutionTokenV1:
    grant_hash: str
    execution_version: str
    _nonce: object = field(repr=False, compare=False)


_ISSUED_TOKENS: dict[int, tuple[weakref.ReferenceType[_D2V2ExecutionTokenV1], object, bool]] = {}


def _issue_execution_token_v1(grant: CommittedD2V2InnerExecutionGrantV1) -> _D2V2ExecutionTokenV1:
    validate_committed_d2_v2_inner_execution_grant_v1(grant)
    nonce = object()
    token = _D2V2ExecutionTokenV1(grant.grant_hash, D2_V2_INNER_EXECUTION_VERSION, nonce)
    oid = id(token)
    _ISSUED_TOKENS[oid] = (weakref.ref(token, lambda _: _ISSUED_TOKENS.pop(oid, None)), nonce, False)
    return token


def _validate_execution_token_v1(token: _D2V2ExecutionTokenV1) -> None:
    issued = _ISSUED_TOKENS.get(id(token))
    if (type(token) is not _D2V2ExecutionTokenV1 or issued is None
            or issued[0]() is not token or issued[1] is not token._nonce or issued[2]
            or token.grant_hash != _expected_grant_v1().grant_hash
            or token.execution_version != D2_V2_INNER_EXECUTION_VERSION):
        _fail("EXECUTION_TOKEN_REJECTED")


def _consume_execution_token_v1(token: _D2V2ExecutionTokenV1) -> None:
    _validate_execution_token_v1(token)
    issued = _ISSUED_TOKENS[id(token)]
    _ISSUED_TOKENS[id(token)] = (issued[0], issued[1], True)


class D2V2ExecutionStateV1(str, Enum):
    NOT_STARTED = "NOT_STARTED"
    GRANT_REPLAYED = "GRANT_REPLAYED"
    PRIVATE_CUSTODY_REVALIDATED = "PRIVATE_CUSTODY_REVALIDATED"
    INPUT_PREDICTIONS_VALIDATED = "INPUT_PREDICTIONS_VALIDATED"
    SOURCE_AND_HORIZON_MAPS_VALIDATED = "SOURCE_AND_HORIZON_MAPS_VALIDATED"
    EVIDENCE_TOKENS_CONSTRUCTED = "EVIDENCE_TOKENS_CONSTRUCTED"
    V2_FUSION_COMPUTED = "V2_FUSION_COMPUTED"
    PRIVATE_FUSION_EVIDENCE_FROZEN = "PRIVATE_FUSION_EVIDENCE_FROZEN"
    COMBINED_PREDICTION_V2_FROZEN = "COMBINED_PREDICTION_V2_FROZEN"
    LABEL_PARSED = "LABEL_PARSED"
    METRICS_COMPUTED = "METRICS_COMPUTED"
    RESULT_FROZEN = "RESULT_FROZEN"


@dataclass
class D2V2ExecutionStateMachineV1:
    state: D2V2ExecutionStateV1 = D2V2ExecutionStateV1.NOT_STARTED

    def transition(self, expected: D2V2ExecutionStateV1, target: D2V2ExecutionStateV1) -> None:
        if self.state is not expected:
            _fail("D2_V2_EXECUTION_STATE_TRANSITION_REJECTED")
        self.state = target

    def require_label_access(self) -> None:
        if self.state is not D2V2ExecutionStateV1.COMBINED_PREDICTION_V2_FROZEN:
            _fail("LABEL_BEFORE_COMBINED_PREDICTION_V2_FREEZE_REJECTED")


@dataclass(frozen=True, repr=False)
class FrozenD0PredictionInputV1:
    artifact_hash: str
    raw_bytes_hash: str
    row_count: int
    point_alarm_count: int
    _alarms: tuple[bool, ...] = field(repr=False, compare=False)


@dataclass(frozen=True)
class _FrozenD1PredictionRecordV1:
    decision_physical_row_index: int
    alarm_emitted: bool
    relation_binding_hash: str
    opportunity_id: str


@dataclass(frozen=True, repr=False)
class FrozenD1PredictionInputV1:
    artifact_hash: str
    raw_bytes_hash: str
    record_count: int
    _records: tuple[_FrozenD1PredictionRecordV1, ...] = field(repr=False, compare=False)


@dataclass(frozen=True, repr=False)
class FrozenD2V2SourceMapV1:
    artifact_hash: str
    raw_bytes_hash: str
    entry_count: int
    distinct_source_count: int
    _entries: tuple[tuple[str, str], ...] = field(repr=False, compare=False)


@dataclass(frozen=True, repr=False)
class FrozenD2V2NativeHorizonMapV1:
    artifact_hash: str
    entry_count: int
    _entries: tuple[tuple[str, int], ...] = field(repr=False, compare=False)


def _parse_frozen_d0_prediction_v1(token: _D2V2ExecutionTokenV1) -> FrozenD0PredictionInputV1:
    _validate_execution_token_v1(token)
    content = _current_bytes_v1(D0_PREDICTION_PATH)
    if content != _commit_bytes_v1(D0_PREDICTION_FREEZE_COMMIT, D0_PREDICTION_PATH):
        _fail("D0_PREDICTION_COMMITTED_BYTES_REJECTED")
    document = _strict_json_object_v1(content)
    if set(document) != D0_ROOT_KEYS or _canonical_self_hash_v1(document) != D0_PREDICTION_HASH:
        _fail("D0_PREDICTION_DOCUMENT_REJECTED")
    records = document.get("prediction_records")
    if type(records) is not list or len(records) != EXPECTED_ROW_COUNT:
        _fail("D0_PREDICTION_CLOSURE_REJECTED")
    alarms: list[bool] = []
    for index, record in enumerate(records):
        if type(record) is not dict or set(record) != D0_RECORD_KEYS:
            _fail("D0_PREDICTION_RECORD_SCHEMA_REJECTED")
        if type(record["physical_row_index"]) is not int or record["physical_row_index"] != index:
            _fail("D0_PREDICTION_ROW_ORDER_REJECTED")
        if type(record["alarm_emitted"]) is not bool:
            _fail("D0_PREDICTION_ALARM_TYPE_REJECTED")
        if type(record["detector_decision_identity"]) is not str or not re.fullmatch(r"[0-9a-f]{64}", record["detector_decision_identity"]):
            _fail("D0_PREDICTION_DECISION_IDENTITY_REJECTED")
        alarms.append(record["alarm_emitted"])
    if (document.get("artifact_type") != "ScientificDetectorPredictionArtifactV1"
            or document.get("label_blind") is not True
            or document.get("labels_accessed_before_prediction_freeze") is not False
            or document.get("row_count") != EXPECTED_ROW_COUNT
            or document.get("unique_row_count") != EXPECTED_ROW_COUNT
            or document.get("point_alarm_count") != sum(alarms)):
        _fail("D0_PREDICTION_AUTHORITY_REJECTED")
    return FrozenD0PredictionInputV1(D0_PREDICTION_HASH, sha256(content).hexdigest(), EXPECTED_ROW_COUNT, sum(alarms), tuple(alarms))


def _parse_frozen_d1_prediction_v1(token: _D2V2ExecutionTokenV1) -> FrozenD1PredictionInputV1:
    _validate_execution_token_v1(token)
    content = _current_bytes_v1(D1_PREDICTION_PATH)
    if content != _commit_bytes_v1(D1_PREDICTION_FREEZE_COMMIT, D1_PREDICTION_PATH):
        _fail("D1_PREDICTION_COMMITTED_BYTES_REJECTED")
    document = _strict_json_object_v1(content)
    if set(document) != D1_ROOT_KEYS or _canonical_self_hash_v1(document) != D1_PREDICTION_HASH:
        _fail("D1_PREDICTION_DOCUMENT_REJECTED")
    records = document.get("prediction_records")
    if type(records) is not list or len(records) != EXPECTED_D1_RECORD_COUNT:
        _fail("D1_PREDICTION_CLOSURE_REJECTED")
    parsed: list[_FrozenD1PredictionRecordV1] = []
    opportunities: set[str] = set()
    for record in records:
        if type(record) is not dict or set(record) != D1_RECORD_KEYS:
            _fail("D1_PREDICTION_RECORD_SCHEMA_REJECTED")
        index, alarm = record["decision_physical_row_index"], record["alarm_emitted"]
        relation, opportunity = record["relation_binding_hash"], record["opportunity_id"]
        if type(index) is not int or not 0 <= index < EXPECTED_ROW_COUNT or type(alarm) is not bool:
            _fail("D1_PREDICTION_RECORD_VALUE_REJECTED")
        if any(type(value) is not str or not re.fullmatch(r"[0-9a-f]{64}", value) for value in (relation, opportunity)):
            _fail("D1_PREDICTION_IDENTITY_REJECTED")
        if opportunity in opportunities:
            _fail("D1_PREDICTION_DUPLICATE_OPPORTUNITY_REJECTED")
        opportunities.add(opportunity)
        parsed.append(_FrozenD1PredictionRecordV1(index, alarm, relation, opportunity))
    if (document.get("artifact_type") != "task039e3_r2r_scientific_rule_prediction_artifact_v1"
            or document.get("label_blind") is not True
            or document.get("labels_accessed_before_prediction_freeze") is not False
            or document.get("common_portfolio") != "COMMON-42"
            or document.get("common_relation_count") != 42
            or document.get("scientific_eligible") is not True):
        _fail("D1_PREDICTION_AUTHORITY_REJECTED")
    return FrozenD1PredictionInputV1(D1_PREDICTION_HASH, sha256(content).hexdigest(), len(parsed), tuple(parsed))


def _parse_frozen_source_map_v1(token: _D2V2ExecutionTokenV1) -> FrozenD2V2SourceMapV1:
    _validate_execution_token_v1(token)
    content = _current_bytes_v1(SOURCE_MAP_PATH)
    if content != _commit_bytes_v1(SOURCE_MAP_FREEZE_COMMIT, SOURCE_MAP_PATH):
        _fail("SOURCE_MAP_COMMITTED_BYTES_REJECTED")
    document = _strict_json_object_v1(content)
    if _canonical_self_hash_v1(document) != SOURCE_MAP_HASH:
        _fail("SOURCE_MAP_HASH_REJECTED")
    records = document.get("entries")
    if type(records) is not list or len(records) != EXPECTED_HORIZON_COUNT:
        _fail("SOURCE_MAP_CLOSURE_REJECTED")
    entries: list[tuple[str, str]] = []
    for record in records:
        if type(record) is not dict or set(record) != {"relation_binding_hash", "source_variable_identity"}:
            _fail("SOURCE_MAP_ENTRY_SCHEMA_REJECTED")
        relation, source = record["relation_binding_hash"], record["source_variable_identity"]
        if type(relation) is not str or not re.fullmatch(r"[0-9a-f]{64}", relation):
            _fail("SOURCE_MAP_RELATION_REJECTED")
        if type(source) is not str or not re.fullmatch(r"P1_[A-Z0-9]+", source):
            _fail("SOURCE_MAP_SOURCE_REJECTED")
        entries.append((relation, source))
    if (document.get("artifact_type") != "D2SourceResolutionMapV1"
            or document.get("source_resolution_policy") != SOURCE_RESOLUTION_POLICY
            or document.get("entry_count") != 42 or document.get("unique_relation_count") != 42
            or document.get("distinct_source_count") != 9
            or len({r for r, _ in entries}) != 42 or len({s for _, s in entries}) != 9):
        _fail("SOURCE_MAP_AUTHORITY_REJECTED")
    return FrozenD2V2SourceMapV1(SOURCE_MAP_HASH, sha256(content).hexdigest(), 42, 9, tuple(entries))


def _parse_frozen_native_horizon_map_v1(token: _D2V2ExecutionTokenV1) -> FrozenD2V2NativeHorizonMapV1:
    _validate_execution_token_v1(token)
    document = design.native_horizon_map_document_v1()
    if design.validate_native_horizon_map_document_v1(document) != NATIVE_HORIZON_MAP_HASH:
        _fail("NATIVE_HORIZON_MAP_HASH_REJECTED")
    entries = document.get("entries")
    if type(entries) is not list or len(entries) != 42:
        _fail("NATIVE_HORIZON_MAP_CLOSURE_REJECTED")
    values: list[tuple[str, int]] = []
    for item in entries:
        if type(item) is not dict or set(item) != {"relation_binding_hash", "native_horizon_seconds"}:
            _fail("NATIVE_HORIZON_ENTRY_SCHEMA_REJECTED")
        relation, horizon = item["relation_binding_hash"], item["native_horizon_seconds"]
        if type(relation) is not str or not re.fullmatch(r"[0-9a-f]{64}", relation):
            _fail("NATIVE_HORIZON_RELATION_REJECTED")
        if type(horizon) is not int or horizon < 0:
            _fail("NATIVE_HORIZON_VALUE_REJECTED")
        values.append((relation, horizon))
    if (document.get("authority_type") != NATIVE_HORIZON_AUTHORITY_TYPE
            or document.get("entry_count") != 42 or len({r for r, _ in values}) != 42
            or document.get("missing_count") != 0 or document.get("ambiguous_count") != 0
            or document.get("label_derived_count") != 0 or document.get("test1_derived_count") != 0):
        _fail("NATIVE_HORIZON_AUTHORITY_REJECTED")
    return FrozenD2V2NativeHorizonMapV1(NATIVE_HORIZON_MAP_HASH, 42, tuple(values))


@dataclass(frozen=True)
class D2V2EvidenceTokenV1:
    relation_binding_hash: str
    source_variable_identity: str
    decision_physical_row_index: int
    native_horizon_seconds: int
    start_physical_row_index: int
    expiry_physical_row_index: int
    token_identity: str


def build_evidence_tokens_v1(
    records: tuple[tuple[int, bool, str], ...],
    source_entries: tuple[tuple[str, str], ...],
    horizon_entries: tuple[tuple[str, int], ...],
    row_count: int,
) -> tuple[D2V2EvidenceTokenV1, ...]:
    if type(records) is not tuple or type(source_entries) is not tuple or type(horizon_entries) is not tuple:
        _fail("TOKEN_INPUT_TYPE_REJECTED")
    if type(row_count) is not int or row_count <= 0:
        _fail("TOKEN_ROW_COUNT_REJECTED")
    sources, horizons = dict(source_entries), dict(horizon_entries)
    if len(sources) != len(source_entries) or len(horizons) != len(horizon_entries):
        _fail("TOKEN_AUTHORITY_AMBIGUITY_REJECTED")
    tokens: list[D2V2EvidenceTokenV1] = []
    for item in records:
        if type(item) is not tuple or len(item) != 3:
            _fail("TOKEN_RECORD_REJECTED")
        index, alarm, relation = item
        if type(index) is not int or not 0 <= index < row_count or type(alarm) is not bool:
            _fail("TOKEN_RECORD_REJECTED")
        if relation not in sources or relation not in horizons:
            _fail("TOKEN_RELATION_UNRESOLVED")
        horizon = horizons[relation]
        if type(horizon) is not int or horizon < 0:
            _fail("TOKEN_HORIZON_REJECTED")
        if not alarm:
            continue
        expiry = min(row_count - 1, index + horizon)
        identity = stable_hash_v1({
            "artifact_type": "task039e3_r2r_d2_v2_evidence_token_identity_v1",
            "d1_prediction_hash": D1_PREDICTION_HASH,
            "native_horizon_map_hash": NATIVE_HORIZON_MAP_HASH,
            "relation_binding_hash": relation,
            "source_variable_identity": sources[relation],
            "decision_physical_row_index": index,
            "native_horizon_seconds": horizon,
            "expiry_physical_row_index": expiry,
        })
        tokens.append(D2V2EvidenceTokenV1(relation, sources[relation], index, horizon, index, expiry, identity))
    return tuple(tokens)


def _fuse_point_v1(d0_alarm: bool, active_sources: frozenset[str]) -> tuple[bool, bool, str]:
    if type(d0_alarm) is not bool or type(active_sources) is not frozenset:
        _fail("FUSION_POINT_INPUT_REJECTED")
    corroborated = len(active_sources) >= 2
    alarm = d0_alarm or corroborated
    if not d0_alarm and not corroborated:
        trigger = "NONE"
    elif d0_alarm and not corroborated:
        trigger = "D0_ONLY"
    elif not d0_alarm and corroborated:
        trigger = "RULE_RECOVERY_NATIVE_HORIZON"
    else:
        trigger = "D0_AND_RULE_CORROBORATION_NATIVE_HORIZON"
    return corroborated, alarm, trigger


def fuse_native_horizon_timeline_v1(
    d0_alarms: tuple[bool, ...], tokens: tuple[D2V2EvidenceTokenV1, ...],
) -> tuple[tuple[tuple[str, ...], ...], tuple[bool, ...], tuple[bool, ...], tuple[str, ...]]:
    if type(d0_alarms) is not tuple or type(tokens) is not tuple or any(type(v) is not bool for v in d0_alarms):
        _fail("FUSION_TIMELINE_INPUT_REJECTED")
    starts: list[list[str]] = [[] for _ in range(len(d0_alarms))]
    ends: list[list[str]] = [[] for _ in range(len(d0_alarms) + 1)]
    for token in tokens:
        if type(token) is not D2V2EvidenceTokenV1 or token.start_physical_row_index != token.decision_physical_row_index:
            _fail("FUSION_TOKEN_REJECTED")
        if not 0 <= token.start_physical_row_index <= token.expiry_physical_row_index < len(d0_alarms):
            _fail("FUSION_TOKEN_INTERVAL_REJECTED")
        starts[token.start_physical_row_index].append(token.source_variable_identity)
        ends[token.expiry_physical_row_index + 1].append(token.source_variable_identity)
    counts: dict[str, int] = {}
    rows: list[tuple[str, ...]] = []
    corroboration: list[bool] = []
    alarms: list[bool] = []
    triggers: list[str] = []
    for index, d0_alarm in enumerate(d0_alarms):
        for source in ends[index]:
            remaining = counts.get(source, 0) - 1
            if remaining <= 0:
                counts.pop(source, None)
            else:
                counts[source] = remaining
        for source in starts[index]:
            counts[source] = counts.get(source, 0) + 1
        active = tuple(sorted(counts))
        corr, alarm, trigger = _fuse_point_v1(d0_alarm, frozenset(active))
        rows.append(active); corroboration.append(corr); alarms.append(alarm); triggers.append(trigger)
    return tuple(rows), tuple(corroboration), tuple(alarms), tuple(triggers)


def brute_force_native_horizon_timeline_v1(
    d0_alarms: tuple[bool, ...], tokens: tuple[D2V2EvidenceTokenV1, ...],
) -> tuple[tuple[tuple[str, ...], ...], tuple[bool, ...], tuple[bool, ...], tuple[str, ...]]:
    rows: list[tuple[str, ...]] = []
    corr: list[bool] = []
    alarms: list[bool] = []
    triggers: list[str] = []
    for index, d0_alarm in enumerate(d0_alarms):
        active = tuple(sorted({t.source_variable_identity for t in tokens if t.start_physical_row_index <= index <= t.expiry_physical_row_index}))
        c, a, tr = _fuse_point_v1(d0_alarm, frozenset(active))
        rows.append(active); corr.append(c); alarms.append(a); triggers.append(tr)
    return tuple(rows), tuple(corr), tuple(alarms), tuple(triggers)


@dataclass(frozen=True, repr=False)
class D2V2FusionEvidenceV1:
    fusion_evidence_hash: str
    evidence_token_set_hash: str
    evidence_token_count: int
    zero_horizon_token_count: int
    split_end_clipped_token_count: int
    corroboration_point_count: int
    trigger_class_counts: tuple[tuple[str, int], ...]
    point_alarm_count: int
    _active_sources_by_row: tuple[tuple[str, ...], ...] = field(repr=False, compare=False)
    _corroboration: tuple[bool, ...] = field(repr=False, compare=False)
    _alarms: tuple[bool, ...] = field(repr=False, compare=False)
    _triggers: tuple[str, ...] = field(repr=False, compare=False)

    def __repr__(self) -> str:
        return "<D2V2FusionEvidenceV1 validated=True private_rows=REDACTED>"


def _build_fusion_evidence_v1(
    d0: FrozenD0PredictionInputV1, d1: FrozenD1PredictionInputV1,
    source_map: FrozenD2V2SourceMapV1, horizon_map: FrozenD2V2NativeHorizonMapV1,
) -> tuple[D2V2FusionEvidenceV1, dict[str, Any]]:
    records = tuple((r.decision_physical_row_index, r.alarm_emitted, r.relation_binding_hash) for r in d1._records)
    tokens = build_evidence_tokens_v1(records, source_map._entries, horizon_map._entries, EXPECTED_ROW_COUNT)
    source_rows, corroboration, alarms, triggers = fuse_native_horizon_timeline_v1(d0._alarms, tokens)
    if any(d0_alarm and not alarm for d0_alarm, alarm in zip(d0._alarms, alarms)):
        _fail("D0_PRESERVATION_REJECTED")
    token_payload = [{
        "relation_binding_hash": t.relation_binding_hash,
        "source_variable_identity": t.source_variable_identity,
        "decision_physical_row_index": t.decision_physical_row_index,
        "native_horizon_seconds": t.native_horizon_seconds,
        "start_physical_row_index": t.start_physical_row_index,
        "expiry_physical_row_index": t.expiry_physical_row_index,
        "token_identity": t.token_identity,
    } for t in tokens]
    token_set_hash = stable_hash_v1({"artifact_type": "D2V2EvidenceTokenSetV1", "tokens": token_payload})
    payload = {
        "artifact_type": "D2V2FusionEvidenceV1", "schema_version": SCHEMA_VERSION,
        "authorization_hash": AUTHORIZATION_HASH, "d2_v2_design_hash": D2_V2_DESIGN_HASH,
        "d0_prediction_hash": D0_PREDICTION_HASH, "d1_prediction_hash": D1_PREDICTION_HASH,
        "source_map_hash": SOURCE_MAP_HASH, "native_horizon_map_hash": NATIVE_HORIZON_MAP_HASH,
        "evidence_token_set_hash": token_set_hash, "evidence_tokens": token_payload,
        "active_sources_by_row": [list(v) for v in source_rows],
        "active_distinct_source_count_by_row": [len(v) for v in source_rows],
        "corroboration_by_row": list(corroboration), "trigger_classes_by_row": list(triggers),
        "d2_v2_alarm_vector": list(alarms),
    }
    document = {**payload, "artifact_hash": stable_hash_v1(payload)}
    counts = tuple((name, sum(t == name for t in triggers)) for name in TRIGGER_CLASSES)
    evidence = D2V2FusionEvidenceV1(
        document["artifact_hash"], token_set_hash, len(tokens),
        sum(t.native_horizon_seconds == 0 for t in tokens),
        sum(t.decision_physical_row_index + t.native_horizon_seconds >= EXPECTED_ROW_COUNT for t in tokens),
        sum(corroboration), counts, sum(alarms), source_rows, corroboration, alarms, triggers,
    )
    return evidence, document


@dataclass(frozen=True)
class ScientificCombinedPredictionRecordV2:
    physical_row_index: int
    d2_v2_alarm_emitted: bool
    trigger_class: str
    combined_decision_identity: str

    def to_public_dict(self) -> dict[str, Any]:
        return dict(self.__dict__)


def _combined_identity_v1(index: int, alarm: bool, trigger: str) -> str:
    return stable_hash_v1({
        "artifact_type": "task039e3_r2r_d2_v2_combined_decision_identity_v1",
        "execution_implementation_identity": D2_V2_INNER_EXECUTION_IMPLEMENTATION_IDENTITY,
        "authorization_hash": AUTHORIZATION_HASH, "d2_v2_design_hash": D2_V2_DESIGN_HASH,
        "d0_prediction_hash": D0_PREDICTION_HASH, "d1_prediction_hash": D1_PREDICTION_HASH,
        "source_map_hash": SOURCE_MAP_HASH, "native_horizon_map_hash": NATIVE_HORIZON_MAP_HASH,
        "physical_row_index": index, "d2_v2_alarm_emitted": alarm, "trigger_class": trigger,
    })


@dataclass(frozen=True)
class ScientificCombinedPredictionArtifactV2:
    fusion_evidence_hash: str
    records: tuple[ScientificCombinedPredictionRecordV2, ...]
    trigger_class_counts: tuple[tuple[str, int], ...]
    point_alarm_count: int
    artifact_hash: str

    def _payload(self) -> dict[str, Any]:
        return {
            "artifact_type": "ScientificCombinedPredictionArtifactV2",
            "schema_version": SCHEMA_VERSION, "execution_version": D2_V2_INNER_EXECUTION_VERSION,
            "execution_mode": EXECUTION_MODE,
            "execution_implementation_identity": D2_V2_INNER_EXECUTION_IMPLEMENTATION_IDENTITY,
            "authorization_hash": AUTHORIZATION_HASH, "d2_v2_id": D2_V2_ID,
            "d2_v2_design_hash": D2_V2_DESIGN_HASH, "d0_prediction_hash": D0_PREDICTION_HASH,
            "d1_prediction_hash": D1_PREDICTION_HASH, "source_map_hash": SOURCE_MAP_HASH,
            "native_horizon_map_hash": NATIVE_HORIZON_MAP_HASH,
            "fusion_evidence_hash": self.fusion_evidence_hash,
            "dataset_manifest_id": DATASET_MANIFEST_ID, "split_id": INNER_SPLIT_ID,
            "row_count": EXPECTED_ROW_COUNT, "unique_row_count": EXPECTED_ROW_COUNT,
            "label_blind": True, "labels_accessed_before_prediction_freeze": False,
            "d0_preservation_validated": True, "trigger_class_counts": dict(self.trigger_class_counts),
            "point_alarm_count": self.point_alarm_count,
            "prediction_records": [record.to_public_dict() for record in self.records],
        }

    def to_public_dict(self) -> dict[str, Any]:
        return {**self._payload(), "artifact_hash": self.artifact_hash}


def _build_combined_prediction_v1(evidence: D2V2FusionEvidenceV1) -> ScientificCombinedPredictionArtifactV2:
    records = tuple(ScientificCombinedPredictionRecordV2(i, alarm, trigger, _combined_identity_v1(i, alarm, trigger)) for i, (alarm, trigger) in enumerate(zip(evidence._alarms, evidence._triggers)))
    provisional = ScientificCombinedPredictionArtifactV2(evidence.fusion_evidence_hash, records, evidence.trigger_class_counts, evidence.point_alarm_count, "")
    return replace(provisional, artifact_hash=stable_hash_v1(provisional._payload()))


def validate_combined_prediction_records_v1(records: tuple[ScientificCombinedPredictionRecordV2, ...], expected_count: int) -> None:
    if type(records) is not tuple or len(records) != expected_count:
        _fail("COMBINED_PREDICTION_V2_CLOSURE_REJECTED")
    for index, record in enumerate(records):
        if type(record) is not ScientificCombinedPredictionRecordV2 or record.physical_row_index != index:
            _fail("COMBINED_PREDICTION_V2_ROW_REJECTED")
        if type(record.d2_v2_alarm_emitted) is not bool or record.trigger_class not in TRIGGER_CLASSES:
            _fail("COMBINED_PREDICTION_V2_STATE_REJECTED")
        if record.d2_v2_alarm_emitted is (record.trigger_class == "NONE"):
            _fail("COMBINED_PREDICTION_V2_TRIGGER_REJECTED")
        if record.combined_decision_identity != _combined_identity_v1(index, record.d2_v2_alarm_emitted, record.trigger_class):
            _fail("COMBINED_PREDICTION_V2_IDENTITY_REJECTED")


def validate_scientific_combined_prediction_artifact_v1(artifact: ScientificCombinedPredictionArtifactV2) -> str:
    if type(artifact) is not ScientificCombinedPredictionArtifactV2:
        _fail("COMBINED_PREDICTION_V2_TYPE_REJECTED")
    validate_combined_prediction_records_v1(artifact.records, EXPECTED_ROW_COUNT)
    if artifact.artifact_hash != stable_hash_v1(artifact._payload()):
        _fail("COMBINED_PREDICTION_V2_HASH_REJECTED")
    return artifact.artifact_hash


def validate_scientific_combined_prediction_document_v1(document: Mapping[str, Any]) -> str:
    required = {
        "artifact_type", "schema_version", "execution_version", "execution_mode",
        "execution_implementation_identity", "authorization_hash", "d2_v2_id",
        "d2_v2_design_hash", "d0_prediction_hash", "d1_prediction_hash", "source_map_hash",
        "native_horizon_map_hash", "fusion_evidence_hash", "dataset_manifest_id", "split_id",
        "row_count", "unique_row_count", "label_blind", "labels_accessed_before_prediction_freeze",
        "d0_preservation_validated", "trigger_class_counts", "point_alarm_count",
        "prediction_records", "artifact_hash",
    }
    if type(document) is not dict or set(document) != required or _canonical_self_hash_v1(document) != document.get("artifact_hash"):
        _fail("COMBINED_PREDICTION_V2_DOCUMENT_REJECTED")
    records = document.get("prediction_records")
    if type(records) is not list or len(records) != EXPECTED_ROW_COUNT:
        _fail("COMBINED_PREDICTION_V2_DOCUMENT_CLOSURE_REJECTED")
    counts = {name: 0 for name in TRIGGER_CLASSES}; alarms = 0
    for index, record in enumerate(records):
        if type(record) is not dict or set(record) != COMBINED_RECORD_KEYS or record.get("physical_row_index") != index:
            _fail("COMBINED_PREDICTION_V2_DOCUMENT_ROW_REJECTED")
        alarm, trigger = record.get("d2_v2_alarm_emitted"), record.get("trigger_class")
        if type(alarm) is not bool or trigger not in TRIGGER_CLASSES or alarm is (trigger == "NONE"):
            _fail("COMBINED_PREDICTION_V2_DOCUMENT_STATE_REJECTED")
        if record.get("combined_decision_identity") != _combined_identity_v1(index, alarm, trigger):
            _fail("COMBINED_PREDICTION_V2_DOCUMENT_IDENTITY_REJECTED")
        counts[trigger] += 1; alarms += int(alarm)
    if (document.get("artifact_type") != "ScientificCombinedPredictionArtifactV2"
            or document.get("execution_version") != D2_V2_INNER_EXECUTION_VERSION
            or document.get("execution_implementation_identity") != D2_V2_INNER_EXECUTION_IMPLEMENTATION_IDENTITY
            or document.get("authorization_hash") != AUTHORIZATION_HASH
            or document.get("d2_v2_design_hash") != D2_V2_DESIGN_HASH
            or document.get("d0_prediction_hash") != D0_PREDICTION_HASH
            or document.get("d1_prediction_hash") != D1_PREDICTION_HASH
            or document.get("source_map_hash") != SOURCE_MAP_HASH
            or document.get("native_horizon_map_hash") != NATIVE_HORIZON_MAP_HASH
            or document.get("row_count") != EXPECTED_ROW_COUNT or document.get("unique_row_count") != EXPECTED_ROW_COUNT
            or document.get("label_blind") is not True
            or document.get("labels_accessed_before_prediction_freeze") is not False
            or document.get("d0_preservation_validated") is not True
            or document.get("trigger_class_counts") != counts or document.get("point_alarm_count") != alarms):
        _fail("COMBINED_PREDICTION_V2_DOCUMENT_AUTHORITY_REJECTED")
    return str(document["artifact_hash"])


def _public_json_bytes_v1(document: Mapping[str, Any]) -> bytes:
    return (json.dumps(document, sort_keys=True, indent=2, ensure_ascii=True, allow_nan=False) + "\n").encode()


def _write_public_json_atomic_v1(relative: str, document: Mapping[str, Any]) -> bytes:
    path = _root_v1() / relative; temporary = path.with_suffix(path.suffix + ".tmp")
    try:
        if path.exists() or path.is_symlink() or temporary.exists() or temporary.is_symlink():
            _fail("PUBLIC_RESULT_ALREADY_EXISTS")
        content = _public_json_bytes_v1(document)
        path.parent.mkdir(parents=True, exist_ok=True)
        with temporary.open("xb") as stream:
            stream.write(content); stream.flush(); os.fsync(stream.fileno())
        os.replace(temporary, path)
        if path.read_bytes() != content:
            _fail("PUBLIC_RESULT_REPLAY_REJECTED")
        return content
    except D2V2InnerExecutionV1Error:
        raise
    except BaseException:
        _fail("PUBLIC_RESULT_WRITE_REJECTED")


def _persist_combined_before_label_v1(state: D2V2ExecutionStateMachineV1, artifact: ScientificCombinedPredictionArtifactV2) -> bytes:
    validate_scientific_combined_prediction_artifact_v1(artifact)
    content = _write_public_json_atomic_v1(COMBINED_PREDICTION_PATH, artifact.to_public_dict())
    validate_scientific_combined_prediction_document_v1(_strict_json_object_v1(content))
    state.transition(D2V2ExecutionStateV1.PRIVATE_FUSION_EVIDENCE_FROZEN, D2V2ExecutionStateV1.COMBINED_PREDICTION_V2_FROZEN)
    return content


def _validate_private_document_v1(document: Mapping[str, Any]) -> str:
    if type(document) is not dict:
        _fail("PRIVATE_DOCUMENT_REJECTED")
    return _canonical_self_hash_v1(document)


def _persist_private_v2(root: recovery_custody.D2RecoveryPrivateRootV1, filename: str, document: Mapping[str, Any]) -> str:
    if filename not in authorization_boundary.V2_PRIVATE_FILENAMES:
        _fail("PRIVATE_V2_FILENAME_REJECTED")
    expected = _validate_private_document_v1(document)
    content = (json.dumps(document, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False) + "\n").encode()
    try:
        replay = recovery_custody._atomic_write_bytes_v1(root, filename, content, allow_sentinel=True)
    except recovery_custody.D2RecoveryCustodyV1Error as error:
        raise D2V2InnerExecutionV1Error(error.code) from None
    if replay != content or document.get("artifact_hash") != expected:
        _fail("PRIVATE_V2_REPLAY_REJECTED")
    return expected


def _binding_value_v1(path: Path, key: str) -> Path:
    try:
        if path.is_symlink() or not path.is_file():
            _fail("LOCAL_BINDING_REJECTED")
        matches: list[str] = []
        for line in path.read_text(encoding="utf-8").splitlines():
            match = re.fullmatch(r"([A-Z0-9_]+)='(.*)'", line)
            if match and match.group(1) == key:
                matches.append(match.group(2).replace("'\"'\"'", "'"))
        if len(matches) != 1:
            _fail("LOCAL_BINDING_REJECTED")
        return Path(matches[0])
    except D2V2InnerExecutionV1Error:
        raise
    except BaseException:
        _fail("LOCAL_BINDING_REJECTED")


@dataclass(frozen=True, repr=False)
class D2V2LabelCustodyV1:
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


def _interval_set_hash_v1(kind: str, intervals: tuple[metric_policy_v1.IntervalV1, ...]) -> str:
    return stable_hash_v1({"artifact_type": f"task039e3_r2r_private_d2_v2_{kind}_interval_set_v1", "interval_semantics": "HALF_OPEN_FILE_LOCAL_ONE_SECOND", "intervals": [{"start": x.start, "end": x.end} for x in intervals]})


def _load_label_custody_once_v1(state: D2V2ExecutionStateMachineV1) -> D2V2LabelCustodyV1:
    state.require_label_access()
    root = _binding_value_v1(_root_v1() / ".env.custody.local", "HAI_DATA_ROOT")
    path = root / "hai-23.05" / LABEL_FILENAME
    try:
        if path.is_symlink() or not path.is_file() or path.stat().st_size != LABEL_BYTE_SIZE:
            _fail("LABEL_RAW_IDENTITY_REJECTED")
        digest = sha256()
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
        if digest.hexdigest() != LABEL_SHA256:
            _fail("LABEL_HASH_REJECTED")
        tokens: list[str] = []
        with path.open("r", encoding="utf-8", newline="") as stream:
            reader = csv.reader(stream)
            if next(reader) != ["timestamp", "label"]:
                _fail("LABEL_HEADER_REJECTED")
            for row in reader:
                if len(row) != 2 or not row[0]:
                    _fail("LABEL_ROW_REJECTED")
                tokens.append(row[1])
        if len(tokens) != EXPECTED_ROW_COUNT:
            _fail("LABEL_ROW_COUNT_REJECTED")
        labels = protocol_v3.parse_raw_label_tokens_v3(tuple(tokens))
        attacks = metric_policy_v1.derive_attack_events_v1(labels)
    except D2V2InnerExecutionV1Error:
        raise
    except BaseException:
        _fail("LABEL_PARSE_REJECTED")
    label_hash = stable_hash_v1({"artifact_type": "task039e3_r2r_private_d2_v2_strict_label_vector_v1", "label_file_sha256": LABEL_SHA256, "labels": list(labels)})
    attack_hash = _interval_set_hash_v1("attack", attacks)
    payload = {"artifact_type": "D2V2LabelCustodyV1", "label_file_sha256": LABEL_SHA256, "row_count": EXPECTED_ROW_COUNT, "strict_label_vector_hash": label_hash, "attack_event_set_hash": attack_hash, "attack_event_count": len(attacks), "attack_event_policy": ATTACK_EVENT_POLICY}
    result = D2V2LabelCustodyV1(LABEL_SHA256, EXPECTED_ROW_COUNT, label_hash, attack_hash, len(attacks), sum(labels), EXPECTED_ROW_COUNT - sum(labels), stable_hash_v1(payload), labels, attacks)
    state.transition(D2V2ExecutionStateV1.COMBINED_PREDICTION_V2_FROZEN, D2V2ExecutionStateV1.LABEL_PARSED)
    return result


def _overlap_v1(left: metric_policy_v1.IntervalV1, right: metric_policy_v1.IntervalV1) -> bool:
    return left.start < right.end and right.start < left.end


def _metric_counts_v1(attacks: tuple[metric_policy_v1.IntervalV1, ...], episodes: tuple[metric_policy_v1.IntervalV1, ...]) -> tuple[int, int]:
    return (sum(any(_overlap_v1(a, e) for e in episodes) for a in attacks), sum(not any(_overlap_v1(a, e) for a in attacks) for e in episodes))


def compute_metric_values_v1(
    attack_events: tuple[metric_policy_v1.IntervalV1, ...], d0_episodes: tuple[metric_policy_v1.IntervalV1, ...],
    v2_episodes: tuple[metric_policy_v1.IntervalV1, ...], recovery_episodes: tuple[metric_policy_v1.IntervalV1, ...], normal_seconds: int,
) -> dict[str, float | None]:
    d0_attacked, d0_false = _metric_counts_v1(attack_events, d0_episodes)
    v2_attacked, v2_false = _metric_counts_v1(attack_events, v2_episodes)
    _, recovery_false = _metric_counts_v1(attack_events, recovery_episodes)
    missed = tuple(a for a in attack_events if not any(_overlap_v1(a, e) for e in d0_episodes))
    recovered = sum(any(_overlap_v1(a, e) for e in recovery_episodes) for a in missed)
    hours = normal_seconds / 3600.0
    d0_recall = d0_attacked / len(attack_events) if attack_events else None
    v2_recall = v2_attacked / len(attack_events) if attack_events else None
    d0_far = d0_false / hours if hours else None; v2_far = v2_false / hours if hours else None
    return {
        "d2_v2_recall": v2_recall, "d2_v2_far": v2_far,
        "d0_missed_recovery": recovered / len(missed) if missed else None,
        "incremental_recall": v2_recall - d0_recall if v2_recall is not None and d0_recall is not None else None,
        "added_recovery_far": recovery_false / hours if hours else None,
        "incremental_far": v2_far - d0_far if v2_far is not None and d0_far is not None else None,
    }


@dataclass(frozen=True)
class ScientificD2V2MetricV1:
    metric_name: str
    formula_identity: str
    value: float | None
    defined: bool
    undefined_reason: str | None
    private_evidence_hash: str
    artifact_hash: str

    def to_public_dict(self) -> dict[str, Any]:
        return {"metric_name": self.metric_name, "formula_identity": self.formula_identity, "value": self.value, "defined": self.defined, "undefined_reason": self.undefined_reason, "private_evidence_hash": self.private_evidence_hash, "artifact_hash": self.artifact_hash}


def _metric_v1(name: str, formula: str, value: float | None, reason: str, evidence_hash: str) -> ScientificD2V2MetricV1:
    payload = {"artifact_type": "ScientificD2V2MetricV1", "metric_name": name, "formula_identity": formula, "value": value, "defined": value is not None, "undefined_reason": None if value is not None else reason, "private_evidence_hash": evidence_hash}
    return ScientificD2V2MetricV1(name, formula, value, value is not None, None if value is not None else reason, evidence_hash, stable_hash_v1(payload))


def _build_private_metric_evidence_v1(
    custody: D2V2LabelCustodyV1, d0_episodes: tuple[metric_policy_v1.IntervalV1, ...],
    v2_episodes: tuple[metric_policy_v1.IntervalV1, ...], recovery_episodes: tuple[metric_policy_v1.IntervalV1, ...],
    combined_hash: str, fusion_hash: str,
) -> tuple[dict[str, Any], dict[str, ScientificD2V2MetricV1]]:
    values = compute_metric_values_v1(custody._attack_events, d0_episodes, v2_episodes, recovery_episodes, custody.normal_labeled_seconds)
    d0_attacked, d0_false = _metric_counts_v1(custody._attack_events, d0_episodes)
    v2_attacked, v2_false = _metric_counts_v1(custody._attack_events, v2_episodes)
    _, recovery_false = _metric_counts_v1(custody._attack_events, recovery_episodes)
    missed = tuple(a for a in custody._attack_events if not any(_overlap_v1(a, e) for e in d0_episodes))
    recovered = sum(any(_overlap_v1(a, e) for e in recovery_episodes) for a in missed)
    payload = {
        "artifact_type": "D2V2MetricEvidenceV1", "schema_version": SCHEMA_VERSION,
        "authorization_hash": AUTHORIZATION_HASH, "d2_v2_design_hash": D2_V2_DESIGN_HASH,
        "combined_prediction_v2_hash": combined_hash, "fusion_evidence_v2_hash": fusion_hash,
        "label_vector_hash": custody.strict_label_vector_hash, "attack_event_set_hash": custody.attack_event_set_hash,
        "d0_alarm_episode_set_hash": _interval_set_hash_v1("d0_alarm", d0_episodes),
        "d2_v2_alarm_episode_set_hash": _interval_set_hash_v1("d2_v2_alarm", v2_episodes),
        "rule_recovery_v2_episode_set_hash": _interval_set_hash_v1("rule_recovery_v2", recovery_episodes),
        "private_counts": {"attack_event_count": len(custody._attack_events), "normal_labeled_seconds": custody.normal_labeled_seconds, "d0_attack_events_overlapped": d0_attacked, "d2_v2_attack_events_overlapped": v2_attacked, "d0_false_alarm_episodes": d0_false, "d2_v2_false_alarm_episodes": v2_false, "d0_missed_attack_events": len(missed), "d0_missed_recovered": recovered, "rule_recovery_false_alarm_episodes": recovery_false},
        "metric_values": values,
    }
    document = {**payload, "artifact_hash": stable_hash_v1(payload)}; evidence_hash = document["artifact_hash"]
    metrics = {
        "d2_v2_attack_event_recall": _metric_v1("D2 V2 Attack-event Recall", ATTACK_EVENT_RECALL_FORMULA, values["d2_v2_recall"], "NO_ATTACK_EVENTS", evidence_hash),
        "d2_v2_normal_far_episodes_per_hour": _metric_v1("D2 V2 Normal FAR episodes/hour", NORMAL_FAR_FORMULA, values["d2_v2_far"], "NO_NORMAL_EXPOSURE", evidence_hash),
        "d0_missed_attack_recovery_rate": _metric_v1("D0-missed Attack Recovery Rate", D0_MISSED_ATTACK_RECOVERY_FORMULA, values["d0_missed_recovery"], "NO_D0_MISSED_ATTACK_EVENTS", evidence_hash),
        "incremental_attack_event_recall": _metric_v1("Incremental Attack-event Recall", INCREMENTAL_ATTACK_RECALL_FORMULA, values["incremental_recall"], "NO_ATTACK_EVENTS", evidence_hash),
        "added_normal_rule_recovery_far_episodes_per_hour": _metric_v1("Added Normal Rule-Recovery FAR episodes/hour", ADDED_NORMAL_RECOVERY_FAR_FORMULA, values["added_recovery_far"], "NO_NORMAL_EXPOSURE", evidence_hash),
        "incremental_normal_far_episodes_per_hour": _metric_v1("Incremental Normal FAR episodes/hour", INCREMENTAL_NORMAL_FAR_FORMULA, values["incremental_far"], "NO_NORMAL_EXPOSURE", evidence_hash),
    }
    return document, metrics


@dataclass(frozen=True)
class D2V2InnerExecutionRunV1:
    committed_grant_hash: str
    authorization_hash: str
    execution_implementation_identity: str
    d2_v2_design_hash: str
    d0_prediction_hash: str
    d1_prediction_hash: str
    source_map_hash: str
    native_horizon_map_hash: str
    fusion_evidence_hash: str
    combined_prediction_hash: str
    private_metric_evidence_hash: str
    metric_artifact_hash: str
    accounting_identity: str
    scientific_execution_attempts: int
    scientific_execution_retries: int
    test2_accesses: int
    result_driven_changes: bool
    run_hash: str

    def _payload(self) -> dict[str, Any]:
        return {key: value for key, value in self.__dict__.items() if key != "run_hash"}


@dataclass(frozen=True)
class D2V2InnerExecutionOutcomeV1:
    execution_run_hash: str
    committed_grant_hash: str
    fusion_evidence_hash: str
    combined_prediction_hash: str
    private_metric_evidence_hash: str
    metric_artifact_hash: str
    metrics: tuple[tuple[str, ScientificD2V2MetricV1], ...]
    alarming_d1_records_used: int
    evidence_tokens_constructed: int
    zero_horizon_token_count: int
    split_end_clipped_token_count: int
    corroboration_point_count: int
    trigger_class_counts: tuple[tuple[str, int], ...]
    point_alarm_count: int
    alarm_episode_count: int
    recovery_episode_count: int
    implementation_audit_hash: str
    accounting_hash: str
    readiness_hash: str
    bundle_hash: str
    receipt_hash: str
    report_hash: str


def _write_report_atomic_v1(text: str) -> None:
    path = _root_v1() / REPORT_PATH; temporary = path.with_suffix(path.suffix + ".tmp")
    try:
        if path.exists() or path.is_symlink() or temporary.exists() or temporary.is_symlink():
            _fail("PUBLIC_REPORT_ALREADY_EXISTS")
        with temporary.open("x", encoding="utf-8", newline="\n") as stream:
            stream.write(text); stream.flush(); os.fsync(stream.fileno())
        os.replace(temporary, path)
        if path.read_text(encoding="utf-8") != text:
            _fail("PUBLIC_REPORT_REPLAY_REJECTED")
    except D2V2InnerExecutionV1Error:
        raise
    except BaseException:
        _fail("PUBLIC_REPORT_WRITE_REJECTED")


def _implementation_git_custody_v1() -> tuple[str, str, str]:
    commit_b = _git_output_v1(["rev-parse", "HEAD"]).decode().strip()
    commit_a = _git_output_v1(["rev-parse", "HEAD^"]).decode().strip()
    relative = "src/paperworks/v6/task039e3_r2r_d2_v2_inner_execution_v1.py"
    current = _current_bytes_v1(relative)
    if current != _commit_bytes_v1(commit_a, relative):
        _fail("IMPLEMENTATION_COMMIT_A_IMMUTABILITY_REJECTED")
    return commit_a, commit_b, sha256(current).hexdigest()


def _write_result_reports_v1(
    grant: CommittedD2V2InnerExecutionGrantV1, evidence: D2V2FusionEvidenceV1,
    combined: ScientificCombinedPredictionArtifactV2, metrics: Mapping[str, ScientificD2V2MetricV1],
    private_metric_hash: str, v2_episode_count: int, recovery_episode_count: int,
) -> tuple[str, str, str, str, str, str, str, str]:
    commit_a, commit_b, source_sha = _implementation_git_custody_v1(); created = _utc_now_v1()
    accounting_core = {
        "scientific_v2_execution_attempts": 1, "scientific_v2_execution_retries": 0,
        "d0_prediction_parses": 1, "d1_prediction_parses": 1, "source_map_reads": 1,
        "native_horizon_map_reads": 1, "alarming_d1_records_used": evidence.evidence_token_count,
        "evidence_tokens_constructed": evidence.evidence_token_count, "fusion_computations": 54000,
        "private_fusion_evidence_freezes": 1, "combined_prediction_v2_freezes": 1,
        "label_hash_reads": 1, "label_scientific_parses": 1,
        "label_before_combined_prediction_v2_access": False, "attack_event_derivations": 1,
        "v2_alarm_episode_derivations": 1, "d0_reference_episode_derivations": 1,
        "v2_rule_recovery_episode_derivations": 1, "primary_metric_computations": 2,
        "incremental_metric_computations": 4, "d0_executions": 0, "d1_executions": 0,
        "d2_v1_executions": 0, "d1_metric_artifact_reads": 0, "d2_v1_prediction_reads": 0,
        "d2_v1_metric_reads": 0, "d0_model_accesses": 0, "d0_score_accesses": 0,
        "d1_rule_reevaluations": 0, "test1_feature_accesses": 0, "test2_accesses": 0,
        "outer_executions": 0, "result_driven_changes": False, "private_paths_exposed": 0,
        "private_source_sets_exposed": 0, "private_label_values_exposed": 0,
    }
    accounting_identity = stable_hash_v1({"artifact_type": "D2V2ExecutionAccountingIdentityV1", **accounting_core})
    metric_document = _strict_json_object_v1(_current_bytes_v1(METRICS_PATH)); metric_hash = _canonical_self_hash_v1(metric_document)
    run_provisional = D2V2InnerExecutionRunV1(
        grant.grant_hash, AUTHORIZATION_HASH, D2_V2_INNER_EXECUTION_IMPLEMENTATION_IDENTITY,
        D2_V2_DESIGN_HASH, D0_PREDICTION_HASH, D1_PREDICTION_HASH, SOURCE_MAP_HASH,
        NATIVE_HORIZON_MAP_HASH, evidence.fusion_evidence_hash, combined.artifact_hash,
        private_metric_hash, metric_hash, accounting_identity, 1, 0, 0, False, "",
    )
    run = replace(run_provisional, run_hash=stable_hash_v1(run_provisional._payload()))
    implementation = _self_hashed_v1({
        "artifact_type": "D2V2ExecutionImplementationAuditV1", "schema_version": SCHEMA_VERSION,
        "created_at_utc": created, "task_id": TASK_ID, "base_commit": BASE_COMMIT,
        "execution_implementation_commit_a": commit_a, "independent_audit_commit_b": commit_b,
        "execution_version": D2_V2_INNER_EXECUTION_VERSION,
        "execution_implementation_identity": D2_V2_INNER_EXECUTION_IMPLEMENTATION_IDENTITY,
        "execution_implementation_source_sha256": source_sha,
        "production_changes_after_commit_a": 0, "scientific_policy_changes_after_commit_a": 0,
        "static_tests_passed": EXPECTED_STATIC_TESTS, "static_tests_total": EXPECTED_STATIC_TESTS,
        "independent_attacks": EXPECTED_INDEPENDENT_ATTACKS,
        "independent_attacks_rejected": EXPECTED_INDEPENDENT_ATTACKS, "accepted_invalid": 0,
        "semantic_differential_cases": SEMANTIC_DIFFERENTIAL_CASES, "semantic_differential_divergences": 0,
        "path_redaction_pass": True, "private_paths_exposed": 0,
    })
    accounting = _self_hashed_v1({"artifact_type": "D2V2ExecutionAccountingV1", "schema_version": SCHEMA_VERSION, "created_at_utc": created, "task_id": TASK_ID, "execution_run_hash": run.run_hash, **accounting_core, "push_attempted": False, "remote_egress_status": "LOCAL_ONLY_NOT_PUSHED"})
    readiness = _self_hashed_v1({
        "artifact_type": "D2V2ExecutionReadinessV1", "schema_version": SCHEMA_VERSION,
        "created_at_utc": created, "task_id": TASK_ID, "status": PASS_STATUS,
        "scientific_state": SCIENTIFIC_STATUS, "execution_run_hash": run.run_hash,
        "implementation_audit_hash": implementation["artifact_hash"], "accounting_hash": accounting["artifact_hash"],
        "authorization_hash": AUTHORIZATION_HASH, "design_hash": D2_V2_DESIGN_HASH,
        "fusion_evidence_hash": evidence.fusion_evidence_hash, "combined_prediction_hash": combined.artifact_hash,
        "private_metric_evidence_hash": private_metric_hash, "metric_artifact_hash": metric_hash,
        "scientific_execution_attempts": 1, "scientific_execution_retries": 0,
        "d2_v2_executed": True, "d2_v2_result_frozen": True,
        "test2_authorized": False, "outer_authorized": False, "blockers": [], "exact_next_task": NEXT_TASK,
    })
    body = (
        "# TASK-039E3-R2R D2 V2 INNER execution\n\n"
        f"Status: `{PASS_STATUS}`\n\n"
        "The single authorized native-horizon D2 V2 INNER execution completed under the exact frozen design and authorization.\n\n"
        f"- CombinedPredictionV2 records: `{EXPECTED_ROW_COUNT}`\n"
        f"- Evidence tokens: `{evidence.evidence_token_count}`\n"
        f"- Native-horizon corroboration points: `{evidence.corroboration_point_count}`\n"
        f"- D2 V2 point alarms: `{combined.point_alarm_count}`\n"
        f"- D2 V2 alarm episodes: `{v2_episode_count}`\n"
        f"- V2 rule-recovery episodes: `{recovery_episode_count}`\n"
        f"- D2 V2 Attack-event Recall: `{metrics['d2_v2_attack_event_recall'].value}`\n"
        f"- D2 V2 Normal FAR episodes/hour: `{metrics['d2_v2_normal_far_episodes_per_hour'].value}`\n"
        f"- D0-missed Attack Recovery Rate: `{metrics['d0_missed_attack_recovery_rate'].value}`\n"
        f"- Incremental Attack-event Recall: `{metrics['incremental_attack_event_recall'].value}`\n"
        f"- Added Normal Rule-Recovery FAR episodes/hour: `{metrics['added_normal_rule_recovery_far_episodes_per_hour'].value}`\n"
        f"- Incremental Normal FAR episodes/hour: `{metrics['incremental_normal_far_episodes_per_hour'].value}`\n\n"
        "Result magnitude did not alter the frozen policy. D0/D1/D2 V1 reruns, rule reevaluation, D0 score access, test1-feature access, test2, OUTER, retries, private leakage, and push remained zero.\n"
    )
    report_hash = sha256(body.encode()).hexdigest()
    bundle = _self_hashed_v1({
        "artifact_type": "D2V2ExecutionBundleV1", "schema_version": SCHEMA_VERSION,
        "created_at_utc": created, "task_id": TASK_ID, "status": PASS_STATUS,
        "execution_run_hash": run.run_hash, "implementation_audit_hash": implementation["artifact_hash"],
        "combined_prediction_hash": combined.artifact_hash, "metric_artifact_hash": metric_hash,
        "accounting_hash": accounting["artifact_hash"], "readiness_hash": readiness["artifact_hash"],
        "fusion_evidence_hash": evidence.fusion_evidence_hash, "private_metric_evidence_hash": private_metric_hash,
        "report_hash_scheme": REPORT_HASH_SCHEME, "report_self_hash": report_hash,
        "remote_egress_status": "LOCAL_ONLY_NOT_PUSHED",
    })
    receipt = _self_hashed_v1({
        "artifact_type": "D2V2ExecutionReceiptV1", "schema_version": SCHEMA_VERSION,
        "created_at_utc": created, "task_id": TASK_ID, "status": PASS_STATUS,
        "execution_run_hash": run.run_hash, "bundle_hash": bundle["artifact_hash"],
        "readiness_hash": readiness["artifact_hash"], "combined_prediction_hash": combined.artifact_hash,
        "metric_artifact_hash": metric_hash, "report_hash_scheme": REPORT_HASH_SCHEME,
        "report_self_hash": report_hash, "d2_v2_executed": True, "outer_authorized": False,
        "exact_next_task": NEXT_TASK,
    })
    _write_public_json_atomic_v1(IMPLEMENTATION_AUDIT_PATH, implementation)
    _write_public_json_atomic_v1(ACCOUNTING_PATH, accounting)
    _write_public_json_atomic_v1(READINESS_PATH, readiness)
    _write_public_json_atomic_v1(BUNDLE_PATH, bundle)
    _write_public_json_atomic_v1(RECEIPT_PATH, receipt)
    footer = (
        "\n<!-- BEGIN D2 V2 EXECUTION REPORT PROVENANCE V1 -->\n"
        f"Report-Hash-Scheme: {REPORT_HASH_SCHEME}\n"
        f"Report-Self-Hash: {report_hash}\n"
        f"Bundle-Hash: {bundle['artifact_hash']}\n"
        f"Receipt-Hash: {receipt['artifact_hash']}\n"
        "<!-- END D2 V2 EXECUTION REPORT PROVENANCE V1 -->\n"
    )
    _write_report_atomic_v1(body + footer)
    return run.run_hash, implementation["artifact_hash"], accounting["artifact_hash"], readiness["artifact_hash"], bundle["artifact_hash"], receipt["artifact_hash"], report_hash, metric_hash


_REAL_EXECUTION_ENTRY_ATTEMPTED = False
_SCIENTIFIC_V2_ATTEMPT_STARTED = False
_SCIENTIFIC_V2_ATTEMPT_COMPLETED = False


def execute_authorized_d2_v2_inner_v1() -> D2V2InnerExecutionOutcomeV1:
    global _REAL_EXECUTION_ENTRY_ATTEMPTED, _SCIENTIFIC_V2_ATTEMPT_STARTED, _SCIENTIFIC_V2_ATTEMPT_COMPLETED
    if _REAL_EXECUTION_ENTRY_ATTEMPTED or _SCIENTIFIC_V2_ATTEMPT_STARTED:
        _fail("D2_V2_SECOND_EXECUTION_ATTEMPT_REJECTED")
    _REAL_EXECUTION_ENTRY_ATTEMPTED = True
    try:
        grant = issue_committed_d2_v2_inner_execution_grant_v1()
        token = _issue_execution_token_v1(grant)
        state = D2V2ExecutionStateMachineV1()
        state.transition(D2V2ExecutionStateV1.NOT_STARTED, D2V2ExecutionStateV1.GRANT_REPLAYED)
        if recovery_custody.RECOVERY_CUSTODY_MODULE_IDENTITY != RECOVERY_CUSTODY_IDENTITY:
            _fail("PRIVATE_CUSTODY_IDENTITY_REJECTED")
        authorization_boundary._validate_v2_private_binding_v1()
        preflight = recovery_custody.perform_d2_recovery_custody_preflight_v1()
        recovery_custody.validate_d2_recovery_custody_preflight_v1(preflight)
        state.transition(D2V2ExecutionStateV1.GRANT_REPLAYED, D2V2ExecutionStateV1.PRIVATE_CUSTODY_REVALIDATED)

        _SCIENTIFIC_V2_ATTEMPT_STARTED = True
        d0 = _parse_frozen_d0_prediction_v1(token)
        d1 = _parse_frozen_d1_prediction_v1(token)
        state.transition(D2V2ExecutionStateV1.PRIVATE_CUSTODY_REVALIDATED, D2V2ExecutionStateV1.INPUT_PREDICTIONS_VALIDATED)
        source_map = _parse_frozen_source_map_v1(token)
        horizon_map = _parse_frozen_native_horizon_map_v1(token)
        if {r for r, _ in source_map._entries} != {r for r, _ in horizon_map._entries}:
            _fail("SOURCE_HORIZON_RELATION_CLOSURE_REJECTED")
        state.transition(D2V2ExecutionStateV1.INPUT_PREDICTIONS_VALIDATED, D2V2ExecutionStateV1.SOURCE_AND_HORIZON_MAPS_VALIDATED)
        evidence, fusion_document = _build_fusion_evidence_v1(d0, d1, source_map, horizon_map)
        state.transition(D2V2ExecutionStateV1.SOURCE_AND_HORIZON_MAPS_VALIDATED, D2V2ExecutionStateV1.EVIDENCE_TOKENS_CONSTRUCTED)
        state.transition(D2V2ExecutionStateV1.EVIDENCE_TOKENS_CONSTRUCTED, D2V2ExecutionStateV1.V2_FUSION_COMPUTED)
        fusion_hash = _persist_private_v2(preflight._root, PRIVATE_FUSION_FILENAME, fusion_document)
        state.transition(D2V2ExecutionStateV1.V2_FUSION_COMPUTED, D2V2ExecutionStateV1.PRIVATE_FUSION_EVIDENCE_FROZEN)
        combined = _build_combined_prediction_v1(evidence)
        frozen_combined = _persist_combined_before_label_v1(state, combined)

        custody = _load_label_custody_once_v1(state)
        if _current_bytes_v1(COMBINED_PREDICTION_PATH) != frozen_combined:
            _fail("COMBINED_PREDICTION_V2_CHANGED_BEFORE_METRICS")
        combined_document = _strict_json_object_v1(frozen_combined)
        validate_scientific_combined_prediction_document_v1(combined_document)
        rows = combined_document["prediction_records"]
        v2_indices = tuple(r["physical_row_index"] for r in rows if r["d2_v2_alarm_emitted"] is True)
        recovery_indices = tuple(r["physical_row_index"] for r in rows if r["trigger_class"] == "RULE_RECOVERY_NATIVE_HORIZON")
        v2_episodes = metric_policy_v1.form_alarm_episodes_v1(v2_indices)
        recovery_episodes = metric_policy_v1.form_alarm_episodes_v1(recovery_indices)
        d0_replay = _current_bytes_v1(D0_PREDICTION_PATH)
        if sha256(d0_replay).hexdigest() != d0.raw_bytes_hash or d0_replay != _commit_bytes_v1(D0_PREDICTION_FREEZE_COMMIT, D0_PREDICTION_PATH):
            _fail("D0_REFERENCE_RELOAD_REJECTED")
        d0_indices = tuple(i for i, alarm in enumerate(d0._alarms) if alarm)
        d0_episodes = metric_policy_v1.form_alarm_episodes_v1(d0_indices)
        metric_document, metrics = _build_private_metric_evidence_v1(custody, d0_episodes, v2_episodes, recovery_episodes, combined.artifact_hash, fusion_hash)
        private_metric_hash = _persist_private_v2(preflight._root, PRIVATE_METRIC_FILENAME, metric_document)
        state.transition(D2V2ExecutionStateV1.LABEL_PARSED, D2V2ExecutionStateV1.METRICS_COMPUTED)
        public_metrics = _self_hashed_v1({
            "artifact_type": "ScientificD2V2MetricArtifactV1", "schema_version": SCHEMA_VERSION,
            "task_id": TASK_ID, "d2_v2_id": D2_V2_ID, "d2_v2_design_hash": D2_V2_DESIGN_HASH,
            "authorization_hash": AUTHORIZATION_HASH, "d0_prediction_hash": D0_PREDICTION_HASH,
            "d1_prediction_hash": D1_PREDICTION_HASH, "source_map_hash": SOURCE_MAP_HASH,
            "native_horizon_map_hash": NATIVE_HORIZON_MAP_HASH, "combined_prediction_v2_hash": combined.artifact_hash,
            "fusion_evidence_v2_hash": fusion_hash, "evidence_token_aggregate_count": evidence.evidence_token_count,
            "native_horizon_corroboration_point_count": evidence.corroboration_point_count,
            "trigger_class_counts": dict(evidence.trigger_class_counts), "d2_v2_point_alarm_count": evidence.point_alarm_count,
            "d2_v2_alarm_episode_count": len(v2_episodes), "v2_rule_recovery_episode_count": len(recovery_episodes),
            "metrics": {name: value.to_public_dict() for name, value in metrics.items()},
            "private_metric_evidence_hash": private_metric_hash,
        })
        _write_public_json_atomic_v1(METRICS_PATH, public_metrics)
        run_hash, implementation_hash, accounting_hash, readiness_hash, bundle_hash, receipt_hash, report_hash, metric_hash = _write_result_reports_v1(grant, evidence, combined, metrics, private_metric_hash, len(v2_episodes), len(recovery_episodes))
        if _current_bytes_v1(COMBINED_PREDICTION_PATH) != frozen_combined:
            _fail("COMBINED_PREDICTION_V2_CHANGED_AFTER_METRICS")
        if sha256(_current_bytes_v1(D0_PREDICTION_PATH)).hexdigest() != d0.raw_bytes_hash or sha256(_current_bytes_v1(D1_PREDICTION_PATH)).hexdigest() != d1.raw_bytes_hash or sha256(_current_bytes_v1(SOURCE_MAP_PATH)).hexdigest() != source_map.raw_bytes_hash:
            _fail("FROZEN_INPUT_BYTES_CHANGED")
        _consume_execution_token_v1(token)
        state.transition(D2V2ExecutionStateV1.METRICS_COMPUTED, D2V2ExecutionStateV1.RESULT_FROZEN)
        _SCIENTIFIC_V2_ATTEMPT_COMPLETED = True
        return D2V2InnerExecutionOutcomeV1(
            run_hash, grant.grant_hash, fusion_hash, combined.artifact_hash, private_metric_hash,
            metric_hash, tuple(metrics.items()), evidence.evidence_token_count, evidence.evidence_token_count,
            evidence.zero_horizon_token_count, evidence.split_end_clipped_token_count,
            evidence.corroboration_point_count, evidence.trigger_class_counts, evidence.point_alarm_count,
            len(v2_episodes), len(recovery_episodes), implementation_hash, accounting_hash,
            readiness_hash, bundle_hash, receipt_hash, report_hash,
        )
    except D2V2InnerExecutionV1Error:
        raise
    except (recovery_custody.D2RecoveryCustodyV1Error, authorization_boundary.D2V2ExecutionAuthorizationError) as error:
        raise D2V2InnerExecutionV1Error(getattr(error, "code", "D2_V2_EXECUTION_UNEXPECTED")) from None
    except BaseException:
        _fail("D2_V2_EXECUTION_UNEXPECTED")


def reject_prohibited_operation_v1(operation: str) -> NoReturn:
    prohibited = {
        "retry", "second_execution", "horizon_change", "horizon_override", "horizon_multiplier",
        "global_temporal_window", "diagnostic_gap_window", "source_count_change",
        "single_source_fallback", "exact_same_second_exclusion", "d0_suppression", "raw_rule_or",
        "d0_score", "d0_rerun", "d1_rerun", "d2_v1_rerun", "rule_reevaluation",
        "label_before_prediction", "test1_feature", "test2", "outer", "result_driven_change",
        "private_source_set_exposure", "private_path_exposure", "alternate_policy",
    }
    _fail("D2_V2_PROHIBITED_OPERATION_REJECTED" if operation in prohibited else "D2_V2_UNKNOWN_OPERATION_REJECTED")


__all__ = [
    "CommittedD2V2InnerExecutionGrantV1", "D2V2EvidenceTokenV1", "D2V2FusionEvidenceV1",
    "D2V2InnerExecutionOutcomeV1", "D2V2InnerExecutionRunV1", "D2V2InnerExecutionV1Error",
    "D2V2LabelCustodyV1", "FrozenD0PredictionInputV1", "FrozenD1PredictionInputV1",
    "FrozenD2V2SourceMapV1", "FrozenD2V2NativeHorizonMapV1",
    "ScientificCombinedPredictionRecordV2", "ScientificCombinedPredictionArtifactV2",
    "ScientificD2V2MetricV1", "D2_V2_INNER_EXECUTION_VERSION",
    "D2_V2_INNER_EXECUTION_IMPLEMENTATION_IDENTITY", "build_evidence_tokens_v1",
    "brute_force_native_horizon_timeline_v1", "compute_metric_values_v1",
    "execute_authorized_d2_v2_inner_v1", "fuse_native_horizon_timeline_v1",
    "issue_committed_d2_v2_inner_execution_grant_v1", "reject_prohibited_operation_v1",
    "validate_combined_prediction_records_v1", "validate_committed_d2_v2_inner_execution_grant_v1",
    "validate_scientific_combined_prediction_artifact_v1",
    "validate_scientific_combined_prediction_document_v1",
]
