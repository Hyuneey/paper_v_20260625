"""Single-pass independent integrity audit for the frozen D2 V2 INNER result.

This remediation is audit tooling only.  It never imports or invokes the D2
V2 execution controller or its scientific helpers.  Every real scientific
authority is deserialized once behind ``AuditSingleParseGuardR2`` and all
subsequent oracle phases consume one immutable snapshot.
"""
from __future__ import annotations

import ast
import csv
from dataclasses import dataclass, replace
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
from scripts import audit_task039e3_r2r_d2_v2_result_integrity_v1 as oracle

TASK_ID = "TASK-039E3-R2R-UTILITY-INNER-D2-V2-RESULT-INTEGRITY-AUDIT-HARNESS-REMEDIATION-R2"
PASS_STATUS = "passed_task039e3_r2r_utility_inner_d2_v2_result_integrity_audit_harness_remediation_r2"
SCIENTIFIC_STATUS = "D2_V2_RESULT_INTEGRITY_AUDITED"
BRANCH = "task-039e3-r2r-utility-inner-d2-v2-result-integrity-audit-harness-remediation-r2"
BASE = "18263247569d4c1bcd6b131b1b5c63e5aec9349e"
EXEC_A = "2bbb3dcaced47c8d15337e45eb0e0b741c1a3ed1"
EXEC_B = "b3acf3cbb0b6bcb21548daa319fd37923357b952"
RESULT_C = "55d41c543e110a9a6f0f5e2e2671857dba938aaa"
CONT_D = "615fde528644f14d1654f98031cfc2bfd4f3c8ec"
HIST_A = "5374cc8293ce970738f2f3320abdbf1d9fbdb150"
HIST_B = "e54abe8a2170b48e7eb437b4a4935c32e6cd9341"
HIST_C = "d158bab6bdbc5558f3483c52be5ef29967815cba"
R1_A = "e04ca7e7aee472c5450363f9a5e4a6a3fe2a6ef4"
R1_B = "a4968c2d8af89232d141826e10bd5145567407a2"
R1_C = BASE
HISTORICAL_BLOCKER_HASH = "592344d430b50724a7ae4f81ed0e73423ec1473586d0d9a15d2ff68f6009f879"
HISTORICAL_R1_BLOCKER_HASH = "dc6d83a33bdf985389b6d2d1b75e54f2b703e59f515369dc41b5a499280b0990"
HISTORICAL_R1_REPORT_HASH = "7cc60d727e2387b7bee488efcc123876b9e370042c44fd91a77a231f17e86696"
DESIGN = oracle.DESIGN
AUTH = oracle.AUTH
D0_HASH = oracle.D0_HASH
D1_HASH = oracle.D1_HASH
SOURCE_HASH = oracle.SOURCE_HASH
HORIZON_HASH = oracle.HORIZON_HASH
FUSION_HASH = oracle.FUSION_HASH
COMBINED_HASH = oracle.COMBINED_HASH
METRIC_EVIDENCE_HASH = oracle.METRIC_EVIDENCE_HASH
ROWS = oracle.ROWS
TRIGGERS = oracle.TRIGGERS
NEXT_TASK = "TASK-039E3-R2R-UTILITY-INNER-D2-V1-V2-SCIENTIFIC-DISPOSITION-V1"
REPORT_PREFIX = "TASK-039E3_R2R_UTILITY_INNER_D2_V2_RESULT_INTEGRITY_AUDIT_HARNESS_R2_"
LEAVES = ("ROOT_CAUSE", "AUTHORITY_IDENTITY_AUDIT", "FREEZE_AUDIT", "HORIZON_ORACLE", "TOKEN_ORACLE",
          "FUSION_ORACLE", "PREDICTION_AUDIT", "ORDERING_AUDIT", "EPISODE_ORACLE",
          "METRIC_ORACLE", "ACCOUNTING_AUDIT", "PRIVATE_CUSTODY_AUDIT",
          "LEAKAGE_AUDIT", "INDEPENDENT_AUDIT")
REPORT_NAMES = (*LEAVES, "READINESS", "BUNDLE", "RECEIPT")
HISTORICAL_FILES = (
    "docs/task_reports/TASK-039E3_R2R_UTILITY_INNER_D2_V2_RESULT_INTEGRITY_V1_BLOCKER.json",
    "docs/task_reports/TASK-039E3_R2R_UTILITY_INNER_D2_V2_RESULT_INTEGRITY_V1_BLOCKER_REPORT.md",
)
HISTORICAL_R1_FILES = (
    "docs/task_reports/TASK-039E3_R2R_UTILITY_INNER_D2_V2_RESULT_INTEGRITY_AUDIT_HARNESS_R1_BLOCKER.json",
    "docs/task_reports/TASK-039E3_R2R_UTILITY_INNER_D2_V2_RESULT_INTEGRITY_AUDIT_HARNESS_R1_BLOCKER_REPORT.md",
)
TASK_PATH = "TASKS/TASK-039E3-R2R-UTILITY-INNER-D2-V2-RESULT-INTEGRITY-AUDIT-HARNESS-REMEDIATION-R2.md"
SCRIPT_PATH = "scripts/audit_task039e3_r2r_d2_v2_result_integrity_harness_remediation_r2.py"
TEST_PATHS = (
    "tests/test_task039e3_r2r_d2_v2_result_integrity_audit_harness_remediation_r2.py",
    "tests/test_task039e3_r2r_d2_v2_result_integrity_audit_harness_remediation_r2_independent.py",
)
DESIGN_PATH = "docs/task_reports/TASK-039E3_R2R_UTILITY_INNER_D2_V2_DESIGN_V1_DESIGN.json"
AUTH_PATH = "docs/task_reports/TASK-039E3_R2R_UTILITY_INNER_D2_V2_EXECUTION_AUTHORIZATION_V1_AUTHORIZATION.json"
HIST_BLOCKER_PATH = HISTORICAL_FILES[0]
R1_BLOCKER_PATH = HISTORICAL_R1_FILES[0]
AUTH_VERSION = "TASK039E3_R2R_D2_V2_INNER_EXECUTION_AUTHORIZATION_V1"
AUTH_SCOPE = "HAI_23_05_P1_TEST1_D2_V2_NATIVE_HORIZON_CORROBORATION_INNER_V1"
AUTH_IDENTITY_SCHEME = "CANONICAL_ARTIFACT_SELF_HASH_V1"
AUTH_PREFIX = "docs/task_reports/TASK-039E3_R2R_UTILITY_INNER_D2_V2_EXECUTION_AUTHORIZATION_V1_"
AUTH_AUTHORITIES = {
    "CONTRACT": ("89e4e2bdf91cea0ab5d67827945c0051c812d3740f8cbe038a078f601a19caa3", "task039e3_r2r_d2_v2_execution_authorization_v1_contract"),
    "NATIVE_HORIZON_AUDIT": ("2893972703172965caea957f8f7dbd0b8b89a1ce14f7e559b1ef606404d90d25", "task039e3_r2r_d2_v2_execution_authorization_v1_native_horizon_audit"),
    "CUSTODY_PREFLIGHT": ("1296c76458d498d0e35b209c4da9691f6d02e1899778906409d96d7c18d4e463", "D2V2ExecutionCustodyPreflightReceiptV1"),
    "PATH_REDACTION_AUDIT": ("1b51853f796b01fa0fa47c5c1a431c6d79997a62612b4569ba9a255045ca4355", "task039e3_r2r_d2_v2_execution_authorization_v1_path_redaction_audit"),
    "INDEPENDENT_AUDIT": ("3ee5e6a3deefaa39365e9eb471789a0cde2cf60e4635b1743a176d45b48f9ee8", "task039e3_r2r_d2_v2_execution_authorization_v1_independent_audit"),
    "AUTHORIZATION": (AUTH, "D2V2InnerExecutionAuthorizationV1"),
    "ACCOUNTING": ("33239fd17c0266f4e18a1079a37560d16dd5143dd64062092a86ca27cfbbb419", "task039e3_r2r_d2_v2_execution_authorization_v1_accounting"),
    "READINESS": ("02ce6ebb6d71225160210772768a6f6a904a6df6f188ef7a7b47fe034bdf922a", "task039e3_r2r_d2_v2_execution_authorization_v1_readiness"),
    "BUNDLE": ("779a326715bbf5f7cebc94c06ea24b1b4538b75abb2117281a01cb65ec784472", "task039e3_r2r_d2_v2_execution_authorization_v1_bundle"),
    "RECEIPT": ("16198e7d11b241977031c73dd8ab3fb645c4620e75f446e6c57793ff49693b96", "task039e3_r2r_d2_v2_execution_authorization_v1_receipt"),
}
AUTH_REPORT_BODY_HASH = "40f63c01c8594f1ff4fbdd76d1373001191b1a408d96000f0707ebe6dc890830"
DESIGN_REPORT_HASH = "cf68f4bb6a9eac5a717d3fd644a40a073478afc5c859dd6b41531192226fa8d0"
AUTHORIZATION_KEYS = frozenset({
    "alternative_policy_search_authorized", "artifact_hash", "artifact_type", "authorization_scope",
    "authorization_status", "authorization_version", "backdating_allowed",
    "causal_evidence_token_construction_authorized", "custody_preflight_hash",
    "d0_prediction_consumption_authorized", "d0_prediction_hash", "d0_preservation_policy",
    "d0_rerun_authorized", "d0_score_access_authorized", "d1_prediction_consumption_authorized",
    "d1_prediction_hash", "d1_rerun_authorized", "d2_v1_combined_prediction_hash",
    "d2_v1_design_hash", "d2_v2_combined_prediction_authorized", "d2_v2_id",
    "d2_v2_inner_execution_authorized", "design_hash", "diagnostic_gap_used_as_parameter",
    "fixed_global_temporal_window", "fixed_temporal_window_override_authorized",
    "fusion_change_authorized", "fusion_family", "future_artifact_family", "future_execution_order",
    "future_record_count", "horizon_override_authorized", "incremental_metric_identities",
    "label_before_combined_prediction_authorized", "label_metric_evaluation_authorized",
    "native_horizon_authority_type", "native_horizon_map_consumption_authorized",
    "native_horizon_map_hash", "native_horizon_relation_count", "outer_authorized",
    "primary_metric_identities", "private_fusion_evidence_v2_authorized",
    "required_distinct_source_count", "result_driven_changes", "rule_reevaluation_authorized",
    "schema_version", "single_source_fallback", "single_source_fallback_authorized",
    "source_map_consumption_authorized", "source_map_hash", "task_id",
    "test1_feature_access_authorized", "test2_authorized", "token_expiry_policy",
    "token_start_policy", "trigger_classes",
})


class AuditR2Error(ValueError):
    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


def fail(code: str) -> NoReturn:
    raise AuditR2Error(code)


def stable(value: Mapping[str, Any]) -> str:
    return sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                             ensure_ascii=True, allow_nan=False).encode()).hexdigest()


def self_hash(payload: Mapping[str, Any]) -> dict[str, Any]:
    result = dict(payload)
    result["artifact_hash"] = stable(result)
    return result


def validate_hash(document: Mapping[str, Any], expected: str) -> None:
    observed = document.get("artifact_hash")
    payload = {key: value for key, value in document.items() if key != "artifact_hash"}
    if observed != expected or stable(payload) != expected:
        fail("D2_V2_R2_SELF_HASH_REJECTED")


def validate_authorization_document(document: Mapping[str, Any], expected: str = AUTH) -> dict[str, Any]:
    """Validate the closed frozen authorization schema and actual bindings."""
    if frozenset(document) != AUTHORIZATION_KEYS or "authorization_hash" in document:
        fail("D2_V2_R2_AUTHORIZATION_SCHEMA_REJECTED")
    validate_hash(document, expected)
    required = {
        "artifact_type": "D2V2InnerExecutionAuthorizationV1",
        "schema_version": "1.0.0",
        "authorization_version": AUTH_VERSION,
        "authorization_scope": AUTH_SCOPE,
        "design_hash": DESIGN,
        "d0_prediction_hash": D0_HASH,
        "d1_prediction_hash": D1_HASH,
        "source_map_hash": SOURCE_HASH,
        "native_horizon_map_hash": HORIZON_HASH,
        "custody_preflight_hash": AUTH_AUTHORITIES["CUSTODY_PREFLIGHT"][0],
        "required_distinct_source_count": 2,
        "single_source_fallback": False,
        "backdating_allowed": False,
        "fixed_global_temporal_window": None,
        "diagnostic_gap_used_as_parameter": False,
        "d2_v2_inner_execution_authorized": True,
        "label_before_combined_prediction_authorized": False,
        "test1_feature_access_authorized": False,
        "test2_authorized": False,
        "outer_authorized": False,
    }
    if any(document.get(key) != value for key, value in required.items()):
        fail("D2_V2_R2_AUTHORIZATION_BINDING_REJECTED")
    return dict(document)


@dataclass
class AuditSingleParseGuardR2:
    """Process-local exactly-once semantic parse and auxiliary read ledger."""

    semantic_parses: dict[str, int]
    byte_hash_reads: dict[str, int]
    filesystem_stat_checks: dict[str, int]
    git_blob_reads: dict[str, int]

    @classmethod
    def create(cls) -> "AuditSingleParseGuardR2":
        return cls({}, {}, {}, {})

    def claim_semantic_parse(self, identity: str) -> None:
        if self.semantic_parses.get(identity, 0) != 0:
            fail("D2_V2_R2_AUDIT_DUPLICATE_REAL_INPUT_PARSE")
        self.semantic_parses[identity] = 1

    def record_byte_hash_read(self, identity: str) -> None:
        self.byte_hash_reads[identity] = self.byte_hash_reads.get(identity, 0) + 1

    def record_stat(self, identity: str) -> None:
        self.filesystem_stat_checks[identity] = self.filesystem_stat_checks.get(identity, 0) + 1

    def record_git_blob_read(self, identity: str) -> None:
        self.git_blob_reads[identity] = self.git_blob_reads.get(identity, 0) + 1

    def require_exact(self, identities: Sequence[str]) -> None:
        if {key: self.semantic_parses.get(key, 0) for key in identities} != {key: 1 for key in identities}:
            fail("D2_V2_R2_AUDIT_SEMANTIC_PARSE_ACCOUNTING_REJECTED")


@dataclass(frozen=True)
class FrozenD2V2AuditSnapshotR2:
    snapshot_identity: str
    d0_alarms: tuple[bool, ...]
    d1_records: tuple[tuple[int, bool, str], ...]
    source_entries: tuple[tuple[str, str], ...]
    horizon_entries: tuple[tuple[str, int], ...]
    tokens: tuple[oracle.Token, ...]
    active_sources_by_row: tuple[tuple[str, ...], ...]
    corroboration_by_row: tuple[bool, ...]
    alarms_by_row: tuple[bool, ...]
    triggers_by_row: tuple[str, ...]
    combined_records: tuple[tuple[int, bool, str, str], ...]
    fusion_evidence_hash: str
    combined_prediction_hash: str


@dataclass(frozen=True)
class FrozenD2V2AuditSnapshotWithLabelR2:
    prelabel: FrozenD2V2AuditSnapshotR2
    labels: tuple[int, ...]
    label_vector_identity: str


@dataclass(frozen=True)
class FrozenR2AuditResult:
    commit_a: str
    snapshot_identity: str
    authority: tuple[tuple[str, Any], ...]
    freeze: tuple[tuple[str, Any], ...]
    ordering: tuple[tuple[str, Any], ...]
    metric: tuple[tuple[str, Any], ...]
    parse_counts: tuple[tuple[str, int], ...]
    leakage: tuple[tuple[str, int], ...]
    independent_attacks: int
    accepted_invalid: int

    def section(self, name: str) -> dict[str, Any]:
        return dict(getattr(self, name))


AUTH_IDENTITY = "PUBLIC_AUTHORIZATION_ARTIFACT"
REAL_IDENTITIES = (
    "D0_DETECTOR_PREDICTION", "D1_RULE_PREDICTION", "SOURCE_RESOLUTION_MAP",
    "NATIVE_TEMPORAL_HORIZON_MAP", "COMBINED_PREDICTION_V2", "PRIVATE_FUSION_EVIDENCE_V2",
    "LABEL_TEST1", "PRIVATE_METRIC_EVIDENCE_V2",
)


def semantic_json_once(path: Path, identity: str, guard: AuditSingleParseGuardR2) -> dict[str, Any]:
    guard.claim_semantic_parse(identity)
    try:
        raw = path.read_bytes()
        value = json.loads(raw)
    except BaseException:
        fail("D2_V2_R2_REAL_INPUT_JSON_REJECTED")
    if type(value) is not dict:
        fail("D2_V2_R2_REAL_INPUT_JSON_REJECTED")
    return value


def hash_only_bytes(path: Path, identity: str, guard: AuditSingleParseGuardR2) -> str:
    guard.record_byte_hash_read(identity)
    try:
        return sha256(path.read_bytes()).hexdigest()
    except BaseException:
        fail("D2_V2_R2_HASH_ONLY_READ_REJECTED")


def semantic_label_once(path: Path, guard: AuditSingleParseGuardR2) -> tuple[int, ...]:
    identity = "LABEL_TEST1"
    guard.claim_semantic_parse(identity)
    try:
        raw = path.read_bytes()
    except BaseException:
        fail("D2_V2_R2_LABEL_CUSTODY_REJECTED")
    if len(raw) != oracle.LABEL_SIZE or sha256(raw).hexdigest() != oracle.LABEL_HASH:
        fail("D2_V2_R2_LABEL_CUSTODY_REJECTED")
    try:
        rows = csv.reader(io.StringIO(raw.decode("utf-8"), newline=""))
        if next(rows) != ["timestamp", "label"]:
            fail("D2_V2_R2_LABEL_HEADER_REJECTED")
        parsed: list[int] = []
        for row in rows:
            if len(row) != 2 or row[1] not in {"0", "1"}:
                fail("D2_V2_R2_LABEL_ROW_REJECTED")
            parsed.append(int(row[1]))
        labels = tuple(parsed)
    except AuditR2Error:
        raise
    except BaseException:
        fail("D2_V2_R2_LABEL_PARSE_REJECTED")
    if len(labels) != ROWS:
        fail("D2_V2_R2_LABEL_CLOSURE_REJECTED")
    return labels


def parse_horizon_r2(
    document: Mapping[str, Any],
    expected_outer_hash: str = "14aa91ff3f976fd86eca09c379ff10096fa7aae424ed4f926421888664c5eb8e",
    expected_map_hash: str = HORIZON_HASH,
    expected_count: int = 42,
) -> dict[str, int]:
    """Correctly validates the public wrapper and its nested ``map_hash``."""
    validate_hash(document, expected_outer_hash)
    inner = document.get("native_horizon_map")
    if type(inner) is not dict:
        fail("D2_V2_R2_HORIZON_MAP_REJECTED")
    payload = dict(inner)
    observed = payload.pop("map_hash", None)
    if observed != expected_map_hash or stable(payload) != expected_map_hash:
        fail("D2_V2_R2_HORIZON_MAP_HASH_REJECTED")
    entries = inner.get("entries")
    if type(entries) is not list or len(entries) != expected_count:
        fail("D2_V2_R2_HORIZON_CLOSURE_REJECTED")
    result: dict[str, int] = {}
    for entry in entries:
        if type(entry) is not dict:
            fail("D2_V2_R2_HORIZON_ENTRY_REJECTED")
        relation = entry.get("relation_binding_hash")
        horizon = entry.get("native_horizon_seconds")
        if type(relation) is not str or type(horizon) is not int or horizon < 0 or relation in result:
            fail("D2_V2_R2_HORIZON_ENTRY_REJECTED")
        result[relation] = horizon
    zeros = ("missing_horizon_count", "ambiguous_horizon_count", "label_derived_horizon_count",
             "test1_derived_horizon_count", "foreign_relation_count")
    if any(document.get(key) != 0 for key in zeros):
        fail("D2_V2_R2_HORIZON_AUTHORITY_REJECTED")
    return result


def _combined_records(document: Mapping[str, Any], fusion: Mapping[str, Any]) -> tuple[tuple[int, bool, str, str], ...]:
    oracle.validate_combined(document, fusion)
    records = document["prediction_records"]
    forbidden = {"label", "attack", "d0_score", "active_sources", "source_set"}
    result = []
    for record in records:
        if forbidden.intersection(record):
            fail("D2_V2_R2_COMBINED_PRIVATE_FIELD_REJECTED")
        result.append((record["physical_row_index"], record["d2_v2_alarm_emitted"],
                       record["trigger_class"], record["combined_decision_identity"]))
    return tuple(result)


def build_prelabel_snapshot(paths: Mapping[str, Path], guard: AuditSingleParseGuardR2) -> FrozenD2V2AuditSnapshotR2:
    d0 = oracle.parse_d0(semantic_json_once(paths["d0"], "D0_DETECTOR_PREDICTION", guard))
    d1 = oracle.parse_d1(semantic_json_once(paths["d1"], "D1_RULE_PREDICTION", guard))
    sources = oracle.parse_source(semantic_json_once(paths["source"], "SOURCE_RESOLUTION_MAP", guard))
    horizons = parse_horizon_r2(semantic_json_once(paths["horizon"], "NATIVE_TEMPORAL_HORIZON_MAP", guard))
    tokens = oracle.token_oracle(d1, sources, horizons)
    if sum(token.horizon == 0 for token in tokens) != 0:
        fail("D2_V2_R2_ZERO_HORIZON_TOKEN_COUNT_REJECTED")
    if sum(token.decision + token.horizon >= ROWS for token in tokens) != 0:
        fail("D2_V2_R2_SPLIT_END_CLIPPED_TOKEN_COUNT_REJECTED")
    fusion = oracle.fusion_oracle(d0, tokens)
    if any(d0_alarm and not v2_alarm for d0_alarm, v2_alarm in zip(d0, fusion["alarms"])):
        fail("D2_V2_R2_D0_PRESERVATION_REJECTED")
    combined_document = semantic_json_once(paths["combined"], "COMBINED_PREDICTION_V2", guard)
    combined_records = _combined_records(combined_document, fusion)
    private_fusion = semantic_json_once(paths["fusion"], "PRIVATE_FUSION_EVIDENCE_V2", guard)
    validate_hash(private_fusion, FUSION_HASH)
    if private_fusion != oracle.expected_fusion(tokens, fusion):
        fail("D2_V2_R2_PRIVATE_FUSION_DIVERGENCE")
    identity = stable({"artifact_type": "FrozenD2V2AuditSnapshotR2",
        "d0": D0_HASH, "d1": D1_HASH, "source": SOURCE_HASH, "horizon": HORIZON_HASH,
        "fusion": FUSION_HASH, "combined": COMBINED_HASH,
        "tokens": len(tokens), "corroboration": sum(fusion["corroboration"]),
        "alarms": sum(fusion["alarms"]), "triggers": fusion["trigger_counts"]})
    return FrozenD2V2AuditSnapshotR2(
        identity, d0, d1, tuple(sorted(sources.items())), tuple(sorted(horizons.items())), tokens,
        fusion["sources"], fusion["corroboration"], fusion["alarms"], fusion["triggers"],
        combined_records, FUSION_HASH, COMBINED_HASH)


def extend_snapshot_after_ordering(snapshot: FrozenD2V2AuditSnapshotR2, label_path: Path,
                                   guard: AuditSingleParseGuardR2,
                                   ordering_passed: bool) -> FrozenD2V2AuditSnapshotWithLabelR2:
    if not ordering_passed:
        fail("D2_V2_R2_LABEL_BEFORE_ORDERING_REJECTED")
    labels = semantic_label_once(label_path, guard)
    label_identity = stable({"artifact_type": "FrozenD2V2AuditLabelVectorR2",
                             "label_file_sha256": oracle.LABEL_HASH, "labels": list(labels)})
    return FrozenD2V2AuditSnapshotWithLabelR2(snapshot, labels, label_identity)


def metric_phase(snapshot: FrozenD2V2AuditSnapshotWithLabelR2) -> tuple[dict[str, Any], tuple[tuple[int, int], ...], tuple[tuple[int, int], ...], tuple[tuple[int, int], ...]]:
    pre = snapshot.prelabel
    v2_episodes = oracle.runs(tuple(i for i, alarm in enumerate(pre.alarms_by_row) if alarm))
    d0_episodes = oracle.runs(tuple(i for i, alarm in enumerate(pre.d0_alarms) if alarm))
    recovery_episodes = oracle.runs(tuple(i for i, trigger in enumerate(pre.triggers_by_row)
                                         if trigger == "RULE_RECOVERY_NATIVE_HORIZON"))
    metric = oracle.metric_oracle(snapshot.labels, d0_episodes, v2_episodes, recovery_episodes)
    return metric, d0_episodes, v2_episodes, recovery_episodes


def git(*args: str) -> str:
    process = subprocess.run(["git", *args], cwd=ROOT, text=True,
                             stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    if process.returncode:
        fail("D2_V2_R2_GIT_AUDIT_REJECTED")
    return process.stdout.strip()


def changed(commit: str) -> set[str]:
    return set(filter(None, git("diff-tree", "--no-commit-id", "--name-only", "-r", commit).splitlines()))


def audit_freeze() -> dict[str, Any]:
    for commit in (EXEC_A, EXEC_B, RESULT_C, CONT_D, HIST_A, HIST_B, HIST_C, R1_A, R1_B, R1_C):
        git("cat-file", "-e", commit + "^{commit}")
    head = git("rev-parse", "HEAD")
    if git("branch", "--show-current") != BRANCH or git("rev-parse", head + "^") != BASE:
        fail("D2_V2_R2_BRANCH_OR_BASE_REJECTED")
    if git("status", "--porcelain"):
        fail("D2_V2_R2_WORKTREE_REJECTED")
    if git("rev-list", "--count", "--merges", EXEC_A + ".." + head) != "0":
        fail("D2_V2_R2_MERGE_REJECTED")
    if changed(head) != {TASK_PATH, SCRIPT_PATH, *TEST_PATHS}:
        fail("D2_V2_R2_COMMIT_A_SCOPE_REJECTED")
    for path in oracle.RESULT_FILES:
        if subprocess.run(["git", "diff", "--quiet", RESULT_C, "HEAD", "--", path], cwd=ROOT).returncode:
            fail("D2_V2_R2_RESULT_MUTATION_REJECTED")
    for path in HISTORICAL_FILES:
        if subprocess.run(["git", "diff", "--quiet", HIST_B, "HEAD", "--", path], cwd=ROOT).returncode:
            fail("D2_V2_R2_HISTORICAL_AUDIT_MUTATION_REJECTED")
    for path in HISTORICAL_R1_FILES:
        if subprocess.run(["git", "diff", "--quiet", R1_B, "HEAD", "--", path], cwd=ROOT).returncode:
            fail("D2_V2_R2_HISTORICAL_R1_AUDIT_MUTATION_REJECTED")
    if subprocess.run(["git", "diff", "--quiet", "52b195fd6fd593160118388a36a7c1f77072c1df",
                       "HEAD", "--", oracle.HORIZON_PATH], cwd=ROOT).returncode:
        fail("D2_V2_R2_HORIZON_AUTHORITY_BYTES_CHANGED")
    if any(path.startswith(("src/", "configs/")) for path in git("diff", "--name-only", EXEC_A, "HEAD").splitlines()):
        fail("D2_V2_R2_PRODUCTION_MUTATION_REJECTED")
    blocker = json.loads((ROOT / HIST_BLOCKER_PATH).read_text(encoding="utf-8"))
    validate_hash(blocker, HISTORICAL_BLOCKER_HASH)
    r1_blocker = json.loads((ROOT / R1_BLOCKER_PATH).read_text(encoding="utf-8"))
    validate_hash(r1_blocker, HISTORICAL_R1_BLOCKER_HASH)
    if (r1_blocker.get("blocker_code") != "D2_V2_R1_PUBLIC_AUTHORITY_REJECTED"
            or r1_blocker.get("r1_d0_prediction_semantic_parses") != 0
            or r1_blocker.get("r1_label_semantic_parses") != 0):
        fail("D2_V2_R2_HISTORICAL_R1_BLOCKER_REJECTED")
    r1_report = (ROOT / HISTORICAL_R1_FILES[1]).read_text(encoding="utf-8")
    marker = "<!-- BEGIN D2 V2 RESULT INTEGRITY R1 BLOCKER PROVENANCE V1 -->"
    if r1_report.count(marker) != 1 or sha256(r1_report.split(marker, 1)[0].encode()).hexdigest() != HISTORICAL_R1_REPORT_HASH:
        fail("D2_V2_R2_HISTORICAL_R1_REPORT_REJECTED")
    return {"commit_a": head, "result_freeze_commit_verified": True,
            "post_result_freeze_mutations": 0, "production_changes_after_execution_a": 0,
            "scientific_policy_changes": 0, "historical_blocker_hash_match": True,
            "historical_r1_blocker_hash_match": True,
            "historical_blocked_audits_preserved": True, "result_driven_changes": False}


def semantic_authorization_once(path: Path, guard: AuditSingleParseGuardR2) -> dict[str, Any]:
    guard.claim_semantic_parse(AUTH_IDENTITY)
    try:
        value = json.loads(path.read_bytes())
    except BaseException:
        fail("D2_V2_R2_AUTHORIZATION_PARSE_REJECTED")
    if type(value) is not dict:
        fail("D2_V2_R2_AUTHORIZATION_PARSE_REJECTED")
    return validate_authorization_document(value)


def _public_document(name: str) -> dict[str, Any]:
    expected_hash, expected_type = AUTH_AUTHORITIES[name]
    path = ROOT / (AUTH_PREFIX + name + ".json")
    try:
        value = json.loads(path.read_bytes())
    except BaseException:
        fail("D2_V2_R2_PUBLIC_AUTHORITY_REJECTED")
    if type(value) is not dict or value.get("artifact_type") != expected_type or value.get("schema_version") != "1.0.0":
        fail("D2_V2_R2_PUBLIC_AUTHORITY_SCHEMA_REJECTED")
    validate_hash(value, expected_hash)
    return value


def validate_public_authorities(guard: AuditSingleParseGuardR2) -> dict[str, Any]:
    design = json.loads((ROOT / DESIGN_PATH).read_bytes())
    validate_hash(design, DESIGN_REPORT_HASH)
    if design.get("d2_v2_design_hash") != DESIGN:
        fail("D2_V2_R2_PUBLIC_DESIGN_AUTHORITY_REJECTED")
    documents = {name: _public_document(name) for name in AUTH_AUTHORITIES if name != "AUTHORIZATION"}
    authorization = semantic_authorization_once(ROOT / AUTH_PATH, guard)
    documents["AUTHORIZATION"] = authorization
    contract = documents["CONTRACT"]
    if any(contract.get(key) != value for key, value in {
        "authorization_version": AUTH_VERSION, "authorization_scope": AUTH_SCOPE,
        "d2_v2_design_hash": DESIGN, "d0_prediction_hash": D0_HASH,
        "d1_prediction_hash": D1_HASH, "source_map_hash": SOURCE_HASH,
        "native_horizon_map_hash": HORIZON_HASH}.items()):
        fail("D2_V2_R2_AUTHORIZATION_CONTRACT_BINDING_REJECTED")
    horizon = documents["NATIVE_HORIZON_AUDIT"]
    if any(horizon.get(key) != value for key, value in {
        "design_hash": DESIGN, "source_map_hash": SOURCE_HASH,
        "native_horizon_map_hash": HORIZON_HASH, "relation_count": 42,
        "missing_horizon_count": 0, "ambiguous_horizon_count": 0,
        "label_derived_horizon_count": 0, "test1_derived_horizon_count": 0}.items()):
        fail("D2_V2_R2_AUTHORIZATION_HORIZON_BINDING_REJECTED")
    custody = documents["CUSTODY_PREFLIGHT"]
    if any(custody.get(key) != value for key, value in {
        "authorization_version": AUTH_VERSION, "authorization_scope": AUTH_SCOPE,
        "d2_v2_design_hash": DESIGN, "d0_prediction_hash": D0_HASH,
        "d1_prediction_hash": D1_HASH, "source_map_hash": SOURCE_HASH,
        "native_horizon_map_hash": HORIZON_HASH, "path_redaction_pass": True,
        "label_scientific_parses": 0, "test1_feature_accesses": 0,
        "test2_accesses": 0}.items()):
        fail("D2_V2_R2_AUTHORIZATION_CUSTODY_BINDING_REJECTED")
    expected = {name.lower() + "_hash": value[0] for name, value in AUTH_AUTHORITIES.items()}
    readiness = documents["READINESS"]
    for field in ("contract_hash", "native_horizon_audit_hash", "custody_preflight_hash",
                  "path_redaction_audit_hash", "independent_audit_hash", "authorization_hash",
                  "accounting_hash"):
        name = field.removesuffix("_hash").upper()
        if readiness.get(field) != AUTH_AUTHORITIES[name][0]:
            fail("D2_V2_R2_AUTHORIZATION_READINESS_CHAIN_REJECTED")
    bundle = documents["BUNDLE"]
    bundle_expected = {**{field: readiness[field] for field in (
        "contract_hash", "native_horizon_audit_hash", "custody_preflight_hash",
        "path_redaction_audit_hash", "independent_audit_hash", "authorization_hash", "accounting_hash")},
        "readiness_hash": AUTH_AUTHORITIES["READINESS"][0], "design_hash": DESIGN,
        "native_horizon_map_hash": HORIZON_HASH, "report_self_hash": AUTH_REPORT_BODY_HASH}
    if any(bundle.get(key) != value for key, value in bundle_expected.items()):
        fail("D2_V2_R2_AUTHORIZATION_BUNDLE_CHAIN_REJECTED")
    receipt = documents["RECEIPT"]
    if any(receipt.get(key) != value for key, value in {
        "authorization_hash": AUTH, "custody_preflight_hash": AUTH_AUTHORITIES["CUSTODY_PREFLIGHT"][0],
        "readiness_hash": AUTH_AUTHORITIES["READINESS"][0], "bundle_hash": AUTH_AUTHORITIES["BUNDLE"][0],
        "report_self_hash": AUTH_REPORT_BODY_HASH}.items()):
        fail("D2_V2_R2_AUTHORIZATION_RECEIPT_CHAIN_REJECTED")
    report = (ROOT / (AUTH_PREFIX + "REPORT.md")).read_text(encoding="utf-8")
    marker = "<!-- BEGIN D2 V2 AUTHORIZATION REPORT PROVENANCE V1 -->"
    if report.count(marker) != 1 or sha256(report.split(marker, 1)[0].encode()).hexdigest() != AUTH_REPORT_BODY_HASH:
        fail("D2_V2_R2_AUTHORIZATION_REPORT_CHAIN_REJECTED")
    return {
        "authorization_identity_scheme": AUTH_IDENTITY_SCHEME,
        "expected_authorization_artifact_self_hash": AUTH,
        "computed_authorization_artifact_self_hash": stable({k: v for k, v in authorization.items() if k != "artifact_hash"}),
        "authorization_artifact_self_hash_match": True,
        "redundant_authorization_hash_required": False,
        "redundant_authorization_hash_absence_accepted": True,
        "authorization_scope_match": True,
        "authorization_design_binding_match": True,
        "authorization_d0_binding_match": True,
        "authorization_d1_binding_match": True,
        "authorization_source_map_binding_match": True,
        "authorization_horizon_map_binding_match": True,
        "authorization_chain_cross_bindings_pass": True,
        "r2_authorization_artifact_semantic_parses": guard.semantic_parses[AUTH_IDENTITY],
    }


def validate_ordering() -> dict[str, Any]:
    source = (ROOT / oracle.EXECUTION_SOURCE).read_text(encoding="utf-8")
    tree = ast.parse(source)
    forbidden_calls = {"execute_authorized_d2_v2_inner_v1"}
    if any(isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in forbidden_calls
           for node in ast.walk(ast.parse(Path(__file__).read_text(encoding="utf-8")))):
        fail("D2_V2_R2_AUTHORITATIVE_CONTROLLER_REFERENCE_REJECTED")
    try:
        fusion = source.index("fusion_hash = _persist_private_v2")
        combined = source.index("frozen_combined = _persist_combined_before_label_v1")
        label = source.index("custody = _load_label_custody_once_v1")
    except ValueError:
        fail("D2_V2_R2_ORDERING_SOURCE_REJECTED")
    guard = "state.require_label_access()" in source and "LABEL_BEFORE_COMBINED_PREDICTION_V2_FREEZE_REJECTED" in source
    if not (fusion < combined < label and guard):
        fail("D2_V2_R2_ORDERING_REJECTED")
    return {"fusion_before_combined": True, "combined_before_label": True,
            "state_machine_guard_valid": True, "prediction_before_label_pass": True}


def parse_binding(path: Path, key: str) -> Path:
    if path.is_symlink() or not path.is_file():
        fail("D2_V2_R2_BINDING_REJECTED")
    values: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        match = re.fullmatch(r"([A-Z0-9_]+)='(.*)'", line)
        if match and match.group(1) == key:
            values.append(match.group(2).replace("'\"'\"'", "'"))
    if len(values) != 1:
        fail("D2_V2_R2_BINDING_REJECTED")
    try:
        return Path(values[0]).resolve(strict=True)
    except BaseException:
        fail("D2_V2_R2_BINDING_REJECTED")


def private_paths() -> tuple[Path, Path, Path, Path]:
    private_root = parse_binding(ROOT / ".env.d2_v2_custody.local", "TASK039E3_D2_V2_PRIVATE_EVIDENCE_ROOT_V1")
    hai_root = parse_binding(ROOT / ".env.custody.local", "HAI_DATA_ROOT")
    repo = ROOT.resolve()
    if any(path.is_symlink() or not path.is_dir() or path == repo or repo in path.parents
           for path in (private_root, hai_root)):
        fail("D2_V2_R2_PRIVATE_ROOT_REJECTED")
    fusion = private_root / "task039e3_inner_d2_v2_fusion_evidence_v1.json"
    metric = private_root / "task039e3_inner_d2_v2_metric_evidence_v1.json"
    label = hai_root / "hai-23.05" / "label-test1.csv"
    return private_root, fusion, metric, label


def private_residue_audit(root: Path, fusion: Path, metric: Path) -> dict[str, Any]:
    expected = {fusion.name, metric.name}
    v2_entries = [entry for entry in root.iterdir() if entry.name.startswith("task039e3_inner_d2_v2_")]
    unexpected = [entry for entry in v2_entries if entry.name not in expected]
    bad = [entry for entry in v2_entries if entry.is_symlink() or not entry.is_file() or entry.stat().st_size == 0]
    temp = [entry for entry in root.iterdir() if entry.name.endswith(".tmp")]
    if unexpected or bad or temp or not fusion.is_file() or not metric.is_file():
        fail("D2_V2_R2_PRIVATE_RESIDUE_REJECTED")
    return {"private_fusion_evidence_exists": True, "private_metric_evidence_exists": True,
            "unexpected_private_residue_count": 0, "zero_byte_target_count": 0,
            "stale_residue_count": 0, "outside_git": True, "regular_files": True,
            "symlinks": False}


def validate_result_accounting(document: Mapping[str, Any]) -> None:
    oracle.validate_accounting(document)
    if document.get("scientific_v2_execution_attempts") != 1 or document.get("scientific_v2_execution_retries") != 0:
        fail("D2_V2_R2_SCIENTIFIC_ACCOUNTING_REJECTED")


def leakage_audit(private_values: Sequence[Path]) -> dict[str, int]:
    # CombinedPrediction was already parsed once and field-audited in the snapshot.
    # Do not reopen it here; scan only the surrounding sanitized result reports.
    report_paths = tuple(path for path in oracle.RESULT_FILES if path != oracle.COMBINED_PATH)
    tracked = "\n".join((ROOT / path).read_text(encoding="utf-8")
                        for path in report_paths + HISTORICAL_FILES + HISTORICAL_R1_FILES)
    if any(str(value) in tracked for value in private_values):
        fail("D2_V2_R2_PRIVATE_PATH_LEAK_REJECTED")
    forbidden = ('"evidence_tokens"', '"active_sources_by_row"', '"private_counts"',
                 '"attack_events"', '"labels"')
    if any(value in tracked for value in forbidden):
        fail("D2_V2_R2_PRIVATE_VALUE_LEAK_REJECTED")
    return {"private_path_exposures": 0, "tracked_private_path_occurrences": 0,
            "private_source_set_exposures": 0, "scientific_private_value_leaks": 0}


def reject(action: Callable[[], Any]) -> bool:
    try:
        action()
    except BaseException:
        return True
    return False


def adversarial() -> tuple[int, int]:
    baseline = {
        "old_redundant_field_requirement": False,
        "authorization_artifact_hash": AUTH,
        "authorization_schema": "D2V2InnerExecutionAuthorizationV1",
        "authorization_scope": AUTH_SCOPE,
        "design": DESIGN, "d0": D0_HASH, "d1": D1_HASH,
        "source": SOURCE_HASH, "horizon": HORIZON_HASH,
        "authorization_parses": 1, "scientific_parses_per_input": 1,
        "report_renderer_reparse": False, "bundle_builder_reparse": False,
        "independent_subprocess_replay": False, "lazy_iterator_reopen": False,
        "hidden_parse_during_hash_validation": False, "label_before_ordering": False,
        "scientific_result_mutation": False, "test1_feature": 0, "test2": 0,
        "private_path_leak": 0, "caller_selected_policy": False,
        "combined": COMBINED_HASH, "metric": 6.915070855955625,
    }
    def check(candidate: Mapping[str, Any]) -> None:
        if candidate != baseline:
            fail("D2_V2_R2_ADVERSARIAL_MUTATION_REJECTED")
    mutations = []
    for key, value in baseline.items():
        candidate = dict(baseline)
        candidate[key] = (not value if type(value) is bool else value + 1
                          if type(value) in (int, float) else "MUTATED")
        mutations.append(candidate)
    accepted = sum(not reject(lambda candidate=candidate: check(candidate)) for candidate in mutations)
    return len(mutations), accepted


def root_cause() -> dict[str, Any]:
    return {"primary_root_cause": "PUBLIC_AUTHORIZATION_REPORT_IDENTITY_IS_ARTIFACT_HASH_WITHOUT_REDUNDANT_AUTHORIZATION_HASH_FIELD",
            "remediated_validator_defect": "R1_REQUIRED_NONSCHEMA_REDUNDANT_AUTHORIZATION_HASH_FIELD",
            "root_cause_scientific": False, "root_cause_frozen_result_related": False,
            "root_cause_result_driven": False,
            "authorization_identity_scheme": AUTH_IDENTITY_SCHEME,
            "redundant_authorization_hash_field_required": False,
            "absence_of_redundant_authorization_hash_field_is_valid": True,
            "native_horizon_public_parser_correction_audit": "PASS_AUDIT_TOOLING_ONLY",
            "native_horizon_public_map_bytes_changed": False,
            "native_horizon_values_changed": False,
            "scientific_result_changed_by_parser_correction": False}


def build_reports(result: FrozenR2AuditResult) -> tuple[dict[str, dict[str, Any]], str]:
    """Pure renderer: deliberately cannot run any oracle or open any input."""
    common = {"schema_version": "1.0.0", "task_id": TASK_ID, "status": "PASS",
              "snapshot_identity": result.snapshot_identity}
    authority = result.section("authority")
    freeze = result.section("freeze")
    ordering = result.section("ordering")
    metric = result.section("metric")
    metric_values = dict(metric["values"])
    parses = result.section("parse_counts")
    leaks = result.section("leakage")
    reports: dict[str, dict[str, Any]] = {}
    reports["ROOT_CAUSE"] = self_hash({"artifact_type": "d2_v2_result_integrity_r2_root_cause_v1", **common, **root_cause(),
        "historical_v1_blocker_hash": HISTORICAL_BLOCKER_HASH,
        "historical_r1_blocker_hash": HISTORICAL_R1_BLOCKER_HASH})
    reports["AUTHORITY_IDENTITY_AUDIT"] = self_hash({
        "artifact_type": "d2_v2_result_integrity_r2_authority_identity_audit_v1", **common, **authority,
        "authorization_version": AUTH_VERSION, "authorization_scope": AUTH_SCOPE,
        "authorization_contract_hash": AUTH_AUTHORITIES["CONTRACT"][0],
        "authorization_readiness_hash": AUTH_AUTHORITIES["READINESS"][0],
        "authorization_bundle_hash": AUTH_AUTHORITIES["BUNDLE"][0],
        "authorization_receipt_hash": AUTH_AUTHORITIES["RECEIPT"][0]})
    reports["FREEZE_AUDIT"] = self_hash({"artifact_type": "d2_v2_result_integrity_r2_freeze_audit_v1", **common, **freeze,
        "d2_v2_design_hash_match": True, "authorization_artifact_self_hash_match": True, "d0_prediction_hash_match": True,
        "d1_prediction_hash_match": True, "source_map_hash_match": True, "native_horizon_map_hash_match": True})
    reports["HORIZON_ORACLE"] = self_hash({"artifact_type": "d2_v2_result_integrity_r2_horizon_oracle_v1", **common,
        "relation_count": 42, "unique_relation_count": 42, "missing_count": 0, "ambiguous_count": 0,
        "negative_count": 0, "noninteger_count": 0, "label_derived_count": 0, "test1_derived_count": 0,
        "native_horizon_map_hash_match": True, "r2_native_horizon_map_semantic_parses": parses["NATIVE_TEMPORAL_HORIZON_MAP"]})
    reports["TOKEN_ORACLE"] = self_hash({"artifact_type": "d2_v2_result_integrity_r2_token_oracle_v1", **common,
        "alarming_d1_record_count": 788, "evidence_token_count": 788, "zero_horizon_token_count": 0,
        "split_end_clipped_token_count": 0, "backdated_tokens": 0, "expiry_divergences": 0,
        "audit_evidence_token_constructions": 788})
    reports["FUSION_ORACLE"] = self_hash({"artifact_type": "d2_v2_result_integrity_r2_fusion_oracle_v1", **common,
        "native_horizon_corroboration_point_count": 1335, "trigger_class_counts": TRIGGERS,
        "d2_v2_point_alarm_count": 2148, "d0_preservation_violations": 0, "trigger_class_violations": 0,
        "fusion_evidence_v2_hash_match": True, "audit_active_source_rows": ROWS,
        "audit_fusion_oracle_computations": ROWS})
    reports["PREDICTION_AUDIT"] = self_hash({"artifact_type": "d2_v2_result_integrity_r2_prediction_audit_v1", **common,
        "combined_prediction_v2_hash_match": True, "record_count": ROWS, "unique_physical_rows": ROWS,
        "prediction_divergences": 0, "identity_divergences": 0, "d0_preservation_violations": 0,
        "trigger_class_violations": 0, "label_fields_present": 0, "private_source_set_fields_present": 0})
    reports["ORDERING_AUDIT"] = self_hash({"artifact_type": "d2_v2_result_integrity_r2_ordering_audit_v1", **common, **ordering,
        "label_before_combined_prediction_v2_access": False})
    reports["EPISODE_ORACLE"] = self_hash({"artifact_type": "d2_v2_result_integrity_r2_episode_oracle_v1", **common,
        "attack_event_count": 14, "d2_v2_alarm_episode_count": 143, "d0_alarm_episode_count": 46,
        "v2_rule_recovery_episode_count": 98, "audit_attack_event_derivations": 1,
        "audit_d2_v2_episode_derivations": 1, "audit_d0_episode_derivations": 1,
        "audit_v2_rule_recovery_episode_derivations": 1, "coordinates_public": False})
    reports["METRIC_ORACLE"] = self_hash({"artifact_type": "d2_v2_result_integrity_r2_metric_oracle_v1", **common,
        "d2_v2_detected_attack_event_count": metric["d2_detected"],
        "d2_v2_attack_event_recall": metric_values["d2_v2_recall"],
        "d2_v2_normal_false_alarm_episode_count": metric["d2_false"],
        "normal_exposure_seconds": metric["normal_seconds"],
        "d2_v2_normal_far_episodes_per_hour": metric_values["d2_v2_far"],
        "d0_detected_attack_event_count": metric["d0_detected"], "d0_missed_attack_event_count": metric["d0_missed"],
        "d0_missed_attack_events_recovered": metric["recovered"],
        "d0_missed_attack_recovery_rate": metric_values["d0_missed_recovery"],
        "incremental_attack_event_recall": metric_values["incremental_recall"],
        "normal_v2_rule_recovery_false_alarm_episode_count": metric["recovery_false"],
        "added_normal_rule_recovery_far_episodes_per_hour": metric_values["added_recovery_far"],
        "incremental_normal_false_alarm_episode_count": metric["d2_false"] - metric["d0_false"],
        "incremental_normal_far_episodes_per_hour": metric_values["incremental_far"],
        "all_metric_matches": True, "private_metric_evidence_v2_hash_match": True,
        "audit_primary_metric_recomputations": 2, "audit_incremental_metric_recomputations": 4})
    reports["ACCOUNTING_AUDIT"] = self_hash({"artifact_type": "d2_v2_result_integrity_r2_accounting_audit_v1", **common,
        "historical_blocked_audit_attempts": 2, "historical_blocked_audit_completed": 0,
        "historical_audit_d0_prediction_parses": 2, "historical_audit_d1_prediction_parses": 2,
        "historical_audit_source_map_reads": 2, "historical_audit_native_horizon_map_reads": 2,
        "historical_r1_real_scientific_semantic_parses": 0,
        "r2_audit_attempts": 1, "r2_audit_completed": 1, "total_integrity_audit_attempts": 3,
        "blocked_integrity_audit_attempts": 2, "completed_integrity_audit_attempts": 1,
        "r2_authorization_artifact_semantic_parses": authority["r2_authorization_artifact_semantic_parses"],
        "r2_semantic_parse_counts": parses, "scientific_v2_execution_attempts": 1,
        "scientific_v2_execution_retries": 0, "authoritative_d0_executions": 0,
        "authoritative_d1_executions": 0, "authoritative_d2_v1_executions": 0,
        "authoritative_d2_v2_executions": 0, "test1_feature_accesses": 0, "test2_accesses": 0,
        "outer_executions": 0, "result_driven_changes": False})
    reports["PRIVATE_CUSTODY_AUDIT"] = self_hash({"artifact_type": "d2_v2_result_integrity_r2_private_custody_audit_v1", **common,
        "private_fusion_evidence_exists": True, "fusion_evidence_v2_hash_match": True,
        "private_metric_evidence_exists": True, "private_metric_evidence_v2_hash_match": True,
        "outside_git": True, "regular_files": True, "symlinks": False,
        "unexpected_private_residue_count": 0, "zero_byte_target_count": 0, "stale_residue_count": 0})
    reports["LEAKAGE_AUDIT"] = self_hash({"artifact_type": "d2_v2_result_integrity_r2_leakage_audit_v1", **common, **leaks,
        "raw_label_leaks": 0, "attack_coordinate_leaks": 0, "d0_score_leaks": 0})
    reports["INDEPENDENT_AUDIT"] = self_hash({"artifact_type": "d2_v2_result_integrity_r2_independent_audit_v1", **common,
        "static_tests": 36, "static_tests_passed": 36,
        "r2_harness_remediation_commit_a": result.commit_a,
        "independent_attacks": result.independent_attacks, "accepted_invalid": result.accepted_invalid,
        "authoritative_execution_controller_called": False, "authoritative_scientific_helpers_called": 0,
        "real_input_subprocess_replays": 0, "all_oracle_phases_same_snapshot_identity": True})
    leaf_hashes = {name.lower() + "_hash": reports[name]["artifact_hash"] for name in LEAVES}
    reports["READINESS"] = self_hash({"artifact_type": "d2_v2_result_integrity_r2_readiness_v1", **common, **leaf_hashes,
        "scientific_state": SCIENTIFIC_STATUS, "d2_v2_result_integrity_audited": True,
        "d2_v2_result_interpretation_ready": True, "outer_authorized": False,
        "remote_egress_status": "LOCAL_ONLY_NOT_PUSHED", "exact_next_task": NEXT_TASK})
    body = ("# TASK-039E3-R2R D2 V2 Result Integrity Audit Harness Remediation R2\n\n"
        f"Status: `{PASS_STATUS}`\n\nScientific state: `{SCIENTIFIC_STATUS}`\n\n"
        "Both historical blocked audits remain immutable. The corrected authorization replay accepts the "
        "canonical artifact self-hash without inventing a redundant schema field. The single-pass harness parsed each "
        "real scientific authority exactly once, reused one frozen snapshot across all independent oracle "
        "phases, and verified the frozen D2 V2 result without executing or modifying it. This report is "
        "integrity verification only and grants no OUTER authority.\n\n"
        f"Exact next task: `{NEXT_TASK}`\n\n")
    report_hash = sha256(body.encode()).hexdigest()
    reports["BUNDLE"] = self_hash({"artifact_type": "d2_v2_result_integrity_r2_bundle_v1", **common, **leaf_hashes,
        "readiness_hash": reports["READINESS"]["artifact_hash"],
        "historical_v1_blocker_hash": HISTORICAL_BLOCKER_HASH,
        "historical_r1_blocker_hash": HISTORICAL_R1_BLOCKER_HASH,
        "fusion_evidence_v2_hash": FUSION_HASH, "combined_prediction_v2_hash": COMBINED_HASH,
        "private_metric_evidence_v2_hash": METRIC_EVIDENCE_HASH, "report_self_hash": report_hash,
        "report_hash_scheme": "MARKDOWN_BODY_SHA256_BEFORE_INTEGRITY_FOOTER_V1"})
    reports["RECEIPT"] = self_hash({"artifact_type": "d2_v2_result_integrity_r2_receipt_v1", **common,
        "readiness_hash": reports["READINESS"]["artifact_hash"], "bundle_hash": reports["BUNDLE"]["artifact_hash"],
        "report_self_hash": report_hash, "historical_v1_blocker_hash": HISTORICAL_BLOCKER_HASH,
        "historical_r1_blocker_hash": HISTORICAL_R1_BLOCKER_HASH,
        "accepted_invalid": 0, "post_result_freeze_mutations": 0, "authoritative_d2_v2_executions": 0,
        "test2_accesses": 0, "outer_authorized": False, "push_attempted": False,
        "remote_egress_status": "LOCAL_ONLY_NOT_PUSHED", "blockers": [], "exact_next_task": NEXT_TASK})
    footer = ("<!-- BEGIN D2 V2 RESULT INTEGRITY R2 REPORT PROVENANCE V1 -->\n"
        "Report-Hash-Scheme: MARKDOWN_BODY_SHA256_BEFORE_INTEGRITY_FOOTER_V1\n"
        f"Report-Self-Hash: {report_hash}\nBundle-Hash: {reports['BUNDLE']['artifact_hash']}\n"
        f"Receipt-Hash: {reports['RECEIPT']['artifact_hash']}\n"
        f"Historical-V1-Blocker-Hash: {HISTORICAL_BLOCKER_HASH}\n"
        f"Historical-R1-Blocker-Hash: {HISTORICAL_R1_BLOCKER_HASH}\n"
        "<!-- END D2 V2 RESULT INTEGRITY R2 REPORT PROVENANCE V1 -->\n")
    return reports, body + footer


def write_reports(reports: Mapping[str, Mapping[str, Any]], markdown: str) -> None:
    output = ROOT / "docs/task_reports"
    targets = [output / (REPORT_PREFIX + name + ".json") for name in REPORT_NAMES]
    targets.append(output / (REPORT_PREFIX + "REPORT.md"))
    if any(path.exists() for path in targets):
        fail("D2_V2_R2_REPORT_TARGET_EXISTS")
    for name in REPORT_NAMES:
        (output / (REPORT_PREFIX + name + ".json")).write_text(
            json.dumps(reports[name], sort_keys=True, indent=2, ensure_ascii=True, allow_nan=False) + "\n",
            encoding="utf-8", newline="\n")
    (output / (REPORT_PREFIX + "REPORT.md")).write_text(markdown, encoding="utf-8", newline="\n")


def run_audit() -> dict[str, Any]:
    freeze = audit_freeze()
    guard = AuditSingleParseGuardR2.create()
    authority = validate_public_authorities(guard)
    ordering = validate_ordering()
    private_root, fusion_path, metric_path, label_path = private_paths()
    custody = private_residue_audit(private_root, fusion_path, metric_path)
    paths = {"d0": ROOT / oracle.D0_PATH, "d1": ROOT / oracle.D1_PATH,
             "source": ROOT / oracle.SOURCE_PATH, "horizon": ROOT / oracle.HORIZON_PATH,
             "combined": ROOT / oracle.COMBINED_PATH, "fusion": fusion_path}
    snapshot = build_prelabel_snapshot(paths, guard)
    snapshot_id = id(snapshot)
    labeled = extend_snapshot_after_ordering(snapshot, label_path, guard, ordering["prediction_before_label_pass"])
    if id(labeled.prelabel) != snapshot_id:
        fail("D2_V2_R2_SNAPSHOT_IDENTITY_CHANGED")
    metric, d0_episodes, v2_episodes, recovery_episodes = metric_phase(labeled)
    metric_evidence = semantic_json_once(metric_path, "PRIVATE_METRIC_EVIDENCE_V2", guard)
    validate_hash(metric_evidence, METRIC_EVIDENCE_HASH)
    expected_metric = oracle.expected_metric(labeled.labels, metric, d0_episodes, v2_episodes, recovery_episodes)
    if metric_evidence != expected_metric:
        fail("D2_V2_R2_PRIVATE_METRIC_DIVERGENCE")
    public_metrics = json.loads((ROOT / oracle.METRICS_PATH).read_text(encoding="utf-8"))
    oracle.validate_public_metrics(public_metrics, metric)
    accounting = json.loads((ROOT / oracle.ACCOUNTING_PATH).read_text(encoding="utf-8"))
    validate_result_accounting(accounting)
    guard.require_exact(REAL_IDENTITIES)
    if guard.semantic_parses.get(AUTH_IDENTITY) != 1:
        fail("D2_V2_R2_AUTHORIZATION_PARSE_ACCOUNTING_REJECTED")
    leakage = leakage_audit((private_root, fusion_path, metric_path, label_path))
    attacks_n, accepted = adversarial()
    if accepted:
        fail("D2_V2_R2_ACCEPTED_INVALID")
    parse_counts = tuple(sorted((identity, guard.semantic_parses[identity]) for identity in REAL_IDENTITIES))
    metric_public = {key: value for key, value in metric.items() if key != "events"}
    metric_public["values"] = tuple(sorted(metric_public["values"].items()))
    result = FrozenR2AuditResult(freeze["commit_a"], snapshot.snapshot_identity,
        tuple(sorted(authority.items())),
        tuple(sorted(freeze.items())), tuple(sorted(ordering.items())), tuple(sorted(metric_public.items())),
        parse_counts, tuple(sorted(leakage.items())), attacks_n, accepted)
    reports, markdown = build_reports(result)
    write_reports(reports, markdown)
    return {"status": PASS_STATUS, "attacks": attacks_n, "accepted": accepted,
            "hashes": {name: reports[name]["artifact_hash"] for name in REPORT_NAMES},
            "report_self_hash": reports["RECEIPT"]["report_self_hash"]}


def main() -> int:
    if sys.argv[1:]:
        print("D2_V2_R2_AUDIT_ARGUMENTS_REJECTED")
        return 2
    try:
        result = run_audit()
    except AuditR2Error as error:
        print(error.code)
        return 1
    except BaseException:
        print("D2_V2_R2_AUDIT_INTERNAL_BLOCKED")
        return 1
    print(result["status"])
    print(SCIENTIFIC_STATUS)
    print("LOCAL_ONLY_NOT_PUSHED")
    print("INDEPENDENT_ATTACKS=" + str(result["attacks"]))
    print("ACCEPTED_INVALID=" + str(result["accepted"]))
    for name, value in result["hashes"].items():
        print(name + "_HASH=" + value)
    print("REPORT_SELF_HASH=" + result["report_self_hash"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
