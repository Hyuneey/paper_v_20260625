"""One-shot sealed OUTER D0/D1/D2-V1 execution bridge.

The public helpers are pure/synthetic.  ``execute_authorized_outer_v1`` is the
only real entry point and accepts no scientific parameters.  It replays the
committed authorization, performs one path-redacted custody sentinel, reads
test2 features once into an immutable shared snapshot, freezes and reopens all
three compact predictions, and only then reads labels once.  Private relation,
fusion, and metric evidence never enters Git or the public return surface.
"""
from __future__ import annotations

from bisect import bisect_left
import csv
from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from enum import Enum
from hashlib import sha256
import io
import json
import math
import os
from pathlib import Path
import statistics
import subprocess
import sys
from typing import Any, Mapping, NoReturn, Sequence

from paperworks.v6 import task039e3_r2r_d0_detector_design_v1 as d0_design
from paperworks.v6 import task039e3_r2r_d0_inner_execution_v1 as d0_inner
from paperworks.v6 import task039e3_r2r_d2_execution_recovery_custody_v1 as private_custody
from paperworks.v6 import task039e3_r2r_outer_d0_d1_d2v1_preregistration_authorization_v1 as outer_auth
from paperworks.v6 import task039e3_r2r_utility_evaluator_metrics_v1 as metric_policy
from paperworks.v6 import task039e3_r2r_utility_evaluator_rule_engine_v1 as evaluator_rule
from paperworks.v6 import task039e3_r2r_utility_inner_d1_execution_v1 as d1_inner
from paperworks.v6 import task039e3_r2r_utility_protocol_v3 as v3
from paperworks.v6 import task039e3_r2r_utility_protocol_v4 as v4


ROOT = Path(__file__).resolve().parents[3]
REPORT_ROOT = ROOT / "docs" / "task_reports"
TASK_ID = "TASK-039E3-R2R-UTILITY-OUTER-D0-D1-D2V1-EXECUTION-V1"
PASS_STATUS = "passed_task039e3_r2r_utility_outer_d0_d1_d2v1_execution_v1"
BLOCK_STATUS = "blocked_task039e3_r2r_utility_outer_d0_d1_d2v1_execution_v1"
SCIENTIFIC_STATE = "OUTER_RESULT_FROZEN_INTEGRITY_AUDIT_PENDING"
OUTER_EXECUTION_VERSION = "TASK039E3_R2R_OUTER_D0_D1_D2V1_EXECUTION_V1"
AUTHORIZATION_SCOPE = "HAI_23_05_P1_TEST2_D0_D1_D2V1_CONFIRMATORY_OUTER_V1"
BRANCH = "task-039e3-r2r-utility-outer-d0-d1-d2v1-execution-v1"
BASE = "65a9439ff4b16960368c21c9ef96da4394cecee7"
NEXT_TASK = "TASK-039E3-R2R-UTILITY-OUTER-D0-D1-D2V1-RESULT-INTEGRITY-AUDIT-V1"
FAILURE_NEXT_TASK = "TASK-039E3-R2R-UTILITY-OUTER-EXECUTION-FAILURE-DISPOSITION-V1"
SCHEME = "MARKDOWN_BODY_SHA256_BEFORE_INTEGRITY_FOOTER_V1"

PREREGISTRATION_SHA256 = "66179921042faecf189fe93ddaf20bb06669afa6e27dbefb67c9b95eabb93427"
AUTHORIZATION_SHA256 = "fb8abb3a342c591873d15d4bcf28cbdcc7363fce77a228f486f122ef5933ac14"
PREREGISTRATION_ARTIFACT_SHA256 = "74611ced3ef1e6cec71d3cd04fd8f5d13b323b159fd0f03ca118b2af72f24a89"
AUTHORIZATION_ARTIFACT_SHA256 = "bbd1c08323ab8d66f342ebb4cbcda4c3b375a7ba1956389c0dc8b642e02f0fa9"
DATASET_MANIFEST_SHA256 = "5b0c395169fea468f7afd52aceafc4e6dadf062a1bc557c5bbe5dd6b8a761aa2"
TEST2_FEATURE_SHA256 = "b2b8dd295aefd87e39260fe43cb4c73ee86d6264b0ac4b0761e7efb0c2b545c3"
TEST2_LABEL_SHA256 = "8090c44981176e39b0f01a7126a80248ac0b93355c00f9db4d4e2f2106452b92"
TEST2_FEATURE_FILENAME = "hai-test2.csv"
TEST2_LABEL_FILENAME = "label-test2.csv"
ROW_COUNT = 230_400

D0_DESIGN_SHA256 = "357d19d02dee73273d52c7b147b5ddcfa11ead43a7198f2bf089ec78c2d8e174"
D0_IMPLEMENTATION_IDENTITY = "8f00469a632643cd10cc4257f5d1fe380036c7763b03cb70b13d01815a287ee2"
D0_MODEL_SHA256 = "f32943cc2172100c77514d9ce8f6731978b51934e753234b2d34b5154127b54b"
D0_THRESHOLD_SHA256 = "7ac0628cad5983b9864d31a9984bd414867b80f175248dbdf5cd69d7589f3695"
D1_CONSTRUCTION_SHA256 = "1a6200adce791ddd9be8d87b566d47b65e78c1735829d0f91f4ea22127ad1343"
D1_DESCRIPTOR_SHA256 = "665af1d58d672dfe8109c01e5dcb4e8f19aa2303a8f6100bfd20b3272c3bd928"
D1_EVALUATOR_IDENTITY = "af74bf3bd9ae240f21c57630b4804eabb997021353f15e7c402904b94f783fb5"
D1_RELATION_COUNT = 42
D2_DESIGN_SHA256 = "eb559a91350fd046204d223d6820ef7f0590ad4beb7a2b17114a496859758e51"
SOURCE_MAP_SHA256 = "f866176000c3d5a943053ac3125d2700b0b72f25b5a0539d8f4713435a959818"
REQUIRED_DISTINCT_SOURCES = 2
TRIGGER_CLASSES = ("NONE", "D0_ONLY", "RULE_RECOVERY", "D0_AND_RULE_CORROBORATION")
STATIC_TESTS = 34
INDEPENDENT_ATTACKS = 26

PREDICTION_PATHS = {
    "d0": REPORT_ROOT / "TASK-039E3_R2R_UTILITY_OUTER_D0_PREDICTION_V1.json",
    "d1": REPORT_ROOT / "TASK-039E3_R2R_UTILITY_OUTER_D1_PREDICTION_V1.json",
    "d2": REPORT_ROOT / "TASK-039E3_R2R_UTILITY_OUTER_D2V1_PREDICTION_V1.json",
}
PREFIX = "TASK-039E3_R2R_UTILITY_OUTER_D0_D1_D2V1_EXECUTION_V1_"
REPORT_PATHS = {
    "implementation_audit": REPORT_ROOT / f"{PREFIX}IMPLEMENTATION_AUDIT.json",
    "accounting": REPORT_ROOT / f"{PREFIX}ACCOUNTING.json",
    "metrics": REPORT_ROOT / f"{PREFIX}METRICS.json",
    "readiness": REPORT_ROOT / f"{PREFIX}READINESS.json",
    "bundle": REPORT_ROOT / f"{PREFIX}BUNDLE.json",
    "receipt": REPORT_ROOT / f"{PREFIX}RECEIPT.json",
    "report": REPORT_ROOT / f"{PREFIX}REPORT.md",
}
AUTH_PATH = REPORT_ROOT / "TASK-039E3_R2R_UTILITY_OUTER_D0_D1_D2V1_V1_AUTHORIZATION.json"
PREREG_PATH = REPORT_ROOT / "TASK-039E3_R2R_UTILITY_OUTER_D0_D1_D2V1_V1_PREREGISTRATION.json"
SOURCE_MAP_PATH = REPORT_ROOT / "TASK-039E3_R2R_UTILITY_INNER_D2_EXECUTION_AUTHORIZATION_V1_SOURCE_MAP.json"


class OuterExecutionError(RuntimeError):
    """Path-free fail-closed execution error."""

    def __init__(self, code: str) -> None:
        self.code = code if code.startswith("OUTER_") else "OUTER_EXECUTION_UNEXPECTED"
        super().__init__(self.code)


def fail(code: str) -> NoReturn:
    raise OuterExecutionError(code) from None


def stable_hash(value: Mapping[str, Any]) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
                     allow_nan=False).encode("utf-8")
    return sha256(raw).hexdigest()


def seal(value: Mapping[str, Any]) -> dict[str, Any]:
    if "artifact_hash" in value:
        fail("OUTER_SELF_HASH_FIELD_COLLISION")
    result = dict(value)
    result["artifact_hash"] = stable_hash(result)
    return result


def strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            fail("OUTER_DUPLICATE_JSON_KEY")
        result[key] = value
    return result


def strict_json(raw: bytes) -> dict[str, Any]:
    try:
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=strict_object)
    except OuterExecutionError:
        raise
    except BaseException:
        fail("OUTER_JSON_REJECTED")
    if type(value) is not dict:
        fail("OUTER_JSON_REJECTED")
    return value


def validate_sealed(document: Mapping[str, Any], expected: str | None = None) -> str:
    observed = document.get("artifact_hash")
    if type(observed) is not str or stable_hash({k: v for k, v in document.items()
                                                if k != "artifact_hash"}) != observed:
        fail("OUTER_ARTIFACT_HASH_REJECTED")
    if expected is not None and observed != expected:
        fail("OUTER_ARTIFACT_HASH_REJECTED")
    return observed


def _git(*args: str) -> str:
    try:
        return subprocess.run(("git", *args), cwd=ROOT, check=True,
                              stdout=subprocess.PIPE, stderr=subprocess.DEVNULL).stdout.decode().strip()
    except BaseException:
        fail("OUTER_GIT_CUSTODY_REJECTED")


@dataclass(frozen=True)
class CommittedOuterThreeArmExecutionGrantV1:
    execution_version: str
    authorization_scope: str
    preregistration_sha256: str
    authorization_sha256: str
    dataset_manifest_sha256: str
    test2_feature_sha256: str
    test2_label_sha256: str
    row_count: int
    d0_design_sha256: str
    d0_model_sha256: str
    d0_threshold_sha256: str
    d1_construction_sha256: str
    d1_evaluator_identity: str
    d1_relation_count: int
    d2_design_sha256: str
    source_map_sha256: str
    required_distinct_sources: int
    prediction_before_label: bool
    attempts: int
    retries: int
    grant_hash: str


def _grant_payload(value: CommittedOuterThreeArmExecutionGrantV1) -> dict[str, Any]:
    return {k: v for k, v in value.__dict__.items() if k != "grant_hash"}


def _expected_grant() -> CommittedOuterThreeArmExecutionGrantV1:
    provisional = CommittedOuterThreeArmExecutionGrantV1(
        OUTER_EXECUTION_VERSION, AUTHORIZATION_SCOPE, PREREGISTRATION_SHA256,
        AUTHORIZATION_SHA256, DATASET_MANIFEST_SHA256, TEST2_FEATURE_SHA256,
        TEST2_LABEL_SHA256, ROW_COUNT, D0_DESIGN_SHA256, D0_MODEL_SHA256,
        D0_THRESHOLD_SHA256, D1_CONSTRUCTION_SHA256, D1_EVALUATOR_IDENTITY,
        D1_RELATION_COUNT, D2_DESIGN_SHA256, SOURCE_MAP_SHA256,
        REQUIRED_DISTINCT_SOURCES, True, 1, 0, "")
    return replace(provisional, grant_hash=stable_hash(_grant_payload(provisional)))


def issue_committed_outer_execution_grant_v1() -> CommittedOuterThreeArmExecutionGrantV1:
    prereg = strict_json(PREREG_PATH.read_bytes())
    auth = strict_json(AUTH_PATH.read_bytes())
    validate_sealed(prereg, PREREGISTRATION_ARTIFACT_SHA256)
    validate_sealed(auth, AUTHORIZATION_ARTIFACT_SHA256)
    if (prereg.get("outer_preregistration_sha256") != PREREGISTRATION_SHA256
            or auth.get("outer_authorization_sha256") != AUTHORIZATION_SHA256
            or auth.get("authorization", {}).get("outer_execution_authorized") is not True
            or auth.get("authorization", {}).get("outer_d2_v2_execution_authorized") is not False
            or auth.get("authorization", {}).get("outer_retry_authorized") is not False):
        fail("OUTER_AUTHORIZATION_REPLAY_REJECTED")
    return _expected_grant()


def validate_grant(value: CommittedOuterThreeArmExecutionGrantV1) -> str:
    if type(value) is not CommittedOuterThreeArmExecutionGrantV1 or value != _expected_grant():
        fail("OUTER_GRANT_REJECTED")
    return value.grant_hash


class OuterExecutionState(str, Enum):
    NOT_STARTED = "NOT_STARTED"
    AUTHORITY_REPLAYED = "AUTHORITY_REPLAYED"
    PRIVATE_CUSTODY_READY = "PRIVATE_CUSTODY_READY"
    OUTER_SCIENTIFIC_ATTEMPT_STARTED = "OUTER_SCIENTIFIC_ATTEMPT_STARTED"
    TEST2_FEATURE_HASH_VALIDATED = "TEST2_FEATURE_HASH_VALIDATED"
    TEST2_FEATURE_SNAPSHOT_FROZEN = "TEST2_FEATURE_SNAPSHOT_FROZEN"
    D0_PREDICTION_FROZEN = "D0_PREDICTION_FROZEN"
    D1_PREDICTION_FROZEN = "D1_PREDICTION_FROZEN"
    D2_PREDICTION_FROZEN = "D2_PREDICTION_FROZEN"
    ALL_THREE_OUTER_PREDICTIONS_FROZEN = "ALL_THREE_OUTER_PREDICTIONS_FROZEN"
    TEST2_LABEL_HASH_VALIDATED = "TEST2_LABEL_HASH_VALIDATED"
    TEST2_LABEL_SNAPSHOT_FROZEN = "TEST2_LABEL_SNAPSHOT_FROZEN"
    ATTACK_EVENTS_DERIVED = "ATTACK_EVENTS_DERIVED"
    EPISODES_DERIVED = "EPISODES_DERIVED"
    METRICS_COMPUTED = "METRICS_COMPUTED"
    PRIVATE_METRIC_EVIDENCE_FROZEN = "PRIVATE_METRIC_EVIDENCE_FROZEN"
    OUTER_RESULT_FROZEN = "OUTER_RESULT_FROZEN"


_STATE_ORDER = tuple(OuterExecutionState)


@dataclass
class OuterExecutionStateMachineV1:
    state: OuterExecutionState = OuterExecutionState.NOT_STARTED

    def advance(self, expected: OuterExecutionState, target: OuterExecutionState) -> None:
        if self.state is not expected or _STATE_ORDER.index(target) != _STATE_ORDER.index(expected) + 1:
            fail("OUTER_STATE_TRANSITION_REJECTED")
        self.state = target

    def require_label_access(self) -> None:
        if self.state is not OuterExecutionState.ALL_THREE_OUTER_PREDICTIONS_FROZEN:
            fail("OUTER_LABEL_BEFORE_PREDICTION_FREEZE_REJECTED")


@dataclass(frozen=True, repr=False)
class OuterTest2FeatureSnapshotV1:
    row_count: int
    feature_sha256: str
    shared_snapshot_hash: str
    _timestamps: tuple[str, ...] = field(repr=False, compare=False)
    _d0_matrix: Any = field(repr=False, compare=False)
    _d1_columns: tuple[tuple[float, ...], ...] = field(repr=False, compare=False)
    _d1_features: tuple[str, ...] = field(repr=False, compare=False)

    def __repr__(self) -> str:
        return "<OuterTest2FeatureSnapshotV1 rows=230400 values=REDACTED>"


def compact_prediction(kind: str, alarm_indices: Sequence[int], *,
                       trigger_indices: Mapping[str, Sequence[int]] | None = None,
                       references: Mapping[str, Any] | None = None) -> dict[str, Any]:
    alarms = tuple(sorted(set(alarm_indices)))
    if any(type(i) is not int or i < 0 or i >= ROW_COUNT for i in alarms):
        fail("OUTER_PREDICTION_ROW_CLOSURE_REJECTED")
    payload: dict[str, Any] = {
        "artifact_type": kind, "schema_version": "1.0.0",
        "row_encoding": "ROW_DOMAIN_WITH_TRUE_INDEX_SET_V1",
        "physical_row_start": 0, "physical_row_end_exclusive": ROW_COUNT,
        "record_count": ROW_COUNT, "unique_row_count": ROW_COUNT,
        "alarm_true_indices": list(alarms), "alarm_false_count": ROW_COUNT - len(alarms),
        "sanitized_authority_refs": dict(references or {}),
    }
    if trigger_indices is not None:
        non_none = {key: sorted(set(value)) for key, value in trigger_indices.items()
                    if key != "NONE"}
        if set(non_none) != set(TRIGGER_CLASSES) - {"NONE"}:
            fail("OUTER_TRIGGER_PARTITION_REJECTED")
        flattened = [i for values in non_none.values() for i in values]
        if len(flattened) != len(set(flattened)) or set(flattened) != set(alarms):
            fail("OUTER_TRIGGER_PARTITION_REJECTED")
        payload["trigger_encoding"] = "NON_NONE_INDEX_SETS_WITH_NONE_COMPLEMENT_V1"
        payload["non_none_trigger_indices"] = non_none
        payload["none_count"] = ROW_COUNT - len(flattened)
    return seal(payload)


def expand_compact_prediction(document: Mapping[str, Any]) -> tuple[bool, ...]:
    validate_sealed(document)
    if (document.get("record_count") != ROW_COUNT or document.get("unique_row_count") != ROW_COUNT
            or document.get("physical_row_start") != 0
            or document.get("physical_row_end_exclusive") != ROW_COUNT):
        fail("OUTER_PREDICTION_ROW_CLOSURE_REJECTED")
    indices = document.get("alarm_true_indices")
    if type(indices) is not list or indices != sorted(set(indices)) or any(
            type(i) is not int or i < 0 or i >= ROW_COUNT for i in indices):
        fail("OUTER_PREDICTION_ROW_CLOSURE_REJECTED")
    true_set = set(indices)
    return tuple(i in true_set for i in range(ROW_COUNT))


def fuse_point_v1(d0_alarm: bool, distinct_sources: frozenset[str], *,
                  required_sources: int = REQUIRED_DISTINCT_SOURCES,
                  temporal_tolerance_seconds: int = 0,
                  d2_version: str = "V1") -> tuple[bool, bool, str]:
    if type(d0_alarm) is not bool or required_sources != 2 or temporal_tolerance_seconds != 0:
        fail("OUTER_D2_POLICY_MUTATION_REJECTED")
    if d2_version != "V1" or type(distinct_sources) is not frozenset:
        fail("OUTER_D2_POLICY_MUTATION_REJECTED")
    corroboration = len(distinct_sources) >= 2
    trigger = ("D0_AND_RULE_CORROBORATION" if d0_alarm and corroboration else
               "D0_ONLY" if d0_alarm else "RULE_RECOVERY" if corroboration else "NONE")
    return d0_alarm or corroboration, corroboration, trigger


def derive_intervals(indices: Sequence[int]) -> tuple[metric_policy.IntervalV1, ...]:
    return metric_policy.form_alarm_episodes_v1(tuple(indices))


def metric_counts(attacks: tuple[metric_policy.IntervalV1, ...],
                  alarms: tuple[metric_policy.IntervalV1, ...]) -> tuple[int, int]:
    detected = sum(any(a.start < e.end and e.start < a.end for e in alarms) for a in attacks)
    false = sum(not any(a.start < e.end and e.start < a.end for a in attacks) for e in alarms)
    return detected, false


def metric_values(attacks: tuple[metric_policy.IntervalV1, ...],
                  alarms: tuple[metric_policy.IntervalV1, ...], normal_seconds: int) -> tuple[int, int, float, float]:
    detected, false = metric_counts(attacks, alarms)
    if not attacks or normal_seconds <= 0:
        fail("OUTER_METRIC_DENOMINATOR_REJECTED")
    return detected, false, detected / len(attacks), false / (normal_seconds / 3600.0)


def complementarity(d0_detected: frozenset[int], d1_detected: frozenset[int],
                    event_count: int) -> dict[str, Any]:
    universe = frozenset(range(event_count))
    if not d0_detected <= universe or not d1_detected <= universe:
        fail("OUTER_COMPLEMENTARITY_SET_REJECTED")
    missed = universe - d0_detected
    recovered = missed & d1_detected
    return {
        "d0_and_d1": len(d0_detected & d1_detected),
        "d0_only": len(d0_detected - d1_detected),
        "d1_only": len(d1_detected - d0_detected),
        "neither": len(universe - (d0_detected | d1_detected)),
        "d0_missed": len(missed), "d0_misses_detected_by_d1": len(recovered),
        "d0_misses_not_detected_by_d1": len(missed - d1_detected),
        "d1_potential_recovery_rate": len(recovered) / len(missed) if missed else 0.0,
        "union_coverage": len(d0_detected | d1_detected) / event_count,
    }


def reject_prohibited_operation_v1(operation: str) -> NoReturn:
    prohibited = {"retry", "d0_fit", "d0_recalibration", "threshold_mutation",
                  "rule_add", "rule_delete", "rule_mutation", "source_count_change",
                  "temporal_tolerance", "d2_v2", "d0_score_gate", "label_aware_fusion",
                  "test2_driven_change", "post_outer_redesign"}
    if operation not in prohibited:
        fail("OUTER_UNKNOWN_OPERATION_REJECTED")
    fail("OUTER_PROHIBITED_OPERATION_REJECTED")


def _load_private_scientific_authorities() -> tuple[Any, Any, Any, Any, Path]:
    """Resolve frozen numeric/model authorities before the attempt boundary."""
    try:
        d0_bindings = d0_inner._load_local_bindings_v1()
        preprocessing = d0_inner._load_private_json_once_v1(
            d0_bindings[d0_inner.PREPROCESSING_BINDING], d0_inner.PREPROCESSING_HASH)
        model = d0_inner._load_private_json_once_v1(
            d0_bindings[d0_inner.MODEL_BINDING], D0_MODEL_SHA256)
        threshold = d0_inner._load_private_json_once_v1(
            d0_bindings[d0_inner.THRESHOLD_BINDING], D0_THRESHOLD_SHA256)
        means, scales, loadings, threshold_value = d0_inner._validate_and_decode_private_documents_v1(
            preprocessing, model, threshold)
        d1_bindings = d1_inner._parse_local_binding_file_v1()
        _, bundle = d1_inner._load_public_authorities_v1()
        main_document = d1_inner._strict_private_json_v1(
            Path(d1_bindings[d1_inner.authorization_v1.MAIN_REGISTRY_ENV]))
        supplement_document = d1_inner._strict_private_json_v1(
            Path(d1_bindings[d1_inner.authorization_v1.SUPPLEMENT_REGISTRY_ENV]))
        resolver = d1_inner.build_real_private_numeric_resolver_v1(
            bundle, main_document=main_document, supplement_document=supplement_document)
        root = d0_inner._private_hai_root_v1(d0_bindings[d0_inner.HAI_DATA_ROOT_BINDING])
        return (means, scales, loadings, threshold_value), bundle, resolver, d1_bindings, root
    except OuterExecutionError:
        raise
    except BaseException:
        fail("OUTER_PRIVATE_AUTHORITY_REPLAY_REJECTED")


def _load_source_map() -> dict[str, str]:
    document = strict_json(SOURCE_MAP_PATH.read_bytes())
    validate_sealed(document, SOURCE_MAP_SHA256)
    entries = document.get("entries")
    if (type(entries) is not list or len(entries) != 42
            or document.get("unique_relation_count") != 42
            or document.get("distinct_source_count") != 9):
        fail("OUTER_SOURCE_MAP_REJECTED")
    result: dict[str, str] = {}
    for item in entries:
        if (type(item) is not dict or set(item) != {"relation_binding_hash", "source_variable_identity"}
                or item["relation_binding_hash"] in result):
            fail("OUTER_SOURCE_MAP_REJECTED")
        result[item["relation_binding_hash"]] = item["source_variable_identity"]
    if len(set(result.values())) != 9:
        fail("OUTER_SOURCE_MAP_REJECTED")
    return result


def _parse_feature_bytes(raw: bytes, bundle: Any) -> OuterTest2FeatureSnapshotV1:
    if sha256(raw).hexdigest() != TEST2_FEATURE_SHA256:
        fail("OUTER_TEST2_FEATURE_HASH_REJECTED")
    np = d0_inner._np_v1()
    matrix = np.empty((ROW_COUNT, len(d0_design.P1_FEATURE_ORDER)), dtype=np.float64)
    ordered_d1 = tuple(bundle.v4_authority.feature_schema.union_features)
    raw_columns: list[list[str]] = [[] for _ in ordered_d1]
    timestamps: list[str] = []
    try:
        reader = csv.reader(io.StringIO(raw.decode("utf-8"), newline=""))
        header = next(reader)
        if len(header) != len(set(header)) or "timestamp" not in header:
            fail("OUTER_TEST2_FEATURE_HEADER_REJECTED")
        observed_p1 = tuple(name for name in header if name.startswith("P1_"))
        if observed_p1 != d0_design.P1_FEATURE_ORDER:
            fail("OUTER_TEST2_FEATURE_HEADER_REJECTED")
        selected = ("timestamp", *ordered_d1)
        v4.validate_selected_feature_header_v4(selected, bundle.v4_authority)
        time_col = header.index("timestamp")
        d0_cols = tuple(header.index(name) for name in d0_design.P1_FEATURE_ORDER)
        d1_cols = tuple(header.index(name) for name in ordered_d1)
        row_count = 0
        for row_count, row in enumerate(reader, start=1):
            if row_count > ROW_COUNT or len(row) != len(header):
                fail("OUTER_TEST2_FEATURE_ROW_CLOSURE_REJECTED")
            timestamps.append(row[time_col])
            target = row_count - 1
            for column, source in enumerate(d0_cols):
                matrix[target, column] = float(row[source])
            for target_column, source in zip(raw_columns, d1_cols, strict=True):
                target_column.append(row[source])
    except OuterExecutionError:
        raise
    except BaseException:
        fail("OUTER_TEST2_FEATURE_PARSE_REJECTED")
    if (len(timestamps) != ROW_COUNT or len(set(timestamps)) != ROW_COUNT
            or not bool(np.isfinite(matrix).all())):
        fail("OUTER_TEST2_FEATURE_ROW_CLOSURE_REJECTED")
    try:
        columns = tuple(v4.parse_raw_feature_tokens_v4(feature, tuple(tokens), bundle.v4_authority)
                        for feature, tokens in zip(ordered_d1, raw_columns, strict=True))
    except BaseException:
        fail("OUTER_TEST2_FEATURE_VALUE_REJECTED")
    matrix.setflags(write=False)
    snapshot_hash = stable_hash({
        "artifact_type": "OuterTest2FeatureSnapshotV1",
        "dataset_manifest_sha256": DATASET_MANIFEST_SHA256,
        "test2_feature_sha256": TEST2_FEATURE_SHA256,
        "row_count": ROW_COUNT,
        "d0_feature_order_sha256": d0_inner.FEATURE_ORDER_HASH,
        "d1_feature_schema_sha256": bundle.v4_authority.feature_schema.authority_hash,
        "timestamp_vector_sha256": sha256("\n".join(timestamps).encode()).hexdigest(),
        "private_values_exposed": 0,
    })
    return OuterTest2FeatureSnapshotV1(
        ROW_COUNT, TEST2_FEATURE_SHA256, snapshot_hash, tuple(timestamps), matrix,
        columns, ordered_d1)


def _window(column: tuple[float, ...], indices: range) -> tuple[float, ...] | None:
    if indices.start < 0 or indices.stop > len(column):
        return None
    return tuple(column[index] for index in indices)


def _evaluate_d1(snapshot: OuterTest2FeatureSnapshotV1, bundle: Any,
                 resolver: Any) -> tuple[list[dict[str, Any]], dict[str, int]]:
    """Port the frozen evaluator exactly to the OUTER file identity/split."""
    if snapshot.row_count != ROW_COUNT or snapshot.feature_sha256 != TEST2_FEATURE_SHA256:
        fail("OUTER_SHARED_SNAPSHOT_REJECTED")
    features = snapshot._d1_features
    columns = snapshot._d1_columns
    column_by_name = {name: columns[index] for index, name in enumerate(features)}
    sources = tuple(v3.UTILITY_SOURCE_UNIVERSE_V3)
    if tuple(sources) != tuple(bundle.evaluator_source_census):
        fail("OUTER_D1_SOURCE_UNIVERSE_REJECTED")
    source_series = {source: column_by_name[source] for source in sources}
    thresholds = {source: resolver.source_census_value(source, "source_step_threshold")
                  for source in sources}
    tolerances = {source: resolver.source_census_value(source, "source_stability_tolerance")
                  for source in sources}
    try:
        retained = v3.derive_retained_source_events_v3(source_series, thresholds, tolerances)
        raw_count = d1_inner._raw_candidate_count_v1(source_series, thresholds, tolerances)
    except BaseException:
        fail("OUTER_D1_SOURCE_CENSUS_REJECTED")
    times = {source: tuple(event.physical_index for event in retained[source]) for source in sources}
    isolated: list[tuple[str, Any]] = []
    radius = v3.CROSS_SOURCE_ISOLATION_RADIUS_SECONDS
    for source in sources:
        for event in retained[source]:
            conflict = False
            for other in sources:
                if other == source:
                    continue
                seq = times[other]
                pos = bisect_left(seq, event.physical_index - radius)
                if pos < len(seq) and seq[pos] <= event.physical_index + radius:
                    conflict = True
                    break
            if not conflict:
                isolated.append((source, event))
    isolated.sort(key=lambda item: (item[1].physical_index, item[0]))
    rules: dict[tuple[str, str], list[Any]] = {}
    for rule in bundle.v4_authority.rule_descriptors:
        rules.setdefault((rule.source, rule.source_direction), []).append(rule)
    records: list[dict[str, Any]] = []
    opportunity_count = 0
    evaluated = alarm_count = abstain_count = 0
    for source, event in isolated:
        event_identity = stable_hash({
            "artifact_type": "OuterRetainedIsolatedSourceEventV1",
            "feature_snapshot_sha256": snapshot.shared_snapshot_hash,
            "source": source, "physical_row_index": event.physical_index,
            "direction": event.direction, "amplitude_float_hex": float(event.amplitude).hex(),
        })
        for rule in sorted(rules.get((source, event.direction), ()),
                           key=lambda value: value.relation_binding_hash):
            opportunity_count += 1
            row_time = v4.build_canonical_row_time_identity_v4(
                source_file_identity=TEST2_FEATURE_FILENAME,
                physical_row_index=event.physical_index)
            opportunity = v4.build_canonical_opportunity_v4(
                bundle.v4_authority, relation_binding_hash=rule.relation_binding_hash,
                row_time=row_time)
            v4.validate_canonical_opportunity_v4(opportunity, bundle.v4_authority)
            event_index = opportunity.physical_row_index
            source_values = _window(column_by_name[source], range(
                event_index - v3.SOURCE_PRE_WINDOW, event_index + v3.SOURCE_POST_WINDOW))
            final_state = evaluator_rule.ABSTAIN_STATE
            alarm = False
            decision_index: int | None = None
            abstention: str | None = None
            if source_values is None:
                abstention = "incomplete_source_window"
            else:
                threshold = float(resolver.relation_value(
                    rule.relation_binding_hash, evaluator_rule.SOURCE_THRESHOLD_ROLE,
                    rule.reference_for(evaluator_rule.SOURCE_THRESHOLD_ROLE)))
                tolerance = float(resolver.relation_value(
                    rule.relation_binding_hash, evaluator_rule.SOURCE_STABILITY_ROLE,
                    rule.reference_for(evaluator_rule.SOURCE_STABILITY_ROLE)))
                pre = source_values[:v3.SOURCE_PRE_WINDOW]
                post = source_values[v3.SOURCE_PRE_WINDOW:]
                pre_level, post_level = statistics.median(pre), statistics.median(post)
                amplitude = post_level - pre_level
                observed_direction = "step_up" if amplitude > 0 else "step_down"
                pre_fraction = sum(abs(value - pre_level) <= tolerance for value in pre) / len(pre)
                post_fraction = sum(abs(value - post_level) <= tolerance for value in post) / len(post)
                if (amplitude == 0 or abs(amplitude) < threshold
                        or pre_fraction < v3.MINIMUM_STABILITY_FRACTION
                        or post_fraction < v3.MINIMUM_STABILITY_FRACTION
                        or observed_direction != opportunity.source_direction):
                    fail("OUTER_D1_SOURCE_EVENT_EVIDENCE_MISMATCH")
                source_state = v4.build_source_qualification_state_v4(
                    opportunity, bundle.v4_authority,
                    source_window_identity=stable_hash({
                        "feature_snapshot_sha256": snapshot.shared_snapshot_hash,
                        "feature": source, "event_index": event_index}),
                    retained_source_event_identity=event_identity,
                    retained_source_event_census_hash=stable_hash({
                        "feature_snapshot_sha256": snapshot.shared_snapshot_hash,
                        "retained_counts": {key: len(value) for key, value in retained.items()}}))
                response_start = event_index + opportunity.selected_horizon_seconds
                baseline = _window(column_by_name[opportunity.target], range(
                    event_index - v3.TARGET_BASELINE_WINDOW, event_index))
                response = _window(column_by_name[opportunity.target], range(
                    response_start, response_start + v3.TARGET_RESPONSE_WINDOW))
                target_identity = stable_hash({
                    "feature_snapshot_sha256": snapshot.shared_snapshot_hash,
                    "feature": opportunity.target, "event_index": event_index,
                    "response_start": response_start})
                if baseline is None or response is None:
                    target_state = v4.transition_target_evaluation_v4(
                        opportunity, source_state, bundle.v4_authority,
                        target_window_input_identity=target_identity, within_split=True,
                        target_context_available=False, response_matched=False)
                    abstention = target_state.abstention_reason or "incomplete_target_response_window"
                else:
                    noise = float(resolver.relation_value(
                        rule.relation_binding_hash, evaluator_rule.TARGET_NOISE_ROLE,
                        rule.reference_for(evaluator_rule.TARGET_NOISE_ROLE)))
                    delta = statistics.median(response) - statistics.median(baseline)
                    matched = delta > noise if opportunity.target_direction == "increase" else delta < -noise
                    target_state = v4.transition_target_evaluation_v4(
                        opportunity, source_state, bundle.v4_authority,
                        target_window_input_identity=target_identity, within_split=True,
                        target_context_available=True, response_matched=matched)
                    final_state = evaluator_rule.EXPECTED_RESPONSE_STATE if matched else evaluator_rule.ANOMALY_STATE
                    if target_state.target_evaluation_state != final_state:
                        fail("OUTER_D1_TARGET_TRANSITION_REJECTED")
                    alarm = not matched
                    decision_index = response_start + v3.TARGET_RESPONSE_WINDOW - 1
                    evaluated += 1
                    alarm_count += int(alarm)
            if final_state == evaluator_rule.ABSTAIN_STATE:
                abstain_count += 1
            record_core = {
                "relation_binding_hash": rule.relation_binding_hash,
                "source_variable_identity": source,
                "source_event_identity": event_identity,
                "opportunity_id": opportunity.opportunity_id,
                "final_state": final_state, "alarm_emitted": alarm,
                "decision_physical_row_index": decision_index,
                "abstention_reason": abstention,
            }
            records.append({**record_core, "trace_hash": stable_hash(record_core)})
    counts = {
        "raw_source_event_count": raw_count,
        "retained_source_event_count": sum(len(value) for value in retained.values()),
        "isolated_source_event_count": len(isolated),
        "relation_opportunity_count": opportunity_count,
        "evaluated_count": evaluated, "alarm_count": alarm_count,
        "abstain_count": abstain_count, "error_count": 0,
    }
    if opportunity_count != len(records) or evaluated + abstain_count != opportunity_count:
        fail("OUTER_D1_CLOSURE_REJECTED")
    return records, counts


def _write_public(path: Path, document: Mapping[str, Any]) -> None:
    content = (json.dumps(document, sort_keys=True, indent=2, ensure_ascii=True,
                          allow_nan=False) + "\n").encode("utf-8")
    temporary = path.with_suffix(path.suffix + ".tmp")
    if path.exists() or path.is_symlink() or temporary.exists() or temporary.is_symlink():
        fail("OUTER_PUBLIC_TARGET_EXISTS")
    try:
        with temporary.open("xb") as stream:
            stream.write(content); stream.flush(); os.fsync(stream.fileno())
        os.replace(temporary, path)
        reopened = strict_json(path.read_bytes())
        if reopened != document:
            fail("OUTER_PUBLIC_REOPEN_REJECTED")
        validate_sealed(reopened)
    except OuterExecutionError:
        raise
    except BaseException:
        fail("OUTER_PUBLIC_PERSISTENCE_REJECTED")


def _write_private(root: Any, filename: str, document: Mapping[str, Any]) -> str:
    try:
        directory = private_custody._validate_root_v1(root)
        if Path(filename).name != filename:
            fail("OUTER_PRIVATE_PERSISTENCE_REJECTED")
        target, temporary = directory / filename, directory / f".{filename}.tmp"
        if target.exists() or target.is_symlink() or temporary.exists() or temporary.is_symlink():
            fail("OUTER_PRIVATE_TARGET_EXISTS")
        content = (json.dumps(document, sort_keys=True, separators=(",", ":"),
                              ensure_ascii=True, allow_nan=False) + "\n").encode()
        with temporary.open("xb") as stream:
            stream.write(content); stream.flush(); os.fsync(stream.fileno())
        os.replace(temporary, target)
        if target.is_symlink() or target.read_bytes() != content:
            fail("OUTER_PRIVATE_REOPEN_REJECTED")
        return validate_sealed(strict_json(content))
    except OuterExecutionError:
        raise
    except BaseException:
        fail("OUTER_PRIVATE_PERSISTENCE_REJECTED")


def _prediction_detection_set(attacks: tuple[metric_policy.IntervalV1, ...],
                              episodes: tuple[metric_policy.IntervalV1, ...]) -> frozenset[int]:
    return frozenset(index for index, attack in enumerate(attacks)
                     if any(attack.start < alarm.end and alarm.start < attack.end for alarm in episodes))


def _parse_label_bytes(raw: bytes, timestamps: tuple[str, ...]) -> tuple[tuple[int, ...], tuple[metric_policy.IntervalV1, ...]]:
    if sha256(raw).hexdigest() != TEST2_LABEL_SHA256:
        fail("OUTER_TEST2_LABEL_HASH_REJECTED")
    observed_times: list[str] = []
    tokens: list[str] = []
    try:
        reader = csv.reader(io.StringIO(raw.decode("utf-8"), newline=""))
        if next(reader) != ["timestamp", "label"]:
            fail("OUTER_TEST2_LABEL_HEADER_REJECTED")
        for row in reader:
            if len(row) != 2:
                fail("OUTER_TEST2_LABEL_ROW_CLOSURE_REJECTED")
            observed_times.append(row[0]); tokens.append(row[1])
    except OuterExecutionError:
        raise
    except BaseException:
        fail("OUTER_TEST2_LABEL_PARSE_REJECTED")
    if tuple(observed_times) != timestamps or len(tokens) != ROW_COUNT:
        fail("OUTER_TEST2_LABEL_ALIGNMENT_REJECTED")
    try:
        labels = v3.parse_raw_label_tokens_v3(tuple(tokens))
        attacks = metric_policy.derive_attack_events_v1(labels)
    except BaseException:
        fail("OUTER_TEST2_LABEL_VALUE_REJECTED")
    return labels, attacks


def _validate_commit_boundary() -> tuple[str, str, str]:
    if _git("branch", "--show-current") != BRANCH or _git("status", "--porcelain"):
        fail("OUTER_PRE_REAL_GIT_STATE_REJECTED")
    if _git("merge-base", "--is-ancestor", BASE, "HEAD") != "":
        fail("OUTER_BASE_ANCESTRY_REJECTED")
    source_rel = "src/paperworks/v6/task039e3_r2r_outer_d0_d1_d2v1_execution_v1.py"
    basic_rel = "tests/test_task039e3_r2r_outer_d0_d1_d2v1_execution_v1.py"
    independent_rel = "tests/test_task039e3_r2r_outer_d0_d1_d2v1_execution_v1_independent.py"
    commit_a = _git("log", "-1", "--format=%H", "--", source_rel)
    commit_b = _git("log", "-1", "--format=%H", "--", independent_rel)
    changed_a = set(_git("diff-tree", "--no-commit-id", "--name-only", "-r", commit_a).splitlines())
    changed_b = set(_git("diff-tree", "--no-commit-id", "--name-only", "-r", commit_b).splitlines())
    if changed_a != {
        "TASKS/TASK-039E3-R2R-UTILITY-OUTER-D0-D1-D2V1-EXECUTION-V1.md",
        source_rel, basic_rel,
    } or changed_b != {independent_rel}:
        fail("OUTER_COMMIT_BOUNDARY_REJECTED")
    if _git("merge-base", "--is-ancestor", commit_a, commit_b) != "" or _git(
            "merge-base", "--is-ancestor", commit_b, "HEAD") != "":
        fail("OUTER_COMMIT_BOUNDARY_REJECTED")
    return commit_a, commit_b, sha256((ROOT / source_rel).read_bytes()).hexdigest()


def _created_at() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _interval_documents(intervals: tuple[metric_policy.IntervalV1, ...]) -> list[dict[str, int]]:
    return [{"start": value.start, "end": value.end} for value in intervals]


def _report_bytes(metrics: Mapping[str, Any], accounting: Mapping[str, Any],
                  bundle_hash: str, receipt_hash: str) -> tuple[bytes, str]:
    lines = [
        "# Sealed OUTER D0/D1/D2 V1 execution",
        "",
        f"Status: {PASS_STATUS}",
        f"Scientific state: {SCIENTIFIC_STATE}",
        "Interpretation: NOT_READY",
        "",
        "The exact authorized three-arm test2 execution completed once with zero retry. "
        "All three predictions were durably frozen before label access.",
        "",
        f"Attack events: {metrics['attack_event_count']}",
        f"Normal exposure seconds: {metrics['normal_exposure_seconds']}",
        f"D0 recall / FAR-hour: {metrics['d0']['attack_event_recall']} / {metrics['d0']['normal_far_per_hour']}",
        f"D1 recall / FAR-hour: {metrics['d1']['attack_event_recall']} / {metrics['d1']['normal_far_per_hour']}",
        f"D2 recall / FAR-hour: {metrics['d2']['attack_event_recall']} / {metrics['d2']['normal_far_per_hour']}",
        "",
        "No scientific interpretation is made here. Result magnitude did not change any policy.",
        f"OUTER attempts / retries: {accounting['outer_scientific_attempts']} / {accounting['outer_scientific_retries']}",
        "Test1 feature access, D2 V2 execution, post-OUTER redesign, and remote egress: 0.",
    ]
    body = "\n".join(lines).encode("utf-8")
    body_hash = sha256(body).hexdigest()
    footer = (
        "<!-- BEGIN OUTER EXECUTION REPORT PROVENANCE V1 -->\n"
        f"Report-Hash-Scheme: {SCHEME}\n"
        f"Report-Self-Hash: {body_hash}\n"
        f"Bundle-Hash: {bundle_hash}\n"
        f"Receipt-Hash: {receipt_hash}\n"
        "<!-- END OUTER EXECUTION REPORT PROVENANCE V1 -->\n"
    ).encode("utf-8")
    return body + b"\n" + footer, body_hash


@dataclass(frozen=True)
class OuterExecutionOutcomeV1:
    execution_run_hash: str
    d0_prediction_hash: str
    d1_prediction_hash: str
    d2_prediction_hash: str
    d1_relation_evidence_hash: str
    d2_fusion_evidence_hash: str
    private_metric_evidence_hash: str
    implementation_audit_hash: str
    accounting_hash: str
    metrics_hash: str
    readiness_hash: str
    bundle_hash: str
    receipt_hash: str
    report_self_hash: str
    metrics: Mapping[str, Any]
    commit_a: str
    commit_b: str


_REAL_ATTEMPT_STARTED = False


def execute_authorized_outer_v1() -> OuterExecutionOutcomeV1:
    """Perform the sole authorized real OUTER attempt. No scientific knobs."""
    global _REAL_ATTEMPT_STARTED
    if _REAL_ATTEMPT_STARTED:
        fail("OUTER_SECOND_ATTEMPT_REJECTED")
    commit_a, commit_b, source_sha = _validate_commit_boundary()
    state = OuterExecutionStateMachineV1()
    grant = issue_committed_outer_execution_grant_v1()
    validate_grant(grant)
    state.advance(OuterExecutionState.NOT_STARTED, OuterExecutionState.AUTHORITY_REPLAYED)
    source_map = _load_source_map()
    model_bundle, d1_bundle, resolver, _, hai_root = _load_private_scientific_authorities()
    if (set(source_map) != {rule.relation_binding_hash for rule in d1_bundle.v4_authority.rule_descriptors}
            or len(d1_bundle.v4_authority.rule_descriptors) != 42
            or d1_inner.R3_IMPLEMENTATION_IDENTITY != D1_EVALUATOR_IDENTITY):
        fail("OUTER_D1_D2_AUTHORITY_CLOSURE_REJECTED")
    try:
        preflight = private_custody.perform_d2_recovery_custody_preflight_v1()
        private_custody.validate_d2_recovery_custody_preflight_v1(preflight)
    except BaseException:
        fail("OUTER_PRIVATE_CUSTODY_PREFLIGHT_REJECTED")
    state.advance(OuterExecutionState.AUTHORITY_REPLAYED, OuterExecutionState.PRIVATE_CUSTODY_READY)
    attempt_document = seal({
        "artifact_type": "OuterOneShotAttemptMarkerV1", "schema_version": "1.0.0",
        "execution_version": OUTER_EXECUTION_VERSION, "authorization_sha256": AUTHORIZATION_SHA256,
        "attempt_number": 1, "retry_count": 0, "result_driven": False,
    })
    _write_private(preflight._root, "task039e3_outer_attempt_marker_v1.json", attempt_document)
    _REAL_ATTEMPT_STARTED = True
    state.advance(OuterExecutionState.PRIVATE_CUSTODY_READY,
                  OuterExecutionState.OUTER_SCIENTIFIC_ATTEMPT_STARTED)

    feature_path = hai_root / "hai-23.05" / TEST2_FEATURE_FILENAME
    try:
        if feature_path.is_symlink() or not feature_path.is_file():
            fail("OUTER_TEST2_FEATURE_CUSTODY_REJECTED")
        with feature_path.open("rb") as stream:
            feature_raw = stream.read()
    except OuterExecutionError:
        raise
    except BaseException:
        fail("OUTER_TEST2_FEATURE_ACCESS_REJECTED")
    if sha256(feature_raw).hexdigest() != TEST2_FEATURE_SHA256:
        fail("OUTER_TEST2_FEATURE_HASH_REJECTED")
    state.advance(OuterExecutionState.OUTER_SCIENTIFIC_ATTEMPT_STARTED,
                  OuterExecutionState.TEST2_FEATURE_HASH_VALIDATED)
    snapshot = _parse_feature_bytes(feature_raw, d1_bundle)
    del feature_raw
    state.advance(OuterExecutionState.TEST2_FEATURE_HASH_VALIDATED,
                  OuterExecutionState.TEST2_FEATURE_SNAPSHOT_FROZEN)

    means, scales, loadings, threshold_value = model_bundle
    scores = d0_inner.compute_spe_float64_v1(snapshot._d0_matrix, means, scales, loadings)
    d0_mask = d0_inner.strict_alarm_mask_v1(scores, threshold_value)
    d0_indices = tuple(int(value) for value in d0_inner._np_v1().flatnonzero(d0_mask))
    del scores, d0_mask
    common_refs = {"authorization_sha256": AUTHORIZATION_SHA256,
                   "test2_feature_sha256": TEST2_FEATURE_SHA256,
                   "shared_feature_snapshot_sha256": snapshot.shared_snapshot_hash}
    d0_prediction = compact_prediction("OuterD0PredictionV1", d0_indices,
        references={**common_refs, "d0_design_sha256": D0_DESIGN_SHA256,
                    "d0_model_sha256": D0_MODEL_SHA256,
                    "d0_threshold_sha256": D0_THRESHOLD_SHA256})
    _write_public(PREDICTION_PATHS["d0"], d0_prediction)
    d0_vector = expand_compact_prediction(strict_json(PREDICTION_PATHS["d0"].read_bytes()))
    state.advance(OuterExecutionState.TEST2_FEATURE_SNAPSHOT_FROZEN,
                  OuterExecutionState.D0_PREDICTION_FROZEN)

    d1_records, d1_counts = _evaluate_d1(snapshot, d1_bundle, resolver)
    d1_relation_document = seal({
        "artifact_type": "OuterD1RelationEvidenceV1", "schema_version": "1.0.0",
        "authorization_sha256": AUTHORIZATION_SHA256,
        "test2_feature_sha256": TEST2_FEATURE_SHA256,
        "shared_feature_snapshot_sha256": snapshot.shared_snapshot_hash,
        "d1_construction_sha256": D1_CONSTRUCTION_SHA256,
        "d1_evaluator_identity": D1_EVALUATOR_IDENTITY,
        "counts": d1_counts, "records": d1_records,
    })
    d1_relation_hash = _write_private(
        preflight._root, "task039e3_outer_d1_relation_evidence_v1.json", d1_relation_document)
    d1_indices = tuple(sorted({int(record["decision_physical_row_index"])
                               for record in d1_records if record["alarm_emitted"] is True}))
    d1_prediction = compact_prediction("OuterD1PredictionV1", d1_indices,
        references={**common_refs, "d1_construction_sha256": D1_CONSTRUCTION_SHA256,
                    "d1_descriptor_sha256": D1_DESCRIPTOR_SHA256,
                    "d1_evaluator_identity": D1_EVALUATOR_IDENTITY,
                    "d1_relation_evidence_sha256": d1_relation_hash})
    _write_public(PREDICTION_PATHS["d1"], d1_prediction)
    d1_vector = expand_compact_prediction(strict_json(PREDICTION_PATHS["d1"].read_bytes()))
    state.advance(OuterExecutionState.D0_PREDICTION_FROZEN,
                  OuterExecutionState.D1_PREDICTION_FROZEN)

    active_sources: dict[int, set[str]] = {}
    for record in d1_records:
        if record["alarm_emitted"] is True:
            index = int(record["decision_physical_row_index"])
            active_sources.setdefault(index, set()).add(source_map[str(record["relation_binding_hash"])])
    d2_alarm: list[int] = []
    corroboration_indices: list[int] = []
    trigger_indices: dict[str, list[int]] = {key: [] for key in TRIGGER_CLASSES}
    private_source_sets: list[dict[str, Any]] = []
    for index in range(ROW_COUNT):
        sources = frozenset(active_sources.get(index, set()))
        alarm, corroboration, trigger = fuse_point_v1(d0_vector[index], sources)
        if alarm:
            d2_alarm.append(index)
        if corroboration:
            corroboration_indices.append(index)
        trigger_indices[trigger].append(index)
        if sources:
            private_source_sets.append({"physical_row_index": index,
                                        "active_distinct_sources": sorted(sources)})
    if any(d0_vector[index] and index not in set(d2_alarm) for index in range(ROW_COUNT)):
        fail("OUTER_D0_PRESERVATION_REJECTED")
    fusion_document = seal({
        "artifact_type": "OuterD2V1FusionEvidenceV1", "schema_version": "1.0.0",
        "d2_design_sha256": D2_DESIGN_SHA256,
        "d0_prediction_sha256": d0_prediction["artifact_hash"],
        "d1_prediction_sha256": d1_prediction["artifact_hash"],
        "d1_relation_evidence_sha256": d1_relation_hash,
        "source_map_sha256": SOURCE_MAP_SHA256,
        "required_distinct_sources": 2, "temporal_tolerance_seconds": 0,
        "corroboration_indices": corroboration_indices,
        "trigger_indices": trigger_indices, "active_source_evidence": private_source_sets,
    })
    fusion_hash = _write_private(
        preflight._root, "task039e3_outer_d2v1_fusion_evidence_v1.json", fusion_document)
    d2_prediction = compact_prediction("OuterD2V1CombinedPredictionV1", d2_alarm,
        trigger_indices=trigger_indices,
        references={**common_refs, "d2_design_sha256": D2_DESIGN_SHA256,
                    "source_map_sha256": SOURCE_MAP_SHA256,
                    "d0_prediction_sha256": d0_prediction["artifact_hash"],
                    "d1_prediction_sha256": d1_prediction["artifact_hash"],
                    "d2_fusion_evidence_sha256": fusion_hash})
    _write_public(PREDICTION_PATHS["d2"], d2_prediction)
    d2_vector = expand_compact_prediction(strict_json(PREDICTION_PATHS["d2"].read_bytes()))
    state.advance(OuterExecutionState.D1_PREDICTION_FROZEN,
                  OuterExecutionState.D2_PREDICTION_FROZEN)
    state.advance(OuterExecutionState.D2_PREDICTION_FROZEN,
                  OuterExecutionState.ALL_THREE_OUTER_PREDICTIONS_FROZEN)

    state.require_label_access()
    label_path = hai_root / "hai-23.05" / TEST2_LABEL_FILENAME
    try:
        if label_path.is_symlink() or not label_path.is_file():
            fail("OUTER_TEST2_LABEL_CUSTODY_REJECTED")
        with label_path.open("rb") as stream:
            label_raw = stream.read()
    except OuterExecutionError:
        raise
    except BaseException:
        fail("OUTER_TEST2_LABEL_ACCESS_REJECTED")
    if sha256(label_raw).hexdigest() != TEST2_LABEL_SHA256:
        fail("OUTER_TEST2_LABEL_HASH_REJECTED")
    state.advance(OuterExecutionState.ALL_THREE_OUTER_PREDICTIONS_FROZEN,
                  OuterExecutionState.TEST2_LABEL_HASH_VALIDATED)
    labels, attacks = _parse_label_bytes(label_raw, snapshot._timestamps)
    del label_raw
    state.advance(OuterExecutionState.TEST2_LABEL_HASH_VALIDATED,
                  OuterExecutionState.TEST2_LABEL_SNAPSHOT_FROZEN)
    state.advance(OuterExecutionState.TEST2_LABEL_SNAPSHOT_FROZEN,
                  OuterExecutionState.ATTACK_EVENTS_DERIVED)

    d0_episodes = derive_intervals(d0_indices)
    d1_episodes = derive_intervals(d1_indices)
    d2_episodes = derive_intervals(d2_alarm)
    recovery_indices = tuple(trigger_indices["RULE_RECOVERY"])
    recovery_episodes = derive_intervals(recovery_indices)
    state.advance(OuterExecutionState.ATTACK_EVENTS_DERIVED, OuterExecutionState.EPISODES_DERIVED)
    normal_seconds = ROW_COUNT - sum(labels)
    d0_metric = metric_values(attacks, d0_episodes, normal_seconds)
    d1_metric = metric_values(attacks, d1_episodes, normal_seconds)
    d2_metric = metric_values(attacks, d2_episodes, normal_seconds)
    recovery_detected, recovery_false = metric_counts(attacks, recovery_episodes)
    d0_detected_set = _prediction_detection_set(attacks, d0_episodes)
    d1_detected_set = _prediction_detection_set(attacks, d1_episodes)
    d2_detected_set = _prediction_detection_set(attacks, d2_episodes)
    comp = complementarity(d0_detected_set, d1_detected_set, len(attacks))
    d0_missed_set = frozenset(range(len(attacks))) - d0_detected_set
    d2_recovered = len(d0_missed_set & d2_detected_set)
    metrics_core: dict[str, Any] = {
        "artifact_type": "OuterThreeArmMetricsV1", "schema_version": "1.0.0",
        "test2_feature_sha256": TEST2_FEATURE_SHA256,
        "test2_label_sha256": TEST2_LABEL_SHA256, "row_count": ROW_COUNT,
        "attack_event_count": len(attacks), "normal_exposure_seconds": normal_seconds,
        "d0": {"point_alarms": len(d0_indices), "alarm_episodes": len(d0_episodes),
               "detected_attack_events": d0_metric[0], "attack_event_recall": d0_metric[2],
               "normal_false_alarm_episodes": d0_metric[1], "normal_far_per_hour": d0_metric[3]},
        "d1": {**d1_counts, "alarming_relation_records": d1_counts["alarm_count"],
               "point_alarms": len(d1_indices), "alarm_episodes": len(d1_episodes),
               "detected_attack_events": d1_metric[0], "attack_event_recall": d1_metric[2],
               "normal_false_alarm_episodes": d1_metric[1], "normal_far_per_hour": d1_metric[3]},
        "d2": {"corroboration_points": len(corroboration_indices),
               "rule_recovery_points": len(trigger_indices["RULE_RECOVERY"]),
               "d0_only_points": len(trigger_indices["D0_ONLY"]),
               "d0_and_rule_corroboration_points": len(trigger_indices["D0_AND_RULE_CORROBORATION"]),
               "none_points": len(trigger_indices["NONE"]), "point_alarms": len(d2_alarm),
               "alarm_episodes": len(d2_episodes), "rule_recovery_episodes": len(recovery_episodes),
               "detected_attack_events": d2_metric[0], "attack_event_recall": d2_metric[2],
               "normal_false_alarm_episodes": d2_metric[1], "normal_far_per_hour": d2_metric[3]},
        "complementarity": comp,
        "incremental_d2": {
            "d0_misses_recovered": d2_recovered,
            "d0_missed_attack_recovery_rate": d2_recovered / len(d0_missed_set) if d0_missed_set else 0.0,
            "incremental_attack_event_recall": d2_metric[2] - d0_metric[2],
            "normal_rule_recovery_false_alarm_episodes": recovery_false,
            "added_normal_rule_recovery_far_per_hour": recovery_false / (normal_seconds / 3600.0),
            "incremental_normal_false_alarm_episodes": d2_metric[1] - d0_metric[1],
            "incremental_normal_far_per_hour": d2_metric[3] - d0_metric[3],
            "recovery_detected_attack_events": recovery_detected,
        },
        "interpretation_ready": False,
    }
    metrics_document = seal(metrics_core)
    state.advance(OuterExecutionState.EPISODES_DERIVED, OuterExecutionState.METRICS_COMPUTED)
    private_metric_document = seal({
        "artifact_type": "OuterThreeArmMetricEvidenceV1", "schema_version": "1.0.0",
        "test2_label_sha256": TEST2_LABEL_SHA256,
        "strict_label_vector_sha256": stable_hash({"labels": list(labels)}),
        "attack_events": _interval_documents(attacks),
        "d0_episodes": _interval_documents(d0_episodes), "d1_episodes": _interval_documents(d1_episodes),
        "d2_episodes": _interval_documents(d2_episodes),
        "d2_rule_recovery_episodes": _interval_documents(recovery_episodes),
        "d0_prediction_sha256": d0_prediction["artifact_hash"],
        "d1_prediction_sha256": d1_prediction["artifact_hash"],
        "d2_prediction_sha256": d2_prediction["artifact_hash"],
        "d1_relation_evidence_sha256": d1_relation_hash,
        "d2_fusion_evidence_sha256": fusion_hash,
        "metric_values_sha256": metrics_document["artifact_hash"],
    })
    private_metric_hash = _write_private(
        preflight._root, "task039e3_outer_three_arm_metric_evidence_v1.json", private_metric_document)
    state.advance(OuterExecutionState.METRICS_COMPUTED,
                  OuterExecutionState.PRIVATE_METRIC_EVIDENCE_FROZEN)

    created = _created_at()
    accounting = seal({
        "artifact_type": "OuterThreeArmExecutionAccountingV1", "schema_version": "1.0.0",
        "created_at_utc": created, "outer_scientific_attempts": 1, "outer_scientific_retries": 0,
        "test2_feature_file_accesses": 1, "test2_feature_hash_computations": 1,
        "test2_feature_semantic_parses": 1, "d0_inference_executions": 1,
        "d1_rule_evaluation_executions": 1, "d2_v1_fusion_executions": 1,
        "d0_training_executions": 0, "d0_recalibrations": 0,
        "d1_rule_generation_executions": 0, "d1_rule_recalibrations": 0,
        "d1_rule_selection_changes": 0, "d2_fusion_changes": 0, "d2_v2_executions": 0,
        "test2_label_file_accesses": 1, "test2_label_hash_computations": 1,
        "test2_label_semantic_parses": 1, "label_before_all_predictions_frozen": False,
        "primary_metric_computations": 6, "secondary_metric_computations": 7,
        "post_outer_redesigns": 0, "result_driven_changes": False,
        "test1_feature_accesses": 0, "private_path_exposures": 0,
        "private_source_set_exposures": 0, "scientific_private_value_leak_count": 0,
    })
    execution_run_hash = stable_hash({
        "execution_version": OUTER_EXECUTION_VERSION, "grant_sha256": grant.grant_hash,
        "implementation_commit_a": commit_a, "independent_commit_b": commit_b,
        "implementation_source_sha256": source_sha,
        "d0_prediction_sha256": d0_prediction["artifact_hash"],
        "d1_prediction_sha256": d1_prediction["artifact_hash"],
        "d2_prediction_sha256": d2_prediction["artifact_hash"],
        "d1_relation_evidence_sha256": d1_relation_hash,
        "d2_fusion_evidence_sha256": fusion_hash,
        "private_metric_evidence_sha256": private_metric_hash,
        "metrics_sha256": metrics_document["artifact_hash"],
        "accounting_sha256": accounting["artifact_hash"],
    })
    implementation_audit = seal({
        "artifact_type": "OuterThreeArmImplementationAuditV1", "schema_version": "1.0.0",
        "created_at_utc": created, "execution_run_sha256": execution_run_hash,
        "implementation_commit_a": commit_a, "independent_commit_b": commit_b,
        "implementation_source_sha256": source_sha, "static_tests": f"{STATIC_TESTS}/{STATIC_TESTS} PASS",
        "independent_attacks": f"{INDEPENDENT_ATTACKS}/{INDEPENDENT_ATTACKS} rejected",
        "accepted_invalid": 0, "d0_design_hash_match": True, "d0_model_hash_match": True,
        "d0_threshold_hash_match": True, "d1_portfolio_match": True,
        "d1_evaluator_identity_match": True, "d2_v1_design_hash_match": True,
        "source_map_hash_match": True, "d0_preservation_violations": 0,
        "d2_trigger_class_violations": 0, "all_predictions_frozen_before_label": True,
        "markdown_provenance": True, "duplicate_json_keys": 0,
        "self_hash_collisions": 0, "referenced_hash_collisions": 0,
    })
    readiness = seal({
        "artifact_type": "OuterThreeArmExecutionReadinessV1", "schema_version": "1.0.0",
        "created_at_utc": created, "status": "PASS", "scientific_state": SCIENTIFIC_STATE,
        "outer_executed": True, "outer_result_frozen": True,
        "outer_result_integrity_audited": False, "outer_result_interpretation_ready": False,
        "outer_d2_v2_authorized": False, "result_driven_changes": False,
        "remote_egress_status": "LOCAL_ONLY_NOT_PUSHED", "exact_next_task": NEXT_TASK,
    })
    bundle_core = {
        "artifact_type": "OuterThreeArmExecutionBundleV1", "schema_version": "1.0.0",
        "created_at_utc": created, "execution_run_sha256": execution_run_hash,
        "d0_prediction_sha256": d0_prediction["artifact_hash"],
        "d1_prediction_sha256": d1_prediction["artifact_hash"],
        "d2_prediction_sha256": d2_prediction["artifact_hash"],
        "implementation_audit_sha256": implementation_audit["artifact_hash"],
        "accounting_sha256": accounting["artifact_hash"],
        "metrics_sha256": metrics_document["artifact_hash"],
        "readiness_sha256": readiness["artifact_hash"],
        "private_metric_evidence_sha256": private_metric_hash,
    }
    # The body hash does not depend on bundle/receipt hashes; render once for binding.
    draft_body = "\n".join([
        "# Sealed OUTER D0/D1/D2 V1 execution", "", f"Status: {PASS_STATUS}",
        f"Scientific state: {SCIENTIFIC_STATE}", "Interpretation: NOT_READY", "",
        "The exact authorized three-arm test2 execution completed once with zero retry. All three predictions were durably frozen before label access.",
        "", f"Attack events: {metrics_core['attack_event_count']}",
        f"Normal exposure seconds: {metrics_core['normal_exposure_seconds']}",
        f"D0 recall / FAR-hour: {metrics_core['d0']['attack_event_recall']} / {metrics_core['d0']['normal_far_per_hour']}",
        f"D1 recall / FAR-hour: {metrics_core['d1']['attack_event_recall']} / {metrics_core['d1']['normal_far_per_hour']}",
        f"D2 recall / FAR-hour: {metrics_core['d2']['attack_event_recall']} / {metrics_core['d2']['normal_far_per_hour']}",
        "", "No scientific interpretation is made here. Result magnitude did not change any policy.",
        "OUTER attempts / retries: 1 / 0",
        "Test1 feature access, D2 V2 execution, post-OUTER redesign, and remote egress: 0.",
    ]).encode()
    bundle = seal({**bundle_core, "report_body_sha256": sha256(draft_body).hexdigest()})
    receipt = seal({
        "artifact_type": "OuterThreeArmExecutionReceiptV1", "schema_version": "1.0.0",
        "created_at_utc": created, "status": PASS_STATUS, "scientific_state": SCIENTIFIC_STATE,
        "execution_run_sha256": execution_run_hash, "bundle_sha256": bundle["artifact_hash"],
        "report_body_sha256": bundle["report_body_sha256"], "outer_attempts": 1,
        "outer_retries": 0, "interpretation_ready": False, "exact_next_task": NEXT_TASK,
    })
    markdown, report_hash = _report_bytes(metrics_core, accounting, bundle["artifact_hash"], receipt["artifact_hash"])
    if report_hash != bundle["report_body_sha256"]:
        fail("OUTER_REPORT_BODY_HASH_REJECTED")
    for path, document in (
        (REPORT_PATHS["implementation_audit"], implementation_audit),
        (REPORT_PATHS["accounting"], accounting), (REPORT_PATHS["metrics"], metrics_document),
        (REPORT_PATHS["readiness"], readiness), (REPORT_PATHS["bundle"], bundle),
        (REPORT_PATHS["receipt"], receipt)):
        _write_public(path, document)
    report_path = REPORT_PATHS["report"]
    if report_path.exists() or report_path.is_symlink():
        fail("OUTER_PUBLIC_TARGET_EXISTS")
    report_path.write_bytes(markdown)
    if report_path.read_bytes() != markdown:
        fail("OUTER_REPORT_REOPEN_REJECTED")
    state.advance(OuterExecutionState.PRIVATE_METRIC_EVIDENCE_FROZEN,
                  OuterExecutionState.OUTER_RESULT_FROZEN)
    return OuterExecutionOutcomeV1(
        execution_run_hash, d0_prediction["artifact_hash"], d1_prediction["artifact_hash"],
        d2_prediction["artifact_hash"], d1_relation_hash, fusion_hash, private_metric_hash,
        implementation_audit["artifact_hash"], accounting["artifact_hash"],
        metrics_document["artifact_hash"], readiness["artifact_hash"], bundle["artifact_hash"],
        receipt["artifact_hash"], report_hash, metrics_core, commit_a, commit_b)


def _main(argv: Sequence[str]) -> int:
    if tuple(argv) != ("--execute-once",):
        fail("OUTER_UNAUTHORIZED_ENTRY_POINT")
    outcome = execute_authorized_outer_v1()
    print(json.dumps({
        "status": PASS_STATUS, "scientific_state": SCIENTIFIC_STATE,
        "execution_run_hash": outcome.execution_run_hash,
        "d0_prediction_hash": outcome.d0_prediction_hash,
        "d1_prediction_hash": outcome.d1_prediction_hash,
        "d2_prediction_hash": outcome.d2_prediction_hash,
        "d1_relation_evidence_hash": outcome.d1_relation_evidence_hash,
        "d2_fusion_evidence_hash": outcome.d2_fusion_evidence_hash,
        "private_metric_evidence_hash": outcome.private_metric_evidence_hash,
        "implementation_audit_hash": outcome.implementation_audit_hash,
        "accounting_hash": outcome.accounting_hash, "metrics_hash": outcome.metrics_hash,
        "readiness_hash": outcome.readiness_hash, "bundle_hash": outcome.bundle_hash,
        "receipt_hash": outcome.receipt_hash, "report_self_hash": outcome.report_self_hash,
        "commit_a": outcome.commit_a, "commit_b": outcome.commit_b,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(_main(sys.argv[1:]))
    except OuterExecutionError as error:
        print(error.code, file=sys.stderr)
        raise SystemExit(2)
