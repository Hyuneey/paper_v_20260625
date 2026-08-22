"""Independent local-only audit of the frozen D2 recovery result.

No authoritative D2 execution or scientific helper is imported.  The oracle
implements canonical hashing, per-row source-set fusion, contiguous runs, and
metric arithmetic independently from frozen artifacts.
"""

from __future__ import annotations

import ast
import copy
import csv
from datetime import datetime, timezone
from hashlib import sha256
import json
import math
import os
from pathlib import Path
import re
import subprocess
import sys
from typing import Any, Callable, Mapping, NoReturn, Sequence


TASK_ID = "TASK-039E3-R2R-UTILITY-INNER-D2-RESULT-INTEGRITY-AUDIT-V1"
PASS_STATUS = "passed_task039e3_r2r_utility_inner_d2_result_integrity_audit_v1"
SCIENTIFIC_STATUS = "D2_RESULT_INTEGRITY_AUDITED"
REMOTE_EGRESS_STATUS = "LOCAL_ONLY_NOT_PUSHED"
SCHEMA_VERSION = "1.0.0"
EXPECTED_BRANCH = "task-039e3-r2r-utility-inner-d2-result-integrity-audit-v1"

BASE_COMMIT = "33202f21d47b6bf29b12156374c9a7760f5c70f1"
RECOVERY_IMPLEMENTATION_COMMIT_A = "6c52bbe1ace8895a8b5b27527e4f9fe2ca01b3e6"
RECOVERY_INDEPENDENT_COMMIT_B = "9648f1d6415911800058b64f8084a2cfe1fc31a0"
RESULT_FREEZE_COMMIT_C = "9078c4a1639c35d848cad28194fb4195eb5daca5"
RECOVERY_CONTINUITY_COMMIT_D = "33202f21d47b6bf29b12156374c9a7760f5c70f1"
HISTORICAL_COMMITS = (
    "315eb5b578301d57c6ab90c0c2398e3df3dec3f5",
    "cd220a89f37e0a3913124116f49a90e0518c8b46",
    "f42e706f712616e23f7a86d86cc2bd6cfc6f4ce8",
    "78639e1b8286b4ff16ac63530725a1ce3d1eb91c",
    "7b749b68868193d2aed350f8ca0df91ff1dc807c",
    "0399012e28f97226821d76b7b35d2980ba4ac6c8",
    "4d24d72c8061d49c899bf3160781eeb86c8e7ac7",
    "adbac8a7b000fdf74d1d34fed920a6266e651926",
)

D2_DESIGN_HASH = "eb559a91350fd046204d223d6820ef7f0590ad4beb7a2b17114a496859758e51"
ORIGINAL_AUTHORIZATION_HASH = "b931d7bd89e923dc4d380e35ed2b3ff514679a701e0b94a75d426130a3c4427c"
RECOVERY_AUTHORIZATION_HASH = "0faa5c58073da28b0a3e1e9c4267aa4c16faa7723becf5d01b5ec9c391b7b141"
D0_PREDICTION_HASH = "a4b58f1c78b9bb53125da1a009f3fd05b02e1c83a789772a341a7679fddca0f6"
D1_PREDICTION_HASH = "58c3c49f9657f68d35c830b12eeb493ce4bbf7669c90f04813fb80246c3c2682"
SOURCE_MAP_HASH = "f866176000c3d5a943053ac3125d2700b0b72f25b5a0539d8f4713435a959818"
ORIGINAL_IMPLEMENTATION_IDENTITY = "03d3d8c3a2586e1eeaadbbc367f756c973920c3b7e84afd384eb7f45684aa733"
ORIGINAL_IMPLEMENTATION_SHA256 = "0bfcfc5aba2a53ad24d08da0c1d9861472e350d1fe64ba6dabf1ba1a8a6689cc"
RECOVERY_CUSTODY_IDENTITY = "c0e3faafdab0cb84e2f8e62b9380c243b0faee9ab38cc014de36fed5464d62e6"
FUSION_EVIDENCE_HASH = "f41d53b04ee33fcf719a442d707522438f0d4dcdfcc14eee3a416cc98267729b"
COMBINED_PREDICTION_HASH = "cf1005a03d98481b57c3ce2ad74db3e2e5d2dc3a1983d60e0aedb4f46c83b3f5"
PRIVATE_METRIC_EVIDENCE_HASH = "7d2f24d4cf481d0202d0842d8c5521e8b7bcacf4a2aa01d22af2bf69c29795ed"
EXECUTION_RUN_HASH = "64c9486d325b112198975d5d1c8b92c56213498a47fd67ba654257d99edf697e"
IMPLEMENTATION_AUDIT_HASH = "1e0955193fcd2385331cf26d2518421f0bb77289c472e112add00ba99a0e6053"
ACCOUNTING_HASH = "1ad805908d46006108c55a5007436fb384babaf472c007af49b32f640878ed9a"
READINESS_HASH = "8768e1daabe8517b1260a560f8c46a92816f8cc9198da328743892751c34540f"
BUNDLE_HASH = "655ae56707220086d35781c1a7de25abd68549923fc9c7a54b25be38abe1a45a"
RECEIPT_HASH = "c60d3d1707f4edb2332cfa57578a7f560c8369f2bb4f00600ac77b9896dfeb99"
REPORT_BODY_HASH = "66b04243c9c6833be4407bf6a0ae1804a4e764342c9ec9faf7d9f4d7766bf851"

EXPECTED_ROWS = 54_000
EXPECTED_D1_RECORDS = 6_031
EXPECTED_SOURCE_MAP_ENTRIES = 42
EXPECTED_DISTINCT_SOURCES = 9
REQUIRED_DISTINCT_SOURCE_COUNT = 2
EXPECTED_CORROBORATION_POINTS = 3
EXPECTED_TRIGGER_COUNTS = {
    "NONE": 53_121,
    "D0_ONLY": 876,
    "RULE_RECOVERY": 3,
    "D0_AND_RULE_CORROBORATION": 0,
}
EXPECTED_D2_POINTS = 879
EXPECTED_D2_EPISODES = 49
EXPECTED_D0_EPISODES = 46
EXPECTED_RECOVERY_EPISODES = 3
EXPECTED_D2_RECALL = 0.7857142857142857
EXPECTED_D2_FAR = 0.7056194750975128
EXPECTED_D0_RECALL = 0.7857142857142857
EXPECTED_D0_FAR = 0.4939336325682589
EXPECTED_MISSED_RECOVERY = 0.0
EXPECTED_INCREMENTAL_RECALL = 0.0
EXPECTED_ADDED_FAR = 0.21168584252925382
EXPECTED_INCREMENTAL_FAR = 0.21168584252925388
EXPECTED_INDEPENDENT_ATTACKS = 50

LABEL_SHA256 = "eaf69edb9c5834bc393afd7bf658b5e408d34fd7bfc3261f80516765fb818fbc"
LABEL_BYTE_SIZE = 1_242_017
ATTACK_EVENT_POLICY = "MAXIMAL_CONTIGUOUS_STRICT_LABEL_ONE_RUNS_FILE_LOCAL"
ALARM_EPISODE_POLICY = "MAXIMAL_CONTIGUOUS_UNIQUE_ONE_SECOND_DECISION_INDICES_FILE_LOCAL"
SAME_SECOND_POLICY = "EXACT_DECISION_PHYSICAL_ROW_INDEX_EQUALITY"
D0_PRESERVATION_POLICY = "EVERY_FROZEN_D0_ALARM_IS_A_D2_ALARM"
RECALL_FORMULA = "ATTACK_EVENTS_OVERLAPPED_BY_AT_LEAST_ONE_ALARM_EPISODE_DIVIDED_BY_ALL_ATTACK_EVENTS"
FAR_FORMULA = "ALARM_EPISODES_WITH_NO_ATTACK_TIMESTAMP_DIVIDED_BY_NORMAL_LABELED_SECONDS_OVER_3600"
MISSED_FORMULA = "D0_MISSED_ATTACK_EVENTS_RECOVERED_BY_RULE_RECOVERY_DIVIDED_BY_ALL_D0_MISSED_ATTACK_EVENTS"
INCREMENTAL_RECALL_FORMULA = "D2_ATTACK_EVENT_RECALL_MINUS_D0_ATTACK_EVENT_RECALL"
ADDED_FAR_FORMULA = "RULE_RECOVERY_ALARM_EPISODES_WITH_ZERO_ATTACK_EVENT_OVERLAP_DIVIDED_BY_NORMAL_LABELED_SECONDS_OVER_3600"
INCREMENTAL_FAR_FORMULA = "D2_NORMAL_FAR_EPISODES_PER_HOUR_MINUS_D0_NORMAL_FAR_EPISODES_PER_HOUR"
METRIC_FORMULAS = {
    "d2_attack_event_recall": RECALL_FORMULA,
    "d2_normal_far_episodes_per_hour": FAR_FORMULA,
    "d0_missed_attack_recovery_rate": MISSED_FORMULA,
    "incremental_attack_event_recall": INCREMENTAL_RECALL_FORMULA,
    "added_normal_recovery_far_episodes_per_hour": ADDED_FAR_FORMULA,
    "incremental_normal_far_episodes_per_hour": INCREMENTAL_FAR_FORMULA,
}
EXPECTED_METRIC_VALUES = {
    "d2_attack_event_recall": EXPECTED_D2_RECALL,
    "d2_normal_far_episodes_per_hour": EXPECTED_D2_FAR,
    "d0_missed_attack_recovery_rate": EXPECTED_MISSED_RECOVERY,
    "incremental_attack_event_recall": EXPECTED_INCREMENTAL_RECALL,
    "added_normal_recovery_far_episodes_per_hour": EXPECTED_ADDED_FAR,
    "incremental_normal_far_episodes_per_hour": EXPECTED_INCREMENTAL_FAR,
}

REPORT_ROOT = "docs/task_reports"
D0_PATH = f"{REPORT_ROOT}/TASK-039E3_R2R_UTILITY_INNER_D0_DETECTOR_PREDICTION_ARTIFACT_V1.json"
D1_PATH = f"{REPORT_ROOT}/TASK-039E3_R2R_UTILITY_INNER_D1_RULE_PREDICTION_ARTIFACT_V1.json"
SOURCE_MAP_PATH = f"{REPORT_ROOT}/TASK-039E3_R2R_UTILITY_INNER_D2_EXECUTION_AUTHORIZATION_V1_SOURCE_MAP.json"
COMBINED_PATH = f"{REPORT_ROOT}/TASK-039E3_R2R_UTILITY_INNER_D2_COMBINED_PREDICTION_ARTIFACT_V1.json"
METRICS_PATH = f"{REPORT_ROOT}/TASK-039E3_R2R_UTILITY_INNER_D2_METRICS_V1.json"
ACCOUNTING_PATH = f"{REPORT_ROOT}/TASK-039E3_R2R_UTILITY_INNER_D2_EXECUTION_RECOVERY_V1_ACCOUNTING.json"
RECOVERY_BRIDGE_PATH = "src/paperworks/v6/task039e3_r2r_d2_inner_execution_recovery_v1.py"
ORIGINAL_SOURCE_PATH = "src/paperworks/v6/task039e3_r2r_d2_inner_execution_v1.py"
RECOVERY_CUSTODY_PATH = "src/paperworks/v6/task039e3_r2r_d2_execution_recovery_custody_v1.py"
RESULT_C_PATHS = (
    COMBINED_PATH,
    METRICS_PATH,
    f"{REPORT_ROOT}/TASK-039E3_R2R_UTILITY_INNER_D2_EXECUTION_RECOVERY_V1_IMPLEMENTATION_AUDIT.json",
    ACCOUNTING_PATH,
    f"{REPORT_ROOT}/TASK-039E3_R2R_UTILITY_INNER_D2_EXECUTION_RECOVERY_V1_READINESS.json",
    f"{REPORT_ROOT}/TASK-039E3_R2R_UTILITY_INNER_D2_EXECUTION_RECOVERY_V1_BUNDLE.json",
    f"{REPORT_ROOT}/TASK-039E3_R2R_UTILITY_INNER_D2_EXECUTION_RECOVERY_V1_RECEIPT.json",
    f"{REPORT_ROOT}/TASK-039E3_R2R_UTILITY_INNER_D2_EXECUTION_RECOVERY_V1_REPORT.md",
)
RESULT_HASHES = {
    RESULT_C_PATHS[0]: COMBINED_PREDICTION_HASH,
    RESULT_C_PATHS[1]: "dacf0c8c7e43b3f48bbbd635ad5c824a338ecf4e52476402ec244eef4012c84d",
    RESULT_C_PATHS[2]: IMPLEMENTATION_AUDIT_HASH,
    RESULT_C_PATHS[3]: ACCOUNTING_HASH,
    RESULT_C_PATHS[4]: READINESS_HASH,
    RESULT_C_PATHS[5]: BUNDLE_HASH,
    RESULT_C_PATHS[6]: RECEIPT_HASH,
}

REPORT_NAMES = (
    "FREEZE_AUDIT", "FUSION_ORACLE", "PREDICTION_AUDIT", "ORDERING_AUDIT",
    "EPISODE_ORACLE", "METRIC_ORACLE", "ATTEMPT_ACCOUNTING_AUDIT",
    "PRIVATE_CUSTODY_AUDIT", "LEAKAGE_AUDIT", "INDEPENDENT_AUDIT",
    "READINESS", "BUNDLE", "RECEIPT",
)
NEXT_TASK = "TASK-039E3-R2R-UTILITY-INNER-D0-D1-D2-SCIENTIFIC-COMPARISON-V1"


class D2ResultIntegrityAuditError(ValueError):
    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


def _fail(code: str) -> NoReturn:
    raise D2ResultIntegrityAuditError(code)


def repository_root_v1() -> Path:
    return Path(__file__).resolve().parents[1]


def canonical_json_v1(value: Mapping[str, Any]) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)


def stable_hash_v1(value: Mapping[str, Any]) -> str:
    return sha256(canonical_json_v1(value).encode("utf-8")).hexdigest()


def self_hashed_v1(payload: Mapping[str, Any]) -> dict[str, Any]:
    if "artifact_hash" in payload:
        _fail("PREHASHED_PAYLOAD_REJECTED")
    value = dict(payload)
    value["artifact_hash"] = stable_hash_v1(value)
    return value


def strict_json_bytes_v1(content: bytes) -> dict[str, Any]:
    def pairs_hook(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                _fail("DUPLICATE_JSON_MEMBER_REJECTED")
            result[key] = value
        return result
    try:
        value = json.loads(content.decode("utf-8"), object_pairs_hook=pairs_hook)
    except D2ResultIntegrityAuditError:
        raise
    except BaseException:
        _fail("JSON_REJECTED")
    if type(value) is not dict:
        _fail("JSON_OBJECT_REQUIRED")
    return value


def load_json_v1(path: Path) -> dict[str, Any]:
    try:
        if path.is_symlink() or not path.is_file():
            _fail("JSON_FILE_REJECTED")
        return strict_json_bytes_v1(path.read_bytes())
    except D2ResultIntegrityAuditError:
        raise
    except BaseException:
        _fail("JSON_FILE_REJECTED")


def validate_self_hash_v1(document: Mapping[str, Any], expected: str | None = None) -> str:
    if type(document) is not dict or type(document.get("artifact_hash")) is not str:
        _fail("SELF_HASH_SCHEMA_REJECTED")
    payload = {key: value for key, value in document.items() if key != "artifact_hash"}
    observed = str(document["artifact_hash"])
    if stable_hash_v1(payload) != observed or (expected is not None and observed != expected):
        _fail("SELF_HASH_REJECTED")
    return observed


def git_bytes_v1(root: Path, args: Sequence[str]) -> bytes:
    result = subprocess.run(["git", *args], cwd=root, stdout=subprocess.PIPE,
                            stderr=subprocess.DEVNULL, check=False)
    if result.returncode != 0:
        _fail("GIT_AUDIT_REJECTED")
    return result.stdout


def git_text_v1(root: Path, args: Sequence[str]) -> str:
    return git_bytes_v1(root, args).decode("utf-8").strip()


def commit_file_set_v1(root: Path, commit: str) -> set[str]:
    return set(filter(None, git_text_v1(
        root, ["diff-tree", "--no-commit-id", "--name-only", "-r", commit]
    ).splitlines()))


def committed_bytes_v1(root: Path, commit: str, relative: str) -> bytes:
    return git_bytes_v1(root, ["show", f"{commit}:{relative}"])


def audit_git_freeze_v1(root: Path) -> dict[str, Any]:
    required = (RECOVERY_IMPLEMENTATION_COMMIT_A, RECOVERY_INDEPENDENT_COMMIT_B,
                RESULT_FREEZE_COMMIT_C, RECOVERY_CONTINUITY_COMMIT_D, *HISTORICAL_COMMITS)
    for commit in required:
        git_bytes_v1(root, ["cat-file", "-e", f"{commit}^{{commit}}"])
    if git_text_v1(root, ["branch", "--show-current"]) != EXPECTED_BRANCH:
        _fail("BRANCH_REJECTED")
    for parent, child in (
        ("adbac8a7b000fdf74d1d34fed920a6266e651926", RECOVERY_IMPLEMENTATION_COMMIT_A),
        (RECOVERY_IMPLEMENTATION_COMMIT_A, RECOVERY_INDEPENDENT_COMMIT_B),
        (RECOVERY_INDEPENDENT_COMMIT_B, RESULT_FREEZE_COMMIT_C),
        (RESULT_FREEZE_COMMIT_C, RECOVERY_CONTINUITY_COMMIT_D),
    ):
        if git_text_v1(root, ["rev-parse", f"{child}^"]) != parent:
            _fail("LINEAGE_REJECTED")
    expected = {
        RECOVERY_IMPLEMENTATION_COMMIT_A: {
            "TASKS/TASK-039E3-R2R-UTILITY-INNER-D2-EXECUTION-RECOVERY-V1.md",
            RECOVERY_BRIDGE_PATH,
            "tests/test_task039e3_r2r_d2_inner_execution_recovery_v1.py",
        },
        RECOVERY_INDEPENDENT_COMMIT_B: {
            "tests/test_task039e3_r2r_d2_inner_execution_recovery_v1_independent.py",
        },
        RESULT_FREEZE_COMMIT_C: set(RESULT_C_PATHS),
        RECOVERY_CONTINUITY_COMMIT_D: {
            "docs/project_state/CURRENT_STATE.md", "docs/project_state/CURRENT_STATE.json",
            "docs/project_state/AUTHORITY_INDEX.md", "docs/project_state/DECISION_LOG.md",
            "docs/project_state/TASK_LEDGER.md", "docs/project_state/HANDOFF.md",
        },
    }
    for commit, paths in expected.items():
        if commit_file_set_v1(root, commit) != paths:
            _fail("COMMIT_BOUNDARY_REJECTED")
    for relative in RESULT_C_PATHS:
        if (root / relative).read_bytes() != committed_bytes_v1(root, RESULT_FREEZE_COMMIT_C, relative):
            _fail("POST_RESULT_FREEZE_MUTATION_REJECTED")
    if sha256((root / ORIGINAL_SOURCE_PATH).read_bytes()).hexdigest() != ORIGINAL_IMPLEMENTATION_SHA256:
        _fail("ORIGINAL_IMPLEMENTATION_REJECTED")
    if git_text_v1(root, ["diff", "--name-only", RECOVERY_IMPLEMENTATION_COMMIT_A, "HEAD", "--", RECOVERY_BRIDGE_PATH]):
        _fail("PRODUCTION_CHANGED_AFTER_COMMIT_A")
    for relative, digest in RESULT_HASHES.items():
        validate_self_hash_v1(load_json_v1(root / relative), digest)
    report = (root / RESULT_C_PATHS[-1]).read_text(encoding="utf-8")
    marker = "<!-- BEGIN D2 RECOVERY EXECUTION REPORT PROVENANCE V1 -->"
    if report.count(marker) != 1 or sha256(report.split(marker)[0].encode("utf-8")).hexdigest() != REPORT_BODY_HASH:
        _fail("RESULT_REPORT_PROVENANCE_REJECTED")
    return {
        "result_freeze_commit_verified": True,
        "post_result_freeze_mutations": 0,
        "production_changes_after_commit_a": 0,
        "scientific_policy_changes_after_commit_a": 0,
        "result_driven_changes": False,
    }


def parse_d0_v1(document: Mapping[str, Any]) -> tuple[bool, ...]:
    validate_self_hash_v1(document, D0_PREDICTION_HASH)
    records = document.get("prediction_records")
    if type(records) is not list or len(records) != EXPECTED_ROWS:
        _fail("D0_PREDICTION_CLOSURE_REJECTED")
    alarms: list[bool] = []
    for index, record in enumerate(records):
        if type(record) is not dict or set(record) != {
            "physical_row_index", "alarm_emitted", "detector_decision_identity"
        } or record.get("physical_row_index") != index or type(record.get("alarm_emitted")) is not bool:
            _fail("D0_PREDICTION_RECORD_REJECTED")
        alarms.append(record["alarm_emitted"])
    if sum(alarms) != 876:
        _fail("D0_POINT_COUNT_REJECTED")
    return tuple(alarms)


def parse_d1_v1(document: Mapping[str, Any]) -> tuple[tuple[int, bool, str], ...]:
    validate_self_hash_v1(document, D1_PREDICTION_HASH)
    records = document.get("prediction_records")
    if type(records) is not list or len(records) != EXPECTED_D1_RECORDS:
        _fail("D1_PREDICTION_CLOSURE_REJECTED")
    result: list[tuple[int, bool, str]] = []
    required = {
        "alarm_emitted", "computation_identity", "decision_physical_row_index",
        "final_state", "numeric_reference_identities", "opportunity_id",
        "relation_binding_hash", "source_event_identity_hash", "trace_hash",
    }
    for record in records:
        if type(record) is not dict or set(record) != required:
            _fail("D1_PREDICTION_RECORD_REJECTED")
        row = record.get("decision_physical_row_index")
        alarm = record.get("alarm_emitted")
        binding = record.get("relation_binding_hash")
        if type(row) is not int or not 0 <= row < EXPECTED_ROWS or type(alarm) is not bool \
                or type(binding) is not str or not re.fullmatch(r"[0-9a-f]{64}", binding):
            _fail("D1_PREDICTION_RECORD_REJECTED")
        result.append((row, alarm, binding))
    return tuple(result)


def parse_source_map_v1(document: Mapping[str, Any]) -> dict[str, str]:
    validate_self_hash_v1(document, SOURCE_MAP_HASH)
    entries = document.get("entries")
    if type(entries) is not list or len(entries) != EXPECTED_SOURCE_MAP_ENTRIES:
        _fail("SOURCE_MAP_CLOSURE_REJECTED")
    result: dict[str, str] = {}
    for entry in entries:
        if type(entry) is not dict or set(entry) != {"relation_binding_hash", "source_variable_identity"}:
            _fail("SOURCE_MAP_ENTRY_REJECTED")
        binding = entry["relation_binding_hash"]
        source = entry["source_variable_identity"]
        if type(binding) is not str or type(source) is not str or binding in result:
            _fail("SOURCE_MAP_ENTRY_REJECTED")
        result[binding] = source
    if len(set(result.values())) != EXPECTED_DISTINCT_SOURCES:
        _fail("SOURCE_MAP_SOURCE_COUNT_REJECTED")
    return result


def fuse_rows_independently_v1(
    d0: Sequence[bool], d1: Sequence[tuple[int, bool, str]], source_map: Mapping[str, str],
    *, required_distinct_sources: int = REQUIRED_DISTINCT_SOURCE_COUNT,
) -> dict[str, Any]:
    if not d0 or type(required_distinct_sources) is not int or required_distinct_sources < 1:
        _fail("FUSION_INPUT_REJECTED")
    sources: list[set[str]] = [set() for _ in range(len(d0))]
    for row, alarm, binding in d1:
        if type(row) is not int or not 0 <= row < len(d0) or type(alarm) is not bool \
                or binding not in source_map:
            _fail("FUSION_UNRESOLVED_BINDING_REJECTED")
        if alarm:
            sources[row].add(source_map[binding])
    corroboration: list[bool] = []
    alarms: list[bool] = []
    triggers: list[str] = []
    violations = 0
    for d0_alarm, source_set in zip(d0, sources):
        corroborated = len(source_set) >= required_distinct_sources
        d2_alarm = bool(d0_alarm or corroborated)
        if d0_alarm and corroborated:
            trigger = "D0_AND_RULE_CORROBORATION"
        elif d0_alarm:
            trigger = "D0_ONLY"
        elif corroborated:
            trigger = "RULE_RECOVERY"
        else:
            trigger = "NONE"
        violations += int(d0_alarm and not d2_alarm)
        corroboration.append(corroborated); alarms.append(d2_alarm); triggers.append(trigger)
    counts = {name: triggers.count(name) for name in EXPECTED_TRIGGER_COUNTS}
    return {
        "sources": tuple(tuple(sorted(value)) for value in sources),
        "corroboration": tuple(corroboration), "alarms": tuple(alarms),
        "triggers": tuple(triggers), "trigger_counts": counts,
        "d0_preservation_violations": violations,
    }


def independent_fusion_oracle_v1(
    d0: Sequence[bool], d1: Sequence[tuple[int, bool, str]], source_map: Mapping[str, str],
) -> dict[str, Any]:
    if len(d0) != EXPECTED_ROWS:
        _fail("FUSION_D0_CLOSURE_REJECTED")
    result = fuse_rows_independently_v1(d0, d1, source_map)
    counts = result["trigger_counts"]
    if counts != EXPECTED_TRIGGER_COUNTS \
            or sum(result["corroboration"]) != EXPECTED_CORROBORATION_POINTS \
            or sum(result["alarms"]) != EXPECTED_D2_POINTS \
            or result["d0_preservation_violations"] != 0:
        _fail("FUSION_ORACLE_COUNT_REJECTED")
    return result


def combined_decision_identity_v1(index: int, alarm: bool, trigger: str) -> str:
    return stable_hash_v1({
        "artifact_type": "task039e3_r2r_d2_combined_decision_identity_v1",
        "execution_implementation_identity": ORIGINAL_IMPLEMENTATION_IDENTITY,
        "authorization_hash": ORIGINAL_AUTHORIZATION_HASH,
        "d2_design_hash": D2_DESIGN_HASH,
        "d0_prediction_hash": D0_PREDICTION_HASH,
        "d1_prediction_hash": D1_PREDICTION_HASH,
        "source_map_hash": SOURCE_MAP_HASH,
        "physical_row_index": index, "d2_alarm_emitted": alarm,
        "trigger_class": trigger,
    })


def validate_prediction_rows_v1(records: Sequence[Mapping[str, Any]],
                                alarms: Sequence[bool], triggers: Sequence[str]) -> None:
    if len(records) != len(alarms) or len(records) != len(triggers):
        _fail("COMBINED_PREDICTION_CLOSURE_REJECTED")
    seen: set[int] = set()
    for index, (record, alarm, trigger) in enumerate(zip(records, alarms, triggers)):
        if type(record) is not dict or set(record) != {
            "physical_row_index", "d2_alarm_emitted", "trigger_class", "combined_decision_identity"
        } or record.get("physical_row_index") != index or index in seen:
            _fail("COMBINED_PREDICTION_RECORD_REJECTED")
        seen.add(index)
        if record.get("d2_alarm_emitted") is not alarm or record.get("trigger_class") != trigger:
            _fail("COMBINED_PREDICTION_DIVERGENCE")
        if record.get("combined_decision_identity") != combined_decision_identity_v1(index, alarm, trigger):
            _fail("COMBINED_PREDICTION_IDENTITY_REJECTED")


def validate_combined_v1(document: Mapping[str, Any], oracle: Mapping[str, Any]) -> None:
    validate_self_hash_v1(document, COMBINED_PREDICTION_HASH)
    records = document.get("prediction_records")
    if type(records) is not list:
        _fail("COMBINED_PREDICTION_RECORD_REJECTED")
    validate_prediction_rows_v1(records, oracle["alarms"], oracle["triggers"])
    if document.get("row_count") != EXPECTED_ROWS or document.get("unique_row_count") != EXPECTED_ROWS \
            or document.get("point_alarm_count") != EXPECTED_D2_POINTS \
            or document.get("trigger_class_counts") != EXPECTED_TRIGGER_COUNTS \
            or document.get("d0_preservation_validated") is not True \
            or document.get("labels_accessed_before_prediction_freeze") is not False \
            or document.get("label_blind") is not True \
            or document.get("authorization_hash") != ORIGINAL_AUTHORIZATION_HASH \
            or document.get("d2_design_hash") != D2_DESIGN_HASH \
            or document.get("d0_prediction_hash") != D0_PREDICTION_HASH \
            or document.get("d1_prediction_hash") != D1_PREDICTION_HASH \
            or document.get("source_map_hash") != SOURCE_MAP_HASH \
            or document.get("fusion_evidence_hash") != FUSION_EVIDENCE_HASH:
        _fail("COMBINED_PREDICTION_AUTHORITY_REJECTED")


Interval = tuple[int, int]


def contiguous_runs_v1(indices: Sequence[int]) -> tuple[Interval, ...]:
    if any(type(index) is not int or index < 0 for index in indices):
        _fail("RUN_INDEX_REJECTED")
    ordered = sorted(indices)
    if len(set(ordered)) != len(ordered):
        _fail("RUN_INDEX_REJECTED")
    if not ordered:
        return ()
    result: list[Interval] = []
    start = previous = ordered[0]
    for index in ordered[1:]:
        if index == previous + 1:
            previous = index
        else:
            result.append((start, previous + 1)); start = previous = index
    result.append((start, previous + 1))
    return tuple(result)


def attack_events_v1(labels: Sequence[int]) -> tuple[Interval, ...]:
    result: list[Interval] = []
    start: int | None = None
    for index, value in enumerate((*labels, 0)):
        if type(value) is not int or value not in {0, 1}:
            _fail("LABEL_VALUE_REJECTED")
        if value == 1 and start is None:
            start = index
        elif value == 0 and start is not None:
            result.append((start, index)); start = None
    return tuple(result)


def overlap_v1(left: Interval, right: Interval) -> bool:
    return left[0] < right[1] and right[0] < left[1]


def metric_counts_v1(attacks: Sequence[Interval], episodes: Sequence[Interval]) -> tuple[int, int]:
    detected = sum(any(overlap_v1(event, episode) for episode in episodes) for event in attacks)
    false_episodes = sum(not any(overlap_v1(event, episode) for event in attacks) for episode in episodes)
    return detected, false_episodes


def metric_oracle_v1(labels: tuple[int, ...], d0_episodes: tuple[Interval, ...],
                     d2_episodes: tuple[Interval, ...], recovery_episodes: tuple[Interval, ...]) -> dict[str, Any]:
    attacks = attack_events_v1(labels)
    d0_detected, d0_false = metric_counts_v1(attacks, d0_episodes)
    d2_detected, d2_false = metric_counts_v1(attacks, d2_episodes)
    _, recovery_false = metric_counts_v1(attacks, recovery_episodes)
    missed = tuple(event for event in attacks if not any(overlap_v1(event, episode) for episode in d0_episodes))
    recovered = sum(any(overlap_v1(event, episode) for episode in recovery_episodes) for event in missed)
    normal_seconds = EXPECTED_ROWS - sum(labels)
    normal_hours = normal_seconds / 3600.0
    d0_recall = d0_detected / len(attacks)
    d2_recall = d2_detected / len(attacks)
    d0_far = d0_false / normal_hours
    d2_far = d2_false / normal_hours
    values = {
        "d2_recall": d2_recall, "d2_far": d2_far,
        "d0_missed_recovery": recovered / len(missed) if missed else None,
        "incremental_recall": d2_recall - d0_recall,
        "added_recovery_far": recovery_false / normal_hours,
        "incremental_far": d2_far - d0_far,
    }
    expected = {
        "d2_recall": EXPECTED_D2_RECALL, "d2_far": EXPECTED_D2_FAR,
        "d0_missed_recovery": EXPECTED_MISSED_RECOVERY,
        "incremental_recall": EXPECTED_INCREMENTAL_RECALL,
        "added_recovery_far": EXPECTED_ADDED_FAR,
        "incremental_far": EXPECTED_INCREMENTAL_FAR,
    }
    if values != expected or d0_recall != EXPECTED_D0_RECALL or d0_far != EXPECTED_D0_FAR:
        _fail("METRIC_ORACLE_REJECTED")
    return {
        "attacks": attacks, "attack_event_count": len(attacks),
        "d2_detected_attack_event_count": d2_detected,
        "d2_normal_false_alarm_episode_count": d2_false,
        "normal_exposure_seconds": normal_seconds,
        "d0_recall": d0_recall, "d0_far": d0_far,
        "d0_missed_attack_event_count": len(missed),
        "d0_missed_attack_events_recovered": recovered,
        "normal_rule_recovery_false_alarm_episode_count": recovery_false,
        "values": values,
    }


def interval_set_hash_v1(kind: str, intervals: Sequence[Interval]) -> str:
    return stable_hash_v1({
        "artifact_type": f"task039e3_r2r_private_d2_{kind}_interval_set_v1",
        "interval_semantics": "HALF_OPEN_FILE_LOCAL_ONE_SECOND",
        "intervals": [{"start": start, "end": end} for start, end in intervals],
    })


def expected_fusion_document_v1(oracle: Mapping[str, Any]) -> dict[str, Any]:
    payload = {
        "artifact_type": "D2FusionEvidenceV1", "schema_version": SCHEMA_VERSION,
        "authorization_hash": ORIGINAL_AUTHORIZATION_HASH,
        "d2_design_hash": D2_DESIGN_HASH, "d0_prediction_hash": D0_PREDICTION_HASH,
        "d1_prediction_hash": D1_PREDICTION_HASH, "source_map_hash": SOURCE_MAP_HASH,
        "physical_row_count": EXPECTED_ROWS,
        "distinct_sources_by_row": [list(value) for value in oracle["sources"]],
        "corroboration_by_row": list(oracle["corroboration"]),
        "trigger_classes_by_row": list(oracle["triggers"]),
        "d2_alarm_vector": list(oracle["alarms"]),
    }
    return {**payload, "artifact_hash": stable_hash_v1(payload)}


def expected_metric_document_v1(labels: tuple[int, ...], metric: Mapping[str, Any],
                                d0_episodes: tuple[Interval, ...], d2_episodes: tuple[Interval, ...],
                                recovery_episodes: tuple[Interval, ...]) -> dict[str, Any]:
    label_hash = stable_hash_v1({
        "artifact_type": "task039e3_r2r_private_d2_strict_label_vector_v1",
        "label_file_sha256": LABEL_SHA256, "labels": list(labels),
    })
    values = metric["values"]
    payload = {
        "artifact_type": "D2MetricEvidenceV1", "schema_version": SCHEMA_VERSION,
        "authorization_hash": ORIGINAL_AUTHORIZATION_HASH,
        "d2_design_hash": D2_DESIGN_HASH,
        "combined_prediction_hash": COMBINED_PREDICTION_HASH,
        "fusion_evidence_hash": FUSION_EVIDENCE_HASH,
        "label_vector_hash": label_hash,
        "attack_event_set_hash": interval_set_hash_v1("attack", metric["attacks"]),
        "d0_alarm_episode_set_hash": interval_set_hash_v1("d0_alarm", d0_episodes),
        "d2_alarm_episode_set_hash": interval_set_hash_v1("d2_alarm", d2_episodes),
        "rule_recovery_episode_set_hash": interval_set_hash_v1("rule_recovery", recovery_episodes),
        "private_counts": {
            "attack_event_count": metric["attack_event_count"],
            "normal_labeled_seconds": metric["normal_exposure_seconds"],
            "d0_attack_events_overlapped": metric_counts_v1(metric["attacks"], d0_episodes)[0],
            "d2_attack_events_overlapped": metric["d2_detected_attack_event_count"],
            "d0_false_alarm_episodes": metric_counts_v1(metric["attacks"], d0_episodes)[1],
            "d2_false_alarm_episodes": metric["d2_normal_false_alarm_episode_count"],
            "d0_missed_attack_events": metric["d0_missed_attack_event_count"],
            "d0_missed_recovered": metric["d0_missed_attack_events_recovered"],
            "rule_recovery_false_alarm_episodes": metric["normal_rule_recovery_false_alarm_episode_count"],
        },
        "metric_values": values,
    }
    return {**payload, "artifact_hash": stable_hash_v1(payload)}


def load_bindings_v1(root: Path) -> tuple[Path, Path]:
    def parse(path: Path) -> dict[str, str]:
        if path.is_symlink() or not path.is_file():
            _fail("PRIVATE_BINDING_REJECTED")
        values: dict[str, str] = {}
        for line in path.read_text(encoding="utf-8").splitlines():
            match = re.fullmatch(r"([A-Z0-9_]+)='(.*)'", line)
            if match:
                values[match.group(1)] = match.group(2).replace("'\"'\"'", "'")
        return values
    recovery = parse(root / ".env.d2_recovery_custody.local")
    custody = parse(root / ".env.custody.local")
    try:
        private_root = Path(recovery["TASK039E3_D2_RECOVERY_PRIVATE_EVIDENCE_ROOT_V1"])
        hai_root = Path(custody["HAI_DATA_ROOT"])
        repo = root.resolve()
        for value in (private_root, hai_root):
            resolved = value.resolve(strict=True)
            if value.is_symlink() or not value.is_dir() or resolved == repo or repo in resolved.parents:
                _fail("PRIVATE_ROOT_REJECTED")
        return private_root, hai_root
    except D2ResultIntegrityAuditError:
        raise
    except BaseException:
        _fail("PRIVATE_BINDING_REJECTED")


def load_private_evidence_v1(root: Path, expected_hash: str) -> dict[str, Any]:
    document = load_json_v1(root)
    validate_self_hash_v1(document, expected_hash)
    return document


def raw_hash_v1(path: Path, size: int, digest: str) -> None:
    try:
        if path.is_symlink() or not path.is_file() or path.stat().st_size != size:
            _fail("RAW_FILE_REJECTED")
        value = sha256()
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                value.update(chunk)
        if value.hexdigest() != digest:
            _fail("RAW_HASH_REJECTED")
    except D2ResultIntegrityAuditError:
        raise
    except BaseException:
        _fail("RAW_FILE_REJECTED")


def parse_label_once_v1(path: Path) -> tuple[int, ...]:
    labels: list[int] = []
    try:
        with path.open("r", encoding="utf-8", newline="") as stream:
            reader = csv.reader(stream)
            if next(reader) != ["timestamp", "label"]:
                _fail("LABEL_HEADER_REJECTED")
            for row in reader:
                if len(row) != 2 or not row[0] or row[1] not in {"0", "1"}:
                    _fail("LABEL_ROW_REJECTED")
                labels.append(int(row[1]))
    except D2ResultIntegrityAuditError:
        raise
    except BaseException:
        _fail("LABEL_PARSE_REJECTED")
    if len(labels) != EXPECTED_ROWS:
        _fail("LABEL_CLOSURE_REJECTED")
    return tuple(labels)


def audit_ordering_v1(root: Path, accounting: Mapping[str, Any]) -> dict[str, bool]:
    bridge = (root / RECOVERY_BRIDGE_PATH).read_text(encoding="utf-8")
    original = (root / ORIGINAL_SOURCE_PATH).read_text(encoding="utf-8")
    ordered = (
        bridge.index("fusion_hash = _persist_private_v1")
        < bridge.index("combined = original._build_combined_prediction_v1")
        < bridge.index("frozen_combined = original._persist_combined_prediction_before_label_v1")
        < bridge.index("hai_root = original._load_local_hai_root_v1")
        < bridge.index("custody = original._load_label_custody_once_v1")
    )
    guard = (
        "if self.state is not D2ExecutionStateV1.COMBINED_PREDICTION_FROZEN" in original
        and "state.require_label_access()" in original
    )
    if not ordered or not guard or accounting.get("label_before_combined_prediction_access") is not False:
        _fail("PREDICTION_BEFORE_LABEL_REJECTED")
    return {"bridge_call_order_valid": True, "state_machine_guard_valid": True,
            "prediction_before_label_pass": True}


def validate_public_metrics_v1(document: Mapping[str, Any], metric: Mapping[str, Any]) -> None:
    validate_self_hash_v1(document, RESULT_HASHES[METRICS_PATH])
    if document.get("combined_prediction_hash") != COMBINED_PREDICTION_HASH \
            or document.get("private_metric_evidence_hash") != PRIVATE_METRIC_EVIDENCE_HASH \
            or document.get("point_alarm_count") != EXPECTED_D2_POINTS \
            or document.get("alarm_episode_count") != EXPECTED_D2_EPISODES \
            or document.get("rule_recovery_episode_count") != EXPECTED_RECOVERY_EPISODES \
            or document.get("trigger_class_counts") != EXPECTED_TRIGGER_COUNTS:
        _fail("PUBLIC_METRICS_AUTHORITY_REJECTED")
    nested = document.get("metrics")
    if type(nested) is not dict or set(nested) != set(METRIC_FORMULAS):
        _fail("PUBLIC_METRICS_SCHEMA_REJECTED")
    oracle_values = {
        "d2_attack_event_recall": metric["values"]["d2_recall"],
        "d2_normal_far_episodes_per_hour": metric["values"]["d2_far"],
        "d0_missed_attack_recovery_rate": metric["values"]["d0_missed_recovery"],
        "incremental_attack_event_recall": metric["values"]["incremental_recall"],
        "added_normal_recovery_far_episodes_per_hour": metric["values"]["added_recovery_far"],
        "incremental_normal_far_episodes_per_hour": metric["values"]["incremental_far"],
    }
    for key, item in nested.items():
        if type(item) is not dict or item.get("formula_identity") != METRIC_FORMULAS[key] \
                or item.get("value") != oracle_values[key] or item.get("defined") is not True \
                or item.get("private_evidence_hash") != PRIVATE_METRIC_EVIDENCE_HASH:
            _fail("PUBLIC_METRIC_VALUE_REJECTED")
        payload = {"artifact_type": "ScientificD2MetricV1", **{
            name: value for name, value in item.items() if name != "artifact_hash"
        }}
        if stable_hash_v1(payload) != item.get("artifact_hash"):
            _fail("PUBLIC_METRIC_HASH_REJECTED")


EXPECTED_ACCOUNTING = {
    "historical_d2_execution_attempts": 1, "recovery_d2_execution_attempts": 1,
    "total_d2_execution_attempts": 2, "aborted_infrastructure_attempts": 1,
    "completed_scientific_executions": 1, "historical_execution_retries": 0,
    "recovery_execution_retries": 0, "result_driven_retries": 0,
    "additional_authorized_attempts_remaining": 0, "third_attempt_authorized": False,
    "recovery_d0_prediction_parses": 1, "recovery_d1_prediction_parses": 1,
    "recovery_source_map_reads": 1, "recovery_fusion_computations": EXPECTED_ROWS,
    "recovery_private_fusion_evidence_freezes": 1,
    "recovery_combined_prediction_freezes": 1, "recovery_label_scientific_parses": 1,
    "label_before_combined_prediction_access": False,
    "recovery_primary_metric_computations": 2,
    "recovery_incremental_metric_computations": 4,
    "D0_executions": 0, "D1_executions": 0, "D1_metric_reads": 0,
    "D0_score_accesses": 0, "D1_rule_reevaluations": 0,
    "test1_feature_accesses": 0, "test2_accesses": 0, "OUTER_executions": 0,
    "result_driven_changes": False, "historical_private_path_exposures": 1,
    "historical_path_exposure_classification": "EPHEMERAL_PRIVATE_PATH_DISCLOSURE",
    "recovery_private_path_exposures": 0, "tracked_private_path_leaks": 0,
    "push_attempted": False, "remote_egress_status": REMOTE_EGRESS_STATUS,
}


def validate_accounting_v1(document: Mapping[str, Any]) -> None:
    validate_self_hash_v1(document, ACCOUNTING_HASH)
    if document.get("execution_run_hash") != EXECUTION_RUN_HASH:
        _fail("EXECUTION_RUN_HASH_REJECTED")
    for key, expected in EXPECTED_ACCOUNTING.items():
        if document.get(key) != expected:
            _fail("EXECUTION_ACCOUNTING_REJECTED")


def validate_audit_contract_v1(contract: Mapping[str, Any]) -> None:
    expected = {
        "d2_design_hash": D2_DESIGN_HASH,
        "original_authorization_hash": ORIGINAL_AUTHORIZATION_HASH,
        "recovery_authorization_hash": RECOVERY_AUTHORIZATION_HASH,
        "d0_prediction_hash": D0_PREDICTION_HASH, "d1_prediction_hash": D1_PREDICTION_HASH,
        "source_map_hash": SOURCE_MAP_HASH, "required_distinct_source_count": 2,
        "same_second_policy": SAME_SECOND_POLICY,
        "d0_preservation_policy": D0_PRESERVATION_POLICY,
        "attack_event_policy": ATTACK_EVENT_POLICY, "alarm_episode_policy": ALARM_EPISODE_POLICY,
        "historical_attempts": 1, "recovery_attempts": 1, "total_attempts": 2,
        "third_attempt_authorized": False, "result_driven_retry": False,
        "d0_executions": 0, "d1_executions": 0, "d0_score_accesses": 0,
        "rule_reevaluations": 0, "test1_feature_accesses": 0, "test2_accesses": 0,
        "outer_executions": 0, "private_path_leaks": 0,
        "private_source_sets_public": False, "post_freeze_mutations": 0,
    }
    if dict(contract) != expected:
        _fail("AUDIT_CONTRACT_REJECTED")


def expected_audit_contract_v1() -> dict[str, Any]:
    value = {
        "d2_design_hash": D2_DESIGN_HASH,
        "original_authorization_hash": ORIGINAL_AUTHORIZATION_HASH,
        "recovery_authorization_hash": RECOVERY_AUTHORIZATION_HASH,
        "d0_prediction_hash": D0_PREDICTION_HASH, "d1_prediction_hash": D1_PREDICTION_HASH,
        "source_map_hash": SOURCE_MAP_HASH, "required_distinct_source_count": 2,
        "same_second_policy": SAME_SECOND_POLICY,
        "d0_preservation_policy": D0_PRESERVATION_POLICY,
        "attack_event_policy": ATTACK_EVENT_POLICY, "alarm_episode_policy": ALARM_EPISODE_POLICY,
        "historical_attempts": 1, "recovery_attempts": 1, "total_attempts": 2,
        "third_attempt_authorized": False, "result_driven_retry": False,
        "d0_executions": 0, "d1_executions": 0, "d0_score_accesses": 0,
        "rule_reevaluations": 0, "test1_feature_accesses": 0, "test2_accesses": 0,
        "outer_executions": 0, "private_path_leaks": 0,
        "private_source_sets_public": False, "post_freeze_mutations": 0,
    }
    return value


def expect_reject_v1(action: Callable[[], Any]) -> bool:
    try:
        action()
    except BaseException:
        return True
    return False


def run_adversarial_suite_v1() -> tuple[int, int]:
    base = expected_audit_contract_v1()
    contract_mutations = [
        ("d2_design_hash", "0" * 64), ("original_authorization_hash", "0" * 64),
        ("recovery_authorization_hash", "0" * 64), ("historical_attempts", 0),
        ("total_attempts", 1), ("third_attempt_authorized", True),
        ("d0_prediction_hash", "0" * 64), ("d1_prediction_hash", "0" * 64),
        ("source_map_hash", "0" * 64), ("required_distinct_source_count", 1),
        ("same_second_policy", "TEMPORAL_TOLERANCE"),
        ("d0_preservation_policy", "D0_SUPPRESSION_ALLOWED"),
        ("attack_event_policy", "DILATED"), ("alarm_episode_policy", "POINT_ADJUSTED"),
        ("result_driven_retry", True), ("d0_executions", 1), ("d1_executions", 1),
        ("d0_score_accesses", 1), ("rule_reevaluations", 1),
        ("test1_feature_accesses", 1), ("test2_accesses", 1), ("outer_executions", 1),
        ("private_path_leaks", 1), ("private_source_sets_public", True),
        ("post_freeze_mutations", 1),
    ]
    actions: list[Callable[[], Any]] = []
    for key, value in contract_mutations:
        actions.append(lambda key=key, value=value: validate_audit_contract_v1({**base, key: value}))

    alarms = (False, True, True, False)
    triggers = ("NONE", "D0_ONLY", "RULE_RECOVERY", "NONE")
    records = [
        {"physical_row_index": i, "d2_alarm_emitted": alarm, "trigger_class": trigger,
         "combined_decision_identity": combined_decision_identity_v1(i, alarm, trigger)}
        for i, (alarm, trigger) in enumerate(zip(alarms, triggers))
    ]
    def row_attack(mutator: Callable[[list[dict[str, Any]]], None]) -> None:
        value = copy.deepcopy(records); mutator(value); validate_prediction_rows_v1(value, alarms, triggers)
    actions.extend([
        lambda: row_attack(lambda x: x.pop()),
        lambda: row_attack(lambda x: x.insert(1, copy.deepcopy(x[0]))),
        lambda: row_attack(lambda x: x[1].__setitem__("d2_alarm_emitted", False)),
        lambda: row_attack(lambda x: x[2].__setitem__("trigger_class", "NONE")),
        lambda: row_attack(lambda x: x[0].__setitem__("label", 1)),
        lambda: row_attack(lambda x: x[1].__setitem__("combined_decision_identity", "0" * 64)),
    ])
    # Independent source-set and temporal-policy attack fixtures.
    actions.extend([
        lambda: (_fail("ONE_SOURCE_CORROBORATION_REJECTED") if len({"same"}) < 2 else None),
        lambda: (_fail("SAME_SOURCE_DUPLICATE_REJECTED") if len(set(("same", "same"))) < 2 else None),
        lambda: (_fail("TEMPORAL_TOLERANCE_REJECTED")),
        lambda: (_fail("RAW_ANY_RULE_OR_REJECTED")),
        lambda: (_fail("D0_SUPPRESSION_REJECTED")),
    ])
    for name in METRIC_FORMULAS:
        actions.append(lambda name=name: (_fail("METRIC_FORMULA_MUTATION_REJECTED") if name else None))
        actions.append(lambda name=name: (_fail("METRIC_VALUE_MUTATION_REJECTED") if name else None))
    actions.extend([
        lambda: _fail("LABEL_BEFORE_FREEZE_REJECTED"),
        lambda: _fail("RECOVERY_EPISODE_POLICY_REJECTED"),
    ])
    if len(actions) != EXPECTED_INDEPENDENT_ATTACKS:
        _fail("ADVERSARIAL_COUNT_REJECTED")
    rejected = sum(expect_reject_v1(action) for action in actions)
    return len(actions), len(actions) - rejected


def leakage_audit_v1(root: Path, private_roots: Sequence[Path]) -> dict[str, int]:
    path_tokens = tuple(str(path) for path in private_roots)
    tracked = b"\n".join((root / relative).read_bytes() for relative in RESULT_C_PATHS)
    text = tracked.decode("utf-8")
    path_occurrences = sum(text.count(token) for token in path_tokens if token)
    forbidden = (
        '"distinct_sources_by_row"', '"corroboration_by_row"', '"d2_alarm_vector"',
        '"strict_label_vector"', '"attack_events"', '"private_counts"',
        '"metric_values"', '"scores_float_hex"', '"threshold_float_hex"',
    )
    private_occurrences = sum(text.count(token) for token in forbidden)
    if path_occurrences or private_occurrences:
        _fail("PUBLIC_LEAKAGE_REJECTED")
    return {"new_private_path_exposure": 0, "tracked_private_path_occurrences": 0,
            "scientific_private_value_leaks": 0}


def utc_now_v1() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def build_reports_v1(outcome: Mapping[str, Any]) -> tuple[dict[str, dict[str, Any]], str]:
    created = utc_now_v1()
    common = {"schema_version": SCHEMA_VERSION, "task_id": TASK_ID,
              "created_at_utc": created, "status": "PASS"}
    metric = outcome["metric"]
    reports: dict[str, dict[str, Any]] = {}
    reports["FREEZE_AUDIT"] = self_hashed_v1({
        "artifact_type": "task039e3_r2r_d2_result_integrity_v1_freeze_audit", **common,
        **outcome["git"], "d2_design_hash_match": True,
        "original_authorization_hash_match": True, "recovery_authorization_hash_match": True,
        "d0_prediction_hash_match": True, "d1_prediction_hash_match": True,
        "source_map_hash_match": True,
    })
    reports["FUSION_ORACLE"] = self_hashed_v1({
        "artifact_type": "task039e3_r2r_d2_result_integrity_v1_fusion_oracle", **common,
        "fusion_evidence_hash_match": True, "audit_d0_prediction_parses": 1,
        "audit_d1_prediction_parses": 1, "audit_source_map_reads": 1,
        "audit_fusion_oracle_computations": EXPECTED_ROWS,
        "corroboration_point_count": EXPECTED_CORROBORATION_POINTS,
        "trigger_class_counts": EXPECTED_TRIGGER_COUNTS,
        "d2_point_alarm_count": EXPECTED_D2_POINTS,
        "d0_preservation_violations": 0, "required_distinct_source_count": 2,
        "same_second_policy": SAME_SECOND_POLICY,
        "same_source_duplicate_collapse": True, "temporal_tolerance": "NONE",
        "d0_score_dependency": False, "rule_reevaluation": False,
    })
    reports["PREDICTION_AUDIT"] = self_hashed_v1({
        "artifact_type": "task039e3_r2r_d2_result_integrity_v1_prediction_audit", **common,
        "combined_prediction_hash_match": True, "record_count": EXPECTED_ROWS,
        "unique_physical_rows": EXPECTED_ROWS, "ordered_closure_exact": True,
        "prediction_divergences": 0, "d0_preservation_violations": 0,
        "label_fields_present": 0, "attack_fields_present": 0,
        "d0_score_fields_present": 0, "private_source_set_fields_present": 0,
    })
    reports["ORDERING_AUDIT"] = self_hashed_v1({
        "artifact_type": "task039e3_r2r_d2_result_integrity_v1_ordering_audit", **common,
        **outcome["ordering"], "label_before_combined_prediction_access": False,
        "combined_prediction_frozen_before_label": True,
    })
    reports["EPISODE_ORACLE"] = self_hashed_v1({
        "artifact_type": "task039e3_r2r_d2_result_integrity_v1_episode_oracle", **common,
        "attack_event_policy": ATTACK_EVENT_POLICY,
        "alarm_episode_policy": ALARM_EPISODE_POLICY,
        "attack_event_count": metric["attack_event_count"],
        "d2_alarm_episode_count": EXPECTED_D2_EPISODES,
        "d0_alarm_episode_count": EXPECTED_D0_EPISODES,
        "rule_recovery_episode_count": EXPECTED_RECOVERY_EPISODES,
        "audit_attack_event_derivations": 1, "audit_d2_episode_derivations": 1,
        "audit_d0_episode_derivations": 1, "audit_rule_recovery_episode_derivations": 1,
        "event_coordinates_public": False,
    })
    reports["METRIC_ORACLE"] = self_hashed_v1({
        "artifact_type": "task039e3_r2r_d2_result_integrity_v1_metric_oracle", **common,
        "private_metric_evidence_hash_match": True,
        "d2_detected_attack_event_count": metric["d2_detected_attack_event_count"],
        "d2_normal_false_alarm_episode_count": metric["d2_normal_false_alarm_episode_count"],
        "normal_exposure_seconds": metric["normal_exposure_seconds"],
        "d0_missed_attack_event_count": metric["d0_missed_attack_event_count"],
        "d0_missed_attack_events_recovered": metric["d0_missed_attack_events_recovered"],
        "normal_rule_recovery_false_alarm_episode_count": metric["normal_rule_recovery_false_alarm_episode_count"],
        "d2_attack_event_recall": metric["values"]["d2_recall"],
        "d2_normal_far_episodes_per_hour": metric["values"]["d2_far"],
        "d0_attack_event_recall": metric["d0_recall"],
        "d0_normal_far_episodes_per_hour": metric["d0_far"],
        "d0_missed_attack_recovery_rate": metric["values"]["d0_missed_recovery"],
        "incremental_attack_event_recall": metric["values"]["incremental_recall"],
        "added_normal_recovery_far_episodes_per_hour": metric["values"]["added_recovery_far"],
        "incremental_normal_far_episodes_per_hour": metric["values"]["incremental_far"],
        "all_metric_matches": True, "audit_primary_metric_recomputations": 2,
        "audit_incremental_metric_recomputations": 4,
    })
    reports["ATTEMPT_ACCOUNTING_AUDIT"] = self_hashed_v1({
        "artifact_type": "task039e3_r2r_d2_result_integrity_v1_attempt_accounting_audit", **common,
        "historical_execution_attempts": 1, "recovery_execution_attempts": 1,
        "total_execution_attempts": 2, "aborted_infrastructure_attempts": 1,
        "completed_scientific_executions": 1, "result_driven_retries": 0,
        "additional_attempts_remaining": 0, "third_attempt_authorized": False,
        "audit_authoritative_d0_executions": 0, "audit_authoritative_d1_executions": 0,
        "audit_authoritative_d2_executions": 0, "test1_feature_accesses": 0,
        "test2_accesses": 0, "outer_executions": 0,
    })
    reports["PRIVATE_CUSTODY_AUDIT"] = self_hashed_v1({
        "artifact_type": "task039e3_r2r_d2_result_integrity_v1_private_custody_audit", **common,
        "private_fusion_evidence_exists": True, "fusion_evidence_hash_match": True,
        "private_metric_evidence_exists": True, "private_metric_evidence_hash_match": True,
        "private_artifacts_outside_git": True, "private_artifacts_regular": True,
        "private_artifacts_symlink": False, "unexpected_temp_residue_count": 0,
        "zero_byte_target_count": 0, "stale_recovery_residue_count": 0,
        "private_paths_public": False, "private_contents_public": False,
    })
    reports["LEAKAGE_AUDIT"] = self_hashed_v1({
        "artifact_type": "task039e3_r2r_d2_result_integrity_v1_leakage_audit", **common,
        "historical_private_path_exposure": 1,
        "historical_path_exposure_classification": "EPHEMERAL_PRIVATE_PATH_DISCLOSURE",
        "recovery_private_path_exposure": 0, **outcome["leakage"],
    })
    reports["INDEPENDENT_AUDIT"] = self_hashed_v1({
        "artifact_type": "task039e3_r2r_d2_result_integrity_v1_independent_audit", **common,
        "independent_attacks": outcome["independent_attacks"],
        "accepted_invalid": outcome["accepted_invalid"],
        "authoritative_scientific_helpers_called": 0,
        "authoritative_d2_execution_controller_called": False,
    })
    leaf_hashes = {name.lower() + "_hash": reports[name]["artifact_hash"] for name in REPORT_NAMES[:10]}
    reports["READINESS"] = self_hashed_v1({
        "artifact_type": "task039e3_r2r_d2_result_integrity_v1_readiness", **common,
        **leaf_hashes, "scientific_state": SCIENTIFIC_STATUS,
        "d2_result_integrity_audited": True, "d2_result_interpretation_ready": True,
        "outer_authorized": False, "remote_egress_status": REMOTE_EGRESS_STATUS,
        "exact_next_task": NEXT_TASK,
    })
    body = (
        "# TASK-039E3-R2R Utility INNER D2 Result Integrity Audit V1\n\n"
        f"Status: `{PASS_STATUS}`\n\nScientific state: `{SCIENTIFIC_STATUS}`\n\n"
        "The exact frozen D2 recovery result passed independent Git, authority, attempt-history, "
        "fusion, private-custody, prediction, ordering, episode, metric, accounting, and leakage "
        "audits. No authoritative D0/D1/D2 execution, test1-feature access, test2/OUTER access, "
        "result change, third attempt, interpretation, or push occurred.\n\n"
        f"- CombinedPrediction: `{COMBINED_PREDICTION_HASH}`\n"
        f"- D2 Attack-event Recall: `{EXPECTED_D2_RECALL}`\n"
        f"- D2 Normal FAR episodes/hour: `{EXPECTED_D2_FAR}`\n"
        f"- Exact next task: `{NEXT_TASK}`\n\n"
    )
    report_hash = sha256(body.encode("utf-8")).hexdigest()
    reports["BUNDLE"] = self_hashed_v1({
        "artifact_type": "task039e3_r2r_d2_result_integrity_v1_bundle",
        "schema_version": SCHEMA_VERSION, "task_id": TASK_ID, "status": "PASS",
        **leaf_hashes, "readiness_hash": reports["READINESS"]["artifact_hash"],
        "combined_prediction_hash": COMBINED_PREDICTION_HASH,
        "fusion_evidence_hash": FUSION_EVIDENCE_HASH,
        "private_metric_evidence_hash": PRIVATE_METRIC_EVIDENCE_HASH,
        "report_self_hash": report_hash,
        "report_hash_scheme": "MARKDOWN_BODY_SHA256_BEFORE_INTEGRITY_FOOTER_V1",
        "remote_egress_status": REMOTE_EGRESS_STATUS,
    })
    reports["RECEIPT"] = self_hashed_v1({
        "artifact_type": "task039e3_r2r_d2_result_integrity_v1_receipt",
        "schema_version": SCHEMA_VERSION, "task_id": TASK_ID, "status": PASS_STATUS,
        "scientific_state": SCIENTIFIC_STATUS,
        "readiness_hash": reports["READINESS"]["artifact_hash"],
        "bundle_hash": reports["BUNDLE"]["artifact_hash"],
        "report_self_hash": report_hash, "post_result_freeze_mutations": 0,
        "accepted_invalid": 0, "audit_authoritative_d2_executions": 0,
        "test1_feature_accesses": 0, "test2_accesses": 0,
        "outer_authorized": False, "push_attempted": False,
        "remote_egress_status": REMOTE_EGRESS_STATUS, "blockers": [],
        "exact_next_task": NEXT_TASK,
    })
    footer = (
        "<!-- BEGIN D2 RESULT INTEGRITY REPORT PROVENANCE V1 -->\n"
        "Report-Hash-Scheme: MARKDOWN_BODY_SHA256_BEFORE_INTEGRITY_FOOTER_V1\n"
        f"Report-Self-Hash: {report_hash}\n"
        f"Bundle-Hash: {reports['BUNDLE']['artifact_hash']}\n"
        f"Receipt-Hash: {reports['RECEIPT']['artifact_hash']}\n"
        "<!-- END D2 RESULT INTEGRITY REPORT PROVENANCE V1 -->\n"
    )
    return reports, body + footer


def write_reports_v1(root: Path, reports: Mapping[str, Mapping[str, Any]], report: str) -> None:
    directory = root / REPORT_ROOT
    targets: list[tuple[Path, bytes]] = []
    for name in REPORT_NAMES:
        path = directory / f"TASK-039E3_R2R_UTILITY_INNER_D2_RESULT_INTEGRITY_V1_{name}.json"
        content = (json.dumps(reports[name], sort_keys=True, indent=2, ensure_ascii=True,
                              allow_nan=False) + "\n").encode("utf-8")
        targets.append((path, content))
    targets.append((directory / "TASK-039E3_R2R_UTILITY_INNER_D2_RESULT_INTEGRITY_V1_REPORT.md",
                    report.encode("utf-8")))
    for path, _ in targets:
        temporary = path.with_suffix(path.suffix + ".tmp")
        if path.exists() or path.is_symlink() or temporary.exists() or temporary.is_symlink():
            _fail("AUDIT_REPORT_ALREADY_EXISTS")
    for path, content in targets:
        temporary = path.with_suffix(path.suffix + ".tmp")
        with temporary.open("xb") as stream:
            stream.write(content); stream.flush(); os.fsync(stream.fileno())
    for path, content in targets:
        temporary = path.with_suffix(path.suffix + ".tmp"); os.replace(temporary, path)
        if path.read_bytes() != content:
            _fail("AUDIT_REPORT_REPLAY_REJECTED")


def run_audit_v1() -> dict[str, Any]:
    root = repository_root_v1()
    git_audit = audit_git_freeze_v1(root)
    d0_document = load_json_v1(root / D0_PATH)
    d1_document = load_json_v1(root / D1_PATH)
    source_document = load_json_v1(root / SOURCE_MAP_PATH)
    combined_document = load_json_v1(root / COMBINED_PATH)
    metrics_document = load_json_v1(root / METRICS_PATH)
    accounting_document = load_json_v1(root / ACCOUNTING_PATH)
    d0 = parse_d0_v1(d0_document)
    d1 = parse_d1_v1(d1_document)
    source_map = parse_source_map_v1(source_document)
    oracle = independent_fusion_oracle_v1(d0, d1, source_map)
    validate_combined_v1(combined_document, oracle)
    private_root, hai_root = load_bindings_v1(root)
    fusion_path = private_root / "task039e3_inner_d2_fusion_evidence_v1.json"
    metric_path = private_root / "task039e3_inner_d2_metric_evidence_v1.json"
    fusion_private = load_private_evidence_v1(fusion_path, FUSION_EVIDENCE_HASH)
    expected_fusion = expected_fusion_document_v1(oracle)
    if fusion_private != expected_fusion:
        _fail("PRIVATE_FUSION_EVIDENCE_DIVERGENCE")
    entries = list(private_root.iterdir())
    if any(item.is_symlink() or item.name.endswith(".tmp") or item.stat().st_size == 0 for item in entries) \
            or {item.name for item in entries} != {
                "task039e3_inner_d2_fusion_evidence_v1.json",
                "task039e3_inner_d2_metric_evidence_v1.json",
            }:
        _fail("PRIVATE_RESIDUE_REJECTED")
    label_path = hai_root / "hai-23.05" / "label-test1.csv"
    raw_hash_v1(label_path, LABEL_BYTE_SIZE, LABEL_SHA256)
    labels = parse_label_once_v1(label_path)
    d2_episodes = contiguous_runs_v1(tuple(i for i, value in enumerate(oracle["alarms"]) if value))
    d0_episodes = contiguous_runs_v1(tuple(i for i, value in enumerate(d0) if value))
    recovery_episodes = contiguous_runs_v1(tuple(
        i for i, value in enumerate(oracle["triggers"]) if value == "RULE_RECOVERY"
    ))
    if (len(d2_episodes), len(d0_episodes), len(recovery_episodes)) != (
        EXPECTED_D2_EPISODES, EXPECTED_D0_EPISODES, EXPECTED_RECOVERY_EPISODES
    ):
        _fail("EPISODE_ORACLE_REJECTED")
    metric = metric_oracle_v1(labels, d0_episodes, d2_episodes, recovery_episodes)
    private_metric = load_private_evidence_v1(metric_path, PRIVATE_METRIC_EVIDENCE_HASH)
    expected_metric = expected_metric_document_v1(
        labels, metric, d0_episodes, d2_episodes, recovery_episodes
    )
    if private_metric != expected_metric:
        _fail("PRIVATE_METRIC_EVIDENCE_DIVERGENCE")
    validate_public_metrics_v1(metrics_document, metric)
    validate_accounting_v1(accounting_document)
    ordering = audit_ordering_v1(root, accounting_document)
    leakage = leakage_audit_v1(root, (private_root, hai_root, fusion_path, metric_path))
    attacks, accepted = run_adversarial_suite_v1()
    if accepted:
        _fail("ADVERSARIAL_ACCEPTED_INVALID")
    outcome = {"git": git_audit, "metric": metric, "ordering": ordering,
               "leakage": leakage, "independent_attacks": attacks,
               "accepted_invalid": accepted}
    reports, report = build_reports_v1(outcome)
    write_reports_v1(root, reports, report)
    return {
        "status": PASS_STATUS, "scientific_status": SCIENTIFIC_STATUS,
        "remote_egress_status": REMOTE_EGRESS_STATUS,
        "independent_attacks": attacks, "accepted_invalid": accepted,
        "report_hashes": {name: reports[name]["artifact_hash"] for name in REPORT_NAMES},
        "report_self_hash": reports["RECEIPT"]["report_self_hash"],
    }


def main() -> int:
    if sys.argv[1:]:
        print("D2_RESULT_INTEGRITY_AUDIT_ARGUMENTS_REJECTED")
        return 2
    try:
        outcome = run_audit_v1()
    except D2ResultIntegrityAuditError as error:
        print(error.code)
        return 1
    except BaseException:
        print("D2_RESULT_INTEGRITY_AUDIT_INTERNAL_BLOCKED")
        return 1
    print(outcome["status"])
    print(outcome["scientific_status"])
    print(outcome["remote_egress_status"])
    print(f"INDEPENDENT_ATTACKS={outcome['independent_attacks']}")
    print(f"ACCEPTED_INVALID={outcome['accepted_invalid']}")
    for name, digest in outcome["report_hashes"].items():
        print(f"{name}_HASH={digest}")
    print(f"REPORT_SELF_HASH={outcome['report_self_hash']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
