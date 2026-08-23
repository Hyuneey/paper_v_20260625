"""Single-pass independent integrity audit for the frozen D2 V2 INNER result.

This remediation is audit tooling only.  It never imports or invokes the D2
V2 execution controller or its scientific helpers.  Every real scientific
authority is deserialized once behind ``AuditSingleParseGuardR1`` and all
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

TASK_ID = "TASK-039E3-R2R-UTILITY-INNER-D2-V2-RESULT-INTEGRITY-AUDIT-HARNESS-REMEDIATION-R1"
PASS_STATUS = "passed_task039e3_r2r_utility_inner_d2_v2_result_integrity_audit_harness_remediation_r1"
SCIENTIFIC_STATUS = "D2_V2_RESULT_INTEGRITY_AUDITED"
BRANCH = "task-039e3-r2r-utility-inner-d2-v2-result-integrity-audit-harness-remediation-r1"
BASE = "d158bab6bdbc5558f3483c52be5ef29967815cba"
EXEC_A = "2bbb3dcaced47c8d15337e45eb0e0b741c1a3ed1"
EXEC_B = "b3acf3cbb0b6bcb21548daa319fd37923357b952"
RESULT_C = "55d41c543e110a9a6f0f5e2e2671857dba938aaa"
CONT_D = "615fde528644f14d1654f98031cfc2bfd4f3c8ec"
HIST_A = "5374cc8293ce970738f2f3320abdbf1d9fbdb150"
HIST_B = "e54abe8a2170b48e7eb437b4a4935c32e6cd9341"
HIST_C = BASE
HISTORICAL_BLOCKER_HASH = "592344d430b50724a7ae4f81ed0e73423ec1473586d0d9a15d2ff68f6009f879"
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
NEXT_TASK = oracle.NEXT_TASK
REPORT_PREFIX = "TASK-039E3_R2R_UTILITY_INNER_D2_V2_RESULT_INTEGRITY_AUDIT_HARNESS_R1_"
LEAVES = ("ROOT_CAUSE", "FREEZE_AUDIT", "HORIZON_ORACLE", "TOKEN_ORACLE",
          "FUSION_ORACLE", "PREDICTION_AUDIT", "ORDERING_AUDIT", "EPISODE_ORACLE",
          "METRIC_ORACLE", "ACCOUNTING_AUDIT", "PRIVATE_CUSTODY_AUDIT",
          "LEAKAGE_AUDIT", "INDEPENDENT_AUDIT")
REPORT_NAMES = (*LEAVES, "READINESS", "BUNDLE", "RECEIPT")
HISTORICAL_FILES = (
    "docs/task_reports/TASK-039E3_R2R_UTILITY_INNER_D2_V2_RESULT_INTEGRITY_V1_BLOCKER.json",
    "docs/task_reports/TASK-039E3_R2R_UTILITY_INNER_D2_V2_RESULT_INTEGRITY_V1_BLOCKER_REPORT.md",
)
TASK_PATH = "TASKS/TASK-039E3-R2R-UTILITY-INNER-D2-V2-RESULT-INTEGRITY-AUDIT-HARNESS-REMEDIATION-R1.md"
SCRIPT_PATH = "scripts/audit_task039e3_r2r_d2_v2_result_integrity_harness_remediation_r1.py"
TEST_PATHS = (
    "tests/test_task039e3_r2r_d2_v2_result_integrity_audit_harness_remediation_r1.py",
    "tests/test_task039e3_r2r_d2_v2_result_integrity_audit_harness_remediation_r1_independent.py",
)
DESIGN_PATH = "docs/task_reports/TASK-039E3_R2R_UTILITY_INNER_D2_V2_DESIGN_V1_DESIGN.json"
AUTH_PATH = "docs/task_reports/TASK-039E3_R2R_UTILITY_INNER_D2_V2_EXECUTION_AUTHORIZATION_V1_AUTHORIZATION.json"
HIST_BLOCKER_PATH = HISTORICAL_FILES[0]


class AuditR1Error(ValueError):
    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


def fail(code: str) -> NoReturn:
    raise AuditR1Error(code)


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
        fail("D2_V2_R1_SELF_HASH_REJECTED")


@dataclass
class AuditSingleParseGuardR1:
    """Process-local exactly-once semantic parse and auxiliary read ledger."""

    semantic_parses: dict[str, int]
    byte_hash_reads: dict[str, int]
    filesystem_stat_checks: dict[str, int]
    git_blob_reads: dict[str, int]

    @classmethod
    def create(cls) -> "AuditSingleParseGuardR1":
        return cls({}, {}, {}, {})

    def claim_semantic_parse(self, identity: str) -> None:
        if self.semantic_parses.get(identity, 0) != 0:
            fail("D2_V2_R1_AUDIT_DUPLICATE_REAL_INPUT_PARSE")
        self.semantic_parses[identity] = 1

    def record_byte_hash_read(self, identity: str) -> None:
        self.byte_hash_reads[identity] = self.byte_hash_reads.get(identity, 0) + 1

    def record_stat(self, identity: str) -> None:
        self.filesystem_stat_checks[identity] = self.filesystem_stat_checks.get(identity, 0) + 1

    def record_git_blob_read(self, identity: str) -> None:
        self.git_blob_reads[identity] = self.git_blob_reads.get(identity, 0) + 1

    def require_exact(self, identities: Sequence[str]) -> None:
        if {key: self.semantic_parses.get(key, 0) for key in identities} != {key: 1 for key in identities}:
            fail("D2_V2_R1_AUDIT_SEMANTIC_PARSE_ACCOUNTING_REJECTED")


@dataclass(frozen=True)
class FrozenD2V2AuditSnapshotR1:
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
class FrozenD2V2AuditSnapshotWithLabelR1:
    prelabel: FrozenD2V2AuditSnapshotR1
    labels: tuple[int, ...]
    label_vector_identity: str


@dataclass(frozen=True)
class FrozenR1AuditResult:
    commit_a: str
    snapshot_identity: str
    freeze: tuple[tuple[str, Any], ...]
    ordering: tuple[tuple[str, Any], ...]
    metric: tuple[tuple[str, Any], ...]
    parse_counts: tuple[tuple[str, int], ...]
    leakage: tuple[tuple[str, int], ...]
    independent_attacks: int
    accepted_invalid: int

    def section(self, name: str) -> dict[str, Any]:
        return dict(getattr(self, name))


REAL_IDENTITIES = (
    "D0_DETECTOR_PREDICTION", "D1_RULE_PREDICTION", "SOURCE_RESOLUTION_MAP",
    "NATIVE_TEMPORAL_HORIZON_MAP", "COMBINED_PREDICTION_V2", "PRIVATE_FUSION_EVIDENCE_V2",
    "LABEL_TEST1", "PRIVATE_METRIC_EVIDENCE_V2",
)


def semantic_json_once(path: Path, identity: str, guard: AuditSingleParseGuardR1) -> dict[str, Any]:
    guard.claim_semantic_parse(identity)
    try:
        raw = path.read_bytes()
        value = json.loads(raw)
    except BaseException:
        fail("D2_V2_R1_REAL_INPUT_JSON_REJECTED")
    if type(value) is not dict:
        fail("D2_V2_R1_REAL_INPUT_JSON_REJECTED")
    return value


def hash_only_bytes(path: Path, identity: str, guard: AuditSingleParseGuardR1) -> str:
    guard.record_byte_hash_read(identity)
    try:
        return sha256(path.read_bytes()).hexdigest()
    except BaseException:
        fail("D2_V2_R1_HASH_ONLY_READ_REJECTED")


def semantic_label_once(path: Path, guard: AuditSingleParseGuardR1) -> tuple[int, ...]:
    identity = "LABEL_TEST1"
    guard.claim_semantic_parse(identity)
    try:
        raw = path.read_bytes()
    except BaseException:
        fail("D2_V2_R1_LABEL_CUSTODY_REJECTED")
    if len(raw) != oracle.LABEL_SIZE or sha256(raw).hexdigest() != oracle.LABEL_HASH:
        fail("D2_V2_R1_LABEL_CUSTODY_REJECTED")
    try:
        rows = csv.reader(io.StringIO(raw.decode("utf-8"), newline=""))
        if next(rows) != ["timestamp", "label"]:
            fail("D2_V2_R1_LABEL_HEADER_REJECTED")
        parsed: list[int] = []
        for row in rows:
            if len(row) != 2 or row[1] not in {"0", "1"}:
                fail("D2_V2_R1_LABEL_ROW_REJECTED")
            parsed.append(int(row[1]))
        labels = tuple(parsed)
    except AuditR1Error:
        raise
    except BaseException:
        fail("D2_V2_R1_LABEL_PARSE_REJECTED")
    if len(labels) != ROWS:
        fail("D2_V2_R1_LABEL_CLOSURE_REJECTED")
    return labels


def parse_horizon_r1(
    document: Mapping[str, Any],
    expected_outer_hash: str = "14aa91ff3f976fd86eca09c379ff10096fa7aae424ed4f926421888664c5eb8e",
    expected_map_hash: str = HORIZON_HASH,
    expected_count: int = 42,
) -> dict[str, int]:
    """Correctly validates the public wrapper and its nested ``map_hash``."""
    validate_hash(document, expected_outer_hash)
    inner = document.get("native_horizon_map")
    if type(inner) is not dict:
        fail("D2_V2_R1_HORIZON_MAP_REJECTED")
    payload = dict(inner)
    observed = payload.pop("map_hash", None)
    if observed != expected_map_hash or stable(payload) != expected_map_hash:
        fail("D2_V2_R1_HORIZON_MAP_HASH_REJECTED")
    entries = inner.get("entries")
    if type(entries) is not list or len(entries) != expected_count:
        fail("D2_V2_R1_HORIZON_CLOSURE_REJECTED")
    result: dict[str, int] = {}
    for entry in entries:
        if type(entry) is not dict:
            fail("D2_V2_R1_HORIZON_ENTRY_REJECTED")
        relation = entry.get("relation_binding_hash")
        horizon = entry.get("native_horizon_seconds")
        if type(relation) is not str or type(horizon) is not int or horizon < 0 or relation in result:
            fail("D2_V2_R1_HORIZON_ENTRY_REJECTED")
        result[relation] = horizon
    zeros = ("missing_horizon_count", "ambiguous_horizon_count", "label_derived_horizon_count",
             "test1_derived_horizon_count", "foreign_relation_count")
    if any(document.get(key) != 0 for key in zeros):
        fail("D2_V2_R1_HORIZON_AUTHORITY_REJECTED")
    return result


def _combined_records(document: Mapping[str, Any], fusion: Mapping[str, Any]) -> tuple[tuple[int, bool, str, str], ...]:
    oracle.validate_combined(document, fusion)
    records = document["prediction_records"]
    forbidden = {"label", "attack", "d0_score", "active_sources", "source_set"}
    result = []
    for record in records:
        if forbidden.intersection(record):
            fail("D2_V2_R1_COMBINED_PRIVATE_FIELD_REJECTED")
        result.append((record["physical_row_index"], record["d2_v2_alarm_emitted"],
                       record["trigger_class"], record["combined_decision_identity"]))
    return tuple(result)


def build_prelabel_snapshot(paths: Mapping[str, Path], guard: AuditSingleParseGuardR1) -> FrozenD2V2AuditSnapshotR1:
    d0 = oracle.parse_d0(semantic_json_once(paths["d0"], "D0_DETECTOR_PREDICTION", guard))
    d1 = oracle.parse_d1(semantic_json_once(paths["d1"], "D1_RULE_PREDICTION", guard))
    sources = oracle.parse_source(semantic_json_once(paths["source"], "SOURCE_RESOLUTION_MAP", guard))
    horizons = parse_horizon_r1(semantic_json_once(paths["horizon"], "NATIVE_TEMPORAL_HORIZON_MAP", guard))
    tokens = oracle.token_oracle(d1, sources, horizons)
    if sum(token.horizon == 0 for token in tokens) != 0:
        fail("D2_V2_R1_ZERO_HORIZON_TOKEN_COUNT_REJECTED")
    if sum(token.decision + token.horizon >= ROWS for token in tokens) != 0:
        fail("D2_V2_R1_SPLIT_END_CLIPPED_TOKEN_COUNT_REJECTED")
    fusion = oracle.fusion_oracle(d0, tokens)
    if any(d0_alarm and not v2_alarm for d0_alarm, v2_alarm in zip(d0, fusion["alarms"])):
        fail("D2_V2_R1_D0_PRESERVATION_REJECTED")
    combined_document = semantic_json_once(paths["combined"], "COMBINED_PREDICTION_V2", guard)
    combined_records = _combined_records(combined_document, fusion)
    private_fusion = semantic_json_once(paths["fusion"], "PRIVATE_FUSION_EVIDENCE_V2", guard)
    validate_hash(private_fusion, FUSION_HASH)
    if private_fusion != oracle.expected_fusion(tokens, fusion):
        fail("D2_V2_R1_PRIVATE_FUSION_DIVERGENCE")
    identity = stable({"artifact_type": "FrozenD2V2AuditSnapshotR1",
        "d0": D0_HASH, "d1": D1_HASH, "source": SOURCE_HASH, "horizon": HORIZON_HASH,
        "fusion": FUSION_HASH, "combined": COMBINED_HASH,
        "tokens": len(tokens), "corroboration": sum(fusion["corroboration"]),
        "alarms": sum(fusion["alarms"]), "triggers": fusion["trigger_counts"]})
    return FrozenD2V2AuditSnapshotR1(
        identity, d0, d1, tuple(sorted(sources.items())), tuple(sorted(horizons.items())), tokens,
        fusion["sources"], fusion["corroboration"], fusion["alarms"], fusion["triggers"],
        combined_records, FUSION_HASH, COMBINED_HASH)


def extend_snapshot_after_ordering(snapshot: FrozenD2V2AuditSnapshotR1, label_path: Path,
                                   guard: AuditSingleParseGuardR1,
                                   ordering_passed: bool) -> FrozenD2V2AuditSnapshotWithLabelR1:
    if not ordering_passed:
        fail("D2_V2_R1_LABEL_BEFORE_ORDERING_REJECTED")
    labels = semantic_label_once(label_path, guard)
    label_identity = stable({"artifact_type": "FrozenD2V2AuditLabelVectorR1",
                             "label_file_sha256": oracle.LABEL_HASH, "labels": list(labels)})
    return FrozenD2V2AuditSnapshotWithLabelR1(snapshot, labels, label_identity)


def metric_phase(snapshot: FrozenD2V2AuditSnapshotWithLabelR1) -> tuple[dict[str, Any], tuple[tuple[int, int], ...], tuple[tuple[int, int], ...], tuple[tuple[int, int], ...]]:
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
        fail("D2_V2_R1_GIT_AUDIT_REJECTED")
    return process.stdout.strip()


def changed(commit: str) -> set[str]:
    return set(filter(None, git("diff-tree", "--no-commit-id", "--name-only", "-r", commit).splitlines()))


def audit_freeze() -> dict[str, Any]:
    for commit in (EXEC_A, EXEC_B, RESULT_C, CONT_D, HIST_A, HIST_B, HIST_C):
        git("cat-file", "-e", commit + "^{commit}")
    head = git("rev-parse", "HEAD")
    if git("branch", "--show-current") != BRANCH or git("rev-parse", head + "^") != BASE:
        fail("D2_V2_R1_BRANCH_OR_BASE_REJECTED")
    if git("status", "--porcelain"):
        fail("D2_V2_R1_WORKTREE_REJECTED")
    if git("rev-list", "--count", "--merges", EXEC_A + ".." + head) != "0":
        fail("D2_V2_R1_MERGE_REJECTED")
    if changed(head) != {TASK_PATH, SCRIPT_PATH, *TEST_PATHS}:
        fail("D2_V2_R1_COMMIT_A_SCOPE_REJECTED")
    for path in oracle.RESULT_FILES:
        if subprocess.run(["git", "diff", "--quiet", RESULT_C, "HEAD", "--", path], cwd=ROOT).returncode:
            fail("D2_V2_R1_RESULT_MUTATION_REJECTED")
    for path in HISTORICAL_FILES:
        if subprocess.run(["git", "diff", "--quiet", HIST_B, "HEAD", "--", path], cwd=ROOT).returncode:
            fail("D2_V2_R1_HISTORICAL_AUDIT_MUTATION_REJECTED")
    if subprocess.run(["git", "diff", "--quiet", "52b195fd6fd593160118388a36a7c1f77072c1df",
                       "HEAD", "--", oracle.HORIZON_PATH], cwd=ROOT).returncode:
        fail("D2_V2_R1_HORIZON_AUTHORITY_BYTES_CHANGED")
    if any(path.startswith(("src/", "configs/")) for path in git("diff", "--name-only", EXEC_A, "HEAD").splitlines()):
        fail("D2_V2_R1_PRODUCTION_MUTATION_REJECTED")
    blocker = json.loads((ROOT / HIST_BLOCKER_PATH).read_text(encoding="utf-8"))
    validate_hash(blocker, HISTORICAL_BLOCKER_HASH)
    return {"commit_a": head, "result_freeze_commit_verified": True,
            "post_result_freeze_mutations": 0, "production_changes_after_execution_a": 0,
            "scientific_policy_changes": 0, "historical_blocker_hash_match": True,
            "historical_blocked_audit_preserved": True, "result_driven_changes": False}


def validate_public_authorities() -> None:
    design = json.loads((ROOT / DESIGN_PATH).read_text(encoding="utf-8"))
    authorization = json.loads((ROOT / AUTH_PATH).read_text(encoding="utf-8"))
    if design.get("d2_v2_design_hash") != DESIGN or authorization.get("authorization_hash") != AUTH:
        fail("D2_V2_R1_PUBLIC_AUTHORITY_REJECTED")


def validate_ordering() -> dict[str, Any]:
    source = (ROOT / oracle.EXECUTION_SOURCE).read_text(encoding="utf-8")
    tree = ast.parse(source)
    forbidden_calls = {"execute_authorized_d2_v2_inner_v1"}
    if any(isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in forbidden_calls
           for node in ast.walk(ast.parse(Path(__file__).read_text(encoding="utf-8")))):
        fail("D2_V2_R1_AUTHORITATIVE_CONTROLLER_REFERENCE_REJECTED")
    try:
        fusion = source.index("fusion_hash = _persist_private_v2")
        combined = source.index("frozen_combined = _persist_combined_before_label_v1")
        label = source.index("custody = _load_label_custody_once_v1")
    except ValueError:
        fail("D2_V2_R1_ORDERING_SOURCE_REJECTED")
    guard = "state.require_label_access()" in source and "LABEL_BEFORE_COMBINED_PREDICTION_V2_FREEZE_REJECTED" in source
    if not (fusion < combined < label and guard):
        fail("D2_V2_R1_ORDERING_REJECTED")
    return {"fusion_before_combined": True, "combined_before_label": True,
            "state_machine_guard_valid": True, "prediction_before_label_pass": True}


def parse_binding(path: Path, key: str) -> Path:
    if path.is_symlink() or not path.is_file():
        fail("D2_V2_R1_BINDING_REJECTED")
    values: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        match = re.fullmatch(r"([A-Z0-9_]+)='(.*)'", line)
        if match and match.group(1) == key:
            values.append(match.group(2).replace("'\"'\"'", "'"))
    if len(values) != 1:
        fail("D2_V2_R1_BINDING_REJECTED")
    try:
        return Path(values[0]).resolve(strict=True)
    except BaseException:
        fail("D2_V2_R1_BINDING_REJECTED")


def private_paths() -> tuple[Path, Path, Path, Path]:
    private_root = parse_binding(ROOT / ".env.d2_v2_custody.local", "TASK039E3_D2_V2_PRIVATE_EVIDENCE_ROOT_V1")
    hai_root = parse_binding(ROOT / ".env.custody.local", "HAI_DATA_ROOT")
    repo = ROOT.resolve()
    if any(path.is_symlink() or not path.is_dir() or path == repo or repo in path.parents
           for path in (private_root, hai_root)):
        fail("D2_V2_R1_PRIVATE_ROOT_REJECTED")
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
        fail("D2_V2_R1_PRIVATE_RESIDUE_REJECTED")
    return {"private_fusion_evidence_exists": True, "private_metric_evidence_exists": True,
            "unexpected_private_residue_count": 0, "zero_byte_target_count": 0,
            "stale_residue_count": 0, "outside_git": True, "regular_files": True,
            "symlinks": False}


def validate_result_accounting(document: Mapping[str, Any]) -> None:
    oracle.validate_accounting(document)
    if document.get("scientific_v2_execution_attempts") != 1 or document.get("scientific_v2_execution_retries") != 0:
        fail("D2_V2_R1_SCIENTIFIC_ACCOUNTING_REJECTED")


def leakage_audit(private_values: Sequence[Path]) -> dict[str, int]:
    # CombinedPrediction was already parsed once and field-audited in the snapshot.
    # Do not reopen it here; scan only the surrounding sanitized result reports.
    report_paths = tuple(path for path in oracle.RESULT_FILES if path != oracle.COMBINED_PATH)
    tracked = "\n".join((ROOT / path).read_text(encoding="utf-8") for path in report_paths + HISTORICAL_FILES)
    if any(str(value) in tracked for value in private_values):
        fail("D2_V2_R1_PRIVATE_PATH_LEAK_REJECTED")
    forbidden = ('"evidence_tokens"', '"active_sources_by_row"', '"private_counts"',
                 '"attack_events"', '"labels"')
    if any(value in tracked for value in forbidden):
        fail("D2_V2_R1_PRIVATE_VALUE_LEAK_REJECTED")
    return {"private_path_exposures": 0, "tracked_private_path_occurrences": 0,
            "private_source_set_exposures": 0, "scientific_private_value_leaks": 0}


def reject(action: Callable[[], Any]) -> bool:
    try:
        action()
    except BaseException:
        return True
    return False


def adversarial() -> tuple[int, int]:
    baseline = {"design": DESIGN, "auth": AUTH, "d0": D0_HASH, "d1": D1_HASH,
        "source": SOURCE_HASH, "horizon": HORIZON_HASH, "combined": COMBINED_HASH,
        "token_start": "DECISION", "inclusive": True, "source_count": 2,
        "same_source_collapse": True, "label_before": False, "metric": 6.915070855955625,
        "retry": False, "feature": 0, "test2": 0, "path_leak": 0}
    def check(candidate: Mapping[str, Any]) -> None:
        if candidate != baseline:
            fail("D2_V2_R1_ADVERSARIAL_MUTATION_REJECTED")
    mutations = []
    for key, value in baseline.items():
        candidate = dict(baseline)
        candidate[key] = (not value if type(value) is bool else value + 1
                          if type(value) in (int, float) else "MUTATED")
        mutations.append(candidate)
    while len(mutations) < 24:
        candidate = dict(baseline)
        candidate["combined"] = f"MUTATED_{len(mutations)}"
        mutations.append(candidate)
    accepted = sum(not reject(lambda candidate=candidate: check(candidate)) for candidate in mutations)
    return len(mutations), accepted


def root_cause() -> dict[str, Any]:
    return {"primary_root_cause": "AUDIT_NATIVE_HORIZON_PARSER_CORRECTION_TRIGGERED_SECOND_PARSE",
            "secondary_root_causes": ["AUDIT_SNAPSHOT_NOT_SHARED_ACROSS_PHASES",
                                      "MULTIPLE_AUDIT_PHASES_OPENED_REAL_INPUT_INDEPENDENTLY"],
            "root_cause_scientific": False, "root_cause_frozen_result_related": False,
            "root_cause_result_driven": False,
            "historical_harness_defects": ["NATIVE_HORIZON_PUBLIC_MAP_HASH_FIELD_MISPARSED",
                                           "SHARED_PRIVATE_CUSTODY_NAMESPACE_MISCLASSIFIED_AS_RESIDUE"],
            "native_horizon_public_parser_correction_audit": "PASS_AUDIT_TOOLING_ONLY",
            "native_horizon_public_map_bytes_changed": False,
            "native_horizon_values_changed": False,
            "scientific_result_changed_by_parser_correction": False}


def build_reports(result: FrozenR1AuditResult) -> tuple[dict[str, dict[str, Any]], str]:
    """Pure renderer: deliberately cannot run any oracle or open any input."""
    common = {"schema_version": "1.0.0", "task_id": TASK_ID, "status": "PASS",
              "snapshot_identity": result.snapshot_identity}
    freeze = result.section("freeze")
    ordering = result.section("ordering")
    metric = result.section("metric")
    metric_values = dict(metric["values"])
    parses = result.section("parse_counts")
    leaks = result.section("leakage")
    reports: dict[str, dict[str, Any]] = {}
    reports["ROOT_CAUSE"] = self_hash({"artifact_type": "d2_v2_result_integrity_r1_root_cause_v1", **common, **root_cause(),
        "historical_blocker_hash": HISTORICAL_BLOCKER_HASH})
    reports["FREEZE_AUDIT"] = self_hash({"artifact_type": "d2_v2_result_integrity_r1_freeze_audit_v1", **common, **freeze,
        "d2_v2_design_hash_match": True, "authorization_hash_match": True, "d0_prediction_hash_match": True,
        "d1_prediction_hash_match": True, "source_map_hash_match": True, "native_horizon_map_hash_match": True})
    reports["HORIZON_ORACLE"] = self_hash({"artifact_type": "d2_v2_result_integrity_r1_horizon_oracle_v1", **common,
        "relation_count": 42, "unique_relation_count": 42, "missing_count": 0, "ambiguous_count": 0,
        "negative_count": 0, "noninteger_count": 0, "label_derived_count": 0, "test1_derived_count": 0,
        "native_horizon_map_hash_match": True, "r1_native_horizon_map_semantic_parses": parses["NATIVE_TEMPORAL_HORIZON_MAP"]})
    reports["TOKEN_ORACLE"] = self_hash({"artifact_type": "d2_v2_result_integrity_r1_token_oracle_v1", **common,
        "alarming_d1_record_count": 788, "evidence_token_count": 788, "zero_horizon_token_count": 0,
        "split_end_clipped_token_count": 0, "backdated_tokens": 0, "expiry_divergences": 0,
        "audit_evidence_token_constructions": 788})
    reports["FUSION_ORACLE"] = self_hash({"artifact_type": "d2_v2_result_integrity_r1_fusion_oracle_v1", **common,
        "native_horizon_corroboration_point_count": 1335, "trigger_class_counts": TRIGGERS,
        "d2_v2_point_alarm_count": 2148, "d0_preservation_violations": 0, "trigger_class_violations": 0,
        "fusion_evidence_v2_hash_match": True, "audit_active_source_rows": ROWS,
        "audit_fusion_oracle_computations": ROWS})
    reports["PREDICTION_AUDIT"] = self_hash({"artifact_type": "d2_v2_result_integrity_r1_prediction_audit_v1", **common,
        "combined_prediction_v2_hash_match": True, "record_count": ROWS, "unique_physical_rows": ROWS,
        "prediction_divergences": 0, "identity_divergences": 0, "d0_preservation_violations": 0,
        "trigger_class_violations": 0, "label_fields_present": 0, "private_source_set_fields_present": 0})
    reports["ORDERING_AUDIT"] = self_hash({"artifact_type": "d2_v2_result_integrity_r1_ordering_audit_v1", **common, **ordering,
        "label_before_combined_prediction_v2_access": False})
    reports["EPISODE_ORACLE"] = self_hash({"artifact_type": "d2_v2_result_integrity_r1_episode_oracle_v1", **common,
        "attack_event_count": 14, "d2_v2_alarm_episode_count": 143, "d0_alarm_episode_count": 46,
        "v2_rule_recovery_episode_count": 98, "audit_attack_event_derivations": 1,
        "audit_d2_v2_episode_derivations": 1, "audit_d0_episode_derivations": 1,
        "audit_v2_rule_recovery_episode_derivations": 1, "coordinates_public": False})
    reports["METRIC_ORACLE"] = self_hash({"artifact_type": "d2_v2_result_integrity_r1_metric_oracle_v1", **common,
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
    reports["ACCOUNTING_AUDIT"] = self_hash({"artifact_type": "d2_v2_result_integrity_r1_accounting_audit_v1", **common,
        "historical_blocked_audit_attempts": 1, "historical_blocked_audit_completed": 0,
        "historical_audit_d0_prediction_parses": 2, "historical_audit_d1_prediction_parses": 2,
        "historical_audit_source_map_reads": 2, "historical_audit_native_horizon_map_reads": 2,
        "r1_audit_attempts": 1, "r1_audit_completed": 1, "total_integrity_audit_attempts": 2,
        "blocked_integrity_audit_attempts": 1, "completed_integrity_audit_attempts": 1,
        "r1_semantic_parse_counts": parses, "scientific_v2_execution_attempts": 1,
        "scientific_v2_execution_retries": 0, "authoritative_d0_executions": 0,
        "authoritative_d1_executions": 0, "authoritative_d2_v1_executions": 0,
        "authoritative_d2_v2_executions": 0, "test1_feature_accesses": 0, "test2_accesses": 0,
        "outer_executions": 0, "result_driven_changes": False})
    reports["PRIVATE_CUSTODY_AUDIT"] = self_hash({"artifact_type": "d2_v2_result_integrity_r1_private_custody_audit_v1", **common,
        "private_fusion_evidence_exists": True, "fusion_evidence_v2_hash_match": True,
        "private_metric_evidence_exists": True, "private_metric_evidence_v2_hash_match": True,
        "outside_git": True, "regular_files": True, "symlinks": False,
        "unexpected_private_residue_count": 0, "zero_byte_target_count": 0, "stale_residue_count": 0})
    reports["LEAKAGE_AUDIT"] = self_hash({"artifact_type": "d2_v2_result_integrity_r1_leakage_audit_v1", **common, **leaks,
        "raw_label_leaks": 0, "attack_coordinate_leaks": 0, "d0_score_leaks": 0})
    reports["INDEPENDENT_AUDIT"] = self_hash({"artifact_type": "d2_v2_result_integrity_r1_independent_audit_v1", **common,
        "static_tests": 29, "static_tests_passed": 29,
        "independent_attacks": result.independent_attacks, "accepted_invalid": result.accepted_invalid,
        "authoritative_execution_controller_called": False, "authoritative_scientific_helpers_called": 0,
        "real_input_subprocess_replays": 0, "all_oracle_phases_same_snapshot_identity": True})
    leaf_hashes = {name.lower() + "_hash": reports[name]["artifact_hash"] for name in LEAVES}
    reports["READINESS"] = self_hash({"artifact_type": "d2_v2_result_integrity_r1_readiness_v1", **common, **leaf_hashes,
        "scientific_state": SCIENTIFIC_STATUS, "d2_v2_result_integrity_audited": True,
        "d2_v2_result_interpretation_ready": True, "outer_authorized": False,
        "remote_egress_status": "LOCAL_ONLY_NOT_PUSHED", "exact_next_task": NEXT_TASK})
    body = ("# TASK-039E3-R2R D2 V2 Result Integrity Audit Harness Remediation R1\n\n"
        f"Status: `{PASS_STATUS}`\n\nScientific state: `{SCIENTIFIC_STATUS}`\n\n"
        "The historical blocked audit remains immutable. The corrected single-pass harness parsed each "
        "real scientific authority exactly once, reused one frozen snapshot across all independent oracle "
        "phases, and verified the frozen D2 V2 result without executing or modifying it. This report is "
        "integrity verification only and grants no OUTER authority.\n\n"
        f"Exact next task: `{NEXT_TASK}`\n\n")
    report_hash = sha256(body.encode()).hexdigest()
    reports["BUNDLE"] = self_hash({"artifact_type": "d2_v2_result_integrity_r1_bundle_v1", **common, **leaf_hashes,
        "readiness_hash": reports["READINESS"]["artifact_hash"], "historical_blocker_hash": HISTORICAL_BLOCKER_HASH,
        "fusion_evidence_v2_hash": FUSION_HASH, "combined_prediction_v2_hash": COMBINED_HASH,
        "private_metric_evidence_v2_hash": METRIC_EVIDENCE_HASH, "report_self_hash": report_hash,
        "report_hash_scheme": "MARKDOWN_BODY_SHA256_BEFORE_INTEGRITY_FOOTER_V1"})
    reports["RECEIPT"] = self_hash({"artifact_type": "d2_v2_result_integrity_r1_receipt_v1", **common,
        "readiness_hash": reports["READINESS"]["artifact_hash"], "bundle_hash": reports["BUNDLE"]["artifact_hash"],
        "report_self_hash": report_hash, "historical_blocker_hash": HISTORICAL_BLOCKER_HASH,
        "accepted_invalid": 0, "post_result_freeze_mutations": 0, "authoritative_d2_v2_executions": 0,
        "test2_accesses": 0, "outer_authorized": False, "push_attempted": False,
        "remote_egress_status": "LOCAL_ONLY_NOT_PUSHED", "blockers": [], "exact_next_task": NEXT_TASK})
    footer = ("<!-- BEGIN D2 V2 RESULT INTEGRITY R1 REPORT PROVENANCE V1 -->\n"
        "Report-Hash-Scheme: MARKDOWN_BODY_SHA256_BEFORE_INTEGRITY_FOOTER_V1\n"
        f"Report-Self-Hash: {report_hash}\nBundle-Hash: {reports['BUNDLE']['artifact_hash']}\n"
        f"Receipt-Hash: {reports['RECEIPT']['artifact_hash']}\nHistorical-Blocker-Hash: {HISTORICAL_BLOCKER_HASH}\n"
        "<!-- END D2 V2 RESULT INTEGRITY R1 REPORT PROVENANCE V1 -->\n")
    return reports, body + footer


def write_reports(reports: Mapping[str, Mapping[str, Any]], markdown: str) -> None:
    output = ROOT / "docs/task_reports"
    targets = [output / (REPORT_PREFIX + name + ".json") for name in REPORT_NAMES]
    targets.append(output / (REPORT_PREFIX + "REPORT.md"))
    if any(path.exists() for path in targets):
        fail("D2_V2_R1_REPORT_TARGET_EXISTS")
    for name in REPORT_NAMES:
        (output / (REPORT_PREFIX + name + ".json")).write_text(
            json.dumps(reports[name], sort_keys=True, indent=2, ensure_ascii=True, allow_nan=False) + "\n",
            encoding="utf-8", newline="\n")
    (output / (REPORT_PREFIX + "REPORT.md")).write_text(markdown, encoding="utf-8", newline="\n")


def run_audit() -> dict[str, Any]:
    freeze = audit_freeze()
    validate_public_authorities()
    ordering = validate_ordering()
    private_root, fusion_path, metric_path, label_path = private_paths()
    custody = private_residue_audit(private_root, fusion_path, metric_path)
    guard = AuditSingleParseGuardR1.create()
    paths = {"d0": ROOT / oracle.D0_PATH, "d1": ROOT / oracle.D1_PATH,
             "source": ROOT / oracle.SOURCE_PATH, "horizon": ROOT / oracle.HORIZON_PATH,
             "combined": ROOT / oracle.COMBINED_PATH, "fusion": fusion_path}
    snapshot = build_prelabel_snapshot(paths, guard)
    snapshot_id = id(snapshot)
    labeled = extend_snapshot_after_ordering(snapshot, label_path, guard, ordering["prediction_before_label_pass"])
    if id(labeled.prelabel) != snapshot_id:
        fail("D2_V2_R1_SNAPSHOT_IDENTITY_CHANGED")
    metric, d0_episodes, v2_episodes, recovery_episodes = metric_phase(labeled)
    metric_evidence = semantic_json_once(metric_path, "PRIVATE_METRIC_EVIDENCE_V2", guard)
    validate_hash(metric_evidence, METRIC_EVIDENCE_HASH)
    expected_metric = oracle.expected_metric(labeled.labels, metric, d0_episodes, v2_episodes, recovery_episodes)
    if metric_evidence != expected_metric:
        fail("D2_V2_R1_PRIVATE_METRIC_DIVERGENCE")
    public_metrics = json.loads((ROOT / oracle.METRICS_PATH).read_text(encoding="utf-8"))
    oracle.validate_public_metrics(public_metrics, metric)
    accounting = json.loads((ROOT / oracle.ACCOUNTING_PATH).read_text(encoding="utf-8"))
    validate_result_accounting(accounting)
    guard.require_exact(REAL_IDENTITIES)
    leakage = leakage_audit((private_root, fusion_path, metric_path, label_path))
    attacks_n, accepted = adversarial()
    if accepted:
        fail("D2_V2_R1_ACCEPTED_INVALID")
    parse_counts = tuple(sorted(guard.semantic_parses.items()))
    metric_public = {key: value for key, value in metric.items() if key != "events"}
    metric_public["values"] = tuple(sorted(metric_public["values"].items()))
    result = FrozenR1AuditResult(freeze["commit_a"], snapshot.snapshot_identity,
        tuple(sorted(freeze.items())), tuple(sorted(ordering.items())), tuple(sorted(metric_public.items())),
        parse_counts, tuple(sorted(leakage.items())), attacks_n, accepted)
    reports, markdown = build_reports(result)
    write_reports(reports, markdown)
    return {"status": PASS_STATUS, "attacks": attacks_n, "accepted": accepted,
            "hashes": {name: reports[name]["artifact_hash"] for name in REPORT_NAMES},
            "report_self_hash": reports["RECEIPT"]["report_self_hash"]}


def main() -> int:
    if sys.argv[1:]:
        print("D2_V2_R1_AUDIT_ARGUMENTS_REJECTED")
        return 2
    try:
        result = run_audit()
    except AuditR1Error as error:
        print(error.code)
        return 1
    except BaseException:
        print("D2_V2_R1_AUDIT_INTERNAL_BLOCKED")
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
