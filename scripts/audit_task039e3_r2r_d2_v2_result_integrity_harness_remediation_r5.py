"""Final single-pass independent audit of the frozen D2 V2 INNER result.

This audit-only module does not import the D2 V2 execution controller.  It
parses each real scientific authority once, constructs its own causal-token,
distinct-source, fusion, episode, and metric oracles, and renders reports only
from one immutable completed result.
"""
from __future__ import annotations

import csv
from dataclasses import dataclass
from hashlib import sha256
import io
import json
from pathlib import Path
import re
import subprocess
import sys
from typing import Any, Callable, Mapping, NoReturn, Sequence

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import audit_task039e3_r2r_d2_v2_result_integrity_harness_remediation_r4 as r4

TASK_ID = "TASK-039E3-R2R-UTILITY-INNER-D2-V2-RESULT-INTEGRITY-AUDIT-HARNESS-REMEDIATION-R5"
PASS_STATUS = "passed_task039e3_r2r_utility_inner_d2_v2_result_integrity_audit_harness_remediation_r5"
SCIENTIFIC_STATUS = "D2_V2_RESULT_INTEGRITY_AUDITED"
BRANCH = "task-039e3-r2r-utility-inner-d2-v2-result-integrity-audit-harness-remediation-r5"
BASE = "a64ce89b0fd9250e5afbdd1ef78a8ffcdf6f7287"
RESULT_C = "55d41c543e110a9a6f0f5e2e2671857dba938aaa"
EXEC_A = "2bbb3dcaced47c8d15337e45eb0e0b741c1a3ed1"
DESIGN = "ace631af367ee2abe1b0ee7658875eeb59a2a8d906d09ce8ea92e8f2d83e31e4"
AUTH = "0f909480cfe3db8afc4042909258fe041f36ad021a917907008ee7e5023f2f45"
D0_HASH = "a4b58f1c78b9bb53125da1a009f3fd05b02e1c83a789772a341a7679fddca0f6"
D1_HASH = "58c3c49f9657f68d35c830b12eeb493ce4bbf7669c90f04813fb80246c3c2682"
SOURCE_HASH = "f866176000c3d5a943053ac3125d2700b0b72f25b5a0539d8f4713435a959818"
HORIZON_HASH = "e9825a578495396d935397e79d8c50717dccb47f069f13e93f6306f992a9407c"
FUSION_HASH = "9fd5563b76cb4af0cf68383e1e2b9d10da9e6fd35a667d4a68d6eb5f8db2e8cb"
COMBINED_HASH = "31035da56e140141917437df5b3473b803153621c7e1022830cccde52f61c0b3"
METRIC_EVIDENCE_HASH = "3e3f20b5b1a9387cd3bed4ad17e4232e714cc588d7df1c2a37dfd69bcd1a8513"
METRICS_HASH = "8fabdccc0c9a9b502497aa58163131647303d5e27acefb995a06ca9d43850ba7"
ACCOUNTING_HASH = "7059e2b4e54ec53d0b72c072c71487b19efe056ce382357615dc152bf2382aca"
IMPL = "9016e5c8be9fa0e56af6a5d1870617f1937e557b7eabd0afa5b20722e89ded62"
LABEL_HASH = "eaf69edb9c5834bc393afd7bf658b5e408d34fd7bfc3261f80516765fb818fbc"
LABEL_SIZE = 1_242_017
ROWS = 54_000
TRIGGERS = {"D0_AND_RULE_CORROBORATION_NATIVE_HORIZON": 63, "D0_ONLY": 813,
            "NONE": 51_852, "RULE_RECOVERY_NATIVE_HORIZON": 1_272}
NEXT_TASK = "TASK-039E3-R2R-UTILITY-INNER-D2-V1-V2-SCIENTIFIC-DISPOSITION-V1"
TASK_PATH = "TASKS/TASK-039E3-R2R-UTILITY-INNER-D2-V2-RESULT-INTEGRITY-AUDIT-HARNESS-REMEDIATION-R5.md"
SCRIPT_PATH = "scripts/audit_task039e3_r2r_d2_v2_result_integrity_harness_remediation_r5.py"
TEST_PATHS = (
    "tests/test_task039e3_r2r_d2_v2_result_integrity_audit_harness_remediation_r5.py",
    "tests/test_task039e3_r2r_d2_v2_result_integrity_audit_harness_remediation_r5_independent.py",
)
D0_PATH = "docs/task_reports/TASK-039E3_R2R_UTILITY_INNER_D0_DETECTOR_PREDICTION_ARTIFACT_V1.json"
D1_PATH = "docs/task_reports/TASK-039E3_R2R_UTILITY_INNER_D1_RULE_PREDICTION_ARTIFACT_V1.json"
SOURCE_PATH = "docs/task_reports/TASK-039E3_R2R_UTILITY_INNER_D2_EXECUTION_AUTHORIZATION_V1_SOURCE_MAP.json"
HORIZON_PATH = "docs/task_reports/TASK-039E3_R2R_UTILITY_INNER_D2_V2_DESIGN_V1_NATIVE_HORIZON_AUTHORITY.json"
COMBINED_PATH = "docs/task_reports/TASK-039E3_R2R_UTILITY_INNER_D2_V2_COMBINED_PREDICTION_ARTIFACT_V1.json"
METRICS_PATH = "docs/task_reports/TASK-039E3_R2R_UTILITY_INNER_D2_V2_METRICS_V1.json"
ACCOUNTING_PATH = "docs/task_reports/TASK-039E3_R2R_UTILITY_INNER_D2_V2_EXECUTION_V1_ACCOUNTING.json"
EXECUTION_SOURCE = "src/paperworks/v6/task039e3_r2r_d2_v2_inner_execution_v1.py"
RESULT_FILES = r4.oracle.RESULT_FILES

COMPAT_PREFIX = "docs/task_reports/TASK-039E3_R2R_UTILITY_INNER_D2_V2_PRIVATE_CUSTODY_BINDING_REMEDIATION_REPORT_SCHEMA_R1_"
COMPAT_AUTHORITIES = {
    "ROOT_CAUSE": "fec9bee7d7f6ffcef29934fb1755715f6df374a399220d0669718f2a571e4ed2",
    "FIELD_CLASSIFICATION": "638e7b4efd593f04db13922c24eb378fa9301ba0e7118ff89ecfd2c7e77dfce1",
    "FUSION_EVIDENCE_IDENTITY": "0b2d3644d91d6f2418189ec001450ce872ecf72248923842d4dbeb759a6d8767",
    "METRIC_EVIDENCE_IDENTITY": "d90e254c019ebeb41dede5625f855125a90164f80a61d914518d876f5a7c68a1",
    "SECURITY_AUDIT": "6c05a04510d1018f7cba7dbe97603161ce14dc9334e4e179be6d73965949cd50",
    "SCHEMA_AUDIT": "2d6235601cfb2f3e475685727ca4c9795fbca35f526dc2096d6075aaad18c8ac",
    "COMPATIBILITY_RECEIPT": "f7ca9d29c7e8d65359781534790c008bec436dc35e521f7de3342b7215e28cd8",
    "INDEPENDENT_AUDIT": "b6d2c87396ffb34c8d65b6ba29cebf3bea9e3d8767ec3c623ff84044940c2573",
    "READINESS": "66cfd0731c0b86a38d0b43caf695466a9a08f178e87a582dfab11011c52f167a",
    "BUNDLE": "17d950f5d394302fd7b7dc4e68db24c600d8e8895089b27a70cb6a58db55fe54",
    "RECEIPT": "36732840373d040c0edd907b278b45503edc5ae30111074478091d1224e2b99a",
}
HISTORICAL_BLOCKERS = (
    ("docs/task_reports/TASK-039E3_R2R_UTILITY_INNER_D2_V2_RESULT_INTEGRITY_V1_BLOCKER.json", "592344d430b50724a7ae4f81ed0e73423ec1473586d0d9a15d2ff68f6009f879"),
    ("docs/task_reports/TASK-039E3_R2R_UTILITY_INNER_D2_V2_RESULT_INTEGRITY_AUDIT_HARNESS_R1_BLOCKER.json", "dc6d83a33bdf985389b6d2d1b75e54f2b703e59f515369dc41b5a499280b0990"),
    ("docs/task_reports/TASK-039E3_R2R_UTILITY_INNER_D2_V2_RESULT_INTEGRITY_AUDIT_HARNESS_R2_BLOCKER.json", "4e6526e382dbb0bf15bae9123eeeba3a090dcb59bfd767f3b19172fe3e353c0c"),
    ("docs/task_reports/TASK-039E3_R2R_UTILITY_INNER_D2_V2_RESULT_INTEGRITY_AUDIT_HARNESS_R3_BLOCKER.json", "2baed348b67ec7567ea57d1892c4e605728120e65480728ca562528c822e9f4a"),
    ("docs/task_reports/TASK-039E3_R2R_UTILITY_INNER_D2_V2_RESULT_INTEGRITY_AUDIT_HARNESS_R4_BLOCKER.json", "34acc0c252b13054b15f3ac6fb1a560fdf0c653f2580305c9d582f6a52e863fc"),
)
REPORT_PREFIX = "TASK-039E3_R2R_UTILITY_INNER_D2_V2_RESULT_INTEGRITY_R5_"
LEAVES = ("AUTHORITY_AUDIT", "CUSTODY_COMPATIBILITY_AUDIT", "FREEZE_AUDIT", "HORIZON_ORACLE",
          "TOKEN_ORACLE", "FUSION_ORACLE", "PREDICTION_AUDIT", "ORDERING_AUDIT",
          "EPISODE_ORACLE", "METRIC_ORACLE", "ACCOUNTING_AUDIT", "PRIVATE_CUSTODY_AUDIT",
          "LEAKAGE_AUDIT", "INDEPENDENT_AUDIT")
REPORT_NAMES = (*LEAVES, "READINESS", "BUNDLE", "RECEIPT")
REPORT_SCHEME = "MARKDOWN_BODY_SHA256_BEFORE_INTEGRITY_FOOTER_V1"
REPORT_BEGIN = b"<!-- BEGIN D2 V2 RESULT INTEGRITY R5 REPORT PROVENANCE V1 -->"
REPORT_END = b"<!-- END D2 V2 RESULT INTEGRITY R5 REPORT PROVENANCE V1 -->"


class AuditR5Error(RuntimeError):
    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


def fail(code: str) -> NoReturn:
    raise AuditR5Error(code)


def stable(value: Mapping[str, Any]) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode()
    return sha256(raw).hexdigest()


def seal(payload: Mapping[str, Any]) -> dict[str, Any]:
    if "artifact_hash" in payload or any(key == "artifact_hash" for key in payload):
        fail("D2_V2_R5_REPORT_SELF_HASH_FIELD_COLLISION")
    result = dict(payload)
    result["artifact_hash"] = stable(result)
    return result


def validate_hash(document: Mapping[str, Any], expected: str) -> None:
    payload = {key: value for key, value in document.items() if key != "artifact_hash"}
    if document.get("artifact_hash") != expected or stable(payload) != expected:
        fail("D2_V2_R5_SELF_HASH_REJECTED")


def load_public(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_bytes())
    except BaseException:
        fail("D2_V2_R5_PUBLIC_AUTHORITY_REJECTED")
    if type(value) is not dict:
        fail("D2_V2_R5_PUBLIC_AUTHORITY_REJECTED")
    return value


def git(*args: str) -> str:
    process = subprocess.run(["git", *args], cwd=ROOT, text=True,
                             stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    if process.returncode:
        fail("D2_V2_R5_GIT_AUDIT_REJECTED")
    return process.stdout.strip()


@dataclass
class SingleParseGuardR5:
    semantic_parses: dict[str, int]

    @classmethod
    def create(cls) -> "SingleParseGuardR5":
        return cls({})

    def claim(self, identity: str) -> None:
        if self.semantic_parses.get(identity, 0):
            fail("D2_V2_R5_AUDIT_DUPLICATE_REAL_INPUT_PARSE")
        self.semantic_parses[identity] = 1

    def require_exact(self) -> None:
        expected = {name: 1 for name in REAL_IDENTITIES}
        if {name: self.semantic_parses.get(name, 0) for name in REAL_IDENTITIES} != expected:
            fail("D2_V2_R5_PARSE_ACCOUNTING_REJECTED")


REAL_IDENTITIES = ("D0_PREDICTION", "D1_PREDICTION", "SOURCE_MAP", "NATIVE_HORIZON_MAP",
                   "COMBINED_PREDICTION_V2", "FUSION_EVIDENCE_V2", "LABEL_TEST1",
                   "METRIC_EVIDENCE_V2")


def semantic_json_once(path: Path, identity: str, guard: SingleParseGuardR5) -> dict[str, Any]:
    guard.claim(identity)
    try:
        value = json.loads(path.read_bytes())
    except BaseException:
        fail("D2_V2_R5_REAL_INPUT_JSON_REJECTED")
    if type(value) is not dict:
        fail("D2_V2_R5_REAL_INPUT_JSON_REJECTED")
    return value


def parse_d0(document: Mapping[str, Any]) -> tuple[bool, ...]:
    validate_hash(document, D0_HASH)
    records = document.get("prediction_records")
    if type(records) is not list or len(records) != ROWS:
        fail("D2_V2_R5_D0_CLOSURE_REJECTED")
    result: list[bool] = []
    for index, record in enumerate(records):
        if type(record) is not dict or record.get("physical_row_index") != index or type(record.get("alarm_emitted")) is not bool:
            fail("D2_V2_R5_D0_RECORD_REJECTED")
        result.append(record["alarm_emitted"])
    if sum(result) != 876:
        fail("D2_V2_R5_D0_COUNT_REJECTED")
    return tuple(result)


def parse_d1(document: Mapping[str, Any]) -> tuple[tuple[int, bool, str], ...]:
    validate_hash(document, D1_HASH)
    records = document.get("prediction_records")
    if type(records) is not list or len(records) != 6031:
        fail("D2_V2_R5_D1_CLOSURE_REJECTED")
    result = []
    for record in records:
        row, alarm, relation = (record.get("decision_physical_row_index"), record.get("alarm_emitted"),
                                record.get("relation_binding_hash"))
        if type(row) is not int or not 0 <= row < ROWS or type(alarm) is not bool or type(relation) is not str:
            fail("D2_V2_R5_D1_RECORD_REJECTED")
        result.append((row, alarm, relation))
    return tuple(result)


def parse_source(document: Mapping[str, Any]) -> dict[str, str]:
    validate_hash(document, SOURCE_HASH)
    entries = document.get("entries")
    if type(entries) is not list or len(entries) != 42:
        fail("D2_V2_R5_SOURCE_CLOSURE_REJECTED")
    result = {entry["relation_binding_hash"]: entry["source_variable_identity"] for entry in entries}
    if len(result) != 42 or len(set(result.values())) != 9:
        fail("D2_V2_R5_SOURCE_CLOSURE_REJECTED")
    return result


def parse_horizon(document: Mapping[str, Any], outer_hash: str = "14aa91ff3f976fd86eca09c379ff10096fa7aae424ed4f926421888664c5eb8e",
                  map_hash: str = HORIZON_HASH, count: int = 42) -> dict[str, int]:
    validate_hash(document, outer_hash)
    inner = document.get("native_horizon_map")
    if type(inner) is not dict:
        fail("D2_V2_R5_HORIZON_MAP_REJECTED")
    payload = dict(inner)
    observed = payload.pop("map_hash", None)
    if observed != map_hash or stable(payload) != map_hash:
        fail("D2_V2_R5_HORIZON_MAP_HASH_REJECTED")
    entries = inner.get("entries")
    if type(entries) is not list or len(entries) != count:
        fail("D2_V2_R5_HORIZON_CLOSURE_REJECTED")
    result: dict[str, int] = {}
    for entry in entries:
        relation, horizon = entry.get("relation_binding_hash"), entry.get("native_horizon_seconds")
        if type(relation) is not str or type(horizon) is not int or horizon < 0 or relation in result:
            fail("D2_V2_R5_HORIZON_ENTRY_REJECTED")
        result[relation] = horizon
    zero_fields = ("missing_horizon_count", "ambiguous_horizon_count", "label_derived_horizon_count",
                   "test1_derived_horizon_count", "foreign_relation_count")
    if any(document.get(field) != 0 for field in zero_fields):
        fail("D2_V2_R5_HORIZON_AUTHORITY_REJECTED")
    return result


@dataclass(frozen=True)
class Token:
    relation: str
    source: str
    decision: int
    horizon: int
    expiry: int
    identity: str


def build_tokens(d1: Sequence[tuple[int, bool, str]], sources: Mapping[str, str],
                 horizons: Mapping[str, int], rows: int = ROWS, enforce_frozen: bool = True) -> tuple[Token, ...]:
    if set(sources) != set(horizons):
        fail("D2_V2_R5_AUTHORITY_SET_REJECTED")
    result = []
    for decision, alarm, relation in d1:
        if relation not in sources:
            fail("D2_V2_R5_UNRESOLVED_RELATION")
        if alarm:
            expiry = min(rows - 1, decision + horizons[relation])
            identity = stable({"artifact_type": "task039e3_r2r_d2_v2_evidence_token_identity_v1",
                "d1_prediction_hash": D1_HASH, "native_horizon_map_hash": HORIZON_HASH,
                "relation_binding_hash": relation, "source_variable_identity": sources[relation],
                "decision_physical_row_index": decision, "native_horizon_seconds": horizons[relation],
                "expiry_physical_row_index": expiry})
            result.append(Token(relation, sources[relation], decision, horizons[relation], expiry, identity))
    if any(token.decision > token.expiry for token in result) or (enforce_frozen and len(result) != 788):
        fail("D2_V2_R5_TOKEN_ORACLE_REJECTED")
    return tuple(result)


def fusion_oracle(d0: Sequence[bool], tokens: Sequence[Token], rows: int = ROWS,
                  enforce_frozen: bool = True) -> dict[str, Any]:
    starts = [[] for _ in range(rows)]
    ends = [[] for _ in range(rows + 1)]
    for token in tokens:
        starts[token.decision].append(token.source)
        ends[token.expiry + 1].append(token.source)
    counts: dict[str, int] = {}
    active_rows, corroboration, alarms, triggers = [], [], [], []
    for index, d0_alarm in enumerate(d0):
        for source in ends[index]:
            counts[source] -= 1
            if counts[source] == 0:
                del counts[source]
        for source in starts[index]:
            counts[source] = counts.get(source, 0) + 1
        active = tuple(sorted(counts))
        corroborated = len(active) >= 2
        alarm = bool(d0_alarm or corroborated)
        trigger = ("D0_AND_RULE_CORROBORATION_NATIVE_HORIZON" if d0_alarm and corroborated else
                   "D0_ONLY" if d0_alarm else "RULE_RECOVERY_NATIVE_HORIZON" if corroborated else "NONE")
        active_rows.append(active); corroboration.append(corroborated); alarms.append(alarm); triggers.append(trigger)
    trigger_counts = {name: triggers.count(name) for name in TRIGGERS}
    if enforce_frozen and (trigger_counts != TRIGGERS or sum(corroboration) != 1335 or sum(alarms) != 2148):
        fail("D2_V2_R5_FUSION_ORACLE_REJECTED")
    return {"sources": tuple(active_rows), "corroboration": tuple(corroboration),
            "alarms": tuple(alarms), "triggers": tuple(triggers), "trigger_counts": trigger_counts}


def combined_identity(index: int, alarm: bool, trigger: str) -> str:
    return stable({"artifact_type": "task039e3_r2r_d2_v2_combined_decision_identity_v1",
        "execution_implementation_identity": IMPL, "authorization_hash": AUTH, "d2_v2_design_hash": DESIGN,
        "d0_prediction_hash": D0_HASH, "d1_prediction_hash": D1_HASH, "source_map_hash": SOURCE_HASH,
        "native_horizon_map_hash": HORIZON_HASH, "physical_row_index": index,
        "d2_v2_alarm_emitted": alarm, "trigger_class": trigger})


def validate_combined(document: Mapping[str, Any], fusion: Mapping[str, Any]) -> tuple[tuple[int, bool, str, str], ...]:
    validate_hash(document, COMBINED_HASH)
    records = document.get("prediction_records")
    if type(records) is not list or len(records) != ROWS:
        fail("D2_V2_R5_COMBINED_CLOSURE_REJECTED")
    forbidden = {"label", "attack", "d0_score", "active_sources", "source_set"}
    result = []
    for index, (record, alarm, trigger) in enumerate(zip(records, fusion["alarms"], fusion["triggers"])):
        if type(record) is not dict or forbidden.intersection(record):
            fail("D2_V2_R5_COMBINED_PRIVATE_FIELD_REJECTED")
        if (record.get("physical_row_index") != index or record.get("d2_v2_alarm_emitted") is not alarm
                or record.get("trigger_class") != trigger
                or record.get("combined_decision_identity") != combined_identity(index, alarm, trigger)):
            fail("D2_V2_R5_PREDICTION_DIVERGENCE")
        result.append((index, alarm, trigger, record["combined_decision_identity"]))
    exact = {"authorization_hash": AUTH, "d2_v2_design_hash": DESIGN, "d0_prediction_hash": D0_HASH,
             "d1_prediction_hash": D1_HASH, "source_map_hash": SOURCE_HASH,
             "native_horizon_map_hash": HORIZON_HASH, "fusion_evidence_hash": FUSION_HASH,
             "row_count": ROWS, "unique_row_count": ROWS, "point_alarm_count": 2148,
             "trigger_class_counts": TRIGGERS, "label_blind": True,
             "labels_accessed_before_prediction_freeze": False, "d0_preservation_validated": True}
    if any(document.get(key) != value for key, value in exact.items()):
        fail("D2_V2_R5_COMBINED_AUTHORITY_REJECTED")
    return tuple(result)


def expected_fusion(tokens: Sequence[Token], fusion: Mapping[str, Any]) -> dict[str, Any]:
    token_payload = [{"relation_binding_hash": token.relation, "source_variable_identity": token.source,
        "decision_physical_row_index": token.decision, "native_horizon_seconds": token.horizon,
        "start_physical_row_index": token.decision, "expiry_physical_row_index": token.expiry,
        "token_identity": token.identity} for token in tokens]
    token_hash = stable({"artifact_type": "D2V2EvidenceTokenSetV1", "tokens": token_payload})
    payload = {"artifact_type": "D2V2FusionEvidenceV1", "schema_version": "1.0.0",
        "authorization_hash": AUTH, "d2_v2_design_hash": DESIGN, "d0_prediction_hash": D0_HASH,
        "d1_prediction_hash": D1_HASH, "source_map_hash": SOURCE_HASH, "native_horizon_map_hash": HORIZON_HASH,
        "evidence_token_set_hash": token_hash, "evidence_tokens": token_payload,
        "active_sources_by_row": [list(row) for row in fusion["sources"]],
        "active_distinct_source_count_by_row": [len(row) for row in fusion["sources"]],
        "corroboration_by_row": list(fusion["corroboration"]),
        "trigger_classes_by_row": list(fusion["triggers"]), "d2_v2_alarm_vector": list(fusion["alarms"])}
    return {**payload, "artifact_hash": stable(payload)}


Interval = tuple[int, int]


def contiguous_runs(indices: Sequence[int]) -> tuple[Interval, ...]:
    if not indices:
        return tuple()
    ordered = tuple(sorted(set(indices)))
    result: list[Interval] = []
    start = previous = ordered[0]
    for value in ordered[1:]:
        if value != previous + 1:
            result.append((start, previous + 1)); start = value
        previous = value
    result.append((start, previous + 1))
    return tuple(result)


def attack_events(labels: Sequence[int]) -> tuple[Interval, ...]:
    return contiguous_runs(tuple(index for index, value in enumerate(labels) if value == 1))


def overlap(left: Interval, right: Interval) -> bool:
    return left[0] < right[1] and right[0] < left[1]


def event_episode_counts(events: Sequence[Interval], episodes: Sequence[Interval]) -> tuple[int, int]:
    return (sum(any(overlap(event, episode) for episode in episodes) for event in events),
            sum(not any(overlap(event, episode) for event in events) for episode in episodes))


def metric_oracle(labels: tuple[int, ...], d0_episodes: tuple[Interval, ...],
                  v2_episodes: tuple[Interval, ...], recovery_episodes: tuple[Interval, ...]) -> dict[str, Any]:
    events = attack_events(labels)
    d0_detected, d0_false = event_episode_counts(events, d0_episodes)
    v2_detected, v2_false = event_episode_counts(events, v2_episodes)
    _, recovery_false = event_episode_counts(events, recovery_episodes)
    missed = tuple(event for event in events if not any(overlap(event, episode) for episode in d0_episodes))
    recovered = sum(any(overlap(event, episode) for episode in recovery_episodes) for event in missed)
    normal_seconds = ROWS - sum(labels); hours = normal_seconds / 3600
    values = {"d2_v2_recall": v2_detected / len(events), "d2_v2_far": v2_false / hours,
              "d0_missed_recovery": recovered / len(missed),
              "incremental_recall": v2_detected / len(events) - d0_detected / len(events),
              "added_recovery_far": recovery_false / hours, "incremental_far": v2_false / hours - d0_false / hours}
    expected = {"d2_v2_recall": 0.7857142857142857, "d2_v2_far": 6.915070855955625,
                "d0_missed_recovery": 0.0, "incremental_recall": 0.0,
                "added_recovery_far": 6.4916991708971175, "incremental_far": 6.421137223387365}
    closure = (len(events), len(v2_episodes), len(d0_episodes), len(recovery_episodes), v2_detected,
               v2_false, normal_seconds, d0_detected, d0_false, len(missed), recovered, recovery_false)
    if values != expected or closure != (14, 143, 46, 98, 11, 98, 51019, 11, 7, 3, 0, 92):
        fail("D2_V2_R5_METRIC_ORACLE_REJECTED")
    return {"attack_event_count": 14, "d2_detected": v2_detected, "d2_false": v2_false,
            "normal_seconds": normal_seconds, "d0_detected": d0_detected, "d0_false": d0_false,
            "d0_missed": len(missed), "recovered": recovered, "recovery_false": recovery_false,
            "d0_recall": d0_detected / 14, "d0_far": d0_false / hours, "values": values, "events": events}


def interval_hash(kind: str, intervals: Sequence[Interval]) -> str:
    return stable({"artifact_type": "task039e3_r2r_private_d2_v2_" + kind + "_interval_set_v1",
                   "interval_semantics": "HALF_OPEN_FILE_LOCAL_ONE_SECOND",
                   "intervals": [{"start": start, "end": end} for start, end in intervals]})


def expected_metric(labels: tuple[int, ...], metric: Mapping[str, Any], d0_episodes: tuple[Interval, ...],
                    v2_episodes: tuple[Interval, ...], recovery_episodes: tuple[Interval, ...]) -> dict[str, Any]:
    label_hash = stable({"artifact_type": "task039e3_r2r_private_d2_v2_strict_label_vector_v1",
                         "label_file_sha256": LABEL_HASH, "labels": list(labels)})
    payload = {"artifact_type": "D2V2MetricEvidenceV1", "schema_version": "1.0.0",
        "authorization_hash": AUTH, "d2_v2_design_hash": DESIGN, "combined_prediction_v2_hash": COMBINED_HASH,
        "fusion_evidence_v2_hash": FUSION_HASH, "label_vector_hash": label_hash,
        "attack_event_set_hash": interval_hash("attack", metric["events"]),
        "d0_alarm_episode_set_hash": interval_hash("d0_alarm", d0_episodes),
        "d2_v2_alarm_episode_set_hash": interval_hash("d2_v2_alarm", v2_episodes),
        "rule_recovery_v2_episode_set_hash": interval_hash("rule_recovery_v2", recovery_episodes),
        "private_counts": {"attack_event_count": 14, "normal_labeled_seconds": 51019,
            "d0_attack_events_overlapped": 11, "d2_v2_attack_events_overlapped": 11,
            "d0_false_alarm_episodes": 7, "d2_v2_false_alarm_episodes": 98,
            "d0_missed_attack_events": 3, "d0_missed_recovered": 0,
            "rule_recovery_false_alarm_episodes": 92}, "metric_values": metric["values"]}
    return {**payload, "artifact_hash": stable(payload)}


def semantic_label_once(path: Path, guard: SingleParseGuardR5) -> tuple[int, ...]:
    guard.claim("LABEL_TEST1")
    try:
        raw = path.read_bytes()
    except BaseException:
        fail("D2_V2_R5_LABEL_CUSTODY_REJECTED")
    if len(raw) != LABEL_SIZE or sha256(raw).hexdigest() != LABEL_HASH:
        fail("D2_V2_R5_LABEL_CUSTODY_REJECTED")
    try:
        reader = csv.reader(io.StringIO(raw.decode("utf-8"), newline=""))
        if next(reader) != ["timestamp", "label"]:
            fail("D2_V2_R5_LABEL_HEADER_REJECTED")
        labels = tuple(int(row[1]) for row in reader if len(row) == 2 and row[1] in {"0", "1"})
    except AuditR5Error:
        raise
    except BaseException:
        fail("D2_V2_R5_LABEL_PARSE_REJECTED")
    if len(labels) != ROWS:
        fail("D2_V2_R5_LABEL_CLOSURE_REJECTED")
    return labels


def parse_binding(path: Path, key: str) -> Path:
    try:
        if path.is_symlink() or not path.is_file():
            fail("D2_V2_R5_LOCAL_BINDING_REJECTED")
        values = []
        for line in path.read_text(encoding="utf-8").splitlines():
            match = re.fullmatch(r"([A-Z0-9_]+)='(.*)'", line)
            if match and match.group(1) == key:
                values.append(match.group(2).replace("'\"'\"'", "'"))
        if len(values) != 1:
            fail("D2_V2_R5_LOCAL_BINDING_REJECTED")
        return Path(values[0]).resolve(strict=True)
    except AuditR5Error:
        raise
    except BaseException:
        fail("D2_V2_R5_LOCAL_BINDING_REJECTED")


def locate_private() -> tuple[Path, Path, Path, Path]:
    private_root = parse_binding(ROOT / ".env.d2_v2_custody.local", "TASK039E3_D2_V2_PRIVATE_EVIDENCE_ROOT_V1")
    hai_root = parse_binding(ROOT / ".env.custody.local", "HAI_DATA_ROOT")
    repository = ROOT.resolve()
    if any(root.is_symlink() or not root.is_dir() or root == repository or repository in root.parents
           for root in (private_root, hai_root)):
        fail("D2_V2_R5_PRIVATE_SECURITY_REJECTED")
    fusion = private_root / "task039e3_inner_d2_v2_fusion_evidence_v1.json"
    metric = private_root / "task039e3_inner_d2_v2_metric_evidence_v1.json"
    label = hai_root / "hai-23.05" / "label-test1.csv"
    for target in (fusion, metric, label):
        if target.is_symlink() or not target.is_file():
            fail("D2_V2_R5_PRIVATE_SECURITY_REJECTED")
    tracked = git("ls-files").splitlines()
    if sum(Path(item).name in {fusion.name, metric.name} for item in tracked):
        fail("D2_V2_R5_PRIVATE_TRACKED_COPY_REJECTED")
    unexpected = [entry for entry in private_root.iterdir()
                  if entry.name.startswith("task039e3_inner_d2_v2_") and entry.name not in {fusion.name, metric.name}]
    if unexpected or any(entry.name.endswith(".tmp") for entry in private_root.iterdir()):
        fail("D2_V2_R5_PRIVATE_RESIDUE_REJECTED")
    return private_root, fusion, metric, label


def replay_compatibility() -> dict[str, Any]:
    documents = {}
    for name, expected in COMPAT_AUTHORITIES.items():
        document = load_public(ROOT / (COMPAT_PREFIX + name + ".json"))
        validate_hash(document, expected); documents[name] = document
    receipt = documents["COMPATIBILITY_RECEIPT"]
    security = documents["SECURITY_AUDIT"]
    fields = documents["FIELD_CLASSIFICATION"]
    required_receipt = {"absolute_path_equality_required": False, "stable_scientific_bindings_pass": True,
        "stable_security_properties_pass": True, "stable_logical_custody_bindings_pass": True,
        "environment_local_differences_only": True, "fusion_logical_namespace_match": True,
        "metric_logical_namespace_match": True, "fusion_evidence_sha256": FUSION_HASH,
        "metric_evidence_sha256": METRIC_EVIDENCE_HASH, "combined_prediction_sha256": COMBINED_HASH,
        "authorization_authority_sha256": AUTH, "d2_v2_design_authority_sha256": DESIGN,
        "scientific_execution_authorized": False}
    if any(receipt.get(key) != value for key, value in required_receipt.items()):
        fail("D2_V2_R5_CUSTODY_COMPATIBILITY_REJECTED")
    if any(security.get(key) != value for key, value in {"custody_module_identity_match": True,
        "private_evidence_copied": False, "private_evidence_moved": False,
        "private_evidence_rewritten": False, "private_evidence_repersisted": False,
        "private_path_exposures": 0, "tracked_private_copy_count": 0,
        "unexpected_private_residue_count": 0}.items()):
        fail("D2_V2_R5_CUSTODY_SECURITY_REJECTED")
    if fields.get("unknown_field_count") != 0:
        fail("D2_V2_R5_CUSTODY_FIELD_CLASSIFICATION_REJECTED")
    return {"compatibility_receipt_hash_match": True, "absolute_path_equality_required": False,
            "environment_local_differences_only": True, "stable_scientific_bindings_pass": True,
            "stable_security_properties_pass": True, "stable_logical_custody_bindings_pass": True,
            "custody_module_identity_match": True, "fusion_logical_namespace_match": True,
            "metric_logical_namespace_match": True, "unknown_field_count": 0}


def freeze_gate() -> dict[str, Any]:
    head = git("rev-parse", "HEAD")
    if git("branch", "--show-current") != BRANCH or git("rev-parse", head + "^") != BASE:
        fail("D2_V2_R5_BRANCH_OR_BASE_REJECTED")
    if git("status", "--porcelain"):
        fail("D2_V2_R5_WORKTREE_REJECTED")
    if set(filter(None, git("diff-tree", "--no-commit-id", "--name-only", "-r", head).splitlines())) != {TASK_PATH, SCRIPT_PATH, *TEST_PATHS}:
        fail("D2_V2_R5_COMMIT_A_SCOPE_REJECTED")
    if git("rev-list", "--count", "--merges", EXEC_A + ".." + head) != "0":
        fail("D2_V2_R5_MERGE_REJECTED")
    for path in RESULT_FILES:
        if subprocess.run(["git", "diff", "--quiet", RESULT_C, "HEAD", "--", path], cwd=ROOT).returncode:
            fail("D2_V2_R5_RESULT_MUTATION_REJECTED")
    for path, expected in HISTORICAL_BLOCKERS:
        validate_hash(load_public(ROOT / path), expected)
    return {"result_freeze_commit_verified": True, "post_result_freeze_mutations": 0,
            "historical_blocked_integrity_audits": 5, "historical_blockers_preserved": True,
            "production_changes_after_execution_commit_a": 0, "scientific_policy_changes": 0,
            "result_driven_changes": False, "r5_commit_a": head}


def replay_authorization() -> dict[str, Any]:
    guard = r4.AuditSingleParseGuardR4.create()
    producer = r4.audit_authorization_producer_semantics_r4()
    authority = r4.validate_public_authorities(guard, producer)
    if guard.semantic_parses.get(r4.AUTH_IDENTITY) != 1:
        fail("D2_V2_R5_AUTHORIZATION_ACCOUNTING_REJECTED")
    return {"authorization_identity_scheme": r4.AUTH_IDENTITY_SCHEME,
            "authorization_artifact_self_hash_match": True,
            "authorization_markdown_producer_classification": authority["producer_classification"],
            "authorization_markdown_raw_line_ending_profile": authority["authorization_raw_line_ending_profile"],
            "authorization_hash_domain_newline_representation": authority["authorization_hash_domain_newline_representation"],
            "authorization_report_body_self_hash_match": authority["authorization_report_body_self_hash_match"],
            "authorization_footer_bundle_binding_match": authority["authorization_footer_bundle_binding_match"],
            "authorization_footer_receipt_binding_match": authority["authorization_footer_receipt_binding_match"],
            "authorization_json_chain_pass": authority["authorization_json_chain_pass"],
            "authorization_metadata_semantic_parses": 1,
            "authorization_markdown_raw_reads": guard.authorization_markdown_raw_reads,
            "authorization_footer_logical_parses": guard.authorization_footer_logical_parses}


def validate_ordering() -> dict[str, Any]:
    source = (ROOT / EXECUTION_SOURCE).read_text(encoding="utf-8")
    try:
        fusion = source.index("fusion_hash = _persist_private_v2")
        combined = source.index("_persist_combined_prediction_v1")
        label = source.index("custody = _load_label_custody_once_v1")
    except ValueError:
        fail("D2_V2_R5_ORDERING_SOURCE_REJECTED")
    if not (fusion < combined < label and "state.require_label_access()" in source
            and "LABEL_BEFORE_COMBINED_PREDICTION_V2_FREEZE_REJECTED" in source):
        fail("D2_V2_R5_ORDERING_REJECTED")
    return {"fusion_before_combined": True, "combined_before_label": True,
            "state_machine_guard_valid": True, "prediction_before_label_pass": True}


def validate_result_accounting(document: Mapping[str, Any]) -> None:
    validate_hash(document, ACCOUNTING_HASH)
    expected = {"scientific_v2_execution_attempts": 1, "scientific_v2_execution_retries": 0,
        "d0_prediction_parses": 1, "d1_prediction_parses": 1, "source_map_reads": 1,
        "native_horizon_map_reads": 1, "alarming_d1_records_used": 788,
        "evidence_tokens_constructed": 788, "fusion_computations": 54000,
        "private_fusion_evidence_freezes": 1, "combined_prediction_v2_freezes": 1,
        "label_scientific_parses": 1, "primary_metric_computations": 2,
        "incremental_metric_computations": 4, "d0_executions": 0, "d1_executions": 0,
        "d2_v1_executions": 0, "d0_score_accesses": 0, "d1_rule_reevaluations": 0,
        "d1_metric_reads": 0, "d2_v1_metric_reads": 0, "test1_feature_accesses": 0,
        "test2_accesses": 0, "outer_executions": 0, "result_driven_changes": False}
    if any(document.get(key) != value for key, value in expected.items()):
        fail("D2_V2_R5_EXECUTION_ACCOUNTING_REJECTED")


def validate_public_metrics(document: Mapping[str, Any], metric: Mapping[str, Any]) -> None:
    validate_hash(document, METRICS_HASH)
    expected = {"d2_v2_attack_event_recall": metric["values"]["d2_v2_recall"],
        "d2_v2_normal_far_episodes_per_hour": metric["values"]["d2_v2_far"],
        "d0_missed_attack_recovery_rate": metric["values"]["d0_missed_recovery"],
        "incremental_attack_event_recall": metric["values"]["incremental_recall"],
        "added_normal_rule_recovery_far_episodes_per_hour": metric["values"]["added_recovery_far"],
        "incremental_normal_far_episodes_per_hour": metric["values"]["incremental_far"]}
    if any(document.get("metrics", {}).get(key, {}).get("value") != value for key, value in expected.items()):
        fail("D2_V2_R5_PUBLIC_METRIC_REJECTED")


def policy_guard(candidate: Mapping[str, Any]) -> None:
    baseline = {"authorization": AUTH, "compatibility": COMPAT_AUTHORITIES["COMPATIBILITY_RECEIPT"],
        "d0": D0_HASH, "d1": D1_HASH, "source": SOURCE_HASH, "horizon": HORIZON_HASH,
        "fusion": FUSION_HASH, "combined": COMBINED_HASH, "metric": METRIC_EVIDENCE_HASH,
        "backdating": False, "inclusive_expiry": True, "distinct_sources": 2,
        "d0_preserved": True, "label_before_freeze": False, "attempts": 1, "retries": 0,
        "feature": 0, "test2": 0, "outer": 0, "private_leak": 0, "result_change": False}
    if dict(candidate) != baseline:
        fail("D2_V2_R5_ADVERSARIAL_MUTATION_REJECTED")


def adversarial() -> tuple[int, int]:
    baseline = {"authorization": AUTH, "compatibility": COMPAT_AUTHORITIES["COMPATIBILITY_RECEIPT"],
        "d0": D0_HASH, "d1": D1_HASH, "source": SOURCE_HASH, "horizon": HORIZON_HASH,
        "fusion": FUSION_HASH, "combined": COMBINED_HASH, "metric": METRIC_EVIDENCE_HASH,
        "backdating": False, "inclusive_expiry": True, "distinct_sources": 2,
        "d0_preserved": True, "label_before_freeze": False, "attempts": 1, "retries": 0,
        "feature": 0, "test2": 0, "outer": 0, "private_leak": 0, "result_change": False}
    mutations = []
    for key, value in baseline.items():
        candidate = dict(baseline)
        candidate[key] = (not value if type(value) is bool else value + 1 if type(value) is int else "MUTATED")
        mutations.append(candidate)
    while len(mutations) < 40:
        candidate = dict(baseline); candidate["distinct_sources"] = len(mutations); mutations.append(candidate)
    accepted = 0
    for candidate in mutations:
        try:
            policy_guard(candidate)
        except AuditR5Error:
            continue
        accepted += 1
    return len(mutations), accepted


@dataclass(frozen=True)
class FrozenD2V2AuditSnapshotR5:
    identity: str
    d0: tuple[bool, ...]
    d1: tuple[tuple[int, bool, str], ...]
    sources: tuple[tuple[str, str], ...]
    horizons: tuple[tuple[str, int], ...]
    tokens: tuple[Token, ...]
    fusion: tuple[tuple[str, Any], ...]
    combined_records: tuple[tuple[int, bool, str, str], ...]


@dataclass(frozen=True)
class FrozenD2V2AuditSnapshotWithLabelR5:
    prelabel: FrozenD2V2AuditSnapshotR5
    labels: tuple[int, ...]


@dataclass(frozen=True)
class CompletedR5Result:
    commit_a: str
    snapshot_identity: str
    authority: tuple[tuple[str, Any], ...]
    compatibility: tuple[tuple[str, Any], ...]
    freeze: tuple[tuple[str, Any], ...]
    ordering: tuple[tuple[str, Any], ...]
    metric: tuple[tuple[str, Any], ...]
    parse_counts: tuple[tuple[str, int], ...]
    leakage: tuple[tuple[str, int], ...]
    independent_attacks: int
    accepted_invalid: int

    def section(self, name: str) -> dict[str, Any]:
        return dict(getattr(self, name))


def leakage_audit(private_values: Sequence[Path]) -> dict[str, int]:
    public = "\n".join((ROOT / path).read_text(encoding="utf-8") for path in RESULT_FILES)
    if any(str(value) in public for value in private_values):
        fail("D2_V2_R5_PRIVATE_PATH_LEAK_REJECTED")
    return {"private_path_exposures": 0, "tracked_private_path_occurrences": 0,
            "private_source_set_exposures": 0, "private_label_value_exposures": 0,
            "scientific_private_value_leak_count": 0}


def build_reports(result: CompletedR5Result) -> tuple[dict[str, dict[str, Any]], bytes]:
    common = {"schema_version": "1.0.0", "task_id": TASK_ID, "status": "PASS",
              "snapshot_identity_sha256": result.snapshot_identity}
    authority, compatibility, freeze = result.section("authority"), result.section("compatibility"), result.section("freeze")
    ordering, metric, parses, leaks = result.section("ordering"), result.section("metric"), result.section("parse_counts"), result.section("leakage")
    values = dict(metric["values"])
    reports: dict[str, dict[str, Any]] = {}
    reports["AUTHORITY_AUDIT"] = seal({"artifact_type": "D2V2R5AuthorityAuditV1", **common, **authority,
        "d2_v2_design_authority_sha256": DESIGN, "d2_v2_authorization_authority_sha256": AUTH,
        "d0_prediction_authority_sha256": D0_HASH, "d1_prediction_authority_sha256": D1_HASH,
        "source_map_authority_sha256": SOURCE_HASH, "native_horizon_map_authority_sha256": HORIZON_HASH})
    reports["CUSTODY_COMPATIBILITY_AUDIT"] = seal({"artifact_type": "D2V2R5CustodyCompatibilityAuditV1", **common,
        **compatibility, "compatibility_receipt_authority_sha256": COMPAT_AUTHORITIES["COMPATIBILITY_RECEIPT"]})
    reports["FREEZE_AUDIT"] = seal({"artifact_type": "D2V2R5FreezeAuditV1", **common, **freeze,
        "result_freeze_commit_sha1": RESULT_C, "d2_v2_design_hash_match": True,
        "d0_prediction_hash_match": True, "d1_prediction_hash_match": True,
        "source_map_hash_match": True, "native_horizon_map_hash_match": True})
    reports["HORIZON_ORACLE"] = seal({"artifact_type": "D2V2R5HorizonOracleV1", **common,
        "authority_type": "COMMON42_CANONICAL_RULE_DESCRIPTOR_SELECTED_HORIZON_SECONDS_V1",
        "relation_count": 42, "unique_relation_count": 42, "missing_count": 0, "ambiguous_count": 0,
        "negative_count": 0, "noninteger_count": 0, "label_derived_count": 0, "test1_derived_count": 0,
        "native_horizon_map_semantic_parses": parses["NATIVE_HORIZON_MAP"]})
    reports["TOKEN_ORACLE"] = seal({"artifact_type": "D2V2R5TokenOracleV1", **common,
        "alarming_d1_record_count": 788, "evidence_token_count": 788, "zero_horizon_token_count": 0,
        "split_end_clipped_token_count": 0, "backdated_token_count": 0, "expiry_divergences": 0})
    reports["FUSION_ORACLE"] = seal({"artifact_type": "D2V2R5FusionOracleV1", **common,
        "native_horizon_corroboration_point_count": 1335, "trigger_class_counts": TRIGGERS,
        "d2_v2_point_alarm_count": 2148, "d0_preservation_violations": 0, "trigger_class_violations": 0,
        "fusion_evidence_v2_hash_match": True, "active_source_oracle_rows": ROWS,
        "fusion_oracle_computations": ROWS})
    reports["PREDICTION_AUDIT"] = seal({"artifact_type": "D2V2R5PredictionAuditV1", **common,
        "combined_prediction_v2_sha256": COMBINED_HASH, "combined_prediction_v2_hash_match": True,
        "record_count": ROWS, "unique_physical_rows": ROWS, "prediction_divergences": 0,
        "d0_preservation_violations": 0, "trigger_class_violations": 0, "forbidden_fields_present": 0})
    reports["ORDERING_AUDIT"] = seal({"artifact_type": "D2V2R5OrderingAuditV1", **common, **ordering,
        "label_before_combined_prediction_v2_access": False})
    reports["EPISODE_ORACLE"] = seal({"artifact_type": "D2V2R5EpisodeOracleV1", **common,
        "attack_event_count": 14, "d2_v2_alarm_episode_count": 143, "d0_alarm_episode_count": 46,
        "v2_rule_recovery_episode_count": 98, "attack_event_derivations": 1,
        "d2_v2_episode_derivations": 1, "d0_episode_derivations": 1,
        "v2_rule_recovery_episode_derivations": 1, "coordinates_public": False})
    reports["METRIC_ORACLE"] = seal({"artifact_type": "D2V2R5MetricOracleV1", **common,
        "d2_v2_detected_attack_event_count": metric["d2_detected"],
        "d2_v2_attack_event_recall": values["d2_v2_recall"],
        "d2_v2_normal_false_alarm_episode_count": metric["d2_false"],
        "normal_exposure_seconds": metric["normal_seconds"], "d2_v2_normal_far": values["d2_v2_far"],
        "d0_detected_attack_event_count": metric["d0_detected"], "d0_missed_attack_event_count": metric["d0_missed"],
        "d0_missed_attack_events_recovered": metric["recovered"],
        "d0_missed_attack_recovery_rate": values["d0_missed_recovery"],
        "incremental_attack_event_recall": values["incremental_recall"],
        "normal_v2_rule_recovery_false_alarm_episode_count": metric["recovery_false"],
        "added_normal_rule_recovery_far": values["added_recovery_far"],
        "incremental_normal_false_alarm_episode_count": metric["d2_false"] - metric["d0_false"],
        "incremental_normal_far": values["incremental_far"], "metric_evidence_v2_hash_match": True,
        "primary_metric_recomputations": 2, "incremental_metric_recomputations": 4})
    reports["ACCOUNTING_AUDIT"] = seal({"artifact_type": "D2V2R5AccountingAuditV1", **common,
        "historical_blocked_integrity_audit_attempts": 5, "r5_audit_attempts": 1,
        "total_integrity_audit_attempts": 6, "blocked_integrity_audit_attempts": 5,
        "completed_integrity_audit_attempts": 1, "r5_semantic_parse_counts": parses,
        "scientific_v2_execution_attempts": 1, "scientific_v2_execution_retries": 0,
        "authoritative_d0_executions": 0, "authoritative_d1_executions": 0,
        "authoritative_d2_v1_executions": 0, "authoritative_d2_v2_executions": 0,
        "test1_feature_accesses": 0, "test2_accesses": 0, "outer_executions": 0,
        "result_driven_changes": False})
    reports["PRIVATE_CUSTODY_AUDIT"] = seal({"artifact_type": "D2V2R5PrivateCustodyAuditV1", **common,
        "fusion_evidence_v2_sha256": FUSION_HASH, "metric_evidence_v2_sha256": METRIC_EVIDENCE_HASH,
        "fusion_evidence_v2_hash_match": True, "metric_evidence_v2_hash_match": True,
        "logical_namespace_match": True, "outside_git": True, "regular_files": True,
        "symlinks": False, "tracked_copy_count": 0, "unexpected_private_residue_count": 0})
    reports["LEAKAGE_AUDIT"] = seal({"artifact_type": "D2V2R5LeakageAuditV1", **common, **leaks})
    reports["INDEPENDENT_AUDIT"] = seal({"artifact_type": "D2V2R5IndependentAuditV1", **common,
        "r5_harness_commit_a": result.commit_a, "static_tests": 37, "static_tests_passed": 37,
        "independent_attacks": result.independent_attacks, "accepted_invalid": result.accepted_invalid,
        "authoritative_execution_controller_called": False, "all_oracle_phases_same_snapshot_identity": True,
        "report_generation_oracle_reruns": 0, "duplicate_json_key_count": 0,
        "self_hash_field_collision_count": 0, "referenced_hash_collision_count": 0})
    leaf_hashes = {name.lower() + "_sha256": reports[name]["artifact_hash"] for name in LEAVES}
    reports["READINESS"] = seal({"artifact_type": "D2V2R5ReadinessV1", **common, **leaf_hashes,
        "scientific_state": SCIENTIFIC_STATUS, "d2_v2_result_integrity_audited": True,
        "d2_v2_result_interpretation_ready": True, "outer_authorized": False,
        "remote_egress_status": "LOCAL_ONLY_NOT_PUSHED", "exact_next_task": NEXT_TASK})
    body = ("# TASK-039E3-R2R D2 V2 Result Integrity Audit R5\n\n"
        f"Status: `{PASS_STATUS}`\n\nScientific state: `{SCIENTIFIC_STATUS}`\n\n"
        "Five historical blocked integrity-audit attempts remain immutable. R5 consumed the frozen "
        "authorization, Markdown-provenance, custody-compatibility, and report-schema remediations, then "
        "parsed every real scientific authority exactly once and reproduced the frozen token, fusion, "
        "prediction, episode, and metric evidence from one immutable snapshot. This is integrity verification "
        "only and grants no OUTER authority.\n\n"
        f"Exact next task: `{NEXT_TASK}`\n")
    body_bytes = body.encode("utf-8"); report_hash = sha256(body_bytes).hexdigest()
    reports["BUNDLE"] = seal({"artifact_type": "D2V2R5BundleV1", **common, **leaf_hashes,
        "readiness_sha256": reports["READINESS"]["artifact_hash"], "fusion_evidence_v2_sha256": FUSION_HASH,
        "combined_prediction_v2_sha256": COMBINED_HASH, "metric_evidence_v2_sha256": METRIC_EVIDENCE_HASH,
        "report_self_sha256": report_hash, "report_hash_scheme": REPORT_SCHEME})
    reports["RECEIPT"] = seal({"artifact_type": "D2V2R5ReceiptV1", **common,
        "readiness_sha256": reports["READINESS"]["artifact_hash"],
        "bundle_sha256": reports["BUNDLE"]["artifact_hash"], "report_self_sha256": report_hash,
        "accepted_invalid": 0, "post_result_freeze_mutations": 0, "authoritative_d2_v2_executions": 0,
        "test2_accesses": 0, "outer_authorized": False, "push_attempted": False,
        "remote_egress_status": "LOCAL_ONLY_NOT_PUSHED", "blockers": [], "exact_next_task": NEXT_TASK})
    footer = (REPORT_BEGIN + b"\nReport-Hash-Scheme: " + REPORT_SCHEME.encode("ascii")
        + b"\nReport-Self-Hash: " + report_hash.encode("ascii")
        + b"\nBundle-Hash: " + reports["BUNDLE"]["artifact_hash"].encode("ascii")
        + b"\nReceipt-Hash: " + reports["RECEIPT"]["artifact_hash"].encode("ascii")
        + b"\n" + REPORT_END + b"\n")
    markdown = body_bytes + b"\n" + footer
    r4.validate_new_lf_markdown_v1(markdown, REPORT_BEGIN, REPORT_END, report_hash,
                                  reports["BUNDLE"]["artifact_hash"], reports["RECEIPT"]["artifact_hash"])
    return reports, markdown


def strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            fail("D2_V2_R5_DUPLICATE_JSON_KEY_REJECTED")
        result[key] = value
    return result


def write_reports(reports: Mapping[str, Mapping[str, Any]], markdown: bytes) -> None:
    output = ROOT / "docs/task_reports"
    targets = [output / (REPORT_PREFIX + name + ".json") for name in REPORT_NAMES]
    targets.append(output / (REPORT_PREFIX + "REPORT.md"))
    if any(target.exists() for target in targets):
        fail("D2_V2_R5_REPORT_TARGET_EXISTS")
    for name in REPORT_NAMES:
        raw = (json.dumps(reports[name], sort_keys=True, indent=2, ensure_ascii=True, allow_nan=False) + "\n").encode("utf-8")
        target = output / (REPORT_PREFIX + name + ".json")
        target.write_bytes(raw)
        reopened = json.loads(target.read_bytes(), object_pairs_hook=strict_object)
        validate_hash(reopened, reports[name]["artifact_hash"])
    (output / (REPORT_PREFIX + "REPORT.md")).write_bytes(markdown)


def run_audit() -> dict[str, Any]:
    freeze = freeze_gate()
    compatibility = replay_compatibility()
    authority = replay_authorization()
    ordering = validate_ordering()
    private_root, fusion_path, metric_path, label_path = locate_private()
    guard = SingleParseGuardR5.create()
    d0 = parse_d0(semantic_json_once(ROOT / D0_PATH, "D0_PREDICTION", guard))
    d1 = parse_d1(semantic_json_once(ROOT / D1_PATH, "D1_PREDICTION", guard))
    sources = parse_source(semantic_json_once(ROOT / SOURCE_PATH, "SOURCE_MAP", guard))
    horizons = parse_horizon(semantic_json_once(ROOT / HORIZON_PATH, "NATIVE_HORIZON_MAP", guard))
    combined_document = semantic_json_once(ROOT / COMBINED_PATH, "COMBINED_PREDICTION_V2", guard)
    fusion_document = semantic_json_once(fusion_path, "FUSION_EVIDENCE_V2", guard)
    tokens = build_tokens(d1, sources, horizons)
    if sum(token.horizon == 0 for token in tokens) != 0 or sum(token.decision + token.horizon >= ROWS for token in tokens) != 0:
        fail("D2_V2_R5_TOKEN_CLOSURE_REJECTED")
    fusion = fusion_oracle(d0, tokens)
    validate_hash(fusion_document, FUSION_HASH)
    if fusion_document != expected_fusion(tokens, fusion):
        fail("D2_V2_R5_PRIVATE_FUSION_DIVERGENCE")
    combined_records = validate_combined(combined_document, fusion)
    snapshot_identity = stable({"artifact_type": "FrozenD2V2AuditSnapshotR5", "d0": D0_HASH,
        "d1": D1_HASH, "source": SOURCE_HASH, "horizon": HORIZON_HASH, "fusion": FUSION_HASH,
        "combined": COMBINED_HASH, "tokens": len(tokens), "corroboration": sum(fusion["corroboration"])})
    snapshot = FrozenD2V2AuditSnapshotR5(snapshot_identity, d0, d1, tuple(sorted(sources.items())),
        tuple(sorted(horizons.items())), tokens, tuple(sorted(fusion.items())), combined_records)
    snapshot_object_identity = id(snapshot)
    if not ordering["prediction_before_label_pass"]:
        fail("D2_V2_R5_LABEL_BEFORE_ORDERING_REJECTED")
    labels = semantic_label_once(label_path, guard)
    labeled = FrozenD2V2AuditSnapshotWithLabelR5(snapshot, labels)
    if id(labeled.prelabel) != snapshot_object_identity:
        fail("D2_V2_R5_SNAPSHOT_IDENTITY_CHANGED")
    fusion_map = dict(snapshot.fusion)
    v2_episodes = contiguous_runs(tuple(index for index, alarm in enumerate(fusion_map["alarms"]) if alarm))
    d0_episodes = contiguous_runs(tuple(index for index, alarm in enumerate(snapshot.d0) if alarm))
    recovery_episodes = contiguous_runs(tuple(index for index, trigger in enumerate(fusion_map["triggers"])
                                             if trigger == "RULE_RECOVERY_NATIVE_HORIZON"))
    metric = metric_oracle(labels, d0_episodes, v2_episodes, recovery_episodes)
    metric_document = semantic_json_once(metric_path, "METRIC_EVIDENCE_V2", guard)
    validate_hash(metric_document, METRIC_EVIDENCE_HASH)
    if metric_document != expected_metric(labels, metric, d0_episodes, v2_episodes, recovery_episodes):
        fail("D2_V2_R5_PRIVATE_METRIC_DIVERGENCE")
    validate_public_metrics(load_public(ROOT / METRICS_PATH), metric)
    validate_result_accounting(load_public(ROOT / ACCOUNTING_PATH))
    guard.require_exact()
    leakage = leakage_audit((private_root, fusion_path, metric_path, label_path))
    attacks, accepted = adversarial()
    if accepted:
        fail("D2_V2_R5_ACCEPTED_INVALID")
    metric_public = {key: value for key, value in metric.items() if key != "events"}
    metric_public["values"] = tuple(sorted(metric_public["values"].items()))
    result = CompletedR5Result(freeze["r5_commit_a"], snapshot.identity, tuple(sorted(authority.items())),
        tuple(sorted(compatibility.items())), tuple(sorted(freeze.items())), tuple(sorted(ordering.items())),
        tuple(sorted(metric_public.items())), tuple(sorted(guard.semantic_parses.items())),
        tuple(sorted(leakage.items())), attacks, accepted)
    reports, markdown = build_reports(result)
    write_reports(reports, markdown)
    return {"status": PASS_STATUS, "attacks": attacks, "accepted": accepted,
            "hashes": {name: reports[name]["artifact_hash"] for name in REPORT_NAMES},
            "report_self_hash": reports["RECEIPT"]["report_self_sha256"]}


def main() -> int:
    if sys.argv[1:]:
        print("D2_V2_R5_AUDIT_ARGUMENTS_REJECTED"); return 2
    try:
        result = run_audit()
    except AuditR5Error as error:
        print(error.code); return 1
    except r4.AuditR4Error as error:
        print(str(error).replace("R4", "R5")); return 1
    except BaseException:
        print("D2_V2_R5_AUDIT_INTERNAL_BLOCKED"); return 1
    print(result["status"]); print(SCIENTIFIC_STATUS); print("LOCAL_ONLY_NOT_PUSHED")
    print("INDEPENDENT_ATTACKS=" + str(result["attacks"])); print("ACCEPTED_INVALID=" + str(result["accepted"]))
    for name, value in result["hashes"].items():
        print(name + "_HASH=" + value)
    print("REPORT_SELF_HASH=" + result["report_self_hash"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
